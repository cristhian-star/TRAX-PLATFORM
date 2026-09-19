from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from io import BytesIO
from urllib.parse import urlsplit

import segno

from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.services.payment_order_application_service import (
    PaymentOrderExpiredError, _authorized_contract, _command, _require_identifiers,
    _require_unexpired, _same_price, _same_reservation, _stored_result,
)
from app.services.psp_payment_order_contract import (
    PaymentOrderCreationUncertainError, validate_payment_order_creation_result,
)


class PaymentOrderUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CheckoutPresentation:
    amount: Decimal
    expires_at: datetime
    checkout_url: str = field(repr=False)

    @property
    def amount_text(self):
        with localcontext() as context:
            context.prec = 70
            return format(self.amount, ".2f")


class PaymentOrderDeliveryService:
    """Owner-only read boundary; never creates on read or QR generation."""

    def __init__(self, *, session_factory, application_service,
                 clock=lambda: datetime.now(timezone.utc), checkout_validator=None):
        self._sessions = session_factory
        self._application = application_service
        self._clock = clock
        self._checkout_validator = checkout_validator

    def create_order(self, *, actor_user_id, contract_request_id):
        # Authorize before invoking 4B; also refuse cancelled/expired replays.
        self._read(actor_user_id, contract_request_id, required=False)
        self._application.create_order(
            actor_user_id=actor_user_id, contract_request_id=contract_request_id,
        )

    def get_checkout(self, *, actor_user_id, contract_request_id):
        result = self._read(actor_user_id, contract_request_id, required=True)
        _require_unexpired(result.expires_at, self._clock)
        return result

    def ensure_unexpired(self, checkout):
        _require_unexpired(checkout.expires_at, self._clock)

    def _read(self, actor_id, contract_id, *, required):
        _require_identifiers(actor_id, contract_id)
        with self._sessions() as session:
            contract = _authorized_contract(session, actor_id, contract_id)
            obligation = session.query(PaymentObligation).filter_by(
                contract_request_id=contract.id,
            ).populate_existing().one_or_none()
            if obligation is None:
                if required:
                    raise PaymentOrderUnavailableError
                return None
            _same_price(obligation, contract)
            reservation = session.query(PaymentOrderReservation).filter_by(
                obligation_id=obligation.id,
            ).populate_existing().one_or_none()
            if reservation is None:
                if required:
                    raise PaymentOrderUnavailableError
                return None
            _same_reservation(reservation, obligation, contract, actor_id)
            _require_unexpired(_command(reservation).expires_at, self._clock)
            if reservation.status != "SUCCEEDED":
                if not required and reservation.status == "PREPARED":
                    return None
                raise PaymentOrderCreationUncertainError
            order = session.get(PaymentOrder, reservation.payment_order_id)
            if order is None:
                raise PaymentOrderCreationUncertainError
            if order.status != "ACTIVE":
                raise PaymentOrderExpiredError
            if order.obligation_id != obligation.id or order.professional_id != contract.professional_id:
                raise PaymentOrderUnavailableError
            invalid_result = False
            try:
                result = validate_payment_order_creation_result(
                    _command(reservation), _stored_result(order, self._checkout_validator)
                )
                parsed = urlsplit(result.checkout_url)
                allowed = (result.provider == "mercadopago"
                           and parsed.hostname == "www.mercadopago.com.ar"
                           and parsed.port in (None, 443))
                if self._checkout_validator is not None:
                    allowed = self._checkout_validator(result)
            except Exception:
                invalid_result = True
            if invalid_result or not allowed:
                raise PaymentOrderUnavailableError
            _require_unexpired(result.expires_at, self._clock)
            return CheckoutPresentation(result.amount, result.expires_at, result.checkout_url)

    def get_qr_png(self, *, actor_user_id, contract_request_id):
        checkout = self.get_checkout(
            actor_user_id=actor_user_id, contract_request_id=contract_request_id,
        )
        buffer = BytesIO()
        segno.make_qr(checkout.checkout_url, error="m").save(
            buffer, kind="png", scale=5, border=4, dark="black", light="white",
        )
        _require_unexpired(checkout.expires_at, self._clock)
        return buffer.getvalue()


def build_checkout_delivery_service(*, session_factory, oauth_provider,
                                    commission_policy, configuration=None,
                                    transport=None,
                                    clock=lambda: datetime.now(timezone.utc)):
    """Explicit composition only; absent 4C configuration remains disabled."""
    from app.services.mercadopago_order_creation_adapter import build_mercadopago_order_service
    application = build_mercadopago_order_service(
        session_factory=session_factory, configuration=configuration,
        oauth_provider=oauth_provider, commission_policy=commission_policy,
        transport=transport, clock=clock,
    )
    return PaymentOrderDeliveryService(
        session_factory=session_factory, application_service=application, clock=clock,
    )
