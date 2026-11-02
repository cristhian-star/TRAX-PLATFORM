"""Pure preparation: no application startup, network or database."""
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from app.services.billing_preparation import (
    BillingValidationError, prepare_profile, prepare_draft, validate_amount, validate_cuit,
)


class BillingPreparationTest(unittest.TestCase):
    def draft(self, **overrides):
        values = dict(description="Reparación", amount="100.125", recipient_name="",
                      service_from="2026-10-01", service_to="2026-10-02")
        values.update(overrides)
        return prepare_draft(**values)

    def test_profile_is_declared_and_immutable(self):
        profile = prepare_profile(cuit="20123456786", legal_name="Emisor",
                                  fiscal_address="Domicilio", human_monotributo_declared=True)
        self.assertEqual(profile.verification_status, "DECLARED_UNVERIFIED")
        with self.assertRaises(FrozenInstanceError):
            profile.cuit = "otra"
        self.assertNotIn(profile.cuit, repr(profile))

    def test_declaration_must_be_explicit(self):
        for declaration in [False, None, "true", 1]:
            with self.subTest(value=declaration), self.assertRaises(BillingValidationError):
                prepare_profile(cuit="20123456786", legal_name="Emisor",
                                fiscal_address="Domicilio", human_monotributo_declared=declaration)

    def test_cuit_syntax_checksum_and_no_silent_normalization(self):
        self.assertEqual(validate_cuit("20123456786"), "20123456786")
        for value in ["20123456780", "20-12345678-6", "２０１２３４５６７８６", "00000000000", "20123456786 ", None]:
            with self.subTest(value=value), self.assertRaises(BillingValidationError):
                validate_cuit(value)

    def test_explicit_decimal_rounding(self):
        self.assertEqual(validate_amount("100.125"), Decimal("100.13"))
        self.assertEqual(validate_amount("0.005"), Decimal("0.01"))
        self.assertEqual(validate_amount("999999999999.99"), Decimal("999999999999.99"))

    def test_invalid_and_nonfinite_money(self):
        for value in ["NaN", "Infinity", "-1", "0", "0.004", "1e3", "1,25", 1.25,
                      True, Decimal("1"), "999999999999.999", "1.1234567", " 1"]:
            with self.subTest(value=value), self.assertRaises(BillingValidationError):
                validate_amount(value)

    def test_draft_cannot_claim_authorization(self):
        draft = self.draft()
        self.assertEqual(draft.status, "INTERNAL_DRAFT")
        self.assertEqual(draft.amount, Decimal("100.13"))
        for name in ["cae", "voucher_number", "qr", "paid"]:
            self.assertFalse(hasattr(draft, name))
        with self.assertRaises(FrozenInstanceError):
            draft.status = "AUTHORIZED"

    def test_service_period_and_dates(self):
        for changes in [dict(service_from="2026-02-30"), dict(service_to="2026-09-01"),
                        dict(service_from="20261001"), dict(service_from=None)]:
            with self.subTest(changes=changes), self.assertRaises(BillingValidationError):
                self.draft(**changes)

    def test_no_silent_corrections_and_private_errors(self):
        for value in ["", " secreto ", "secreto\n", "x" * 1001, None]:
            with self.subTest(value=value), self.assertRaises(BillingValidationError) as error:
                self.draft(description=value)
            self.assertNotIn("secreto", str(error.exception))
        self.assertNotIn("Reparación", repr(self.draft()))

    def test_unsupported_currency(self):
        with self.assertRaises(BillingValidationError):
            self.draft(currency="USD")


if __name__ == "__main__":
    unittest.main()
