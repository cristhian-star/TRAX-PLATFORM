"""UX-04B/C: real Flask contracts, no production DB or deliberate public errors."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from flask import abort
from werkzeug.exceptions import ServiceUnavailable
from app import create_app, db
from app.config.config import DevelopmentConfig, ProductionConfig
from app.utils.error_pages import ERROR_PAGES

ROOT = Path(__file__).resolve().parents[1]


class LoadingErrorStatesTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:", "SECRET_KEY": "isolated-error-states-tests",
            "ENABLE_DEV_QA_PANEL": "true", "PYTHON_DOTENV_DISABLED": "1",
        }, clear=True):
            self.app = create_app(DevelopmentConfig)
        self.app.config.update(RATELIMIT_ENABLED=False)

        @self.app.get('/_test/error/<int:code>')
        def error(code):
            if code == 503:
                raise ServiceUnavailable(description='secret SQL password traceback', retry_after=60)
            abort(code, description='secret SQL password traceback')

        @self.app.get('/_test/unexpected')
        def unexpected():
            raise RuntimeError('secret SQL password traceback')

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_html_statuses_generic_text_actions_security_and_no_secrets(self):
        for code, (title, message) in ERROR_PAGES.items():
            with self.subTest(code=code):
                response = self.client.get(f'/_test/error/{code}', headers={'Accept': 'text/html'})
                self.assertEqual(response.status_code, code)
                html = response.get_data(as_text=True)
                self.assertIn(title, html)
                self.assertIn(message, html)
                self.assertIn('href="/"', html)
                self.assertIn('href="/explorar"', html)
                self.assertIn('alt="" aria-hidden="true"', html)
                for private in ('secret SQL', 'password', 'Traceback', 'RuntimeError'):
                    self.assertNotIn(private, html)
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
                self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
                if code == 503:
                    self.assertEqual(response.headers['Retry-After'], '60')

    def test_json_negotiation_and_testing_contract(self):
        for headers in ({'Accept': 'application/json'}, {'Content-Type': 'application/json'}):
            for code in ERROR_PAGES:
                response = self.client.get(f'/_test/error/{code}', headers=headers)
                self.assertEqual(response.status_code, code)
                self.assertEqual(set(response.json), {'error'})
        self.app.config['TESTING'] = True
        self.assertEqual(self.client.get('/missing', headers={'Accept': 'text/html'}).json,
                         {'error': 'Recurso no encontrado'})

    def test_unexpected_error_logged_once_without_payload(self):
        with self.assertLogs(self.app.logger, level='ERROR') as logs:
            response = self.client.get('/_test/unexpected')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(logs.output), 1)
        self.assertIn('Error inesperado procesando la solicitud', logs.output[0])
        self.assertNotIn('password', logs.output[0])
        self.assertNotIn('RuntimeError', response.get_data(as_text=True))

    def test_authenticated_error_does_not_query_notifications_or_database(self):
        with self.client.session_transaction() as session:
            session['user_id'] = 987
        with patch('app.services.notification_service.obtener_no_leidas', side_effect=RuntimeError('DB unavailable')), \
             patch('app.services.notification_service.obtener_notificaciones_usuario', side_effect=RuntimeError('DB unavailable')):
            response = self.client.get('/_test/error/500')
        self.assertEqual(response.status_code, 500)
        self.assertIn(ERROR_PAGES[500][0], response.get_data(as_text=True))

    def test_health_webhook_and_csrf_contracts_preserved(self):
        health = self.client.get('/healthz', headers={'Accept': 'text/html'})
        self.assertEqual(health.status_code, 503)
        self.assertEqual(health.json, {'status': 'unavailable'})
        self.assertEqual(health.headers['Cache-Control'], 'no-store')
        webhook = self.client.post('/api/webhooks/mercadopago')
        self.assertEqual(webhook.status_code, 503)
        self.assertEqual(webhook.json, {'error': 'service unavailable'})
        self.assertEqual(self.client.get('/api/missing').get_data(as_text=True), '404 - Recurso no encontrado')
        self.assertEqual(self.client.get('/api/missing', headers={'Accept': 'application/json'}).json,
                         {'error': 'Recurso no encontrado'})
        csrf = self.client.post('/dev/qa/estados')
        self.assertEqual(csrf.status_code, 400)
        self.assertEqual(csrf.get_data(as_text=True), '400 - Solicitud invalida')

    def test_http_methods_head_and_retry_after(self):
        # Disable CSRF here only to isolate the HTTPException routing contract.
        self.app.config['WTF_CSRF_ENABLED'] = False
        response = self.client.put('/_test/unexpected')
        self.assertEqual(response.status_code, 405)
        self.assertIn('GET', response.headers['Allow'])
        for code in ERROR_PAGES:
            response = self.client.head(f'/_test/error/{code}')
            self.assertEqual(response.status_code, code)
            self.assertEqual(response.data, b'')

    def test_qa_previews_no_false_error_logs_and_bounded_delay(self):
        with patch.object(self.app.logger, 'error') as log:
            for code in ERROR_PAGES:
                response = self.client.get(f'/dev/qa/estados/{code}')
                self.assertEqual(response.status_code, 200)
                self.assertIn(f'Vista previa QA · Error {code}', response.get_data(as_text=True))
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
            log.assert_not_called()
        with patch('app.routes.dev_routes.sleep') as sleep:
            self.client.get('/dev/qa/estados?demora=10')
            sleep.assert_called_once_with(10)
            sleep.reset_mock()
            self.client.get('/dev/qa/estados?demora=9999')
            self.client.head('/dev/qa/estados?demora=10')
            sleep.assert_not_called()
        self.assertEqual(self.client.get('/dev/qa/estados/401').status_code, 404)

    def test_qa_flag_environment_and_production_isolation(self):
        for flag, env in ((False, 'development'), (True, 'production')):
            self.app.config.update(ENABLE_DEV_QA_PANEL=flag, ENV_NAME=env)
            with patch('app.routes.dev_routes.sleep') as sleep:
                for path in ('/dev/qa/estados?demora=10', '/dev/qa/estados/500'):
                    self.assertEqual(self.client.get(path).status_code, 404)
                sleep.assert_not_called()
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:',
                                    'SECRET_KEY': 'production-contract-test-only', 'ENABLE_DEV_QA_PANEL': 'true'}, clear=True):
            production = create_app(ProductionConfig)
        self.assertFalse(any(rule.rule.startswith('/dev/') for rule in production.url_map.iter_rules()))

    def test_testing_qa_preview_can_render_without_changing_error_contract(self):
        self.app.config.update(TESTING=True, ENV_NAME='testing')
        self.assertEqual(self.client.get('/dev/qa/estados/500').status_code, 200)
        self.assertTrue(self.client.get('/missing').is_json)

    def test_svg_safe_local_get_head_mime_and_reduced_motion(self):
        path = ROOT / 'app/static/images/states/mandobra-repair.svg'
        svg = ET.fromstring(path.read_text(encoding='utf-8'))
        self.assertLess(path.stat().st_size, 12000)
        for element in svg.iter():
            self.assertNotIn(element.tag.split('}')[-1], ('script', 'foreignObject', 'image', 'text', 'a'))
            self.assertFalse(any(key.lower().startswith('on') or key.endswith('href') for key in element.attrib))
        self.assertIn('prefers-reduced-motion: reduce', path.read_text())
        for method in (self.client.get, self.client.head):
            response = method('/static/images/states/mandobra-repair.svg')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/svg+xml')
            response.close()

    def test_loading_markup_motion_and_global_integration(self):
        response = self.client.get('/dev/qa/estados')
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(html.count('data-page-loading hidden'), 1)
        self.assertEqual(html.count('js/page-loading.js'), 1)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('class="page-loading__shapes" aria-hidden="true"', html)
        css = (ROOT / 'app/static/css/page-loading.css').read_text()
        self.assertIn('prefers-reduced-motion: reduce', css)
        self.assertIn('visibility: hidden', css)
        self.assertIn('pointer-events: none', css)
        error_css = (ROOT / 'app/static/css/error-pages.css').read_text()
        self.assertIn(':focus-visible', error_css)
        self.assertIn('.theme-dark', error_css)

    def test_error_links_are_relative_and_static_assets_exist(self):
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.urls = []

            def handle_starttag(self, tag, attrs):
                self.urls.extend(value for key, value in attrs if key in ('href', 'src'))

        parser = Links()
        parser.feed(self.client.get('/dev/qa/estados/404').get_data(as_text=True))
        for url in parser.urls:
            self.assertTrue(url.startswith('/') and not url.startswith('//'), url)
            if url.startswith('/static/'):
                self.assertTrue((ROOT / 'app' / url.lstrip('/')).is_file(), url)
            else:
                with self.app.test_request_context():
                    self.app.url_map.bind('localhost').match(url, method='GET')


if __name__ == '__main__':
    unittest.main()
