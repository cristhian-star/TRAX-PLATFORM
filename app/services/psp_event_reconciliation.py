from dataclasses import dataclass
from enum import Enum

from app.models.payment_attempt import PaymentAttemptRecord
from app.models.payment_obligation import PaymentObligation
from app.models.psp_event import PSPEventRecord
from app.services.payment_orchestration import (
    PaymentObligation as PaymentObligationRequest,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.payment_persistence_service import (
    PaymentPersistenceConflictError,
    apply_reconciliation,
    get_attempt_by_psp_identity,
)
from app.services.psp_contract import (
    PSPAdapter,
    PaymentAttemptStatus,
    UncertainResponseError,
)
from app.services.psp_event_contract import normalize_psp_provider


class PSPEventProcessingStatus(str, Enum):
    RECONCILED = "RECONCILED"
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    UNMATCHED = "UNMATCHED"
    INCOMPATIBLE_CONTEXT = "INCOMPATIBLE_CONTEXT"
    UNSUPPORTED_TOPIC = "UNSUPPORTED_TOPIC"
    ALREADY_TERMINAL = "ALREADY_TERMINAL"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class PSPEventProcessingResult:
    status: PSPEventProcessingStatus
    event_id: int
    attempt_id: int | None = None
    financial_status: PaymentAttemptStatus | None = None


class PSPEventReconciliationProcessor:
    """Use a persisted PSP event only as a signal for an authoritative query."""

    def __init__(
        self, *, session_factory, adapter, provider, live_mode, payment_topics
    ):
        if not callable(session_factory):
            raise TypeError("session_factory must be callable")
        if not isinstance(adapter, PSPAdapter):
            raise TypeError("adapter must satisfy PSPAdapter")
        if type(live_mode) is not bool:
            raise TypeError("live_mode must be a boolean")
        self._session_factory = session_factory
        self._adapter = adapter
        self._provider = normalize_psp_provider(provider)
        self._live_mode = live_mode
        self._payment_topics = _normalize_topics(payment_topics)

    def process(self, event_id):
        loaded = self._load(event_id)
        if isinstance(loaded, PSPEventProcessingResult):
            return loaded
        attempt_id, external_attempt_id, obligation = loaded

        try:
            authoritative = self._adapter.get_attempt(external_attempt_id)
        except UncertainResponseError as exc:
            if exc.attempt_id not in (None, external_attempt_id):
                raise PaymentPersistenceConflictError(
                    "PSP response belongs to a different external attempt"
                ) from exc
            result = _uncertain_result(obligation, external_attempt_id)
        else:
            if authoritative.attempt_id != external_attempt_id:
                raise PaymentPersistenceConflictError(
                    "PSP response belongs to a different external attempt"
                )
            result = _authoritative_result(obligation, authoritative.status)

        with self._session_factory() as session:
            with session.begin():
                current = session.query(PaymentAttemptRecord).filter_by(
                    id=attempt_id
                ).with_for_update().one()
                persisted = apply_reconciliation(session, current.id, result)
                status = (
                    PSPEventProcessingStatus.RECONCILIATION_REQUIRED
                    if persisted.requires_reconciliation
                    else PSPEventProcessingStatus.RECONCILED
                )
                return PSPEventProcessingResult(
                    status, event_id, persisted.id,
                    _financial_status(persisted.financial_status),
                )

    def _load(self, event_id):
        with self._session_factory() as session:
            with session.begin():
                event = session.get(PSPEventRecord, event_id)
                if event is None:
                    return PSPEventProcessingResult(
                        PSPEventProcessingStatus.EVENT_NOT_FOUND, event_id
                    )
                if (
                    event.provider != self._provider
                    or (not event.test_mode) != self._live_mode
                ):
                    return PSPEventProcessingResult(
                        PSPEventProcessingStatus.INCOMPATIBLE_CONTEXT, event_id
                    )
                if _normalize_topic(event.topic) not in self._payment_topics:
                    return PSPEventProcessingResult(
                        PSPEventProcessingStatus.UNSUPPORTED_TOPIC, event_id
                    )
                attempt = get_attempt_by_psp_identity(
                    session,
                    psp_provider=event.provider,
                    psp_live_mode=not event.test_mode,
                    external_attempt_id=event.external_resource_id,
                )
                if attempt is None:
                    return PSPEventProcessingResult(
                        PSPEventProcessingStatus.UNMATCHED, event_id
                    )
                if attempt.orchestration_result in {"APPROVED", "REJECTED"}:
                    return PSPEventProcessingResult(
                        PSPEventProcessingStatus.ALREADY_TERMINAL,
                        event_id,
                        attempt.id,
                        _financial_status(attempt.financial_status),
                    )
                obligation = session.get(PaymentObligation, attempt.obligation_id)
                request = PaymentObligationRequest(
                    obligation.internal_reference,
                    obligation.amount,
                    obligation.currency,
                    attempt.idempotency_key,
                )
                return attempt.id, attempt.external_attempt_id, request


def _authoritative_result(obligation, status):
    if not isinstance(status, PaymentAttemptStatus):
        status = PaymentAttemptStatus(status)
    return PaymentOrchestrationResult(
        obligation.internal_reference,
        obligation.amount,
        obligation.currency,
        obligation.idempotency_key,
        None,
        status,
        PaymentOutcome(status.value),
        False,
    )


def _uncertain_result(obligation, attempt_id):
    return PaymentOrchestrationResult(
        obligation.internal_reference,
        obligation.amount,
        obligation.currency,
        obligation.idempotency_key,
        attempt_id,
        None,
        PaymentOutcome.RECONCILIATION_REQUIRED,
        True,
    )


def _financial_status(value):
    return PaymentAttemptStatus(value) if value is not None else None


def _normalize_topics(values):
    if isinstance(values, (str, bytes)):
        raise ValueError("payment_topics must be a non-empty collection")
    try:
        normalized = frozenset(_normalize_topic(value) for value in values)
    except TypeError as exc:
        raise ValueError("payment_topics must be a non-empty collection") from exc
    if not normalized:
        raise ValueError("payment_topics must be a non-empty collection")
    return normalized


def _normalize_topic(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("payment topic must be a non-empty string")
    return value.strip().lower()
