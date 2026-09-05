import os
import re
import unittest
from pathlib import Path


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from flask import flash, render_template

from app import create_app, db
from app.config.config import TestingConfig
from app.models.activity_notification import ActivityNotification
from app.models.user import User


def _css_block(css, selector):
    match = re.search(rf"{re.escape(selector)}\s*\{{([^{{}}]*)\}}", css)
    if match is None:
        raise AssertionError(f"CSS selector not found: {selector}")
    return match.group(1)


def _css_declarations(block):
    declarations = {}
    for property_name, value in re.findall(
        r"(?m)^\s*([a-z-]+)\s*:\s*([^;]+);", block
    ):
        declarations.setdefault(property_name, []).append(value.strip())
    return declarations


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
            ".trax-toast-region",
            ".trax-modal",
            ".trax-modal__dialog",
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

    def test_base_loads_design_system_before_legacy_styles(self):
        base = Path("app/templates/base.html").read_text(encoding="utf-8")
        styles = Path("app/static/css/styles.css").read_text(encoding="utf-8")

        design_tokens_index = base.index("css/design-tokens.css")
        design_system_index = base.index("css/design-system-v2.css")
        legacy_styles_index = base.index("css/styles.css")

        self.assertLess(design_tokens_index, design_system_index)
        self.assertLess(design_system_index, legacy_styles_index)
        self.assertNotIn("@import url(\"design-system-v2.css\")", styles)

    def test_auth_css_delegates_core_controls_to_design_system(self):
        css = Path("app/static/css/auth-ux-v1.css").read_text(encoding="utf-8")

        self.assertNotIn(".auth-field input,\n.auth-password input", css)
        self.assertNotIn(".auth-password button {", css)
        self.assertIn(".auth-password .trax-button", css)
        self.assertIn(".auth-field-error", css)

    def test_pro_upgrade_and_admin_users_surfaces_use_theme_tokens(self):
        css = Path("app/static/css/styles.css").read_text(encoding="utf-8")
        admin_template = Path("app/templates/admin_usuarios.html").read_text(
            encoding="utf-8"
        )

        required_blocks = {
            (
                ".pro-upgrade-screen .upgrade-summary article,\n"
                ".pro-upgrade-screen .upgrade-benefits article,\n"
                ".pro-upgrade-screen .upgrade-action-card"
            ): {
                "background": "var(--trax-ds-card)",
                "color": "var(--trax-ds-text)",
                "border-color": "var(--trax-ds-border-subtle)",
            },
            ".admin-users-screen .admin-nav a": {
                "background": "var(--trax-ds-surface)",
                "color": "var(--trax-ds-text-strong)",
                "border-color": "var(--trax-ds-border)",
            },
            ".admin-users-table.admin-table": {
                "background": "var(--trax-ds-card)",
                "color": "var(--trax-ds-text)",
            },
            ".admin-users-table.admin-table th": {
                "background": "var(--trax-ds-surface-soft)",
                "color": "var(--trax-ds-text-strong)",
                "border-color": "var(--trax-ds-border-subtle)",
            },
            ".admin-users-table.admin-table td": {
                "color": "var(--trax-ds-text)",
                "border-color": "var(--trax-ds-border-subtle)",
            },
            ".admin-users-table .user-status-pill.is-muted": {
                "background": "var(--trax-ds-surface-soft)",
                "color": "var(--trax-ds-text-muted)",
            },
            ".admin-users-table .admin-user-actions button": {
                "background": "var(--trax-ds-surface)",
                "color": "var(--trax-ds-text-strong)",
                "border-color": "var(--trax-ds-border)",
            },
            ".admin-users-table .admin-user-actions button.danger": {
                "background": "var(--trax-ds-danger-soft)",
                "color": "var(--trax-ds-danger)",
                "border-color": "var(--trax-ds-danger-border)",
            },
        }

        literal_color = re.compile(
            r"#[0-9a-f]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(|\b(?:white|black)\b",
            re.IGNORECASE,
        )
        for selector, expected_properties in required_blocks.items():
            block = _css_block(css, selector)
            declarations = _css_declarations(block)
            self.assertIsNone(
                literal_color.search(block),
                msg=f"Literal color found in {selector}",
            )
            for property_name in ("background", "color", "border-color"):
                self.assertLessEqual(
                    len(declarations.get(property_name, [])),
                    1,
                    msg=f"Duplicate {property_name} declaration in {selector}",
                )
            for property_name, expected_value in expected_properties.items():
                values = declarations.get(property_name, [])
                self.assertEqual(
                    len(values),
                    1,
                    msg=f"Expected one {property_name} declaration in {selector}",
                )
                self.assertEqual(
                    values[-1],
                    expected_value,
                    msg=f"Unexpected effective {property_name} in {selector}",
                )

        self.assertIn(
            'class="section-container admin-management-screen admin-users-screen"',
            admin_template,
        )

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

    def test_base_flash_messages_render_canonical_alerts_by_category(self):
        @self.app.route("/_test/ds/flash")
        def _test_ds_flash():
            flash("Operacion completada", "success")
            flash("Revisar datos", "warning")
            flash("No autorizado", "error")
            return render_template(
                "rubro_solicitado.html",
                nombre_rubro="Electricidad",
                cantidad=1,
            )

        html = self.client.get("/_test/ds/flash").get_data(as_text=True)

        self.assertIn("trax-toast-region", html)
        self.assertIn("trax-alert trax-alert--success trax-alert--dismissible", html)
        self.assertIn("trax-alert trax-alert--warning trax-alert--dismissible", html)
        self.assertIn("trax-alert trax-alert--danger trax-alert--dismissible", html)
        self.assertIn('aria-live="assertive"', html)
        self.assertIn('data-trax-alert-dismiss', html)

    def test_notifications_page_uses_canonical_components_without_route_regression(self):
        with self.app.app_context():
            user = User(
                nombre="Cliente Notificaciones",
                email="cliente-notificaciones@trax.test",
                password="hash",
                rol="CLIENTE",
            )
            db.session.add(user)
            db.session.commit()
            db.session.add(
                ActivityNotification(
                    user_id=user.id,
                    tipo="CUENTA_VERIFICADA",
                    categoria="CUENTA",
                    titulo="Cuenta activa",
                    mensaje="Tu cuenta esta lista para operar.",
                    prioridad="ACCION_REQUERIDA",
                    requiere_accion=True,
                    url_destino="/",
                )
            )
            db.session.commit()
            user_id = user.id

        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_role"] = "CLIENTE"
            sess["user_name"] = "Cliente Notificaciones"

        response = self.client.get("/notificaciones")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("trax-page notifications-page", html)
        self.assertIn("trax-card notification-card", html)
        self.assertIn("trax-badge trax-badge--info", html)
        self.assertIn("trax-badge trax-badge--warning", html)
        self.assertIn("trax-button trax-button--secondary", html)
        self.assertIn("Accion Requerida", html)

    def test_notifications_empty_state_uses_canonical_component(self):
        with self.app.app_context():
            user = User(
                nombre="Cliente Sin Novedades",
                email="sin-novedades@trax.test",
                password="hash",
                rol="CLIENTE",
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_role"] = "CLIENTE"
            sess["user_name"] = "Cliente Sin Novedades"

        html = self.client.get("/notificaciones").get_data(as_text=True)

        self.assertIn("trax-empty-state notifications-page__empty", html)
        self.assertIn("trax-empty-state__title", html)
        self.assertIn("Podes volver a revisar mas tarde", html)

    def test_whatsapp_modal_uses_canonical_modal_and_keeps_data_selectors(self):
        with self.app.test_request_context("/"):
            html = render_template("components/_whatsapp_consent_modal.html")

        self.assertIn("trax-modal whatsapp-consent-modal", html)
        self.assertIn('role="dialog"', html)
        self.assertIn('aria-modal="true"', html)
        self.assertIn('aria-labelledby="whatsapp-consent-title"', html)
        self.assertIn('aria-describedby="whatsapp-consent-description"', html)
        self.assertIn("trax-modal__dialog whatsapp-consent-modal__content", html)
        self.assertIn("data-whatsapp-consent-checkbox", html)
        self.assertIn("data-whatsapp-consent-confirm", html)


if __name__ == "__main__":
    unittest.main()
