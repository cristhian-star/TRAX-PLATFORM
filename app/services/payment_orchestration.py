from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.psp_contract import (
    PSPAdapter,
    PaymentAttempt,
    PaymentAttemptStatus,
    UncertainResponseError,
)


class InvalidPaymentRequestError(ValueError):
    pass


class PaymentOutcome(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class PaymentObligation:
    internal_reference: str
    amount: Decimal
    currency: str
    idempotency_key: str

    def __post_init__(self) -> None:
        reference = _required_text(self.internal_reference, "internal_reference")
        currency = _required_text(self.currency, "currency").upper()
        key = _required_text(self.idempotency_key, "idempotency_key")
        if key != self.idempotency_key:
            raise InvalidPaymentRequestError(
                "idempotency_key must not contain surrounding whitespace"
            )
        amount = _valid_amount(self.amount)

        object.__setattr__(self, "internal_reference", reference)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "idempotency_key", key)


@dataclass(frozen=True, slots=True)
class PaymentOrchestrationResult:
    internal_reference: str
    amount: Decimal
    currency: str
    idempotency_key: str
    attempt_id: str | None
    financial_status: PaymentAttemptStatus | None
    outcome: PaymentOutcome
    requires_reconciliation: bool


class InMemoryPaymentOrchestrator:
    """Neutral one-step payment orchestration over a PSPAdapter.

    The service owns no persistence and performs no automatic retries. A caller
    must explicitly invoke ``reconcile`` after an uncertain response.
    """

    def __init__(self, adapter: PSPAdapter):
        if not isinstance(adapter, PSPAdapter):
            raise TypeError("adapter must satisfy PSPAdapter")
        self._adapter = adapter

    def process(self, obligation: PaymentObligation) -> PaymentOrchestrationResult:
        request = self._valid_obligation(obligation)
        try:
            attempt = self._adapter.create_attempt(
                internal_reference=request.internal_reference,
                amount=request.amount,
                currency=request.currency,
                idempotency_key=request.idempotency_key,
            )
        except UncertainResponseError as exc:
            return self._uncertain_result(request, exc.attempt_id)
        return self._attempt_result(request, attempt)

    def reconcile(
        self,
        obligation: PaymentObligation,
        uncertain_result: PaymentOrchestrationResult,
    ) -> PaymentOrchestrationResult:
        request = self._valid_obligation(obligation)
        self._validate_reconciliation(request, uncertain_result)

        if uncertain_result.attempt_id is not None:
            attempt = self._adapter.get_attempt(uncertain_result.attempt_id)
        else:
            try:
                attempt = self._adapter.create_attempt(
                    internal_reference=request.internal_reference,
                    amount=request.amount,
                    currency=request.currency,
                    idempotency_key=request.idempotency_key,
                )
            except UncertainResponseError as exc:
                return self._uncertain_result(request, exc.attempt_id)
        return self._attempt_result(request, attempt)

    @staticmethod
    def _valid_obligation(obligation: PaymentObligation) -> PaymentObligation:
        if not isinstance(obligation, PaymentObligation):
            raise InvalidPaymentRequestError("obligation must be PaymentObligation")
        return obligation

    @staticmethod
    def _validate_reconciliation(
        obligation: PaymentObligation,
        result: PaymentOrchestrationResult,
    ) -> None:
        if not isinstance(result, PaymentOrchestrationResult):
            raise InvalidPaymentRequestError(
                "uncertain_result must be PaymentOrchestrationResult"
            )
        if not result.requires_reconciliation or (
            result.outcome is not PaymentOutcome.RECONCILIATION_REQUIRED
        ):
            raise InvalidPaymentRequestError(
                "only a reconciliation-required result can be reconciled"
            )
        if (
            result.internal_reference,
            result.amount,
            result.currency,
            result.idempotency_key,
        ) != (
            obligation.internal_reference,
            obligation.amount,
            obligation.currency,
            obligation.idempotency_key,
        ):
            raise InvalidPaymentRequestError(
                "reconciliation result does not match the payment obligation"
            )

    @staticmethod
    def _attempt_result(
        obligation: PaymentObligation,
        attempt: PaymentAttempt,
    ) -> PaymentOrchestrationResult:
        outcome = PaymentOutcome(attempt.status.value)
        return PaymentOrchestrationResult(
            internal_reference=obligation.internal_reference,
            amount=obligation.amount,
            currency=obligation.currency,
            idempotency_key=obligation.idempotency_key,
            attempt_id=attempt.attempt_id,
            financial_status=attempt.status,
            outcome=outcome,
            requires_reconciliation=False,
        )

    @staticmethod
    def _uncertain_result(
        obligation: PaymentObligation,
        attempt_id: str | None,
    ) -> PaymentOrchestrationResult:
        return PaymentOrchestrationResult(
            internal_reference=obligation.internal_reference,
            amount=obligation.amount,
            currency=obligation.currency,
            idempotency_key=obligation.idempotency_key,
            attempt_id=attempt_id,
            financial_status=None,
            outcome=PaymentOutcome.RECONCILIATION_REQUIRED,
            requires_reconciliation=True,
        )


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidPaymentRequestError(f"{field_name} must be a non-empty string")
    return value.strip()


def _valid_amount(value: Decimal) -> Decimal:
    if isinstance(value, float) or not isinstance(value, Decimal):
        raise InvalidPaymentRequestError("amount must be a Decimal, never float")
    if not value.is_finite() or value <= 0:
        raise InvalidPaymentRequestError("amount must be finite and positive")
    return value
