from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.models.payment_attempt import PaymentAttemptRecord
from app.models.payment_obligation import PaymentObligation
from app.services.payment_orchestration import (
    InvalidPaymentRequestError,
    PaymentObligation as PaymentObligationRequest,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.psp_event_contract import normalize_psp_provider


IDEMPOTENCY_KEY_CONSTRAINT = "uq_payment_attempts_idempotency_key"
OBLIGATION_REFERENCE_CONSTRAINT = "uq_payment_obligations_reference"


class PaymentPersistenceConflictError(ValueError):
    pass


class PaymentPersistenceNotFoundError(LookupError):
    pass


def create_or_get_obligation(session, request):
    if not isinstance(request, PaymentObligationRequest):
        raise InvalidPaymentRequestError("request must be PaymentObligation")
    existing = session.query(PaymentObligation).filter_by(
        internal_reference=request.internal_reference
    ).first()
    if existing is not None:
        return _matching_obligation(existing, request)

    record = PaymentObligation(
        internal_reference=request.internal_reference,
        amount=request.amount,
        currency=request.currency,
    )
    if session.get_bind().dialect.name == "sqlite":
        session.add(record)
        session.flush()
        return record
    try:
        with session.begin_nested():
            session.add(record)
            session.flush()
        return record
    except IntegrityError as exc:
        if not _is_postgresql_constraint_violation(
            exc, "23505", OBLIGATION_REFERENCE_CONSTRAINT
        ):
            raise
        existing = session.query(PaymentObligation).filter_by(
            internal_reference=request.internal_reference
        ).one_or_none()
        if existing is None:
            raise
        return _matching_obligation(existing, request)


def register_or_get_attempt(
    session, obligation, result, *, psp_provider=None, psp_live_mode=None
):
    if not isinstance(obligation, PaymentObligation):
        raise InvalidPaymentRequestError("obligation must be persisted")
    if not isinstance(result, PaymentOrchestrationResult):
        raise InvalidPaymentRequestError("result must be PaymentOrchestrationResult")
    _require_result_matches(obligation, result)
    psp_provider, psp_live_mode = _normalize_psp_context(
        psp_provider, psp_live_mode
    )
    existing = session.query(PaymentAttemptRecord).filter_by(
        idempotency_key=result.idempotency_key
    ).first()
    if existing is not None:
        return _matching_attempt(
            existing, obligation, result, psp_provider, psp_live_mode
        )

    record = PaymentAttemptRecord(
        obligation_id=obligation.id,
        idempotency_key=result.idempotency_key,
        external_attempt_id=result.attempt_id,
        psp_provider=psp_provider,
        psp_live_mode=psp_live_mode,
        financial_status=(result.financial_status.value if result.financial_status else None),
        orchestration_result=result.outcome.value,
        requires_reconciliation=result.requires_reconciliation,
    )
    if session.get_bind().dialect.name == "sqlite":
        session.add(record)
        session.flush()
        return record
    try:
        with session.begin_nested():
            session.add(record)
            session.flush()
        return record
    except IntegrityError as exc:
        if not _is_postgresql_constraint_violation(
            exc, "23505", IDEMPOTENCY_KEY_CONSTRAINT
        ):
            raise
        existing = session.query(PaymentAttemptRecord).filter_by(
            idempotency_key=result.idempotency_key
        ).one_or_none()
        if existing is None:
            raise
        return _matching_attempt(
            existing, obligation, result, psp_provider, psp_live_mode
        )


def get_attempt_by_psp_identity(
    session, *, psp_provider, psp_live_mode, external_attempt_id
):
    provider, live_mode = _normalize_psp_context(psp_provider, psp_live_mode)
    if not isinstance(external_attempt_id, str) or not external_attempt_id.strip():
        raise InvalidPaymentRequestError(
            "external_attempt_id must be a non-empty string"
        )
    return session.query(PaymentAttemptRecord).filter_by(
        psp_provider=provider,
        psp_live_mode=live_mode,
        external_attempt_id=external_attempt_id,
    ).one_or_none()


def associate_attempt_psp_identity(
    session, attempt_id, *, psp_provider, psp_live_mode, external_attempt_id
):
    provider, live_mode = _normalize_psp_context(psp_provider, psp_live_mode)
    if not isinstance(external_attempt_id, str) or not external_attempt_id.strip():
        raise InvalidPaymentRequestError(
            "external_attempt_id must be a non-empty string"
        )
    attempt = session.get(PaymentAttemptRecord, attempt_id)
    if attempt is None:
        raise PaymentPersistenceNotFoundError("payment attempt not found")
    current = (attempt.psp_provider, attempt.psp_live_mode, attempt.external_attempt_id)
    target = (provider, live_mode, external_attempt_id)
    if current == target:
        return attempt
    if any(value is not None for value in current):
        raise PaymentPersistenceConflictError("PSP identity cannot be replaced")
    attempt.psp_provider = provider
    attempt.psp_live_mode = live_mode
    attempt.external_attempt_id = external_attempt_id
    session.flush()
    return attempt


def get_obligation(session, obligation_id):
    record = session.get(PaymentObligation, obligation_id)
    if record is None:
        raise PaymentPersistenceNotFoundError("payment obligation not found")
    return record


def get_attempts(session, obligation_id):
    get_obligation(session, obligation_id)
    return session.query(PaymentAttemptRecord).filter_by(
        obligation_id=obligation_id
    ).order_by(PaymentAttemptRecord.id).all()


def apply_reconciliation(session, attempt_id, result):
    if not isinstance(result, PaymentOrchestrationResult):
        raise InvalidPaymentRequestError("result must be PaymentOrchestrationResult")
    attempt = session.query(PaymentAttemptRecord).filter_by(id=attempt_id).with_for_update().first()
    if attempt is None:
        raise PaymentPersistenceNotFoundError("payment attempt not found")
    obligation = get_obligation(session, attempt.obligation_id)
    _require_result_matches(obligation, result)
    if result.idempotency_key != attempt.idempotency_key:
        raise PaymentPersistenceConflictError("idempotency key does not match")
    if attempt.external_attempt_id is not None and result.attempt_id not in (
        None, attempt.external_attempt_id
    ):
        raise PaymentPersistenceConflictError("external attempt id cannot be replaced")

    current = attempt.orchestration_result
    target = result.outcome.value
    allowed = {
        "RECONCILIATION_REQUIRED": {"RECONCILIATION_REQUIRED", "PENDING", "APPROVED", "REJECTED"},
        "PENDING": {"PENDING", "APPROVED", "REJECTED"},
        "APPROVED": {"APPROVED"},
        "REJECTED": {"REJECTED"},
    }
    if target not in allowed[current]:
        raise PaymentPersistenceConflictError(f"transition {current} -> {target} is not allowed")
    if target == current:
        expected_financial_status = (
            result.financial_status.value if result.financial_status else None
        )
        if (
            attempt.obligation_id != obligation.id
            or attempt.financial_status != expected_financial_status
            or attempt.requires_reconciliation != result.requires_reconciliation
        ):
            raise PaymentPersistenceConflictError(
                "reconciliation result has different content"
            )
        if attempt.external_attempt_id is None and result.attempt_id is not None:
            attempt.external_attempt_id = result.attempt_id
            attempt.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.flush()
        return attempt

    attempt.external_attempt_id = attempt.external_attempt_id or result.attempt_id
    attempt.financial_status = result.financial_status.value if result.financial_status else None
    attempt.orchestration_result = target
    attempt.requires_reconciliation = result.requires_reconciliation
    attempt.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.flush()
    return attempt


def _matching_obligation(record, request):
    if Decimal(record.amount) != request.amount or record.currency != request.currency:
        raise PaymentPersistenceConflictError("payment obligation reference has different content")
    return record


def _require_result_matches(obligation, result):
    if (obligation.internal_reference, Decimal(obligation.amount), obligation.currency) != (
        result.internal_reference, result.amount, result.currency
    ):
        raise PaymentPersistenceConflictError("orchestration result does not match obligation")


def _matching_attempt(record, obligation, result, psp_provider=None, psp_live_mode=None):
    expected = (
        obligation.id, result.attempt_id,
        result.financial_status.value if result.financial_status else None,
        result.outcome.value, result.requires_reconciliation,
        psp_provider, psp_live_mode,
    )
    actual = (
        record.obligation_id, record.external_attempt_id, record.financial_status,
        record.orchestration_result, record.requires_reconciliation,
        record.psp_provider, record.psp_live_mode,
    )
    if actual != expected:
        raise PaymentPersistenceConflictError("idempotency key has different content")
    return record


def _normalize_psp_context(psp_provider, psp_live_mode):
    if psp_provider is None and psp_live_mode is None:
        return None, None
    if psp_provider is None or psp_live_mode is None:
        raise InvalidPaymentRequestError(
            "psp_provider and psp_live_mode must be provided together"
        )
    if type(psp_live_mode) is not bool:
        raise InvalidPaymentRequestError("psp_live_mode must be a boolean")
    try:
        provider = normalize_psp_provider(psp_provider)
    except ValueError as exc:
        raise InvalidPaymentRequestError(str(exc)) from exc
    return provider, psp_live_mode


def _is_postgresql_constraint_violation(error, sqlstate, constraint_name):
    driver_error = error.orig
    actual_sqlstate = getattr(driver_error, "sqlstate", None) or getattr(
        driver_error, "pgcode", None
    )
    diagnostic = getattr(driver_error, "diag", None)
    actual_constraint = getattr(diagnostic, "constraint_name", None)
    return actual_sqlstate == sqlstate and actual_constraint == constraint_name
