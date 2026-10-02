"""E2: real Flask/CSRF with disposable in-memory SQLite only."""
import os
import re
import unittest
from html.parser import HTMLParser
from werkzeug.datastructures import MultiDict
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.models.emergency_request import EmergencyRequest
from app.models.activity_notification import ActivityNotification


class EmergencyEntryTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:",
                                    "SECRET_KEY": "isolated-e2-test-only"}, clear=True):
            self.app = create_app(TestingConfig)
        self.app.config.update(WTF_CSRF_ENABLED=True, RATELIMIT_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.assertEqual(str(db.engine.url), "sqlite:///:memory:")
            db.create_all()
            db.session.add_all([
                User(id=1, nombre="Cliente", email="client@test.invalid", password="unused", rol="CLIENTE"),
                User(id=2, nombre="Inactivo", email="inactive@test.invalid", password="unused", estado="SUSPENDIDO"),
                User(id=3, nombre="Profesional", email="pro@test.invalid", password="unused", rol="PROFESIONAL"),
            ])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def post(self, **overrides):
        html = self.client.get('/emergencias/nueva').get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', html)[1]
        data = dict(categoria="electricidad", zona="Villa Lugano", descripcion="Corte de luz",
                    csrf_token=token, modalidad="manual")
        data.update(overrides)
        return self.client.post('/emergencias/nueva', data=data)

    def counts(self):
        with self.app.app_context():
            return EmergencyRequest.query.count(), ActivityNotification.query.count()

    def login(self, user_id, role="CLIENTE"):
        with self.client.session_transaction() as session:
            session.update(user_id=user_id, user_role=role)

    def test_public_render_content_and_accessibility(self):
        r = self.client.get('/emergencias/nueva')
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        main = html.split('<main class="emergency-e2">')[1].split('</main>')[0]
        for text in ('Encontrá ayuda técnica para una urgencia', 'Primero, protegé a las personas',
                     'Bomberos, Defensa Civil', '07:00–19:00', '19:00–07:00',
                     'Mandobra nunca asigna', 'condiciones climáticas',
                     'Esta verificación reforzada todavía no está disponible',
                     'aria-describedby=', '<fieldset', '<legend>Rubro de la urgencia</legend>', 'readonly'):
            self.assertIn(text, main)
        self.assertEqual(re.findall(r'name="categoria" value="([^"]+)"', main),
                         ['electricidad', 'plomeria', 'Cerrajería', 'Auxilio vehicular'])
        for text in ('Refrigeración', 'Albañilería', 'Prioridad PRO', 'latitude', 'longitude', 'geolocation'):
            self.assertNotIn(text, main)
        self.assertIn('disabled aria-describedby="broadcast-help"', main)
        self.assertEqual(main.count('<form '), 1)
        self.assertIn('name="modalidad" value="manual"', main)
        self.assertIn('Indicá qué necesitás y dónde.', main)
        self.assertIn('Turnos previstos de 12 horas', main)
        self.assertNotIn('profesionales verificados que estén de guardia', main)
        self.assertNotIn('Mostramos profesionales de guardia', main)
        self.assertIn('trax-theme', html)
        self.assertIn('storedTheme === "dark"', html)
        self.assertIn('theme-light', html)

    def test_anonymous_manual_contract_no_persistence(self):
        r = self.post(categoria="Electricidad")
        self.assertEqual(r.status_code, 302)
        target = urlsplit(r.location)
        self.assertEqual(target.path, '/emergencias/directorio')
        self.assertEqual(parse_qs(target.query), dict(categoria=['Electricidad'], zona=['Villa Lugano'], consulta_anonima=['1']))
        self.assertEqual(self.counts(), (0, 0))

    def test_active_client_preserves_real_request_and_notification(self):
        self.login(1)
        r = self.post()
        self.assertEqual(r.status_code, 302)
        self.assertIn('solicitud=', r.location)
        self.assertEqual(self.counts(), (1, 1))

    def test_inactive_user_can_search_but_cannot_create(self):
        self.login(2)
        r = self.post()
        self.assertEqual(r.status_code, 302)
        self.assertIn('consulta_anonima=1', r.location)
        self.assertEqual(self.counts(), (0, 0))

    def test_unauthorized_roles_rejected_before_processing(self):
        for role in ('PROFESIONAL', 'ADMIN', 'ADMINISTRADOR', 'DESCONOCIDO', ''):
            with self.subTest(role=role):
                with self.app.app_context():
                    db.session.get(User, 3).rol = role
                    db.session.commit()
                self.login(3, 'CLIENTE')  # Session role must not override the stored role.
                html = self.client.get('/emergencias/nueva').get_data(as_text=True)
                token = re.search(r'name="csrf_token" value="([^"]+)"', html)[1]
                with patch('app.routes.operation_routes.entry_context') as context, \
                     patch('app.routes.operation_routes.create_emergency_request') as create, \
                     patch('app.routes.operation_routes.notify_emergency_created') as notify:
                    r = self.client.post('/emergencias/nueva', data=dict(
                        csrf_token=token, modalidad='manual', categoria='electricidad',
                        zona='Palermo', descripcion='Prueba'))
                    self.assertEqual(r.status_code, 403)
                    self.assertIsNone(r.location)
                    context.assert_not_called()
                    create.assert_not_called()
                    notify.assert_not_called()
                self.assertEqual(self.counts(), (0, 0))

    def test_adversarial_mode_collections_fail_closed(self):
        cases = [[], [''], ['difundir'], ['otro'], ['manual', 'manual'],
                 ['difundir', 'difundir'], ['manual', 'difundir'], ['difundir', 'manual'],
                 ['manual', 'manual', 'manual'], ['manual', '']]
        self.login(1)
        for modes in cases:
            with self.subTest(modes=modes):
                html = self.client.get('/emergencias/nueva').get_data(as_text=True)
                token = re.search(r'name="csrf_token" value="([^"]+)"', html)[1]
                data = MultiDict([('csrf_token', token), ('categoria', 'electricidad'),
                                  ('zona', 'Palermo'), ('descripcion', 'Prueba')]
                                 + [('modalidad', mode) for mode in modes])
                with patch('app.routes.operation_routes.entry_context') as context, \
                     patch('app.routes.operation_routes.create_emergency_request') as create, \
                     patch('app.routes.operation_routes.notify_emergency_created') as notify:
                    r = self.client.post('/emergencias/nueva', data=data)
                    self.assertEqual(r.status_code, 400)
                    self.assertIsNone(r.location)
                    context.assert_not_called()
                    create.assert_not_called()
                    notify.assert_not_called()
                self.assertEqual(self.counts(), (0, 0))

    def test_disabled_broadcast_rejected_without_side_effects(self):
        self.login(1)
        r = self.post(modalidad="difundir")
        self.assertEqual(r.status_code, 400)
        self.assertIsNone(r.location)
        self.assertEqual(self.counts(), (0, 0))

    def test_field_errors_preserve_values_and_escape(self):
        r = self.post(categoria="Refrigeración", zona="", descripcion='<script>alert(1)</script>')
        html = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 400)
        self.assertIn('id="category-error"', html)
        self.assertIn('id="zone-error"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertEqual(self.counts(), (0, 0))

    def test_server_limits_and_empty_description(self):
        for values in [dict(descripcion=''), dict(descripcion='a' * 601), dict(zona='a' * 121)]:
            with self.subTest(values=values):
                self.assertEqual(self.post(**values).status_code, 400)
        self.assertEqual(self.post(descripcion='a' * 600, zona='b' * 120).status_code, 302)

    def test_allowed_categories_and_legacy_aliases(self):
        for category in ('electricidad', 'plomeria', 'Plomería', 'Cerrajería', 'Auxilio vehicular'):
            with self.subTest(category=category):
                self.assertEqual(self.post(categoria=category).status_code, 302)

    def test_csrf_missing_and_invalid_rejected(self):
        for token in ('', 'invalid'):
            with self.subTest(token=token):
                self.assertEqual(self.post(csrf_token=token).status_code, 400)
        self.assertEqual(self.counts(), (0, 0))

    def test_no_coordinates_or_contextual_province_forwarded(self):
        r = self.post(latitude='-34', longitude='-58', provincia='Fake')
        self.assertEqual(r.status_code, 302)
        for key in ('latitude', 'longitude', 'provincia'):
            self.assertNotIn(key, parse_qs(urlsplit(r.location).query))

    def test_prefill_and_resource(self):
        html = self.client.get('/emergencias/nueva?categoria=Plomer%C3%ADa&zona=Palermo').get_data(as_text=True)
        self.assertIn('value="plomeria" required checked', html)
        self.assertIn('value="Palermo"', html)
        with self.client.get('/static/css/emergency-entry-v2.css') as response:
            self.assertEqual(response.status_code, 200)

    def test_unified_form_modes_and_decorative_icons(self):
        class FormParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.forms = []
                self.current = None
                self.icons = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'form':
                    self.current = {'attrs': attrs, 'inputs': []}
                    self.forms.append(self.current)
                elif tag == 'input' and self.current is not None:
                    self.current['inputs'].append(attrs)
                elif tag == 'svg' and 'data-icon' in attrs:
                    self.icons.append(attrs)
            def handle_endtag(self, tag):
                if tag == 'form':
                    self.current = None
        html = self.client.get('/emergencias/nueva').get_data(as_text=True)
        parser = FormParser()
        parser.feed(html)
        forms = [f for f in parser.forms if f['attrs'].get('aria-labelledby') == 'emergency-form-title']
        self.assertEqual(len(forms), 1)
        self.assertEqual(html.count('id="emergency-form-title"'), 1)
        modes = {a['value']: a for a in forms[0]['inputs'] if a.get('name') == 'modalidad'}
        self.assertEqual(set(modes), {'manual', 'difundir'})
        self.assertEqual(modes['manual']['type'], 'radio')
        self.assertIn('checked', modes['manual'])
        self.assertNotIn('disabled', modes['manual'])
        self.assertIn('disabled', modes['difundir'])
        self.assertNotIn('checked', modes['difundir'])
        self.assertEqual(modes['difundir']['aria-describedby'], 'broadcast-help')
        self.assertNotIn('Antecedentes verificados', html)
        self.assertIn('Próximamente', html)
        self.assertIn('Esta lista es orientativa', html)
        names = {a['data-icon'] for a in parser.icons}
        self.assertTrue({'broadcast', 'person-search', 'bolt', 'tap', 'lock-key', 'wheel',
                         'clock', 'rain', 'check', 'shield-check', 'shield-alert',
                         'pin', 'document', 'arrow', 'info', 'list'} <= names)
        for a in parser.icons:
            self.assertEqual(a.get('aria-hidden'), 'true')
            self.assertEqual(a.get('focusable'), 'false')


if __name__ == '__main__':
    unittest.main()
