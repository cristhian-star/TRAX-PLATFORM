"""Canonical URLs, public terminology and form order, isolated SQLite fixtures."""
import re
import unittest
from html.parser import HTMLParser
from flask import url_for
from werkzeug.datastructures import MultiDict
from tests import test_emergency_entry as fixtures
from app import db
from app.models.activity_notification import ActivityNotification
from app.models.user import User


class PublicContent(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignored = 0
        self.text = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style', 'template'):
            self.ignored += 1
        if not self.ignored:
            self.ids.append(attrs.get('id', ''))
            self.text.extend(attrs.get(name, '') for name in ('aria-label', 'alt', 'title', 'placeholder'))

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template'):
            self.ignored -= 1

    def handle_data(self, text):
        if not self.ignored:
            self.text.append(text)


class UrgenciasE31Test(unittest.TestCase):
    setUp = fixtures.EmergencyEntryTest.setUp
    tearDown = fixtures.EmergencyEntryTest.tearDown
    login = fixtures.EmergencyEntryTest.login
    counts = fixtures.EmergencyEntryTest.counts

    def data(self, modes=('manual',)):
        html = self.client.get('/urgencias/nueva').get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', html)[1]
        return MultiDict([('csrf_token', token), ('categoria', 'electricidad'),
                          ('zona', 'La Plata'), ('descripcion', 'Consulta de prueba')]
                         + [('modalidad', mode) for mode in modes])

    def legacy_post(self, data, query=''):
        # Werkzeug's test redirect reuses a stream already consumed by Flask-WTF.
        # Replay the same MultiDict explicitly, as a browser does for HTTP 308.
        redirect = self.client.post('/emergencias/nueva' + query, data=data)
        self.assertEqual(redirect.status_code, 308)
        self.assertEqual(redirect.location, '/urgencias/nueva' + query)
        self.assertEqual(self.counts(), (0, 0))
        response = self.client.post(redirect.location, data=data)
        self.assertEqual(response.request.method, 'POST')
        return response

    def test_canonical_url_generation_and_legacy_get_queries(self):
        with self.app.test_request_context():
            self.assertEqual(url_for('operations.nueva_emergencia'), '/urgencias/nueva')
            self.assertEqual(url_for('operations.directorio_emergencias'), '/urgencias/directorio')
        query = '?categoria=Plomer%C3%ADa&zona=La+Plata&zona=Otra'
        for suffix in ('nueva', 'directorio'):
            response = self.client.get('/emergencias/' + suffix + query)
            self.assertEqual(response.status_code, 308)
            self.assertEqual(response.location, '/urgencias/' + suffix + query)
            self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(self.counts(), (0, 0))

    def test_legacy_post_preserves_body_csrf_and_persists_once(self):
        self.login(1)
        response = self.legacy_post(self.data(), '?origen=legacy')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith('/urgencias/directorio?'))
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(self.counts(), (1, 1))
        with self.app.app_context():
            notification = ActivityNotification.query.one()
            self.assertEqual(notification.tipo, 'EMERGENCIA_PUBLICADA')
            self.assertEqual(notification.categoria, 'EMERGENCIAS')
            self.assertEqual(notification.titulo, 'Publicaste una solicitud urgente')
            self.assertEqual(notification.url_destino, '/urgencias/directorio')

    def test_legacy_invalid_modes_never_write(self):
        self.login(1)
        for modes in ([], [''], ['difundir'], ['otro'], ['manual', 'manual'],
                      ['difundir', 'difundir'], ['manual', 'difundir'], ['difundir', 'manual'],
                      ['manual', 'manual', 'manual']):
            with self.subTest(modes=modes):
                response = self.legacy_post(self.data(modes))
                self.assertEqual(response.status_code, 400)
                self.assertIsNone(response.location)
                self.assertEqual(self.counts(), (0, 0))

    def test_legacy_roles_and_csrf_remain_enforced(self):
        for role in ('PROFESIONAL', 'ADMIN', 'ADMINISTRADOR', 'OTRO', ''):
            with self.subTest(role=role):
                with self.app.app_context():
                    db.session.get(User, 3).rol = role
                    db.session.commit()
                self.login(3, 'CLIENTE')
                response = self.legacy_post(self.data())
                self.assertEqual(response.status_code, 403)
                self.assertEqual(self.counts(), (0, 0))
        for path in ('/emergencias/nueva', '/urgencias/nueva'):
            self.assertEqual(self.client.post(path, data={'modalidad': 'manual'}).status_code, 400)

    def test_rendered_form_order(self):
        html = self.client.get('/urgencias/nueva').get_data(as_text=True)
        parser = PublicContent()
        parser.feed(html)
        ordered = ['category-1', 'emergency-province', 'emergency-zone',
                   'emergency-description', 'emergency-description-count', 'mode-broadcast',
                   'mode-manual', 'broadcast-help', 'mode-help']
        indexes = [parser.ids.index(key) for key in ordered]
        self.assertEqual(indexes, sorted(indexes))
        form = html.split('id="emergency-form"')[1].split('</form>')[0]
        self.assertLess(form.index('id="mode-help"'), form.index('La búsqueda es manual por zona'))
        self.assertLess(form.index('La búsqueda es manual por zona'), form.index('type="submit"'))

    def test_public_pages_use_urgencias_and_canonical_home_link(self):
        for actor, role, paths in (
            (None, None, ('/', '/urgencias/nueva', '/urgencias/directorio', '/planes')),
            (1, 'CLIENTE', ('/', '/cliente/dashboard', '/notificaciones')),
            (3, 'PROFESIONAL', ('/', '/profesional/dashboard', '/profesional/perfil/completar')),
        ):
            if actor:
                self.login(actor, role)
            for path in paths:
                with self.subTest(actor=actor, path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    parser = PublicContent()
                    parser.feed(html)
                    self.assertNotRegex(' '.join(parser.text).lower(), r'emergencias?')
                    self.assertIn('/urgencias/nueva', html)

    def test_legacy_notification_presentation_does_not_rewrite_history(self):
        with self.app.app_context():
            note = ActivityNotification(user_id=1, tipo='EMERGENCIA_PUBLICADA', categoria='EMERGENCIAS',
                titulo='Publicaste una emergencia', mensaje='Tu emergencia de Electricidad en La Plata quedo registrada.',
                url_destino='/emergencias/directorio?solicitud=7')
            db.session.add(note)
            db.session.commit()
        self.login(1)
        for path in ('/notificaciones', '/cliente/dashboard', '/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            parser = PublicContent()
            parser.feed(response.get_data(as_text=True))
            self.assertNotRegex(' '.join(parser.text).lower(), r'emergencias?')
            self.assertIn('/urgencias/directorio?solicitud=7', response.get_data(as_text=True))
        with self.app.app_context():
            note = ActivityNotification.query.one()
            self.assertEqual(note.titulo, 'Publicaste una emergencia')
            self.assertTrue(note.mensaje.startswith('Tu emergencia de '))
            self.assertEqual(note.url_destino, '/emergencias/directorio?solicitud=7')
            self.assertFalse(db.session.dirty)


if __name__ == '__main__':
    unittest.main()
