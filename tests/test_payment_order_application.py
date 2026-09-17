from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app import create_app, db
from app.config.config import TestingConfig
from app.models.audit_log import AuditLog
from app.models.contract_request import ContractRequest
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.models.professional import Professional
from app.models.user import User
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from app.services.payment_order_application_service import PaymentOrderApplicationService, PaymentOrderExpiredError
from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError,
    PaymentOrderCreationUncertainError,
    PaymentOrderIdempotencyConflictError,
)


class TrackingSessionFactory:
    def __init__(self, engine):
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)
        self.open_sessions = 0

    def __call__(self):
        owner = self
        session = self.Session()

        class Context:
            def __enter__(self):
                owner.open_sessions += 1
                return session

            def __exit__(self, *exc):
                try:
                    return session.__exit__(*exc)
                finally:
                    owner.open_sessions -= 1

        return Context()


class ObservingCreationAdapter:
    def __init__(self, factory, engine):
        self.factory = factory
        self.engine = engine
        self.calls = 0
        self.commands = []
        self.delegate = InMemoryPSPPaymentOrderCreationAdapter()
        self.callback = lambda command: None

    def create_payment_order(self, command):
        assert self.factory.open_sessions == 0
        assert self.engine.pool.checkedout() == 0
        self.calls += 1
        self.commands.append(command)
        self.callback(command)
        return self.delegate.create_payment_order(command)


class PaymentOrderApplicationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = (Path(self.temporary.name) / "application.db").as_posix()

        class LocalConfig(TestingConfig):
            @classmethod
            def apply_runtime_config(cls, app_config):
                super().apply_runtime_config(app_config)
                app_config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{path}"

        self.app = create_app(config_class=LocalConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.engine = db.engine
        self.factory = TrackingSessionFactory(self.engine)
        self.actor_id, self.client_id, self.intruder_id, self.professional_id, self.contract_id = seed_contract(self.factory.Session)
        self.now = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        self.adapter = ObservingCreationAdapter(self.factory, self.engine)
        self.service = self._service()

    def tearDown(self):
        db.session.remove()
        self.engine.dispose()
        self.context.pop()
        self.temporary.cleanup()

    def _service(self):
        return PaymentOrderApplicationService(
            session_factory=self.factory,
            adapter=self.adapter,
            clock=lambda: self.now,
        )

    def _create(self, actor=None, contract=None):
        return self.service.create_order(
            actor_user_id=self.actor_id if actor is None else actor,
            contract_request_id=self.contract_id if contract is None else contract,
        )

    def _counts(self):
        with self.factory.Session() as session:
            return tuple(session.query(model).count() for model in (
                PaymentObligation, PaymentOrderReservation, PaymentOrder, AuditLog
            ))

    def test_success_derives_price_context_and_command_and_replay_survives_restart(self):
        first = self._create()
        self.assertEqual(first.amount, Decimal("1250.50"))
        self.assertEqual(first.currency, "ARS")
        self.assertEqual(first.expires_at, first.created_at + timedelta(hours=72))
        self.assertEqual(self.adapter.commands[0].professional_id, self.professional_id)
        self.assertEqual(self._counts(), (1, 1, 1, 1))
        self.now += timedelta(hours=1)
        self.service = self._service()
        with patch.object(self.service, "_ids", side_effect=AssertionError("must not regenerate")):
            replay = self._create()
        self.assertEqual(replay, first)
        self.assertEqual(self.adapter.calls, 1)
        with self.factory.Session() as session:
            obligation = session.query(PaymentObligation).one()
            reservation = session.query(PaymentOrderReservation).one()
            self.assertEqual(obligation.contract_request_id, self.contract_id)
            self.assertEqual(reservation.status, "SUCCEEDED")

    def test_expired_replay_does_not_deliver_checkout_or_call_adapter(self):
        first = self._create()
        self.now = first.expires_at
        with self.assertRaises(PaymentOrderExpiredError):
            self._create()
        self.assertEqual(self.adapter.calls, 1)
        self.assertEqual(self._counts(), (1, 1, 1, 1))

    def test_actor_adversarial_cases_make_no_reservation_or_adapter_call(self):
        for actor in (self.client_id, self.intruder_id, 999999, None, True, "1"):
            with self.subTest(actor=actor), self.assertRaises(PermissionError):
                self.service.create_order(actor_user_id=actor, contract_request_id=self.contract_id)
        self.assertEqual(self._counts(), (0, 0, 0, 0))
        self.assertEqual(self.adapter.calls, 0)

    def test_inactive_or_wrong_role_actor_is_rejected(self):
        for changes in ({"estado": "SUSPENDIDO"}, {"rol": "ADMIN"}):
            with self.factory.Session.begin() as session:
                actor = session.get(User, self.actor_id)
                actor.estado = "ACTIVO"
                actor.rol = "PROFESIONAL"
                for key, value in changes.items():
                    setattr(actor, key, value)
            with self.subTest(changes=changes), self.assertRaises(PermissionError):
                self._create()
        self.assertEqual(self.adapter.calls, 0)

    def test_contract_and_professional_ownership_must_both_match(self):
        for target in ("contract", "profile"):
            with self.factory.Session.begin() as session:
                contract = session.get(ContractRequest, self.contract_id)
                profile = session.get(Professional, self.professional_id)
                contract.professional_user_id = self.actor_id
                profile.user_id = self.actor_id
                if target == "contract":
                    contract.professional_user_id = self.intruder_id
                else:
                    profile.user_id = self.intruder_id
            with self.subTest(target=target), self.assertRaises(PermissionError):
                self._create()
        with self.assertRaises(PermissionError):
            self._create(contract=999999)
        self.assertEqual(self._counts(), (0, 0, 0, 0))

    def test_every_non_confirmed_contract_state_is_rejected(self):
        for state in ContractRequest.ESTADOS:
            if state == "CONFIRMADA":
                continue
            with self.factory.Session.begin() as session:
                session.get(ContractRequest, self.contract_id).estado = state
            with self.subTest(state=state), self.assertRaises(PermissionError):
                self._create()
        self.assertEqual(self.adapter.calls, 0)
        self.assertEqual(self._counts(), (0, 0, 0, 0))

    def test_missing_zero_or_negative_agreed_price_is_rejected_before_call(self):
        for price in (None, Decimal("0"), Decimal("-1")):
            with self.factory.Session.begin() as session:
                session.get(ContractRequest, self.contract_id).precio_acordado = price
            with self.subTest(price=price), self.assertRaises(InvalidPaymentOrderCreationRequestError):
                self._create()
        self.assertEqual(self._counts(), (0, 0, 0, 0))
        self.assertEqual(self.adapter.calls, 0)

    def test_caller_cannot_supply_amount_or_professional_id(self):
        for key in ("amount", "professional_id"):
            with self.subTest(key=key), self.assertRaises(TypeError):
                self.service.create_order(
                    actor_user_id=self.actor_id,
                    contract_request_id=self.contract_id,
                    **{key: 1},
                )
        self.assertEqual(self.adapter.calls, 0)

    def test_price_change_on_replay_conflicts_without_another_call(self):
        self._create()
        with self.factory.Session.begin() as session:
            session.get(ContractRequest, self.contract_id).precio_acordado = Decimal("1250.51")
        with self.assertRaises(PaymentOrderIdempotencyConflictError):
            self._create()
        self.assertEqual(self.adapter.calls, 1)

    def test_uncertain_adapter_response_is_durable_and_blocks_replay(self):
        def uncertain(command):
            raise PaymentOrderCreationUncertainError("external uncertainty")

        self.adapter.callback = uncertain
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create()
        self.assertEqual(self._counts(), (1, 1, 0, 0))
        with self.factory.Session() as session:
            original = session.query(PaymentOrderReservation).one()
            key = original.idempotency_key
            self.assertEqual(original.status, "UNCERTAIN")
        self.service = self._service()
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create()
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().idempotency_key, key)
        self.assertEqual(self.adapter.calls, 1)

    def test_crash_after_committed_claim_blocks_a_new_service_instance(self):
        def crash(command):
            with self.factory.Session() as session:
                self.assertEqual(session.query(PaymentOrderReservation).one().status, "CALL_IN_PROGRESS")
            raise SystemExit("process stopped")

        self.adapter.callback = crash
        with self.assertRaises(SystemExit):
            self._create()
        self.service = self._service()
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create()
        self.assertEqual(self._counts(), (1, 1, 0, 0))
        self.assertEqual(self.adapter.calls, 1)

    def test_invalid_echo_is_uncertain_and_cannot_write_order(self):
        with patch.object(self.adapter, "create_payment_order", side_effect=lambda command: replace(
            self.adapter.delegate.create_payment_order(command), concept="Different concept"
        )):
            with self.assertRaises(PaymentOrderCreationUncertainError):
                self._create()
        self.assertEqual(self._counts(), (1, 1, 0, 0))

    def test_finalization_failure_rolls_back_order_and_audit_but_keeps_claim(self):
        import app.services.payment_order_persistence_service as persistence
        original = persistence._persist_new_record

        def fail_after_writes(*args):
            original(*args)
            raise RuntimeError("failed after order and audit flush")

        with patch.object(persistence, "_persist_new_record", fail_after_writes):
            with self.assertRaises(PaymentOrderCreationUncertainError):
                self._create()
        self.assertEqual(self._counts(), (1, 1, 0, 0))
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().status, "CALL_IN_PROGRESS")
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create()
        self.assertEqual(self.adapter.calls, 1)

    def test_first_transaction_failure_rolls_back_obligation_and_reservation(self):
        with patch.object(self.service, "_ids", return_value="unsafe value"):
            with self.assertRaises(InvalidPaymentOrderCreationRequestError):
                self._create()
        self.assertEqual(self._counts(), (0, 0, 0, 0))
        self.assertEqual(self.adapter.calls, 0)

    def test_contract_obligation_is_unique_and_legacy_rows_remain_unlinked(self):
        self._create()
        with self.factory.Session.begin() as session:
            session.add(PaymentObligation(internal_reference="legacy", amount=Decimal("1"), currency="ARS"))
        with self.assertRaises(IntegrityError):
            with self.factory.Session.begin() as session:
                session.add(PaymentObligation(
                    contract_request_id=self.contract_id,
                    internal_reference="duplicate-contract", amount=Decimal("1"), currency="ARS",
                ))
                session.flush()
        with self.factory.Session() as session:
            self.assertIsNone(session.query(PaymentObligation).filter_by(internal_reference="legacy").one().contract_request_id)

    def test_adapter_observes_no_open_session_or_checked_out_connection(self):
        self._create()
        self.assertEqual(self.factory.open_sessions, 0)
        self.assertEqual(self.adapter.calls, 1)
        self.assertEqual(self.engine.pool.checkedout(), 0)


def seed_contract(Session):
    with Session.begin() as session:
        actor = User(nombre="Pro", email="pro@app.test", password="hash", rol="PROFESIONAL")
        client = User(nombre="Client", email="client@app.test", password="hash", rol="CLIENTE")
        intruder = User(nombre="Intruder", email="intruder@app.test", password="hash", rol="PROFESIONAL")
        session.add_all((actor, client, intruder))
        session.flush()
        professional = Professional(user_id=actor.id, nombre="Pro", servicio="Service", zona="CABA")
        session.add(professional)
        session.flush()
        contract = ContractRequest(
            cliente_id=client.id, professional_id=professional.id,
            professional_user_id=actor.id, servicio="Sensitive service description",
            estado="CONFIRMADA", precio_acordado=Decimal("1250.50"),
        )
        session.add(contract)
        session.flush()
        return actor.id, client.id, intruder.id, professional.id, contract.id


if __name__ == "__main__":
    unittest.main()
