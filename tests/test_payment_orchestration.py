import ast
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from app.services.payment_orchestration import (
    InMemoryPaymentOrchestrator,
    InvalidPaymentRequestError,
    PaymentObligation,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.psp_contract import (
    AttemptNotFoundError,
    IdempotencyConflictError,
    PaymentAttempt,
    PaymentAttemptStatus,
    UncertainResponseError,
)
from app.services.psp_simulator import (
    InMemoryPSPSimulator,
    ScenarioController,
    SimulationScenario,
)


class UncertainWithoutIdentifierAdapter:
    def __init__(self, *, remain_uncertain=False):
        self.remain_uncertain = remain_uncertain
        self.create_calls = 0
        self.get_calls = 0
        self._attempt = None

    def create_attempt(self, **values):
        self.create_calls += 1
        if self.create_calls == 1 or self.remain_uncertain:
            raise UncertainResponseError("transport response unavailable")
        self._attempt = PaymentAttempt(
            attempt_id="provider-001",
            status=PaymentAttemptStatus.APPROVED,
            created_at=datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
            **values,
        )
        return self._attempt

    def get_attempt(self, attempt_id):
        self.get_calls += 1
        if self._attempt is None or self._attempt.attempt_id != attempt_id:
            raise AttemptNotFoundError("attempt not found")
        return self._attempt


class PaymentOrchestrationTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
        self.obligation = PaymentObligation(
            internal_reference="obligation-001",
            amount=Decimal("1250.500"),
            currency="ars",
            idempotency_key="payment-key-001",
        )

    def _orchestrator(self, *scenarios):
        ids = iter(("attempt-001", "attempt-002", "attempt-003"))
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: next(ids),
            clock=lambda: self.now,
            scenario_controller=ScenarioController(scenarios),
        )
        return InMemoryPaymentOrchestrator(simulator), simulator

    def test_approved_obligation(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.APPROVED)
        result = orchestrator.process(self.obligation)
        self.assertEqual(result.outcome, PaymentOutcome.APPROVED)
        self.assertEqual(result.financial_status, PaymentAttemptStatus.APPROVED)
        self.assertFalse(result.requires_reconciliation)

    def test_rejected_obligation(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.REJECTED)
        result = orchestrator.process(self.obligation)
        self.assertEqual(result.outcome, PaymentOutcome.REJECTED)
        self.assertEqual(result.financial_status, PaymentAttemptStatus.REJECTED)
        self.assertFalse(result.requires_reconciliation)

    def test_pending_obligation_is_not_transport_uncertainty(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.PENDING)
        result = orchestrator.process(self.obligation)
        self.assertEqual(result.outcome, PaymentOutcome.PENDING)
        self.assertEqual(result.financial_status, PaymentAttemptStatus.PENDING)
        self.assertFalse(result.requires_reconciliation)

    def test_uncertain_response_with_known_identifier(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.UNCERTAIN)
        result = orchestrator.process(self.obligation)
        self.assertEqual(result.outcome, PaymentOutcome.RECONCILIATION_REQUIRED)
        self.assertEqual(result.attempt_id, "attempt-001")
        self.assertIsNone(result.financial_status)
        self.assertTrue(result.requires_reconciliation)

    def test_uncertain_response_without_identifier(self):
        adapter = UncertainWithoutIdentifierAdapter()
        result = InMemoryPaymentOrchestrator(adapter).process(self.obligation)
        self.assertEqual(result.outcome, PaymentOutcome.RECONCILIATION_REQUIRED)
        self.assertIsNone(result.attempt_id)
        self.assertEqual(adapter.create_calls, 1)

    def test_reconciliation_with_identifier_queries_attempt(self):
        orchestrator, simulator = self._orchestrator(SimulationScenario.UNCERTAIN)
        uncertain = orchestrator.process(self.obligation)
        result = orchestrator.reconcile(self.obligation, uncertain)
        self.assertEqual(result.outcome, PaymentOutcome.PENDING)
        self.assertEqual(result.attempt_id, uncertain.attempt_id)
        self.assertEqual(simulator.attempt_count, 1)

    def test_reconciliation_without_identifier_replays_same_request(self):
        adapter = UncertainWithoutIdentifierAdapter()
        orchestrator = InMemoryPaymentOrchestrator(adapter)
        uncertain = orchestrator.process(self.obligation)
        result = orchestrator.reconcile(self.obligation, uncertain)
        self.assertEqual(result.outcome, PaymentOutcome.APPROVED)
        self.assertEqual(adapter.create_calls, 2)
        self.assertEqual(adapter.get_calls, 0)

    def test_repeated_uncertainty_stays_reconciliation_required(self):
        adapter = UncertainWithoutIdentifierAdapter(remain_uncertain=True)
        orchestrator = InMemoryPaymentOrchestrator(adapter)
        first = orchestrator.process(self.obligation)
        second = orchestrator.reconcile(self.obligation, first)
        self.assertTrue(second.requires_reconciliation)
        self.assertEqual(second.outcome, PaymentOutcome.RECONCILIATION_REQUIRED)
        self.assertIsNone(second.attempt_id)
        self.assertEqual(adapter.create_calls, 2)

    def test_identical_replay_does_not_duplicate_attempt(self):
        orchestrator, simulator = self._orchestrator(SimulationScenario.APPROVED)
        first = orchestrator.process(self.obligation)
        second = orchestrator.process(self.obligation)
        self.assertEqual(first, second)
        self.assertEqual(simulator.attempt_count, 1)

    def test_same_key_with_different_content_preserves_explicit_conflict(self):
        orchestrator, simulator = self._orchestrator(SimulationScenario.APPROVED)
        orchestrator.process(self.obligation)
        changed = PaymentObligation(
            internal_reference=self.obligation.internal_reference,
            amount=Decimal("1251"), currency="ARS",
            idempotency_key=self.obligation.idempotency_key,
        )
        with self.assertRaises(IdempotencyConflictError):
            orchestrator.process(changed)
        self.assertEqual(simulator.attempt_count, 1)

    def test_decimal_is_preserved_exactly_without_quantization(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.APPROVED)
        result = orchestrator.process(self.obligation)
        self.assertEqual(result.amount.as_tuple(), Decimal("1250.500").as_tuple())

    def test_invalid_amounts_are_rejected_before_adapter_call(self):
        invalid = (1.25, Decimal("0"), Decimal("-1"), Decimal("NaN"),
                   Decimal("Infinity"), Decimal("-Infinity"))
        for amount in invalid:
            with self.subTest(amount=amount):
                with self.assertRaises(InvalidPaymentRequestError):
                    PaymentObligation("ref", amount, "ARS", "key")

    def test_invalid_text_and_wrapped_key_are_rejected(self):
        for values in (("", Decimal("1"), "ARS", "key"),
                       ("ref", Decimal("1"), "", "key"),
                       ("ref", Decimal("1"), "ARS", " key ")):
            with self.subTest(values=values):
                with self.assertRaises(InvalidPaymentRequestError):
                    PaymentObligation(*values)

    def test_request_and_result_are_immutable(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.APPROVED)
        result = orchestrator.process(self.obligation)
        with self.assertRaises(FrozenInstanceError):
            self.obligation.amount = Decimal("2")
        with self.assertRaises(FrozenInstanceError):
            result.outcome = PaymentOutcome.REJECTED

    def test_attempt_not_found_remains_distinct_during_reconciliation(self):
        adapter = UncertainWithoutIdentifierAdapter()
        orchestrator = InMemoryPaymentOrchestrator(adapter)
        uncertain = PaymentOrchestrationResult(
            internal_reference=self.obligation.internal_reference,
            amount=self.obligation.amount, currency=self.obligation.currency,
            idempotency_key=self.obligation.idempotency_key,
            attempt_id="missing", financial_status=None,
            outcome=PaymentOutcome.RECONCILIATION_REQUIRED,
            requires_reconciliation=True,
        )
        with self.assertRaises(AttemptNotFoundError):
            orchestrator.reconcile(self.obligation, uncertain)

    def test_non_uncertain_or_mismatched_result_cannot_be_reconciled(self):
        orchestrator, _ = self._orchestrator(SimulationScenario.PENDING)
        pending = orchestrator.process(self.obligation)
        with self.assertRaises(InvalidPaymentRequestError):
            orchestrator.reconcile(self.obligation, pending)

        wrong = PaymentObligation("other", Decimal("1250.500"), "ARS",
                                  "payment-key-001")
        uncertain = PaymentOrchestrationResult(
            internal_reference=self.obligation.internal_reference,
            amount=self.obligation.amount, currency=self.obligation.currency,
            idempotency_key=self.obligation.idempotency_key,
            attempt_id=None, financial_status=None,
            outcome=PaymentOutcome.RECONCILIATION_REQUIRED,
            requires_reconciliation=True,
        )
        with self.assertRaises(InvalidPaymentRequestError):
            orchestrator.reconcile(wrong, uncertain)

    def test_instances_have_no_shared_orchestration_state(self):
        approved, approved_adapter = self._orchestrator(SimulationScenario.APPROVED)
        rejected, rejected_adapter = self._orchestrator(SimulationScenario.REJECTED)
        self.assertEqual(approved.process(self.obligation).outcome,
                         PaymentOutcome.APPROVED)
        self.assertEqual(rejected.process(self.obligation).outcome,
                         PaymentOutcome.REJECTED)
        self.assertEqual(approved_adapter.attempt_count, 1)
        self.assertEqual(rejected_adapter.attempt_count, 1)

    def test_orchestrator_imports_only_neutral_contract_boundary(self):
        path = Path(__file__).parents[1] / "app" / "services" / "payment_orchestration.py"
        tree = ast.parse(path.read_text(), filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        self.assertEqual(imports, {"dataclasses", "decimal", "enum",
                                   "app.services.psp_contract"})
        source = path.read_text()
        for forbidden in ("ScenarioController", "SimulationScenario", "sleep(",
                          "random", "app.models", "subscription", "credit"):
            self.assertNotIn(forbidden, source)

    def test_process_and_reconcile_make_one_explicit_adapter_call_each(self):
        adapter = UncertainWithoutIdentifierAdapter()
        orchestrator = InMemoryPaymentOrchestrator(adapter)
        uncertain = orchestrator.process(self.obligation)
        self.assertEqual(adapter.create_calls, 1)
        orchestrator.reconcile(self.obligation, uncertain)
        self.assertEqual(adapter.create_calls, 2)


if __name__ == "__main__":
    unittest.main()
