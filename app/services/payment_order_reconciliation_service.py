"""Durable inbox scheduling and fenced, evidence-only reconciliation."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import and_, or_, update, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.models.contract_request import ContractRequest
from app.models.psp_event import PSPEventRecord
from app.models.payment_order_reconciliation import (
    PaymentOrderReconciliationWork as Work,
    PaymentOrderReconciliationAttempt as Attempt,
    PaymentOrderReconciliationEvidence as Evidence,
    PaymentOrderReconciliationQuarantine as Quarantine,
)
from app.services.psp_event_inbox import (
    PSPEventConflictError, get_event_by_identity, register_or_get_event,
)
from app.services.mercadopago_order_query_adapter import (
    OrderQueryContext, OrderQueryUnavailableError, OrderQueryAuthenticationError,
    OrderQueryResponseError, OrderSnapshot, refunds_are_consistent,
)


# Eight attempts, each dispatched separately. No retries in the HTTP transport.
RETRY_DELAYS = (900, 900, 19800, 151200, 172800, 345600, 345600)
LEASE_DURATION_SECONDS = 60
STALE_LEASE_RECOVERY_SECONDS = 120
_PROCESS_FAILED = object()


class OrderReconciliationPersistenceError(RuntimeError):
    pass


def _run_safely(function, *args):
    try:
        return function(*args)
    except Exception:
        return _PROCESS_FAILED


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _instant(value):
    if not isinstance(value, datetime):
        raise ValueError("invalid reconciliation clock")
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def insert_once(session, model, values, identity):
    """Target only the expected unique identity; propagate other DB failures."""
    dialect = session.get_bind().dialect.name
    builder = {"sqlite": sqlite_insert, "postgresql": pg_insert}.get(dialect)
    if builder is None:
        raise ValueError("unsupported reconciliation database")
    session.execute(builder(model.__table__).values(**values).on_conflict_do_nothing(index_elements=identity))


def quarantine(session, event_id, digest, reason, now):
    insert_once(session, Quarantine, dict(
        event_id=event_id, content_hash=digest, reason=reason, received_at=now,
    ), ["event_id", "content_hash", "reason"])
    insert_once(session, Work, dict(
        event_id=event_id, status="QUARANTINED", attempt_count=0,
        next_attempt_at=now, created_at=now, last_error=reason,
    ), ["event_id"])
    session.execute(update(Work).where(Work.event_id == event_id).values(
        status="QUARANTINED", lease_token=None, lease_until=None, last_error=reason,
    ))
    session.execute(update(Attempt).where(
        Attempt.work_id.in_(select(Work.id).where(Work.event_id == event_id)),
        Attempt.outcome == "STARTED",
    ).values(outcome="QUARANTINED", finished_at=now, error_code=reason))
    # Effects and quarantine linearize on the same order row. Keep Work -> Order
    # lock order consistent with reconciliation completion; no external I/O here.
    event = session.get(PSPEventRecord, event_id)
    order = session.query(PaymentOrder).filter_by(
        provider=event.provider, live_mode=not event.test_mode,
        external_order_id=event.external_resource_id,
    ).populate_existing().with_for_update().one_or_none()
    if order is not None:
        session.execute(update(PaymentOrder).where(PaymentOrder.id == order.id).values(
            amount=PaymentOrder.amount, updated_at=PaymentOrder.updated_at))


def receive_order_event(session, event, *, quarantine_reason=None):
    """Caller owns commit/rollback. Collisions never overwrite the first receipt."""
    now = _instant(event.received_at)
    collision = False
    try:
        record = register_or_get_event(session, event)
    except PSPEventConflictError:
        collision = True
    if collision:
        record = get_event_by_identity(session, event.provider, event.test_mode, event.external_event_id)
        quarantine(session, record.id, event.payload_hash, "EVENT_COLLISION", now)
        if quarantine_reason == "TIMESTAMP_OUTSIDE_WINDOW":
            quarantine(session, record.id, event.payload_hash, quarantine_reason, now)
        return record.id
    if quarantine_reason is not None:
        if quarantine_reason != "TIMESTAMP_OUTSIDE_WINDOW":
            raise ValueError("invalid receipt quarantine classification")
        quarantine(session, record.id, event.payload_hash, quarantine_reason, now)
        return record.id
    insert_once(session, Work, dict(
        event_id=record.id, status="QUEUED", attempt_count=0,
        next_attempt_at=now, created_at=now,
    ), ["event_id"])
    return record.id


def _query(adapter, context):
    # Retain only classifications; no original exception crosses this boundary.
    try:
        return adapter.query_order(context), None
    except OrderQueryAuthenticationError:
        return None, "AUTHENTICATION"
    except OrderQueryUnavailableError:
        return None, "UNAVAILABLE"
    except OrderQueryResponseError:
        return None, "INVALID_RESPONSE"
    except Exception:
        return None, "UNAVAILABLE"


class PaymentOrderReconciliationProcessor:
    def __init__(self, *, session_factory, adapter, enabled=False, clock=utcnow,
                 simulated_timing=None):
        if (not callable(session_factory) or not callable(clock)
                or not callable(getattr(adapter, "query_order", None)) or type(enabled) is not bool
                or (simulated_timing is not None and not callable(simulated_timing))):
            raise ValueError("invalid reconciliation configuration")
        self._sessions = session_factory
        self._adapter = adapter
        self._enabled = enabled
        self._clock = clock
        self._simulated_timing = simulated_timing

    def __repr__(self):
        return "PaymentOrderReconciliationProcessor(enabled=<configured>)"

    def _now(self):
        return _instant(self._clock())

    def claim(self, work_id):
        result = _run_safely(self._claim, work_id)
        if result is _PROCESS_FAILED:
            raise OrderReconciliationPersistenceError("reconciliation temporarily unavailable")
        return result

    def _claim(self, work_id):
        if not self._enabled:
            return None
        now, token = self._now(), str(uuid4())
        with self._sessions() as session:
            with session.begin():
                # A crash in the eighth attempt must also terminate durably.
                exhausted = session.execute(update(Work).where(
                    Work.id == work_id, Work.status == "PROCESSING",
                    Work.lease_until <= _stale_lease_cutoff(now), Work.attempt_count == 8,
                ).values(status="EXHAUSTED", lease_token=None, lease_until=None, last_error="LEASE_LOST"))
                if exhausted.rowcount:
                    session.execute(update(Attempt).where(Attempt.work_id == work_id, Attempt.outcome == "STARTED").values(
                        outcome="LEASE_LOST", finished_at=now, error_code="LEASE_LOST"))
                    return None
                claimed = session.execute(update(Work).where(
                    Work.id == work_id, Work.attempt_count < 8,
                    or_(and_(Work.status == "QUEUED", Work.next_attempt_at <= now),
                        and_(Work.status == "PROCESSING", Work.lease_until <= _stale_lease_cutoff(now))),
                ).values(status="PROCESSING", attempt_count=Work.attempt_count + 1,
                         lease_token=token, lease_until=now + timedelta(seconds=LEASE_DURATION_SECONDS)))
                if not claimed.rowcount:
                    return None
                work = session.get(Work, work_id, populate_existing=True)
                session.execute(update(Attempt).where(Attempt.work_id == work_id, Attempt.outcome == "STARTED").values(
                    outcome="LEASE_LOST", finished_at=now, error_code="LEASE_LOST"))
                session.add(Attempt(work_id=work_id, number=work.attempt_count,
                                    started_at=now, outcome="STARTED"))
                return token

    def process(self, work_id):
        result = _run_safely(self._process, work_id)
        if result is _PROCESS_FAILED:
            raise OrderReconciliationPersistenceError("reconciliation temporarily unavailable")
        return result

    def _process(self, work_id):
        token = self.claim(work_id)
        if token is None:
            return "NOT_CLAIMED"
        return self.process_claim(work_id, token)

    def process_due(self, *, limit=100):
        """One bounded dispatch pass; the caller schedules subsequent passes."""
        result = _run_safely(self._process_due, limit)
        if result is _PROCESS_FAILED:
            raise OrderReconciliationPersistenceError("reconciliation temporarily unavailable")
        return result

    def _process_due(self, limit):
        if not self._enabled:
            return []
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("invalid dispatch limit")
        now = self._now()
        with self._sessions() as session:
            ids = [row[0] for row in session.query(Work.id).filter(or_(
                and_(Work.status == "QUEUED", Work.next_attempt_at <= now),
                and_(Work.status == "PROCESSING", Work.lease_until <= _stale_lease_cutoff(now)),
            )).order_by(Work.next_attempt_at, Work.id).limit(limit).all()]
        return [(work_id, self.process(work_id)) for work_id in ids]

    def process_claim(self, work_id, token):
        """Resume a claimed work item; leases fence stale completion after crashes."""
        result = _run_safely(self._process_claim, work_id, token)
        if result is _PROCESS_FAILED:
            raise OrderReconciliationPersistenceError("reconciliation temporarily unavailable")
        return result

    def _process_claim(self, work_id, token):
        if not self._enabled:
            return "NOT_CLAIMED"
        context = None
        with self._sessions() as session:
            with session.begin():
                now = self._now()
                fenced = session.execute(update(Work).where(
                    Work.id == work_id, Work.status == "PROCESSING",
                    Work.lease_token == token, Work.lease_until > now,
                ).values(last_error=None))
                if not fenced.rowcount:
                    return "LEASE_LOST"
                work = session.get(Work, work_id, populate_existing=True)
                dispatched = session.execute(update(Attempt).where(
                    Attempt.work_id == work_id, Attempt.number == work.attempt_count,
                    Attempt.outcome == "STARTED", Attempt.dispatched_at.is_(None),
                ).values(dispatched_at=now))
                if not dispatched.rowcount:
                    return "NOT_CLAIMED"
                event = session.get(PSPEventRecord, work.event_id)
                context = _context(session, event)
                lease_until = work.lease_until
        if self._now() >= lease_until:
            return "LEASE_LOST"
        # No ORM session or transaction remains open for credential resolution/HTTP.
        if context is None:
            result, error = None, "UNMATCHED"
        else:
            result, error = _query(self._adapter, context)
            if result is not None and type(result) is not OrderSnapshot:
                result, error = None, "INVALID_RESPONSE"
        return self._finish(work_id, token, context, result, error)

    def _finish(self, work_id, token, context, result, error):
        now = self._now()
        with self._sessions() as session:
            with session.begin():
                work = session.query(Work).filter_by(id=work_id).populate_existing().with_for_update().one()
                now = self._now()
                if not _owned(work, token, now):
                    return "LEASE_LOST"
                lease_deadline = work.lease_until
                # SQLite needs a write fence as well; PostgreSQL has the row lock.
                fenced = session.execute(update(Work).where(
                    Work.id == work_id, Work.status == "PROCESSING",
                    Work.lease_token == token, Work.lease_until > now,
                ).values(last_error=error))
                if not fenced.rowcount:
                    return "LEASE_LOST"
                attempt = session.query(Attempt).filter_by(work_id=work_id, number=work.attempt_count).one()
                event = session.get(PSPEventRecord, work.event_id)
                if result is not None and _context(session, event) != context:
                    result, error = None, "CONTEXT_CHANGED"
                if result is not None:
                    # Serialize accumulated facts for distinct events of the same order.
                    session.query(PaymentOrder).filter_by(id=context.payment_order_id).populate_existing().with_for_update().one()
                    session.execute(update(PaymentOrder).where(PaymentOrder.id == context.payment_order_id).values(amount=PaymentOrder.amount))
                    now = self._now()
                    if not _owned(work, token, now):
                        return "LEASE_LOST"
                    snapshots = [row.snapshot for row in session.query(Evidence).filter_by(payment_order_id=context.payment_order_id).all()]
                    if not refunds_are_consistent(snapshots + [result.content], context.amount):
                        result, error = None, "REFUND_CONTRADICTION"
                if error in ("INVALID_RESPONSE", "CONTEXT_CHANGED", "REFUND_CONTRADICTION"):
                    quarantine(session, event.id, event.payload_hash, error, now)
                    work.status, attempt.outcome = "QUARANTINED", "QUARANTINED"
                elif error is not None:
                    work.last_error = error
                    if work.attempt_count == 8:
                        work.status, attempt.outcome = "EXHAUSTED", "EXHAUSTED"
                    else:
                        work.status, attempt.outcome = "QUEUED", "RETRY"
                        work.next_attempt_at = now + timedelta(seconds=RETRY_DELAYS[work.attempt_count - 1])
                else:
                    # Append facts, including older snapshots and reversals. No financial
                    # projection or contractual mutation can be regressed by event order.
                    timing = "AFTER_LOCAL_EXPIRY" if result.remote_created_at >= context.expires_at else "UNKNOWN"
                    if self._simulated_timing is not None and context.external_order_id.startswith("sim-"):
                        candidate = self._simulated_timing(result, context)
                        if candidate not in ("BEFORE_LOCAL_EXPIRY", "AFTER_LOCAL_EXPIRY", "UNKNOWN"):
                            raise ValueError("invalid simulated timing")
                        if timing != "AFTER_LOCAL_EXPIRY":
                            timing = candidate
                    insert_once(session, Evidence, dict(
                        payment_order_id=context.payment_order_id, event_id=event.id,
                        attempt_id=attempt.id, snapshot_hash=result.digest,
                        remote_updated_at=result.remote_updated_at, observed_at=now,
                        timing=timing, snapshot=result.content,
                    ), ["payment_order_id", "snapshot_hash"])
                    work.status, attempt.outcome = "DONE", "RECONCILED"
                    work.last_error = None
                # A quarantine/order lock can wait beyond the lease. Roll back
                # this entire completion; the abandoned attempt remains durable.
                if self._now() >= lease_deadline:
                    session.rollback()
                    return "LEASE_LOST"
                work.lease_token = work.lease_until = None
                attempt.finished_at, attempt.error_code = now, error
                return work.status


def _owned(work, token, now):
    return (work is not None and work.status == "PROCESSING"
            and work.lease_token == token and work.lease_until > now)


def _context(session, event):
    if event is None or event.provider != "mercadopago" or event.topic != "order":
        return None
    order = session.query(PaymentOrder).filter_by(
        provider=event.provider, live_mode=not event.test_mode,
        external_order_id=event.external_resource_id,
    ).populate_existing().one_or_none()
    if order is None:
        return None
    obligation = session.get(PaymentObligation, order.obligation_id, populate_existing=True)
    contract = session.get(ContractRequest, obligation.contract_request_id) if obligation is not None and obligation.contract_request_id is not None else None
    reservation = session.query(PaymentOrderReservation).filter_by(payment_order_id=order.id).one_or_none()
    if (contract is None or reservation is None or reservation.status != "SUCCEEDED"
            or reservation.obligation_id != obligation.id
            or order.professional_id != contract.professional_id
            or reservation.professional_id != order.professional_id
            or reservation.external_reference != order.external_reference
            or reservation.amount != order.amount or order.amount != obligation.amount
            or obligation.amount != contract.precio_acordado or order.currency != obligation.currency
            or order.currency != "ARS"):
        return None
    return OrderQueryContext(order.id, order.professional_id, order.external_order_id,
                             order.external_reference, order.amount, order.currency,
                             order.live_mode, order.expires_at)


def build_order_reconciliation_processor(*, app, session_factory, oauth_provider, transport=None, clock=utcnow):
    """Explicit trusted composition; a flag alone never supplies credentials."""
    from app.services.mercadopago_order_query_adapter import (
        MercadoPagoOrderQueryAdapter, UrllibMercadoPagoOrderQueryTransport,
    )
    processor = PaymentOrderReconciliationProcessor(
        session_factory=session_factory,
        adapter=MercadoPagoOrderQueryAdapter(oauth_provider, transport if transport is not None else UrllibMercadoPagoOrderQueryTransport()),
        enabled=app.config.get("MERCADOPAGO_ORDER_RECONCILIATION_ENABLED") is True,
        clock=clock,
    )
    app.extensions["payment_order_reconciliation_processor"] = processor
    return processor


def _stale_lease_cutoff(now):
    # lease_until is claim time + 60s; recovery starts at claim time + 120s.
    return now - timedelta(seconds=STALE_LEASE_RECOVERY_SECONDS - LEASE_DURATION_SECONDS)
