import os
import json
import re
import sys
import threading
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

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
from app.models.psp_event import PSPEventRecord
from app.services.payment_orchestration import (
    InMemoryPaymentOrchestrator,
    PaymentObligation as PaymentObligationRequest,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.persistent_payment_workflow import PersistentPaymentWorkflow
from app.services.payment_persistence_service import (
    PaymentPersistenceConflictError,
    apply_reconciliation,
    create_or_get_obligation,
    register_or_get_attempt,
)
from app.services.psp_contract import (
    PSPPaymentQueryResult,
    PaymentAttempt,
    PaymentAttemptStatus,
)
from app.services.mercadopago_payment_query_http import (
    MercadoPagoHTTPResponse,
    MercadoPagoPaymentQueryHTTPClient,
)
from app.services.mercadopago_psp_adapter import MercadoPagoPSPAdapter
from app.services.psp_event_contract import PSPEvent
from app.services.psp_event_inbox import register_or_get_event
from app.services.psp_event_reconciliation import (
    PSPEventProcessingStatus,
    PSPEventReconciliationProcessor,
)
from app.services.psp_simulator import (
    InMemoryPSPSimulator,
    ScenarioController,
    SimulationScenario,
)
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
                sa.text(
                    "TRUNCATE TABLE psp_event_inbox, payment_attempts, "
                    "payment_obligations RESTART IDENTITY"
                )
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
            "20260911_02",
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

    def test_invalid_obligation_preserves_integrity_error_and_session_recovers(self):
        session = self.Session()
        invalid = self._request("invalid-obligation", "1", "invalid-obligation-key")
        # This regression targets PostgreSQL's real constraint diagnostics, so
        # it deliberately bypasses the already-covered DTO boundary.
        object.__setattr__(invalid, "amount", Decimal("0"))
        received = None
        try:
            create_or_get_obligation(session, invalid)
        except Exception as exc:
            received = exc
        self.assertIsInstance(received, IntegrityError)
        self.assertNotIsInstance(received, NoResultFound)
        self.assertEqual(
            getattr(received.orig, "sqlstate", None)
            or getattr(received.orig, "pgcode", None),
            "23514",
        )
        self.assertEqual(
            received.orig.diag.constraint_name,
            "ck_payment_obligations_amount_positive",
        )
        session.rollback()
        recovered = create_or_get_obligation(
            session,
            self._request("recovered-obligation", "1", "recovered-obligation-key"),
        )
        session.commit()
        self.assertIsNotNone(recovered.id)
        session.close()

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

    def test_contextual_psp_identity_is_unique_under_concurrency(self):
        requests = (
            self._request("psp-one", "10", "psp-one-key"),
            self._request("psp-two", "10", "psp-two-key"),
        )
        with self.Session.begin() as session:
            obligation_ids = [
                create_or_get_obligation(session, request).id for request in requests
            ]

        def register(session, index):
            obligation = session.get(PaymentObligation, obligation_ids[index])
            return register_or_get_attempt(
                session, obligation, self._result(requests[index]),
                psp_provider="provider", psp_live_mode=False,
            ).id

        results = self._race([
            lambda session: register(session, 0),
            lambda session: register(session, 1),
        ])
        self.assertEqual(sum(kind == "ok" for kind, _ in results), 1)
        error = next(value for kind, value in results if kind == "error")
        self.assertIsInstance(error, IntegrityError)
        self.assertEqual(error.orig.diag.constraint_name, "uq_payment_attempts_psp_identity")
        with self.Session() as session:
            self.assertEqual(session.query(PaymentAttemptRecord).count(), 1)

    def test_contextual_identity_boundaries_and_legacy_rows(self):
        legacy_request = self._request("legacy-psp", "10", "legacy-psp-key")
        with self.Session.begin() as session:
            legacy_obligation = create_or_get_obligation(session, legacy_request)
            legacy = register_or_get_attempt(
                session, legacy_obligation, self._result(legacy_request)
            )
            self.assertIsNone(legacy.psp_provider)
            self.assertIsNone(legacy.psp_live_mode)

        for index, (provider, live_mode) in enumerate((
            ("provider-a", True), ("provider-b", True), ("provider-a", False),
        )):
            request = self._request(f"boundary-{index}", "10", f"boundary-key-{index}")
            with self.Session.begin() as session:
                obligation = create_or_get_obligation(session, request)
                register_or_get_attempt(
                    session, obligation, self._result(request),
                    psp_provider=provider, psp_live_mode=live_mode,
                )
        with self.Session() as session:
            self.assertEqual(session.query(PaymentAttemptRecord).count(), 4)

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

    def test_concurrent_event_processing_converges_without_duplicate_financial_rows(self):
        request = self._request("event-reconciliation", "10", "event-key")
        with self.Session.begin() as session:
            obligation = create_or_get_obligation(session, request)
            attempt = register_or_get_attempt(
                session,
                obligation,
                self._result(request, PaymentOutcome.PENDING, "event-attempt"),
                psp_provider="provider",
                psp_live_mode=False,
            )
            event = register_or_get_event(session, PSPEvent(
                "provider", "event-id", "payment", "updated", "event-attempt",
                True, None, datetime.now(timezone.utc), "a" * 64,
            ))
            event_id = event.id
            attempt_id = attempt.id

        class Adapter:
            provider = "provider"
            live_mode = False

            def query_payment(self, external_attempt_id):
                return PSPPaymentQueryResult(
                    external_attempt_id,
                    PaymentAttemptStatus.APPROVED,
                )

        processor = PSPEventReconciliationProcessor(
            session_factory=self.Session,
            adapter=Adapter(),
            provider="provider",
            live_mode=False,
            payment_topics=("payment",),
        )
        results = self._race([
            lambda session: processor.process(event_id).status,
            lambda session: processor.process(event_id).status,
        ])
        self.assertEqual([kind for kind, _ in results], ["ok", "ok"])
        self.assertTrue(all(
            value in {
                PSPEventProcessingStatus.RECONCILED,
                PSPEventProcessingStatus.ALREADY_TERMINAL,
            }
            for _, value in results
        ))
        with self.Session() as session:
            rows = session.query(PaymentAttemptRecord).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].id, attempt_id)
            self.assertEqual(rows[0].financial_status, "APPROVED")
            self.assertEqual(session.query(PSPEventRecord).count(), 1)

    def test_mercadopago_query_transport_reconciles_in_second_transaction(self):
        request = self._request("mp-query", "10", "mp-query-key")
        with self.Session.begin() as session:
            obligation = create_or_get_obligation(session, request)
            attempt = register_or_get_attempt(
                session,
                obligation,
                self._result(request, PaymentOutcome.PENDING, "123456"),
                psp_provider="mercadopago",
                psp_live_mode=False,
            )
            event = register_or_get_event(session, PSPEvent(
                "mercadopago", "mp-event", "payment", "payment.updated",
                "123456", True, None, datetime.now(timezone.utc), "b" * 64,
            ))
            event_id = event.id
            attempt_id = attempt.id

        calls = []

        def transport(**values):
            with self.Session() as independent:
                stored = independent.get(PaymentAttemptRecord, attempt_id)
                self.assertEqual(stored.financial_status, "PENDING")
            calls.append(values)
            return MercadoPagoHTTPResponse(
                200,
                (("Content-Type", "application/json"),),
                json.dumps({
                    "id": 123456,
                    "status": "approved",
                    "live_mode": False,
                }).encode(),
            )

        client = MercadoPagoPaymentQueryHTTPClient(
            access_token="APP_USR-fake-postgresql-token",
            transport=transport,
            timeout=5,
        )
        processor = PSPEventReconciliationProcessor(
            session_factory=self.Session,
            adapter=MercadoPagoPSPAdapter(client=client, live_mode=False),
            provider="mercadopago",
            live_mode=False,
            payment_topics=("payment",),
        )
        result = processor.process(event_id)
        self.assertEqual(result.status, PSPEventProcessingStatus.RECONCILED)
        self.assertEqual(result.financial_status, PaymentAttemptStatus.APPROVED)
        self.assertEqual(len(calls), 1)
        with self.Session() as session:
            rows = session.query(PaymentAttemptRecord).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].id, attempt_id)
            self.assertEqual(rows[0].financial_status, "APPROVED")

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

    def test_persistent_workflow_commits_obligation_before_external_call(self):
        request = self._request("workflow-visible", "25.50", "workflow-visible-key")
        observations = []
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: "workflow-visible-attempt",
            clock=lambda: datetime(2026, 9, 11, 22, 0, tzinfo=timezone.utc),
            scenario_controller=ScenarioController((SimulationScenario.APPROVED,)),
        )

        class Adapter:
            def create_attempt(adapter_self, **values):
                with self.Session() as independent:
                    observations.append(
                        independent.query(PaymentObligation).filter_by(
                            internal_reference=request.internal_reference
                        ).count()
                    )
                return simulator.create_attempt(**values)

            def get_attempt(adapter_self, attempt_id):
                return simulator.get_attempt(attempt_id)

        workflow = PersistentPaymentWorkflow(
            session_factory=self.Session,
            orchestrator=InMemoryPaymentOrchestrator(Adapter()),
        )
        result = workflow.process(request)
        self.assertEqual(observations, [1])
        self.assertEqual(result.outcome, PaymentOutcome.APPROVED)
        with self.Session() as independent:
            self.assertEqual(independent.query(PaymentObligation).count(), 1)
            self.assertEqual(independent.query(PaymentAttemptRecord).count(), 1)

    def test_persistent_workflow_rolls_back_result_and_recovers_by_adapter_replay(self):
        request = self._request("workflow-recovery", "90", "workflow-recovery-key")
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: "workflow-recovery-attempt",
            clock=lambda: datetime(2026, 9, 11, 22, 5, tzinfo=timezone.utc),
            scenario_controller=ScenarioController((SimulationScenario.APPROVED,)),
        )
        orchestrator = InMemoryPaymentOrchestrator(simulator)
        workflow = PersistentPaymentWorkflow(
            session_factory=self.Session,
            orchestrator=orchestrator,
        )
        original = register_or_get_attempt

        def fail_after_flush(session, obligation, result):
            original(session, obligation, result)
            raise RuntimeError("forced failure after result flush")

        with patch(
            "app.services.persistent_payment_workflow.register_or_get_attempt",
            side_effect=fail_after_flush,
        ):
            with self.assertRaisesRegex(RuntimeError, "forced failure"):
                workflow.process(request)
        with self.Session() as independent:
            self.assertEqual(independent.query(PaymentObligation).count(), 1)
            self.assertEqual(independent.query(PaymentAttemptRecord).count(), 0)

        result = workflow.process(request)
        self.assertEqual(result.outcome, PaymentOutcome.APPROVED)
        self.assertEqual(simulator.attempt_count, 1)
        with self.Session() as independent:
            self.assertEqual(independent.query(PaymentAttemptRecord).count(), 1)

    def test_persistent_workflow_reconciles_with_external_call_between_transactions(self):
        request = self._request("workflow-reconcile", "75", "workflow-reconcile-key")
        observations = []
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: "workflow-reconcile-attempt",
            clock=lambda: datetime(2026, 9, 11, 22, 10, tzinfo=timezone.utc),
            scenario_controller=ScenarioController((SimulationScenario.UNCERTAIN,)),
        )

        class Adapter:
            def create_attempt(adapter_self, **values):
                return simulator.create_attempt(**values)

            def get_attempt(adapter_self, attempt_id):
                with self.Session() as independent:
                    observations.append(
                        independent.query(PaymentAttemptRecord).filter_by(
                            idempotency_key=request.idempotency_key,
                            requires_reconciliation=True,
                        ).count()
                    )
                return simulator.get_attempt(attempt_id)

        workflow = PersistentPaymentWorkflow(
            session_factory=self.Session,
            orchestrator=InMemoryPaymentOrchestrator(Adapter()),
        )
        uncertain = workflow.process(request)
        self.assertEqual(uncertain.outcome, PaymentOutcome.RECONCILIATION_REQUIRED)
        self.assertIsNone(uncertain.financial_status)
        self.assertTrue(uncertain.requires_reconciliation)
        self.assertEqual(uncertain.attempt_id, "workflow-reconcile-attempt")
        with self.Session() as independent:
            stored = independent.query(PaymentAttemptRecord).filter_by(
                idempotency_key=request.idempotency_key
            ).one()
            self.assertIsNone(stored.financial_status)
            self.assertEqual(
                stored.orchestration_result,
                PaymentOutcome.RECONCILIATION_REQUIRED.value,
            )
            self.assertTrue(stored.requires_reconciliation)
            self.assertEqual(
                stored.external_attempt_id, "workflow-reconcile-attempt"
            )
        result = workflow.reconcile(request)
        self.assertEqual(observations, [1])
        self.assertEqual(result.outcome, PaymentOutcome.PENDING)


if __name__ == "__main__":
    unittest.main()
