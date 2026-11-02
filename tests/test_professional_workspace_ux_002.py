"""PROF-UX-002: isolated reads and exact ownership/period contracts."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from werkzeug.datastructures import MultiDict
from sqlalchemy.exc import SQLAlchemyError
import unittest
import tests.test_professional_workspace_ux as fixtures
from app import db
from app.models.contract_request import ContractRequest
from app.models.budget_offer import BudgetOffer
from app.models.budget_request import BudgetRequest
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.services.professional_statistics_service import statistics_context

class Workspace002Test(unittest.TestCase):
    setUp = fixtures.ProfessionalWorkspaceTest.setUp
    tearDown = fixtures.ProfessionalWorkspaceTest.tearDown
    login = fixtures.ProfessionalWorkspaceTest.login
    def test_new_private_routes_roles(self):
        paths = ['/profesional/' + p for p in ['presupuestos','propuestas','estadisticas','facturacion']]
        for path in paths:
            self.assertEqual(self.client.get(path).status_code,302)
        self.login(30, 'PROFESIONAL')
        for path in paths:
            self.assertEqual(self.client.get(path).status_code,403)
        self.login()
        for path in paths:
            self.assertEqual(self.client.get(path).status_code,200)

    def test_navigation_order_selection_and_legacy(self):
        self.login()
        html=self.client.get('/profesional/estadisticas').text
        nav=html.split('<nav aria-label="Espacio profesional">')[1].split('</nav>')[0]
        paths=['dashboard','presupuestos','oportunidades/urgencias','propuestas','trabajos','estadisticas','facturacion','perfil/completar']
        offsets=[nav.index('href="/profesional/'+p+'"') for p in paths]
        self.assertEqual(offsets,sorted(offsets))
        self.assertIn('href="/profesional/estadisticas" aria-current="page"',nav)
        self.assertNotIn('>Oportunidades<',nav)
        self.assertEqual(self.client.get('/profesional/oportunidades').status_code,200)
        self.assertEqual(self.client.post('/profesional/estadisticas').status_code,405)

    def test_tabs_periods_and_invalid_parameters(self):
        self.login()
        titles={'resumen':'Tu actividad, en contexto','perfil':'Apariciones en búsquedas','actividad':'Estado actual de los registros','demanda':'Referencias de precios'}
        for tab,title in titles.items():
            for days in (7,30,90):
                r=self.client.get(f'/profesional/estadisticas?tab={tab}&periodo={days}')
                self.assertEqual(r.status_code,200);self.assertIn(title,r.text)
        for query in ['periodo=0','periodo=31','periodo=7&periodo=90','tab=otro','tab=resumen&tab=perfil','periodo='+('9'*1000),'tab=<script>']:
            self.assertEqual(self.client.get('/profesional/estadisticas?'+query).status_code,400)

    def test_aggregates_boundaries_ownership_and_state_meaning(self):
        now=datetime(2026,10,16,15,tzinfo=timezone.utc)
        end=now.replace(tzinfo=None);start=end-timedelta(days=7)
        with self.app.app_context():
            db.session.query(ContractRequest).delete()
            db.session.add(BudgetRequest(id=900,cliente_id=30,categoria='Electricidad',titulo='Sintético',zona='CABA'))
            db.session.add(ProposalRequest(id=901,cliente_id=30,titulo='Sintética',categoria='Electricidad',estado='PUBLICADA'))
            db.session.flush()
            db.session.add(BudgetOffer(budget_request_id=900,professional_id=101,professional_user_id=10,monto=100,mensaje='Test',plazo_estimado='Test',fecha_creacion=start,estado='ADJUDICADO'))
            db.session.add(ProposalApplication(proposal_id=901,professional_id=101,professional_user_id=10,mensaje='Test',created_at=start,estado='ACEPTADA'))
            for i,(pid,uid,created,state,confirmed) in enumerate([
                (101,10,start,'COMPLETADA',None), (101,10,start-timedelta(seconds=1),'CONFIRMADA',start),
                (101,10,end,'CREADA',None), (202,20,start,'CONFIRMADA',start),
                (202,10,start,'CONFIRMADA',start)]):
                db.session.add(ContractRequest(id=400+i,cliente_id=30,professional_id=pid,professional_user_id=uid,servicio='Test',estado=state,fecha_creacion=created,confirmed_at=confirmed))
            db.session.commit()
            result=statistics_context(10,MultiDict({'periodo':'7'}),now)
            self.assertEqual([m['value'] for m in result['metrics']],[1,1,1,1])
            self.assertEqual(sum(row['count'] for row in result['evolution']),1)
            self.assertEqual(dict(result['groups'][2]['rows'])['COMPLETADA'],1)
            self.assertEqual(dict(result['groups'][2]['rows'])['CONFIRMADA'],0)

    def test_empty_unavailable_and_safe_error(self):
        self.login(40)
        self.assertIn('Sin registros en el período',self.client.get('/profesional/estadisticas').text)
        self.assertIn('Métrica todavía no disponible',self.client.get('/profesional/estadisticas?tab=perfil').text)
        with patch('app.services.professional_statistics_service.owned_contracts',side_effect=SQLAlchemyError('private database detail')):
            r=self.client.get('/profesional/estadisticas')
            self.assertEqual(r.status_code,200)
            self.assertIn('Reintentar',r.text)
            self.assertNotIn('private database detail',r.text)

    def test_statistics_no_writes_or_manipulable_owner(self):
        self.login()
        with patch.object(db.session,'commit',side_effect=AssertionError('write')):
            r=self.client.get('/profesional/estadisticas?user_id=20')
            self.assertEqual(r.status_code,200)
            self.assertNotIn('Trabajo ajeno',r.text)
        self.assertNotIn('128',r.text.split('<main>')[1].split('</main>')[0])
        self.assertNotIn('12,5%',r.text)

    def test_billing_prepared_and_native_menu(self):
        self.login()
        r=self.client.get('/profesional/facturacion')
        self.assertIn('Disponible próximamente',r.text)
        self.assertIn('<details class="pw-mobile-menu">',r.text)
        self.assertIn('data-notification-toggle hidden',r.text)
        self.assertIn('js/professional-notifications.js',r.text)
        self.assertNotIn('Emitir factura',r.text)

