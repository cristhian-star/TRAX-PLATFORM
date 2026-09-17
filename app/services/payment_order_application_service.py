from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.models.contract_request import ContractRequest
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.models.professional import Professional
from app.services.actor_policy_service import require_active_actor
from app.services.payment_order_persistence_service import register_or_get_payment_order
from app.services.psp_payment_order_contract import (
    PaymentOrderCreationCommand,
    PaymentOrderCreationResult,
    PaymentOrderCreationUncertainError,
    PaymentOrderIdempotencyConflictError,
    validate_payment_order_creation_result,
)


def _utcnow():
    return datetime.now(timezone.utc)


class PaymentOrderApplicationService:
    """Reserve and claim durably before a single, session-free creation call.

    CALL_IN_PROGRESS is deliberately never reclaimed: a crash cannot prove
    whether the external operation happened. Terminal replays keep history;
    renewal and recovery belong to future explicitly authorized operations.
    The factory must return fresh, dedicated sessions, not a caller's session.
    """

    def __init__(self, *, session_factory, adapter, clock=_utcnow, id_factory=uuid4):
        if not callable(session_factory) or not callable(clock) or not callable(id_factory):
            raise TypeError("invalid payment order application configuration")
        if not callable(getattr(adapter, "create_payment_order", None)):
            raise TypeError("invalid payment order creation adapter")
        self._sessions = session_factory
        self._adapter = adapter
        self._clock = clock
        self._ids = id_factory

    def create_order(self, *, actor_user_id, contract_request_id):
        _require_identifiers(actor_user_id, contract_request_id)
        reservation_id, command, stored = self._prepare(actor_user_id, contract_request_id)
        if stored is not None:
            return stored

        result = _external_result(self._adapter, command)
        if result is None:
            self._mark_uncertain(reservation_id)
            raise PaymentOrderCreationUncertainError("payment order creation requires recovery")

        completed = self._complete_safely(
            actor_user_id, contract_request_id, reservation_id, command, result
        )
        if completed is None:
            # The initial committed claim survives the rolled-back completion.
            raise PaymentOrderCreationUncertainError("payment order creation requires recovery")
        return completed

    def _prepare(self, actor_id, contract_id):
        with self._sessions() as session:
            with session.begin():
                contract = _authorized_contract(session, actor_id, contract_id)
                obligation = session.query(PaymentObligation).filter_by(
                    contract_request_id=contract.id
                ).populate_existing().with_for_update().one_or_none()
                reservation = None
                if obligation is not None:
                    _same_price(obligation, contract)
                    reservation = session.query(PaymentOrderReservation).filter_by(
                        obligation_id=obligation.id
                    ).populate_existing().with_for_update().one_or_none()
                if reservation is not None:
                    command = _command(reservation)
                    _same_reservation(reservation, obligation, contract, actor_id)
                    if reservation.status == "SUCCEEDED":
                        order = session.get(PaymentOrder, reservation.payment_order_id)
                        if order is None:
                            raise PaymentOrderIdempotencyConflictError("payment order reservation conflict")
                        return reservation.id, command, _stored_result(order)
                    if reservation.status != "PREPARED":
                        raise PaymentOrderCreationUncertainError("payment order creation requires recovery")
                else:
                    created = _read_clock(self._clock)
                    reference = (
                        obligation.internal_reference if obligation is not None
                        else f"obligation-{self._ids()}"
                    )
                    command = PaymentOrderCreationCommand(
                        local_order_id=f"order-{self._ids()}",
                        obligation_reference=reference,
                        professional_id=contract.professional_id,
                        amount=contract.precio_acordado,
                        currency="ARS",
                        concept="Cobro de servicio acordado",
                        external_reference=f"reference-{self._ids()}",
                        idempotency_key=f"creation-{self._ids()}",
                        created_at=created,
                        expires_at=created + timedelta(hours=72),
                    )
                    if obligation is None:
                        obligation = PaymentObligation(
                            contract_request_id=contract.id,
                            internal_reference=reference,
                            amount=command.amount,
                            currency=command.currency,
                        )
                        session.add(obligation)
                        session.flush()
                    reservation = PaymentOrderReservation(
                        obligation_id=obligation.id,
                        actor_user_id=actor_id,
                        **_command_columns(command),
                        status="PREPARED",
                    )
                    session.add(reservation)
                reservation.status = "CALL_IN_PROGRESS"
                session.flush()
                return reservation.id, command, None

    def _mark_uncertain(self, reservation_id):
        with self._sessions() as session:
            with session.begin():
                reservation = session.query(PaymentOrderReservation).filter_by(
                    id=reservation_id
                ).populate_existing().with_for_update().one()
                if reservation.status == "CALL_IN_PROGRESS":
                    reservation.status = "UNCERTAIN"
                    reservation.finished_at = _read_clock(self._clock).replace(tzinfo=None)
                    session.flush()

    def _complete_safely(self, actor_id, contract_id, reservation_id, command, result):
        try:
            with self._sessions() as session:
                with session.begin():
                    contract = _authorized_contract(session, actor_id, contract_id)
                    obligation = session.query(PaymentObligation).filter_by(
                        contract_request_id=contract.id
                    ).populate_existing().with_for_update().one()
                    reservation = session.query(PaymentOrderReservation).filter_by(
                        id=reservation_id
                    ).populate_existing().with_for_update().one()
                    _same_price(obligation, contract)
                    _same_reservation(reservation, obligation, contract, actor_id)
                    if reservation.status != "CALL_IN_PROGRESS" or _command(reservation) != command:
                        raise PaymentOrderIdempotencyConflictError("payment order reservation conflict")
                    order = register_or_get_payment_order(
                        session, obligation.id, command, result,
                        actor_user_id=actor_id, clock=self._clock,
                    )
                    reservation.status = "SUCCEEDED"
                    reservation.payment_order_id = order.id
                    reservation.finished_at = _read_clock(self._clock).replace(tzinfo=None)
                    session.flush()
                    stored = _stored_result(order)
            return stored
        except (PermissionError, PaymentOrderIdempotencyConflictError):
            raise
        except Exception:
            return None


def _require_identifiers(actor_id, contract_id):
    if type(actor_id) is not int or actor_id <= 0:
        raise PermissionError("authenticated professional required")
    if type(contract_id) is not int or contract_id <= 0:
        raise ValueError("invalid contract identifier")


def _authorized_contract(session, actor_id, contract_id):
    actor = require_active_actor(actor_id, ("PROFESIONAL",), session=session)
    contract = session.query(ContractRequest).filter_by(id=contract_id).populate_existing().with_for_update().one_or_none()
    if contract is None:
        raise PermissionError("contract is not authorized for payment order creation")
    professional = session.get(Professional, contract.professional_id)
    if (
        contract.professional_user_id != actor.id
        or professional is None or professional.user_id != actor.id
        or contract.estado != "CONFIRMADA"
    ):
        raise PermissionError("contract is not authorized for payment order creation")
    return contract


def _same_price(obligation, contract):
    if obligation.amount != contract.precio_acordado or obligation.currency != "ARS":
        raise PaymentOrderIdempotencyConflictError("final payment obligation conflict")


def _same_reservation(reservation, obligation, contract, actor_id):
    if (
        reservation.obligation_id != obligation.id
        or reservation.actor_user_id != actor_id
        or reservation.professional_id != contract.professional_id
        or reservation.obligation_reference != obligation.internal_reference
        or reservation.amount != obligation.amount or reservation.currency != obligation.currency
    ):
        raise PaymentOrderIdempotencyConflictError("payment order reservation conflict")


def _read_clock(clock):
    value = clock()
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("invalid payment order application clock")
    return value.astimezone(timezone.utc)


def _command_columns(command):
    return {
        "local_order_id": command.local_order_id,
        "obligation_reference": command.obligation_reference,
        "professional_id": command.professional_id,
        "amount": command.amount,
        "currency": command.currency,
        "concept": command.concept,
        "external_reference": command.external_reference,
        "idempotency_key": command.idempotency_key,
        "created_at": command.created_at.replace(tzinfo=None),
        "expires_at": command.expires_at.replace(tzinfo=None),
    }


def _command(reservation):
    values = {name: getattr(reservation, name) for name in (
        "local_order_id", "obligation_reference", "professional_id", "amount", "currency",
        "concept", "external_reference", "idempotency_key", "created_at", "expires_at",
    )}
    values["created_at"] = values["created_at"].replace(tzinfo=timezone.utc)
    values["expires_at"] = values["expires_at"].replace(tzinfo=timezone.utc)
    values["amount"] = _stored_amount(values["amount"])
    return PaymentOrderCreationCommand(**values)


def _stored_amount(value):
    # SQLAlchemy's unconstrained Numeric adds trailing fractional zeros on read.
    # Remove only those zeros: never round a nonzero fractional digit.
    if type(value) is not Decimal or not value.is_finite():
        raise PaymentOrderIdempotencyConflictError("stored payment order amount conflict")
    sign, digits, exponent = value.as_tuple()
    while exponent < -2 and digits[-1] == 0:
        digits = digits[:-1]
        exponent += 1
    return Decimal((sign, digits, exponent))


def _external_result(adapter, command):
    try:
        return validate_payment_order_creation_result(command, adapter.create_payment_order(command))
    except Exception:
        return None


def _stored_result(order):
    values = {name: getattr(order, name) for name in (
        "local_order_id", "external_reference", "amount", "currency", "concept",
        "idempotency_key", "external_order_id", "checkout_url", "provider", "live_mode",
    )}
    values["amount"] = _stored_amount(values["amount"])
    return PaymentOrderCreationResult(
        **values,
        obligation_reference=order.obligation.internal_reference,
        created_at=order.created_at.replace(tzinfo=timezone.utc),
        expires_at=order.expires_at.replace(tzinfo=timezone.utc),
    )
