import unittest
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.config.config import TestingConfig
from app.services.payment_orchestration import (
    InvalidPaymentRequestError,
    PaymentObligation as PaymentRequest,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.payment_persistence_service import (
    PaymentPersistenceConflictError,
    associate_attempt_psp_identity,
    create_or_get_obligation,
    get_attempt_by_psp_identity,
    register_or_get_attempt,
)
from app.services.psp_contract import PaymentAttemptStatus
from app.services.psp_event_contract import PSPEvent


class PaymentAttemptPSPIdentityTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    @staticmethod
    def _request(suffix):
        return PaymentRequest(f"ref-{suffix}", Decimal("10"), "ARS", f"key-{suffix}")

    @staticmethod
    def _result(request, external_id="shared-id"):
        return PaymentOrchestrationResult(
            request.internal_reference, request.amount, request.currency,
            request.idempotency_key, external_id, PaymentAttemptStatus.PENDING,
            PaymentOutcome.PENDING, False,
        )

    def _register(self, suffix, *, provider=None, live_mode=None, external_id="shared-id"):
        request = self._request(suffix)
        obligation = create_or_get_obligation(db.session, request)
        return register_or_get_attempt(
            db.session, obligation, self._result(request, external_id),
            psp_provider=provider, psp_live_mode=live_mode,
        )

    def test_context_pair_legacy_compatibility_and_false_mode(self):
        legacy = self._register("legacy")
        self.assertIsNone(legacy.psp_provider)
        self.assertIsNone(legacy.psp_live_mode)
        sandbox = self._register("sandbox", provider=" Provider-A ", live_mode=False)
        self.assertEqual(sandbox.psp_provider, "provider-a")
        self.assertIs(sandbox.psp_live_mode, False)
        for provider, mode in (("provider", None), (None, True), ("provider", 0)):
            with self.subTest(provider=provider, mode=mode), self.assertRaises(InvalidPaymentRequestError):
                self._register(f"invalid-{provider}-{mode}", provider=provider, live_mode=mode)

    def test_contextual_uniqueness_allows_provider_and_mode_boundaries(self):
        first = self._register("first", provider="alpha", live_mode=True)
        db.session.commit()
        with self.assertRaises(IntegrityError):
            self._register("duplicate", provider="ALPHA", live_mode=True)
        db.session.rollback()
        other_provider = self._register("other-provider", provider="beta", live_mode=True)
        sandbox = self._register("sandbox", provider="alpha", live_mode=False)
        self.assertEqual(len({first.id, other_provider.id, sandbox.id}), 3)

    def test_exact_lookup_excludes_legacy_and_respects_context(self):
        legacy = self._register("legacy")
        scoped = self._register("scoped", provider="alpha", live_mode=False)
        self.assertIsNone(get_attempt_by_psp_identity(
            db.session, psp_provider="alpha", psp_live_mode=True,
            external_attempt_id="shared-id",
        ))
        self.assertEqual(get_attempt_by_psp_identity(
            db.session, psp_provider="ALPHA", psp_live_mode=False,
            external_attempt_id="shared-id",
        ).id, scoped.id)
        self.assertNotEqual(legacy.id, scoped.id)

    def test_identity_can_be_assigned_once_but_not_replaced(self):
        request = self._request("unassigned")
        obligation = create_or_get_obligation(db.session, request)
        attempt = register_or_get_attempt(
            db.session, obligation, self._result(request, None)
        )
        associated = associate_attempt_psp_identity(
            db.session, attempt.id, psp_provider="ALPHA", psp_live_mode=False,
            external_attempt_id="opaque-id",
        )
        self.assertEqual((associated.psp_provider, associated.psp_live_mode, associated.external_attempt_id),
                         ("alpha", False, "opaque-id"))
        self.assertEqual(associate_attempt_psp_identity(
            db.session, attempt.id, psp_provider="alpha", psp_live_mode=False,
            external_attempt_id="opaque-id",
        ).id, attempt.id)
        with self.assertRaises(PaymentPersistenceConflictError):
            associate_attempt_psp_identity(
                db.session, attempt.id, psp_provider="beta", psp_live_mode=False,
                external_attempt_id="opaque-id",
            )

    def test_event_and_attempt_share_provider_canonicalization(self):
        event = PSPEvent(
            " Provider-A ", "event", "payment", "updated", "resource", False,
            None, __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            "A" * 64,
        )
        attempt = self._register("canonical", provider="PROVIDER-A", live_mode=False)
        self.assertEqual(event.provider, attempt.psp_provider)


if __name__ == "__main__":
    unittest.main()
