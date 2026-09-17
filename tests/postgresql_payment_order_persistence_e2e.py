import os
import sys
import threading
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.audit_log import AuditLog
from app.models.payment_order import PaymentOrder
from app.services.in_memory_psp_payment_order_creation_adapter import (
    InMemoryPSPPaymentOrderCreationAdapter,
)
from app.services.payment_order_persistence_service import (
    ActivePaymentOrderExistsError,
    cancel_payment_order,
    register_or_get_payment_order,
)
from app.services.psp_payment_order_contract import (
    PaymentOrderCreationCommand,
    PaymentOrderIdempotencyConflictError,
)
from tests.alembic_head_validation import assert_database_at_repository_head
from tests.postgresql_payment_persistence_e2e import _create_guarded_engine


class PostgreSQLPaymentOrderPersistenceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("TRAX_POSTGRES_PAYMENT_TEST_URL")
        cls.engine = _create_guarded_engine(
            cls.url, os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET")
        )
        cls.config = Config(str(PROJECT_ROOT / "alembic.ini"))
        cls.previous_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = cls.url
        command.upgrade(cls.config, "head")
        with cls.engine.connect() as connection:
            revisions = connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalars().all()
        assert_database_at_repository_head(cls.config, revisions)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)

    @classmethod
    def tearDownClass(cls):
        try:
            command.downgrade(cls.config, "base")
            with cls.engine.begin() as connection:
                connection.execute(sa.text("DROP TABLE alembic_version"))
            if sa.inspect(cls.engine).get_table_names():
                raise AssertionError("la base descartable no quedo limpia")
        finally:
            cls.engine.dispose()
            if cls.previous_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = cls.previous_url

    def setUp(self):
        with self.engine.begin() as connection:
            connection.execute(sa.text(
                "TRUNCATE TABLE payment_orders, audit_logs, payment_attempts, "
                "payment_obligations, professionals, users RESTART IDENTITY CASCADE"
            ))
            self.actor_id = connection.execute(sa.text(
                "INSERT INTO users (nombre,email,password,rol,estado) "
                "VALUES ('Operator','operator@example.test','hash','ADMIN','ACTIVO') "
                "RETURNING id"
            )).scalar_one()
            user_id = connection.execute(sa.text(
                "INSERT INTO users (nombre,email,password,rol,estado) "
                "VALUES ('Pro','pro@example.test','hash','PROFESIONAL','ACTIVO') "
                "RETURNING id"
            )).scalar_one()
            self.professional_id = connection.execute(sa.text(
                "INSERT INTO professionals (user_id,nombre,servicio,zona,"
                "whatsapp_contact_preference,estado_perfil,perfil_completo) "
                "VALUES (:user_id,'Pro','Service','CABA','AUTO','INCOMPLETO',false) "
                "RETURNING id"
            ), {"user_id": user_id}).scalar_one()
            self.obligation_id = connection.execute(sa.text(
                "INSERT INTO payment_obligations "
                "(internal_reference,amount,currency,created_at) "
                "VALUES ('obligation-0001',1250.50,'ARS',now()) RETURNING id"
            )).scalar_one()
            self.second_obligation_id = connection.execute(sa.text(
                "INSERT INTO payment_obligations "
                "(internal_reference,amount,currency,created_at) "
                "VALUES ('obligation-0002',1250.50,'ARS',now()) RETURNING id"
            )).scalar_one()
        self.created_at = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)

    def _command(
        self,
        suffix="0001",
        *,
        obligation_reference="obligation-0001",
        local_order_id=None,
        external_reference=None,
        idempotency_key=None,
    ):
        return PaymentOrderCreationCommand(
            local_order_id=local_order_id or f"local-order-{suffix}",
            obligation_reference=obligation_reference,
            professional_id=self.professional_id,
            amount=Decimal("1250.50"),
            currency="ARS",
            concept="Servicio acordado",
            external_reference=external_reference or f"external-reference-{suffix}",
            idempotency_key=idempotency_key or f"private-idempotency-key-{suffix}",
            created_at=self.created_at,
            expires_at=self.created_at + timedelta(hours=72),
        )

    @staticmethod
    def _result(command):
        return InMemoryPSPPaymentOrderCreationAdapter().create_payment_order(command)

    def test_concurrent_identical_replay_converges_to_one_order_and_one_audit(self):
        command_value = self._command()
        barrier = threading.Barrier(2)
        ids = []
        errors = []

        def worker():
            session = self.Session()
            try:
                barrier.wait(timeout=5)
                record = register_or_get_payment_order(
                    session,
                    self.obligation_id,
                    command_value,
                    self._result(command_value),
                    actor_user_id=self.actor_id,
                    clock=lambda: self.created_at,
                )
                session.commit()
                ids.append(record.id)
            except BaseException as exc:
                session.rollback()
                errors.append(exc)
            finally:
                session.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertEqual(len(set(ids)), 1)
        with self.Session() as session:
            self.assertEqual(session.query(PaymentOrder).count(), 1)
            self.assertEqual(session.query(AuditLog).count(), 1)

    def test_concurrent_distinct_orders_leave_one_active_order(self):
        barrier = threading.Barrier(2)
        outcomes = []

        def worker(suffix):
            session = self.Session()
            command_value = self._command(suffix)
            try:
                barrier.wait(timeout=5)
                register_or_get_payment_order(
                    session,
                    self.obligation_id,
                    command_value,
                    self._result(command_value),
                    actor_user_id=self.actor_id,
                    clock=lambda: self.created_at,
                )
                session.commit()
                outcomes.append("created")
            except ActivePaymentOrderExistsError:
                session.rollback()
                outcomes.append("active-conflict")
            finally:
                session.close()

        threads = [threading.Thread(target=worker, args=(suffix,)) for suffix in ("0001", "0002")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertCountEqual(outcomes, ["created", "active-conflict"])
        with self.Session() as session:
            self.assertEqual(session.query(PaymentOrder).filter_by(status="ACTIVE").count(), 1)

    def test_same_idempotency_key_across_obligations_has_one_winner_and_domain_conflict(self):
        barrier = threading.Barrier(2)
        outcomes = []
        commands = (
            (self.obligation_id, self._command("shared", local_order_id="local-shared-a")),
            (
                self.second_obligation_id,
                self._command(
                    "shared-b",
                    obligation_reference="obligation-0002",
                    local_order_id="local-shared-b",
                    idempotency_key="private-idempotency-key-shared",
                ),
            ),
        )

        def worker(obligation_id, command_value):
            session = self.Session()
            try:
                barrier.wait(timeout=5)
                result = replace(
                    self._result(command_value),
                    external_order_id=f"provider-{command_value.local_order_id}",
                )
                register_or_get_payment_order(
                    session,
                    obligation_id,
                    command_value,
                    result,
                    actor_user_id=self.actor_id,
                    clock=lambda: self.created_at,
                )
                session.commit()
                outcomes.append("created")
            except PaymentOrderIdempotencyConflictError:
                session.rollback()
                outcomes.append("idempotency-conflict")
            except BaseException as exc:
                session.rollback()
                outcomes.append(type(exc).__name__)
            finally:
                session.close()

        threads = [
            threading.Thread(target=worker, args=values) for values in commands
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertCountEqual(outcomes, ["created", "idempotency-conflict"])
        with self.Session() as session:
            self.assertEqual(session.query(PaymentOrder).count(), 1)

    def test_unrecognized_unique_violation_is_not_interpreted_as_replay(self):
        first = self._command("first", local_order_id="duplicated-local-order")
        second = self._command(
            "second",
            obligation_reference="obligation-0002",
            local_order_id="duplicated-local-order",
        )
        with self.Session.begin() as session:
            register_or_get_payment_order(
                session,
                self.obligation_id,
                first,
                self._result(first),
                actor_user_id=self.actor_id,
                clock=lambda: self.created_at,
            )
        session = self.Session()
        try:
            with self.assertRaises(sa.exc.IntegrityError) as raised:
                register_or_get_payment_order(
                    session,
                    self.second_obligation_id,
                    second,
                    self._result(second),
                    actor_user_id=self.actor_id,
                    clock=lambda: self.created_at,
                )
            self.assertEqual(
                getattr(raised.exception.orig, "sqlstate", None)
                or getattr(raised.exception.orig, "pgcode", None),
                "23505",
            )
            self.assertEqual(
                raised.exception.orig.diag.constraint_name,
                "uq_payment_orders_local_order_id",
            )
        finally:
            session.rollback()
            session.close()

    def test_migrated_state_constraint_rejects_each_invalid_null_shape_independently(self):
        command_value = self._command()
        with self.Session.begin() as session:
            order = register_or_get_payment_order(
                session,
                self.obligation_id,
                command_value,
                self._result(command_value),
                actor_user_id=self.actor_id,
                clock=lambda: self.created_at,
            )
            order_id = order.id
        one_hour = (self.created_at + timedelta(hours=1)).replace(tzinfo=None)
        expires = command_value.expires_at.replace(tzinfo=None)
        cases = (
            ("ACTIVE", one_hour, None),
            ("ACTIVE", None, one_hour),
            ("EXPIRED", None, None),
            ("EXPIRED", expires, one_hour),
            ("CANCELLED", None, one_hour),
            ("CANCELLED", one_hour, None),
            ("CANCELLED", one_hour, one_hour + timedelta(minutes=1)),
        )
        for status, closed_at, cancelled_at in cases:
            with self.subTest(status=status, closed_at=closed_at, cancelled_at=cancelled_at):
                with self.assertRaises(sa.exc.IntegrityError) as raised:
                    with self.engine.begin() as connection:
                        connection.execute(sa.text(
                            "UPDATE payment_orders SET status=:status,closed_at=:closed_at,"
                            "cancelled_at=:cancelled_at WHERE id=:id"
                        ), {
                            "status": status,
                            "closed_at": closed_at,
                            "cancelled_at": cancelled_at,
                            "id": order_id,
                        })
                self.assertEqual(
                    raised.exception.orig.diag.constraint_name,
                    "ck_payment_orders_status_timestamps_coherent",
                )

    def test_foreign_keys_preserve_history_and_cancellation_is_atomic(self):
        command_value = self._command()
        with self.Session.begin() as session:
            order = register_or_get_payment_order(
                session,
                self.obligation_id,
                command_value,
                self._result(command_value),
                actor_user_id=self.actor_id,
                clock=lambda: self.created_at,
            )
            order_id = order.id
        with self.Session.begin() as session:
            cancel_payment_order(
                session,
                order_id,
                actor_user_id=self.actor_id,
                clock=lambda: self.created_at + timedelta(hours=1),
            )
        with self.assertRaises(sa.exc.IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(sa.text(
                    "DELETE FROM payment_obligations WHERE id=:id"
                ), {"id": self.obligation_id})
        with self.Session() as session:
            self.assertEqual(session.get(PaymentOrder, order_id).status, "CANCELLED")
            self.assertEqual(
                session.query(AuditLog).filter_by(entity_type="payment_order").count(),
                2,
            )


if __name__ == "__main__":
    unittest.main()
