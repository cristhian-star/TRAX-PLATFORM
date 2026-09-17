from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import sessionmaker

from app.models.audit_log import AuditLog
from app.models.contract_request import ContractRequest
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.psp_payment_order_contract import PaymentOrderCreationUncertainError, PaymentOrderIdempotencyConflictError
from tests.alembic_head_validation import assert_database_at_repository_head
from tests.postgresql_payment_persistence_e2e import _create_guarded_engine
from tests.test_payment_order_application import seed_contract


class ThreadAwareSessionFactory:
    def __init__(self, engine):
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)
        self.local = threading.local()

    def __call__(self):
        owner = self
        session = self.Session()

        class Context:
            def __enter__(self):
                owner.local.open_sessions = getattr(owner.local, "open_sessions", 0) + 1
                return session

            def __exit__(self, *exc):
                try:
                    return session.__exit__(*exc)
                finally:
                    owner.local.open_sessions -= 1

        return Context()


class ObservingAdapter:
    def __init__(self, factory):
        self.factory = factory
        self.calls = 0
        self.lock = threading.Lock()
        self.callback = lambda command_value: None
        self.delegate = InMemoryPSPPaymentOrderCreationAdapter()

    def create_payment_order(self, command_value):
        assert self.factory.local.open_sessions == 0
        with self.lock:
            self.calls += 1
        self.callback(command_value)
        return self.delegate.create_payment_order(command_value)


class PostgreSQLPaymentOrderApplicationGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("TRAX_POSTGRES_PAYMENT_TEST_URL")
        cls.engine = _create_guarded_engine(cls.url, os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET"))
        cls.previous_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = cls.url
        cls.config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(cls.config, "head")
        with cls.engine.connect() as connection:
            revisions = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalars().all()
        assert_database_at_repository_head(cls.config, revisions)

    @classmethod
    def tearDownClass(cls):
        try:
            command.downgrade(cls.config, "base")
            with cls.engine.begin() as connection:
                connection.execute(sa.text("DROP TABLE alembic_version"))
            if sa.inspect(cls.engine).get_table_names():
                raise AssertionError("disposable database was not cleaned")
        finally:
            cls.engine.dispose()
            if cls.previous_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = cls.previous_url

    def setUp(self):
        with self.engine.begin() as connection:
            connection.execute(sa.text("TRUNCATE users, payment_obligations RESTART IDENTITY CASCADE"))
        self.factory = ThreadAwareSessionFactory(self.engine)
        self.actor, _, _, _, self.contract = seed_contract(self.factory.Session)
        self.adapter = ObservingAdapter(self.factory)
        self.now = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        self.service = self._service()

    def _service(self):
        return PaymentOrderApplicationService(
            session_factory=self.factory, adapter=self.adapter, clock=lambda: self.now
        )

    def _create(self, service=None):
        return (service or self.service).create_order(actor_user_id=self.actor, contract_request_id=self.contract)

    def _assert_counts(self, orders, audits):
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentObligation).count(), 1)
            self.assertEqual(session.query(PaymentOrderReservation).count(), 1)
            self.assertEqual(session.query(PaymentOrder).count(), orders)
            self.assertEqual(session.query(AuditLog).count(), audits)

    def test_concurrent_claim_makes_only_one_external_call(self):
        barrier = threading.Barrier(2)
        release = threading.Event()
        outcomes = []
        errors = []

        def block(command_value):
            if not release.wait(timeout=15):
                raise AssertionError("concurrent replay did not finish")

        self.adapter.callback = block

        def worker():
            try:
                barrier.wait(timeout=5)
                self._create(self._service())
                outcomes.append("succeeded")
            except PaymentOrderCreationUncertainError:
                outcomes.append("blocked")
                release.set()
            except BaseException as exc:
                errors.append(exc)
                release.set()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertCountEqual(outcomes, ["succeeded", "blocked"])
        self.assertEqual(self.adapter.calls, 1)
        self._assert_counts(1, 1)
        self._create(self._service())
        self.assertEqual(self.adapter.calls, 1)

    def test_uncertainty_blocks_restart_and_preserves_original_key(self):
        def uncertain(command_value):
            raise PaymentOrderCreationUncertainError("uncertain")

        self.adapter.callback = uncertain
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create()
        with self.factory.Session() as session:
            reservation = session.query(PaymentOrderReservation).one()
            key = reservation.idempotency_key
            self.assertEqual(reservation.status, "UNCERTAIN")
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create(self._service())
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().idempotency_key, key)
        self.assertEqual(self.adapter.calls, 1)
        self._assert_counts(0, 0)

    def test_crash_keeps_committed_claim_and_blocks_restart(self):
        def crash(command_value):
            self.assertEqual(self.engine.pool.checkedout(), 0)
            with self.factory.Session() as session:
                self.assertEqual(session.query(PaymentOrderReservation).one().status, "CALL_IN_PROGRESS")
            raise SystemExit("crash")

        self.adapter.callback = crash
        with self.assertRaises(SystemExit):
            self._create()
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create(self._service())
        self.assertEqual(self.adapter.calls, 1)
        self._assert_counts(0, 0)

    def test_finalization_rollback_is_atomic_and_keeps_uncertain_claim(self):
        import app.services.payment_order_persistence_service as persistence
        original = persistence._persist_new_record

        def fail(*args):
            original(*args)
            raise RuntimeError("failure after writes")

        with patch.object(persistence, "_persist_new_record", fail):
            with self.assertRaises(PaymentOrderCreationUncertainError):
                self._create()
        self._assert_counts(0, 0)
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self._create(self._service())
        self.assertEqual(self.adapter.calls, 1)

    def test_context_is_revalidated_after_external_call(self):
        def change_price(command_value):
            self.assertEqual(self.engine.pool.checkedout(), 0)
            with self.factory.Session.begin() as session:
                session.get(ContractRequest, self.contract).precio_acordado = Decimal("1250.51")

        self.adapter.callback = change_price
        with self.assertRaises(PaymentOrderIdempotencyConflictError):
            self._create()
        self._assert_counts(0, 0)
        self.assertEqual(self.adapter.calls, 1)

    def test_migration_roundtrip_preserves_order_and_does_not_backfill_context(self):
        self._create()
        with self.factory.Session.begin() as session:
            session.add(PaymentObligation(internal_reference="legacy", amount=Decimal("1"), currency="ARS"))
        with self.assertRaises(sa.exc.IntegrityError) as raised:
            with self.factory.Session.begin() as session:
                session.add(PaymentObligation(
                    contract_request_id=self.contract, internal_reference="duplicate",
                    amount=Decimal("1"), currency="ARS",
                ))
                session.flush()
        self.assertEqual(raised.exception.orig.diag.constraint_name, "uq_payment_obligations_contract_request")
        command.downgrade(self.config, "20260916_01")
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(sa.text("SELECT count(*) FROM payment_orders")).scalar_one(), 1)
            self.assertEqual(connection.execute(sa.text("SELECT count(*) FROM payment_obligations")).scalar_one(), 2)
        command.upgrade(self.config, "head")
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(sa.text(
                "SELECT count(*) FROM payment_obligations WHERE contract_request_id IS NULL"
            )).scalar_one(), 2)


if __name__ == "__main__":
    unittest.main()
