import hashlib
import hmac
import inspect
import traceback
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.services.mercadopago_webhook_notification import (
    MercadoPagoWebhookNotificationError,
    parse_mercadopago_webhook_notification,
)
from app.services.mercadopago_webhook_signature import (
    MercadoPagoWebhookSignatureError,
)
from app.services.psp_event_contract import PSPEvent


class MercadoPagoWebhookNotificationTest(unittest.TestCase):
    SECRET = "fictional-notification-secret"
    REQUEST_ID = "request-123"
    TIMESTAMP = str(int(datetime(2026, 9, 12, 21, tzinfo=timezone.utc).timestamp() * 1000))
    RECEIVED_AT = datetime(2026, 9, 12, 21, tzinfo=timezone.utc)

    @classmethod
    def _signature(cls, data_id, **overrides):
        manifest = (
            f"id:{data_id};"
            f"request-id:{overrides.get('request_id', cls.REQUEST_ID)};"
            f"ts:{overrides.get('timestamp', cls.TIMESTAMP)};"
        )
        return hmac.new(
            overrides.get("secret", cls.SECRET).encode(),
            manifest.encode(),
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def _body(cls, data_id="123456", **overrides):
        body = {
            "id": 9001,
            "type": "payment",
            "action": "payment.updated",
            "data": {"id": data_id},
            "live_mode": False,
            "date_created": "2026-09-12T20:59:00Z",
            "api_version": "v1",
            "user_id": 123,
        }
        body.update(overrides)
        return body

    @classmethod
    def _parse(cls, data_id="123456", **overrides):
        signature = overrides.pop("signature", cls._signature(data_id))
        return parse_mercadopago_webhook_notification(
            query_params=overrides.pop(
                "query_params", {"data.id": data_id, "type": "payment"}
            ),
            headers=overrides.pop(
                "headers",
                {
                    "X-Signature": f"ts={cls.TIMESTAMP},v1={signature}",
                    "X-Request-Id": cls.REQUEST_ID,
                },
            ),
            body=overrides.pop("body", cls._body(data_id)),
            secret=overrides.pop("secret", cls.SECRET),
            received_at=overrides.pop("received_at", cls.RECEIVED_AT),
            **overrides,
        )

    def test_valid_notification_maps_to_neutral_immutable_event(self):
        event = self._parse(body=self._body(data={"id": 123456}))
        self.assertIsInstance(event, PSPEvent)
        self.assertEqual(event.provider, "mercadopago")
        self.assertEqual(event.external_event_id, "9001")
        self.assertEqual(event.topic, "payment")
        self.assertEqual(event.action, "payment.updated")
        self.assertEqual(event.external_resource_id, "123456")
        self.assertTrue(event.test_mode)
        self.assertEqual(event.occurred_at.utcoffset(), timedelta(0))
        self.assertEqual(event.received_at, self.RECEIVED_AT)
        self.assertRegex(event.payload_hash, r"^[0-9a-f]{64}$")
        with self.assertRaises(FrozenInstanceError):
            event.action = "payment.approved"

    def test_live_mode_maps_only_to_neutral_mode_without_financial_interpretation(self):
        event = self._parse(
            body=self._body(live_mode=True, action="payment.approved")
        )
        self.assertFalse(event.test_mode)
        self.assertEqual(event.action, "payment.approved")
        self.assertFalse(hasattr(event, "financial_status"))

    def test_order_identifier_preserves_case_in_signature_manifest(self):
        data_id = "ORD01JQ4S4KY8HWQ6NA5PXB65B3D3"
        event = self._parse(
            data_id,
            query_params={"data.id": data_id, "type": " ORDER "},
            body=self._body(data_id, type="order", action="order.updated"),
        )
        self.assertEqual(event.external_resource_id, data_id)
        self.assertEqual(event.topic, "order")

    def test_signature_is_verified_before_body_can_produce_an_event(self):
        with patch(
            "app.services.mercadopago_webhook_notification."
            "verify_mercadopago_webhook_signature",
            side_effect=MercadoPagoWebhookSignatureError("invalid webhook signature"),
        ) as verifier:
            with self.assertRaises(MercadoPagoWebhookSignatureError):
                self._parse(body=None)
        verifier.assert_called_once()

    def test_query_and_header_duplicates_or_invalid_structures_fail_closed(self):
        digest = self._signature("123456")
        cases = (
            {"query_params": [("data.id", "123456"), ("data.id", "123456"), ("type", "payment")]},
            {"query_params": {"data.id": ["123456"], "type": "payment"}},
            {"headers": [("x-signature", f"ts={self.TIMESTAMP},v1={digest}"),
                         ("X-Signature", f"ts={self.TIMESTAMP},v1={digest}"),
                         ("x-request-id", self.REQUEST_ID)]},
            {"headers": {"x-signature": f"ts={self.TIMESTAMP},v1={digest}",
                         "x-request-id": [self.REQUEST_ID]}},
        )
        for values in cases:
            with self.subTest(values=values), self.assertRaises(
                MercadoPagoWebhookNotificationError
            ):
                self._parse(**values)

    def test_body_requires_exact_shape_and_types(self):
        cases = (
            None,
            [],
            self._body(data=None),
            self._body(data={"id": "123456", "extra": "raw"}),
            self._body(unexpected="field"),
            self._body(live_mode=1),
            self._body(id=True),
            self._body(api_version="v2"),
            self._body(date_created="2026-09-12T20:59:00"),
        )
        for body in cases:
            with self.subTest(body=body), self.assertRaises(
                MercadoPagoWebhookNotificationError
            ):
                self._parse(body=body)

    def test_signed_resource_and_topic_must_match_body(self):
        cases = (
            self._body("other"),
            self._body(type="merchant_order"),
        )
        for body in cases:
            with self.subTest(body=body), self.assertRaises(
                MercadoPagoWebhookNotificationError
            ):
                self._parse(body=body)

    def test_required_fields_and_timestamps_fail_closed(self):
        for field in ("id", "type", "action", "data", "live_mode", "date_created", "api_version"):
            body = self._body()
            del body[field]
            with self.subTest(field=field), self.assertRaises(
                MercadoPagoWebhookNotificationError
            ):
                self._parse(body=body)
        with self.assertRaises(MercadoPagoWebhookNotificationError):
            self._parse(received_at=datetime(2026, 9, 12, 21))

    def test_invalid_timestamp_does_not_leak_parser_error_or_sensitive_value(self):
        sensitive_marker = "PRIVATE-TIMESTAMP-MARKER"
        body = self._body(date_created=sensitive_marker)

        try:
            self._parse(body=body)
        except MercadoPagoWebhookNotificationError as exc:
            captured_exc = exc
            formatted_traceback = "".join(traceback.format_exception(exc))
        else:
            self.fail("invalid timestamp was accepted")

        self.assertNotIn(sensitive_marker, str(captured_exc))
        self.assertNotIn(sensitive_marker, repr(captured_exc))
        self.assertNotIn(sensitive_marker, formatted_traceback)
        self.assertIsNone(captured_exc.__cause__)
        self.assertIsNone(captured_exc.__context__)

    def test_payload_hash_is_deterministic_and_excludes_delivery_time(self):
        first = self._parse()
        redelivery = self._parse(received_at=self.RECEIVED_AT + timedelta(minutes=1))
        changed = self._parse(body=self._body(action="payment.created"))
        changed_identity_metadata = self._parse(body=self._body(user_id=124))
        self.assertEqual(first.payload_hash, redelivery.payload_hash)
        self.assertNotEqual(first.payload_hash, changed.payload_hash)
        self.assertNotEqual(first.payload_hash, changed_identity_metadata.payload_hash)
        self.assertFalse(hasattr(first, "payload"))

    def test_errors_do_not_expose_inputs_and_module_has_no_side_effect_boundaries(self):
        secret = "highly-sensitive-contract-secret"
        data_id = "PRIVATE-RESOURCE-ID"
        try:
            self._parse(data_id, secret=secret, signature="0" * 64)
        except MercadoPagoWebhookSignatureError as exc:
            exposed = f"{exc!s} {exc!r}"
        else:
            self.fail("invalid signature was accepted")
        self.assertNotIn(secret, exposed)
        self.assertNotIn(data_id, exposed)

        import app.services.mercadopago_webhook_notification as service

        source = inspect.getsource(service)
        for forbidden in (
            "flask", "sqlalchemy", ".commit(", "register_or_get_event(",
            "process_event(", "requests.", "urllib", "mercadopago.SDK",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
