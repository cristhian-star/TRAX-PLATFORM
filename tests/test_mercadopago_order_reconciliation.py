from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from app import create_app, db
from app.config.config import Config, TestingConfig
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reconciliation import (
    PaymentOrderReconciliationWork as Work,
    PaymentOrderReconciliationAttempt as Attempt,
    PaymentOrderReconciliationEvidence as Evidence,
    PaymentOrderReconciliationQuarantine as Quarantine,
)
from app.models.psp_event import PSPEventRecord
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.mercadopago_webhook_signature import verify_mercadopago_webhook_signature, MercadoPagoWebhookSignatureError, webhook_timestamp_in_window
from app.services import mercadopago_payment_query_http as http
from app.services.mercadopago_order_query_adapter import (
    MercadoPagoOrderQueryAdapter, OrderQueryContext, ProfessionalOrderQueryCredential,
    OrderQueryResponseError, OrderQueryAuthenticationError, OrderQueryUnavailableError,
    UrllibMercadoPagoOrderQueryTransport, parse_order_snapshot,
)
from app.services.payment_order_reconciliation_service import (
    PaymentOrderReconciliationProcessor, receive_order_event, RETRY_DELAYS, LEASE_DURATION_SECONDS, STALE_LEASE_RECOVERY_SECONDS,
    build_order_reconciliation_processor,
    OrderReconciliationPersistenceError,
)
from app.services.psp_event_contract import PSPEvent
from tests.test_payment_order_application import TrackingSessionFactory, seed_contract


NOW = datetime(2026, 9, 17, 20, tzinfo=timezone.utc)
TOKEN = "SECRET-OAUTH-MARKER"
SECRET = "SECRET-WEBHOOK-MARKER"


def payload(context):
    return dict(
        id=context.external_order_id, external_reference=context.external_reference,
        user_id="12345", type="online", processing_mode="manual", currency="ARS",
        total_amount="1250.50", total_paid_amount="1250.50",
        status="processed", status_detail="accredited",
        created_date=NOW.isoformat(), last_updated_date=(NOW + timedelta(seconds=1)).isoformat(),
        transactions={"payments": [dict(id="PAY123", amount="1250.50", paid_amount="1250.50", status="processed", status_detail="accredited")]},
        payer={"email": "PRIVATE-PAYER-MARKER"}, client_token="PRIVATE-CLIENT-MARKER",
    )


def response(content):
    return http.MercadoPagoHTTPResponse(200, (("Content-Type", "application/json"),), json.dumps(content).encode())


class OrderQueryTest(unittest.TestCase):
    def setUp(self):
        self.context = OrderQueryContext(1, 7, "ORD123", "ref-123", Decimal("1250.50"), "ARS", False, (NOW + timedelta(hours=72)).replace(tzinfo=None))
        self.provider = Mock(return_value=ProfessionalOrderQueryCredential(7, "12345", TOKEN, False))
        self.transport = Mock(return_value=response(payload(self.context)))
        self.adapter = MercadoPagoOrderQueryAdapter(self.provider, self.transport)

    def assert_neutral(self, call, kind, message, marker=TOKEN):
        with self.assertRaises(kind) as caught:
            call()
        error = caught.exception
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        self.assertEqual(str(error), message)
        self.assertNotIn(marker, repr(error))
        self.assertNotIn(marker, repr(error.args))
        return error

    def test_exact_get_and_headers_single_call_and_privacy(self):
        snapshot = self.adapter.query_order(self.context)
        self.provider.assert_called_once_with(7)
        self.transport.assert_called_once_with(method="GET", url="https://api.mercadopago.com/v1/orders/ORD123", headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}, timeout=10.0, allow_redirects=False, body=None)
        self.assertNotIn("PRIVATE", repr(snapshot))
        self.assertNotIn(TOKEN, repr(self.provider.return_value))
        self.assertNotIn(TOKEN, repr(self.adapter))

    def test_oauth_failure_has_no_exception_context_and_no_http(self):
        self.provider.side_effect = RuntimeError(TOKEN)
        self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryAuthenticationError, "order provider authentication unavailable")
        self.transport.assert_not_called()

    def test_credential_validation_failure_neutralizes_context(self):
        self.provider.return_value = ProfessionalOrderQueryCredential(8, "12345", TOKEN, False)
        self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryAuthenticationError, "order provider authentication unavailable")
        self.transport.assert_not_called()

    def test_no_global_fallback_missing_credential(self):
        self.provider.return_value = None
        self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryAuthenticationError, "order provider authentication unavailable")
        self.transport.assert_not_called()

    def test_environment_account_and_currency_binding_before_http(self):
        for credential in (ProfessionalOrderQueryCredential(7, "12345", TOKEN, True), ProfessionalOrderQueryCredential(7, "../evil", TOKEN, False), ProfessionalOrderQueryCredential(7, "12345", TOKEN, False, "USD")):
            with self.subTest(credential=credential):
                self.provider.return_value = credential
                self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryAuthenticationError, "order provider authentication unavailable")
        self.transport.assert_not_called()

    def test_transport_exception_is_neutral_without_retry(self):
        self.transport.side_effect = TimeoutError(TOKEN)
        self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryUnavailableError, "order provider temporarily unavailable")
        self.transport.assert_called_once()

    def test_decoder_and_parser_exceptions_are_neutral(self):
        for name in ("http._decode_json_response", "parse_order_snapshot"):
            with self.subTest(name=name), patch(f"app.services.mercadopago_order_query_adapter.{name}", side_effect=RuntimeError(TOKEN)):
                self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryResponseError, "invalid order provider response")
        self.assertEqual(self.transport.call_count, 2)

    def test_http_classifications_no_retries_or_body_leak(self):
        for status, kind, message in ((401, OrderQueryAuthenticationError, "order provider authentication unavailable"), (403, OrderQueryAuthenticationError, "order provider authentication unavailable"), (404, OrderQueryUnavailableError, "order provider temporarily unavailable"), (408, OrderQueryUnavailableError, "order provider temporarily unavailable"), (429, OrderQueryUnavailableError, "order provider temporarily unavailable"), (500, OrderQueryUnavailableError, "order provider temporarily unavailable"), (400, OrderQueryResponseError, "invalid order provider response"), (302, OrderQueryResponseError, "invalid order provider response")):
            with self.subTest(status=status):
                self.transport.reset_mock()
                self.transport.return_value = http.MercadoPagoHTTPResponse(status, (), TOKEN.encode())
                self.assert_neutral(lambda: self.adapter.query_order(self.context), kind, message)
                self.transport.assert_called_once()

    def test_json_utf8_content_type_limits_and_duplicate_keys(self):
        invalid = (
            http.MercadoPagoHTTPResponse(200, (("Content-Type", "application/json"),), b"{"),
            http.MercadoPagoHTTPResponse(200, (("Content-Type", "application/json"),), b'{"id":"ORD123","id":"ORD123"}'),
            http.MercadoPagoHTTPResponse(200, (("Content-Type", "application/json"),), b'{"amount":NaN}'),
            http.MercadoPagoHTTPResponse(200, (("Content-Type", "application/json"),), b'\xff'),
            http.MercadoPagoHTTPResponse(200, (("Content-Type", "text/html"),), b"{}"),
            http.MercadoPagoHTTPResponse(200, (("Content-Type", "application/json"),), b"x" * (1024 * 1024 + 1)),
        )
        for item in invalid:
            with self.subTest(length=len(item.body)):
                self.transport.return_value = item
                self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryResponseError, "invalid order provider response")

    def test_correlation_and_decimal_reject_mismatches(self):
        for name, value in (("id", "ORDother"), ("user_id", "98765"), ("external_reference", "wrong"), ("currency", "USD"), ("total_amount", 1250.5), ("total_amount", "1250.500"), ("total_amount", "1250.51"), ("total_paid_amount", "1250.51"), ("live_mode", True), ("status", TOKEN), ("last_updated_date", "invalid")):
            with self.subTest(name=name, value=value):
                content = payload(self.context)
                content[name] = value
                self.transport.return_value = response(content)
                self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryResponseError, "invalid order provider response")

    def test_all_orders_statuses_are_preserved(self):
        for status, detail in (("created", "created"), ("processing", "in_process"), ("action_required", "waiting_capture"), ("failed", "rejected_by_issuer"), ("canceled", "canceled"), ("processed", "accredited"), ("processed", "partially_refunded"), ("processed", "refunded"), ("refunded", "refunded")):
            with self.subTest(status=status, detail=detail):
                content = payload(self.context)
                content.update(status=status, status_detail=detail)
                self.transport.return_value = response(content)
                self.assertEqual(self.adapter.query_order(self.context).content["status_detail"], detail)

    def test_refunds_and_chargebacks_are_correlated_and_sanitized(self):
        content = payload(self.context)
        content["transactions"]["refunds"] = [dict(id="REF123", transaction_id="PAY123", amount="125.05", status="processed", secret=TOKEN)]
        content["transactions"]["chargebacks"] = [dict(id="CBK123", transaction_id="PAY123", status="in_process", case_id="PRIVATE-CASE")]
        self.transport.return_value = response(content)
        snapshot = self.adapter.query_order(self.context)
        self.assertEqual(snapshot.content["transactions"]["refunds"][0]["amount"], "125.05")
        self.assertEqual(snapshot.content["transactions"]["chargebacks"][0]["id"], "CBK123")
        self.assertNotIn("PRIVATE", repr(snapshot))
        self.assertNotIn(TOKEN, repr(snapshot))
        content["transactions"]["refunds"][0]["transaction_id"] = "PAYevil"
        self.transport.return_value = response(content)
        self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryResponseError, "invalid order provider response")

    def test_duplicate_transactions_and_excessive_refunds_rejected(self):
        for kind in ("duplicate", "excess"):
            content = payload(self.context)
            if kind == "duplicate":
                content["transactions"]["payments"] *= 2
            else:
                content["transactions"]["refunds"] = [dict(id="REF1", transaction_id="PAY123", amount="1250.51", status="processed")]
            self.transport.return_value = response(content)
            self.assert_neutral(lambda: self.adapter.query_order(self.context), OrderQueryResponseError, "invalid order provider response")

    def test_timeout_configuration_and_stdlib_transport_target(self):
        for timeout in (0, 31, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                MercadoPagoOrderQueryAdapter(self.provider, self.transport, timeout)
        transport = UrllibMercadoPagoOrderQueryTransport()
        for url in ("https://evil.test/v1/orders/ORD123", "https://api.mercadopago.com/v1/orders/../evil", "https://api.mercadopago.com/v1/orders/ORD123?token=evil"):
            with self.assertRaises(ValueError):
                transport(method="GET", url=url, headers={}, timeout=10, allow_redirects=False, body=None)


class ReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = (Path(self.temporary.name) / "reconciliation.db").as_posix()
        class LocalConfig(TestingConfig):
            @classmethod
            def apply_runtime_config(cls, config):
                super().apply_runtime_config(config)
                config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{path}"
        self.app = create_app(config_class=LocalConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.engine = db.engine
        self.factory = TrackingSessionFactory(self.engine)
        self.actor, _, _, self.professional, self.contract = seed_contract(self.factory.Session)
        self.now = NOW.replace(tzinfo=None)
        service = PaymentOrderApplicationService(session_factory=self.factory, adapter=InMemoryPSPPaymentOrderCreationAdapter(), clock=lambda: NOW)
        service.create_order(actor_user_id=self.actor, contract_request_id=self.contract)
        with self.factory.Session.begin() as session:
            order = session.query(PaymentOrder).one()
            order.provider, order.external_order_id = "mercadopago", "ORD123"
            self.order_id, self.reference = order.id, order.external_reference
            self.context = OrderQueryContext(order.id, order.professional_id, order.external_order_id, order.external_reference, order.amount, order.currency, order.live_mode, order.expires_at)
        self.content = payload(self.context)
        self.oauth = Mock(side_effect=self.credential)
        self.transport = Mock(side_effect=self.remote)
        self.adapter = MercadoPagoOrderQueryAdapter(self.oauth, self.transport)
        self.processor = PaymentOrderReconciliationProcessor(session_factory=self.factory, adapter=self.adapter, enabled=True, clock=lambda: self.now)

    def tearDown(self):
        db.session.remove()
        self.engine.dispose()
        self.app_context.pop()
        self.temporary.cleanup()

    def credential(self, professional):
        self.assertEqual(self.factory.open_sessions, 0)
        self.assertEqual(self.engine.pool.checkedout(), 0)
        self.assertEqual(professional, self.professional)
        return ProfessionalOrderQueryCredential(professional, "12345", TOKEN, False)

    def remote(self, **request):
        self.assertEqual(self.factory.open_sessions, 0)
        self.assertEqual(self.engine.pool.checkedout(), 0)
        with self.factory.Session() as session:
            self.assertTrue(session.query(Attempt).filter(Attempt.dispatched_at.is_not(None)).count())
        return response(self.content)

    def event(self, identity="event-1", *, digest="a" * 64, resource="ORD123"):
        return PSPEvent("mercadopago", identity, "order", "order.processed", resource, True, NOW, self.now.replace(tzinfo=timezone.utc), digest)

    def receive(self, identity="event-1", **changes):
        with self.factory.Session.begin() as session:
            event_id = receive_order_event(session, self.event(identity, **changes))
            return session.query(Work).filter_by(event_id=event_id).one().id

    def count(self, model):
        with self.factory.Session() as session:
            return session.query(model).count()

    def test_inbox_work_atomic_replay_and_evidence(self):
        work_id = self.receive()
        self.assertEqual(self.receive(), work_id)
        self.assertEqual(self.count(Work), 1)
        self.assertEqual(self.processor.process(work_id), "DONE")
        self.assertEqual(self.processor.process(work_id), "NOT_CLAIMED")
        self.transport.assert_called_once()
        with self.factory.Session() as session:
            evidence = session.query(Evidence).one()
            self.assertEqual(evidence.payment_order_id, self.order_id)
            self.assertEqual(evidence.snapshot["external_reference"], self.reference)
            self.assertNotIn("PRIVATE", repr(evidence.snapshot))
            self.assertEqual(session.query(PaymentOrder).one().status, "ACTIVE")

    def test_outer_rollback_removes_inbox_and_work(self):
        with self.factory.Session() as session:
            session.begin()
            receive_order_event(session, self.event())
            session.rollback()
        self.assertEqual(self.count(PSPEventRecord), 0)
        self.assertEqual(self.count(Work), 0)

    def test_collision_quarantines_without_overwrite_and_deduplicates(self):
        work_id = self.receive()
        self.receive(digest="b" * 64)
        self.receive(digest="b" * 64)
        self.assertEqual(self.count(Quarantine), 1)
        self.assertEqual(self.processor.process(work_id), "NOT_CLAIMED")
        self.transport.assert_not_called()
        with self.factory.Session() as session:
            self.assertEqual(session.query(PSPEventRecord).one().payload_hash, "a" * 64)

    def test_concurrent_receipts_deduplicate_inbox_and_work(self):
        barrier = threading.Barrier(4)
        def receive(_):
            barrier.wait(timeout=10)
            return self.receive()
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(receive, range(4)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(self.count(PSPEventRecord), 1)
        self.assertEqual(self.count(Work), 1)

    def test_concurrent_claims_have_one_owner(self):
        work_id = self.receive()
        barrier = threading.Barrier(4)
        def claim(_):
            barrier.wait(timeout=10)
            return self.processor.claim(work_id)
        with ThreadPoolExecutor(max_workers=4) as pool:
            tokens = list(pool.map(claim, range(4)))
        self.assertEqual(sum(token is not None for token in tokens), 1)
        self.assertEqual(self.count(Attempt), 1)

    def test_concurrent_dispatch_same_claim_calls_psp_once(self):
        work_id = self.receive()
        # Other workers may own independent transactions; the single-worker
        # tests above assert that the HTTP caller itself has released its session.
        self.oauth.side_effect = None
        self.oauth.return_value = ProfessionalOrderQueryCredential(self.professional, "12345", TOKEN, False)
        self.transport.side_effect = lambda **request: response(self.content)
        token = self.processor.claim(work_id)
        barrier = threading.Barrier(2)
        def dispatch(_):
            barrier.wait(timeout=10)
            return self.processor.process_claim(work_id, token)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(dispatch, range(2)))
        self.assertIn("DONE", outcomes)
        self.transport.assert_called_once()

    def test_unexpired_lease_and_crash_before_dispatch(self):
        work_id = self.receive()
        first = self.processor.claim(work_id)
        self.assertIsNone(self.processor.claim(work_id))
        self.now += timedelta(seconds=STALE_LEASE_RECOVERY_SECONDS)
        second = self.processor.claim(work_id)
        self.assertNotEqual(first, second)
        self.assertEqual(self.processor.process_claim(work_id, first), "LEASE_LOST")
        self.assertEqual(self.processor.process_claim(work_id, second), "DONE")
        self.transport.assert_called_once()
        with self.factory.Session() as session:
            self.assertEqual(session.query(Attempt).filter_by(number=1).one().outcome, "LEASE_LOST")

    def test_crash_after_http_preserves_lease_and_no_duplicate_dispatch(self):
        work_id = self.receive()
        with patch.object(self.processor, "_finish", side_effect=RuntimeError("simulated crash")):
            with self.assertRaises(RuntimeError):
                self.processor.process(work_id)
        with self.factory.Session() as session:
            token = session.get(Work, work_id).lease_token
        self.assertEqual(self.processor.process_claim(work_id, token), "NOT_CLAIMED")
        self.transport.assert_called_once()
        self.now += timedelta(seconds=STALE_LEASE_RECOVERY_SECONDS)
        self.assertEqual(self.processor.process(work_id), "DONE")
        self.assertEqual(self.transport.call_count, 2)
        self.assertEqual(self.count(Evidence), 1)

    def test_commit_failure_rolls_back_evidence_and_public_error_is_neutral(self):
        work_id = self.receive()
        from app.services.payment_order_reconciliation_service import insert_once
        def failed_insert(session, model, values, identity):
            insert_once(session, model, values, identity)
            if model is Evidence:
                raise RuntimeError(TOKEN)
        with patch("app.services.payment_order_reconciliation_service.insert_once", side_effect=failed_insert):
            with self.assertRaises(OrderReconciliationPersistenceError) as caught:
                self.processor.process(work_id)
        error = caught.exception
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        self.assertEqual(str(error), "reconciliation temporarily unavailable")
        self.assertNotIn(TOKEN, repr(error))
        self.assertNotIn(TOKEN, repr(error.args))
        self.assertEqual(self.count(Evidence), 0)
        self.assertEqual(self.processor.process(work_id), "NOT_CLAIMED")
        self.transport.assert_called_once()

    def test_full_refund_evidence_preserves_original_payment_identity(self):
        self.content.update(status="refunded", status_detail="refunded")
        self.content["transactions"]["refunds"] = [dict(id="REFtotal", transaction_id="PAY123", amount="1250.50", status="processed")]
        self.assertEqual(self.processor.process(self.receive()), "DONE")
        with self.factory.Session() as session:
            fact = session.query(Evidence).one().snapshot
            self.assertEqual(fact["transactions"]["refunds"][0]["transaction_id"], "PAY123")
            self.assertEqual(fact["transactions"]["refunds"][0]["amount"], "1250.50")

    def test_charged_back_order_and_payment_are_durable_without_effects(self):
        self.content.update(status="charged_back", status_detail="in_process")
        self.content["transactions"]["payments"][0].update(status="charged_back", status_detail="in_process")
        self.content["transactions"]["chargebacks"] = [dict(id="CBK1", transaction_id="PAY123", status="in_process")]
        self.assertEqual(self.processor.process(self.receive()), "DONE")
        with self.factory.Session() as session:
            fact = session.query(Evidence).one().snapshot
            self.assertEqual(fact["status"], "charged_back")
            self.assertEqual(fact["transactions"]["payments"][0]["status"], "charged_back")
            self.assertEqual(session.get(PaymentOrder, self.order_id).status, "ACTIVE")

    def test_rejected_canceled_and_pending_are_distinct_durable_facts(self):
        for identity, status, detail in (("pending", "processing", "in_process"), ("rejected", "failed", "rejected_by_issuer"), ("canceled", "canceled", "canceled")):
            self.content.update(status=status, status_detail=detail, total_paid_amount="0.00")
            self.content["transactions"] = {"payments": []}
            self.assertEqual(self.processor.process(self.receive(identity)), "DONE")
        with self.factory.Session() as session:
            self.assertEqual({row.snapshot["status"] for row in session.query(Evidence)}, {"processing", "failed", "canceled"})

    def test_concurrent_distinct_events_deduplicate_same_snapshot(self):
        ids = [self.receive("first"), self.receive("second")]
        self.oauth.side_effect = None
        self.oauth.return_value = ProfessionalOrderQueryCredential(self.professional, "12345", TOKEN, False)
        self.transport.side_effect = lambda **request: response(self.content)
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(self.processor.process, ids)), ["DONE", "DONE"])
        self.assertEqual(self.count(Evidence), 1)
        self.assertEqual(self.transport.call_count, 2)

    def test_stale_completion_after_lease_recovery_is_fenced(self):
        work_id = self.receive()
        token = self.processor.claim(work_id)
        with patch.object(self.transport, "side_effect", lambda **request: response(self.content)):
            result = self.adapter.query_order(self.context)
        self.now += timedelta(seconds=STALE_LEASE_RECOVERY_SECONDS)
        newer = self.processor.claim(work_id)
        self.assertEqual(self.processor._finish(work_id, token, self.context, result, None), "LEASE_LOST")
        self.assertEqual(self.count(Evidence), 0)
        self.assertEqual(self.processor.process_claim(work_id, newer), "DONE")

    def test_eight_attempts_backoff_and_exhaustion(self):
        work_id = self.receive()
        self.transport.side_effect = TimeoutError(TOKEN)
        for number in range(1, 9):
            self.assertEqual(self.processor.process(work_id), "EXHAUSTED" if number == 8 else "QUEUED")
            with self.factory.Session() as session:
                work = session.get(Work, work_id)
                self.assertEqual(work.attempt_count, number)
                if number < 8:
                    self.assertEqual(work.next_attempt_at, self.now + timedelta(seconds=RETRY_DELAYS[number - 1]))
                    self.assertEqual(self.processor.process(work_id), "NOT_CLAIMED")
                    self.now = work.next_attempt_at
        self.assertEqual(self.transport.call_count, 8)
        self.assertEqual(self.count(Attempt), 8)
        self.assertEqual(self.processor.process(work_id), "NOT_CLAIMED")
        self.assertEqual(self.count(Evidence), 0)

    def test_eighth_attempt_crash_exhausts_after_lease(self):
        work_id = self.receive()
        for _ in range(8):
            self.assertIsNotNone(self.processor.claim(work_id))
            self.now += timedelta(seconds=STALE_LEASE_RECOVERY_SECONDS)
        self.assertIsNone(self.processor.claim(work_id))
        with self.factory.Session() as session:
            self.assertEqual(session.get(Work, work_id).status, "EXHAUSTED")
        self.transport.assert_not_called()

    def test_unknown_order_retries_without_guessing_oauth(self):
        work_id = self.receive(resource="ORDunknown")
        self.assertEqual(self.processor.process(work_id), "QUEUED")
        self.oauth.assert_not_called()
        self.transport.assert_not_called()

    def test_oauth_failure_is_durable_and_secret_free(self):
        work_id = self.receive()
        self.oauth.side_effect = RuntimeError(TOKEN)
        self.assertEqual(self.processor.process(work_id), "QUEUED")
        self.transport.assert_not_called()
        with self.factory.Session() as session:
            self.assertEqual(session.query(Attempt).one().error_code, "AUTHENTICATION")
            self.assertNotIn(TOKEN, repr(session.get(Work, work_id).last_error))

    def test_invalid_correlation_quarantines(self):
        work_id = self.receive()
        self.content["user_id"] = "other-account"
        self.assertEqual(self.processor.process(work_id), "QUARANTINED")
        self.assertEqual(self.count(Evidence), 0)
        self.assertEqual(self.count(Quarantine), 1)
        self.transport.assert_called_once()

    def test_collision_during_http_fences_completion(self):
        work_id = self.receive()
        def collision(**request):
            self.receive(digest="b" * 64)
            return response(self.content)
        self.transport.side_effect = collision
        self.assertEqual(self.processor.process(work_id), "LEASE_LOST")
        self.assertEqual(self.count(Evidence), 0)
        self.transport.assert_called_once()
        with self.factory.Session() as session:
            self.assertEqual(session.query(Attempt).one().outcome, "QUARANTINED")

    def test_local_context_change_during_http_quarantines(self):
        work_id = self.receive()
        def changed(**request):
            with self.factory.Session.begin() as session:
                session.get(PaymentOrder, self.order_id).external_reference = "changed"
            return response(self.content)
        self.transport.side_effect = changed
        self.assertEqual(self.processor.process(work_id), "QUARANTINED")
        self.assertEqual(self.count(Evidence), 0)

    def test_out_of_order_pending_does_not_erase_approval_or_reversals(self):
        self.assertEqual(self.processor.process(self.receive("approved")), "DONE")
        self.content.update(status="processing", status_detail="in_process", last_updated_date=NOW.isoformat())
        self.assertEqual(self.processor.process(self.receive("older")), "DONE")
        self.content.update(status="processed", status_detail="partially_refunded", last_updated_date=(NOW + timedelta(minutes=1)).isoformat())
        self.content["transactions"]["refunds"] = [dict(id="REF1", transaction_id="PAY123", amount="12.50", status="processed")]
        self.content["transactions"]["chargebacks"] = [dict(id="CBK1", transaction_id="PAY123", status="in_process")]
        self.assertEqual(self.processor.process(self.receive("reverse")), "DONE")
        with self.factory.Session() as session:
            facts = [row.snapshot for row in session.query(Evidence).all()]
            self.assertEqual(len(facts), 3)
            self.assertTrue(any(row["status_detail"] == "accredited" for row in facts))
            self.assertTrue(any(row["transactions"]["refunds"] for row in facts))
            self.assertTrue(any(row["transactions"]["chargebacks"] for row in facts))
            self.assertEqual(session.get(PaymentOrder, self.order_id).status, "ACTIVE")

    def test_identical_snapshots_from_distinct_events_are_deduplicated(self):
        for identity in ("one", "two"):
            self.assertEqual(self.processor.process(self.receive(identity)), "DONE")
        self.assertEqual(self.count(Evidence), 1)
        self.assertEqual(self.count(Attempt), 2)

    def test_expired_order_evidence_does_not_reactivate_checkout(self):
        self.now += timedelta(hours=73)
        with self.factory.Session.begin() as session:
            order = session.get(PaymentOrder, self.order_id)
            order.status, order.closed_at = "EXPIRED", order.expires_at
        self.content["last_updated_date"] = self.now.replace(tzinfo=timezone.utc).isoformat()
        self.assertEqual(self.processor.process(self.receive()), "DONE")
        with self.factory.Session() as session:
            evidence = session.query(Evidence).one()
            self.assertEqual(evidence.timing, "UNKNOWN")
            self.assertGreater(evidence.observed_at, self.context.expires_at)
            self.assertEqual(session.get(PaymentOrder, self.order_id).status, "EXPIRED")

    def test_remote_order_created_after_local_expiry_is_late_evidence(self):
        self.now += timedelta(hours=73)
        self.content["created_date"] = self.now.replace(tzinfo=timezone.utc).isoformat()
        self.content["last_updated_date"] = self.content["created_date"]
        self.assertEqual(self.processor.process(self.receive()), "DONE")
        with self.factory.Session() as session:
            self.assertEqual(session.query(Evidence).one().timing, "AFTER_LOCAL_EXPIRY")

    def test_flags_disable_receipt_and_processing_by_default(self):
        self.assertIs(Config.MERCADOPAGO_ORDER_WEBHOOK_ENABLED, False)
        self.assertIs(Config.MERCADOPAGO_ORDER_RECONCILIATION_ENABLED, False)
        work_id = self.receive()
        disabled = build_order_reconciliation_processor(app=self.app, session_factory=self.factory, oauth_provider=self.oauth, transport=self.transport)
        self.assertEqual(disabled.process(work_id), "NOT_CLAIMED")
        self.assertEqual(disabled.process_due(), [])
        self.assertEqual(self.app.test_client().post("/api/webhooks/mercadopago").status_code, 503)
        self.oauth.assert_not_called()

    def test_due_dispatch_runs_one_pass_not_inline_retries(self):
        self.receive()
        self.transport.side_effect = TimeoutError(TOKEN)
        self.assertEqual(len(self.processor.process_due()), 1)
        self.assertEqual(self.processor.process_due(), [])
        self.transport.assert_called_once()

    def test_lease_boundaries_59_61_119_120(self):
        self.assertEqual(LEASE_DURATION_SECONDS, 60)
        self.assertEqual(STALE_LEASE_RECOVERY_SECONDS, 120)
        start = self.now
        work_id = self.receive()
        token = self.processor.claim(work_id)
        self.now = start + timedelta(seconds=59)
        self.assertIsNone(self.processor.claim(work_id))
        self.assertEqual(self.processor.process_claim(work_id, token), "DONE")
        self.transport.assert_called_once()
        self.transport.reset_mock()
        self.now = start
        work_id = self.receive("abandoned")
        token = self.processor.claim(work_id)
        for seconds in (61, 119):
            self.now = start + timedelta(seconds=seconds)
            self.assertEqual(self.processor.process_claim(work_id, token), "LEASE_LOST")
            self.assertIsNone(self.processor.claim(work_id))
            self.assertEqual(self.processor.process_due(), [])
            self.transport.assert_not_called()
        self.now = start + timedelta(seconds=120)
        recovered = self.processor.claim(work_id)
        self.assertIsNotNone(recovered)
        self.assertNotEqual(token, recovered)
        self.assertEqual(self.processor.process_claim(work_id, token), "LEASE_LOST")
        self.assertEqual(self.processor.process_claim(work_id, recovered), "DONE")
        self.transport.assert_called_once()

    def test_expired_lease_cannot_finalize_remote_response(self):
        work_id = self.receive()
        def delayed(**request):
            self.now += timedelta(seconds=61)
            return response(self.content)
        self.transport.side_effect = delayed
        self.assertEqual(self.processor.process(work_id), "LEASE_LOST")
        self.assertEqual(self.count(Evidence), 0)
        self.transport.assert_called_once()

    def test_remote_refunds_per_payment_not_only_order(self):
        payment = self.content["transactions"]["payments"][0]
        payment.update(amount="100.00", paid_amount="100.00")
        self.content["transactions"]["refunds"] = [dict(id="REF1", transaction_id="PAY123", amount="60.00", status="processed"), dict(id="REF2", transaction_id="PAY123", amount="40.01", status="processed", secret=TOKEN)]
        self.assertEqual(self.processor.process(self.receive()), "QUARANTINED")
        self.assertEqual(self.count(Evidence), 0)
        with self.factory.Session() as session:
            self.assertNotIn(TOKEN, repr(session.query(Quarantine).one().reason))
        self.transport.assert_called_once()

    def test_accumulated_refunds_deduplicate_and_reject_excess(self):
        self.content["transactions"]["payments"][0].update(amount="100.00", paid_amount="100.00")
        def refund(identity, amount):
            return dict(id=identity, transaction_id="PAY123", amount=amount, status="processed")
        self.content["transactions"]["refunds"] = [refund("REF1", "60.00")]
        self.assertEqual(self.processor.process(self.receive("first")), "DONE")
        self.content["last_updated_date"] = (NOW + timedelta(seconds=2)).isoformat()
        self.content["transactions"]["refunds"] *= 2
        self.assertEqual(self.processor.process(self.receive("duplicate")), "DONE")
        self.content["transactions"]["refunds"] = [refund("REF2", "40.01")]
        self.assertEqual(self.processor.process(self.receive("excess")), "QUARANTINED")
        self.assertEqual(self.count(Evidence), 2)
        with self.factory.Session() as session:
            self.assertEqual(session.query(Quarantine).one().reason, "REFUND_CONTRADICTION")
        self.assertEqual(self.transport.call_count, 3)

    def test_refund_quarantine_rollback_is_atomic_and_secret_neutral(self):
        self.content["transactions"]["payments"][0].update(amount="100.00", paid_amount="100.00")
        self.content["transactions"]["refunds"] = [dict(id="REF1", transaction_id="PAY123", amount="60.00", status="processed")]
        self.assertEqual(self.processor.process(self.receive("first")), "DONE")
        self.content["transactions"]["refunds"] = [dict(id="REF2", transaction_id="PAY123", amount="60.00", status="processed")]
        work_id = self.receive("second")
        from app.services import payment_order_reconciliation_service as service
        original = service.quarantine
        def fail(*args):
            original(*args)
            raise RuntimeError(TOKEN)
        with patch.object(service, "quarantine", side_effect=fail), self.assertRaises(OrderReconciliationPersistenceError) as caught:
            self.processor.process(work_id)
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)
        self.assertNotIn(TOKEN, repr(caught.exception.args))
        self.assertEqual(self.count(Quarantine), 0)
        self.assertEqual(self.count(Evidence), 1)
        self.assertEqual(self.transport.call_count, 2)

    def test_accumulated_global_refund_limit_and_identity_conflict(self):
        transactions = self.content["transactions"]
        transactions["payments"] += [dict(id="PAYother", amount="1250.50", paid_amount="1250.50", status="processed", status_detail="accredited")]
        transactions["refunds"] = [dict(id="REF1", transaction_id="PAY123", amount="700.00", status="processed")]
        self.assertEqual(self.processor.process(self.receive("first")), "DONE")
        for identity, payment, amount in (("second", "PAYother", "700.00"), ("conflict", "PAYother", "1.00")):
            transactions["refunds"] = [dict(id="REF2" if identity == "second" else "REF1", transaction_id=payment, amount=amount, status="processed")]
            self.assertEqual(self.processor.process(self.receive(identity)), "QUARANTINED")
        self.assertEqual(self.count(Evidence), 1)
        self.assertEqual(self.count(Quarantine), 2)
        self.assertEqual(self.transport.call_count, 3)

    def test_concurrent_temporal_quarantine_deduplicates_without_dispatch(self):
        event = self.event()
        def receive():
            with self.factory.Session.begin() as session:
                return receive_order_event(session, event, quarantine_reason="TIMESTAMP_OUTSIDE_WINDOW")
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(receive) for _ in range(2)]
            self.assertEqual(futures[0].result(), futures[1].result())
        self.assertEqual(self.count(PSPEventRecord), 1)
        self.assertEqual(self.count(Quarantine), 1)
        self.assertEqual(self.processor.process_due(), [])
        self.transport.assert_not_called()

    def test_concurrent_refunds_serialize_accumulated_limit(self):
        self.content["transactions"]["payments"][0].update(amount="100.00", paid_amount="100.00")
        ids = [self.receive("concurrent-a"), self.receive("concurrent-b")]
        tokens = [self.processor.claim(identity) for identity in ids]
        snapshots = []
        for number in (1, 2):
            self.content["transactions"]["refunds"] = [dict(id=f"REF{number}", transaction_id="PAY123", amount="60.00", status="processed")]
            snapshots.append(parse_order_snapshot(self.content, self.context, "12345"))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.processor._finish, identity, token, self.context, snapshot, None) for identity, token, snapshot in zip(ids, tokens, snapshots)]
            self.assertCountEqual([future.result() for future in futures], ["DONE", "QUARANTINED"])
        self.assertEqual(self.count(Evidence), 1)
        self.assertEqual(self.count(Quarantine), 1)


class SignatureWindowTest(unittest.TestCase):
    def verify(self, offset=0, *, resource="ORDaBc", received_resource=None):
        timestamp = str(int(NOW.timestamp() * 1000) + offset)
        manifest = f"id:{resource};request-id:request-123;ts:{timestamp};"
        digest = hmac.new(SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        return verify_mercadopago_webhook_signature(x_signature=f"ts={timestamp},v1={digest}", x_request_id="request-123", data_id=received_resource or resource, secret=SECRET)

    def test_millisecond_window_is_inclusive_both_directions(self):
        for offset in (-600000, 0, 600000):
            self.assertTrue(webhook_timestamp_in_window(self.verify(offset), NOW))

    def test_outside_window_is_authentic_but_temporally_quarantined(self):
        for offset in (-600001, 600001, -int(NOW.timestamp() * 999)):
            verification = self.verify(offset)
            self.assertTrue(verification.verified)
            self.assertFalse(webhook_timestamp_in_window(verification, NOW))

    def test_resource_case_is_exact(self):
        self.assertTrue(self.verify().verified)
        with self.assertRaises(MercadoPagoWebhookSignatureError):
            self.verify(received_resource="ORDabc")

    def test_postgresql_gate_rejects_persistent_database_before_connecting(self):
        from tests.postgresql_payment_order_reconciliation_e2e import guarded_engine
        with patch("tests.postgresql_payment_order_reconciliation_e2e.sa.create_engine") as connect:
            for url in ("postgresql://localhost/trax_db", "sqlite:///trax.db", "postgresql://localhost/trax_order_reconciliation_test?options=unsafe"):
                with self.assertRaises(RuntimeError):
                    guarded_engine(url, "1")
            with self.assertRaises(RuntimeError):
                guarded_engine("postgresql://localhost/trax_order_reconciliation_test", "0")
        connect.assert_not_called()
