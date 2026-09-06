import os
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import TestingConfig
from app.models.professional import Professional
from app.models.user import User
from app.models.whatsapp_contact_session import WhatsAppContactSession
from app.services.coverage_service import normalizar_cobertura, normalizar_radio
from app.services.google_maps_config_service import (
    google_maps_disponible,
    normalizar_google_maps_api_key,
    obtener_google_maps_api_key,
)


class WhatsAppGeolocationCompletionPhase2Test(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=False)
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
            SERVER_NAME="localhost",
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(
                nombre="Cliente",
                email="cliente-fase2@trax.test",
                password="hash",
                rol="CLIENTE",
            )
            self.professional_user = User(
                nombre="Profesional",
                email="profesional-fase2@trax.test",
                password="hash",
                rol="PROFESIONAL",
            )
            db.session.add_all([self.client_user, self.professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Pro Fase 2",
                servicio="Electricidad",
                zona="CABA",
                telefono="+54 9 11 0000-1001",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.commit()
            self.client_user_id = self.client_user.id
            self.professional_user_id = self.professional_user.id
            self.professional_id = self.professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_as_client(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.client_user_id
            sess["user_name"] = "Cliente"
            sess["user_role"] = "CLIENTE"

    def login_as_professional_owner(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.professional_user_id
            sess["user_name"] = "Profesional"
            sess["user_role"] = "PROFESIONAL"

    def whatsapp_payload(self, **overrides):
        payload = {
            "professional_id": str(self.professional_id),
            "operation_type": "PERFIL_PROFESIONAL",
            "whatsapp_consent": "on",
        }
        payload.update(overrides)
        return payload

    def test_whatsapp_requires_consent_for_json(self):
        response = self.client.post(
            "/whatsapp/iniciar",
            data=self.whatsapp_payload(whatsapp_consent=""),
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("consentimiento", response.json["error"])

    def test_whatsapp_json_response_returns_authorized_url_and_opens_session(self):
        self.login_as_client()
        response = self.client.post(
            "/whatsapp/iniciar",
            data=self.whatsapp_payload(),
            headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["whatsapp_url"].startswith("https://wa.me/5491100001001?text="))
        self.assertEqual(response.json["status"], WhatsAppContactSession.STATUS_CONTACTO_ABIERTO)

        with self.app.app_context():
            sessions = WhatsAppContactSession.query.all()
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].status, WhatsAppContactSession.STATUS_CONTACTO_ABIERTO)
            self.assertEqual(sessions[0].contact_identifier_masked, "*********1001")
            self.assertNotIn("5491100001001", sessions[0].contact_identifier_masked)

    def test_whatsapp_html_request_keeps_redirect_fallback(self):
        response = self.client.post("/whatsapp/iniciar", data=self.whatsapp_payload())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("https://wa.me/5491100001001?text="))

    def test_whatsapp_missing_or_invalid_phone_returns_safe_error(self):
        with self.app.app_context():
            professional = db.session.get(Professional, self.professional_id)
            professional.telefono = "123"
            db.session.commit()

        response = self.client.post(
            "/whatsapp/iniciar",
            data=self.whatsapp_payload(),
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("WhatsApp", response.json["error"])
        self.assertNotIn("123", response.get_data(as_text=True))

    def test_whatsapp_blocks_ownership_self_contact(self):
        self.login_as_professional_owner()
        response = self.client.post(
            "/whatsapp/iniciar",
            data=self.whatsapp_payload(),
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 403)

    def test_whatsapp_csrf_invalid_is_rejected(self):
        csrf_app = create_app(config_class=TestingConfig, initialize_schema=False)
        csrf_app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=True,
            RATELIMIT_ENABLED=False,
            SERVER_NAME="localhost",
        )
        csrf_client = csrf_app.test_client()

        with csrf_app.app_context():
            db.drop_all()
            db.create_all()
            user = User(nombre="Pro CSRF", email="pro-csrf@trax.test", password="hash", rol="PROFESIONAL")
            db.session.add(user)
            db.session.flush()
            professional = Professional(
                user_id=user.id,
                nombre="Pro CSRF",
                servicio="Gas",
                zona="CABA",
                telefono="5491100002002",
                perfil_completo=True,
            )
            db.session.add(professional)
            db.session.commit()
            professional_id = professional.id

        response = csrf_client.post(
            "/whatsapp/iniciar",
            data={
                "professional_id": str(professional_id),
                "operation_type": "PERFIL_PROFESIONAL",
                "whatsapp_consent": "on",
            },
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 400)

        with csrf_app.app_context():
            db.session.remove()
            db.drop_all()

    def test_templates_do_not_include_direct_whatsapp_links(self):
        templates_dir = Path("app/templates")
        offenders = []
        for template in templates_dir.rglob("*.html"):
            body = template.read_text(encoding="utf-8")
            if "wa.me/" in body or "whatsapp.com/send" in body:
                offenders.append(str(template))

        self.assertEqual(offenders, [])

    def test_google_maps_key_normalization(self):
        self.assertIsNone(normalizar_google_maps_api_key(None))
        self.assertIsNone(normalizar_google_maps_api_key("tu_clave_real"))
        self.assertIsNone(normalizar_google_maps_api_key(" placeholder "))
        self.assertEqual(normalizar_google_maps_api_key("AIza-test"), "AIza-test")

    def test_google_maps_environment_availability(self):
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "tu_clave_real"}, clear=False):
            self.assertIsNone(obtener_google_maps_api_key())
            self.assertFalse(google_maps_disponible())

        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "AIza-realistic-test"}, clear=False):
            self.assertEqual(obtener_google_maps_api_key(), "AIza-realistic-test")
            self.assertTrue(google_maps_disponible())

    def test_private_profile_rejects_placeholder_google_maps_key(self):
        self.login_as_professional_owner()
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "tu_clave_real"}, clear=False):
            response = self.client.get("/profesional/perfil/completar")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('data-has-api-key="false"', body)
        self.assertNotIn("maps.googleapis.com/maps/api/js?key=tu_clave_real", body)

    def test_coverage_radius_and_coordinates_validation(self):
        self.assertEqual(normalizar_radio("1"), 1)
        self.assertEqual(normalizar_radio("200"), 200)

        with self.assertRaises(ValueError):
            normalizar_radio("0")

        with self.assertRaises(ValueError):
            normalizar_radio("201")

        with self.assertRaises(ValueError):
            normalizar_cobertura({
                "coverage_mode": "RADIO",
                "coverage_radius_km": "10",
                "coverage_location_consent": "on",
                "latitude": "-120",
                "longitude": "-58.381592",
            })

    def test_coverage_coordinates_are_saved_only_with_consent(self):
        without_consent = normalizar_cobertura({
            "coverage_mode": "RADIO",
            "coverage_radius_km": "10",
            "latitude": "-34.603722",
            "longitude": "-58.381592",
        })
        self.assertIsNone(without_consent["latitude"])
        self.assertIsNone(without_consent["longitude"])
        self.assertIsNone(without_consent["coverage_location_consent_at"])

        with_consent = normalizar_cobertura({
            "coverage_mode": "RADIO",
            "coverage_radius_km": "10",
            "coverage_location_consent": "on",
            "latitude": "-34.603722",
            "longitude": "-58.381592",
        })
        self.assertEqual(with_consent["latitude"], -34.603722)
        self.assertEqual(with_consent["longitude"], -58.381592)
        self.assertIsNotNone(with_consent["coverage_location_consent_at"])


if __name__ == "__main__":
    unittest.main()
