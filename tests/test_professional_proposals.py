"""Private proposal journeys on the normal factory, synthetic isolated SQLite."""
import re
import unittest
from unittest.mock import patch
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.models.contract_request import ContractRequest
from app.models.user import User
from app.models.professional import Professional
from app.models.verification_request import VerificationRequest
from app.services.proposal_service import accept_application, _parse_decimal
import tests.test_proposal_portal_p1 as fixtures


class ProfessionalProposalsTest(unittest.TestCase):
    setUp = fixtures.ProposalPortalTest.setUp
    tearDown = fixtures.ProposalPortalTest.tearDown
    login = fixtures.ProposalPortalTest.login

    def get(self, query=''):
        response = self.client.get('/profesional/propuestas' + query)
        self.assertEqual(response.status_code, 200)
        return response.text

    def verify(self):
        with self.app.app_context():
            db.session.add(VerificationRequest(user_id=2, tipo_usuario='PROFESIONAL', estado='APROBADO'))
            db.session.commit()

    def test_tabs_shell_public_compatibility_and_ownership(self):
        self.login()
        with self.app.app_context():
            db.session.get(ProposalRequest, 1).owner_user_id = 2
            db.session.commit()
        available = self.get()
        self.assertIn('pp-workspace', available)
        self.assertNotIn('proposals-hero', available)
        self.assertIn('href="/profesional/propuestas" aria-current="page"', available)
        own = self.get('?vista=publicaciones&owner_user_id=1')
        self.assertIn('Trabajo 01', own)
        self.assertNotIn('Trabajo 02', own)
        applied = self.get('?vista=postulaciones&professional_user_id=1')
        self.assertIn('Trabajo 15', applied)
        self.assertNotIn('Trabajo 14', applied)
        self.assertIn('POSTULADA', applied)
        self.assertEqual(self.client.get('/propuestas').status_code, 200)
        for path in ('/propuestas/15?vista=postulaciones','/propuestas/nueva?vista=publicaciones'):
            html = self.client.get(path).text
            self.assertIn('pw-layout', html)
            self.assertIn('/profesional/propuestas?vista=', html)

    def test_creation_layout_preserves_fields_client_and_read_only(self):
        from html.parser import HTMLParser
        class Fields(HTMLParser):
            def __init__(self):
                super().__init__()
                self.fields = {}
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag in ('input', 'select', 'textarea') and attrs.get('name'):
                    self.fields[attrs['name']] = (tag, {k: v for k, v in attrs.items() if k != 'value'})
        self.login(1)
        client_html = self.client.get('/propuestas/nueva').text
        self.assertNotIn('pc-create', client_html)
        self.assertIn('proposal-hero', client_html)
        self.login()
        with self.app.app_context():
            writes = []
            def track(conn, cursor, statement, parameters, context, many):
                if statement.lstrip().split()[0].upper() in ('INSERT', 'UPDATE', 'DELETE'):
                    writes.append(statement)
            event.listen(db.engine, 'before_cursor_execute', track)
            try:
                response = self.client.get('/propuestas/nueva?vista=publicaciones')
                self.assertEqual(response.status_code, 200)
                self.assertFalse(writes)
            finally:
                event.remove(db.engine, 'before_cursor_execute', track)
        self.assertIn('pc-create', response.text)
        self.assertNotIn('class="proposal-hero"', response.text)
        self.assertIn('Publicar una propuesta no confirma una contratación.', response.text)
        a, b = Fields(), Fields()
        a.feed(client_html); b.feed(response.text)
        self.assertEqual(a.fields, b.fields)
        self.assertEqual(len(b.fields), 14)  # twelve fields, CSRF and view
        self.assertGreaterEqual(response.text.count('href="/profesional/propuestas?vista=publicaciones"'), 2)

    def test_roles_and_suspended_persisted(self):
        self.assertEqual(self.client.get('/profesional/propuestas').status_code, 302)
        self.login(1)
        self.assertEqual(self.client.get('/profesional/propuestas').status_code, 403)
        self.login()
        with self.app.app_context():
            db.session.get(User, 2).estado = 'SUSPENDIDO'
            db.session.commit()
        self.assertEqual(self.client.get('/profesional/propuestas').status_code, 302)

    def test_filters_pagination_invalid_and_empty(self):
        self.login()
        for query in ('industria=Servicios','categoria=Plomer%C3%ADa','rubro=Desag','ubicacion=Belgrano',
                      'industria=Servicios&categoria=Plomer%C3%ADa&rubro=Desag&ubicacion=Belgrano'):
            self.assertIn('7 propuestas', self.get('?' + query))
        page = self.get('?rubro=Tableros&per_page=2')
        self.assertIn('/profesional/propuestas?rubro=Tableros', page)
        self.assertIn('page=2', page)
        for view in ('disponibles','postulaciones','publicaciones'):
            self.assertIn('Volver a la primera página', self.get('?vista='+view+'&page=99'))
        for query in ('vista=no','vista=disponibles&vista=publicaciones','page=-1','page=9999999999','rubro='+'a'*121):
            self.assertEqual(self.client.get('/profesional/propuestas?'+query).status_code, 400)
        self.assertIn('No encontramos coincidencias', self.get('?rubro=not-real'))
        self.assertIn('Todavía no publicaste', self.get('?vista=publicaciones'))
        with self.app.app_context():
            ProposalApplication.query.delete(); db.session.commit()
        self.assertIn('Todavía no tenés postulaciones', self.get('?vista=postulaciones'))

    def test_get_no_writes_xss_and_private_fields(self):
        self.login()
        with self.app.app_context():
            db.session.get(ProposalRequest,15).titulo='<script>alert(1)</script>'
            db.session.commit()
            writes=[]
            def track(conn,cursor,statement,parameters,context,many):
                if statement.lstrip().split()[0].upper() in ('INSERT','UPDATE','DELETE'):
                    writes.append(statement)
            event.listen(db.engine,'before_cursor_execute',track)
            try:
                for view in ('disponibles','postulaciones','publicaciones'):
                    html=self.get('?vista='+view)
                    self.assertNotIn('<script>alert(1)</script>',html)
                    self.assertNotIn('private-owner@test.invalid',html)
                    self.assertNotIn('PRIVATE_APPLICATION',html)
                self.assertFalse(writes)
            finally:
                event.remove(db.engine,'before_cursor_execute',track)

    def test_eligibility_and_self_application(self):
        self.login()
        self.assertNotIn('>Postularme</a>',self.get())
        self.verify()
        self.assertIn('>Postularme</a>',self.get())
        self.assertIn('Ya te postulaste',self.get())
        with self.app.app_context():
            db.session.get(ProposalRequest,14).owner_user_id=2;db.session.commit()
        self.assertNotIn('/propuestas/14?vista=disponibles#postularme',self.get())
        self.assertEqual(self.client.post('/propuestas/14/postular',data={'mensaje':'own'}).status_code,400)

    def test_nonfinite_and_invalid_money_form_recovery_and_resubmit(self):
        self.login(); self.verify()
        for value in ('NaN','sNaN','Infinity','-Infinity','invalid','1e1000'):
            with self.subTest(value=value):
                response=self.client.post('/propuestas/14/postular',data=dict(mensaje='<b>QA</b>',
                    experiencia_relevante='Experiencia QA',disponibilidad='Mañana',pretension_economica=value,vista='disponibles'))
                self.assertEqual(response.status_code,400)
                self.assertIn('&lt;b&gt;QA&lt;/b&gt;',response.text)
                self.assertIn('Experiencia QA',response.text)
                self.assertIn('value="Mañana"',response.text)
                with self.app.app_context():
                    self.assertEqual(ProposalApplication.query.filter_by(proposal_id=14).count(),0)
                with self.assertRaises(ValueError):
                    _parse_decimal(value,'Importe')
        response=self.client.post('/propuestas/14/postular',data=dict(mensaje='QA',pretension_economica='12.50',vista='postulaciones'))
        self.assertEqual(response.status_code,302)
        self.assertIn('vista=postulaciones',response.location)
        self.client.post('/propuestas/14/postular',data=dict(mensaje='QA'))
        with self.app.app_context():
            self.assertEqual(ProposalApplication.query.filter_by(proposal_id=14).count(),1)

    def test_professional_creation_errors_preserve_and_success(self):
        self.login()
        data=dict(industria='Construcción',categoria='Plomería',rubro='Instalaciones',titulo='Necesidad QA',
                  descripcion='<b>Conservar</b>',ubicacion='CABA',modalidad='Presencial',cantidad_profesionales='1',
                  presupuesto_estimado='NaN',vista='publicaciones')
        for value in ('NaN','sNaN','Infinity','-Infinity','invalid','100000000'):
            data['presupuesto_estimado']=value
            response=self.client.post('/propuestas/nueva',data=data)
            self.assertEqual(response.status_code,400)
            self.assertIn('&lt;b&gt;Conservar&lt;/b&gt;',response.text)
        data['presupuesto_estimado']='150'
        response=self.client.post('/propuestas/nueva',data=data)
        self.assertEqual(response.status_code,302)
        self.assertIn('vista=publicaciones',response.location)
        self.assertIn('Necesidad QA',self.get('?vista=publicaciones'))

    def test_csrf_and_acceptance_contract_link_no_duplicate(self):
        self.login()
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post('/propuestas/14/postular',data={'mensaje':'QA'}).status_code,400)
        self.assertEqual(self.client.post('/propuestas/nueva',data={}).status_code,400)
        with self.app.app_context():
            app=ProposalApplication.query.filter_by(proposal_id=15).one()
            with self.assertRaises(PermissionError): accept_application(15,app.id,2)
            result=accept_application(15,app.id,1)
            again=accept_application(15,app.id,1)
            self.assertEqual(result.contract.id,again.contract.id)
            self.assertEqual(ContractRequest.query.count(),1)
            contract_id=result.contract.id
        html=self.get('?vista=postulaciones')
        self.assertIn(f'/contratacion/{contract_id}',html)
        self.assertIn('pw-layout',self.client.get(f'/contratacion/{contract_id}').text)

    def test_safe_recoverable_read_error(self):
        self.login()
        with patch('app.services.professional_proposals_service.build_proposal_portal',side_effect=SQLAlchemyError('SECRET')):
            response=self.client.get('/profesional/propuestas')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('SECRET',response.text)
        self.assertIn('Reintentar',response.text)

    def test_professional_publisher_can_confirm_only_own_proposal_contract(self):
        from app.services.contract_service import accept_contract, start_contract, declare_work_completed, confirm_completion
        with self.app.app_context():
            db.session.get(User,1).rol='PROFESIONAL'
            db.session.commit()
            application=ProposalApplication.query.filter_by(proposal_id=15).one()
            contract=accept_application(15,application.id,1).contract
            for index, operation in enumerate((accept_contract,start_contract,declare_work_completed)):
                contract=operation(contract.id,2,expected_version=contract.version,
                                   idempotency_key=f'proposal-private-lifecycle-{index}')
            version=contract.version
            with self.assertRaises(PermissionError):
                confirm_completion(contract.id,actor_user_id=2,expected_version=version,idempotency_key='wrong-publisher-confirm-key')
            contract=confirm_completion(contract.id,actor_user_id=1,expected_version=version,idempotency_key='owner-publisher-confirm-key')
            self.assertEqual(contract.estado,'CONFIRMADA')
            replay=confirm_completion(contract.id,actor_user_id=1,expected_version=version,idempotency_key='owner-publisher-confirm-key')
            self.assertEqual(contract.id,replay.id)
