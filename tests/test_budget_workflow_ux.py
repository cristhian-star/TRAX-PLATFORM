"""Presupuestos navigation and real POST workflow on disposable SQLite."""
import unittest
from app import db
from app.models.budget_request import BudgetRequest
from app.models.budget_offer import BudgetOffer
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from tests import test_sprint7_budget_to_contract as fixtures


class BudgetWorkflowUXTest(unittest.TestCase):
    tearDown = fixtures.Sprint7BudgetToContractTest.tearDown

    def login(self, user):
        self.app.config['RATELIMIT_ENABLED'] = False
        with self.client.session_transaction() as s:
            s.clear()
            s['user_id'] = user

    def setUp(self):
        fixtures.Sprint7BudgetToContractTest.setUp(self)
        self.client = self.app.test_client()
        self.app.config['RATELIMIT_ENABLED'] = False
        with self.app.app_context():
            self.assertEqual(db.engine.url.drivername, 'sqlite')
            self.assertEqual(db.engine.url.database, ':memory:')

    def test_detail_keeps_owner_and_non_actionable_professional_states(self):
        from unittest.mock import patch
        path = f'/presupuestos/{self.budget_request_id}'
        self.login(self.client_id)
        self.assertIn('Confirmar adjudicación', self.client.get(path).text)
        self.login(self.professional_user_id)
        own = self.client.get(path).text
        self.assertIn('Tu presupuesto', own)
        self.assertNotIn('name="monto_desde"', own)
        with self.app.app_context():
            BudgetOffer.query.delete()
            db.session.commit()
        with patch('app.services.operation_view_service.get_offer_allowance', return_value={
                'is_pro': False, 'used': 9, 'limit': 9, 'remaining': 0}):
            limited = self.client.get(path).text
            self.assertIn('Alcanzaste el limite mensual', limited)
            self.assertNotIn('name="monto_desde"', limited)
        with self.app.app_context():
            db.session.get(BudgetRequest, self.budget_request_id).estado = 'CANCELADA'
            db.session.commit()
        closed = self.client.get(path).text
        self.assertIn('Esta solicitud ya no recibe presupuestos', closed)
        self.assertNotIn('name="monto_desde"', closed)

    def test_compact_design_uses_real_data_and_service_limit(self):
        from unittest.mock import patch
        self.login(self.professional_user_id)
        with self.app.app_context():
            item = db.session.get(BudgetRequest, self.budget_request_id)
            item.titulo = '<script>alert(1)</script>' + ' Título largo' * 20
            db.session.commit()
        with patch('app.routes.operation_routes.MAX_OFFERS_PER_REQUEST', 9):
            html = self.client.get('/profesional/presupuestos').text.split('<main class="budget-page')[1]
        self.assertIn('1 de 9 presupuestos recibidos', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        for removed in ('Marketplace profesional', 'Filtrar oportunidades', 'budget-counter', 'budget-estimate-note'):
            self.assertNotIn(removed, html)
        for expected in ('Solicitudes disponibles', 'Presupuestos enviados', 'Ver solicitud', 'Zona: CABA', '<time datetime='):
            self.assertIn(expected, html)
        self.assertIn('estimaciones preliminares', self.client.get(f'/presupuestos/{self.budget_request_id}').text)

    def test_compact_tabs_and_empty_states(self):
        self.login(self.professional_user_id)
        html = self.client.get('/presupuestos/mis-enviados').text
        self.assertIn('href="/presupuestos/mis-enviados" aria-current="page"', html)
        self.assertIn('href="/profesional/presupuestos"', html)
        with self.app.app_context():
            BudgetOffer.query.delete()
            db.session.get(BudgetRequest, self.budget_request_id).estado = 'CANCELADA'
            db.session.commit()
        self.assertIn('No hay solicitudes disponibles', self.client.get('/profesional/presupuestos').text)
        self.assertIn('Todavia no enviaste presupuestos', self.client.get('/presupuestos/mis-enviados').text)

    def test_publication_age_is_derived_from_utc_timestamp(self):
        from datetime import datetime, timedelta
        from app.services.operation_view_service import budget_publication_age
        now = datetime(2026, 10, 23, 15)
        for seconds, expected in ((0, 'Recién publicada'), (120, 'Hace 2 min'), (7200, 'Hace 2 h'), (86400, 'Hace 1 día'), (172800, 'Hace 2 días'), (-60, 'Recién publicada')):
            self.assertEqual(budget_publication_age(now-timedelta(seconds=seconds), now), expected)

    def test_professional_shell_list_detail_followup_and_pagination(self):
        self.login(self.professional_user_id)
        for path in ['/profesional/presupuestos','/presupuestos','/presupuestos/mis-enviados',f'/presupuestos/{self.budget_request_id}']:
            with self.subTest(path=path):
                r=self.client.get(path)
                self.assertEqual(r.status_code,200)
                self.assertIn('class="pw-header"',r.text)
                self.assertIn('href="/profesional/presupuestos" aria-current="page"',r.text)
        self.assertIn('Página 2',self.client.get('/presupuestos?page=2&per_page=1').text)
        self.assertEqual(self.client.get('/presupuestos?page=-5').status_code,200)

    def test_award_replay_keeps_one_contract_and_both_actors_can_follow(self):
        self.login(self.client_id)
        path=f'/presupuestos/{self.budget_request_id}'
        before=self.client.get(path).text
        self.assertIn('Confirmar adjudicación',before)
        self.assertNotIn('class="pw-header"',before)
        for _ in range(2):
            self.assertEqual(self.client.post(path+f'/adjudicar/{self.offer_id}').status_code,302)
        with self.app.app_context():
            self.assertEqual(ContractRequest.query.count(),1)
            contract=ContractRequest.query.one()
            cid=contract.id
            self.assertEqual(contract.estado,'CREADA')
        for user in [self.client_id,self.professional_user_id]:
            self.login(user)
            self.assertIn(f'/contratacion/{cid}',self.client.get(path).text)
            r=self.client.get(f'/contratacion/{cid}')
            self.assertEqual(r.status_code,200)
            self.assertEqual('class="pw-header"' in r.text,user==self.professional_user_id)

    def test_offer_post_duplicate_validation_and_success_are_real(self):
        with self.app.app_context():
            item=BudgetRequest(cliente_id=self.client_id,categoria='Electricidad',titulo='Solicitud sintética',descripcion='Detalle',zona='CABA',estado='PUBLICADA')
            db.session.add(item);db.session.commit();bid=item.id
        self.login(self.professional_user_id)
        path=f'/presupuestos/{bid}'
        self.assertNotIn('Presupuesto preliminar enviado correctamente.',self.client.get(path+'?enviado=1').text)
        bad=self.client.post(path+'/ofertar',data={'monto_desde':'200','monto_hasta':'100','plazo_estimado':'3 días'},follow_redirects=True)
        self.assertIn('menor o igual',bad.text)
        form={'monto_desde':'100','monto_hasta':'200','plazo_estimado':'3 días','condiciones':'<script>alert(1)</script>'}
        good=self.client.post(path+'/ofertar',data=form,follow_redirects=True)
        self.assertIn('Presupuesto preliminar enviado correctamente.',good.text)
        self.client.post(path+'/ofertar',data=form)
        with self.app.app_context():
            self.assertEqual(BudgetOffer.query.filter_by(budget_request_id=bid).count(),1)
        self.login(self.client_id)
        self.assertNotIn('<script>alert(1)</script>',self.client.get(path).text)

    def test_ownership_and_csrf_not_relaxed(self):
        path=f'/presupuestos/{self.budget_request_id}'
        self.assertEqual(self.client.get(path).status_code,302)
        self.login(self.other_id)
        self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.client.post(path+f'/adjudicar/{self.offer_id}').status_code,403)
        self.login(self.professional_user_id)
        self.assertEqual(self.client.post(path+f'/adjudicar/{self.offer_id}').status_code,403)
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post(path+'/ofertar',data={}).status_code,400)

    def test_closed_followup_and_incomplete_profile_are_honest(self):
        self.login(self.professional_user_id)
        with self.app.app_context():
            db.session.get(BudgetRequest,self.budget_request_id).estado='CANCELADA'
            db.session.commit()
        self.assertIn('Solicitud cancelada',self.client.get('/presupuestos/mis-enviados').text)
        with self.app.app_context():
            item=BudgetRequest(cliente_id=self.client_id,categoria='Electricidad',titulo='Otra',descripcion='Detalle',zona='CABA',estado='PUBLICADA')
            db.session.add(item)
            db.session.get(Professional,self.professional_id).perfil_completo=False
            db.session.commit();bid=item.id
        r=self.client.get(f'/presupuestos/{bid}')
        self.assertIn('Completá tu perfil para responder',r.text)
        self.assertNotIn('name="monto_desde"',r.text)

    def test_filters_empty_state_and_reads_do_not_write(self):
        from unittest.mock import patch
        self.login(self.professional_user_id)
        with patch.object(db.session, 'commit') as commit:
            matched = self.client.get('/presupuestos?categoria=Electricidad&zona=CABA')
            empty = self.client.get('/presupuestos?categoria=NoExiste&zona=CABA')
            self.assertIn('Tablero', matched.text)
            self.assertNotIn('Tablero', empty.text)
            self.assertIn('No hay solicitudes disponibles', empty.text)
            self.assertEqual(self.client.get('/presupuestos?page=abc').status_code, 200)
            commit.assert_not_called()

    def test_client_can_cancel_and_other_clients_cannot_see_followup(self):
        self.login(self.other_id)
        self.assertNotIn('Tablero', self.client.get('/presupuestos/mis-solicitudes').text)
        path = f'/presupuestos/{self.budget_request_id}'
        self.assertEqual(self.client.post(path + '/cancelar').status_code, 403)
        self.login(self.client_id)
        self.assertIn('Confirmar cancelación', self.client.get('/presupuestos/mis-solicitudes').text)
        self.assertEqual(self.client.post(path + '/cancelar').status_code, 302)
        self.login(self.professional_user_id)
        self.assertIn('No hay solicitudes disponibles', self.client.get('/presupuestos').text)
        self.assertIn('Solicitud cancelada', self.client.get('/presupuestos/mis-enviados').text)
        with self.app.app_context():
            self.assertEqual(ContractRequest.query.count(), 0)

    def fresh_offer_form(self):
        with self.app.app_context():
            item = BudgetRequest(cliente_id=self.client_id, categoria='Electricidad',
                titulo='Regresión P2', descripcion='Datos sintéticos', zona='CABA', estado='PUBLICADA')
            db.session.add(item)
            db.session.commit()
            bid = item.id
        self.login(self.professional_user_id)
        return f'/presupuestos/{bid}', {
            'monto_desde': '200', 'monto_hasta': '300', 'plazo_estimado': '3 días',
            'condiciones': '<script>alert("x")</script> & condiciones privadas',
            'cobra_visita': 'si', 'precio_visita': '25.50',
        }

    def test_p2_nonfinite_amounts_are_controlled_without_effects(self):
        from unittest.mock import patch
        path, form = self.fresh_offer_form()
        for field in ('monto_desde', 'monto_hasta', 'precio_visita'):
            for value in ('NaN', 'sNaN', 'Infinity', '-Infinity', 'no-es-importe'):
                with self.subTest(field=field, value=value):
                    with patch('app.routes.operation_routes.notify_budget_offer_created') as notify:
                        response = self.client.post(path + '/ofertar', data={**form, field: value})
                        self.assertEqual(response.status_code, 400)
                        self.assertNotIn('Location', response.headers)
                        self.assertIn('no es valido', response.text)
                        notify.assert_not_called()
                    with self.app.app_context():
                        self.assertEqual(BudgetOffer.query.count(), 1)  # only fixture offer
                        self.assertEqual(ContractRequest.query.count(), 0)
                        self.assertEqual(db.session.get(BudgetRequest, int(path.split('/')[-1])).estado, 'PUBLICADA')

    def test_p2_invalid_range_preserves_form(self):
        from html.parser import HTMLParser
        class FormParser(HTMLParser):
            def __init__(self):
                super().__init__(); self.values = {}; self.current = None; self.select = None
            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                if tag == 'input' and a.get('name'): self.values[a['name']] = a.get('value', '')
                if tag == 'select': self.select = a.get('name')
                if tag == 'option' and 'selected' in a: self.values[self.select] = a.get('value')
                if tag == 'textarea': self.current = a.get('name'); self.values[self.current] = ''
            def handle_data(self, data):
                if self.current: self.values[self.current] += data
            def handle_endtag(self, tag):
                if tag == 'textarea': self.current = None
        path, form = self.fresh_offer_form()
        self.app.config['WTF_CSRF_ENABLED'] = True
        initial = FormParser(); initial.feed(self.client.get(path).text)
        form['csrf_token'] = initial.values['csrf_token']
        for changes in ({'monto_hasta': '100'}, {'plazo_estimado': ''}, {'precio_visita': ''}):
            with self.subTest(changes=changes):
                submitted = {**form, **changes}
                response = self.client.post(path + '/ofertar', data=submitted)
                self.assertEqual(response.status_code, 400)
                self.assertNotIn('Location', response.headers)
                self.assertIn('class="pw-header"', response.text)
                parsed = FormParser(); parsed.feed(response.text)
                for key, value in submitted.items():
                    if key != 'csrf_token':
                        self.assertEqual(parsed.values[key], value)
                self.assertTrue(parsed.values['csrf_token'])
                form['csrf_token'] = parsed.values['csrf_token']
                self.assertNotIn('<script>alert("x")</script>', response.text)
                self.assertIn('&lt;script&gt;', response.text)
        success = self.client.post(path + '/ofertar', data=form)
        self.assertEqual(success.status_code, 302)
        self.assertTrue(success.location.endswith('?enviado=1'))
        duplicate = self.client.post(path + '/ofertar', data=form)
        self.assertEqual(duplicate.status_code, 400)
        with self.app.app_context():
            self.assertEqual(BudgetOffer.query.filter_by(budget_request_id=int(path.split('/')[-1])).count(), 1)

    def test_p2_negative_and_required_amount_rules_preserved(self):
        path, form = self.fresh_offer_form()
        for field in ('monto_desde', 'monto_hasta'):
            for value in ('', '-0.01'):
                with self.subTest(field=field, value=value):
                    response = self.client.post(path + '/ofertar', data={**form, field: value})
                    self.assertEqual(response.status_code, 400)
        response = self.client.post(path + '/ofertar', data={**form, 'monto_desde': '0.00', 'monto_hasta': '0.01', 'cobra_visita': 'no', 'precio_visita': ''})
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            offer = BudgetOffer.query.filter_by(budget_request_id=int(path.split('/')[-1])).one()
            self.assertEqual(str(offer.monto_hasta), '0.01')
            self.assertIsNone(offer.precio_visita)
