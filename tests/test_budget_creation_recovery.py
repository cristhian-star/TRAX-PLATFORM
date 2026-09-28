"""Atomic creation and real Flask session/CSRF recovery (no JS dependency)."""
import json
from pathlib import Path
import re
import time
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash
import tests.test_budget_request_ux06a as baseline
from app import db
from app.models.activity_notification import ActivityNotification
from app.models.budget_request import BudgetRequest
from app.models.operation_command import OperationCommand
from app.models.user import User
from app.services.budget_service import create_budget_request
from app.services.budget_creation_key_service import issue_budget_key
from app.services.operation_notification_service import notify_budget_created


def hidden(html, name):
    return re.search(r'name="' + name + r'" value="([^"]+)"', html).group(1)


class BudgetCreationRecoveryTest(unittest.TestCase):
    setUp = baseline.BudgetRequestUX06ATest.setUp
    tearDown = baseline.BudgetRequestUX06ATest.tearDown
    login = baseline.BudgetRequestUX06ATest.login

    def payload(self):
        html = self.client.get('/presupuestos/nuevo').get_data(as_text=True)
        return {**self.data, **{n: hidden(html, n) for n in ('csrf_token', 'idempotency_key', 'draft_proof')}}

    def counts(self, expected):
        with self.app.app_context():
            self.assertEqual(tuple(m.query.count() for m in (BudgetRequest, ActivityNotification, OperationCommand)), expected)

    def expire(self):
        with self.client.session_transaction() as session:
            session.clear()

    def start_expired(self, **fields):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        payload = {**self.payload(), **fields}
        self.expire()
        response = self.client.post('/presupuestos/nuevo', data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/login?next=/presupuestos/nuevo')
        self.counts((0, 0, 0))
        return payload

    def auth_login(self, index=0, password='correct-password'):
        with self.app.app_context():
            db.session.get(User, self.ids[index]).password = generate_password_hash('correct-password')
            db.session.commit()
        html = self.client.get('/login?next=/presupuestos/nuevo').get_data(as_text=True)
        return self.client.post('/login?next=/presupuestos/nuevo', data={
            'csrf_token': hidden(html, 'csrf_token'), 'email': f'ux06-{index}@test.local', 'password': password})

    def test_sequential_double_post_replay_one_notification_and_rotated_next_form(self):
        self.login()
        data = self.payload()
        first = self.client.post('/presupuestos/nuevo', data=data)
        second = self.client.post('/presupuestos/nuevo', data=data)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.location, first.location)
        self.counts((1, 1, 1))
        self.assertNotEqual(self.payload()['idempotency_key'], data['idempotency_key'])

    def test_payload_conflict_and_different_keys(self):
        self.login()
        data = self.payload()
        self.client.post('/presupuestos/nuevo', data=data)
        self.assertEqual(self.client.post('/presupuestos/nuevo', data={**data, 'titulo': 'Otro trabajo'}).status_code, 409)
        self.counts((1, 1, 1))
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=self.payload()).status_code, 302)
        self.counts((2, 2, 2))

    def test_actor_bound_key_and_authorize_before_replay(self):
        self.login()
        data = self.payload()
        self.client.post('/presupuestos/nuevo', data=data)
        self.login(3)
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=data).status_code, 400)
        with self.app.app_context():
            db.session.get(User, self.ids[0]).rol = 'PROFESIONAL'
            db.session.commit()
            with self.assertRaises(PermissionError):
                create_budget_request(self.ids[0], **{k: v for k, v in data.items() if k not in ('csrf_token', 'draft_proof')})
        self.counts((1, 1, 1))

    def test_missing_malformed_and_oversized_key(self):
        self.login()
        for key in ('', 'invented', 'x' * 161):
            self.assertEqual(self.client.post('/presupuestos/nuevo', data={**self.data, 'idempotency_key': key}).status_code, 400)
        self.counts((0, 0, 0))

    def test_notification_failure_rolls_back_flushed_facts_and_session_retries(self):
        with self.app.app_context():
            key = issue_budget_key(self.ids[0])
            data = {**self.data, 'fecha_estimada': None, 'idempotency_key': key}
            def fail_after_flush(budget):
                notify_budget_created(budget)
                db.session.flush()
                raise RuntimeError('forced local notification failure')
            with patch('app.services.budget_service.notify_budget_created', side_effect=fail_after_flush):
                with self.assertRaises(RuntimeError):
                    create_budget_request(self.ids[0], **data)
            self.assertEqual(tuple(m.query.count() for m in (BudgetRequest, ActivityNotification, OperationCommand)), (0, 0, 0))
            first = create_budget_request(self.ids[0], **data)
            self.assertEqual(create_budget_request(self.ids[0], **data).id, first.id)
            self.assertEqual(OperationCommand.query.one().status, 'SUCCEEDED')
        self.counts((1, 1, 1))

    def test_full_expired_auth_login_restore_review_publish_without_javascript(self):
        original = self.start_expired()
        self.assertEqual(self.auth_login().status_code, 302)
        response = self.client.get('/presupuestos/nuevo')
        html = response.get_data(as_text=True)
        self.assertIn('Recuperamos tu borrador', html)
        self.assertIn(self.data['descripcion'], html)
        self.assertEqual(hidden(html, 'idempotency_key'), original['idempotency_key'])
        recovered = {**self.data, **{n: hidden(html, n) for n in ('csrf_token', 'idempotency_key', 'draft_proof')}}
        for _ in range(2):
            self.assertEqual(self.client.post('/presupuestos/nuevo', data=recovered).status_code, 302)
        self.counts((1, 1, 1))
        self.assertFalse(list(Path(self.drafts.name).glob('*.json')))

    def test_failed_login_retains_draft_then_correct_login(self):
        self.start_expired()
        self.assertEqual(self.auth_login(password='incorrect').status_code, 401)
        self.assertEqual(len(list(Path(self.drafts.name).glob('*.json'))), 1)
        self.assertEqual(self.auth_login().status_code, 302)
        self.assertIn('Recuperamos tu borrador', self.client.get('/presupuestos/nuevo').get_data(as_text=True))

    def test_other_user_and_browser_cannot_restore_or_select(self):
        original = self.start_expired()
        self.auth_login(3)
        html = self.client.get('/presupuestos/nuevo').get_data(as_text=True)
        self.assertNotIn('Recuperamos tu borrador', html)
        response = self.client.post('/presupuestos/borrador', data={'csrf_token': hidden(html, 'csrf_token'), 'draft_handle': original['idempotency_key'].split('.')[2]})
        self.assertEqual(response.status_code, 404)
        self.auth_login()
        self.client.delete_cookie('budget_navigation')
        self.assertNotIn('Recuperamos tu borrador', self.client.get('/presupuestos/nuevo').get_data(as_text=True))

    def test_expiry_removes_stored_draft(self):
        self.start_expired()
        self.auth_login()
        with patch('app.services.budget_draft_service.time.time', return_value=time.time() + 901):
            self.assertNotIn('Recuperamos tu borrador', self.client.get('/presupuestos/nuevo').get_data(as_text=True))
        self.assertFalse(list(Path(self.drafts.name).glob('*.json')))

    def test_unknown_fields_never_stored_and_known_fields_bounded(self):
        self.start_expired(titulo='x' * 999, descripcion='d' * 2000, rol='PROFESIONAL', cliente_id='999', estado='ADJUDICADA', password='secret', fecha_estimada='not-a-date', urgencia='OTHER')
        record = json.loads(next(Path(self.drafts.name).glob('*.json')).read_text())
        self.assertEqual(set(record['data']), {'titulo', 'categoria', 'zona', 'descripcion', 'urgencia', 'fecha_estimada'})
        self.assertEqual(len(record['data']['titulo']), 160)
        self.assertEqual(len(record['data']['descripcion']), 1200)
        self.assertEqual(record['data']['urgencia'], 'NORMAL')
        self.assertEqual(record['data']['fecha_estimada'], '')
        self.assertNotIn('csrf_token', record)
        self.assertNotIn('draft_proof', record)

    def test_invalid_csrf_proof_and_foreign_navigation_fail_closed(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        data = self.payload()
        self.expire()
        for field in ('csrf_token', 'draft_proof', 'idempotency_key'):
            self.assertEqual(self.client.post('/presupuestos/nuevo', data={**data, field: 'forged'}).status_code, 400)
        self.client.set_cookie('budget_navigation', 'a' * 64)
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=data).status_code, 400)
        self.assertFalse(list(Path(self.drafts.name).glob('*.json')))
        self.counts((0, 0, 0))

    def test_cancel_requires_csrf_and_cleans_draft(self):
        self.start_expired()
        self.auth_login()
        data = self.payload()
        self.assertEqual(self.client.post('/presupuestos/borrador', data={'action': 'cancel', 'idempotency_key': data['idempotency_key']}).status_code, 400)
        self.assertEqual(self.client.post('/presupuestos/borrador', data={**data, 'action': 'cancel'}).status_code, 302)
        self.assertFalse(list(Path(self.drafts.name).glob('*.json')))

    def test_active_session_with_invalid_csrf_cannot_use_recovery(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        data = self.payload()
        self.assertEqual(self.client.post('/presupuestos/nuevo', data={**data, 'csrf_token': 'bad'}).status_code, 400)
        self.assertFalse(list(Path(self.drafts.name).glob('*.json')))
        self.counts((0, 0, 0))

    def test_expired_recovery_proof_is_rejected(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        data = self.payload()
        self.expire()
        with patch('itsdangerous.timed.TimestampSigner.get_timestamp', return_value=int(time.time()) + 901):
            self.assertEqual(self.client.post('/presupuestos/nuevo', data=data).status_code, 400)
        self.assertFalse(list(Path(self.drafts.name).glob('*.json')))

    def test_auth_id_loss_with_valid_csrf_preserves_in_route(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        data = self.payload()
        with self.client.session_transaction() as session:
            session.pop('user_id')
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=data).status_code, 302)
        self.assertEqual(len(list(Path(self.drafts.name).glob('*.json'))), 1)
        self.counts((0, 0, 0))

    def test_multiple_tabs_keep_distinct_payload_and_key(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        first = {**self.payload(), 'titulo': 'Primera pestaña'}
        second = {**self.payload(), 'titulo': 'Segunda pestaña'}
        self.expire()
        for data in (first, second):
            self.assertEqual(self.client.post('/presupuestos/nuevo', data=data).status_code, 302)
        self.auth_login()
        html = self.client.get('/presupuestos/nuevo').get_data(as_text=True)
        self.assertIn('Elegí qué solicitud', html)
        for data in (first, second):
            response = self.client.post('/presupuestos/borrador', data={'csrf_token': hidden(html, 'csrf_token'), 'draft_handle': data['idempotency_key'].split('.')[2]})
            page = response.get_data(as_text=True)
            self.assertIn(data['titulo'], page)
            self.assertEqual(hidden(page, 'idempotency_key'), data['idempotency_key'])
