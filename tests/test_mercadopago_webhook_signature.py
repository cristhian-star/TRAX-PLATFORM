import hashlib
import hmac
import unittest
from unittest.mock import patch

from app.services.mercadopago_webhook_signature import (
    MercadoPagoWebhookSignatureError,
    MercadoPagoWebhookSignatureVerification,
    verify_mercadopago_webhook_signature,
)


class MercadoPagoWebhookSignatureTest(unittest.TestCase):
    SECRET = "fictional-test-secret"
    REQUEST_ID = "request-123"
    TIMESTAMP = "1742505638683"

    @classmethod
    def _signature(cls, data_id, *, secret=None, request_id=None, timestamp=None):
        manifest = (
            f"id:{data_id.lower()};"
            f"request-id:{request_id or cls.REQUEST_ID};"
            f"ts:{timestamp or cls.TIMESTAMP};"
        )
        return hmac.new(
            (secret or cls.SECRET).encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()

    @classmethod
    def _verify(cls, data_id="123456", **overrides):
        signature = overrides.pop("signature", cls._signature(data_id))
        return verify_mercadopago_webhook_signature(
            x_signature=overrides.pop(
                "x_signature", f"ts={cls.TIMESTAMP},v1={signature}"
            ),
            x_request_id=overrides.pop("x_request_id", cls.REQUEST_ID),
            data_id=overrides.pop("received_data_id", data_id),
            secret=overrides.pop("secret", cls.SECRET),
            **overrides,
        )

    def test_valid_signature_uses_constant_time_comparison(self):
        with patch(
            "app.services.mercadopago_webhook_signature.hmac.compare_digest",
            wraps=hmac.compare_digest,
        ) as compare:
            result = self._verify()
        self.assertEqual(
            result,
            MercadoPagoWebhookSignatureVerification(True, "123456", self.TIMESTAMP),
        )
        compare.assert_called_once()

    def test_uppercase_data_id_is_lowercased_only_for_manifest(self):
        original = "ORD01JQ4S4KY8HWQ6NA5PXB65B3D3"
        result = self._verify(original)
        self.assertEqual(result.data_id, original)
        self.assertEqual(original, "ORD01JQ4S4KY8HWQ6NA5PXB65B3D3")
        numeric = self._verify("123456")
        self.assertEqual(numeric.data_id, "123456")

    def test_data_id_is_signature_sensitive_after_official_lowercasing(self):
        signature = self._signature("ORDER-A")
        self._verify("order-a", signature=signature, received_data_id="ORDER-A")
        with self.assertRaises(MercadoPagoWebhookSignatureError):
            self._verify("order-b", signature=signature)

    def test_incorrect_signature_or_secret_is_rejected(self):
        for values in (
            {"signature": "0" * 64},
            {"secret": "different-fictional-secret"},
        ):
            with self.subTest(values=values):
                with self.assertRaises(MercadoPagoWebhookSignatureError):
                    self._verify(**values)

    def test_required_fail_closed_fields(self):
        cases = (
            {"x_signature": None}, {"x_signature": " "},
            {"x_request_id": None}, {"x_request_id": " "},
            {"received_data_id": None}, {"received_data_id": " "},
            {"secret": None}, {"secret": " "},
        )
        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(MercadoPagoWebhookSignatureError):
                    self._verify(**values)

    def test_missing_malformed_and_ambiguous_signature_components(self):
        digest = self._signature("123456")
        headers = (
            f"v1={digest}",
            f"ts={self.TIMESTAMP}",
            f"ts=not-a-timestamp,v1={digest}",
            f"ts={self.TIMESTAMP},v1=not-a-sha256",
            f"ts={self.TIMESTAMP},ts={self.TIMESTAMP},v1={digest}",
            f"ts={self.TIMESTAMP},v1={digest},v1={digest}",
            f"ts={self.TIMESTAMP},broken,v1={digest}",
        )
        for header in headers:
            with self.subTest(header=header):
                with self.assertRaises(MercadoPagoWebhookSignatureError):
                    self._verify(x_signature=header)

    def test_component_order_and_reasonable_header_spacing_are_accepted(self):
        digest = self._signature("123456")
        for header in (
            f"v1={digest},ts={self.TIMESTAMP}",
            f"  ts = {self.TIMESTAMP} , v1 = {digest}  ",
        ):
            with self.subTest(header=header):
                self.assertTrue(self._verify(x_signature=header).verified)

    def test_component_keys_are_case_insensitive_and_duplicates_fail_closed(self):
        timestamp = "1"
        digest = self._signature("123456", timestamp=timestamp)
        other_digest = "0" * 64
        duplicate_headers = (
            f"ts=1,TS=2,v1={digest}",
            f"ts=1,v1={digest},V1={other_digest}",
            f"ts=1,TS=1,v1={digest}",
            f"ts=1,v1={digest},V1={digest}",
        )
        for header in duplicate_headers:
            with self.subTest(header=header):
                with self.assertRaises(MercadoPagoWebhookSignatureError):
                    self._verify(x_signature=header)

        result = self._verify(
            x_signature=f" TS = {timestamp} , V1 = {digest} "
        )
        self.assertTrue(result.verified)
        self.assertEqual(result.timestamp, timestamp)

    def test_request_id_timestamp_and_secret_are_not_normalized(self):
        request_id = " Request-Exact "
        timestamp = "1742505638683"
        secret = " fictional-secret-with-spaces "
        signature = self._signature(
            "ABC", secret=secret, request_id=request_id, timestamp=timestamp
        )
        result = verify_mercadopago_webhook_signature(
            x_signature=f"ts={timestamp},v1={signature}",
            x_request_id=request_id,
            data_id="ABC",
            secret=secret,
        )
        self.assertTrue(result.verified)

    def test_errors_and_results_do_not_leak_secret_signature_or_manifest(self):
        secret = "highly-sensitive-fictional-secret"
        signature = "0" * 64
        try:
            self._verify(secret=secret, signature=signature)
        except MercadoPagoWebhookSignatureError as exc:
            exposed = f"{exc!s} {exc!r}"
        else:
            self.fail("invalid signature was accepted")
        self.assertNotIn(secret, exposed)
        self.assertNotIn(signature, exposed)
        self.assertNotIn("request-id:", exposed)
        result = self._verify("ABC")
        self.assertNotIn(self.SECRET, repr(result))
        self.assertNotIn(self._signature("ABC"), repr(result))


if __name__ == "__main__":
    unittest.main()
