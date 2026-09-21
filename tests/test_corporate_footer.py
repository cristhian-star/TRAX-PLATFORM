import os
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.config.config import TestingConfig


ROOT = Path(__file__).resolve().parents[1]


class CorporateFooterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
        cls.home = cls.client.get('/').get_data(as_text=True)
        cls.footer = cls.home.split('<footer class="footer"', 1)[1].split('</footer>', 1)[0]

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_identity_columns_and_copyright(self):
        self.assertEqual(self.home.count('<footer class="footer"'), 1)
        self.assertIn('Conectamos necesidades con profesionales y oportunidades técnicas.', self.footer)
        self.assertIn('Capital Federal y AMBA', self.footer)
        self.assertNotIn('Marketplace premium', self.footer)
        self.assertEqual(re.findall(r'<h2 id="footer-[^"]+">([^<]+)</h2>', self.footer),
                         ['Explorar', 'Para profesionales', 'Ayuda', 'Legal'])
        for label in ('Buscar profesionales', 'Pedir presupuestos', 'Emergencias',
                      'Oficios destacados', 'Crear perfil profesional', 'Ver oportunidades',
                      'MANDOBRA PRO', 'Herramientas para tu trabajo', 'Cómo funciona',
                      'Preguntas frecuentes', 'Seguridad y confianza', 'Contacto',
                      'Términos y condiciones', 'Política de privacidad', 'Política de cookies',
                      'Pagos, cancelaciones y reembolsos', 'Normas de la comunidad'):
            self.assertIn(label, self.footer)
        self.assertIn('© 2026 MANDOBRA. Todos los derechos reservados.', self.footer)
        self.assertIn('Argentina · Capital Federal y AMBA', self.footer)

    def test_real_links_and_anchors_reach_existing_pages(self):
        links = re.findall(r'<a href="([^"]+)">([^<]+)</a>', self.footer)
        self.assertEqual(links, [
            ('/buscar', 'Buscar profesionales'),
            ('/presupuestos/nuevo', 'Pedir presupuestos'),
            ('/emergencias/nueva', 'Emergencias'),
            ('/#featured-title', 'Oficios destacados'),
            ('/register', 'Crear perfil profesional'),
            ('/propuestas', 'Ver oportunidades'),
            ('/planes', 'MANDOBRA PRO'),
            ('/#faq-title', 'Preguntas frecuentes'),
            ('/#trust-title', 'Seguridad y confianza'),
        ])
        for href, _ in links:
            with self.subTest(href=href):
                split = urlsplit(href)
                self.assertEqual(self.client.get(split.path).status_code, 200)
                if split.fragment:
                    self.assertIn(f'id="{split.fragment}"', self.home)

    def test_future_items_and_social_icons_are_not_links_or_controls(self):
        self.assertNotIn('href="#"', self.footer)
        for name in ('Herramientas para tu trabajo', 'Cómo funciona', 'Contacto',
                     'Términos y condiciones', 'Política de privacidad', 'Política de cookies',
                     'Pagos, cancelaciones y reembolsos', 'Normas de la comunidad'):
            self.assertIn(f'class="footer__future">{name}</li>', self.footer)
        self.assertEqual(re.findall(r'data-social="([^"]+)"', self.footer),
                         ['instagram', 'facebook', 'linkedin'])
        self.assertEqual(self.footer.count('<svg viewBox="0 0 24 24" focusable="false">'), 3)
        self.assertIn('Redes oficiales próximamente', self.footer)
        self.assertEqual(self.footer.count('class="footer__social-icon" aria-hidden="true"'), 3)
        self.assertNotRegex(self.footer, r'https?://|<script|<iframe|<button')

    def test_global_footer_and_responsive_focus_contrast(self):
        for route in ('/login', '/register', '/planes'):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_data(as_text=True).count('<footer class="footer"'), 1)
        css = (ROOT / 'app/static/css/styles.css').read_text(encoding='utf-8')
        self.assertIn('.footer__column a:focus-visible {', css)
        self.assertIn('outline: 2px solid #8eeaf3', css)
        self.assertIn('background: var(--trax-steel-950)', css)
        self.assertIn('color: #f1f5f9', css)
        self.assertIn('grid-template-columns: minmax(0, 1.4fr) repeat(4, minmax(0, 1fr))', css)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr))', css)
        self.assertIn('grid-template-columns: minmax(0, 1fr)', css)
        self.assertIn('overflow-wrap: anywhere', css)

    def test_logged_layout_does_not_link_to_visitor_only_anchors(self):
        with self.client.session_transaction() as session:
            session['user_id'] = 999999
            session['user_role'] = 'CLIENTE'
            session['user_name'] = 'Cliente de prueba'
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        footer = response.get_data(as_text=True).split('<footer class="footer"', 1)[1].split('</footer>', 1)[0]
        for fragment in ('#featured-title', '#faq-title', '#trust-title'):
            self.assertNotIn(fragment, footer)
        for name in ('Oficios destacados', 'Preguntas frecuentes', 'Seguridad y confianza'):
            self.assertIn(f'class="footer__future">{name}</li>', footer)


if __name__ == '__main__':
    unittest.main()
