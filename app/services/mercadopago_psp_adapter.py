from dataclasses import dataclass, field

from app.services.mercadopago_payment_query import (
    MercadoPagoPaymentQueryError,
    MercadoPagoPaymentStatusNotRepresentableError,
    normalize_mercadopago_payment_id,
)
from app.services.mercadopago_payment_query_http import (
    MercadoPagoPaymentAuthenticationError,
    MercadoPagoPaymentNotFoundError,
    MercadoPagoPaymentRecoverableError,
    MercadoPagoPaymentRequestRejectedError,
    MercadoPagoPaymentResponseError,
)
from app.services.psp_contract import (
    PSPPaymentQueryError,
    PSPPaymentQueryResult,
    PSPPaymentQueryUncertainError,
)


@dataclass(frozen=True, slots=True, repr=False, init=False)
class MercadoPagoPSPAdapter:
    """Mercado Pago implementation of the neutral payment-query capability."""

    _client: object = field(repr=False)
    _live_mode: bool

    def __init__(self, *, client, live_mode):
        if not callable(getattr(client, "get_payment", None)):
            raise TypeError("client must provide get_payment")
        if type(live_mode) is not bool:
            raise TypeError("live_mode must be a boolean")
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_live_mode", live_mode)

    @property
    def provider(self):
        return "mercadopago"

    @property
    def live_mode(self):
        return self._live_mode

    def __repr__(self):
        mode = "live" if self._live_mode else "test"
        return f"MercadoPagoPSPAdapter(provider=mercadopago, mode={mode})"

    def query_payment(self, external_attempt_id):
        try:
            normalized_id = normalize_mercadopago_payment_id(external_attempt_id)
        except MercadoPagoPaymentQueryError:
            raise PSPPaymentQueryError("invalid payment query") from None

        outcome = _query_client(self._client, normalized_id, self._live_mode)
        if outcome is _UNCERTAIN:
            raise PSPPaymentQueryUncertainError(
                external_attempt_id=normalized_id
            )
        if outcome is _QUERY_ERROR:
            raise PSPPaymentQueryError("payment query failed")
        return PSPPaymentQueryResult(
            external_attempt_id=outcome.attempt_id,
            status=outcome.status,
        )


_UNCERTAIN = object()
_QUERY_ERROR = object()


def _query_client(client, external_attempt_id, live_mode):
    try:
        return client.get_payment(
            external_attempt_id,
            expected_live_mode=live_mode,
        )
    except (
        MercadoPagoPaymentNotFoundError,
        MercadoPagoPaymentRecoverableError,
        MercadoPagoPaymentStatusNotRepresentableError,
    ):
        return _UNCERTAIN
    except (
        MercadoPagoPaymentAuthenticationError,
        MercadoPagoPaymentRequestRejectedError,
        MercadoPagoPaymentResponseError,
        MercadoPagoPaymentQueryError,
        TypeError,
        ValueError,
    ):
        return _QUERY_ERROR
