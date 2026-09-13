import hashlib
import hmac
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app import create_app, db
from app.config.config import TestingConfig
from app.models.psp_event import PSPEventRecord
from app.services.psp_event_inbox import register_or_get_event


class MercadoPagoWebhookRoutesTest(unittest.TestCase):
    SECRET = "fictional-http-ingress-secret"
    REQUEST_ID = "request-http-123"
    TIMESTAMP = "1742505638683"
    NOW = datetime(2026, 9, 12, 22, tzinfo=timezone.utc)

    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.app.config["MERCADOPAGO_WEBHOOK_SECRET"] = self.SECRET
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _signature(self, data_id="123456", *, secret=None, request_id=None):
        manifest = (
            f"id:{data_id.lower()};"
            f"request-id:{request_id or self.REQUEST_ID};"
            f"ts:{self.TIMESTAMP};"
        )
        return hmac.new(
            (secret or self.SECRET).encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()

    def _body(self, data_id="123456", **changes):
        body = {
            "id": 9001,
            "type": "payment",
            "action": "payment.updated",
            "data": {"id": data_id},
            "live_mode": False,
            "date_created": "2026-09-12T20:59:00Z",
            "api_version": "v1",
        }
        body.update(changes)
        return body

    def _post(self, data_id="123456", **changes):
        signature = changes.pop("signature", self._signature(data_id))
        headers = changes.pop(
            "headers",
            {
                "X-Signature": f"ts={self.TIMESTAMP},v1={signature}",
                "X-Request-Id": self.REQUEST_ID,
            },
        )
        return self.client.post(
            changes.pop("path", f"/api/webhooks/mercadopago?data.id={data_id}&type=payment"),
            headers=headers,
            json=changes.pop("body", self._body(data_id)),
            **changes,
        )

    def _post_raw(self, payload, *, content_type="application/json"):
        return self.client.post(
            "/api/webhooks/mercadopago?data.id=123456&type=payment",
            headers={
                "X-Signature": (
                    f"ts={self.TIMESTAMP},v1={self._signature()}"
                ),
                "X-Request-Id": self.REQUEST_ID,
            },
            data=payload,
            content_type=content_type,
        )

    def test_public_valid_request_persists_and_commits_before_success(self):
        with patch(
            "app.routes.mercadopago_webhook_routes._utc_now",
            return_value=self.NOW,
        ), patch.object(db.session, "commit", wraps=db.session.commit) as commit:
            response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "accepted"})
        commit.assert_called_once()
        row = PSPEventRecord.query.one()
        self.assertEqual(row.received_at.replace(tzinfo=timezone.utc), self.NOW)
        self.assertEqual(row.provider, "mercadopago")

    def test_identical_replay_is_indistinguishable_and_keeps_first_receipt(self):
        moments = [self.NOW, self.NOW.replace(hour=23)]
        with patch(
            "app.routes.mercadopago_webhook_routes._utc_now",
            side_effect=moments,
        ):
            first = self._post()
            replay = self._post()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(first.get_json(), replay.get_json())
        self.assertEqual(PSPEventRecord.query.count(), 1)
        stored = PSPEventRecord.query.one().received_at.replace(tzinfo=timezone.utc)
        self.assertEqual(stored, self.NOW)

    def test_material_conflict_returns_generic_409_without_updating_row(self):
        self.assertEqual(self._post().status_code, 200)
        response = self._post(body=self._body(action="payment.created"))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json(), {"error": "conflict"})
        self.assertEqual(PSPEventRecord.query.one().action, "payment.updated")

    def test_invalid_signature_is_401_even_before_body_interpretation(self):
        response = self.client.post(
            "/api/webhooks/mercadopago?data.id=123456&type=payment",
            headers={
                "X-Signature": f"ts={self.TIMESTAMP},v1={'0' * 64}",
                "X-Request-Id": self.REQUEST_ID,
                "Content-Type": "text/plain",
            },
            data="not-json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "unauthorized"})

    def test_malformed_metadata_json_and_content_type_are_rejected(self):
        valid_headers = {
            "X-Signature": f"ts={self.TIMESTAMP},v1={self._signature()}",
            "X-Request-Id": self.REQUEST_ID,
        }
        cases = (
            self._post(path="/api/webhooks/mercadopago?data.id=123456&data.id=123456&type=payment"),
            self.client.post(
                "/api/webhooks/mercadopago?data.id=123456&type=payment",
                headers={**valid_headers, "Content-Type": "text/plain"},
                data="{}",
            ),
            self.client.post(
                "/api/webhooks/mercadopago?data.id=123456&type=payment",
                headers={**valid_headers, "Content-Type": "application/json"},
                data="{broken",
            ),
        )
        self.assertEqual([response.status_code for response in cases], [400, 400, 400])
        self.assertEqual(PSPEventRecord.query.count(), 0)

    def test_duplicate_signature_headers_are_rejected_without_persistence(self):
        signature = f"ts={self.TIMESTAMP},v1={self._signature()}"
        response = self._post(
            headers=[
                ("X-Signature", signature),
                ("x-signature", signature),
                ("X-Request-Id", self.REQUEST_ID),
            ]
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(PSPEventRecord.query.count(), 0)

    def test_folded_duplicate_request_id_is_400_before_signature_or_transaction(self):
        session = db.session()
        self.assertFalse(session.in_transaction())
        signature = f"ts={self.TIMESTAMP},v1={self._signature()}"
        with patch(
            "app.routes.mercadopago_webhook_routes."
            "verify_mercadopago_webhook_signature"
        ) as verifier, patch(
            "app.routes.mercadopago_webhook_routes.register_or_get_event"
        ) as register:
            response = self._post(
                headers=[
                    ("X-Signature", signature),
                    ("X-Request-Id", self.REQUEST_ID),
                    ("x-request-id", "second-request-id"),
                ]
            )
        self.assertEqual(response.status_code, 400)
        verifier.assert_not_called()
        register.assert_not_called()
        self.assertFalse(session.in_transaction())
        self.assertEqual(PSPEventRecord.query.count(), 0)

    def test_request_id_rejects_empty_or_ambiguous_whitespace(self):
        signature = f"ts={self.TIMESTAMP},v1={self._signature()}"
        for request_id in ("", " ", f" {self.REQUEST_ID}", f"{self.REQUEST_ID} "):
            with self.subTest(request_id=request_id):
                response = self._post(
                    headers={
                        "X-Signature": signature,
                        "X-Request-Id": request_id,
                    }
                )
                self.assertEqual(response.status_code, 400)

    def test_strict_json_rejects_duplicate_keys_at_every_depth(self):
        payloads = (
            b'{"id":9001,"type":"payment","action":"payment.updated",'
            b'"action":"payment.updated","data":{"id":"123456"},'
            b'"live_mode":false,"date_created":"2026-09-12T20:59:00Z",'
            b'"api_version":"v1"}',
            b'{"id":9001,"type":"payment","action":"payment.updated",'
            b'"data":{"id":"123456","id":"123456"},'
            b'"live_mode":false,"date_created":"2026-09-12T20:59:00Z",'
            b'"api_version":"v1"}',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self._post_raw(payload)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(PSPEventRecord.query.count(), 0)

    def test_strict_json_rejects_invalid_utf8_and_nonstandard_constants(self):
        base = (
            b'{"id":9001,"type":"payment","action":"payment.updated",'
            b'"data":{"id":"123456"},"live_mode":false,'
            b'"date_created":"2026-09-12T20:59:00Z","api_version":"v1"'
        )
        for payload in (b"{broken", b'{"value":"\xff"}', base + b',"value":NaN}', base + b',"value":Infinity}'):
            with self.subTest(payload=payload):
                response = self._post_raw(payload)
                self.assertEqual(response.status_code, 400)

    def test_json_errors_do_not_leak_payload_exception_or_logs(self):
        marker = "PRIVATE-JSON-MARKER"
        payload = f'{{"action":"{marker}","action":"{marker}"}}'.encode()
        with patch("logging.Logger._log") as log_call:
            response = self._post_raw(payload)
        exposed = f"{response.get_data(as_text=True)} {response!r}"
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(marker, exposed)
        for call in log_call.call_args_list:
            self.assertNotIn(marker, repr(call))

    def test_missing_secret_returns_generic_503(self):
        self.app.config["MERCADOPAGO_WEBHOOK_SECRET"] = None
        response = self._post()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "service unavailable"})

    def test_secret_is_loaded_from_environment_configuration(self):
        with patch.dict(
            os.environ,
            {"MERCADOPAGO_WEBHOOK_SECRET": "configured-webhook-secret"},
        ):
            configured = {}
            TestingConfig.apply_runtime_config(configured)
        self.assertEqual(
            configured["MERCADOPAGO_WEBHOOK_SECRET"],
            "configured-webhook-secret",
        )

    def test_notification_contract_errors_are_generic_400(self):
        response = self._post(body=self._body(type="merchant_order"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "bad request"})

    def test_persistence_failure_rolls_back_and_session_recovers(self):
        with patch(
            "app.routes.mercadopago_webhook_routes.register_or_get_event",
            side_effect=RuntimeError("PRIVATE SQL DETAIL"),
        ), patch.object(db.session, "rollback", wraps=db.session.rollback) as rollback:
            response = self._post()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "internal error"})
        rollback.assert_called_once()
        self.assertNotIn("PRIVATE", response.get_data(as_text=True))
        self.assertEqual(self._post().status_code, 200)
        self.assertEqual(PSPEventRecord.query.count(), 1)

    def test_route_does_not_call_provider_or_financial_processor(self):
        with patch(
            "app.routes.mercadopago_webhook_routes.register_or_get_event",
            wraps=register_or_get_event,
        ):
            response = self._post(body=self._body(action="payment.approved"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(hasattr(PSPEventRecord.query.one(), "financial_status"))

if __name__ == "__main__":
    unittest.main()
