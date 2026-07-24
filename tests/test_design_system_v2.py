import os
import unittest
from pathlib import Path


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from flask import render_template

from app import create_app, db
from app.config.config import TestingConfig


class DesignSystemV2Test(unittest.TestCase):
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

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_design_system_contract_defines_tokens_and_components(self):
        css = Path("app/static/css/design-system-v2.css").read_text(encoding="utf-8")

        required_tokens = [
            "--trax-ds-bg",
            "--trax-ds-surface",
            "--trax-ds-text",
            "--trax-ds-primary-active",
            "--trax-ds-secondary",
            "--trax-ds-overlay",
            "--trax-ds-font-sans",
            "--trax-ds-control-height-md",
            "--trax-ds-breakpoint-md",
            "--trax-ds-shadow-modal",
        ]
        required_components = [
            ".trax-page",
            ".trax-container",
            ".trax-button",
            ".trax-button--primary",
            ".trax-button--icon-only",
            ".trax-field",
            ".trax-input",
            ".trax-card",
            ".trax-badge",
            ".trax-alert",
            ".trax-empty-state",
        ]

        for token in required_tokens:
            self.assertIn(token, css)
        for component in required_components:
            self.assertIn(component, css)

        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_auth_templates_use_canonical_components_and_keep_accessibility(self):
        login = self.client.get("/login").get_data(as_text=True)
        register = self.client.get("/register").get_data(as_text=True)

        self.assertIn('class="trax-page auth-page auth-page--login"', login)
        self.assertIn("trax-card auth-card", login)
        self.assertIn("trax-input", login)
        self.assertIn("trax-button trax-button--primary", login)
        self.assertIn('for="login-email"', login)
        self.assertIn('aria-describedby="login-email-help', login)
        self.assertIn("data-password-toggle", login)

        self.assertIn('class="trax-page auth-page auth-page--register"', register)
        self.assertIn("trax-radio", register)
        self.assertIn("trax-checkbox", register)
        self.assertIn("<legend>Tipo de cuenta</legend>", register)
        self.assertIn('aria-describedby="register-password-help register-password-strength', register)

        register_template = Path("app/templates/register.html").read_text(encoding="utf-8")
        self.assertIn("trax-field__error auth-field-error", register_template)

    def test_auth_css_delegates_core_controls_to_design_system(self):
        css = Path("app/static/css/auth-ux-v1.css").read_text(encoding="utf-8")

        self.assertNotIn(".auth-field input,\n.auth-password input", css)
        self.assertNotIn(".auth-password button {", css)
        self.assertIn(".auth-password .trax-button", css)
        self.assertIn(".auth-field-error", css)

    def test_low_risk_pilot_template_renders_canonical_components(self):
        with self.app.test_request_context("/rubros/solicitar", method="POST"):
            html = render_template(
                "rubro_solicitado.html",
                nombre_rubro="Domotica",
                cantidad=10,
            )

        self.assertIn("trax-card trax-card--compact", html)
        self.assertIn("trax-badge trax-badge--success", html)
        self.assertIn("trax-alert trax-alert--warning", html)
        self.assertIn("trax-button trax-button--secondary", html)
        self.assertIn("Domotica", html)


if __name__ == "__main__":
    unittest.main()
