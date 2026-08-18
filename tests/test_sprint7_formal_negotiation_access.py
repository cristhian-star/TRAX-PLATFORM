import os
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.config.config import ProductionConfig, TestingConfig
from app.models.professional import Professional
from app.models.user import User
from app.models.verification_request import VerificationRequest
from app.models.whatsapp_contact_session import WhatsAppContactSession


class FormalNegotiationAccessTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=True)
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
            ENABLE_DEV_QA_PANEL=False,
        )
        self.http = self.app.test_client()
        with self.app.app_context():
            users = [
                User(
                    nombre="Cliente habilitado",
                    email="eligible-client@qa.local",
                    password=generate_password_hash("ClientQa123!"),
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Cliente basico",
                    email="basic-client@qa.local",
                    password=generate_password_hash("BasicQa123!"),
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Cliente suspendido",
                    email="suspended-client@qa.local",
                    password=generate_password_hash("SuspendedQa123!"),
                    rol="CLIENTE",
                    estado="SUSPENDIDO",
                ),
                User(
                    nombre="Profesional habilitado",
                    email="professional@qa.local",
                    password=generate_password_hash("ProfessionalQa123!"),
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
            ]
            db.session.add_all(users)
            db.session.flush()
            professional = Professional(
                user_id=users[3].id,
                nombre="Profesional QA",
                servicio="Electricidad",
                zona="CABA",
                telefono="5491100009999",
                perfil_completo=True,
                estado_perfil="VERIFICADO",
            )
            db.session.add(professional)
            db.session.add_all(
                [
                    VerificationRequest(
                        user_id=users[0].id,
                        tipo_usuario="CLIENTE",
                        estado="APROBADO",
                    ),
                    VerificationRequest(
                        user_id=users[2].id,
                        tipo_usuario="CLIENTE",
                        estado="APROBADO",
                    ),
                    VerificationRequest(
                        user_id=users[3].id,
                        tipo_usuario="PROFESIONAL",
                        estado="APROBADO",
                    ),
                ]
            )
            db.session.commit()
            self.eligible_client_id = users[0].id
            self.basic_client_id = users[1].id
            self.suspended_client_id = users[2].id
            self.professional_user_id = users[3].id
            self.professional_id = professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login_session(self, user_id, role):
        with self.http.session_transaction() as browser_session:
            browser_session.clear()
            browser_session["user_id"] = user_id
            browser_session["user_role"] = role

    def _profile(self):
        return self.http.get(f"/profesional/{self.professional_id}")

    def test_visitor_keeps_whatsapp_but_does_not_see_formal_negotiation(self):
        response = self._profile()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"WhatsApp", response.data)
        self.assertIn(b"Contactar", response.data)
        self.assertNotIn(b"Formalizar condiciones", response.data)
        self.assertNotIn(b"/negociacion/nueva", response.data)

    def test_basic_client_does_not_see_or_access_formal_negotiation(self):
        self._login_session(self.basic_client_id, "CLIENTE")
        self.assertNotIn(b"Formalizar condiciones", self._profile().data)
        response = self.http.get(
            f"/negociacion/nueva?professional_id={self.professional_id}"
        )
        self.assertEqual(response.status_code, 403)

    def test_professional_on_own_profile_does_not_see_or_access_negotiation(self):
        self._login_session(self.professional_user_id, "PROFESIONAL")
        self.assertNotIn(b"Formalizar condiciones", self._profile().data)
        response = self.http.get(
            f"/negociacion/nueva?professional_id={self.professional_id}"
        )
        self.assertEqual(response.status_code, 403)

    def test_eligible_client_sees_formal_entry_and_disclaimer(self):
        self._login_session(self.eligible_client_id, "CLIENTE")
        response = self._profile()
        self.assertIn(b"Formalizar condiciones", response.data)
        self.assertIn(b"MANDOBRA registra el acuerdo", response.data)
        entry = self.http.get(
            f"/negociacion/nueva?professional_id={self.professional_id}"
        )
        self.assertEqual(entry.status_code, 200)
        self.assertIn(b"Iniciar acuerdo formal", entry.data)

    def test_suspended_client_is_rejected(self):
        self._login_session(self.suspended_client_id, "CLIENTE")
        response = self.http.get(
            f"/negociacion/nueva?professional_id={self.professional_id}"
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_inactive_target_hides_entry_and_rejects_direct_access(self):
        self._login_session(self.eligible_client_id, "CLIENTE")
        with self.app.app_context():
            target = db.session.get(User, self.professional_user_id)
            target.estado = "SUSPENDIDO"
            db.session.commit()
        self.assertNotIn(b"Formalizar condiciones", self._profile().data)
        response = self.http.get(
            f"/negociacion/nueva?professional_id={self.professional_id}"
        )
        self.assertEqual(response.status_code, 403)

    def test_visitor_whatsapp_flow_still_creates_contact_session(self):
        response = self.http.post(
            "/whatsapp/iniciar",
            data={
                "professional_id": str(self.professional_id),
                "operation_type": "PERFIL_PROFESIONAL",
                "whatsapp_consent": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("wa.me", response.location)
        with self.app.app_context():
            self.assertEqual(WhatsAppContactSession.query.count(), 1)

    def test_explicit_testing_qa_panel_logs_in_both_roles_and_uses_profile_id(self):
        self.app.config["ENABLE_DEV_QA_PANEL"] = True
        client_login = self.http.post(
            f"/dev/qa/login/{self.eligible_client_id}"
        )
        self.assertEqual(client_login.status_code, 302)
        self.assertTrue(client_login.location.endswith("/resultados"))
        with self.http.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_role"], "CLIENTE")

        professional_login = self.http.post(
            f"/dev/qa/login/{self.professional_user_id}"
        )
        self.assertEqual(professional_login.status_code, 302)
        self.assertTrue(
            professional_login.location.endswith(
                f"/profesional/{self.professional_id}"
            )
        )
        with self.http.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_role"], "PROFESIONAL")

    def test_seeded_client_and_professional_can_use_normal_login(self):
        from scripts import dev_seed_professionals

        original_password = dev_seed_professionals.DEMO_PASSWORD
        dev_seed_professionals.DEMO_PASSWORD = "TemporaryQaLogin123!"
        try:
            with self.app.app_context():
                dev_seed_professionals.seed_professionals()
        finally:
            dev_seed_professionals.DEMO_PASSWORD = original_password

        client_login = self.http.post(
            "/login",
            data={
                "email": "cliente.demo@trax.local",
                "password": "TemporaryQaLogin123!",
            },
        )
        self.assertEqual(client_login.status_code, 302)
        with self.http.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_role"], "CLIENTE")

        professional_login = self.http.post(
            "/login",
            data={
                "email": "electricidad.pro@demo.trax.local",
                "password": "TemporaryQaLogin123!",
            },
        )
        self.assertEqual(professional_login.status_code, 302)
        with self.http.session_transaction() as browser_session:
            self.assertEqual(browser_session["user_role"], "PROFESIONAL")

    def test_qa_panel_is_disabled_by_default_and_in_production(self):
        self.assertEqual(self.http.get("/dev/qa").status_code, 404)
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "SECRET_KEY": "production-secret-not-for-development",
                "DATABASE_URL": "sqlite:///:memory:",
                "ENABLE_DEV_QA_PANEL": "true",
            },
            clear=True,
        ):
            production_app = create_app(config_class=ProductionConfig)
        self.assertNotIn("dev", production_app.blueprints)
        self.assertEqual(production_app.test_client().get("/dev/qa").status_code, 404)


if __name__ == "__main__":
    unittest.main()
