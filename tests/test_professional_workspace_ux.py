"""Workspace contracts against an isolated in-memory database."""
import os
import unittest
from unittest.mock import patch
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'workspace-test'
from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.models.professional import Professional
from app.models.contract_request import ContractRequest
from app.services.professional_workspace_service import build_workspace, contract_card

class ProfessionalWorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, RATELIMIT_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            db.session.add_all([User(id=i, nombre=name, email=f'{i}@example.test', password='hash', rol=role)
                for i,name,role in [(10,'Técnica Uno','PROFESIONAL'),(20,'Otro Técnico','PROFESIONAL'),(30,'Cliente Uno','CLIENTE'),(40,'Sin Perfil','PROFESIONAL'),(50,'Admin','SUPER_ADMIN')]])
            db.session.flush()
            db.session.add_all([Professional(id=101,user_id=10,nombre='Técnica Uno',servicio='Electricidad',zona='CABA',perfil_completo=True),
                                Professional(id=202,user_id=20,nombre='Otro Técnico',servicio='Plomería',zona='CABA')])
            db.session.flush()
            db.session.add_all([ContractRequest(id=301,cliente_id=30,professional_id=101,professional_user_id=10,servicio='Tablero propio',estado='COMPLETADA'),
                                ContractRequest(id=302,cliente_id=30,professional_id=202,professional_user_id=20,servicio='Trabajo ajeno',estado='EN_PROGRESO')])
            db.session.commit()
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    def login(self, user=10, role='PROFESIONAL'):
        with self.client.session_transaction() as sess:
            sess.update(user_id=user,user_role=role,user_name='Técnica Uno')
    def test_entry_uses_persisted_role_and_client_public_home(self):
        self.login(10,'CLIENTE')
        self.assertEqual(self.client.get('/').location,'/profesional/dashboard')
        self.login(30,'PROFESIONAL')
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertIn('Mis operaciones',response.text)
        self.assertNotIn('Ingresá a tu cuenta',response.text)
        self.login(50,'CLIENTE')
        self.assertEqual(self.client.get('/').status_code,200)
    def test_four_sections_render_and_share_identity(self):
        self.login()
        with self.app.app_context():
            expected=build_workspace(10)['completion']
        for url in ['/profesional/dashboard','/profesional/oportunidades','/profesional/trabajos','/profesional/perfil/completar']:
            with self.subTest(url=url):
                response=self.client.get(url)
                self.assertEqual(response.status_code,200)
                self.assertIn('professional-workspace.css',response.text)
                self.assertIn('Espacio profesional',response.text)
                self.assertIn('FREE',response.text)
                self.assertNotIn('Clima Técnico',response.text)
        self.assertIn(f'{expected} %',self.client.get('/profesional/dashboard').text)
    def test_contract_ownership_uses_both_identifiers(self):
        self.login()
        for url in ['/profesional/dashboard','/profesional/trabajos/contratados']:
            response=self.client.get(url)
            self.assertIn('Tablero propio',response.text)
            self.assertIn('/contratacion/301',response.text)
            self.assertIn('Esperando confirmación del cliente',response.text)
            self.assertNotIn('Trabajo ajeno',response.text)
            self.assertNotIn('/contratacion/302',response.text)
    def test_anonymous_and_forged_role_cannot_enter(self):
        for url in ['/profesional/dashboard','/profesional/trabajos','/profesional/oportunidades']:
            self.assertEqual(self.client.get(url).status_code,302)
        self.login(30,'PROFESIONAL')
        for url in ['/profesional/dashboard','/profesional/trabajos','/profesional/oportunidades']:
            self.assertEqual(self.client.get(url).status_code,403)
    def test_missing_profile_is_actionable_without_fake_data(self):
        self.login(40)
        response=self.client.get('/profesional/dashboard')
        self.assertEqual(response.status_code,200)
        self.assertIn('Empezá por tu presentación',response.text)
        self.assertIn('0 %',response.text)
        self.assertIn('No tenés trabajos',response.text)
        self.assertIn('Todavía no hay actividad',response.text)
    def test_invalid_and_empty_pagination(self):
        self.login()
        for path in ['/profesional/trabajos','/profesional/oportunidades']:
            for query in ['page=-1','page=abc','page=0','page=1&page=2','page=999999999999']:
                self.assertEqual(self.client.get(f'{path}?{query}').status_code,400)
            self.assertEqual(self.client.get(f'{path}?page=1000').status_code,200)
    def test_reads_do_not_commit_and_escape_names(self):
        with self.app.app_context():
            db.session.get(Professional,101).nombre='<script>alert(1)</script>'
            db.session.commit()
        self.login()
        with patch.object(db.session,'commit',side_effect=AssertionError('GET committed')):
            for path in ['/profesional/dashboard','/profesional/trabajos','/profesional/oportunidades']:
                response=self.client.get(path)
                self.assertEqual(response.status_code,200)
                self.assertNotIn('<script>alert(1)</script>',response.text)
                self.assertIn('&lt;script&gt;',response.text)
    def test_all_states_have_canonical_detail_actions(self):
        for state in ContractRequest.ESTADOS:
            card=contract_card(ContractRequest(id=1,estado=state,servicio='Trabajo',source_type='DIRECT'))
            self.assertEqual(card['url'],'/contratacion/1')
            self.assertTrue(card['action'])
    def test_jobs_paginate_twenty_without_duplicates(self):
        with self.app.app_context():
            db.session.add_all([ContractRequest(cliente_id=30,professional_id=101,professional_user_id=10,servicio=f'Trabajo número {i}',estado='CREADA') for i in range(21)])
            db.session.commit()
        self.login()
        self.assertIn('Siguiente',self.client.get('/profesional/trabajos/contratados').text)
        self.assertNotIn('Siguiente',self.client.get('/profesional/trabajos/contratados?page=2').text)
        self.assertIn('Tablero propio',self.client.get('/profesional/trabajos/contratados?page=2').text)

    def test_opportunities_use_published_sources_and_do_not_become_jobs(self):
        from app.models.budget_request import BudgetRequest
        from app.models.proposal_request import ProposalRequest
        with self.app.app_context():
            db.session.add_all([BudgetRequest(cliente_id=30,categoria='Electricidad',titulo='Presupuesto público',zona='CABA'),
                BudgetRequest(cliente_id=30,categoria='Electricidad',titulo='Presupuesto privado',zona='CABA',estado='BORRADOR'),
                ProposalRequest(cliente_id=30,categoria='Electricidad',titulo='Propuesta pública',estado='PUBLICADA'),
                ProposalRequest(cliente_id=30,categoria='Electricidad',titulo='Propuesta cerrada',estado='CERRADA')])
            db.session.commit()
        self.login()
        response=self.client.get('/profesional/oportunidades')
        self.assertIn('Presupuesto público',response.text)
        self.assertIn('Propuesta pública',response.text)
        self.assertNotIn('Presupuesto privado',response.text)
        self.assertNotIn('Propuesta cerrada',response.text)
        self.assertNotIn('Propuesta pública',self.client.get('/profesional/trabajos/contratados').text)
        self.assertIn('Necesitás una verificación aprobada',response.text)

    def test_prepared_profile_uses_same_canonical_values_on_both_screens(self):
        with self.app.app_context():
            pro=db.session.get(Professional,101)
            pro.descripcion='Servicio técnico'
            pro.logo_url='/avatar.png'
            pro.cover_url='/cover.png'
            pro.gallery_urls='/gallery.png'
            pro.portfolio_urls='/portfolio.png'
            pro.website_url='https://example.test'
            pro.certificaciones_text='Certificado'
            pro.anios_experiencia=2
            db.session.commit()
        self.login()
        service='app.services.professional_workspace_service.'
        with patch(service+'has_approved_verification',return_value=True), patch(service+'has_pro_access',return_value=True):
            home=self.client.get('/profesional/dashboard').text
            profile=self.client.get('/profesional/perfil/completar').text
            self.assertIn('Tu presentación está completa',home)
            self.assertIn('100 %',home)
            self.assertIn('100%',profile)
            for html in (home,profile):
                self.assertIn('Verificado',html)
                self.assertIn('PRO',html)

    def test_suspended_account_cannot_enter(self):
        with self.app.app_context():
            db.session.get(User,10).estado='SUSPENDIDO'
            db.session.commit()
        self.login()
        self.assertEqual(self.client.get('/profesional/dashboard').status_code,302)
        with self.client.session_transaction() as sess:
            self.assertNotIn('user_id',sess)

    def test_profile_and_logout_preserve_csrf(self):
        self.login()
        self.app.config['WTF_CSRF_ENABLED']=True
        html=self.client.get('/profesional/perfil/completar').text
        self.assertIn('name="csrf_token"',html)
        self.assertEqual(self.client.post('/profesional/perfil/completar',data={}).status_code,400)
        self.assertEqual(self.client.post('/logout',data={}).status_code,400)

    def test_notifications_owned_escaped_and_not_read_on_get(self):
        from app.models.activity_notification import ActivityNotification as N
        with self.app.app_context():
            db.session.add_all([N(id=901,user_id=10,tipo='TEST',categoria='CUENTA',titulo='<script>unsafe</script>',mensaje='Mensaje propio',url_destino='/profesional/trabajos'),
                N(id=902,user_id=20,tipo='TEST',categoria='CUENTA',titulo='SECRETO AJENO',mensaje='Privado'),
                N(id=903,user_id=10,tipo='TEST',categoria='CUENTA',titulo='Leída propia',mensaje='Ya vista',leida=True)])
            db.session.commit()
        self.login()
        for path in ['/profesional/dashboard','/profesional/oportunidades','/profesional/trabajos','/profesional/perfil/completar']:
            with patch.object(db.session,'commit',side_effect=AssertionError('GET wrote')):
                html=self.client.get(path).text
            self.assertIn('aria-controls="pw-notification-panel"',html)
            self.assertIn('Notificaciones: 1 sin leer',html)
            self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;',html)
            self.assertNotIn('SECRETO AJENO',html)
            self.assertIn('href="/profesional/trabajos"',html)
            self.assertIn('professional-notifications.js',html)
        with self.app.app_context():
            self.assertFalse(db.session.get(N,901).leida)
        self.assertEqual(self.client.post('/notificaciones/902/leer').status_code,404)
        response=self.client.post('/notificaciones/901/leer',data={'next':'/profesional/dashboard'},follow_redirects=True)
        self.assertIn('Notificaciones: 0 sin leer',response.text)
        self.assertIn('professional-workspace',response.text)

    def test_notification_empty_and_csrf(self):
        self.login()
        html=self.client.get('/profesional/dashboard').text
        self.assertIn('No tenés notificaciones',html)
        self.assertIn('type="button" class="pw-notifications"',html)
        self.assertNotIn('href="/notificaciones"',html)
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post('/notificaciones/901/leer').status_code,400)

if __name__ == '__main__': unittest.main()
