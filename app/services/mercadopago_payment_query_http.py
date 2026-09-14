from dataclasses import dataclass
import json
import re

from app.services.mercadopago_payment_query import (
    MercadoPagoPaymentQueryError,
    normalize_mercadopago_payment_id,
    parse_mercadopago_payment_query,
)


class MercadoPagoPaymentHTTPError(RuntimeError):
    pass


class MercadoPagoPaymentAuthenticationError(MercadoPagoPaymentHTTPError):
    pass


class MercadoPagoPaymentNotFoundError(MercadoPagoPaymentHTTPError):
    pass


class MercadoPagoPaymentRecoverableError(MercadoPagoPaymentHTTPError):
    pass


class MercadoPagoPaymentRequestRejectedError(MercadoPagoPaymentHTTPError):
    pass


class MercadoPagoPaymentResponseError(MercadoPagoPaymentHTTPError):
    pass


@dataclass(frozen=True, slots=True)
class MercadoPagoHTTPResponse:
    status_code: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


_BASE_URL = "https://api.mercadopago.com"
_MAX_RESPONSE_BYTES = 1024 * 1024
_MAX_ACCESS_TOKEN_LENGTH = 2048
_ACCESS_TOKEN = re.compile(r"[A-Za-z0-9._~+/-]+=*", re.ASCII)
_TRANSPORT_FAILURE = object()
_DECODE_FAILURE = object()


class MercadoPagoPaymentQueryHTTPClient:
    def __init__(self, *, access_token, transport, timeout=10.0):
        self._access_token = _validate_access_token(access_token)
        if not callable(transport):
            raise TypeError("transport must be callable")
        if type(timeout) not in (int, float) or not 0 < timeout <= 30:
            raise ValueError("timeout must be between 0 and 30 seconds")
        self._transport = transport
        self._timeout = float(timeout)

    def __repr__(self):
        return "MercadoPagoPaymentQueryHTTPClient(timeout=<configured>)"

    def get_payment(self, payment_id, *, expected_live_mode):
        normalized_id = normalize_mercadopago_payment_id(payment_id)
        if type(expected_live_mode) is not bool:
            raise MercadoPagoPaymentQueryError(
                "invalid expected payment environment"
            )
        response = _call_transport(
            self._transport,
            method="GET",
            url=f"{_BASE_URL}/v1/payments/{normalized_id}",
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
            },
            timeout=self._timeout,
            allow_redirects=False,
            body=None,
        )
        if response is _TRANSPORT_FAILURE:
            raise MercadoPagoPaymentRecoverableError(
                "payment provider is temporarily unavailable"
            )
        if type(response) is not MercadoPagoHTTPResponse:
            raise MercadoPagoPaymentResponseError("invalid provider response")

        _classify_status(response.status_code)
        payload = _decode_json_response(response)
        return parse_mercadopago_payment_query(
            requested_payment_id=normalized_id,
            expected_live_mode=expected_live_mode,
            response=payload,
        )


def _validate_access_token(value):
    if (
        type(value) is not str
        or not value
        or len(value) > _MAX_ACCESS_TOKEN_LENGTH
        or _ACCESS_TOKEN.fullmatch(value) is None
    ):
        raise ValueError("invalid access token configuration")
    return value


def _call_transport(transport, **request):
    try:
        return transport(**request)
    except Exception:
        return _TRANSPORT_FAILURE


def _classify_status(status_code):
    if type(status_code) is not int:
        raise MercadoPagoPaymentResponseError("invalid provider response")
    if status_code == 200:
        return
    if status_code in (401, 403):
        raise MercadoPagoPaymentAuthenticationError(
            "payment provider authentication failed"
        )
    if status_code == 404:
        raise MercadoPagoPaymentNotFoundError("payment was not found")
    if status_code == 429 or 500 <= status_code <= 599:
        raise MercadoPagoPaymentRecoverableError(
            "payment provider is temporarily unavailable"
        )
    if 400 <= status_code <= 499:
        raise MercadoPagoPaymentRequestRejectedError(
            "payment provider rejected the request"
        )
    raise MercadoPagoPaymentResponseError("unexpected provider response")


def _decode_json_response(response):
    if type(response.body) is not bytes or not response.body:
        raise MercadoPagoPaymentResponseError("invalid provider response")
    if len(response.body) > _MAX_RESPONSE_BYTES:
        raise MercadoPagoPaymentResponseError("invalid provider response")
    if not _has_json_utf8_content_type(response.headers):
        raise MercadoPagoPaymentResponseError("invalid provider response")
    decoded = _strict_json_object(response.body)
    if decoded is _DECODE_FAILURE:
        raise MercadoPagoPaymentResponseError("invalid provider response")
    return decoded


def _has_json_utf8_content_type(headers):
    if type(headers) is not tuple:
        return False
    values = []
    for item in headers:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
        ):
            return False
        if item[0].strip().lower() == "content-type":
            values.append(item[1].strip().lower())
    if len(values) != 1:
        return False
    parts = [part.strip() for part in values[0].split(";")]
    if parts[0] != "application/json":
        return False
    charset = [part for part in parts[1:] if part.startswith("charset=")]
    return len(charset) <= 1 and (not charset or charset[0] == "charset=utf-8")


def _strict_json_object(body):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject_constant(_value):
        raise ValueError

    try:
        text = body.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
        if type(value) is not dict:
            return _DECODE_FAILURE
        return value
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        return _DECODE_FAILURE
