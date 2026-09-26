import os
import re
import unittest
from pathlib import Path


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User


ROOT = Path(__file__).resolve().parents[1]


def primary_navigation(html):
    return html.split('<nav id="primary-navigation"', 1)[1].split("</nav>", 1)[0]


def normalized_text(fragment):
    return " ".join(re.sub(r"<[^>]+>", " ", fragment).split())


class NavbarMarketsUX03ATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
            SERVER_NAME="localhost",
        )
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()
            users = [
                User(
                    nombre="Cliente Navbar",
                    email="cliente-navbar@example.test",
                    password="not-a-real-password",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Profesional Navbar",
                    email="profesional-navbar@example.test",
                    password="not-a-real-password",
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
            ]
            db.session.add_all(users)
            db.session.commit()
            cls.user_ids = {user.rol: user.id for user in users}

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def tearDown(self):
        with self.client.session_transaction() as session:
            session.clear()

    def _login_as(self, role):
        with self.client.session_transaction() as session:
            session["user_id"] = self.user_ids[role]
            session["user_name"] = f"{role.title()} Navbar"
            session["user_role"] = role

    def _assert_public_navigation_contract(self, html):
        navigation = primary_navigation(html)
        expected_labels = [
            "Inicio",
            "Explorar rubros",
            "Precios de mercado",
            "Operaciones",
            "Ecosistema",
            "Planes",
        ]
        positions = [normalized_text(navigation).index(label) for label in expected_labels]

        self.assertEqual(positions, sorted(positions))
        self.assertEqual(navigation.count('href="/mercados"'), 1)
        self.assertEqual(normalized_text(navigation).count("Precios de mercado"), 1)
        self.assertNotRegex(normalized_text(navigation), r"(?:^|\s)Mercados(?:\s|$)")
        self.assertNotIn("Mi panel", normalized_text(navigation))

    def test_public_navigation_has_the_exact_market_position_and_label(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self._assert_public_navigation_contract(response.get_data(as_text=True))

    def test_client_navigation_keeps_the_same_public_order(self):
        self._login_as("CLIENTE")

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self._assert_public_navigation_contract(response.get_data(as_text=True))

    def test_professional_navigation_keeps_the_same_public_order(self):
        self._login_as("PROFESIONAL")

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self._assert_public_navigation_contract(response.get_data(as_text=True))

    def test_markets_route_is_public_and_has_one_active_navigation_link(self):
        response = self.client.get("/mercados")
        navigation = primary_navigation(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '<a href="/mercados" aria-current="page">Precios de mercado</a>',
            navigation,
        )
        self.assertEqual(navigation.count('aria-current="page"'), 1)

    def test_authenticated_roles_keep_the_same_public_markets_route(self):
        for role in ("CLIENTE", "PROFESIONAL"):
            with self.subTest(role=role):
                self._login_as(role)
                response = self.client.get("/mercados")
                navigation = primary_navigation(response.get_data(as_text=True))
                self.assertEqual(response.status_code, 200)
                self.assertIn('href="/mercados" aria-current="page"', navigation)

    def test_mobile_uses_the_same_navigation_without_a_duplicate_copy(self):
        html = self.client.get("/").get_data(as_text=True)
        css = (ROOT / "app/static/css/visitor-navbar-v1.css").read_text(encoding="utf-8")

        self.assertEqual(html.count('id="primary-navigation"'), 1)
        self.assertIn('aria-controls="primary-navigation"', html)
        self.assertIn("@media (max-width: 820px)", css)
        self.assertIn("body.menu-open .site-header--visitor .main-nav--visitor", css)
        self._assert_public_navigation_contract(html)

    def test_active_link_keeps_visible_focus_and_theme_compatible_tokens(self):
        css = (ROOT / "app/static/css/visitor-navbar-v1.css").read_text(encoding="utf-8")

        self.assertIn('.main-nav--visitor > a[aria-current="page"]', css)
        self.assertIn("color: var(--trax-color-action-primary)", css)
        self.assertIn(".main-nav--visitor > a:focus-visible", css)


if __name__ == "__main__":
    unittest.main()
