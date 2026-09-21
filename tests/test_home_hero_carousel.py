import os
import re
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from PIL import Image

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import TestingConfig


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app/static/images/home/hero"
SCENES = (
    "electricidad", "plomeria", "refrigeracion-interior", "pintura",
    "climatizacion-exterior", "cableado-estructurado",
    "instalacion-caldera", "mesada-porcelanato",
)


class HomeHeroCarouselTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
        cls.html = cls.client.get("/").get_data(as_text=True)

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_preserves_search_and_renders_eight_local_scenes(self):
        self.assertIn('action="/buscar" method="GET"', self.html)
        self.assertIn('name="servicio"', self.html)
        self.assertIn('name="zona"', self.html)
        self.assertEqual(len(re.findall(r'class="trax-home__slide(?: |")', self.html)), 8)
        for scene in SCENES:
            self.assertIn(f"/static/images/home/hero/{scene}.webp", self.html)

    def test_first_scene_is_no_script_fallback_and_priority(self):
        first = re.search(r'<img class="trax-home__slide is-active"[^>]+>', self.html)
        self.assertIsNotNone(first)
        self.assertIn('src="/static/images/home/hero/electricidad.webp"', first.group())
        self.assertIn('fetchpriority="high"', first.group())
        self.assertNotIn("data-src", first.group())
        self.assertEqual(self.html.count('data-src="/static/images/home/hero/'), 7)

    def test_three_exact_messages_and_first_html_fallback(self):
        pairs = (
            (
                "El trabajo correcto empieza con una conexión confiable.",
                "Encontrá profesionales, compará presupuestos, resolvé una urgencia o accedé a nuevas oportunidades desde un solo lugar.",
            ),
            (
                "Tu oficio merece más oportunidades.",
                "Mostrá tu experiencia, recibí nuevas solicitudes y organizá cada trabajo desde MANDOBRA.",
            ),
            (
                "Formá parte de nuestra comunidad técnica.",
                "Clientes, profesionales y empresas conectados para resolver necesidades, crear oportunidades y hacer crecer cada oficio.",
            ),
        )
        hero = self.html.split('class="trax-home__hero"', 1)[1].split('class="trax-home__featured"', 1)[0]
        self.assertEqual(hero.count("<h1 "), 1)
        self.assertIn(f'<h1 id="home-title" class="trax-home__message-title">{pairs[0][0]}</h1>', hero)
        self.assertIn(f'<p class="trax-home__lead">{pairs[0][1]}</p>', hero)
        for title, subtitle in pairs[1:]:
            self.assertIn(f'<span class="trax-home__message-title">{title}</span>', hero)
            self.assertIn(f'<p class="trax-home__lead">{subtitle}</p>', hero)
        self.assertEqual(hero.count('data-hero-message aria-hidden="true"'), 2)
        self.assertIn('data-hero-message-content aria-live="off"', hero)

    def test_controls_have_accessible_names_and_are_hidden_without_script(self):
        for name in ("Imagen anterior", "Imagen siguiente"):
            self.assertIn(f'aria-label="{name}"', self.html)
        self.assertIn('data-hero-controls role="group"', self.html)
        self.assertIn('aria-label="Navegación de imágenes" hidden', self.html)
        self.assertIn('data-hero-status aria-live="polite"', self.html)
        hero = self.html.split('class="trax-home__hero"', 1)[1].split('class="trax-home__featured"', 1)[0]
        for removed in (
            "Servicios tecnicos y oficios", "Perfiles con reputacion visible",
            "Busqueda por servicio y zona", "Seguimiento dentro de MANDOBRA",
            "Imágenes ilustrativas", "data-hero-pause", "Pausar carrusel",
        ):
            self.assertNotIn(removed, hero)

    def test_assets_are_webp_and_within_budget(self):
        self.assertEqual({item.name for item in ASSETS.iterdir()}, {f"{scene}.webp" for scene in SCENES})
        for scene in SCENES:
            path = ASSETS / f"{scene}.webp"
            with self.subTest(scene=scene), Image.open(path) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertEqual(image.size, (1600, 900))
                self.assertLessEqual(path.stat().st_size, 150_000)

    def test_featured_section_replaces_old_cards_and_links_to_search(self):
        section = self.html.split('class="trax-home__featured"', 1)[1].split('class="trax-home__trust"', 1)[0]
        self.assertIn('aria-labelledby="featured-title"', section)
        self.assertIn('<h2 id="featured-title">Oficios destacados</h2>', section)
        self.assertIn('Explorá servicios y encontrá profesionales para resolver tu necesidad.', section)
        for removed in (
            "UNA RED PARA CADA TAREA", "Elegi como queres avanzar", "pathway",
            "Busca con criterio", "Compara propuestas", "Hace crecer tu oficio",
            "Los más buscados", "Los más solicitados", "Los más populares",
        ):
            self.assertNotIn(removed, section)

        cards = re.findall(
            r'<a class="trax-home__featured-card" href="([^"]+)">\s*'
            r'<img src="([^"]+)"([^>]+)>\s*<h3>([^<]+)</h3>\s*</a>',
            section,
        )
        # Search filters Professional.servicio as free text. The dropdown supplies
        # the first five canonical values; Pintura is an existing service value
        # but is absent from that dropdown and must not map to an unrelated trade.
        expected = (
            ("Electricidad", "Electricidad", "electricidad.webp"),
            ("Plomería", "Plomeria", "plomeria.webp"),
            ("Refrigeración y climatización", "Refrigeracion A/C", "refrigeracion-interior.webp"),
            ("Cableado estructurado", "Electricidad", "cableado-estructurado.webp"),
            ("Instalación de calderas", "Gas domiciliario", "instalacion-caldera.webp"),
            ("Pintura", "Pintura", "pintura.webp"),
        )
        self.assertEqual(len(cards), 6)
        for card, (title, value, image) in zip(cards, expected):
            href, src, attributes, label = card
            with self.subTest(title=title):
                self.assertEqual(label, title)
                self.assertEqual(urlsplit(href).path, "/buscar")
                self.assertEqual(parse_qs(urlsplit(href).query), {"servicio": [value]})
                self.assertEqual(src, f"/static/images/home/hero/{image}")
                self.assertIn('width="1600" height="900" loading="lazy"', attributes)
                self.assertIn('alt=""', attributes)
                response = self.client.get(href)
                self.assertEqual(response.status_code, 200)
                self.assertIn(value, response.get_data(as_text=True))

    def test_featured_grid_breakpoints_and_accessibility(self):
        css = (ROOT / "app/static/css/home-v1.css").read_text(encoding="utf-8")
        self.assertIn('.trax-home__featured-grid {\n    display: grid;', css)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr))', css)
        self.assertIn('grid-template-columns: repeat(3, minmax(0, 1fr))', css)
        self.assertIn('aspect-ratio: 16 / 9', css)
        self.assertIn('object-fit: cover', css)
        self.assertIn('.trax-home__featured-card:focus-visible', css)
        self.assertIn('.trax-home__featured-card {\n        transition: none;', css)
        self.assertNotIn('trax-home__pathway', css)
        self.assertNotIn('trax-home__section-heading', css)

    def test_lower_home_order_trust_faq_closing_and_footer(self):
        markers = ('class="trax-home__hero"', 'class="trax-home__featured"',
                   'class="trax-home__trust"', 'class="trax-home__faq"',
                   'class="trax-home__closing"', '<footer class="footer"')
        self.assertEqual(sorted(self.html.index(marker) for marker in markers),
                         [self.html.index(marker) for marker in markers])
        self.assertEqual(self.html.count('<footer class="footer"'), 1)
        trust = self.html.split('class="trax-home__trust"', 1)[1].split('class="trax-home__faq"', 1)[0]
        for content in (
            'Más claridad en cada etapa.',
            'Perfiles con información verificable', 'Revisá la información disponible antes de elegir.',
            'Presupuestos para comparar', 'Evaluá alcance, condiciones y propuestas antes de decidir.',
            'Seguimiento del trabajo', 'Consultá el estado de la contratación desde MANDOBRA.',
        ):
            self.assertIn(content, trust)
        self.assertEqual(trust.count('<article>'), 3)

    def test_faq_semantics_exact_copy_and_no_script_fallback(self):
        faq = self.html.split('class="trax-home__faq"', 1)[1].split('class="trax-home__closing"', 1)[0]
        self.assertIn('¿Cómo podemos ayudarte?', faq)
        self.assertIn('Encontrá respuestas rápidas sobre el uso de MANDOBRA.', faq)
        self.assertIn('type="search" placeholder="Escribí tu duda sobre MANDOBRA"', faq)
        self.assertIn('for="home-faq-search"', faq)
        self.assertIn('role="status" aria-live="polite"', faq)
        self.assertNotIn('<form', faq)
        self.assertEqual(faq.count('<details data-home-faq-item>'), 6)
        self.assertEqual(faq.count('<summary>'), 6)
        pairs = (
            ('¿Cómo encuentro y contacto a un profesional?', 'Buscá por servicio y zona, revisá los perfiles disponibles y elegí la opción de contacto o contratación correspondiente.'),
            ('¿Puedo pedir y comparar presupuestos?', 'Podés describir tu necesidad y revisar las propuestas recibidas antes de decidir cómo continuar.'),
            ('¿Cómo verifica MANDOBRA a los profesionales?', 'Los perfiles muestran la información y el estado de verificación disponible. Revisá también su experiencia, especialidad y reputación antes de elegir.'),
            ('¿Cómo funcionan los pagos dentro de la plataforma?', 'Cuando el cobro esté disponible para una contratación, MANDOBRA mostrará la orden, el importe y el medio habilitado. Abrir un enlace o QR no confirma por sí solo el pago.'),
            ('¿Qué hago si surge un problema con el trabajo?', 'Consultá el seguimiento de la contratación y utilizá los canales de ayuda disponibles para registrar la situación y conocer los próximos pasos.'),
            ('¿Cómo puedo registrarme como profesional?', 'Creá una cuenta profesional, completá tu perfil y presentá la información necesaria para su revisión antes de comenzar a recibir oportunidades.'),
        )
        for question, answer in pairs:
            self.assertIn(f'<summary>{question}</summary>\n                    <p>{answer}</p>', faq)
        self.assertIn('No encontramos una respuesta. Probá con otras palabras.', faq)
        self.assertIn('data-home-faq-empty hidden', faq)
        self.assertIn('/static/js/home-faq.js', self.html)

    def test_closing_actions_resolve_without_changing_registration(self):
        closing = self.html.split('class="trax-home__closing"', 1)[1].split('</main>', 1)[0]
        for text in ('Empezá a usar MANDOBRA.', '¿Necesitás resolver un trabajo?',
                     'Encontrá profesionales y elegí cómo avanzar según tu necesidad.',
                     '¿Querés ofrecer tus servicios?',
                     'Creá tu perfil, mostrale tu experiencia a la comunidad y accedé a nuevas oportunidades.'):
            self.assertIn(text, closing)
        actions = re.findall(r'<a class="trax-button trax-button--[^\"]+" href="([^\"]+)">([^<]+)</a>', closing)
        self.assertEqual(actions, [('/buscar', 'Buscar profesionales'), ('/register', 'Crear perfil profesional')])
        for url, _ in actions:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        css = (ROOT / 'app/static/css/home-v1.css').read_text(encoding='utf-8')
        self.assertIn('.trax-home__trust-list {\n        grid-template-columns: repeat(3, minmax(0, 1fr));', css)
        self.assertIn('.trax-home__closing-grid {\n        grid-template-columns: repeat(2, minmax(0, 1fr));', css)
        self.assertIn('.trax-home__faq summary:focus-visible', css)

    def test_static_http_mime_for_all_hero_webp_and_other_types(self):
        static_files = [
            *((f"images/home/hero/{scene}.webp", "image/webp") for scene in SCENES),
            ("css/home-v1.css", "text/css"),
            ("js/home-hero-carousel.js", "text/javascript"),
            ("img/branding/mandobra/mandobra-symbol-compact.png", "image/png"),
        ]
        for name, expected_mime in static_files:
            with self.subTest(name=name):
                url = f"/static/{name}"
                for method in ("HEAD", "GET"):
                    response = self.client.open(url, method=method)
                    try:
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.mimetype, expected_mime)
                        if expected_mime == "image/webp":
                            self.assertEqual(response.headers["Content-Type"], "image/webp")
                        if method == "GET":
                            self.assertTrue(response.data)
                        else:
                            self.assertEqual(response.data, b"")
                    finally:
                        response.close()

    def test_motion_contrast_focus_and_progressive_loading(self):
        css = (ROOT / "app/static/css/home-v1.css").read_text(encoding="utf-8")
        js = (ROOT / "app/static/js/home-hero-carousel.js").read_text(encoding="utf-8")
        self.assertIn("linear-gradient(90deg, rgba(5, 12, 23, 0.78), rgba(5, 12, 23, 0.66))", css)
        self.assertIn("object-fit: cover", css)
        self.assertIn(".trax-home__carousel-controls button:focus-visible", css)
        self.assertRegex(css, r"@media \(prefers-reduced-motion: reduce\)\s*\{\s*\.trax-home__slide\s*\{\s*transition: none")
        self.assertIn('window.matchMedia("(prefers-reduced-motion: reduce)")', js)
        self.assertIn("if (canAdvance()) imageTimer = window.setTimeout(() => void advance(1, false), 5000)", js)
        self.assertIn("if (canAdvance()) messageTimer = window.setTimeout(advanceMessage, 10000)", js)
        self.assertIn("if (imageTimer !== null) window.clearTimeout(imageTimer)", js)
        self.assertIn("if (messageTimer !== null) window.clearTimeout(messageTimer)", js)
        self.assertIn("if (messageFadeTimer !== null) window.clearTimeout(messageFadeTimer)", js)
        self.assertIn("scheduleImages();", js)
        self.assertIn("scheduleMessages();", js)
        self.assertIn("if (!canAdvance()) return", js)
        self.assertIn('previous.addEventListener("click", () => void advance(-1, true))', js)
        self.assertIn('next.addEventListener("click", () => void advance(1, true))', js)
        self.assertIn("if (manual) status.textContent", js)
        self.assertIn('hero.addEventListener("pointerenter"', js)
        self.assertIn('hero.addEventListener("touchstart"', js)
        self.assertIn('hero.addEventListener("focusin"', js)
        self.assertIn("slide.src = slide.dataset.src", js)
        self.assertIn("document.addEventListener(\"visibilitychange\", scheduleBoth)", js)
        self.assertIn('reducedMotion.addEventListener("change", scheduleBoth)', js)
        self.assertIn('messageContent.classList.add("is-fading")', js)
        self.assertIn('messageContent.classList.remove("is-fading")', js)
        self.assertIn('.trax-home__message-measure {\n    visibility: hidden;', css)
        self.assertIn('grid-area: 1 / 1', css)
        self.assertIn('padding: calc(var(--trax-space-12) + 24px) 0 calc(var(--trax-space-16) + 24px)', css)
        self.assertIn('padding: calc(var(--trax-space-16) + 40px) 0 calc(var(--trax-space-20) + 40px)', css)
        self.assertIn('.trax-home__message-content {\n        transition: none;', css)
        self.assertIn("left: 0.25rem", css)
        self.assertIn("right: 0.25rem", css)
        self.assertIn("width: 2.75rem", css)
        self.assertIn("height: 2.75rem", css)
        self.assertIn("padding-inline: 2.75rem", css)
        self.assertIn("overflow: hidden", css)
        self.assertNotRegex(self.html + css + js, r"https?://|//[^/]\\S+")


if __name__ == "__main__":
    unittest.main()
