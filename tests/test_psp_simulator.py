import importlib.util
import sys
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "app" / "services" / "psp_simulator.py"
MODULE_SPEC = importlib.util.spec_from_file_location("psp_simulator_under_test", MODULE_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError("Unable to load the PSP simulator module")
PSP_SIMULATOR = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = PSP_SIMULATOR
MODULE_SPEC.loader.exec_module(PSP_SIMULATOR)

AttemptNotFoundError = PSP_SIMULATOR.AttemptNotFoundError
AttemptStatus = PSP_SIMULATOR.AttemptStatus
CreationOutcome = PSP_SIMULATOR.CreationOutcome
IdempotencyConflictError = PSP_SIMULATOR.IdempotencyConflictError
InMemoryPSPSimulator = PSP_SIMULATOR.InMemoryPSPSimulator
SimulatorConfigurationError = PSP_SIMULATOR.SimulatorConfigurationError
UncertainResponseError = PSP_SIMULATOR.UncertainResponseError


class InMemoryPSPSimulatorTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)
        self.generated_ids = iter(("sim-001", "sim-002", "sim-003"))
        self.simulator = InMemoryPSPSimulator(
            id_factory=lambda: next(self.generated_ids),
            clock=lambda: self.now,
        )

    def _create(self, **overrides):
        values = {
            "internal_reference": "order-001",
            "amount": Decimal("1250.50"),
            "currency": "ars",
            "idempotency_key": "idem-001",
            "outcome": CreationOutcome.PENDING,
        }
        values.update(overrides)
        return self.simulator.create_attempt(**values)

    def test_valid_creation_and_lookup(self):
        created = self._create()

        self.assertIs(self.simulator.get_attempt(created.attempt_id), created)
        self.assertEqual(created.amount, Decimal("1250.50"))
        self.assertEqual(created.currency, "ARS")

    def test_identical_replay_returns_existing_attempt(self):
        first = self._create()
        replay = self._create()

        self.assertIs(replay, first)
        self.assertEqual(replay.attempt_id, "sim-001")
        self.assertEqual(self.simulator.attempt_count, 1)

    def test_replay_accepts_canonically_equivalent_content(self):
        first = self._create()
        replay = self._create(
            internal_reference=" order-001 ",
            amount=Decimal("1250.500"),
            currency=" ARS ",
            idempotency_key=" idem-001 ",
        )

        self.assertIs(replay, first)

    def test_same_key_with_different_reference_is_rejected(self):
        self._create()

        with self.assertRaises(IdempotencyConflictError):
            self._create(internal_reference="order-002")

    def test_same_key_with_different_amount_is_rejected(self):
        self._create()

        with self.assertRaises(IdempotencyConflictError):
            self._create(amount=Decimal("1250.51"))

    def test_same_key_with_different_currency_is_rejected(self):
        self._create()

        with self.assertRaises(IdempotencyConflictError):
            self._create(currency="USD")

    def test_approved_status_is_configurable(self):
        attempt = self._create(outcome=CreationOutcome.APPROVED)

        self.assertEqual(attempt.status, AttemptStatus.APPROVED)

    def test_rejected_status_is_configurable(self):
        attempt = self._create(outcome=CreationOutcome.REJECTED)

        self.assertEqual(attempt.status, AttemptStatus.REJECTED)

    def test_pending_status_is_configurable(self):
        attempt = self._create(outcome=CreationOutcome.PENDING)

        self.assertEqual(attempt.status, AttemptStatus.PENDING)

    def test_uncertain_creation_stores_an_attempt_before_raising(self):
        with self.assertRaises(UncertainResponseError):
            self._create(outcome=CreationOutcome.UNCERTAIN)

        self.assertEqual(self.simulator.attempt_count, 1)

    def test_replay_after_uncertain_creation_recovers_without_duplicate(self):
        with self.assertRaises(UncertainResponseError):
            self._create(outcome=CreationOutcome.UNCERTAIN)

        replay = self._create(outcome=CreationOutcome.APPROVED)

        self.assertEqual(replay.attempt_id, "sim-001")
        self.assertEqual(self.simulator.attempt_count, 1)

    def test_transport_uncertainty_is_separate_from_stored_status(self):
        with self.assertRaises(UncertainResponseError):
            self._create(outcome=CreationOutcome.UNCERTAIN)

        replay = self._create()

        self.assertEqual(replay.status, AttemptStatus.PENDING)
        self.assertNotEqual(replay.status.value, CreationOutcome.UNCERTAIN.value)

    def test_clock_controls_timestamp(self):
        attempt = self._create()

        self.assertEqual(attempt.created_at, self.now)

    def test_identifier_factory_controls_identifier(self):
        first = self._create()
        second = self._create(idempotency_key="idem-002")

        self.assertEqual((first.attempt_id, second.attempt_id), ("sim-001", "sim-002"))

    def test_two_instances_have_isolated_storage(self):
        other = InMemoryPSPSimulator(
            id_factory=lambda: "other-001",
            clock=lambda: self.now,
        )
        self._create()
        other_attempt = other.create_attempt(
            internal_reference="order-001",
            amount=Decimal("1250.50"),
            currency="ARS",
            idempotency_key="idem-001",
            outcome=CreationOutcome.APPROVED,
        )

        self.assertEqual(self.simulator.attempt_count, 1)
        self.assertEqual(other.attempt_count, 1)
        self.assertEqual(other_attempt.attempt_id, "other-001")
        with self.assertRaises(AttemptNotFoundError):
            other.get_attempt("sim-001")

    def test_each_test_receives_fresh_storage(self):
        self.assertEqual(self.simulator.attempt_count, 0)

    def test_float_amount_is_rejected(self):
        with self.assertRaises(TypeError):
            self._create(amount=1.25)

        self.assertEqual(self.simulator.attempt_count, 0)

    def test_minimum_input_validation(self):
        for field_name, invalid_value in (
            ("internal_reference", " "),
            ("currency", ""),
            ("idempotency_key", None),
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    self._create(**{field_name: invalid_value})

        for invalid_amount in (
            Decimal("0"),
            Decimal("-1"),
            Decimal("NaN"),
            Decimal("Infinity"),
        ):
            with self.subTest(amount=invalid_amount):
                with self.assertRaises(ValueError):
                    self._create(amount=invalid_amount)

    def test_returned_attempt_is_immutable(self):
        attempt = self._create()

        with self.assertRaises(FrozenInstanceError):
            attempt.status = AttemptStatus.APPROVED

        self.assertEqual(
            self.simulator.get_attempt(attempt.attempt_id).status,
            AttemptStatus.PENDING,
        )

    def test_unknown_attempt_is_distinct_from_other_errors(self):
        with self.assertRaises(AttemptNotFoundError):
            self.simulator.get_attempt("missing")

    def test_invalid_factories_and_duplicate_ids_are_rejected(self):
        with self.assertRaises(SimulatorConfigurationError):
            InMemoryPSPSimulator(id_factory=None, clock=lambda: self.now)

        duplicate = InMemoryPSPSimulator(
            id_factory=lambda: "same-id",
            clock=lambda: self.now,
        )
        duplicate.create_attempt(
            internal_reference="order-001",
            amount=Decimal("1"),
            currency="ARS",
            idempotency_key="key-001",
            outcome=CreationOutcome.PENDING,
        )
        with self.assertRaises(SimulatorConfigurationError):
            duplicate.create_attempt(
                internal_reference="order-002",
                amount=Decimal("2"),
                currency="ARS",
                idempotency_key="key-002",
                outcome=CreationOutcome.PENDING,
            )


if __name__ == "__main__":
    unittest.main()
