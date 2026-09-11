import os
import re
import sys
import threading
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.payment_attempt import PaymentAttemptRecord
from app.models.payment_obligation import PaymentObligation
from app.services.payment_orchestration import (
    PaymentObligation as PaymentObligationRequest,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.payment_persistence_service import (
    PaymentPersistenceConflictError,
    apply_reconciliation,
    create_or_get_obligation,
    register_or_get_attempt,
)
from app.services.psp_contract import PaymentAttemptStatus
from tests.alembic_head_validation import assert_database_at_repository_head


RESERVED_DATABASE = "trax_payment_persistence_test"
POSTGRESQL_IDENTIFIER_MAX_BYTES = 63
RESERVED_DATABASE_PATTERN = re.compile(
    rf"{RESERVED_DATABASE}(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?"
)


def _validate_postgresql_test_url(url, allow_reset):
    if allow_reset != "1":
        raise RuntimeError("Gate bloqueado: falta autorizacion explicita")
    if not isinstance(url, str) or not url:
        raise RuntimeError("Gate bloqueado: falta URL PostgreSQL descartable")
    parsed = make_url(url)
    database = parsed.database
    if parsed.get_backend_name() != "postgresql":
        raise RuntimeError("Gate bloqueado: el motor no es PostgreSQL")
    if (
        not isinstance(database, str)
        or len(database.encode("utf-8")) > POSTGRESQL_IDENTIFIER_MAX_BYTES
        or RESERVED_DATABASE_PATTERN.fullmatch(database) is None
        or bool(parsed.query)
    ):
        raise RuntimeError(
            "Gate bloqueado: la base debe llamarse "
            f"{RESERVED_DATABASE} o {RESERVED_DATABASE}_<segmentos_ascii>, "
            f"sin parametros y con hasta {POSTGRESQL_IDENTIFIER_MAX_BYTES} bytes"
        )
    return parsed


def _create_guarded_engine(url, allow_reset):
    parsed = _validate_postgresql_test_url(url, allow_reset)
    engine = sa.create_engine(parsed)
    if engine.dialect.name != "postgresql":
        engine.dispose()
        raise RuntimeError("Gate bloqueado: el dialecto efectivo no es PostgreSQL")
    return engine


class PostgreSQLPaymentPersistenceGate(unittest.TestCase):
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
            connection.execute(
                sa.text("TRUNCATE TABLE payment_attempts, payment_obligations RESTART IDENTITY")
            )

    @staticmethod
    def _request(reference="pg-obligation", amount="123456789.123456789", key="pg-key"):
        return PaymentObligationRequest(reference, Decimal(amount), "ARS", key)

    @staticmethod
    def _result(request, outcome=PaymentOutcome.APPROVED, attempt_id="pg-attempt"):
        status = None if outcome is PaymentOutcome.RECONCILIATION_REQUIRED else PaymentAttemptStatus(outcome.value)
        return PaymentOrchestrationResult(
            request.internal_reference, request.amount, request.currency,
            request.idempotency_key, attempt_id, status, outcome,
            outcome is PaymentOutcome.RECONCILIATION_REQUIRED,
        )

    def _race(self, callbacks):
        barrier = threading.Barrier(len(callbacks))
        results = []
        lock = threading.Lock()

        def worker(callback):
            session = self.Session()
            try:
                barrier.wait()
                value = callback(session)
                session.commit()
                result = ("ok", value)
            except Exception as exc:
                session.rollback()
                result = ("error", exc)
            finally:
                session.close()
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker, args=(callback,)) for callback in callbacks]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)
            self.assertFalse(thread.is_alive(), "concurrent operation timed out")
        return results

    def test_a_migration_upgrade_downgrade_upgrade_and_dynamic_head(self):
        command.downgrade(self.config, "20260904_01")
        self.assertNotIn("payment_obligations", sa.inspect(self.engine).get_table_names())
        command.upgrade(self.config, "head")
        with self.engine.connect() as connection:
            revisions = connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalars().all()
        self.assertEqual(
            assert_database_at_repository_head(self.config, revisions),
            "20260910_01",
        )

    def test_concurrent_identical_obligations_converge_and_preserve_decimal(self):
        request = self._request()
        results = self._race([
            lambda session: create_or_get_obligation(session, request).id,
            lambda session: create_or_get_obligation(session, request).id,
        ])
        self.assertEqual([kind for kind, _ in results], ["ok", "ok"])
        with self.Session() as session:
            rows = session.query(PaymentObligation).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].amount.as_tuple(), request.amount.as_tuple())

    def test_concurrent_obligation_conflict_has_one_winner(self):
        first = self._request(amount="10")
        second = self._request(amount="11")
        results = self._race([
            lambda session: create_or_get_obligation(session, first).id,
            lambda session: create_or_get_obligation(session, second).id,
        ])
        self.assertEqual(sum(kind == "ok" for kind, _ in results), 1)
        errors = [value for kind, value in results if kind == "error"]
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], PaymentPersistenceConflictError)

    def test_concurrent_attempt_replay_and_conflict(self):
        request = self._request()
        with self.Session.begin() as session:
            obligation_id = create_or_get_obligation(session, request).id

        def register(session, result):
            obligation = session.get(PaymentObligation, obligation_id)
            return register_or_get_attempt(session, obligation, result).id

        identical = self._result(request)
        replay = self._race([
            lambda session: register(session, identical),
            lambda session: register(session, identical),
        ])
        self.assertEqual([kind for kind, _ in replay], ["ok", "ok"])
        with self.engine.begin() as connection:
            connection.execute(sa.text("DELETE FROM payment_attempts"))
        conflict = self._race([
            lambda session: register(session, identical),
            lambda session: register(
                session, self._result(request, PaymentOutcome.REJECTED, "other-attempt")
            ),
        ])
        self.assertEqual(sum(kind == "ok" for kind, _ in conflict), 1)
        self.assertIsInstance(
            next(value for kind, value in conflict if kind == "error"),
            PaymentPersistenceConflictError,
        )

    def test_concurrent_reconciliation_serializes_identical_and_incompatible_results(self):
        request = self._request()
        with self.Session.begin() as session:
            obligation = create_or_get_obligation(session, request)
            attempt_id = register_or_get_attempt(
                session,
                obligation,
                self._result(request, PaymentOutcome.RECONCILIATION_REQUIRED, None),
            ).id

        approved = self._result(request, PaymentOutcome.APPROVED, "provider-001")
        identical = self._race([
            lambda session: apply_reconciliation(session, attempt_id, approved).orchestration_result,
            lambda session: apply_reconciliation(session, attempt_id, approved).orchestration_result,
        ])
        self.assertEqual([kind for kind, _ in identical], ["ok", "ok"])

        with self.engine.begin() as connection:
            connection.execute(
                sa.text(
                    "UPDATE payment_attempts SET external_attempt_id=NULL, financial_status=NULL, "
                    "orchestration_result='RECONCILIATION_REQUIRED', requires_reconciliation=true"
                )
            )
        rejected = self._result(request, PaymentOutcome.REJECTED, "provider-001")
        conflict = self._race([
            lambda session: apply_reconciliation(session, attempt_id, approved).orchestration_result,
            lambda session: apply_reconciliation(session, attempt_id, rejected).orchestration_result,
        ])
        self.assertEqual(sum(kind == "ok" for kind, _ in conflict), 1)
        self.assertIsInstance(
            next(value for kind, value in conflict if kind == "error"),
            PaymentPersistenceConflictError,
        )

    def test_constraints_foreign_key_rollback_visibility_and_session_recovery(self):
        session = self.Session()
        request = self._request()
        obligation = create_or_get_obligation(session, request)
        register_or_get_attempt(session, obligation, self._result(request))
        with self.engine.connect() as independent:
            self.assertEqual(independent.execute(sa.text("SELECT count(*) FROM payment_obligations")).scalar_one(), 0)
        session.rollback()
        with self.engine.connect() as independent:
            self.assertEqual(independent.execute(sa.text("SELECT count(*) FROM payment_obligations")).scalar_one(), 0)
        valid = create_or_get_obligation(session, self._request("recovered", "1", "recovered-key"))
        session.commit()
        self.assertIsNotNone(valid.id)
        valid_attempt = register_or_get_attempt(
            session,
            valid,
            self._result(self._request("recovered", "1", "recovered-key")),
        )
        session.commit()
        with self.assertRaises(IntegrityError):
            session.execute(
                sa.text("DELETE FROM payment_obligations WHERE id=:id"),
                {"id": valid.id},
            )
        session.rollback()
        self.assertIsNotNone(session.get(PaymentAttemptRecord, valid_attempt.id))
        session.close()

        invalid = self.Session()
        invalid.add(PaymentObligation(internal_reference="zero", amount=Decimal("0"), currency="ARS"))
        with self.assertRaises(IntegrityError):
            invalid.flush()
        invalid.rollback()
        invalid.add(PaymentAttemptRecord(
            obligation_id=999999,
            idempotency_key="bad-fk",
            external_attempt_id=None,
            financial_status=None,
            orchestration_result="RECONCILIATION_REQUIRED",
            requires_reconciliation=True,
        ))
        with self.assertRaises(IntegrityError):
            invalid.flush()
        invalid.rollback()
        obligation_id = invalid.query(PaymentObligation.id).filter_by(
            internal_reference="recovered"
        ).scalar()
        invalid.add(PaymentAttemptRecord(
            obligation_id=obligation_id,
            idempotency_key="bad-coherence",
            external_attempt_id=None,
            financial_status="APPROVED",
            orchestration_result="RECONCILIATION_REQUIRED",
            requires_reconciliation=True,
        ))
        with self.assertRaises(IntegrityError):
            invalid.flush()
        invalid.rollback()
        invalid.close()

    def test_foreign_key_violation_is_not_misclassified_as_idempotent_replay(self):
        session = self.Session()
        request = self._request("missing-obligation", "10", "missing-fk-key")
        missing = PaymentObligation(
            id=999999,
            internal_reference=request.internal_reference,
            amount=request.amount,
            currency=request.currency,
        )
        received = None
        try:
            register_or_get_attempt(session, missing, self._result(request))
        except Exception as exc:
            received = exc

        self.assertIsInstance(received, IntegrityError)
        self.assertNotIsInstance(received, NoResultFound)
        self.assertEqual(
            getattr(received.orig, "sqlstate", None)
            or getattr(received.orig, "pgcode", None),
            "23503",
        )
        self.assertEqual(
            received.orig.diag.constraint_name,
            "fk_payment_attempts_obligation",
        )
        with self.engine.connect() as independent:
            self.assertEqual(
                independent.execute(
                    sa.text(
                        "SELECT count(*) FROM payment_attempts "
                        "WHERE idempotency_key='missing-fk-key'"
                    )
                ).scalar_one(),
                0,
            )

        session.rollback()
        recovered_request = self._request("after-fk-rollback", "10", "after-fk-key")
        recovered = create_or_get_obligation(session, recovered_request)
        register_or_get_attempt(session, recovered, self._result(recovered_request))
        session.commit()
        self.assertEqual(
            session.query(PaymentAttemptRecord).filter_by(
                idempotency_key="after-fk-key"
            ).count(),
            1,
        )
        session.close()


if __name__ == "__main__":
    unittest.main()
