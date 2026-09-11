import ast
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from app.config.config import ProductionConfig, TestingConfig


class DevPaymentSimulatorRouteTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=False)
        self.app.config.update(
            TESTING=True,
            ENABLE_DEV_QA_PANEL=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
        )
        self.client = self.app.test_client()

    def _post(self, **overrides):
        values = {
            "internal_reference": "obligation-001",
            "amount": "1250.500",
            "currency": "ARS",
            "idempotency_key": "payment-key-001",
            "scenario": "APPROVED",
        }
        values.update(overrides)
        return self.client.post("/dev/qa/payments/simulator", data=values)

    def test_disabled_route_returns_404(self):
        self.app.config["ENABLE_DEV_QA_PANEL"] = False
        self.assertEqual(self.client.get("/dev/qa/payments/simulator").status_code, 404)
        self.assertEqual(self._post().status_code, 404)

    def test_route_is_not_registered_in_production(self):
        with patch.dict(
            os.environ,
            {"SECRET_KEY": "production-secret", "DATABASE_URL": "sqlite:///:memory:",
             "ENABLE_DEV_QA_PANEL": "true"},
            clear=True,
        ):
            app = create_app(config_class=ProductionConfig)
        self.assertNotIn("dev", app.blueprints)
        self.assertEqual(app.test_client().get("/dev/qa/payments/simulator").status_code, 404)

    def test_enabled_get_renders_internal_form_and_warning(self):
        response = self.client.get("/dev/qa/payments/simulator")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Simulador de pagos", html)
        self.assertIn("Entorno de prueba. No mueve dinero real.", html)
        for name in ("internal_reference", "amount", "currency",
                     "idempotency_key", "scenario"):
            self.assertIn(f'name="{name}"', html)
        for scenario in ("APPROVED", "REJECTED", "PENDING", "UNCERTAIN"):
            self.assertIn(f'value="{scenario}"', html)

    def test_four_scenarios_render_distinct_interpretations(self):
        expected = {
            "APPROVED": ("Pago aprobado", "RECONCILIATION_REQUIRED"),
            "REJECTED": ("Pago rechazado", "Conciliacion requerida"),
            "PENDING": ("Pago pendiente", "Conciliacion requerida"),
            "UNCERTAIN": ("Conciliacion requerida", "Pago rechazado"),
        }
        for scenario, (present, absent) in expected.items():
            with self.subTest(scenario=scenario):
                html = self._post(scenario=scenario).get_data(as_text=True)
                self.assertIn(present, html)
                if scenario == "UNCERTAIN":
                    self.assertIn("RECONCILIATION_REQUIRED", html)
                    self.assertIn("No confirmado por la respuesta", html)
                self.assertNotIn(absent, html.split("Interpretacion de MANDOBRA", 1)[1])

    def test_invalid_amount_does_not_compose_simulator_and_preserves_values(self):
        with patch("app.routes.dev_routes.InMemoryPSPSimulator") as simulator:
            html = self._post(amount="NaN", currency="USD").get_data(as_text=True)
        simulator.assert_not_called()
        self.assertIn("El importe debe ser mayor que cero y finito.", html)
        self.assertIn('value="USD"', html)
        self.assertIn('value="obligation-001"', html)
        self.assertIn("La simulacion no fue ejecutada.", html)

    def test_invalid_format_does_not_use_float(self):
        with patch("app.routes.dev_routes.InMemoryPSPSimulator") as simulator:
            html = self._post(amount="12,50").get_data(as_text=True)
        simulator.assert_not_called()
        self.assertIn("Ingresa un importe numerico valido.", html)
        route_source = Path("app/routes/dev_routes.py").read_text(encoding="utf-8")
        self.assertNotIn("float(", route_source)

    def test_each_post_uses_a_fresh_simulator_without_history(self):
        first = self._post(scenario="APPROVED").get_data(as_text=True)
        second = self._post(scenario="REJECTED").get_data(as_text=True)
        self.assertIn("dev-payment-attempt-001", first)
        self.assertIn("dev-payment-attempt-001", second)
        self.assertIn("Pago aprobado", first)
        self.assertIn("Pago rechazado", second)

    def test_template_uses_design_system_accessibility_and_no_provider_assets(self):
        template = Path("app/templates/dev_payment_simulator.html").read_text(
            encoding="utf-8"
        )
        css = Path("app/static/css/dev-payment-simulator.css").read_text(
            encoding="utf-8"
        )
        for component in ("trax-page", "trax-container", "trax-card", "trax-field",
                          "trax-input", "trax-radio", "trax-button", "trax-badge",
                          "trax-alert", "trax-stack"):
            self.assertIn(component, template)
        self.assertIn("<fieldset", template)
        self.assertIn("<legend", template)
        self.assertIn('aria-live="polite"', template)
        self.assertIn("aria-invalid", template)
        self.assertNotIn("<script", template.lower())
        self.assertNotIn("http://", template.lower())
        self.assertNotIn("https://", template.lower())
        self.assertNotIn("mercado pago", template.lower())
        self.assertNotIn("mercadopago", template.lower())
        self.assertNotIn("--trax-color-", css)
        self.assertNotIn("--trax-space-", css)
        self.assertIn("--trax-ds-", css)
        self.assertIn("@media", css)

    def test_route_composes_simulator_only_at_development_boundary(self):
        path = Path("app/routes/dev_routes.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules = {
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertIn("app.services.payment_orchestration", imported_modules)
        self.assertIn("app.services.psp_simulator", imported_modules)
        orchestration_source = Path(
            "app/services/payment_orchestration.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("ScenarioController", orchestration_source)
        self.assertNotIn("SimulationScenario", orchestration_source)

    def test_route_has_no_database_or_commercial_side_effects(self):
        source = Path("app/routes/dev_routes.py").read_text(encoding="utf-8")
        payment_function = source.split("def payment_simulator():", 1)[1].split(
            '@dev.route("/dev/qa/login', 1
        )[0]
        for forbidden in ("db.", "commit(", "Subscription", "has_pro_access",
                          "credit", "User.query"):
            self.assertNotIn(forbidden, payment_function)


if __name__ == "__main__":
    unittest.main()
