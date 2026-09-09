import ast
import inspect
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import app.services.psp_contract as psp_contract
import app.services.psp_simulator as psp_simulator
from app.services.psp_contract import (
    AttemptNotFoundError,
    IdempotencyConflictError,
    PSPAdapter,
    PaymentAttemptStatus,
    UncertainResponseError,
)
from app.services.psp_simulator import (
    CreationOutcome,
    InMemoryPSPSimulator,
    ScenarioController,
    SimulationScenario,
    SimulatorConfigurationError,
)


class InMemoryPSPSimulatorTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
        self.generated_ids = iter(("sim-001", "sim-002", "sim-003"))
        self.scenarios = ScenarioController((SimulationScenario.PENDING,))
        self.simulator = InMemoryPSPSimulator(
            id_factory=lambda: next(self.generated_ids),
            clock=lambda: self.now,
            scenario_controller=self.scenarios,
        )

    def _create(self, **overrides):
        values = {
            "internal_reference": "order-001",
            "amount": Decimal("1250.50"),
            "currency": "ars",
            "idempotency_key": "idem-001",
        }
        values.update(overrides)
        return self.simulator.create_attempt(**values)

    def _simulator_for(self, *scenarios):
        controller = ScenarioController(scenarios)
        generated_ids = iter(("sim-001", "sim-002", "sim-003"))
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: next(generated_ids),
            clock=lambda: self.now,
            scenario_controller=controller,
        )
        return simulator, controller

    def test_simulator_satisfies_neutral_adapter_contract(self):
        adapter: PSPAdapter = self.simulator

        self.assertIsInstance(adapter, PSPAdapter)
        created = adapter.create_attempt(
            internal_reference="order-001",
            amount=Decimal("1250.50"),
            currency="ARS",
            idempotency_key="idem-001",
        )
        self.assertIs(adapter.get_attempt(created.attempt_id), created)

    def test_neutral_creation_signature_has_no_simulation_instruction(self):
        parameters = inspect.signature(PSPAdapter.create_attempt).parameters

        self.assertNotIn("outcome", parameters)
        self.assertNotIn("scenario", parameters)
        self.assertNotIn("approved", parameters)
        self.assertNotIn("should_timeout", parameters)
        with self.assertRaises(TypeError):
            self._create(outcome=SimulationScenario.APPROVED)

        self.assertIs(CreationOutcome, SimulationScenario)

    def test_uncertain_error_accepts_absent_or_exact_opaque_identifier(self):
        without_identifier = UncertainResponseError("response unavailable")
        with_identifier = UncertainResponseError(
            "response unavailable", attempt_id=" provider/id: A-01 "
        )

        self.assertIsNone(without_identifier.attempt_id)
        self.assertEqual(with_identifier.attempt_id, " provider/id: A-01 ")
        with self.assertRaises(ValueError):
            UncertainResponseError("response unavailable", attempt_id="")
        with self.assertRaises(ValueError):
            UncertainResponseError("response unavailable", attempt_id="   ")
        with self.assertRaises(ValueError):
            UncertainResponseError("response unavailable", attempt_id=123)

    def test_valid_creation_normalizes_data_and_is_consultable(self):
        created = self._create(internal_reference=" order-001 ", currency=" ars ")

        self.assertIs(self.simulator.get_attempt(created.attempt_id), created)
        self.assertEqual(created.internal_reference, "order-001")
        self.assertEqual(created.amount, Decimal("1250.50"))
        self.assertEqual(created.currency, "ARS")
        self.assertEqual(created.created_at, self.now)
        self.assertEqual(created.attempt_id, "sim-001")

    def test_approved_rejected_and_pending_scenarios_are_deterministic(self):
        simulator, _ = self._simulator_for(
            SimulationScenario.APPROVED,
            SimulationScenario.REJECTED,
            SimulationScenario.PENDING,
        )

        attempts = tuple(
            simulator.create_attempt(
                internal_reference=f"order-{index}",
                amount=Decimal("1"),
                currency="ARS",
                idempotency_key=f"key-{index}",
            )
            for index in range(3)
        )

        self.assertEqual(
            tuple(attempt.status for attempt in attempts),
            (
                PaymentAttemptStatus.APPROVED,
                PaymentAttemptStatus.REJECTED,
                PaymentAttemptStatus.PENDING,
            ),
        )

    def test_identical_replay_returns_original_without_consuming_scenario(self):
        simulator, controller = self._simulator_for(
            SimulationScenario.PENDING,
            SimulationScenario.APPROVED,
        )
        first = simulator.create_attempt(
            internal_reference="order-001",
            amount=Decimal("1.0"),
            currency="ars",
            idempotency_key="idem-001",
        )
        replay = simulator.create_attempt(
            internal_reference=" order-001 ",
            amount=Decimal("1.00"),
            currency=" ARS ",
            idempotency_key=" idem-001 ",
        )

        self.assertIs(replay, first)
        self.assertEqual(simulator.attempt_count, 1)
        self.assertEqual(controller.remaining_count, 1)

    def test_conflicts_do_not_mutate_original_or_consume_scenario(self):
        for field_name, value in (
            ("internal_reference", "order-002"),
            ("amount", Decimal("2")),
            ("currency", "USD"),
        ):
            with self.subTest(field_name=field_name):
                simulator, controller = self._simulator_for(
                    SimulationScenario.PENDING,
                    SimulationScenario.APPROVED,
                )
                original = simulator.create_attempt(
                    internal_reference="order-001",
                    amount=Decimal("1"),
                    currency="ARS",
                    idempotency_key="idem-001",
                )
                conflicting = {
                    "internal_reference": "order-001",
                    "amount": Decimal("1"),
                    "currency": "ARS",
                    "idempotency_key": "idem-001",
                }
                conflicting[field_name] = value
                with self.assertRaises(IdempotencyConflictError):
                    simulator.create_attempt(**conflicting)

                self.assertIs(simulator.get_attempt(original.attempt_id), original)
                self.assertEqual(simulator.attempt_count, 1)
                self.assertEqual(controller.remaining_count, 1)

    def test_validation_errors_do_not_consume_scenario_or_store_state(self):
        invalid_requests = (
            {"internal_reference": " "},
            {"currency": ""},
            {"idempotency_key": None},
            {"amount": 1.25},
            {"amount": Decimal("0")},
            {"amount": Decimal("-1")},
            {"amount": Decimal("NaN")},
            {"amount": Decimal("Infinity")},
        )
        for overrides in invalid_requests:
            with self.subTest(overrides=overrides):
                with self.assertRaises((TypeError, ValueError)):
                    self._create(**overrides)
                self.assertEqual(self.simulator.attempt_count, 0)
                self.assertEqual(self.scenarios.remaining_count, 1)

    def test_two_new_operations_consume_scenarios_in_order(self):
        simulator, controller = self._simulator_for(
            SimulationScenario.REJECTED,
            SimulationScenario.APPROVED,
        )

        first = simulator.create_attempt(
            internal_reference="order-001", amount=Decimal("1"),
            currency="ARS", idempotency_key="key-001",
        )
        second = simulator.create_attempt(
            internal_reference="order-002", amount=Decimal("2"),
            currency="ARS", idempotency_key="key-002",
        )

        self.assertEqual(first.status, PaymentAttemptStatus.REJECTED)
        self.assertEqual(second.status, PaymentAttemptStatus.APPROVED)
        self.assertEqual(controller.remaining_count, 0)

    def test_missing_scenario_is_explicit_and_leaves_no_state(self):
        simulator, controller = self._simulator_for()

        with self.assertRaisesRegex(
            SimulatorConfigurationError, "no simulation scenario is configured"
        ):
            simulator.create_attempt(
                internal_reference="order-001", amount=Decimal("1"),
                currency="ARS", idempotency_key="key-001",
            )

        self.assertEqual(simulator.attempt_count, 0)
        self.assertEqual(controller.remaining_count, 0)

    def test_uncertain_response_exposes_consultable_pending_attempt(self):
        simulator, controller = self._simulator_for(SimulationScenario.UNCERTAIN)

        with self.assertRaises(UncertainResponseError) as captured:
            simulator.create_attempt(
                internal_reference="order-001", amount=Decimal("1"),
                currency="ARS", idempotency_key="key-001",
            )

        stored = simulator.get_attempt(captured.exception.attempt_id)
        self.assertEqual(stored.status, PaymentAttemptStatus.PENDING)
        self.assertEqual(simulator.attempt_count, 1)
        self.assertEqual(controller.remaining_count, 0)

    def test_replay_after_uncertainty_recovers_without_new_scenario(self):
        simulator, controller = self._simulator_for(SimulationScenario.UNCERTAIN)
        request = {
            "internal_reference": "order-001", "amount": Decimal("1"),
            "currency": "ARS", "idempotency_key": "key-001",
        }
        with self.assertRaises(UncertainResponseError) as captured:
            simulator.create_attempt(**request)

        replay = simulator.create_attempt(**request)

        self.assertEqual(replay.attempt_id, captured.exception.attempt_id)
        self.assertEqual(replay.status, PaymentAttemptStatus.PENDING)
        self.assertEqual(simulator.attempt_count, 1)
        self.assertEqual(controller.remaining_count, 0)

    def test_instances_keep_storage_and_scenarios_isolated(self):
        first, first_controller = self._simulator_for(SimulationScenario.APPROVED)
        second, second_controller = self._simulator_for(SimulationScenario.REJECTED)

        first_attempt = first.create_attempt(
            internal_reference="order-001", amount=Decimal("1"),
            currency="ARS", idempotency_key="same-key",
        )
        second_attempt = second.create_attempt(
            internal_reference="order-001", amount=Decimal("1"),
            currency="ARS", idempotency_key="same-key",
        )

        self.assertEqual(first_attempt.status, PaymentAttemptStatus.APPROVED)
        self.assertEqual(second_attempt.status, PaymentAttemptStatus.REJECTED)
        self.assertEqual(first_controller.remaining_count, 0)
        self.assertEqual(second_controller.remaining_count, 0)

    def test_fresh_instance_starts_without_attempts(self):
        simulator, controller = self._simulator_for(SimulationScenario.PENDING)

        self.assertEqual(simulator.attempt_count, 0)
        self.assertEqual(controller.remaining_count, 1)

    def test_scenario_controller_enqueue_is_ordered_atomic_and_isolated(self):
        first = ScenarioController()
        second = ScenarioController()

        first.enqueue(SimulationScenario.APPROVED)
        first.enqueue(SimulationScenario.REJECTED)
        self.assertEqual(first.remaining_count, 2)
        with self.assertRaises(SimulatorConfigurationError):
            first.enqueue("PENDING")
        self.assertEqual(first.remaining_count, 2)
        self.assertEqual(second.remaining_count, 0)
        self.assertIs(first.consume(), SimulationScenario.APPROVED)
        self.assertIs(first.consume(), SimulationScenario.REJECTED)
        self.assertEqual(first.remaining_count, 0)

    def test_attempt_is_immutable(self):
        attempt = self._create()

        with self.assertRaises(FrozenInstanceError):
            attempt.status = PaymentAttemptStatus.APPROVED

    def test_unknown_attempt_uses_neutral_error(self):
        with self.assertRaises(AttemptNotFoundError):
            self.simulator.get_attempt("missing")

    def test_neutral_errors_are_distinct_and_match_observable_failures(self):
        self.assertIsNot(AttemptNotFoundError, IdempotencyConflictError)
        self.assertIsNot(AttemptNotFoundError, UncertainResponseError)
        self.assertIsNot(IdempotencyConflictError, UncertainResponseError)

        with self.assertRaises(AttemptNotFoundError):
            self.simulator.get_attempt("missing")

        conflict_simulator, _ = self._simulator_for(SimulationScenario.PENDING)
        request = {
            "internal_reference": "order-001", "amount": Decimal("1"),
            "currency": "ARS", "idempotency_key": "key-001",
        }
        conflict_simulator.create_attempt(**request)
        with self.assertRaises(IdempotencyConflictError):
            conflict_simulator.create_attempt(**{**request, "currency": "USD"})

        uncertain_simulator, _ = self._simulator_for(SimulationScenario.UNCERTAIN)
        with self.assertRaises(UncertainResponseError):
            uncertain_simulator.create_attempt(**request)

    def test_invalid_simulator_dependencies_are_explicit(self):
        with self.assertRaises(SimulatorConfigurationError):
            InMemoryPSPSimulator(
                id_factory=None, clock=lambda: self.now,
                scenario_controller=self.scenarios,
            )
        with self.assertRaises(SimulatorConfigurationError):
            ScenarioController(("APPROVED",))

    def test_duplicate_identifier_does_not_consume_next_scenario(self):
        controller = ScenarioController(
            (SimulationScenario.PENDING, SimulationScenario.APPROVED)
        )
        simulator = InMemoryPSPSimulator(
            id_factory=lambda: "same-id", clock=lambda: self.now,
            scenario_controller=controller,
        )
        simulator.create_attempt(
            internal_reference="order-001", amount=Decimal("1"),
            currency="ARS", idempotency_key="key-001",
        )

        with self.assertRaises(SimulatorConfigurationError):
            simulator.create_attempt(
                internal_reference="order-002", amount=Decimal("2"),
                currency="ARS", idempotency_key="key-002",
            )

        self.assertEqual(simulator.attempt_count, 1)
        self.assertEqual(controller.remaining_count, 1)

    def test_historical_reexports_are_canonical_objects(self):
        self.assertIs(psp_simulator.SimulatedPaymentAttempt, psp_contract.PaymentAttempt)
        self.assertIs(psp_simulator.AttemptStatus, psp_contract.PaymentAttemptStatus)
        self.assertIs(psp_simulator.AttemptNotFoundError, psp_contract.AttemptNotFoundError)
        self.assertIs(
            psp_simulator.IdempotencyConflictError,
            psp_contract.IdempotencyConflictError,
        )
        self.assertIs(
            psp_simulator.UncertainResponseError,
            psp_contract.UncertainResponseError,
        )

    def test_contract_and_simulator_import_only_allowed_boundaries(self):
        services_dir = Path(__file__).parents[1] / "app" / "services"
        imported_modules = set()
        for filename in ("psp_contract.py", "psp_simulator.py"):
            tree = ast.parse((services_dir / filename).read_text(), filename=filename)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_modules.add(node.module)

        allowed = {
            "collections", "dataclasses", "datetime", "decimal", "enum", "typing",
            "app.services.psp_contract",
        }
        self.assertEqual(imported_modules, allowed)


if __name__ == "__main__":
    unittest.main()
