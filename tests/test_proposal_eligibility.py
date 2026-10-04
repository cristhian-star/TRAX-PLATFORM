"""P0: persisted eligibility, real CSRF, isolated SQLite only."""
import os
import re
import unittest
from unittest.mock import patch
from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.models.professional import Professional
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.models.verification_request import VerificationRequest
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_request import ContractRequest
from app.services.proposal_service import apply_to_proposal
from app.services.proposal_eligibility_service import proposal_application_eligibility


class ProposalEligibilityTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "SECRET_KEY": "p0-test"}):
            self.app = create_app(TestingConfig)
        self.app.config.update(WTF_CSRF_ENABLED=True, RATELIMIT_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.assertEqual(str(db.engine.url), "sqlite:///:memory:")
            db.create_all()
            db.session.add_all([
                User(id=1, nombre="Owner", email="owner@test.invalid", password="unused", rol="CLIENTE"),
                User(id=2, nombre="Applicant", email="applicant@test.invalid", password="unused", rol="PROFESIONAL"),
            ])
            db.session.flush()
            db.session.add(Professional(id=1, user_id=2, nombre="Applicant", servicio="Electricidad", zona="Palermo", perfil_completo=True))
            db.session.add(ProposalRequest(id=1, cliente_id=1, owner_user_id=1, categoria="Electricidad", titulo="Trabajo", descripcion="Descripcion", estado="PUBLICADA"))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def configure(self, role="PROFESIONAL", state="ACTIVO", complete=True, verification=None):
        with self.app.app_context():
            user = db.session.get(User, 2)
            user.rol, user.estado = role, state
            db.session.get(Professional, 1).perfil_completo = complete
            VerificationRequest.query.delete()
            if verification:
                db.session.add(VerificationRequest(user_id=2, tipo_usuario="PROFESIONAL", estado=verification))
            db.session.commit()
        with self.client.session_transaction() as session:
            session.update(user_id=2, user_role="PROFESIONAL", verified=True, perfil_completo=True)

    def counts(self):
        with self.app.app_context():
            return tuple(model.query.count() for model in (ProposalApplication, ActivityNotification, AuditLog, ContractRequest))

    def post(self, **extra):
        html = self.client.get('/propuestas/1').get_data(as_text=True)
        # Global base forms also carry the CSRF token for ineligible viewers.
        token_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        if not token_match:
            html = self.client.get('/login').get_data(as_text=True)
            token_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        data = dict(csrf_token=token_match[1], mensaje="Quiero postularme")
        data.update(extra)
        return self.client.post('/propuestas/1/postular', data=data)

    def test_rejection_matrix_route_service_and_presentation(self):
        cases = [
            ({}, "VERIFICATION_REQUIRED"),
            ({"verification": "PENDIENTE"}, "VERIFICATION_REQUIRED"),
            ({"verification": "RECHAZADO"}, "VERIFICATION_REQUIRED"),
            ({"verification": "OBSERVADO"}, "VERIFICATION_REQUIRED"),
            ({"complete": False, "verification": "APROBADO"}, "PROFILE_INCOMPLETE"),
            ({"state": "SUSPENDIDO", "verification": "APROBADO"}, "ACCOUNT_INACTIVE"),
        ] + [({"role": role, "verification": "APROBADO"}, "ROLE_NOT_PROFESSIONAL")
             for role in ("CLIENTE", "ADMIN", "ADMINISTRADOR", "", "DESCONOCIDO")]
        for config, reason in cases:
            with self.subTest(config=config):
                self.configure(**config)
                with self.app.app_context():
                    result = proposal_application_eligibility(2)
                    self.assertFalse(result.eligible)
                    self.assertEqual(result.reason, reason)
                    with self.assertRaises(PermissionError):
                        apply_to_proposal(1, 2, "Direct call")
                html = self.client.get('/propuestas/1').get_data(as_text=True)
                self.assertNotIn('action="/propuestas/1/postular"', html)
                self.assertIn(result.message, html)
                response = self.post(verified="true", rol="PROFESIONAL")
                self.assertEqual(response.status_code, 403)
                self.assertIsNone(response.location)
                self.assertEqual(self.counts(), (0, 0, 0, 0))

    def test_anonymous_and_csrf(self):
        response = self.post()
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
        self.configure(verification="APROBADO")
        self.assertEqual(self.post(csrf_token="invalid").status_code, 400)
        self.assertEqual(self.counts(), (0, 0, 0, 0))

    def test_eligible_without_pro_and_duplicate(self):
        self.configure(verification="APROBADO")
        html = self.client.get('/propuestas/1').get_data(as_text=True)
        self.assertIn('action="/propuestas/1/postular"', html)
        self.assertEqual(self.post().status_code, 302)
        first = self.counts()
        self.assertEqual(first[0], 1)
        self.assertEqual(first[3], 0)
        self.assertGreater(first[1], 0)
        self.post()
        self.assertEqual(self.counts(), first)

    def test_owner_and_closed_proposal_still_rejected(self):
        self.configure(verification="APROBADO")
        with self.app.app_context():
            proposal = db.session.get(ProposalRequest, 1)
            proposal.owner_user_id = 2
            db.session.commit()
            with self.assertRaises(ValueError):
                apply_to_proposal(1, 2, "Owner")
            proposal.owner_user_id = 1
            proposal.estado = "CERRADA"
            db.session.commit()
            with self.assertRaises(ValueError):
                apply_to_proposal(1, 2, "Closed")
        self.assertEqual(self.counts(), (0, 0, 0, 0))
