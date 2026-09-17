from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.services.payment_persistence_service import _is_postgresql_constraint_violation
from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError,
    InvalidPaymentOrderCreationResultError,
    PaymentOrderCreationCommand,
    PaymentOrderCreationResult,
    PaymentOrderIdempotencyConflictError,
    validate_payment_order_creation_result,
)


IDEMPOTENCY_CONSTRAINT = "uq_payment_orders_idempotency_key"
ACTIVE_OBLIGATION_CONSTRAINT = "uq_payment_orders_active_obligation"


def _utcnow():
    return datetime.now(timezone.utc)


class PaymentOrderNotFoundError(LookupError):
    pass


class ActivePaymentOrderExistsError(ValueError):
    pass


def register_or_get_payment_order(
    session, obligation_id, command, result, *, actor_user_id, clock=_utcnow
):
    _validate_inputs(command, result, actor_user_id)
    obligation = _lock_obligation(session, obligation_id)
    _require_obligation_matches(obligation, command)
    existing = session.query(PaymentOrder).filter_by(
        idempotency_key=command.idempotency_key
    ).one_or_none()
    if existing is not None:
        return _matching_order(existing, obligation.id, command, result)

    now = _read_clock(clock)
    _expire_due_active(session, obligation.id, now, actor_user_id)
    if _active_query(session, obligation.id, now).first() is not None:
        raise ActivePaymentOrderExistsError("an active payment order already exists")

    status = "ACTIVE" if now < _naive_utc(command.expires_at) else "EXPIRED"
    record = _new_record(obligation.id, command, result, status)
    if status == "EXPIRED":
        record.closed_at = record.expires_at
    try:
        if session.get_bind().dialect.name == "postgresql":
            with session.begin_nested():
                _persist_new_record(session, record, actor_user_id, status)
        else:
            _persist_new_record(session, record, actor_user_id, status)
        return record
    except IntegrityError as exc:
        if _is_postgresql_constraint_violation(exc, "23505", IDEMPOTENCY_CONSTRAINT):
            existing = session.query(PaymentOrder).filter_by(
                idempotency_key=command.idempotency_key
            ).one_or_none()
            if existing is None:
                raise
            return _matching_order(existing, obligation.id, command, result)
        if _is_postgresql_constraint_violation(exc, "23505", ACTIVE_OBLIGATION_CONSTRAINT):
            raise ActivePaymentOrderExistsError(
                "an active payment order already exists"
            ) from None
        raise


def get_payment_order(session, order_id):
    record = session.get(PaymentOrder, order_id)
    if record is None:
        raise PaymentOrderNotFoundError("payment order not found")
    return record


def get_active_payment_order(session, obligation_id, *, clock=_utcnow):
    now = _read_clock(clock)
    return _active_query(session, obligation_id, now).one_or_none()


def materialize_payment_order_expiration(
    session, order_id, *, actor_user_id, clock=_utcnow
):
    stub = get_payment_order(session, order_id)
    _lock_obligation(session, stub.obligation_id)
    now = _read_clock(clock)
    record = _locked_current_order(session, order_id)
    if record.status == "ACTIVE" and now >= record.expires_at:
        _mark_expired(session, record, actor_user_id)
        session.flush()
    return record


def cancel_payment_order(session, order_id, *, actor_user_id, clock=_utcnow):
    stub = get_payment_order(session, order_id)
    _lock_obligation(session, stub.obligation_id)
    now = _read_clock(clock)
    record = _locked_current_order(session, order_id)
    if record.status == "ACTIVE" and now >= record.expires_at:
        _mark_expired(session, record, actor_user_id)
    elif record.status == "ACTIVE":
        record.status = "CANCELLED"
        record.cancelled_at = now
        record.closed_at = now
        record.updated_at = now
        _add_audit(session, record, actor_user_id, "PAYMENT_ORDER_CANCELLED")
    session.flush()
    return record


def _validate_inputs(command, result, actor_user_id):
    if type(command) is not PaymentOrderCreationCommand:
        raise InvalidPaymentOrderCreationRequestError("invalid payment order creation request")
    if type(result) is not PaymentOrderCreationResult:
        raise InvalidPaymentOrderCreationResultError("invalid payment order creation result")
    if type(actor_user_id) is not int or actor_user_id <= 0:
        raise InvalidPaymentOrderCreationRequestError("invalid payment order creation request")
    validate_payment_order_creation_result(command, result)


def _lock_obligation(session, obligation_id):
    obligation = session.query(PaymentObligation).filter_by(
        id=obligation_id
    ).with_for_update().one_or_none()
    if obligation is None:
        raise PaymentOrderNotFoundError("payment obligation not found")
    return obligation


def _locked_current_order(session, order_id):
    return (
        session.query(PaymentOrder)
        .filter_by(id=order_id)
        .populate_existing()
        .with_for_update()
        .one()
    )


def _require_obligation_matches(obligation, command):
    if (
        obligation.internal_reference != command.obligation_reference
        or Decimal(obligation.amount) != command.amount
        or obligation.currency != command.currency
    ):
        raise PaymentOrderIdempotencyConflictError(
            "payment order does not match obligation"
        )


def _read_clock(clock):
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise InvalidPaymentOrderCreationRequestError("invalid payment order creation request")
    return _naive_utc(value)


def _naive_utc(value):
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _active_query(session, obligation_id, now):
    return session.query(PaymentOrder).filter(
        PaymentOrder.obligation_id == obligation_id,
        PaymentOrder.status == "ACTIVE",
        PaymentOrder.expires_at > now,
    )


def _expire_due_active(session, obligation_id, now, actor_user_id):
    due = session.query(PaymentOrder).filter(
        PaymentOrder.obligation_id == obligation_id,
        PaymentOrder.status == "ACTIVE",
        PaymentOrder.expires_at <= now,
    ).with_for_update().all()
    for record in due:
        _mark_expired(session, record, actor_user_id)
    if due:
        session.flush()


def _mark_expired(session, record, actor_user_id):
    if record.status != "ACTIVE":
        return
    record.status = "EXPIRED"
    record.closed_at = record.expires_at
    record.updated_at = record.expires_at
    _add_audit(session, record, actor_user_id, "PAYMENT_ORDER_EXPIRED")


def _new_record(obligation_id, command, result, status):
    return PaymentOrder(
        obligation_id=obligation_id,
        professional_id=command.professional_id,
        local_order_id=command.local_order_id,
        external_reference=command.external_reference,
        idempotency_key=command.idempotency_key,
        amount=command.amount,
        currency=command.currency,
        concept=command.concept,
        provider=result.provider,
        live_mode=result.live_mode,
        external_order_id=result.external_order_id,
        checkout_url=result.checkout_url,
        status=status,
        created_at=_naive_utc(command.created_at),
        expires_at=_naive_utc(command.expires_at),
    )


def _persist_new_record(session, record, actor_user_id, status):
    session.add(record)
    session.flush()
    _add_audit(session, record, actor_user_id, "PAYMENT_ORDER_CREATED")
    if status == "EXPIRED":
        _add_audit(session, record, actor_user_id, "PAYMENT_ORDER_EXPIRED")
    session.flush()


def _matching_order(record, obligation_id, command, result):
    expected = (
        obligation_id, command.professional_id, command.local_order_id,
        command.external_reference, command.idempotency_key, command.amount,
        command.currency, command.concept, result.provider, result.live_mode,
        result.external_order_id, result.checkout_url,
        _naive_utc(command.created_at), _naive_utc(command.expires_at),
    )
    actual = (
        record.obligation_id, record.professional_id, record.local_order_id,
        record.external_reference, record.idempotency_key, Decimal(record.amount),
        record.currency, record.concept, record.provider, record.live_mode,
        record.external_order_id, record.checkout_url,
        record.created_at, record.expires_at,
    )
    if actual != expected:
        raise PaymentOrderIdempotencyConflictError(
            "payment order idempotency conflict"
        )
    return record


def _add_audit(session, record, actor_user_id, action):
    session.add(AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        description="Payment order lifecycle transition",
        entity_type="payment_order",
        entity_id=record.id,
        operation=action,
        metadata_json={"status": record.status},
    ))
