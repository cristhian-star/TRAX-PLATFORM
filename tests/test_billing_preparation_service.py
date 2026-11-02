"""Internal persistence on exclusive SQLite; not a PostgreSQL concurrency gate."""
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app import db
from app.models.audit_log import AuditLog
from app.models.billing_preparation import BillingProfile, BillingDraft
from app.models.subscription import Subscription
from app.models.verification_request import VerificationRequest
from app.services.billing_access_policy import BillingAccessDenied
from app.services.billing_preparation_service import save_profile, create_draft, read_draft, BillingConflict
import tests.test_professional_workspace_ux as fixtures


class BillingPreparationServiceTest(unittest.TestCase):
    setUp = fixtures.ProfessionalWorkspaceTest.setUp
    tearDown = fixtures.ProfessionalWorkspaceTest.tearDown

    def profile(self, **overrides):
        args = dict(actor_user_id=10, expected_version=0, cuit="20123456786", legal_name="Emisor",
                    fiscal_address="Domicilio", human_monotributo_declared=True)
        args.update(overrides)
        return save_profile(**args)

    def draft(self, **overrides):
        args = dict(actor_user_id=10, request_key=str(uuid4()), description="Servicio", amount="123.45",
                    recipient_name="Receptor", service_from="2026-10-01", service_to="2026-10-02")
        args.update(overrides)
        return create_draft(**args)

    def grant(self):
        db.session.add(VerificationRequest(user_id=10, tipo_usuario="PROFESIONAL", estado="APROBADO"))
        db.session.add(Subscription(user_id=10, plan="PRO", estado="ACTIVA", source_type="SUBSCRIPTION",
                                    expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)))
        db.session.commit()

    def test_profile_draft_and_audit_roll_back_together(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            self.draft()
            self.assertEqual(AuditLog.query.filter(AuditLog.action.like("BILLING_%")).count(), 2)
            db.session.rollback()
            self.assertEqual(BillingProfile.query.count(), 0)
            self.assertEqual(BillingDraft.query.count(), 0)
            self.assertEqual(AuditLog.query.filter(AuditLog.action.like("BILLING_%")).count(), 0)

    def test_committed_internal_draft_and_private_audit(self):
        with self.app.app_context():
            self.grant()
            result = self.profile()
            draft = self.draft()
            db.session.commit()
            self.assertEqual(result["verification_status"], "DECLARED_UNVERIFIED")
            self.assertEqual(read_draft(actor_user_id=10, draft_id=draft["id"])["status"], "INTERNAL_DRAFT")
            for event in AuditLog.query.filter(AuditLog.action.like("BILLING_%")):
                self.assertIsNone(event.description)
                self.assertIsNone(event.metadata_json)

    def test_replay_same_key_is_unique_conflicting_payload_rejected(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            key = str(uuid4())
            first = self.draft(request_key=key)
            db.session.commit()
            self.assertEqual(first, self.draft(request_key=key))
            with self.assertRaises(BillingConflict):
                self.draft(request_key=key, amount="999")
            self.assertEqual(BillingDraft.query.count(), 1)

    def test_other_owner_and_nonexistent_are_indistinguishable(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            draft = self.draft()
            db.session.commit()
            messages = []
            for draft_id in [draft["id"], draft["id"] + 1000]:
                with self.assertRaises(BillingAccessDenied) as error:
                    read_draft(actor_user_id=20, draft_id=draft_id)
                messages.append(str(error.exception))
            self.assertEqual(messages[0], messages[1])

    def test_loss_of_pro_blocks_write_and_replay_but_preserves_read(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            key = str(uuid4())
            draft = self.draft(request_key=key)
            Subscription.query.filter_by(user_id=10).first().estado = "EXPIRADA"
            db.session.commit()
            with self.assertRaises(BillingAccessDenied):
                self.draft(request_key=key)
            with self.assertRaises(BillingAccessDenied):
                self.profile(expected_version=1)
            self.assertEqual(read_draft(actor_user_id=10, draft_id=draft["id"])["id"], draft["id"])

    def test_stale_profile_version_rejected(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            db.session.commit()
            result = self.profile(expected_version=1, legal_name="Nombre actualizado")
            db.session.commit()
            self.assertEqual(result["version"], 2)
            with self.assertRaises(BillingConflict):
                self.profile(expected_version=1)


if __name__ == "__main__":
    unittest.main()
