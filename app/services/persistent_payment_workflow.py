from app.models.payment_attempt import PaymentAttemptRecord
from app.models.payment_obligation import PaymentObligation as PaymentObligationRecord
from app.services.payment_orchestration import (
    PaymentObligation,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.payment_persistence_service import (
    PaymentPersistenceConflictError,
    apply_reconciliation,
    create_or_get_obligation,
    get_obligation,
    register_or_get_attempt,
)
from app.services.psp_contract import PaymentAttemptStatus


class PersistentPaymentWorkflow:
    """Coordinate durable state around, never across, a PSP adapter call.

    Transport uncertainty is persisted without a financial status. ``PENDING``
    is reserved for an authoritative PSP response.
    """

    def __init__(self, *, session_factory, orchestrator):
        if not callable(session_factory):
            raise TypeError("session_factory must be callable")
        if not callable(getattr(orchestrator, "process", None)) or not callable(
            getattr(orchestrator, "reconcile", None)
        ):
            raise TypeError("orchestrator must provide process and reconcile")
        self._session_factory = session_factory
        self._orchestrator = orchestrator

    def process(self, request):
        obligation_id, persisted = self._prepare(request)
        if persisted is not None:
            return persisted

        result = self._orchestrator.process(request)

        with self._session_factory() as session:
            with session.begin():
                obligation = get_obligation(session, obligation_id)
                attempt = register_or_get_attempt(session, obligation, result)
                persisted = _stored_result(obligation, attempt)
        return persisted

    def reconcile(self, request):
        obligation_id, uncertain = self._load_reconciliation(request)

        result = self._orchestrator.reconcile(request, uncertain)

        with self._session_factory() as session:
            with session.begin():
                obligation = get_obligation(session, obligation_id)
                attempt = session.query(PaymentAttemptRecord).filter_by(
                    idempotency_key=request.idempotency_key
                ).one()
                reconciled = apply_reconciliation(session, attempt.id, result)
                persisted = _stored_result(obligation, reconciled)
        return persisted

    def _prepare(self, request):
        with self._session_factory() as session:
            with session.begin():
                obligation = create_or_get_obligation(session, request)
                existing = session.query(PaymentAttemptRecord).filter_by(
                    idempotency_key=request.idempotency_key
                ).one_or_none()
                if existing is None:
                    return obligation.id, None
                if existing.obligation_id != obligation.id:
                    raise PaymentPersistenceConflictError(
                        "idempotency key belongs to a different obligation"
                    )
                persisted = _stored_result(obligation, existing)
                _require_same_request(request, persisted)
                return obligation.id, persisted

    def _load_reconciliation(self, request):
        if not isinstance(request, PaymentObligation):
            raise TypeError("request must be PaymentObligation")
        with self._session_factory() as session:
            with session.begin():
                obligation = session.query(PaymentObligationRecord).filter_by(
                    internal_reference=request.internal_reference
                ).one_or_none()
                if obligation is None:
                    raise PaymentPersistenceConflictError(
                        "payment obligation is not persisted"
                    )
                existing = session.query(PaymentAttemptRecord).filter_by(
                    idempotency_key=request.idempotency_key
                ).one_or_none()
                if existing is None or existing.obligation_id != obligation.id:
                    raise PaymentPersistenceConflictError(
                        "reconciliation attempt is not persisted"
                    )
                uncertain = _stored_result(obligation, existing)
                _require_same_request(request, uncertain)
                if (
                    uncertain.outcome is not PaymentOutcome.RECONCILIATION_REQUIRED
                    or not uncertain.requires_reconciliation
                ):
                    raise PaymentPersistenceConflictError(
                        "only reconciliation-required attempts can be reconciled"
                    )
                return obligation.id, uncertain


def _stored_result(obligation, attempt):
    financial_status = (
        PaymentAttemptStatus(attempt.financial_status)
        if attempt.financial_status is not None
        else None
    )
    return PaymentOrchestrationResult(
        internal_reference=obligation.internal_reference,
        amount=obligation.amount,
        currency=obligation.currency,
        idempotency_key=attempt.idempotency_key,
        attempt_id=attempt.external_attempt_id,
        financial_status=financial_status,
        outcome=PaymentOutcome(attempt.orchestration_result),
        requires_reconciliation=attempt.requires_reconciliation,
    )


def _require_same_request(request, result):
    if (
        request.internal_reference,
        request.amount,
        request.currency,
        request.idempotency_key,
    ) != (
        result.internal_reference,
        result.amount,
        result.currency,
        result.idempotency_key,
    ):
        raise PaymentPersistenceConflictError(
            "persisted payment attempt has different content"
        )
