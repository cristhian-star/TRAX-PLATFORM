import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app
from app.config.config import TestingConfig
from app.services.market_view_service import (
    MARKET_DEMAND_REFERENCES,
    MARKET_INDICATORS,
    MARKET_PRICE_REFERENCES,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "app/templates/mercados.html"
CSS = ROOT / "app/static/css/markets-v2.css"
CAROUSEL_JS = ROOT / "app/static/js/markets-carousel.js"


class MarketsUX03Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        cls.client = cls.app.test_client()
        cls.response = cls.client.get("/mercados")
        cls.html = cls.response.get_data(as_text=True)

    def test_route_is_public_and_preserves_the_approved_navigation(self):
        self.assertEqual(self.response.status_code, 200)
        navigation = self.html.split('<nav id="primary-navigation"', 1)[1].split("</nav>", 1)[0]
        text = " ".join(re.sub(r"<[^>]+>", " ", navigation).split())
        labels = [
            "Inicio",
            "Explorar rubros",
            "Precios de mercado",
            "Operaciones",
            "Ecosistema",
            "Planes",
        ]
        positions = [text.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(navigation.count('href="/mercados"'), 1)
        self.assertIn('href="/mercados" aria-current="page"', navigation)
        self.assertNotIn("Mi panel", text)

    def test_hero_keeps_the_purpose_without_the_removed_labels_or_notice(self):
        self.assertIn("Precios de mercado para decidir mejor", self.html)
        self.assertNotIn("Referencia pública de precios", self.html)
        self.assertNotIn("Datos demostrativos", self.html)
        self.assertNotIn('class="market-guide__notice"', self.html)
        self.assertNotIn("Market intelligence", self.html)

    def test_indicators_are_complete_simulated_and_live_inside_the_hero(self):
        self.assertEqual(len(MARKET_INDICATORS), 4)
        self.assertEqual(self.html.count('class="market-guide__indicator"'), 4)
        hero = self.html.split('class="market-guide__hero"', 1)[1].split("</section>", 1)[0]
        self.assertEqual(hero.count('class="market-guide__indicator"'), 4)
        self.assertIn("Indicadores de referencia", hero)
        self.assertIn("Valores simulados", hero)
        for indicator in MARKET_INDICATORS:
            with self.subTest(indicator=indicator.label):
                self.assertIn(indicator.label, self.html)
                self.assertIn(indicator.value, self.html)
                self.assertIn("simulad", indicator.description.lower())

    def test_each_price_category_has_five_pending_ranges_and_an_encoded_search_link(self):
        self.assertEqual(len(MARKET_PRICE_REFERENCES), 6)
        self.assertEqual(self.html.count('class="market-guide__price-card"'), 6)
        self.assertEqual(self.html.count('class="market-guide__work-row"'), 30)
        self.assertEqual(self.html.count("$0 – $0"), 30)
        self.assertIn("Los valores en $0 son marcadores temporales", self.html)
        links = re.findall(
            r'class="market-guide__price-action" href="([^"]+)"', self.html
        )
        self.assertEqual(len(links), 6)
        for reference, link in zip(MARKET_PRICE_REFERENCES, links):
            with self.subTest(service=reference.service):
                self.assertIn(reference.service, self.html)
                self.assertEqual(len(reference.works), 5)
                for work in reference.works:
                    self.assertIn(work.name, self.html)
                    self.assertIn(work.unit, self.html)
                    self.assertEqual(work.price_range, "$0 – $0")
                parsed = urlsplit(link.replace("&amp;", "&"))
                self.assertEqual(parsed.path, "/buscar")
                self.assertEqual(parse_qs(parsed.query), {"servicio": [reference.search_term]})

    def test_hero_carousel_uses_four_local_pairs_with_a_no_script_fallback(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertEqual(template.count('class="market-guide__visual-slide'), 4)
        self.assertEqual(template.count("images/home/hero/"), 8)
        first_slide = template.split('class="market-guide__visual-slide is-active"', 1)[1].split("</div>", 1)[0]
        self.assertEqual(first_slide.count("<img "), 2)
        self.assertEqual(first_slide.count("fetchpriority=\"high\""), 2)
        self.assertNotIn("data-src", first_slide)
        self.assertNotRegex(template, r"https?://|//cdn")

    def test_carousel_advances_every_three_seconds_and_can_pause_for_accessibility(self):
        script = CAROUSEL_JS.read_text(encoding="utf-8")
        self.assertIn("window.setTimeout(advance, 3000)", script)
        self.assertIn('prefers-reduced-motion: reduce', script)
        self.assertIn('aria-pressed', script)
        self.assertIn('Pausar imágenes', script)
        self.assertIn('Reanudar imágenes', script)
        self.assertIn('document.hidden', script)
        self.assertIn('pointerenter', script)
        self.assertIn('focusin', script)

    def test_demo_trends_use_four_semantic_line_charts_with_accessible_values(self):
        self.assertEqual(len(MARKET_DEMAND_REFERENCES), 4)
        self.assertEqual(
            [trend.service for trend in MARKET_DEMAND_REFERENCES],
            ["Electricidad", "Refrigeración", "Plomería", "Herrería"],
        )
        self.assertNotIn("<progress ", self.html)
        self.assertEqual(self.html.count('class="market-guide__trend-chart"'), 4)
        self.assertEqual(self.html.count('class="market-guide__trend-line"'), 4)
        self.assertEqual(self.html.count('class="market-guide__trend-area"'), 4)
        self.assertEqual(self.html.count('class="market-guide__trend-point"'), 24)
        self.assertEqual(self.html.count("Tendencia demostrativa"), 4)
        self.assertEqual(self.html.count('role="img" aria-labelledby="trend-chart-title-'), 4)
        for trend in MARKET_DEMAND_REFERENCES:
            with self.subTest(service=trend.service):
                self.assertEqual(len(trend.values), 6)
                self.assertEqual(len(trend.chart_points), 6)
                self.assertIn(trend.line_points, self.html)
                self.assertIn(trend.area_points, self.html)
                self.assertIn(trend.closing_trend, self.html)
                self.assertIn(trend.summary, self.html)
                for period, value in enumerate(trend.values, start=1):
                    self.assertIn(
                        f"Período demostrativo {period}: índice simulado {value}",
                        self.html,
                    )
        self.assertIn("No representan operaciones ni mediciones reales", self.html)

    def test_trend_charts_use_local_svg_and_responsive_unique_cards(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")
        self.assertEqual(template.count('<article class="market-guide__trend">'), 1)
        self.assertIn("<svg", template)
        self.assertIn("<polyline", template)
        self.assertIn("<polygon", template)
        self.assertIn("<circle", template)
        self.assertNotIn("Chart.js", template)
        self.assertNotIn("<canvas", template)
        self.assertNotRegex(template, r"https?://|//cdn")
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css)
        self.assertNotIn("grid-template-columns: repeat(4, minmax(0, 1fr))", css)
        self.assertIn("min-height: 22rem", css)
        self.assertIn("stroke: var(--trax-ds-primary)", css)
        self.assertIn(".market-guide__trend-values", css)

    def test_page_has_semantic_sections_accessible_local_icons_and_real_actions(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertGreaterEqual(self.html.count("<h2"), 5)
        self.assertGreaterEqual(self.html.count('aria-labelledby="'), 6)
        self.assertGreaterEqual(self.html.count('aria-hidden="true" focusable="false"'), 15)
        self.assertNotRegex(template, r"https?://|//cdn")
        self.assertIn("js/markets-carousel.js", template)
        self.assertNotRegex(self.html, r'href="(?:#|javascript:)')
        self.assertIn('href="/explorar"', self.html)
        self.assertIn('href="/presupuestos/nuevo"', self.html)

    def test_methodology_and_interpretation_explain_limits_without_fake_controls(self):
        for text in (
            "Cómo interpretar estos rangos",
            "Ubicación",
            "Complejidad",
            "Materiales",
            "Urgencia",
            "Temporada",
            "Metodología y transparencia",
            "datos ficticios y estables",
        ):
            self.assertIn(text, self.html)
        self.assertNotIn("<select", self.html)
        self.assertNotIn("<canvas", self.html)
        self.assertNotIn("role=\"button\"", self.html)

    def test_dynamic_market_content_is_escaped(self):
        malicious = '<img src=x onerror=alert("markets-xss")>'
        context = {
            "market_indicators": [
                {
                    "icon": "wallet",
                    "label": malicious,
                    "value": malicious,
                    "description": malicious,
                }
            ],
            "market_price_references": [],
            "market_demand_references": [],
        }
        with patch(
            "app.routes.main_routes.build_markets_page_context",
            return_value=context,
        ):
            html = self.client.get("/mercados").get_data(as_text=True)
        self.assertNotIn(malicious, html)
        self.assertNotIn("<img src=x", html)
        self.assertGreaterEqual(html.count("&lt;img"), 2)

    def test_styles_cover_themes_reflow_touch_targets_and_focus_without_duplication(self):
        css = CSS.read_text(encoding="utf-8")
        for token in (
            "var(--trax-ds-bg)",
            "var(--trax-ds-card)",
            "var(--trax-ds-text)",
            "var(--trax-ds-text-muted)",
            "var(--trax-ds-border)",
            "var(--trax-ds-primary)",
        ):
            self.assertIn(token, css)
        self.assertIn("min-height: 44px", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("@media (min-width: 48rem)", css)
        self.assertIn("@media (min-width: 64rem)", css)
        self.assertIn("@media (max-width: 47.99rem)", css)
        self.assertIn("@media (max-width: 24rem)", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertNotRegex(css, r"\.market-guide__price-card\s*\{[^}]*position:\s*absolute")
        self.assertEqual(TEMPLATE.read_text(encoding="utf-8").count("market-guide__prices"), 1)


if __name__ == "__main__":
    unittest.main()
