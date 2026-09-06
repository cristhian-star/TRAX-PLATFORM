import os
import unittest
from unittest.mock import patch

from flask import abort


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import ProductionConfig, TestingConfig
from app.models.professional import Professional
from app.models.user import User


class SecurityControlsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=False)
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=True,
            SERVER_NAME="localhost",
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(
                nombre="Cliente",
                email="cliente@trax.test",
                password="hash",
                rol="CLIENTE",
            )
            self.professional_user = User(
                nombre="Profesional",
                email="pro@trax.test",
                password="hash",
                rol="PROFESIONAL",
            )
            db.session.add_all([self.client_user, self.professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Pro Test",
                servicio="Electricidad",
                zona="CABA",
                telefono="5491100001001",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.commit()
            self.client_user_id = self.client_user.id
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

    def test_login_rate_limit_returns_429(self):
        for _ in range(5):
            response = self.client.post(
                "/login",
                data={"email": "nadie@trax.test", "password": "bad"},
                environ_base={"REMOTE_ADDR": "10.10.0.1"},
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            "/login",
            data={"email": "nadie@trax.test", "password": "bad"},
            environ_base={"REMOTE_ADDR": "10.10.0.1"},
        )

        self.assertEqual(response.status_code, 429)
        self.assertNotIn(b"password", response.data.lower())

    def test_whatsapp_rate_limit_uses_authenticated_user_and_ip(self):
        self.login_as_client()
        payload = {
            "professional_id": str(self.professional_id),
            "operation_type": "PERFIL_PROFESIONAL",
            "whatsapp_consent": "on",
        }

        for _ in range(10):
            response = self.client.post(
                "/whatsapp/iniciar",
                data=payload,
                environ_base={"REMOTE_ADDR": "10.10.0.2"},
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            "/whatsapp/iniciar",
            data=payload,
            environ_base={"REMOTE_ADDR": "10.10.0.2"},
        )

        self.assertEqual(response.status_code, 429)

    def test_whatsapp_rate_limit_uses_ip_for_anonymous_users(self):
        payload = {
            "professional_id": str(self.professional_id),
            "operation_type": "PERFIL_PROFESIONAL",
            "whatsapp_consent": "on",
        }

        for _ in range(10):
            response = self.client.post(
                "/whatsapp/iniciar",
                data=payload,
                environ_base={"REMOTE_ADDR": "10.10.0.9"},
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            "/whatsapp/iniciar",
            data=payload,
            environ_base={"REMOTE_ADDR": "10.10.0.9"},
        )

        self.assertEqual(response.status_code, 429)

    def test_search_rate_limit_and_parameter_length(self):
        response = self.client.get(
            "/buscar",
            query_string={"servicio": "x" * 121},
            environ_base={"REMOTE_ADDR": "10.10.0.3"},
        )
        self.assertEqual(response.status_code, 400)

        for _ in range(60):
            response = self.client.get(
                "/buscar",
                environ_base={"REMOTE_ADDR": "10.10.0.4"},
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/buscar",
            environ_base={"REMOTE_ADDR": "10.10.0.4"},
        )
        self.assertEqual(response.status_code, 429)

    def test_report_rate_limit_authenticated_user(self):
        self.login_as_client()
        for _ in range(5):
            response = self.client.post(
                f"/reportar/usuario/{self.professional_id}",
                data={"motivo": "spam", "descripcion": "reporte"},
                environ_base={"REMOTE_ADDR": "10.10.0.5"},
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            f"/reportar/usuario/{self.professional_id}",
            data={"motivo": "spam", "descripcion": "reporte"},
            environ_base={"REMOTE_ADDR": "10.10.0.5"},
        )
        self.assertEqual(response.status_code, 429)

    def test_max_content_length_returns_413(self):
        self.app.config["MAX_CONTENT_LENGTH"] = 32
        response = self.client.post(
            "/rubros/solicitar",
            data={"nombre_rubro": "x" * 100, "descripcion_rubro": "x", "email_notificacion": "a@b.test"},
            environ_base={"REMOTE_ADDR": "10.10.0.6"},
        )

        self.assertEqual(response.status_code, 413)

    def test_list_results_are_capped_by_per_page(self):
        with self.app.app_context():
            for index in range(70):
                db.session.add(Professional(
                    user_id=None,
                    nombre=f"Profesional {index:02d}",
                    servicio="Plomeria",
                    zona="CABA",
                    perfil_completo=True,
                ))
            db.session.commit()

        response = self.client.get(
            "/resultados",
            query_string={"servicio": "Plomeria", "per_page": "999"},
            environ_base={"REMOTE_ADDR": "10.10.0.7"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Profesional 49", body)
        self.assertNotIn("Profesional 50", body)

    def test_error_handlers_are_safe(self):
        @self.app.route("/_test/forbidden")
        def _test_forbidden():
            abort(403)

        @self.app.route("/_test/error")
        def _test_error():
            raise RuntimeError("SECRET_KEY=leak password=bad")

        response = self.client.get("/no-existe", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Recurso no encontrado")

        response = self.client.get("/_test/forbidden", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["error"], "Acceso no autorizado")

        response = self.client.get("/_test/error", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json["error"], "Error interno")
        self.assertNotIn("SECRET_KEY", response.get_data(as_text=True))
        self.assertNotIn("password", response.get_data(as_text=True).lower())

    def test_security_headers_development_and_production_hsts(self):
        response = self.client.get("/", environ_base={"REMOTE_ADDR": "10.10.0.8"})
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertNotIn("Strict-Transport-Security", response.headers)

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "SECRET_KEY": "prod-secret",
                "DATABASE_URL": "sqlite:///:memory:",
            },
            clear=True,
        ):
            prod_app = create_app(config_class=ProductionConfig, initialize_schema=False)
            prod_app.config.update(TESTING=True, SERVER_NAME="localhost")

        prod_client = prod_app.test_client()
        response = prod_client.get("/", base_url="https://localhost")
        self.assertIn("Strict-Transport-Security", response.headers)


if __name__ == "__main__":
    unittest.main()
