import inspect
import traceback
import unittest
from dataclasses import FrozenInstanceError

from app.services.mercadopago_payment_query import (
    MercadoPagoPaymentQueryError,
    MercadoPagoPaymentQueryResult,
    MercadoPagoPaymentStatusNotRepresentableError,
    parse_mercadopago_payment_query,
)
from app.services.psp_contract import PaymentAttemptStatus


class MercadoPagoPaymentQueryContractTest(unittest.TestCase):
    def _parse(self, **overrides):
        response = {
            "id": 123456789,
            "status": "approved",
            "live_mode": False,
            "status_detail": "accredited",
        }
        response.update(overrides.pop("response", {}))
        return parse_mercadopago_payment_query(
            requested_payment_id=overrides.pop(
                "requested_payment_id", "123456789"
            ),
            expected_live_mode=overrides.pop("expected_live_mode", False),
            response=response,
            **overrides,
        )

    def test_known_statuses_map_to_neutral_values(self):
        cases = {
            "approved": PaymentAttemptStatus.APPROVED,
            "pending": PaymentAttemptStatus.PENDING,
            "in_process": PaymentAttemptStatus.PENDING,
            "authorized": PaymentAttemptStatus.PENDING,
            "rejected": PaymentAttemptStatus.REJECTED,
            "cancelled": PaymentAttemptStatus.REJECTED,
        }
        for provider_status, expected in cases.items():
            with self.subTest(provider_status=provider_status):
                result = self._parse(response={"status": provider_status})
                self.assertEqual(result.status, expected)

    def test_result_is_immutable_and_contains_no_raw_payload(self):
        result = self._parse(response={"card": {"number": "sensitive"}})
        self.assertIsInstance(result, MercadoPagoPaymentQueryResult)
        self.assertEqual(result.attempt_id, "123456789")
        self.assertEqual(result.status_detail, "accredited")
        self.assertFalse(hasattr(result, "payload"))
        self.assertFalse(hasattr(result, "response"))
        with self.assertRaises(FrozenInstanceError):
            result.status = PaymentAttemptStatus.REJECTED

    def test_requested_id_is_safe_for_a_path_segment(self):
        invalid = (
            "", " 123", "123 ", "../123", "123/456", "123\\456",
            "123?x=1", "123#fragment", "123%2F456", "+123", "１２３",
            0, -1, True, 1.5, None, "1" * 33,
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                self._parse(requested_payment_id=value)

    def test_integer_requested_id_is_supported_without_accepting_boolean(self):
        self.assertEqual(self._parse(requested_payment_id=123456789).attempt_id,
                         "123456789")

    def test_response_requires_an_unambiguous_plain_json_object(self):
        for value in (None, [], (), "{}", [("id", 123456789)]):
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                parse_mercadopago_payment_query(
                    requested_payment_id="123456789",
                    expected_live_mode=False,
                    response=value,
                )
        with self.assertRaises(MercadoPagoPaymentQueryError):
            self._parse(response={1: "ambiguous"})

    def test_response_id_has_strict_numeric_type_and_matches_request(self):
        for value in (True, False, "123456789", 123456789.0, None, -1):
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                self._parse(response={"id": value})
        with self.assertRaises(MercadoPagoPaymentQueryError):
            self._parse(response={"id": 987654321})

    def test_required_response_fields_cannot_be_omitted(self):
        base = {"id": 123456789, "status": "approved", "live_mode": False}
        for field in ("id", "status", "live_mode"):
            response = dict(base)
            del response[field]
            with self.subTest(field=field), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                parse_mercadopago_payment_query(
                    requested_payment_id="123456789",
                    expected_live_mode=False,
                    response=response,
                )

    def test_live_mode_is_strict_and_matches_expected_environment(self):
        for value in (0, 1, "false", None):
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                self._parse(response={"live_mode": value})
        with self.assertRaises(MercadoPagoPaymentQueryError):
            self._parse(response={"live_mode": True})
        self.assertTrue(
            self._parse(
                expected_live_mode=True, response={"live_mode": True}
            ).live_mode
        )

    def test_status_has_strict_canonical_type(self):
        for value in (None, True, 1, "", " APPROVED ", "APPROVED"):
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                self._parse(response={"status": value})

    def test_non_representable_and_unknown_statuses_require_reconciliation(self):
        for value in ("refunded", "charged_back", "in_mediation", "unknown"):
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentStatusNotRepresentableError
            ):
                self._parse(response={"status": value})

    def test_status_detail_is_optional_bounded_technical_token(self):
        self.assertIsNone(self._parse(response={"status_detail": None}).status_detail)
        without_detail = {
            "id": 123456789,
            "status": "approved",
            "live_mode": False,
        }
        result = parse_mercadopago_payment_query(
            requested_payment_id="123456789",
            expected_live_mode=False,
            response=without_detail,
        )
        self.assertIsNone(result.status_detail)
        valid_tokens = (
            "accredited",
            "pending_contingency",
            "cc_rejected_bad_filled_card_number",
        )
        for value in valid_tokens:
            with self.subTest(value=value):
                self.assertEqual(
                    self._parse(response={"status_detail": value}).status_detail,
                    value,
                )

        invalid_tokens = (
            True,
            1,
            "",
            "x" * 129,
            "4111111111111111",
            "card_4111111111111_suffix",
            "contains spaces",
            "Uppercase",
            "with-hyphen",
            "con_punto.final",
            "válido",
            "123_status",
        )
        for value in invalid_tokens:
            with self.subTest(value=value), self.assertRaises(
                MercadoPagoPaymentQueryError
            ):
                self._parse(response={"status_detail": value})

    def test_rejected_status_detail_never_leaks_through_domain_exception(self):
        marker = "pan_4111111111111_private"
        try:
            self._parse(response={"status_detail": marker})
        except MercadoPagoPaymentQueryError as exc:
            captured_exc = exc
            rendered = "".join(traceback.format_exception(exc))
        else:
            self.fail("sensitive status detail was accepted")

        exposed = " ".join(
            (
                str(captured_exc),
                repr(captured_exc),
                rendered,
                repr(captured_exc.args),
                repr(vars(captured_exc)),
            )
        )
        self.assertNotIn(marker, exposed)
        self.assertEqual(captured_exc.args, ("invalid payment response detail",))
        self.assertEqual(vars(captured_exc), {})
        self.assertIsNone(captured_exc.__cause__)
        self.assertIsNone(captured_exc.__context__)

    def test_sensitive_payload_never_leaks_from_domain_errors(self):
        marker = "PRIVATE-PAYMENT-PAYLOAD-MARKER"
        try:
            self._parse(response={"status": marker, marker: marker})
        except MercadoPagoPaymentQueryError as exc:
            captured_exc = exc
            rendered = "".join(traceback.format_exception(exc))
        else:
            self.fail("unknown status was accepted")
        self.assertNotIn(marker, str(captured_exc))
        self.assertNotIn(marker, repr(captured_exc))
        self.assertNotIn(marker, rendered)
        self.assertIsNone(captured_exc.__cause__)
        self.assertIsNone(captured_exc.__context__)

    def test_module_has_no_side_effect_boundaries_or_provider_sdk(self):
        import app.services.mercadopago_payment_query as service

        source = inspect.getsource(service)
        for forbidden in (
            "requests", "urllib", "flask", "sqlalchemy", "os.environ",
            "MERCADOPAGO_ACCESS_TOKEN", ".commit(", "mercadopago.SDK",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
