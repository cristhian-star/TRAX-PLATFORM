from dataclasses import dataclass
import re

from app.services.psp_contract import PaymentAttemptStatus


class MercadoPagoPaymentQueryError(ValueError):
    """Neutral validation failure for a Mercado Pago payment response."""


class MercadoPagoPaymentStatusNotRepresentableError(
    MercadoPagoPaymentQueryError
):
    """The provider status requires reconciliation outside the neutral contract."""


@dataclass(frozen=True, slots=True)
class MercadoPagoPaymentQueryResult:
    attempt_id: str
    status: PaymentAttemptStatus
    live_mode: bool
    status_detail: str | None = None


_SAFE_PAYMENT_ID = re.compile(r"[0-9]{1,32}", re.ASCII)
_SAFE_STATUS_DETAIL = re.compile(r"[a-z][a-z0-9_]{0,127}", re.ASCII)
_LONG_DIGIT_SEQUENCE = re.compile(r"[0-9]{13,19}", re.ASCII)
_STATUS_MAP = {
    "approved": PaymentAttemptStatus.APPROVED,
    "pending": PaymentAttemptStatus.PENDING,
    "in_process": PaymentAttemptStatus.PENDING,
    "authorized": PaymentAttemptStatus.PENDING,
    "rejected": PaymentAttemptStatus.REJECTED,
    "cancelled": PaymentAttemptStatus.REJECTED,
}
_NON_REPRESENTABLE_STATUSES = frozenset({"refunded", "charged_back"})


def parse_mercadopago_payment_query(
    *, requested_payment_id, expected_live_mode, response
):
    """Validate a decoded GET /v1/payments/{id} response without side effects."""

    requested_id = normalize_mercadopago_payment_id(requested_payment_id)
    if type(expected_live_mode) is not bool:
        raise MercadoPagoPaymentQueryError("invalid expected payment environment")
    if type(response) is not dict or not all(
        type(key) is str for key in response
    ):
        raise MercadoPagoPaymentQueryError("invalid payment response object")

    returned_id = response.get("id")
    status = response.get("status")
    live_mode = response.get("live_mode")
    if type(returned_id) is not int or returned_id <= 0:
        raise MercadoPagoPaymentQueryError("invalid payment response identity")
    if str(returned_id) != requested_id:
        raise MercadoPagoPaymentQueryError("payment response identity mismatch")
    if type(live_mode) is not bool:
        raise MercadoPagoPaymentQueryError("invalid payment response environment")
    if live_mode is not expected_live_mode:
        raise MercadoPagoPaymentQueryError("payment response environment mismatch")
    if type(status) is not str or not status:
        raise MercadoPagoPaymentQueryError("invalid payment response status")

    neutral_status = _STATUS_MAP.get(status)
    if neutral_status is None:
        if status in _NON_REPRESENTABLE_STATUSES or status:
            raise MercadoPagoPaymentStatusNotRepresentableError(
                "payment status requires explicit reconciliation"
            )
        raise MercadoPagoPaymentQueryError("invalid payment response status")

    status_detail = _validated_status_detail(response)
    return MercadoPagoPaymentQueryResult(
        attempt_id=requested_id,
        status=neutral_status,
        live_mode=live_mode,
        status_detail=status_detail,
    )


def normalize_mercadopago_payment_id(value):
    if type(value) is int:
        if value <= 0:
            raise MercadoPagoPaymentQueryError("invalid requested payment identity")
        value = str(value)
    elif type(value) is not str:
        raise MercadoPagoPaymentQueryError("invalid requested payment identity")
    if _SAFE_PAYMENT_ID.fullmatch(value) is None:
        raise MercadoPagoPaymentQueryError("invalid requested payment identity")
    return value


def _validated_status_detail(response):
    if "status_detail" not in response or response["status_detail"] is None:
        return None
    value = response["status_detail"]
    if (
        type(value) is not str
        or _SAFE_STATUS_DETAIL.fullmatch(value) is None
        or _LONG_DIGIT_SEQUENCE.search(value) is not None
    ):
        raise MercadoPagoPaymentQueryError("invalid payment response detail")
    return value
