from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import inspect
import traceback
import unittest

from app.services.psp_contract import PSPAdapter, PSPPaymentQueryAdapter
from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError,
    InvalidPaymentOrderCreationResultError,
    PSPPaymentOrderCreationAdapter,
    PaymentOrderCreationCommand,
    PaymentOrderCreationResult,
    PaymentOrderCreationUncertainError,
    PaymentOrderIdempotencyConflictError,
    validate_payment_order_creation_result,
)


class QueryOnlyAdapter:
    @property
    def provider(self):
        return "provider"

    @property
    def live_mode(self):
        return False

    def query_payment(self, external_attempt_id):
        raise NotImplementedError


class CreationOnlyAdapter:
    def create_payment_order(self, command):
        raise NotImplementedError


class PaymentOrderContractTest(unittest.TestCase):
    def setUp(self):
        self.created_at = datetime(2026, 9, 14, 13, 0, tzinfo=timezone.utc)
        self.command_values = {
            "local_order_id": "order-local-0001",
            "obligation_reference": "obligation-0001",
            "professional_id": 7,
            "amount": Decimal("1250.50"),
            "currency": "ARS",
            "concept": "Servicio acordado",
            "external_reference": "external-order-0001",
            "idempotency_key": "payment-order-key-0001",
            "created_at": self.created_at,
            "expires_at": self.created_at + timedelta(hours=72),
        }

    def _command(self, **overrides):
        values = dict(self.command_values)
        values.update(overrides)
        return PaymentOrderCreationCommand(**values)

    def _result(self, command=None, **overrides):
        command = command or self._command()
        values = {
            "local_order_id": command.local_order_id,
            "obligation_reference": command.obligation_reference,
            "external_reference": command.external_reference,
            "amount": command.amount,
            "currency": command.currency,
            "concept": command.concept,
            "idempotency_key": command.idempotency_key,
            "created_at": command.created_at,
            "expires_at": command.expires_at,
            "external_order_id": "provider-order-0001",
            "checkout_url": "https://checkout.example.test/pay/order-0001?mode=test",
            "provider": "provider",
            "live_mode": False,
        }
        values.update(overrides)
        return PaymentOrderCreationResult(**values)

    def test_valid_command_and_result_are_immutable(self):
        command = self._command()
        result = self._result(command)
        self.assertIs(validate_payment_order_creation_result(command, result), result)
        with self.assertRaises(FrozenInstanceError):
            command.amount = Decimal("1")
        with self.assertRaises(FrozenInstanceError):
            result.live_mode = True

    def test_identifiers_and_idempotency_are_strict(self):
        fields = (
            "local_order_id",
            "obligation_reference",
            "external_reference",
        )
        for field in fields:
            for value in ("", " value", "value ", "value/part", "á", "x" * 161):
                with self.subTest(field=field, value=repr(value)), self.assertRaises(
                    InvalidPaymentOrderCreationRequestError
                ):
                    self._command(**{field: value})
        for value in ("", "short", " key-with-valid-length", "key-with-valid-length "):
            with self.subTest(key=repr(value)), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self._command(idempotency_key=value)
        for value in (None, True, 0, -1, "7"):
            with self.subTest(professional_id=value), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self._command(professional_id=value)

    def test_amount_is_positive_finite_decimal_with_at_most_two_decimals(self):
        for value in (
            Decimal("1250.5"),
            Decimal("1250.50"),
            Decimal("125050e-2"),
            Decimal("1.2505e3"),
        ):
            with self.subTest(valid=value):
                amount = self._command(amount=value).amount
                self.assertEqual(amount, Decimal("1250.50"))
                self.assertEqual(amount.as_tuple().exponent, -2)
        invalid = (
            Decimal("0"), Decimal("-1"), Decimal("NaN"),
            Decimal("Infinity"), Decimal("-Infinity"), Decimal("1.001"),
            1.25, True, 1, "1.25", None,
        )
        for value in invalid:
            with self.subTest(invalid=repr(value)), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self._command(amount=value)

        with localcontext() as context:
            context.prec = 2
            amount = self._command(amount=Decimal("1250.5")).amount
        self.assertEqual(amount, Decimal("1250.50"))
        self.assertEqual(amount.as_tuple().exponent, -2)

    def test_equivalent_amount_scales_are_canonical_for_correspondence(self):
        command = self._command(amount=Decimal("1250.5"))
        result = self._result(command, amount=Decimal("1250.50"))
        self.assertEqual(command.amount.as_tuple().exponent, -2)
        self.assertEqual(result.amount.as_tuple().exponent, -2)
        self.assertIs(validate_payment_order_creation_result(command, result), result)

        with self.assertRaises(InvalidPaymentOrderCreationResultError):
            validate_payment_order_creation_result(
                command,
                self._result(command, amount=Decimal("1250.01")),
            )
        with self.assertRaises(InvalidPaymentOrderCreationResultError):
            self._result(command, amount=Decimal("1250.501"))

    def test_extreme_decimals_are_contained_at_each_public_boundary(self):
        invalid_values = (
            Decimal("1E+1000000"),
            Decimal("1E-1000000"),
            Decimal("1E+62"),
            Decimal("1E+63"),
            Decimal("1E-3"),
            Decimal("9" * 65),
            Decimal("NaN"),
            Decimal("sNaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
        )
        for value in invalid_values:
            with self.subTest(boundary="command", value=value):
                with self.assertRaises(
                    InvalidPaymentOrderCreationRequestError
                ) as captured:
                    self._command(amount=value)
                self.assertIsNone(captured.exception.__cause__)
                self.assertIsNone(captured.exception.__context__)
                self.assertEqual(
                    self._command(amount=Decimal("10.5")).amount,
                    Decimal("10.50"),
                )

            with self.subTest(boundary="result", value=value):
                with self.assertRaises(
                    InvalidPaymentOrderCreationResultError
                ) as captured:
                    self._result(amount=value)
                self.assertIsNone(captured.exception.__cause__)
                self.assertIsNone(captured.exception.__context__)
                self.assertEqual(
                    self._result(amount=Decimal("10.5")).amount,
                    Decimal("10.50"),
                )

        for value, expected in (
            (Decimal("1E+61"), Decimal("1" + "0" * 61 + ".00")),
            (Decimal("1E-2"), Decimal("0.01")),
        ):
            with self.subTest(valid_boundary=value):
                self.assertEqual(self._command(amount=value).amount, expected)

    def test_decimal_canonicalization_ignores_global_precision_and_traps(self):
        with localcontext() as context:
            context.prec = 1
            for signal in context.traps:
                context.traps[signal] = True
            command = self._command(amount=Decimal("1250.5"))
            result = self._result(command, amount=Decimal("1250.50"))
        self.assertEqual(command.amount, Decimal("1250.50"))
        self.assertEqual(result.amount, Decimal("1250.50"))
        self.assertIs(validate_payment_order_creation_result(command, result), result)

    def test_currency_concept_and_dates_are_strict(self):
        for currency in ("ars", "USD", " ARS", "ARS ", ""):
            with self.subTest(currency=currency), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self._command(currency=currency)
        for concept in ("", " concept", "concept ", "bad\nconcept", "x" * 201):
            with self.subTest(concept=repr(concept)), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self._command(concept=concept)
        naive = self.created_at.replace(tzinfo=None)
        for overrides in (
            {"created_at": naive},
            {"expires_at": naive},
            {"expires_at": self.created_at + timedelta(hours=71)},
            {"expires_at": self.created_at + timedelta(hours=73)},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                self._command(**overrides)

    def test_result_validates_provider_external_identity_and_strict_mode(self):
        for field, value in (
            ("external_order_id", ""),
            ("external_order_id", "unsafe/value"),
            ("provider", ""),
            ("provider", "provider.example"),
            ("live_mode", 0),
            ("live_mode", "false"),
            ("currency", "USD"),
            ("amount", Decimal("1.001")),
            ("concept", " unsafe"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(
                InvalidPaymentOrderCreationResultError
            ):
                self._result(**{field: value})
        self.assertIs(self._result(live_mode=True).live_mode, True)
        self.assertEqual(self._result(provider="  ProViDeR  ").provider, "provider")

    def test_checkout_url_requires_safe_absolute_https_structure(self):
        valid = (
            "https://checkout.example.test",
            "https://checkout.example.test/pay/1?source=mandobra",
            "https://127.0.0.1/pay/1",
        )
        for value in valid:
            with self.subTest(valid=value):
                self.assertEqual(self._result(checkout_url=value).checkout_url, value)
        invalid = (
            "", "/pay/1", "http://checkout.example.test/pay/1",
            "ftp://checkout.example.test/pay/1", "https:///pay/1",
            "https://user@checkout.example.test/pay/1",
            "https://user:pass@checkout.example.test/pay/1",
            "https://checkout.example.test/pay/1#fragment",
            "https://checkout.example.test/pay 1",
            " https://checkout.example.test/pay/1",
            "https://checkout.example.test/pay/1\n",
            "https://checkout.example.test/pay/%0A1",
            "https://checkout.example.test/pay/%201",
            "https://checkout.example.test/pay/%C3%A1",
            "https://checkout.example.test/pay/%broken",
            "https://checkout.example.test\\pay\\1",
            "https://checkout.exámple.test/pay/1",
            "https://checkout.example.test/pay/\u200b1",
            "https://-invalid.example/pay/1",
            "https://invalid-.example/pay/1",
            "https://checkout.example.test:invalid/pay/1",
        )
        for value in invalid:
            with self.subTest(invalid=repr(value)), self.assertRaises(
                InvalidPaymentOrderCreationResultError
            ):
                self._result(checkout_url=value)

    def test_percent_encoded_structural_separators_are_rejected(self):
        encoded_separators = (
            "%2F", "%2f", "%5C", "%5c", "%3F", "%3f",
            "%23", "%40", "%3A", "%3a",
        )
        for escape in encoded_separators:
            urls = (
                f"https://checkout.example.test/pay{escape}order",
                f"https://checkout.example.test/pay?value={escape}",
                f"https://checkout.example.test/pay{escape}one{escape}two",
            )
            for value in urls:
                with self.subTest(escape=escape, url=value), self.assertRaises(
                    InvalidPaymentOrderCreationResultError
                ):
                    self._result(checkout_url=value)

        for malformed in ("%", "%2", "%2G", "%G2"):
            with self.subTest(malformed=malformed), self.assertRaises(
                InvalidPaymentOrderCreationResultError
            ):
                self._result(
                    checkout_url=f"https://checkout.example.test/pay?value={malformed}"
                )

        safe_url = "https://checkout.example.test/pay/order?reference=%41bc-123_456"
        self.assertEqual(self._result(checkout_url=safe_url).checkout_url, safe_url)

    def test_percent_encoded_percent_blocks_all_double_encoding_levels(self):
        encoded_delimiters = (
            "%252F", "%255C", "%253F", "%2523", "%2540", "%253A",
        )
        for encoded in encoded_delimiters:
            for value in (
                f"https://checkout.example.test/pay/{encoded}",
                f"https://checkout.example.test/pay?value={encoded}",
                f"https://checkout.example.test/pay/{encoded}{encoded}",
                f"https://checkout.example.test/pay/%41{encoded}%42",
            ):
                with self.subTest(value=value), self.assertRaises(
                    InvalidPaymentOrderCreationResultError
                ):
                    self._result(checkout_url=value)

        for encoded in ("%25", "%25252F"):
            with self.subTest(encoded=encoded), self.assertRaises(
                InvalidPaymentOrderCreationResultError
            ):
                self._result(
                    checkout_url=f"https://checkout.example.test/pay?value={encoded}"
                )

    def test_timestamps_are_canonicalized_to_utc_before_correspondence(self):
        argentina = timezone(timedelta(hours=-3))
        local_created_at = datetime(2026, 9, 14, 10, 0, tzinfo=argentina)
        command = self._command(
            created_at=local_created_at,
            expires_at=local_created_at + timedelta(hours=72),
        )
        self.assertEqual(command.created_at, self.created_at)
        self.assertEqual(command.created_at.tzinfo, timezone.utc)
        self.assertEqual(command.expires_at.tzinfo, timezone.utc)

        result = self._result(
            command,
            created_at=self.created_at,
            expires_at=self.created_at + timedelta(hours=72),
        )
        self.assertIs(validate_payment_order_creation_result(command, result), result)
        self.assertEqual(result.created_at.tzinfo, timezone.utc)

        shifted_created_at = self.created_at + timedelta(seconds=1)
        shifted_result = self._result(
            command,
            created_at=shifted_created_at,
            expires_at=shifted_created_at + timedelta(hours=72),
        )
        with self.assertRaises(InvalidPaymentOrderCreationResultError):
            validate_payment_order_creation_result(command, shifted_result)

    def test_result_must_echo_every_canonical_shared_field_exactly(self):
        command = self._command()
        alterations = {
            "local_order_id": "order-local-0002",
            "obligation_reference": "obligation-0002",
            "external_reference": "external-order-0002",
            "amount": Decimal("1250.51"),
            "currency": "USD",
            "concept": "Otro servicio",
            "idempotency_key": "payment-order-key-0002",
            "created_at": command.created_at + timedelta(hours=1),
            "expires_at": command.expires_at + timedelta(hours=1),
        }
        for field, value in alterations.items():
            result = self._result(command)
            object.__setattr__(result, field, value)
            with self.subTest(field=field), self.assertRaises(
                InvalidPaymentOrderCreationResultError
            ):
                validate_payment_order_creation_result(command, result)

    def test_correspondence_rejects_wrong_types_without_accidental_equality(self):
        command = self._command()
        result = self._result(command)
        for invalid_command in (None, object(), self.command_values):
            with self.subTest(command=type(invalid_command)), self.assertRaises(
                InvalidPaymentOrderCreationRequestError
            ):
                validate_payment_order_creation_result(invalid_command, result)
        for invalid_result in (None, object(), vars):
            with self.subTest(result=invalid_result), self.assertRaises(
                InvalidPaymentOrderCreationResultError
            ):
                validate_payment_order_creation_result(command, invalid_result)

    def test_result_contains_no_financial_or_transport_fields(self):
        fields = set(PaymentOrderCreationResult.__dataclass_fields__)
        for forbidden in (
            "status", "financial_status", "approved", "token", "headers",
            "payload", "qr", "payment_attempt_status",
        ):
            self.assertNotIn(forbidden, fields)

    def test_creation_protocol_is_runtime_checkable_and_segregated(self):
        creation = CreationOnlyAdapter()
        query = QueryOnlyAdapter()
        self.assertIsInstance(creation, PSPPaymentOrderCreationAdapter)
        self.assertNotIsInstance(creation, PSPAdapter)
        self.assertNotIsInstance(creation, PSPPaymentQueryAdapter)
        self.assertIsInstance(query, PSPPaymentQueryAdapter)
        self.assertNotIsInstance(query, PSPPaymentOrderCreationAdapter)
        self.assertEqual(
            tuple(inspect.signature(
                PSPPaymentOrderCreationAdapter.create_payment_order
            ).parameters),
            ("self", "command"),
        )

    def test_exact_error_taxonomy_is_available(self):
        for error_type in (
            InvalidPaymentOrderCreationRequestError,
            InvalidPaymentOrderCreationResultError,
            PaymentOrderIdempotencyConflictError,
            PaymentOrderCreationUncertainError,
        ):
            self.assertTrue(issubclass(error_type, Exception))

    def test_validation_errors_do_not_expose_sensitive_values(self):
        marker = "PRIVATE-SENSITIVE-MARKER"
        cases = (
            lambda: self._command(local_order_id=marker + "/invalid"),
            lambda: self._result(external_order_id=marker + "/invalid"),
            lambda: self._result(
                checkout_url=f"https://user:{marker}@checkout.example.test/pay"
            ),
        )
        for case in cases:
            captured = None
            try:
                case()
            except (InvalidPaymentOrderCreationRequestError,
                    InvalidPaymentOrderCreationResultError) as exc:
                captured = exc
                rendered = " ".join((
                    str(exc), repr(exc), repr(exc.args), repr(vars(exc)),
                    "".join(traceback.format_exception(exc)),
                ))
            else:
                self.fail("invalid value was accepted")
            self.assertNotIn(marker, rendered)
            self.assertIsNone(captured.__cause__)
            self.assertIsNone(captured.__context__)


if __name__ == "__main__":
    unittest.main()
