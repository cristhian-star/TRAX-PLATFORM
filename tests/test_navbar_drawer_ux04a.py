"""Server/render contracts. Interaction coverage is in tests/js/navbar_drawer.test.js.

Browser layout, modal inertness and native details require the visual matrix too.
"""
import os
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"
from flask import render_template
from app import create_app, db
from app.config.config import TestingConfig

ROOT = Path(__file__).resolve().parents[1]


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class NavbarDrawerUX04ATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def render(self, role=None, path="/"):
        with self.app.test_request_context(path):
            from flask import session
            if role:
                session.update(user_id=1, user_name="Nombre de prueba", user_role=role)
            # Notification context uses isolated SQLite; real route/role HTTP
            # coverage also lives in the navbar/identity regression suites.
            return render_template("base.html", navbar_notifications=[], navbar_unread_notifications=0)

    def test_single_navigation_outside_closed_dialog_is_available_without_js(self):
        html = self.render()
        self.assertEqual(html.count('id="primary-navigation"'), 1)
        self.assertLess(html.index('id="primary-navigation"'), html.index('<dialog'))
        self.assertNotIn('hidden', html.split('<nav id="primary-navigation"', 1)[1].split('>', 1)[0])
        self.assertIn('<details class="nav-dropdown">', html)

    def test_dialog_and_trigger_have_resolved_accessible_names_and_controls(self):
        tags = Tags(self.render()).tags
        ids = [a['id'] for _, a in tags if 'id' in a]
        self.assertEqual(len(ids), len(set(ids)))
        button = next(a for t, a in tags if t == 'button' and a.get('class') == 'menu-toggle')
        self.assertEqual(button['aria-controls'], 'navigation-drawer')
        self.assertEqual(button['aria-expanded'], 'false')
        self.assertEqual(button['aria-label'], 'Abrir menú')
        self.assertIn('hidden', button)
        dialog = next(a for t, a in tags if t == 'dialog')
        self.assertIn(dialog['aria-labelledby'], ids)
        self.assertNotIn('open', dialog)
        close = next(a for t, a in tags if t == 'button' and a.get('class') == 'nav-drawer__close')
        self.assertEqual(close['type'], 'button')
        self.assertEqual(close['aria-label'], 'Cerrar menú')

    def test_public_order_and_role_actions_preserved(self):
        for role in (None, 'CLIENTE', 'PROFESIONAL'):
            with self.subTest(role=role):
                html = self.render(role)
                nav = html.split('<nav id="primary-navigation"', 1)[1].split('</nav>', 1)[0]
                labels = ['Inicio', 'Explorar rubros', 'Precios de mercado', 'Operaciones', 'Ecosistema', 'Planes']
                positions = [nav.index(label) for label in labels]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn('Mi panel', nav)
                self.assertEqual('Panel profesional' in html, role == 'PROFESIONAL')
                self.assertEqual('action="/logout"' in html, role is not None)
                self.assertEqual('class="visitor-start"' in html, role is None)
                self.assertIn('data-theme-switch', html)

    def test_active_route_is_not_lost(self):
        html = self.render(path='/mercados')
        self.assertIn('href="/mercados" aria-current="page"', html)

    def test_assets_are_local_and_legacy_drawer_listener_removed(self):
        html = self.render()
        tags = Tags(html).tags
        for tag, attrs in tags:
            if tag in ('script', 'link', 'img'):
                url = attrs.get('src', attrs.get('href', ''))
                self.assertFalse(url.startswith(('https:', 'http:', '//')))
        self.assertEqual(html.count('js/navbar-drawer.js'), 1)
        self.assertNotIn('menu-open', (ROOT / 'app/static/main.js').read_text(encoding='utf-8'))
        self.assertIn('mandobra-wordmark-light.png', html)
        self.assertIn('mandobra-wordmark-dark.png', html)

    def test_css_retains_fallback_reduced_motion_and_touch_targets(self):
        css = (ROOT / 'app/static/css/navbar-drawer.css').read_text(encoding='utf-8')
        self.assertIn('height: 100dvh', css)
        self.assertIn('overflow-y: auto', css)
        self.assertIn('@media (prefers-reduced-motion: reduce)', css)
        self.assertIn(':not([data-nav-ready])', css)
        self.assertIn(':focus-visible', css)
        self.assertNotIn('!important', css)
        self.assertNotRegex(css, r'@media\s*\([^)]*(?:min|max)-width')

    def test_drawer_touch_rule_wins_loaded_cascade_for_all_roles(self):
        """Structural cascade guard, not a simulated layout measurement.

        Native browser measurements at 320px in both themes complement this
        test. The ID-scoped minimum beats class/type rules at every viewport;
        later ID sizing, inline sizing and important sizing fail this guard.
        """
        selector = '#navigation-drawer :is(a[href], button, summary)'
        sizing = {'min-height', 'min-width', 'max-height', 'max-width',
                  'height', 'width', 'all'}
        for role in (None, 'CLIENTE', 'PROFESIONAL'):
            with self.subTest(role=role):
                html = self.render(role)
                tags = Tags(html).tags
                styles = [a['href'] for t, a in tags
                          if t == 'link' and a.get('rel') == 'stylesheet']
                self.assertEqual(styles[-1], '/static/css/navbar-drawer.css')
                self.assertLess(styles.index('/static/css/visitor-navbar-v1.css'),
                                styles.index('/static/css/navbar-drawer.css'))
                rules = []
                for url in styles:
                    css = (ROOT / 'app' / url.lstrip('/')).read_text(encoding='utf-8')
                    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
                    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
                        declarations = dict(re.findall(r'([\w-]+)\s*:\s*([^;]+)', match[2]))
                        rules.append((match[1].strip(),
                                      {k: v.strip() for k, v in declarations.items()}))
                target = [(i, d) for i, (s, d) in enumerate(rules) if s == selector]
                self.assertEqual(len(target), 1)
                index, declarations = target[0]
                self.assertEqual(declarations['min-height'], '44px')
                self.assertEqual(declarations['min-width'], '44px')
                self.assertEqual(declarations['box-sizing'], 'border-box')
                self.assertEqual(declarations['flex-shrink'], '0')
                for i, (rule, values) in enumerate(rules):
                    sized = sizing.intersection(values)
                    for property_name in sized:
                        self.assertNotIn('!important', values[property_name], rule)
                    # Any competing ID sizing needs explicit review, including
                    # theme/viewport rules. Class-only selectors cannot beat ID.
                    if sized and '#' in rule and i != index:
                        self.fail('Review competing ID sizing rule: ' + rule)
                self.assertIn('id="navigation-drawer" class="nav-drawer"', html)
                nav = html.split('<nav id="primary-navigation"', 1)[1].split('</nav>', 1)[0]
                for href in ('/', '/explorar', '/mercados', '/planes'):
                    self.assertIn('href="' + href + '"', nav)
                for tag, attrs in tags:
                    if tag in ('a', 'button', 'summary'):
                        self.assertNotRegex(attrs.get('style', ''),
                                            r'(?:height|width|all)\s*:')


if __name__ == '__main__':
    unittest.main()
