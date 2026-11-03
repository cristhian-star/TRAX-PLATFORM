"""Persisted actor and real entitlement policy, exclusive in-memory fixtures."""
import unittest
from datetime import datetime, timedelta

from app import db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.verification_request import VerificationRequest
from app.services.billing_access_policy import require_billing_actor, BillingAccessDenied
import tests.test_professional_workspace_ux as fixtures


class BillingAccessPolicyTest(unittest.TestCase):
    setUp = fixtures.ProfessionalWorkspaceTest.setUp
    tearDown = fixtures.ProfessionalWorkspaceTest.tearDown

    def grant(self, now):
        db.session.add(VerificationRequest(user_id=10, tipo_usuario="PROFESIONAL", estado="APROBADO"))
        db.session.add(Subscription(user_id=10, plan="PRO", estado="ACTIVA",
                                    source_type="SUBSCRIPTION", expires_at=now + timedelta(days=1)))
        db.session.commit()

    def test_free_can_pass_actor_boundary_but_not_write(self):
        with self.app.app_context():
            self.assertEqual(require_billing_actor(10), 10)
            with self.assertRaises(BillingAccessDenied):
                require_billing_actor(10, writing=True)
            self.assertEqual(Subscription.query.count(), 0)

    def test_entitlement_expiration_rechecked_each_command(self):
        now = datetime(2026, 11, 1, 12)
        with self.app.app_context():
            self.grant(now)
            self.assertEqual(require_billing_actor(10, writing=True, now=now), 10)
            with self.assertRaises(BillingAccessDenied):
                require_billing_actor(10, writing=True, now=now + timedelta(days=1))
            self.assertEqual(require_billing_actor(10, now=now + timedelta(days=2)), 10)

    def test_invalid_actors_and_persisted_roles(self):
        with self.app.app_context():
            for actor in [None, True, "10", -1, 99999, 30]:
                with self.subTest(actor=actor), self.assertRaises(BillingAccessDenied):
                    require_billing_actor(actor)
            db.session.get(User, 10).estado = "SUSPENDIDO"
            db.session.commit()
            with self.assertRaises(BillingAccessDenied):
                require_billing_actor(10)

    def test_read_policy_never_grants_ownership(self):
        # The result is the actor identity, never an arbitrary requested owner.
        with self.app.app_context():
            self.assertEqual(require_billing_actor(10), 10)
            self.assertEqual(require_billing_actor(20), 20)


if __name__ == "__main__":
    unittest.main()
