import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from app import create_app, db
from app.config.config import TestingConfig
from app.models.payment_attempt import PaymentAttemptRecord
from app.services.payment_orchestration import (
    PaymentObligation,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.payment_persistence_service import (
    PaymentPersistenceConflictError,
    create_or_get_obligation,
    register_or_get_attempt,
)
from app.services.psp_contract import (
    PaymentAttempt,
    PaymentAttemptStatus,
    UncertainResponseError,
)
from app.services.psp_event_contract import PSPEvent
from app.services.psp_event_inbox import register_or_get_event
from app.services.psp_event_reconciliation import (
    PSPEventProcessingStatus,
    PSPEventReconciliationProcessor,
)


class Adapter:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create_attempt(self, **kwargs):
        raise AssertionError("processor must not create PSP attempts")

    def get_attempt(self, attempt_id):
        self.calls.append(attempt_id)
        if self.error:
            raise self.error
        return self.response


class PSPEventReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _seed(self, *, provider="provider", live_mode=False, state=PaymentOutcome.PENDING,
              contextual=True, resource_id="psp-1", topic="payment",
              action="updated"):
        request = PaymentObligation("ref-1", Decimal("10.00"), "ARS", "key-1")
        obligation = create_or_get_obligation(db.session, request)
        result = PaymentOrchestrationResult(
            request.internal_reference, request.amount, request.currency,
            request.idempotency_key, resource_id,
            None if state is PaymentOutcome.RECONCILIATION_REQUIRED else PaymentAttemptStatus(state.value),
            state, state is PaymentOutcome.RECONCILIATION_REQUIRED,
        )
        attempt = register_or_get_attempt(
            db.session, obligation, result,
            psp_provider=provider if contextual else None,
            psp_live_mode=live_mode if contextual else None,
        )
        event = register_or_get_event(db.session, PSPEvent(
            provider, "event-1", topic, action, resource_id,
            not live_mode, None, datetime.now(timezone.utc), "a" * 64,
        ))
        db.session.commit()
        return event.id, attempt.id

    @staticmethod
    def _attempt(status, attempt_id="psp-1"):
        return PaymentAttempt(
            attempt_id, "ref-1", Decimal("10.00"), "ARS", "key-1",
            status, datetime.now(timezone.utc),
        )

    def _processor(
        self, adapter, *, provider="provider", live_mode=False,
        payment_topics=("payment",),
    ):
        return PSPEventReconciliationProcessor(
            session_factory=db.session.session_factory,
            adapter=adapter,
            provider=provider,
            live_mode=live_mode,
            payment_topics=payment_topics,
        )

    def test_payment_topics_are_required_normalized_and_immutable(self):
        adapter = Adapter(self._attempt(PaymentAttemptStatus.APPROVED))
        for invalid in ((), [], "payment", None, ("",), (None,)):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    self._processor(adapter, payment_topics=invalid)
        configured = ["  PaYmEnT  "]
        processor = self._processor(adapter, payment_topics=configured)
        configured.clear()
        event_id, _ = self._seed(topic="PAYMENT")
        result = processor.process(event_id)
        self.assertEqual(result.status, PSPEventProcessingStatus.RECONCILED)
        self.assertEqual(adapter.calls, ["psp-1"])

    def test_unsupported_topic_is_repeatable_and_never_touches_payment(self):
        event_id, attempt_id = self._seed(
            topic="merchant_order", action="payment.approved"
        )
        adapter = Adapter(self._attempt(PaymentAttemptStatus.APPROVED))
        processor = self._processor(adapter, payment_topics=("payment",))
        with patch(
            "app.services.psp_event_reconciliation.get_attempt_by_psp_identity"
        ) as lookup:
            first = processor.process(event_id)
            second = processor.process(event_id)
        lookup.assert_not_called()
        self.assertEqual(first.status, PSPEventProcessingStatus.UNSUPPORTED_TOPIC)
        self.assertEqual(second, first)
        self.assertEqual(adapter.calls, [])
        record = db.session.get(PaymentAttemptRecord, attempt_id)
        self.assertEqual(record.financial_status, "PENDING")
        self.assertEqual(record.orchestration_result, "PENDING")

    def test_missing_event_and_context_mismatch_do_not_call_adapter(self):
        adapter = Adapter()
        missing = self._processor(adapter).process(999)
        self.assertEqual(missing.status, PSPEventProcessingStatus.EVENT_NOT_FOUND)
        event_id, _ = self._seed()
        wrong_provider = self._processor(adapter, provider="other").process(event_id)
        wrong_mode = self._processor(adapter, live_mode=True).process(event_id)
        self.assertEqual(wrong_provider.status, PSPEventProcessingStatus.INCOMPATIBLE_CONTEXT)
        self.assertEqual(wrong_mode.status, PSPEventProcessingStatus.INCOMPATIBLE_CONTEXT)
        self.assertEqual(adapter.calls, [])

    def test_unmatched_and_legacy_attempts_do_not_call_adapter(self):
        adapter = Adapter()
        event_id, _ = self._seed(contextual=False)
        result = self._processor(adapter).process(event_id)
        self.assertEqual(result.status, PSPEventProcessingStatus.UNMATCHED)
        self.assertEqual(adapter.calls, [])

    def test_authoritative_states_are_persisted_and_reprocessing_is_safe(self):
        for status in PaymentAttemptStatus:
            with self.subTest(status=status):
                db.session.remove()
                db.drop_all()
                db.create_all()
                event_id, attempt_id = self._seed()
                adapter = Adapter(self._attempt(status))
                first = self._processor(adapter).process(event_id)
                self.assertEqual(first.status, PSPEventProcessingStatus.RECONCILED)
                self.assertEqual(first.financial_status, status)
                second = self._processor(adapter).process(event_id)
                if status in {PaymentAttemptStatus.APPROVED, PaymentAttemptStatus.REJECTED}:
                    self.assertEqual(second.status, PSPEventProcessingStatus.ALREADY_TERMINAL)
                    self.assertEqual(adapter.calls, ["psp-1"])
                else:
                    self.assertEqual(second.status, PSPEventProcessingStatus.RECONCILED)
                    self.assertEqual(adapter.calls, ["psp-1", "psp-1"])
                self.assertEqual(second.attempt_id, attempt_id)

    def test_uncertain_response_preserves_reconciliation_required(self):
        event_id, _ = self._seed(state=PaymentOutcome.RECONCILIATION_REQUIRED)
        adapter = Adapter(error=UncertainResponseError("timeout", attempt_id="psp-1"))
        result = self._processor(adapter).process(event_id)
        self.assertEqual(result.status, PSPEventProcessingStatus.RECONCILIATION_REQUIRED)
        self.assertIsNone(result.financial_status)
        self.assertEqual(adapter.calls, ["psp-1"])

    def test_incompatible_returned_id_and_external_exception_do_not_write(self):
        event_id, _ = self._seed()
        adapter = Adapter(self._attempt(PaymentAttemptStatus.APPROVED, "other"))
        with self.assertRaises(PaymentPersistenceConflictError):
            self._processor(adapter).process(event_id)
        error = RuntimeError("provider unavailable")
        adapter = Adapter(error=error)
        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            self._processor(adapter).process(event_id)
        self.assertEqual(adapter.calls, ["psp-1"])

    def test_adapter_call_occurs_after_read_session_is_closed(self):
        event_id, _ = self._seed()
        open_sessions = 0
        factory = db.session.session_factory

        class TrackedSession:
            def __init__(self):
                nonlocal open_sessions
                self.session = factory()
                open_sessions += 1

            def __enter__(self):
                return self.session

            def __exit__(self, *args):
                nonlocal open_sessions
                self.session.close()
                open_sessions -= 1

        class InspectingAdapter(Adapter):
            def get_attempt(self, attempt_id):
                self.test.assertEqual(open_sessions, 0)
                return super().get_attempt(attempt_id)

        adapter = InspectingAdapter(self._attempt(PaymentAttemptStatus.APPROVED))
        adapter.test = self
        processor = PSPEventReconciliationProcessor(
            session_factory=TrackedSession, adapter=adapter,
            provider="provider", live_mode=False, payment_topics=("payment",),
        )
        processor.process(event_id)
        self.assertEqual(open_sessions, 0)

    def test_persistence_error_rolls_back_and_leaves_session_reusable(self):
        event_id, _ = self._seed()
        adapter = Adapter(self._attempt(PaymentAttemptStatus.APPROVED))
        processor = self._processor(adapter)
        error = RuntimeError("persistence failed")
        with patch(
            "app.services.psp_event_reconciliation.apply_reconciliation",
            side_effect=error,
        ):
            with self.assertRaisesRegex(RuntimeError, "persistence failed"):
                processor.process(event_id)
        recovered = processor.process(event_id)
        self.assertEqual(recovered.status, PSPEventProcessingStatus.RECONCILED)
        self.assertEqual(adapter.calls, ["psp-1", "psp-1"])


if __name__ == "__main__":
    unittest.main()
