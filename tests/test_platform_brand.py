import hashlib
import io
import os
import unittest
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from flask import render_template
from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/static/img/branding/mandobra/"
HASHES = {
    "light": "4d5e5b8738979d373ab5021f0ba89f15bd98d2ccd831fff47097025a6dfacb9e",
    "dark": "ca6933542a281720f24d5fc3e9c1be2a4c6f9ce21458a14da81f601694cf2f0f",
}
LEGACY = ("ahora_si2.png", "mandobra-wordmark-on-dark.png", "mandobra-symbol-compact.png")


class BrandParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.brand = None
        self.images = []
        self.text = []
        self.inside = False
        self.nav_count = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("id") == "primary-navigation":
            self.nav_count += 1
        if tag == "a" and "brand" in attrs.get("class", "").split():
            self.brand = attrs
            self.inside = True
        if self.inside and tag == "img":
            self.images.append(attrs)

    def handle_endtag(self, tag):
        if tag == "a":
            self.inside = False

    def handle_data(self, data):
        if self.inside and data.strip():
            self.text.append(data.strip())


class PlatformBrandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, RATELIMIT_ENABLED=False, WTF_CSRF_ENABLED=False)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
            users = [User(nombre=f"Brand {role}", email=f"brand-{role.lower()}@example.test", password="test", rol=role, estado="ACTIVO")
                     for role in ("CLIENTE", "PROFESIONAL", "SUPER_ADMIN")]
            db.session.add_all(users)
            db.session.commit()
            cls.user_ids = {user.rol: user.id for user in users}
            cls.user_id = cls.user_ids["CLIENTE"]

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def tearDown(self):
        with self.client.session_transaction() as session:
            session.clear()

    def home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def assert_shared_brand(self, html):
        brand = BrandParser(html)
        self.assertEqual([i["src"] for i in brand.images], [PREFIX + f"mandobra-wordmark-{v}.png" for v in HASHES])
        self.assertEqual(brand.brand["aria-label"], "MANDOBRA inicio")
        self.assertEqual(brand.nav_count, 1)
        self.assertNotIn("brand--home-canary", html)

    def test_public_home_has_two_local_assets_and_one_accessible_navigation(self):
        brand = BrandParser(self.home())
        self.assertEqual(brand.nav_count, 1)
        self.assertEqual(brand.brand["aria-label"], "MANDOBRA inicio")
        self.assertEqual(brand.brand["href"], "/")
        self.assertEqual([i["src"] for i in brand.images], [PREFIX + f"mandobra-wordmark-{v}.png" for v in HASHES])
        self.assertEqual(brand.text, [])  # no added slogan or Casa text
        for image in brand.images:
            self.assertEqual(image["alt"], "")
            self.assertEqual(image["aria-hidden"], "true")
            self.assertEqual((image["width"], image["height"]), ("1696", "720"))

    def test_public_pages_use_shared_brand(self):
        for path in ("/mercados", "/explorar", "/login", "/register", "/planes", "/buscar"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assert_shared_brand(response.get_data(as_text=True))

    def test_authenticated_home_uses_shared_brand(self):
        with self.client.session_transaction() as session:
            session.update(user_id=self.user_id, user_name="Canary", user_role="CLIENTE")
        self.assert_shared_brand(self.home())

    def test_base_uses_shared_brand_without_path_or_template_opt_in(self):
        for path in ("/", "/profesional/dashboard", "/contratacion/nueva"):
            with self.subTest(path=path), self.app.test_request_context(path):
                self.assert_shared_brand(render_template("base.html"))

    def test_dashboards_and_operational_pages_use_shared_brand(self):
        for role, dashboard in (("CLIENTE", "/cliente/dashboard"), ("PROFESIONAL", "/profesional/dashboard"), ("SUPER_ADMIN", "/admin/dashboard")):
            with self.client.session_transaction() as session:
                session.clear()
                session.update(user_id=self.user_ids[role], user_name=f"Brand {role}", user_role=role)
            for path in ("/", dashboard, "/notificaciones"):
                with self.subTest(role=role, path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assert_shared_brand(response.get_data(as_text=True))
                    self.assertIn("site-header--authenticated", response.get_data(as_text=True))

    def test_no_template_retains_canary_opt_in(self):
        for p in (ROOT / "app/templates").rglob("*.html"):
            self.assertNotIn("home_brand_canary", p.read_text(encoding="utf-8"))

    def test_assets_get_head_png_hash_and_shared_alpha(self):
        alphas = []
        for variant, expected in HASHES.items():
            url = PREFIX + f"mandobra-wordmark-{variant}.png"
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "image/png")
            self.assertEqual(hashlib.sha256(response.data).hexdigest(), expected)
            head = self.client.head(url)
            self.assertEqual((head.status_code, head.mimetype), (200, "image/png"))
            with Image.open(io.BytesIO(response.data)) as image:
                self.assertEqual((image.format, image.mode, image.size), ("PNG", "RGBA", (1696, 720)))
                alphas.append(image.getchannel("A").tobytes())
            response.close()
            head.close()
        self.assertEqual(alphas[0], alphas[1])
        self.assertIn(0, alphas[0])
        self.assertIn(255, alphas[0])

    def test_shared_css_preserves_size_and_uses_contain(self):
        css = (ROOT / "app/static/css/visitor-navbar-v1.css").read_text(encoding="utf-8")
        image_rule = css.split(".site-header--visitor .brand-logo {", 1)[1].split("}", 1)[0]
        self.assertIn("object-fit: contain", image_rule)
        self.assertNotIn("cover", image_rule)
        self.assertIn("width: 100%", image_rule)
        self.assertIn("height: 100%", image_rule)
        self.assertIn("width: clamp(144px, 46vw, 180px)", css)

    def test_theme_contract_is_css_only_and_initialized_before_body(self):
        css = (ROOT / "app/static/css/visitor-navbar-v1.css").read_text(encoding="utf-8")
        dark_hide = ".theme-dark .site-header--visitor .brand-logo--light"
        dark_show = ".theme-dark .site-header--visitor .brand-logo--dark"
        self.assertIn("display: none", css.split(dark_hide, 1)[1].split("}", 1)[0])
        self.assertIn("display: block", css.split(dark_show, 1)[1].split("}", 1)[0])
        html = self.home()
        self.assertLess(html.index('document.documentElement.classList.add("theme-" + theme)'), html.index("<body>"))
        self.assertIn('classList.add("theme-light")', html)

    def test_authenticated_layout_and_menu_use_shared_responsive_controls(self):
        css = (ROOT / "app/static/css/visitor-navbar-v1.css").read_text(encoding="utf-8")
        self.assertIn("@media (min-width: 821px) and (max-width: 1180px)", css)
        self.assertIn("body.menu-open .site-header--authenticated .main-nav--visitor", css)
        self.assertIn("background: var(--trax-color-surface)", css.split(".site-header--visitor .menu-toggle {", 1)[1].split("}", 1)[0])
        self.assertIn("background: var(--trax-color-text)", css.split(".site-header--visitor .menu-toggle span {", 1)[1].split("}", 1)[0])

    def test_legacy_logo_resources_still_resolve(self):
        for asset in LEGACY:
            with self.subTest(asset=asset):
                response = self.client.get(PREFIX + asset)
                self.assertEqual((response.status_code, response.mimetype), (200, "image/png"))
                response.close()


if __name__ == "__main__":
    unittest.main()
