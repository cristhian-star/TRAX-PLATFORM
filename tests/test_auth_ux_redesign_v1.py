import os
import unittest
from unittest.mock import patch


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.config.config import TestingConfig
from app.models.terms_acceptance import TermsAcceptance
from app.models.user import User
from app.services.auth_service import (
    CURRENT_TERMS_TYPE,
    CURRENT_TERMS_VERSION,
    authenticate_user,
    register_user_from_form,
)


class AuthUxRedesignTest(unittest.TestCase):
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
                nombre="Cliente Auth",
                email="cliente-auth@trax.test",
                password=generate_password_hash("Password123!"),
                rol="CLIENTE",
            )
            self.suspended_user = User(
                nombre="Suspendido",
                email="suspendido@trax.test",
                password=generate_password_hash("Password123!"),
                rol="CLIENTE",
                estado="SUSPENDIDO",
            )
            db.session.add_all([self.client_user, self.suspended_user])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_success_redirects_and_sets_session(self):
        response = self.client.post(
            "/login",
            data={"email": " CLIENTE-AUTH@TRAX.TEST ", "password": "Password123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["user_role"], "CLIENTE")

    def test_login_invalid_and_suspended_user_are_rejected(self):
        response = self.client.post(
            "/login",
            data={"email": "cliente-auth@trax.test", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("No pudimos validar esos datos", response.get_data(as_text=True))

        with self.app.app_context():
            self.assertIsNone(authenticate_user("suspendido@trax.test", "Password123!"))
        response = self.client.post(
            "/login",
            data={"email": "suspendido@trax.test", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 401)

    def test_register_client_creates_terms_acceptance_and_redirects_to_safe_next(self):
        response = self.client.post(
            "/register?next=/presupuestos/nuevo",
            data={
                "nombre": "Nueva Cliente",
                "email": "NUEVA@TRAX.TEST",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "rol": "CLIENTE",
                "terms_accepted": "on",
            },
            environ_base={"REMOTE_ADDR": "10.20.0.1", "HTTP_USER_AGENT": "auth-tests"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/presupuestos/nuevo")
        with self.app.app_context():
            user = User.query.filter_by(email="nueva@trax.test").one()
            acceptance = TermsAcceptance.query.filter_by(user_id=user.id).one()
            self.assertEqual(user.rol, "CLIENTE")
            self.assertEqual(acceptance.tipo_termino, CURRENT_TERMS_TYPE)
            self.assertEqual(acceptance.version, CURRENT_TERMS_VERSION)
            self.assertEqual(acceptance.ip_address, "10.20.0.1")
            self.assertEqual(acceptance.user_agent, "auth-tests")

    def test_register_professional_redirects_to_profile_completion_without_creating_professional(self):
        response = self.client.post(
            "/register",
            data={
                "nombre": "Nueva Pro",
                "email": "pro-nueva@trax.test",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "rol": "PROFESIONAL",
                "terms_accepted": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profesional/perfil/completar")
        with self.app.app_context():
            user = User.query.filter_by(email="pro-nueva@trax.test").one()
            self.assertEqual(user.rol, "PROFESIONAL")
            self.assertIsNone(user.professional_profile)

    def test_register_rejects_duplicate_email_with_neutral_message(self):
        response = self.client.post(
            "/register",
            data={
                "nombre": "Duplicado",
                "email": "cliente-auth@trax.test",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "rol": "CLIENTE",
                "terms_accepted": "on",
            },
        )

        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("No pudimos crear la cuenta", body)
        self.assertNotIn("ya esta registrado", body.lower())

    def test_register_rejects_invalid_role_short_password_mismatch_and_missing_terms(self):
        response = self.client.post(
            "/register",
            data={
                "nombre": "",
                "email": "bad-email",
                "password": "short",
                "password_confirm": "different",
                "rol": "SUPER_ADMIN",
            },
        )

        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Ingresa tu nombre", body)
        self.assertIn("Ingresa un email valido", body)
        self.assertIn("al menos 8 caracteres", body)
        self.assertIn("Las contrasenas no coinciden", body)
        self.assertIn("tipo de cuenta valido", body)
        self.assertIn("Acepta los terminos", body)

    def test_register_blocks_external_next(self):
        response = self.client.post(
            "/register?next=https://evil.test/path",
            data={
                "nombre": "Next Seguro",
                "email": "next-seguro@trax.test",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "rol": "CLIENTE",
                "terms_accepted": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_terms_rollback_if_acceptance_fails(self):
        with self.app.app_context():
            with patch("app.services.auth_service.db.session.commit", side_effect=RuntimeError("terms failed")):
                with self.assertRaises(RuntimeError):
                    register_user_from_form(
                        {
                            "nombre": "Rollback",
                            "email": "rollback@trax.test",
                            "password": "Password123!",
                            "password_confirm": "Password123!",
                            "rol": "CLIENTE",
                            "terms_accepted": "on",
                        }
                    )

            self.assertIsNone(User.query.filter_by(email="rollback@trax.test").first())

    def test_templates_include_accessible_labels_and_auth_assets(self):
        login = self.client.get("/login").get_data(as_text=True)
        register = self.client.get("/register").get_data(as_text=True)

        self.assertIn('for="login-email"', login)
        self.assertIn('aria-describedby="login-email-help', login)
        self.assertIn('data-password-toggle', login)
        self.assertIn("auth-ux-v1.css", login)
        self.assertIn("auth-ux-v1.js", login)

        self.assertIn('for="register-name"', register)
        self.assertIn("<legend>Tipo de cuenta</legend>", register)
        self.assertIn('name="terms_accepted"', register)
        self.assertIn('data-password-strength', register)

    def test_csrf_invalid_is_rejected_for_login_and_register(self):
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

        login_response = csrf_client.post(
            "/login",
            data={"email": "nadie@trax.test", "password": "Password123!"},
        )
        register_response = csrf_client.post(
            "/register",
            data={
                "nombre": "CSRF",
                "email": "csrf-auth@trax.test",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "rol": "CLIENTE",
                "terms_accepted": "on",
            },
        )

        self.assertEqual(login_response.status_code, 400)
        self.assertEqual(register_response.status_code, 400)

        with csrf_app.app_context():
            db.session.remove()
            db.drop_all()

    def test_rate_limits_login_and_register(self):
        limited_app = create_app(config_class=TestingConfig, initialize_schema=False)
        limited_app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=True,
            SERVER_NAME="localhost",
        )
        limited_client = limited_app.test_client()
        with limited_app.app_context():
            db.drop_all()
            db.create_all()

        for _ in range(5):
            response = limited_client.post(
                "/login",
                data={"email": "nadie@trax.test", "password": "Password123!"},
                environ_base={"REMOTE_ADDR": "10.20.0.2"},
            )
            self.assertNotEqual(response.status_code, 429)
        response = limited_client.post(
            "/login",
            data={"email": "nadie@trax.test", "password": "Password123!"},
            environ_base={"REMOTE_ADDR": "10.20.0.2"},
        )
        self.assertEqual(response.status_code, 429)

        for index in range(3):
            response = limited_client.post(
                "/register",
                data={
                    "nombre": f"Rate {index}",
                    "email": f"rate-{index}@trax.test",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "rol": "CLIENTE",
                    "terms_accepted": "on",
                },
                environ_base={"REMOTE_ADDR": "10.20.0.3"},
            )
            self.assertNotEqual(response.status_code, 429)
        response = limited_client.post(
            "/register",
            data={
                "nombre": "Rate blocked",
                "email": "rate-blocked@trax.test",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "rol": "CLIENTE",
                "terms_accepted": "on",
            },
            environ_base={"REMOTE_ADDR": "10.20.0.3"},
        )
        self.assertEqual(response.status_code, 429)

        with limited_app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
