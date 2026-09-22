import html
import os
import re
import unittest
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from PIL import Image

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.services.explore_catalog_service import EXPLORE_CATALOG, ExploreTrade


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app/static/images/explorar/rubros"
TEMPLATE = ROOT / "app/templates/explorar_rubros.html"
CSS = ROOT / "app/static/css/explore-rubros-v1.css"


class ExploreRubrosUX02Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
            user = User(
                nombre="Cliente UX",
                email="cliente.ux02@example.test",
                password="not-a-real-password",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            db.session.add(user)
            db.session.commit()
            cls.user_id = user.id
        cls.response = cls.client.get("/explorar")
        cls.html = cls.response.get_data(as_text=True)

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_catalog_defines_twenty_unique_cards_and_exact_categories(self):
        self.assertEqual(
            [category.title for category in EXPLORE_CATALOG],
            [
                "Climatización y gas",
                "Electricidad, seguridad y conectividad",
                "Obra y remodelación",
                "Revestimientos y terminaciones",
                "Carpintería y metal",
            ],
        )
        trades = [trade for category in EXPLORE_CATALOG for trade in category.trades]
        self.assertEqual(len(trades), 20)
        self.assertEqual(len({trade.id for trade in trades}), 20)
        self.assertEqual(len({trade.image_filename for trade in trades}), 20)
        for category in EXPLORE_CATALOG:
            self.assertTrue(all(trade.category_id == category.id for trade in category.trades))
        self.assertEqual(self.html.count('class="rubro-card"'), 20)
        self.assertEqual(self.html.count('<h3 class="rubro-card__title">'), 20)

    def test_catalog_defines_the_approved_compact_card_contract(self):
        self.assertEqual(
            [field.name for field in fields(ExploreTrade)],
            [
                "id",
                "category_id",
                "title",
                "examples",
                "image_filename",
                "alt_text",
                "search_term",
            ],
        )
        for category in EXPLORE_CATALOG:
            self.assertRegex(category.id, r"^[a-z0-9-]+$")
            for trade in category.trades:
                with self.subTest(trade=trade.id):
                    self.assertTrue(trade.title)
                    self.assertTrue(trade.examples)
                    self.assertLessEqual(len(trade.examples), 3)
                    self.assertTrue(trade.alt_text.startswith("Escena ilustrativa"))
                    self.assertTrue(trade.search_term)
                    self.assertNotIn("|safe", TEMPLATE.read_text(encoding="utf-8"))

    def test_only_approved_canonical_search_mappings_are_narrowed(self):
        terms = {
            trade.title: trade.search_term
            for category in EXPLORE_CATALOG
            for trade in category.trades
        }
        self.assertEqual(terms["Electricidad domiciliaria"], "Electricista")
        self.assertEqual(terms["Plomería"], "Plomero")
        self.assertEqual(terms["Aire acondicionado"], "Técnico en Aire Acondicionado")
        for title, term in terms.items():
            if title not in {"Electricidad domiciliaria", "Plomería", "Aire acondicionado"}:
                self.assertEqual(term, title)

    def test_images_exist_are_valid_webp_and_have_required_markup(self):
        expected = {
            trade.image_filename
            for category in EXPLORE_CATALOG
            for trade in category.trades
        }
        self.assertEqual({path.name for path in ASSETS.glob("*.webp")}, expected)
        image_tags = re.findall(r'<img\s+class="rubro-card__image"[^>]+>', self.html)
        self.assertEqual(len(image_tags), 20)
        for filename in expected:
            path = ASSETS / filename
            with self.subTest(filename=filename), Image.open(path) as image:
                image.load()
                self.assertEqual(image.format, "WEBP")
                self.assertEqual(image.size, (1200, 900))
            tag = next(tag for tag in image_tags if f"/{filename}" in tag)
            self.assertIn('width="1200"', tag)
            self.assertIn('height="900"', tag)
            self.assertIn('loading="lazy"', tag)
            self.assertIn('decoding="async"', tag)
            self.assertRegex(tag, r'alt="Escena ilustrativa [^"]+"')

    def test_static_images_are_served_as_webp(self):
        for category in EXPLORE_CATALOG:
            for trade in category.trades:
                url = f"/static/images/explorar/rubros/{trade.image_filename}"
                with self.subTest(url=url):
                    for method in ("HEAD", "GET"):
                        response = self.client.open(url, method=method)
                        try:
                            self.assertEqual(response.status_code, 200)
                            self.assertEqual(response.headers["Content-Type"], "image/webp")
                            if method == "GET":
                                self.assertTrue(response.data)
                            else:
                                self.assertEqual(response.data, b"")
                        finally:
                            response.close()

    def test_heading_hierarchy_category_anchors_and_general_action(self):
        self.assertEqual(self.response.status_code, 200)
        main = self.html.split('<main class="explore-rubros">', 1)[1].split("</main>", 1)[0]
        self.assertEqual(main.count("<h1>"), 1)
        self.assertIn("<h1>Explorá rubros</h1>", main)
        self.assertIn("Encontrá el servicio que necesitás y buscá profesionales en tu zona.", main)
        self.assertEqual(main.count("<h2 "), 5)
        self.assertIn('aria-label="Categorías de rubros"', main)
        for category in EXPLORE_CATALOG:
            self.assertIn(f'href="#{category.id}"', main)
            self.assertIn(f'id="{category.id}"', main)
            self.assertIn(f'id="{category.id}-title"', main)
        self.assertIn('href="/buscar"', main)
        self.assertIn("Ver todos los profesionales", main)

    def test_visible_get_search_has_service_zone_and_no_javascript_dependency(self):
        form = self.html.split('class="explore-search"', 1)[1].split("</form>", 1)[0]
        self.assertIn('action="/buscar" method="GET"', self.html)
        self.assertIn('for="explore-service"', form)
        self.assertIn('name="servicio"', form)
        self.assertIn('for="explore-zone"', form)
        self.assertIn('name="zona"', form)
        self.assertIn("Buscar profesionales", form)
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn("<script", template)
        self.assertNotIn("javascript:", template.lower())
        main = self.html.split('<main class="explore-rubros">', 1)[1].split("</main>", 1)[0]
        for unsupported_claim in ("más buscados", "más contratados", "más populares"):
            self.assertNotIn(unsupported_claim, main.casefold())
        self.assertNotIn("profesionales disponibles", main.casefold())

    def test_card_links_encode_terms_and_reach_search(self):
        links = re.findall(
            r'href="([^"]+)">\s*Explorar profesionales',
            self.html,
        )
        expected_terms = [
            trade.search_term
            for category in EXPLORE_CATALOG
            for trade in category.trades
        ]
        self.assertEqual(len(links), 20)
        decoded_links = [html.unescape(link) for link in links]
        self.assertEqual(
            [parse_qs(urlsplit(link).query)["servicio"][0] for link in decoded_links],
            expected_terms,
        )
        for link in decoded_links:
            with self.subTest(link=link):
                response = self.client.get(link)
                self.assertEqual(response.status_code, 200)
                self.assertIn("No encontramos profesionales con esos filtros.", response.get_data(as_text=True))

    def test_approved_cards_render_title_tags_and_action_without_description_slot(self):
        main = self.html.split('<main class="explore-rubros">', 1)[1].split("</main>", 1)[0]
        card_bodies = re.findall(
            r'<div class="rubro-card__body">(.*?)</div>',
            main,
            flags=re.DOTALL,
        )
        self.assertEqual(len(card_bodies), 20)
        for category in EXPLORE_CATALOG:
            for trade in category.trades:
                with self.subTest(trade=trade.id):
                    for example in trade.examples:
                        self.assertIn(f"<li>{example}</li>", main)

        for body in card_bodies:
            self.assertEqual(body.count('class="rubro-card__title"'), 1)
            self.assertEqual(body.count('class="rubro-card__examples"'), 1)
            self.assertEqual(body.count("rubro-card__action"), 1)
            self.assertNotIn("<p", body)

        self.assertEqual(main.count("Explorar profesionales"), 20)
        self.assertEqual(main.count("trax-button--primary rubro-card__action"), 20)
        self.assertNotIn("Buscar este servicio", main)
        self.assertNotIn("description", {field.name for field in fields(ExploreTrade)})

        css = CSS.read_text(encoding="utf-8")
        self.assertIn("color: var(--trax-orange-700)", css)
        self.assertIn(".theme-dark .rubro-card__examples li", css)
        self.assertIn("color: var(--trax-ds-primary)", css)
        self.assertIn("border: 1px solid var(--trax-ds-primary-border)", css)
        self.assertIn("background: var(--trax-ds-primary-soft)", css)
        self.assertIn("font-weight: var(--trax-font-weight-semibold)", css)

    def test_cards_use_one_shared_grid_structure_without_artificial_fillers(self):
        main = self.html.split('<main class="explore-rubros">', 1)[1].split("</main>", 1)[0]
        template = TEMPLATE.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")

        self.assertEqual(main.count('class="rubro-card"'), 20)
        self.assertEqual(main.count('class="rubro-card__title"'), 20)
        self.assertEqual(main.count('class="rubro-card__examples"'), 20)
        self.assertEqual(main.count("rubro-card__action"), 20)
        self.assertNotIn('style="', template)
        self.assertNotIn("rubro-card__spacer", template)
        self.assertNotIn("&nbsp;", template)

        self.assertRegex(css, r"\.rubro-grid\s*\{[^}]*align-items:\s*stretch")
        self.assertRegex(css, r"\.rubro-card\s*\{[^}]*grid-template-rows:\s*auto 1fr")
        self.assertRegex(css, r"\.rubro-card\s*\{[^}]*height:\s*100%")
        self.assertRegex(css, r"\.rubro-card__body\s*\{[^}]*grid-template-areas:")
        self.assertRegex(css, r"\.rubro-card__title\s*\{[^}]*min-block-size:\s*3\.15rem")
        self.assertRegex(css, r"\.rubro-card__examples\s*\{[^}]*grid-area:\s*examples")
        self.assertRegex(css, r"\.rubro-card__action\s*\{[^}]*grid-area:\s*action")
        self.assertNotIn("nth-child", css)
        self.assertNotIn("position: absolute", css)

    def test_search_preserves_service_and_zone_with_accents_and_special_characters(self):
        servicio = "Cerámicos & porcelanato <especial>"
        zona = "Núñez & Belgrano"
        response = self.client.get("/buscar", query_string={"servicio": servicio, "zona": zona})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cerámicos &amp; porcelanato &lt;especial&gt;", body)
        self.assertIn("Núñez &amp; Belgrano", body)
        self.assertIn(
            'value="Cerámicos &amp; porcelanato &lt;especial&gt;" selected',
            body,
        )
        self.assertNotIn("<especial>", body)

    def test_route_is_available_to_visitors_and_authenticated_users(self):
        visitor = self.client.get("/explorar")
        self.assertEqual(visitor.status_code, 200)
        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id
        authenticated = self.client.get("/explorar")
        self.assertEqual(authenticated.status_code, 200)
        self.assertIn("Explorá rubros", authenticated.get_data(as_text=True))
        with self.client.session_transaction() as session:
            session.clear()

    def test_empty_catalog_is_distinct_from_professional_search_empty_state(self):
        with patch("app.routes.main_routes.get_explore_catalog", return_value=()):
            response = self.client.get("/explorar")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("El catálogo no está disponible.", body)
        self.assertNotIn("No encontramos profesionales", body)

    def test_unexpected_catalog_error_is_not_presented_as_no_professionals(self):
        with patch("app.routes.main_routes.get_explore_catalog", side_effect=RuntimeError("marker")):
            response = self.client.get("/explorar")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Error interno", body)
        self.assertNotIn("No encontramos profesionales", body)
        self.assertNotIn("marker", body)

    def test_css_has_required_breakpoints_touch_targets_focus_and_no_overflow(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("@media (min-width: 48rem)", css)
        self.assertIn("@media (min-width: 80rem)", css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr))", css)
        self.assertIn("flex-wrap: wrap", css)
        self.assertIn("min-height: 44px", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("object-fit: cover", css)
        self.assertIn("aspect-ratio: 4 / 3", css)
        self.assertIn("overflow-x: clip", css)
        self.assertIn(".explore-rubros__hero h1 {", css)
        self.assertIn("color: var(--trax-white)", css)


if __name__ == "__main__":
    unittest.main()
