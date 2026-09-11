import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app import db
from app.models.payment_attempt import PaymentAttemptRecord
from app.models.payment_obligation import PaymentObligation as StoredObligation
from app.services.payment_orchestration import (
    InMemoryPaymentOrchestrator,
    PaymentObligation,
    PaymentOutcome,
)
from app.services.payment_persistence_service import PaymentPersistenceConflictError
from app.services.persistent_payment_workflow import PersistentPaymentWorkflow
from app.services.psp_contract import (
    AttemptNotFoundError,
    PaymentAttempt,
    PaymentAttemptStatus,
    UncertainResponseError,
)
from app.services.psp_simulator import (
    InMemoryPSPSimulator,
    ScenarioController,
    SimulationScenario,
)


class TrackingSessionFactory:
    def __init__(self, engine):
        self._factory = sessionmaker(bind=engine, expire_on_commit=False)
        self.open_sessions = 0

    def __call__(self):
        owner = self
        session = self._factory()

        class Context:
            def __enter__(self):
                owner.open_sessions += 1
                return session

            def __exit__(self, exc_type, exc, traceback):
                try:
                    return session.__exit__(exc_type, exc, traceback)
                finally:
                    owner.open_sessions -= 1

        return Context()

    def plain(self):
        return self._factory()


class ObservingAdapter:
    def __init__(self, delegate, callback=lambda: None):
        self.delegate = delegate
        self.callback = callback
        self.create_calls = 0
        self.get_calls = 0

    def create_attempt(self, **values):
        self.create_calls += 1
        self.callback()
        return self.delegate.create_attempt(**values)

    def get_attempt(self, attempt_id):
        self.get_calls += 1
        self.callback()
        return self.delegate.get_attempt(attempt_id)


class UncertainWithoutIdentifierAdapter:
    def __init__(self, created_at):
        self.created_at = created_at
        self.create_calls = 0
        self.get_calls = 0
        self._attempt = None

    def create_attempt(self, **values):
        self.create_calls += 1
        if self.create_calls == 1:
            raise UncertainResponseError("response unavailable")
        if self._attempt is None:
            self._attempt = PaymentAttempt(
                attempt_id="recovered-attempt",
                status=PaymentAttemptStatus.APPROVED,
                created_at=self.created_at,
                **values,
            )
        return self._attempt

    def get_attempt(self, attempt_id):
        self.get_calls += 1
        if self._attempt is None or self._attempt.attempt_id != attempt_id:
            raise AttemptNotFoundError("attempt not found")
        return self._attempt


class UncertainThenAuthoritativeAdapter:
    def __init__(self, created_at, status, attempt_id):
        self.created_at = created_at
        self.status = status
        self.attempt_id = attempt_id
        self.values = None

    def create_attempt(self, **values):
        self.values = values
        raise UncertainResponseError(
            "response unavailable", attempt_id=self.attempt_id
        )

    def get_attempt(self, attempt_id):
        if attempt_id != self.attempt_id or self.values is None:
            raise AttemptNotFoundError("attempt not found")
        return PaymentAttempt(
            attempt_id=self.attempt_id,
            status=self.status,
            created_at=self.created_at,
            **self.values,
        )


class FailingAdapter:
    def __init__(self):
        self.create_calls = 0

    def create_attempt(self, **values):
        self.create_calls += 1
        raise RuntimeError("adapter failed")

    def get_attempt(self, attempt_id):
        raise AssertionError("get_attempt must not be called")


class PersistentPaymentWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        database = Path(self.temporary.name) / "workflow.db"
        self.engine = sa.create_engine(f"sqlite:///{database.as_posix()}")
        db.metadata.create_all(self.engine)
        self.sessions = TrackingSessionFactory(self.engine)
        self.now = datetime(2026, 9, 11, 18, 0, tzinfo=timezone.utc)
        self.request = PaymentObligation(
            "workflow-obligation", Decimal("1250.500"), "ARS", "workflow-key"
        )

    def tearDown(self):
        self.engine.dispose()
        self.temporary.cleanup()

    def _workflow(self, *scenarios, callback=lambda: None):
        identifiers = iter(("attempt-001", "attempt-002"))
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: next(identifiers),
            clock=lambda: self.now,
            scenario_controller=ScenarioController(scenarios),
        )
        adapter = ObservingAdapter(simulator, callback)
        return (
            PersistentPaymentWorkflow(
                session_factory=self.sessions,
                orchestrator=InMemoryPaymentOrchestrator(adapter),
            ),
            adapter,
            simulator,
        )

    def _counts(self):
        with self.sessions.plain() as session:
            return (
                session.query(StoredObligation).count(),
                session.query(PaymentAttemptRecord).count(),
            )

    def _stored_attempt(self, idempotency_key=None):
        with self.sessions.plain() as session:
            return session.query(PaymentAttemptRecord).filter_by(
                idempotency_key=idempotency_key or self.request.idempotency_key
            ).one()

    def test_obligation_is_committed_and_session_closed_before_adapter_call(self):
        observations = []

        def observe():
            with self.sessions.plain() as independent:
                observations.append(
                    (self.sessions.open_sessions, independent.query(StoredObligation).count())
                )

        workflow, _, _ = self._workflow(SimulationScenario.APPROVED, callback=observe)
        workflow.process(self.request)
        self.assertEqual(observations, [(0, 1)])

    def test_approved_rejected_and_pending_results_are_persisted(self):
        for index, (scenario, expected) in enumerate((
            (SimulationScenario.APPROVED, PaymentOutcome.APPROVED),
            (SimulationScenario.REJECTED, PaymentOutcome.REJECTED),
            (SimulationScenario.PENDING, PaymentOutcome.PENDING),
        )):
            with self.subTest(scenario=scenario):
                request = PaymentObligation(
                    f"obligation-{index}", Decimal("10"), "ARS", f"key-{index}"
                )
                workflow, _, _ = self._workflow(scenario)
                result = workflow.process(request)
                self.assertEqual(result.outcome, expected)
                self.assertFalse(result.requires_reconciliation)
                stored = self._stored_attempt(request.idempotency_key)
                self.assertEqual(stored.financial_status, expected.value)
                self.assertEqual(stored.orchestration_result, expected.value)
                self.assertFalse(stored.requires_reconciliation)

    def test_uncertainty_with_identifier_is_persisted_without_rejection(self):
        workflow, adapter, _ = self._workflow(SimulationScenario.UNCERTAIN)
        result = workflow.process(self.request)
        self.assertEqual(result.outcome, PaymentOutcome.RECONCILIATION_REQUIRED)
        self.assertIsNone(result.financial_status)
        self.assertTrue(result.requires_reconciliation)
        self.assertEqual(result.attempt_id, "attempt-001")
        self.assertEqual(adapter.create_calls, 1)
        stored = self._stored_attempt()
        self.assertIsNone(stored.financial_status)
        self.assertEqual(
            stored.orchestration_result,
            PaymentOutcome.RECONCILIATION_REQUIRED.value,
        )
        self.assertTrue(stored.requires_reconciliation)
        self.assertEqual(stored.external_attempt_id, "attempt-001")

    def test_uncertainty_without_identifier_is_persisted(self):
        adapter = UncertainWithoutIdentifierAdapter(self.now)
        workflow = PersistentPaymentWorkflow(
            session_factory=self.sessions,
            orchestrator=InMemoryPaymentOrchestrator(adapter),
        )
        result = workflow.process(self.request)
        self.assertIsNone(result.attempt_id)
        self.assertEqual(result.outcome, PaymentOutcome.RECONCILIATION_REQUIRED)
        self.assertIsNone(result.financial_status)
        self.assertTrue(result.requires_reconciliation)
        stored = self._stored_attempt()
        self.assertIsNone(stored.financial_status)
        self.assertEqual(
            stored.orchestration_result,
            PaymentOutcome.RECONCILIATION_REQUIRED.value,
        )
        self.assertTrue(stored.requires_reconciliation)
        self.assertIsNone(stored.external_attempt_id)
        self.assertEqual(self._counts(), (1, 1))

    def test_terminal_replay_skips_adapter_and_keeps_single_rows(self):
        workflow, adapter, _ = self._workflow(SimulationScenario.APPROVED)
        first = workflow.process(self.request)
        second = workflow.process(self.request)
        self.assertEqual(first, second)
        self.assertEqual(adapter.create_calls, 1)
        self.assertEqual(self._counts(), (1, 1))

    def test_conflict_is_detected_before_adapter_call_and_rolls_back_new_obligation(self):
        workflow, adapter, _ = self._workflow(SimulationScenario.APPROVED)
        workflow.process(self.request)
        conflicting = PaymentObligation(
            "other-reference", Decimal("10"), "ARS", self.request.idempotency_key
        )
        with self.assertRaises(PaymentPersistenceConflictError):
            workflow.process(conflicting)
        self.assertEqual(adapter.create_calls, 1)
        self.assertEqual(self._counts(), (1, 1))

    def test_failure_before_adapter_does_not_call_it_or_write_partial_rows(self):
        workflow, adapter, _ = self._workflow(SimulationScenario.APPROVED)
        with patch(
            "app.services.persistent_payment_workflow.create_or_get_obligation",
            side_effect=RuntimeError("preparation failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "preparation failed"):
                workflow.process(self.request)
        self.assertEqual(adapter.create_calls, 0)
        self.assertEqual(self._counts(), (0, 0))

    def test_adapter_failure_leaves_committed_obligation_without_attempt(self):
        adapter = FailingAdapter()
        workflow = PersistentPaymentWorkflow(
            session_factory=self.sessions,
            orchestrator=InMemoryPaymentOrchestrator(adapter),
        )
        with self.assertRaisesRegex(RuntimeError, "adapter failed"):
            workflow.process(self.request)
        self.assertEqual(adapter.create_calls, 1)
        self.assertEqual(self._counts(), (1, 0))

    def test_persistence_failure_replays_adapter_and_recovers_one_attempt(self):
        workflow, adapter, simulator = self._workflow(SimulationScenario.APPROVED)
        from app.services.payment_persistence_service import register_or_get_attempt

        with patch(
            "app.services.persistent_payment_workflow.register_or_get_attempt",
            side_effect=RuntimeError("persistence failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "persistence failed"):
                workflow.process(self.request)
        self.assertEqual(self._counts(), (1, 0))

        with patch(
            "app.services.persistent_payment_workflow.register_or_get_attempt",
            wraps=register_or_get_attempt,
        ):
            result = workflow.process(self.request)
        self.assertEqual(result.outcome, PaymentOutcome.APPROVED)
        self.assertEqual(adapter.create_calls, 2)
        self.assertEqual(simulator.attempt_count, 1)
        self.assertEqual(self._counts(), (1, 1))

    def test_reconciliation_with_identifier_queries_outside_transaction(self):
        observations = []
        workflow, adapter, _ = self._workflow(
            SimulationScenario.UNCERTAIN,
            callback=lambda: observations.append(self.sessions.open_sessions),
        )
        workflow.process(self.request)
        result = workflow.reconcile(self.request)
        self.assertEqual(result.outcome, PaymentOutcome.PENDING)
        self.assertEqual(adapter.create_calls, 1)
        self.assertEqual(adapter.get_calls, 1)
        self.assertEqual(observations, [0, 0])

    def test_reconciliation_without_identifier_replays_exact_request_once(self):
        adapter = UncertainWithoutIdentifierAdapter(self.now)
        workflow = PersistentPaymentWorkflow(
            session_factory=self.sessions,
            orchestrator=InMemoryPaymentOrchestrator(adapter),
        )
        workflow.process(self.request)
        result = workflow.reconcile(self.request)
        self.assertEqual(result.outcome, PaymentOutcome.APPROVED)
        self.assertEqual(adapter.create_calls, 2)
        self.assertEqual(adapter.get_calls, 0)
        self.assertEqual(self._counts(), (1, 1))

    def test_reconciliation_from_unknown_accepts_each_authoritative_status(self):
        for index, status in enumerate((
            PaymentAttemptStatus.PENDING,
            PaymentAttemptStatus.APPROVED,
            PaymentAttemptStatus.REJECTED,
        )):
            with self.subTest(status=status):
                request = PaymentObligation(
                    f"reconcile-{index}", Decimal("30"), "ARS", f"reconcile-key-{index}"
                )
                adapter = UncertainThenAuthoritativeAdapter(
                    self.now, status, f"reconcile-attempt-{index}"
                )
                workflow = PersistentPaymentWorkflow(
                    session_factory=self.sessions,
                    orchestrator=InMemoryPaymentOrchestrator(adapter),
                )
                uncertain = workflow.process(request)
                self.assertIsNone(uncertain.financial_status)
                self.assertEqual(
                    uncertain.outcome, PaymentOutcome.RECONCILIATION_REQUIRED
                )
                self.assertTrue(uncertain.requires_reconciliation)

                reconciled = workflow.reconcile(request)
                self.assertEqual(reconciled.financial_status, status)
                self.assertEqual(reconciled.outcome.value, status.value)
                self.assertFalse(reconciled.requires_reconciliation)
                stored = self._stored_attempt(request.idempotency_key)
                self.assertEqual(stored.financial_status, status.value)
                self.assertEqual(stored.orchestration_result, status.value)
                self.assertFalse(stored.requires_reconciliation)

    def test_workflows_and_tests_are_isolated(self):
        first, first_adapter, _ = self._workflow(SimulationScenario.APPROVED)
        first.process(self.request)
        second_request = PaymentObligation("second", Decimal("2"), "USD", "second-key")
        second, second_adapter, _ = self._workflow(SimulationScenario.REJECTED)
        second.process(second_request)
        self.assertEqual(first_adapter.create_calls, 1)
        self.assertEqual(second_adapter.create_calls, 1)
        self.assertEqual(self._counts(), (2, 2))


if __name__ == "__main__":
    unittest.main()
