"""UX-06A: isolated SQLite route, ownership and BUDGET continuity regression."""
import os
import re
import unittest
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "ux06a-test-secret"
from app import create_app, db
from app.models.user import User
from app.models.professional import Professional
from app.models.budget_request import BudgetRequest
from app.models.budget_offer import BudgetOffer
from app.models.contract_request import ContractRequest
from app.models.contract_event import ContractEvent
from app.models.audit_log import AuditLog
from app.services.budget_service import create_budget_request, create_budget_offer, cancel_budget_request, get_offer_allowance, award_budget_offer, get_client_budget_requests, get_client_budget_requests_with_counts
from app.services.contract_service import _require_role_and_ownership, get_contract_detail_context
from app.services.contracting_core_service import create_contract_from_budget_offer
from app.services.operation_view_service import build_budget_detail_context


class BudgetRequestUX06ATest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, RATELIMIT_ENABLED=False)
        self.drafts = tempfile.TemporaryDirectory()
        self.app.config['BUDGET_DRAFT_DIRECTORY'] = self.drafts.name
        self.client = self.app.test_client()
        self.data = dict(titulo="Reparar cocina", categoria="Plomería", zona="Caballito", descripcion="Cambiar la canilla", urgencia="NORMAL", fecha_estimada="")
        with self.app.app_context():
            db.create_all()
            users = [User(nombre=role, email=f"ux06-{i}@test.local", password="hash", rol=role) for i, role in enumerate(("CLIENTE", "PROFESIONAL", "PROFESIONAL", "CLIENTE"))]
            db.session.add_all(users)
            db.session.flush()
            self.ids = [u.id for u in users]
            for u in users[1:3]:
                db.session.add(Professional(user_id=u.id, nombre=u.nombre, servicio="Plomería", zona="CABA", perfil_completo=True))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.drafts.cleanup()

    def login(self, index=0):
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = self.ids[index]
            session["user_role"] = "PROFESIONAL" if index in (1, 2) else "CLIENTE"
        if index not in (1, 2):
            html = self.client.get('/presupuestos/nuevo').get_data(as_text=True)
            self.data['idempotency_key'] = re.search(r'name="idempotency_key" value="([^"]+)"', html).group(1)

    def create(self, index=0):
        self.login(index)
        response = self.client.post("/presupuestos/nuevo", data=self.data)
        self.assertEqual(response.status_code, 302)
        return int(response.location.split("/")[-2])

    def offer(self, request_id, index=2):
        return create_budget_offer(request_id, self.ids[index], "no", None, "100", "150", "3 días", "CONDICION PRIVADA UX06")

    def test_visitor_has_safe_login_register_and_no_operational_form(self):
        html = self.client.get("/presupuestos/nuevo").get_data(as_text=True)
        self.assertIn('/login?next=/presupuestos/nuevo', html)
        self.assertIn('/register?next=/presupuestos/nuevo', html)
        self.assertNotIn('data-budget-form', html)
        self.assertNotIn('name="titulo"', html)

    def test_anonymous_post_never_creates_or_previews(self):
        response = self.client.post("/presupuestos/nuevo", data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login?next=/presupuestos/nuevo', response.location)
        self.assertNotIn(self.data['titulo'], response.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(BudgetRequest.query.count(), 0)

    def legacy_professional_request(self):
        # Inconsistent ownership left by the rejected increment or a manipulated caller.
        with self.app.app_context():
            budget = BudgetRequest(cliente_id=self.ids[1], titulo='Legacy', categoria='Plomería', zona='CABA', descripcion='Solicitud anterior al P1')
            db.session.add(budget)
            db.session.commit()
            return budget.id

    def test_client_creates_confirms_views_lists_and_cancels_own(self):
        request_id = self.create()
        confirmation = self.client.get(f"/presupuestos/{request_id}/confirmacion")
        self.assertEqual(confirmation.status_code, 200)
        self.assertIn('0 de 6', confirmation.get_data(as_text=True))
        self.assertEqual(self.client.get(f"/presupuestos/{request_id}").status_code, 200)
        self.assertEqual(self.client.get('/presupuestos/mis-solicitudes').status_code, 200)
        self.assertEqual(self.client.post(f"/presupuestos/{request_id}/cancelar").status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(BudgetRequest, request_id).estado, 'CANCELADA')

    def test_professional_get_post_and_owner_routes_rejected_even_for_legacy_owner(self):
        request_id = self.legacy_professional_request()
        with self.app.app_context():
            offer_id = self.offer(request_id).id
        self.login(1)
        for path in ('/presupuestos/nuevo', '/presupuestos/mis-solicitudes', f'/presupuestos/{request_id}/confirmacion', f'/presupuestos/{request_id}'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 403, path)
            self.assertNotIn('data-budget-form', response.get_data(as_text=True))
        for path in ('/presupuestos/nuevo', f'/presupuestos/{request_id}/cancelar', f'/presupuestos/{request_id}/adjudicar/{offer_id}'):
            self.assertEqual(self.client.post(path, data=self.data).status_code, 403, path)
        with self.app.app_context():
            self.assertEqual(BudgetRequest.query.count(), 1)
            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertEqual(db.session.get(BudgetRequest, request_id).estado, 'COTIZANDO')
            ctx = build_budget_detail_context(db.session.get(BudgetRequest, request_id), self.ids[1], {})
            self.assertFalse(ctx['is_owner'])
            self.assertEqual(ctx['offer_rows'], [])
            self.assertIsNone(ctx['budget_contract'])

    def test_professional_internal_owner_operations_rejected_without_side_effects(self):
        request_id = self.legacy_professional_request()
        with self.app.app_context():
            offer = self.offer(request_id)
            for operation in (
                lambda: create_budget_request(cliente_id=self.ids[1], **self.data),
                lambda: cancel_budget_request(request_id, self.ids[1]),
                lambda: award_budget_offer(request_id, offer.id, self.ids[1]),
                lambda: get_client_budget_requests(self.ids[1]),
                lambda: get_client_budget_requests_with_counts(self.ids[1]),
            ):
                with self.assertRaises(PermissionError):
                    operation()
            offer.estado = 'ADJUDICADO'
            db.session.commit()
            with self.assertRaises(PermissionError):
                create_contract_from_budget_offer(offer.id, actor_user_id=self.ids[1])
            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertEqual(ContractEvent.query.count(), 0)
            self.assertEqual(AuditLog.query.count(), 0)
            self.assertEqual(BudgetRequest.query.count(), 1)
            self.assertEqual(db.session.get(BudgetRequest, request_id).estado, 'COTIZANDO')

    def test_ownership_and_private_offers(self):
        request_id = self.create(0)
        with self.app.app_context():
            offer_id = self.offer(request_id).id
        self.login(2)
        for path in (f'/presupuestos/{request_id}/confirmacion',):
            self.assertEqual(self.client.get(path).status_code, 403)
        for path in (f'/presupuestos/{request_id}/cancelar', f'/presupuestos/{request_id}/adjudicar/{offer_id}'):
            self.assertEqual(self.client.post(path).status_code, 403)
        with self.app.app_context():
            ctx = build_budget_detail_context(db.session.get(BudgetRequest, request_id), self.ids[3], {})
            self.assertEqual(ctx['offer_rows'], [])
            self.assertIsNone(ctx['budget_contract'])
        self.login(3)
        for path in (f'/presupuestos/{request_id}', f'/presupuestos/{request_id}/confirmacion'):
            self.assertEqual(self.client.get(path).status_code, 403)
        for path in (f'/presupuestos/{request_id}/cancelar', f'/presupuestos/{request_id}/adjudicar/{offer_id}'):
            self.assertEqual(self.client.post(path).status_code, 403)

    def test_provider_budget_links_point_to_real_opportunities(self):
        self.login(1)
        for path in ('/', '/mercados', '/presupuestos', '/presupuestos/mis-enviados'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertNotIn('href="/presupuestos/nuevo"', html)
            self.assertIn('href="/presupuestos"', html)

    def test_existing_html_403_is_used_for_professional(self):
        self.login(1)
        self.app.config['TESTING'] = False
        response = self.client.get('/presupuestos/nuevo', headers={'Accept': 'text/html'})
        self.assertEqual(response.status_code, 403)
        self.assertIn('text/html', response.content_type)
        self.assertNotIn('data-budget-form', response.get_data(as_text=True))

    def test_legacy_budget_contract_does_not_grant_professional_client_actions_or_replay(self):
        request_id = self.create(0)
        with self.app.app_context():
            offer_id = self.offer(request_id).id
            contract = award_budget_offer(request_id, offer_id, self.ids[0]).contract
            contract_id = contract.id
            db.session.get(User, self.ids[0]).rol = 'PROFESIONAL'
            db.session.commit()
            with self.assertRaises(PermissionError):
                create_contract_from_budget_offer(offer_id, actor_user_id=self.ids[0])
            with self.assertRaises(PermissionError):
                award_budget_offer(request_id, offer_id, self.ids[0])
            with self.assertRaises(PermissionError):
                get_contract_detail_context(contract, self.ids[0])
        # Stale CLIENTE session must not bypass the database role.
        self.assertEqual(self.client.get(f'/contratacion/{contract_id}').status_code, 403)
        for action in ('confirmar', 'cancelar'):
            self.assertEqual(self.client.post(f'/contratacion/{contract_id}/{action}', data={'expected_version': 1, 'idempotency_key': f'forbidden-{action}'}).status_code, 403)
        with self.app.app_context():
            self.assertEqual(db.session.get(ContractRequest, contract_id).estado, 'CREADA')
            self.assertEqual(ContractEvent.query.count(), 2)
            self.assertEqual(AuditLog.query.count(), 1)
            self.assertEqual(ContractRequest.query.count(), 1)

    def test_professional_still_offers_on_other_requests_and_not_own(self):
        own = self.legacy_professional_request()
        other = self.create(0)
        self.login(1)
        payload = dict(cobra_visita='no', monto_desde='100', monto_hasta='150', plazo_estimado='3 días')
        self.assertEqual(self.client.post(f'/presupuestos/{other}/ofertar', data=payload).status_code, 302)
        self.client.post(f'/presupuestos/{own}/ofertar', data=payload)
        with self.app.app_context():
            self.assertEqual(BudgetOffer.query.filter_by(budget_request_id=other).count(), 1)
            self.assertEqual(BudgetOffer.query.filter_by(budget_request_id=own).count(), 0)

    def test_inactive_account_cannot_publish_or_manage_in_service(self):
        request_id = self.create(0)
        with self.app.app_context():
            db.session.get(User, self.ids[0]).estado = 'SUSPENDIDO'
            db.session.commit()
            with self.assertRaises(PermissionError):
                create_budget_request(cliente_id=self.ids[0], **self.data)
            with self.assertRaises(PermissionError):
                cancel_budget_request(request_id, self.ids[0])
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=self.data).status_code, 302)
        with self.app.app_context():
            self.assertEqual(BudgetRequest.query.count(), 1)

    def test_server_limits_and_values_preserved(self):
        self.login()
        for name, maximum in [('titulo', 160), ('categoria', 120), ('zona', 120), ('descripcion', 1200)]:
            for value in ('', 'x' * (maximum + 1)):
                with self.subTest(name=name, length=len(value)):
                    response = self.client.post('/presupuestos/nuevo', data={**self.data, name: value})
                    self.assertEqual(response.status_code, 400)
                    html = response.get_data(as_text=True)
                    self.assertIn(f'id="budget-{name}-error"', html)
                    self.assertIn('aria-invalid="true"', html)
                    self.assertIn('data-budget-errors', html)
                    if value:
                        self.assertIn(value, html)
        with self.app.app_context():
            self.assertEqual(BudgetRequest.query.count(), 0)

    def test_maximum_lengths_are_accepted(self):
        self.login()
        data = {**self.data, **{name: 'x' * size for name, size in [('titulo', 160), ('categoria', 120), ('zona', 120), ('descripcion', 1200)]}}
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=data).status_code, 302)

    def test_invalid_date_priority_and_escaped_values(self):
        self.login()
        for name, value in [('fecha_estimada', '2026-02-31'), ('urgencia', 'OTRA'), ('titulo', '<script>' + 'x' * 161)]:
            response = self.client.post('/presupuestos/nuevo', data={**self.data, name: value})
            self.assertEqual(response.status_code, 400)
            html = response.get_data(as_text=True)
            self.assertNotIn('<script>xxx', html)
            self.assertIn(f'budget-{name}-error', html)

    def test_native_no_js_fallback_has_all_essential_fields_and_csrf(self):
        self.login()
        html = self.client.get('/presupuestos/nuevo').get_data(as_text=True)
        self.assertIn('method="post" action="/presupuestos/nuevo" data-budget-form', html)
        self.assertIn('data-budget-submit>Publicar solicitud', html)
        self.assertIn('name="csrf_token"', html)
        self.assertIn('<div data-budget-fields>', html)
        for name in ('titulo', 'categoria', 'zona', 'descripcion'):
            self.assertIn(f'name="{name}"', html)
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=self.data).status_code, 302)

    def test_csrf_rejects_missing_token_and_accepts_rendered_token(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.login()
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=self.data).status_code, 400)
        html = self.client.get('/presupuestos/nuevo').get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
        self.assertEqual(self.client.post('/presupuestos/nuevo', data={**self.data, 'csrf_token': token}).status_code, 302)

    def test_rate_limit_blocks_eleventh_post(self):
        self.app.config['RATELIMIT_ENABLED'] = True
        self.login()
        for _ in range(10):
            self.assertEqual(self.client.post('/presupuestos/nuevo', data=self.data).status_code, 302)
        self.assertEqual(self.client.post('/presupuestos/nuevo', data=self.data).status_code, 429)
        with self.app.app_context():
            self.assertEqual(BudgetRequest.query.count(), 1)  # Ten HTTP retries, one durable command.

    def test_client_award_is_idempotent_with_contract_link_and_effects(self):
        request_id = self.create(0)
        with self.app.app_context():
            offer_id = self.offer(request_id).id
        for _ in range(2):
            self.assertEqual(self.client.post(f'/presupuestos/{request_id}/adjudicar/{offer_id}').status_code, 302)
        with self.app.app_context():
            contract = ContractRequest.query.one()
            self.assertEqual(contract.source_type, 'BUDGET')
            self.assertEqual(contract.cliente_id, self.ids[0])
            self.assertEqual(contract.professional_user_id, self.ids[2])
            self.assertEqual(ContractEvent.query.filter_by(contract_id=contract.id).count(), 2)
            self.assertEqual(AuditLog.query.filter_by(entity_id=contract.id).count(), 1)
            contract_id = contract.id
        self.assertIn(f'/contratacion/{contract_id}', self.client.get(f'/presupuestos/{request_id}').get_data(as_text=True))
        self.assertEqual(self.client.get(f'/contratacion/{contract_id}').status_code, 200)

    def test_professional_never_has_client_contract_capabilities(self):
        actor = SimpleNamespace(id=self.ids[1], rol='PROFESIONAL')
        for source in ('DIRECT', 'PROPOSAL', 'BUDGET'):
            contract = SimpleNamespace(cliente_id=actor.id, professional_user_id=self.ids[2], source_type=source)
            with self.assertRaises(PermissionError):
                _require_role_and_ownership(contract, actor, 'CLIENT')
            with self.assertRaises(PermissionError):
                _require_role_and_ownership(contract, actor, 'PROFESSIONAL')
        assigned = SimpleNamespace(id=self.ids[2], rol='PROFESIONAL')
        _require_role_and_ownership(contract, assigned, 'PROFESSIONAL')
        with self.assertRaises(PermissionError):
            _require_role_and_ownership(contract, assigned, 'CLIENT')

    def test_client_confirms_and_assigned_professional_keeps_provider_transitions(self):
        request_id = self.create(0)
        with self.app.app_context():
            offer_id = self.offer(request_id).id
        self.client.post(f'/presupuestos/{request_id}/adjudicar/{offer_id}')
        with self.app.app_context():
            contract_id = ContractRequest.query.one().id
        self.assertEqual(self.client.post(f'/contratacion/{contract_id}/aceptar', data={'expected_version': 1, 'idempotency_key': 'owner-cannot-accept'}).status_code, 403)
        self.login(2)
        for version, action in enumerate(('aceptar', 'iniciar', 'completar'), 1):
            self.assertEqual(self.client.post(f'/contratacion/{contract_id}/{action}', data={'expected_version': version, 'idempotency_key': f'ux06-{action}'}).status_code, 302)
        self.login(0)
        for _ in range(2):
            self.assertEqual(self.client.post(f'/contratacion/{contract_id}/confirmar', data={'expected_version': 4, 'idempotency_key': 'ux06-confirm'}).status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(ContractRequest, contract_id).estado, 'CONFIRMADA')
            self.assertEqual(ContractEvent.query.filter_by(contract_id=contract_id).count(), 6)
        self.assertIn('Calificar trabajo realizado', self.client.get(f'/contratacion/{contract_id}').get_data(as_text=True))

    def test_only_client_owner_cancels_budget_contract(self):
        request_id = self.create(0)
        with self.app.app_context():
            offer_id = self.offer(request_id).id
        self.client.post(f'/presupuestos/{request_id}/adjudicar/{offer_id}')
        with self.app.app_context():
            contract_id = ContractRequest.query.one().id
        payload = {'expected_version': 1, 'idempotency_key': 'ux06-cancel'}
        self.login(2)
        self.assertEqual(self.client.post(f'/contratacion/{contract_id}/cancelar', data=payload).status_code, 403)
        self.login(0)
        self.assertEqual(self.client.post(f'/contratacion/{contract_id}/cancelar', data=payload).status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(ContractRequest, contract_id).estado, 'CANCELADA')

    def test_offer_cap_and_free_pro_allowance_preserved(self):
        request_id = self.create(0)
        with self.app.app_context():
            self.assertEqual(get_offer_allowance(self.ids[1])['limit'], 9)
            with patch('app.services.budget_service.has_pro_access', return_value=True):
                self.assertIsNone(get_offer_allowance(self.ids[1])['remaining'])
            with patch('app.services.budget_service.get_offer_allowance', return_value={'is_pro': False, 'remaining': 0}):
                with self.assertRaises(ValueError):
                    self.offer(request_id, 1)
            for i in range(6):
                u = User(nombre='P', email=f'cap-{i}@test.local', password='hash', rol='PROFESIONAL')
                db.session.add(u); db.session.flush()
                p = Professional(user_id=u.id, nombre='P', servicio='Plomería', zona='CABA', perfil_completo=True)
                db.session.add(p); db.session.flush()
                db.session.add(BudgetOffer(budget_request_id=request_id, professional_id=p.id, professional_user_id=u.id, monto=100, monto_desde=100, monto_hasta=150, mensaje="Oferta", plazo_estimado='3 días'))
            db.session.commit()
            with self.assertRaises(ValueError):
                self.offer(request_id, 1)
