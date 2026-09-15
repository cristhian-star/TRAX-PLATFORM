from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import inspect
from threading import Barrier
import unittest

from app.services.in_memory_psp_payment_order_creation_adapter import (
    InMemoryPSPPaymentOrderCreationAdapter,
)
from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError,
    PSPPaymentOrderCreationAdapter,
    PaymentOrderCreationCommand,
    PaymentOrderIdempotencyConflictError,
    validate_payment_order_creation_result,
)


class InMemoryPSPPaymentOrderCreationAdapterTest(unittest.TestCase):
    def setUp(self):
        created_at = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        self.command = PaymentOrderCreationCommand(
            local_order_id="local-order-0001",
            obligation_reference="obligation-0001",
            professional_id=17,
            amount=Decimal("1250.50"),
            currency="ARS",
            concept="Servicio acordado",
            external_reference="external-reference-0001",
            idempotency_key="private-idempotency-key-0001",
            created_at=created_at,
            expires_at=created_at + timedelta(hours=72),
        )
        self.adapter = InMemoryPSPPaymentOrderCreationAdapter()

    def test_satisfies_creation_protocol_at_runtime(self):
        self.assertIsInstance(self.adapter, PSPPaymentOrderCreationAdapter)
        self.assertEqual(
            tuple(inspect.signature(self.adapter.create_payment_order).parameters),
            ("command",),
        )

    def test_valid_creation_has_deterministic_neutral_content(self):
        result = self.adapter.create_payment_order(self.command)
        digest = hashlib.sha256(
            self.command.idempotency_key.encode("utf-8")
        ).hexdigest()

        self.assertIs(
            validate_payment_order_creation_result(self.command, result), result
        )
        self.assertEqual(result.external_order_id, f"fake-order-{digest}")
        self.assertEqual(
            result.checkout_url,
            f"https://checkout.example.test/payment-orders/{digest}",
        )
        self.assertEqual(result.provider, "fake")
        self.assertIs(result.live_mode, False)

    def test_identical_replay_returns_exact_stored_object(self):
        first = self.adapter.create_payment_order(self.command)
        replay = self.adapter.create_payment_order(self.command)

        self.assertIs(replay, first)

    def test_equal_command_from_another_instance_is_deterministic(self):
        first = self.adapter.create_payment_order(self.command)
        second = InMemoryPSPPaymentOrderCreationAdapter().create_payment_order(
            self.command
        )

        self.assertEqual(second, first)
        self.assertIsNot(second, first)

    def test_same_key_conflicts_when_any_material_field_changes(self):
        self.adapter.create_payment_order(self.command)
        shifted_created_at = self.command.created_at + timedelta(seconds=1)
        cases = (
            ("local_order_id", replace(
                self.command, local_order_id="local-order-0002"
            )),
            ("obligation_reference", replace(
                self.command, obligation_reference="obligation-0002"
            )),
            ("professional_id", replace(self.command, professional_id=18)),
            ("amount", replace(self.command, amount=Decimal("1250.51"))),
            ("concept", replace(self.command, concept="Otro servicio")),
            ("external_reference", replace(
                self.command, external_reference="external-reference-0002"
            )),
            ("timestamps", replace(
                self.command,
                created_at=shifted_created_at,
                expires_at=shifted_created_at + timedelta(hours=72),
            )),
        )
        for field, conflicting in cases:
            with self.subTest(field=field), self.assertRaises(
                PaymentOrderIdempotencyConflictError
            ):
                self.adapter.create_payment_order(conflicting)

        self.assertIs(
            self.adapter.create_payment_order(self.command),
            self.adapter.create_payment_order(self.command),
        )

    def test_distinct_keys_are_independent(self):
        first = self.adapter.create_payment_order(self.command)
        second_command = replace(
            self.command,
            local_order_id="local-order-0002",
            idempotency_key="private-idempotency-key-0002",
        )
        second = self.adapter.create_payment_order(second_command)

        self.assertNotEqual(second.external_order_id, first.external_order_id)
        self.assertIs(self.adapter.create_payment_order(self.command), first)
        self.assertIs(self.adapter.create_payment_order(second_command), second)

    def test_instances_do_not_share_storage(self):
        first = self.adapter.create_payment_order(self.command)
        second_adapter = InMemoryPSPPaymentOrderCreationAdapter()
        changed = replace(self.command, professional_id=99)
        second = second_adapter.create_payment_order(changed)

        self.assertEqual(second.external_order_id, first.external_order_id)
        self.assertIs(second_adapter.create_payment_order(changed), second)
        with self.assertRaises(PaymentOrderIdempotencyConflictError):
            self.adapter.create_payment_order(changed)

    def test_non_command_objects_use_public_request_error(self):
        for value in (None, object(), {}, "command"):
            with self.subTest(value=type(value)), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self.adapter.create_payment_order(value)

    def test_key_is_absent_from_outputs_and_conflict_messages(self):
        result = self.adapter.create_payment_order(self.command)

        self.assertNotIn(self.command.idempotency_key, result.external_order_id)
        self.assertNotIn(self.command.idempotency_key, result.checkout_url)
        with self.assertRaises(PaymentOrderIdempotencyConflictError) as captured:
            self.adapter.create_payment_order(
                replace(self.command, professional_id=18)
            )
        self.assertNotIn(self.command.idempotency_key, str(captured.exception))
        self.assertNotIn(self.command.idempotency_key, repr(captured.exception))

    def test_concurrent_identical_calls_converge_on_one_object(self):
        with ThreadPoolExecutor(max_workers=16) as executor:
            results = tuple(
                executor.map(
                    self.adapter.create_payment_order,
                    (self.command,) * 64,
                )
            )

        self.assertEqual(len(results), 64)
        self.assertTrue(all(result is results[0] for result in results))

    def test_concurrent_conflicting_commands_have_one_consistent_winner(self):
        commands = {
            "first": self.command,
            "second": replace(
                self.command,
                local_order_id="local-order-0002",
                obligation_reference="obligation-0002",
                external_reference="external-reference-0002",
            ),
        }
        calls_per_command = 16
        calls = tuple(
            (label, command)
            for _ in range(calls_per_command)
            for label, command in commands.items()
        )
        start = Barrier(len(calls))

        def invoke(label, command):
            start.wait(timeout=10)
            try:
                return label, self.adapter.create_payment_order(command), None
            except Exception as error:  # Capture worker outcomes for assertion.
                return label, None, error

        with ThreadPoolExecutor(max_workers=len(calls)) as executor:
            observations = tuple(
                executor.map(lambda call: invoke(*call), calls)
            )

        successes = {
            label: tuple(
                result
                for observed_label, result, error in observations
                if observed_label == label and error is None
            )
            for label in commands
        }
        errors = {
            label: tuple(
                error
                for observed_label, result, error in observations
                if observed_label == label and error is not None
            )
            for label in commands
        }
        winners = tuple(label for label, results in successes.items() if results)

        self.assertEqual(len(winners), 1)
        winner = winners[0]
        loser = next(label for label in commands if label != winner)
        self.assertEqual(len(successes[winner]), calls_per_command)
        self.assertTrue(
            all(result is successes[winner][0] for result in successes[winner])
        )
        self.assertIs(
            validate_payment_order_creation_result(
                commands[winner], successes[winner][0]
            ),
            successes[winner][0],
        )
        self.assertEqual(errors[winner], ())
        self.assertEqual(successes[loser], ())
        self.assertEqual(len(errors[loser]), calls_per_command)
        self.assertTrue(
            all(
                isinstance(error, PaymentOrderIdempotencyConflictError)
                for error in errors[loser]
            )
        )


if __name__ == "__main__":
    unittest.main()
