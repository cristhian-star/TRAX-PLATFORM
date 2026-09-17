from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import math
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from app.services import mercadopago_payment_query_http as http
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError,
    InvalidPaymentOrderCreationResultError,
    PaymentOrderCreationCommand,
    PaymentOrderCreationResult,
    PaymentOrderCreationUncertainError,
)


class MercadoPagoOrderConfigurationError(ValueError):
    pass


class MercadoPagoOrderAuthenticationError(RuntimeError):
    pass


class MercadoPagoOrderRejectedError(RuntimeError):
    pass


_URL = "https://api.mercadopago.com/v1/orders"
_CHECKOUT_HOST = "www.mercadopago.com.ar"
_REFERENCE = re.compile(r"[A-Za-z0-9_-]{1,64}", re.ASCII)
_ID = re.compile(r"[A-Za-z0-9_-]{1,160}", re.ASCII)


@dataclass(frozen=True, slots=True)
class ProfessionalOAuthCredential:
    professional_id: int
    access_token: str = field(repr=False)
    live_mode: bool
    currency: str


@dataclass(frozen=True, slots=True)
class MercadoPagoOrderConfiguration:
    enabled: bool = False
    live_mode: bool = False
    timeout: float = 10.0

    def __post_init__(self):
        if (
            type(self.enabled) is not bool or type(self.live_mode) is not bool
            or type(self.timeout) not in (int, float)
            or not math.isfinite(self.timeout) or not 0 < self.timeout <= 30
        ):
            raise MercadoPagoOrderConfigurationError("invalid order configuration")


class UrllibMercadoPagoOrderTransport(http.UrllibMercadoPagoTransport):
    """Reuse verified TLS, no redirects and bounded response reading for POST."""

    def __repr__(self):
        return "UrllibMercadoPagoOrderTransport()"

    def __call__(self, *, method, url, headers, timeout, allow_redirects, body):
        if (
            method != "POST" or url != _URL or allow_redirects is not False
            or type(body) is not bytes
        ):
            raise ValueError("invalid order transport request")
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with self._opener.open(request, timeout=timeout) as response:
                return http._stdlib_response(response)
        except urllib.error.HTTPError as error:
            status = error.code
            http._close_http_error(error)
            return http.MercadoPagoHTTPResponse(status, (), b"")


@dataclass(frozen=True, slots=True, repr=False)
class MercadoPagoOrderCreationAdapter:
    configuration: MercadoPagoOrderConfiguration
    oauth_provider: object = field(repr=False)
    commission_policy: object = field(repr=False)
    transport: object = field(repr=False)
    clock: object = field(default=lambda: datetime.now(timezone.utc), repr=False)

    def __post_init__(self):
        if (
            type(self.configuration) is not MercadoPagoOrderConfiguration
            or not all(callable(x) for x in (
                self.oauth_provider, self.commission_policy, self.transport, self.clock
            ))
        ):
            raise MercadoPagoOrderConfigurationError("invalid order configuration")

    def __repr__(self):
        return "MercadoPagoOrderCreationAdapter()"

    def validate_configuration(self):
        if not self.configuration.enabled:
            raise MercadoPagoOrderConfigurationError("order creation is disabled")

    def prepare_payment_order(self, command):
        """Resolve trusted local providers before 4B writes/reserves its claim."""
        self.validate_configuration()
        _validate_command(command, self.clock)
        credential = _resolve(self.oauth_provider, command.professional_id)
        if (
            type(credential) is not ProfessionalOAuthCredential
            or type(credential.professional_id) is not int
            or credential.professional_id != command.professional_id
            or type(credential.live_mode) is not bool
            or credential.live_mode != self.configuration.live_mode
            or credential.currency != "ARS"
        ):
            raise MercadoPagoOrderConfigurationError("invalid receiver configuration")
        invalid_token = False
        try:
            token = http._validate_access_token(credential.access_token)
        except Exception:
            invalid_token = True
        if invalid_token:
            raise MercadoPagoOrderConfigurationError("invalid receiver configuration")
        fee = _resolve(self.commission_policy, command)
        if (
            type(fee) is not Decimal or not fee.is_finite()
            or fee < 0 or fee > command.amount or fee.as_tuple().exponent < -2
        ):
            raise MercadoPagoOrderConfigurationError("invalid commission configuration")
        payload = {
            "type": "online",
            "processing_mode": "manual",
            "total_amount": _money(command.amount),
            "external_reference": command.external_reference,
            "marketplace_fee": _money(fee),
            "expiration_time": "PT72H",
            "items": [{
                "title": command.concept,
                "quantity": 1,
                "unit_price": _money(command.amount),
            }],
        }
        return _PreparedOrder(
            command, token, json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            self.configuration, self.transport, self.clock,
        )

    def create_payment_order(self, command):
        return self.prepare_payment_order(command).create_payment_order(command)


@dataclass(frozen=True, slots=True, repr=False)
class _PreparedOrder:
    command: PaymentOrderCreationCommand
    token: str = field(repr=False)
    body: bytes = field(repr=False)
    configuration: MercadoPagoOrderConfiguration
    transport: object = field(repr=False)
    clock: object = field(repr=False)

    def __repr__(self):
        return "PreparedMercadoPagoOrder()"

    def create_payment_order(self, command):
        if command != self.command:
            raise InvalidPaymentOrderCreationRequestError("invalid prepared order")
        _validate_command(command, self.clock)
        transport_failed = False
        try:
            response = self.transport(
                method="POST", url=_URL,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "X-Idempotency-Key": command.idempotency_key,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self.configuration.timeout, allow_redirects=False, body=self.body,
            )
        except Exception:
            transport_failed = True
        if transport_failed:
            raise PaymentOrderCreationUncertainError("order creation is uncertain")
        if type(response) is not http.MercadoPagoHTTPResponse or type(response.status_code) is not int:
            raise PaymentOrderCreationUncertainError("invalid order response")
        status = response.status_code
        if status in (401, 403):
            raise MercadoPagoOrderAuthenticationError("order provider authentication failed")
        if status in (409, 423, 429) or 500 <= status <= 599:
            raise PaymentOrderCreationUncertainError("order creation requires recovery")
        if 400 <= status <= 499:
            raise MercadoPagoOrderRejectedError("order provider rejected the request")
        if status != 201:
            raise PaymentOrderCreationUncertainError("unexpected order response")
        invalid_response = False
        try:
            payload = http._decode_json_response(response)
            result = _result(command, payload, self.configuration.live_mode)
        except Exception:
            invalid_response = True
        if invalid_response:
            raise InvalidPaymentOrderCreationResultError("invalid order response")
        return result


def _resolve(provider, value):
    unavailable = False
    try:
        resolved = provider(value)
    except Exception:
        unavailable = True
    if unavailable:
        raise MercadoPagoOrderConfigurationError("order prerequisites unavailable")
    return resolved


def _validate_command(command, clock):
    if (
        type(command) is not PaymentOrderCreationCommand
        or len(command.idempotency_key) > 128
        or _REFERENCE.fullmatch(command.external_reference) is None
    ):
        raise InvalidPaymentOrderCreationRequestError("invalid order request")
    now = clock()
    if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
        raise MercadoPagoOrderConfigurationError("invalid order clock")
    if now >= command.expires_at:
        raise InvalidPaymentOrderCreationRequestError("order has expired")


def _money(value):
    # No float conversion and no caller Decimal context rounding.
    with localcontext() as context:
        context.prec = 70
        return format(value, ".2f")


def _result(command, payload, live_mode):
    identifier = payload.get("id")
    url = payload.get("checkout_url")
    if type(identifier) is not str or _ID.fullmatch(identifier) is None:
        raise ValueError
    if type(url) is not str:
        raise ValueError
    parsed = urlsplit(url)
    if parsed.hostname != _CHECKOUT_HOST or parsed.port not in (None, 443):
        raise ValueError
    if (
        payload.get("external_reference") != command.external_reference
        or payload.get("currency") != "ARS"
        or type(payload.get("total_amount")) is not str
        or Decimal(payload["total_amount"]) != command.amount
    ):
        raise ValueError
    values = {name: getattr(command, name) for name in (
        "local_order_id", "obligation_reference", "external_reference", "amount",
        "currency", "concept", "idempotency_key", "created_at", "expires_at",
    )}
    return PaymentOrderCreationResult(
        **values, external_order_id=identifier, checkout_url=url,
        provider="mercadopago", live_mode=live_mode,
    )


def build_mercadopago_order_service(
    *, session_factory, configuration=None, oauth_provider, commission_policy,
    transport=None, clock=lambda: datetime.now(timezone.utc),
):
    """Explicit internal composition; never obtains a global access token."""
    adapter = MercadoPagoOrderCreationAdapter(
        configuration=configuration if configuration is not None else MercadoPagoOrderConfiguration(),
        oauth_provider=oauth_provider, commission_policy=commission_policy,
        transport=transport if transport is not None else UrllibMercadoPagoOrderTransport(),
        clock=clock,
    )
    return PaymentOrderApplicationService(session_factory=session_factory, adapter=adapter, clock=clock)
