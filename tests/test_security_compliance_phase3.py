import logging
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import ProductionConfig, TestingConfig
from app.models.professional import Professional
from app.models.user import User
from app.services.coverage_service import obtener_cobertura_profesional
from app.services.terms_service import accept_terms, has_accepted_terms


def _logger_state(logger):
    return {
        "disabled": logger.disabled,
        "level": logger.level,
        "propagate": logger.propagate,
        "handlers": tuple(logger.handlers),
        "filters": tuple(logger.filters),
        "manager_disable": logging.root.manager.disable,
    }


def _restore_logger_state(logger, state):
    logger.disabled = state["disabled"]
    logger.setLevel(state["level"])
    logger.propagate = state["propagate"]
    logger.handlers[:] = state["handlers"]
    logger.filters[:] = state["filters"]
    logging.disable(state["manager_disable"])


@contextmanager
def _enabled_logger_capture(logger):
    state = _logger_state(logger)
    try:
        logging.disable(logging.NOTSET)
        logger.disabled = False
        logger.filters[:] = []
        yield
    finally:
        _restore_logger_state(logger, state)


class SecurityCompliancePhase3Test(unittest.TestCase):
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
            self.user = User(
                nombre="Cliente Privado",
                email="privado@trax.test",
                password="hash-secreto",
                rol="CLIENTE",
            )
            self.professional_user = User(
                nombre="Profesional Privado",
                email="profesional-privado@trax.test",
                password="hash-secreto",
                rol="PROFESIONAL",
            )
            db.session.add_all([self.user, self.professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Oficio Seguro",
                servicio="Electricidad",
                especialidad="Electricidad",
                zona="Caballito",
                telefono="+54 9 11 1234-5678",
                descripcion="Servicio profesional",
                perfil_completo=True,
                coverage_city="Caballito",
                coverage_province="CABA",
                coverage_radius_km=20,
                coverage_mode="RADIO",
                latitude=-34.603722,
                longitude=-58.381592,
            )
            db.session.add(self.professional)
            db.session.commit()
            self.user_id = self.user.id
            self.professional_id = self.professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _capture_unexpected_error(self):
        marker = "Authorization=Bearer abc SECRET_KEY=leak telefono=5491112345678"
        endpoint = f"phase3_error_{self._testMethodName}"
        path = f"/_test/phase3/error/{self._testMethodName}"

        def _test_error():
            raise RuntimeError(marker)

        self.app.add_url_rule(path, endpoint=endpoint, view_func=_test_error)
        with _enabled_logger_capture(self.app.logger):
            with self.assertLogs(self.app.logger, level="ERROR") as captured:
                response = self.client.get(path, headers={"Accept": "application/json"})
        return response, "\n".join(captured.output), marker

    def test_gitignore_covers_sensitive_local_artifacts(self):
        with open(".gitignore", encoding="utf-8") as gitignore_file:
            patterns = set(
                line.strip()
                for line in gitignore_file
                if line.strip() and not line.startswith("#")
            )

        expected_patterns = {
            ".env",
            ".env.*",
            "!.env.example",
            ".venv/",
            "node_modules/",
            "logs/",
            "uploads/",
            "instance/",
            "*.sqlite",
            "*.sqlite3",
            "*.db",
            "*.pem",
            "*.key",
            "*.crt",
            "*.dump",
            "*.sql",
        }
        self.assertTrue(expected_patterns.issubset(patterns))

    def test_production_rejects_placeholder_secret_key(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "SECRET_KEY": "tu_clave_aqui",
                "DATABASE_URL": "sqlite:///:memory:",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                create_app(config_class=ProductionConfig)

    def test_public_professional_profile_does_not_expose_precise_private_data(self):
        response = self.client.get(f"/profesional/{self.professional_id}")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn("5491112345678", body)
        self.assertNotIn("+54 9 11 1234-5678", body)
        self.assertNotIn("profesional-privado@trax.test", body)
        self.assertNotIn("-34.603722", body)
        self.assertNotIn("-58.381592", body)

    def test_search_results_do_not_expose_phone_email_or_precise_coordinates(self):
        response = self.client.get("/resultados", query_string={"servicio": "Electricidad"})

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn("5491112345678", body)
        self.assertNotIn("profesional-privado@trax.test", body)
        self.assertNotIn("-34.603722", body)
        self.assertNotIn("-58.381592", body)

    def test_public_coverage_coordinates_are_approximate(self):
        with self.app.app_context():
            coverage = obtener_cobertura_profesional(db.session.get(Professional, self.professional_id))

        self.assertEqual(coverage["public_latitude"], -34.6)
        self.assertEqual(coverage["public_longitude"], -58.39)
        self.assertNotEqual(coverage["public_latitude"], -34.603722)
        self.assertNotEqual(coverage["public_longitude"], -58.381592)

    def test_error_log_does_not_include_sensitive_exception_payload(self):
        response, logs, marker = self._capture_unexpected_error()

        self.assertEqual(response.status_code, 500)
        self.assertIn("Error inesperado procesando la solicitud", logs)
        for sensitive_fragment in ("Authorization", "SECRET_KEY", "5491112345678", marker):
            self.assertNotIn(sensitive_fragment, logs)

    def test_error_log_capture_restores_preexisting_logger_state(self):
        logger = self.app.logger
        original_state = _logger_state(logger)
        sentinel_handler = logging.NullHandler()
        sentinel_filter = logging.Filter("unrelated.logger")
        try:
            logger.disabled = True
            logger.setLevel(logging.CRITICAL)
            logger.propagate = False
            logger.handlers[:] = [sentinel_handler]
            logger.filters[:] = [sentinel_filter]
            logging.disable(logging.CRITICAL)
            contaminated_state = _logger_state(logger)

            response, logs, marker = self._capture_unexpected_error()

            self.assertEqual(response.status_code, 500)
            self.assertIn("Error inesperado procesando la solicitud", logs)
            self.assertNotIn(marker, logs)
            self.assertEqual(_logger_state(logger), contaminated_state)
        finally:
            _restore_logger_state(logger, original_state)

    def test_headers_do_not_expose_powered_by_and_csp_is_restricted(self):
        response = self.client.get("/")

        self.assertNotIn("X-Powered-By", response.headers)
        csp = response.headers["Content-Security-Policy"]
        self.assertIn("object-src 'none'", csp)
        self.assertIn("https://maps.googleapis.com", csp)
        self.assertIn("https://maps.gstatic.com", csp)
        self.assertNotIn("*", csp)

    def test_terms_acceptance_supports_versioned_documents_with_context(self):
        with self.app.app_context():
            acceptance = accept_terms(
                self.user_id,
                "privacy_policy",
                "2026-07",
                ip_address="127.0.0.1",
                user_agent="tests",
            )

            self.assertEqual(acceptance.user_id, self.user_id)
            self.assertEqual(acceptance.tipo_termino, "privacy_policy")
            self.assertEqual(acceptance.version, "2026-07")
            self.assertEqual(acceptance.ip_address, "127.0.0.1")
            self.assertEqual(acceptance.user_agent, "tests")
            self.assertTrue(has_accepted_terms(self.user_id, "privacy_policy", "2026-07"))
            self.assertFalse(has_accepted_terms(self.user_id, "privacy_policy", "2026-08"))


if __name__ == "__main__":
    unittest.main()
