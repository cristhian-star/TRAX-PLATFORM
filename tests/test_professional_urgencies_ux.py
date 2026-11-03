"""Private Urgencias presentation: never expose the legacy client inbox."""
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from werkzeug.datastructures import MultiDict
from tests import test_professional_workspace_ux as workspace_tests
from app import db
from app.models.emergency_request import EmergencyRequest
from app.services.professional_urgencies_view_service import urgency_context

class ProfessionalUrgenciesTest(unittest.TestCase):
    setUp = workspace_tests.ProfessionalWorkspaceTest.setUp
    tearDown = workspace_tests.ProfessionalWorkspaceTest.tearDown
    login = workspace_tests.ProfessionalWorkspaceTest.login
    path = '/profesional/oportunidades/urgencias'

    def test_roles_and_persisted_authorization(self):
        self.assertEqual(self.client.get(self.path).status_code,302)
        for uid,role in [(30,'PROFESIONAL'),(50,'PROFESIONAL')]:
            self.login(uid,role)
            self.assertEqual(self.client.get(self.path).status_code,403)
        self.login(10,'CLIENTE')
        self.assertEqual(self.client.get(self.path).status_code,200)

    def test_pending_not_empty_inbox_and_no_private_requests(self):
        with self.app.app_context():
            db.session.add_all([EmergencyRequest(cliente_id=30,categoria='Electricidad',zona='Privada',prioridad='ALTA',descripcion='SECRETO CLIENTE',estado=state) for state in ('ABIERTA','CANCELADA')])
            db.session.commit()
        self.login()
        with patch.object(db.session,'commit',side_effect=AssertionError('GET wrote')):
            for view in ['solicitudes','guardias','actividad']:
                html=self.client.get(self.path+'?vista='+view).text
                self.assertIn('professional-workspace',html)
                self.assertNotIn('SECRETO CLIENTE',html)
                if view != 'guardias': self.assertIn('todavía no',html)
                self.assertNotIn('Responder por WhatsApp',html)
                self.assertNotIn('Tu guardia está activa',html)
        self.assertEqual(self.client.get(self.path+'?solicitud=1').status_code,404)
        self.assertEqual(self.client.get(self.path+'/1').status_code,404)
        self.assertEqual(self.client.post(self.path,data={'reservar':'1'}).status_code,405)

    def test_date_preview_crosses_midnight_without_reserving(self):
        self.login()
        with patch('app.services.professional_urgencies_view_service.utc_now', return_value=datetime(2026,12,31,tzinfo=timezone.utc)):
            html=self.client.get(self.path+'?vista=guardias&fecha=2026-12-31').text
        self.assertIn('01/01/2027 07:00',html)
        self.assertIn('America/Argentina/Buenos_Aires',html)
        self.assertIn('La selección es provisional',html)
        self.assertIn('data-shift-accept',html)
        self.assertIn('Confirmar turnos',html)
        with self.app.test_request_context(), patch('app.services.professional_urgencies_view_service.ZoneInfo',return_value=timezone(timedelta(hours=-3))):
            vm=urgency_context(MultiDict(),clock=lambda:datetime(2026,10,15,1,tzinfo=timezone.utc))
            self.assertEqual(str(vm['today']),'2026-10-14')
            self.assertEqual(len(vm['shift_blocks']),2)

    def test_week_boundary_cutoff_and_acceptance_unchecked(self):
        zone = timezone(timedelta(hours=-3))
        with self.app.test_request_context(), patch('app.services.professional_urgencies_view_service.ZoneInfo', return_value=zone):
            for micros, expected in [(0, True), (1, False)]:
                vm = urgency_context(MultiDict({'fecha':'2026-10-26'}), clock=lambda:datetime(2026,10,26,6,58,0,micros,tzinfo=zone))
                self.assertEqual(len(vm['week']), 7)
                self.assertEqual(vm['week'][0]['shifts'][0]['selectable'], expected)
                self.assertEqual(vm['week'][0]['shifts'][1]['end'].day, 27)
                self.assertEqual(vm['week_start'].weekday(), 0)
        self.login()
        with patch('app.services.professional_urgencies_view_service.utc_now', return_value=datetime(2027,1,1,tzinfo=timezone.utc)):
            html = self.client.get(self.path+'?vista=guardias&fecha=2027-01-01').text
        self.assertIn('28/12/2026', html)
        self.assertIn('03/01/2027', html)
        self.assertNotIn('pw-opportunity-nav', html)
        self.assertNotIn(' checked', html)
        self.assertIn('professional-shifts.js', html)

    def test_invalid_filters_and_dates(self):
        self.login()
        for query in ['vista=falsa','vista=guardias&vista=actividad','fecha=bad','fecha=2026-02-30','fecha=9999-12-31','fecha=2026-10-14&fecha=2026-10-15','fecha=%3Cscript%3E']:
            self.assertEqual(self.client.get(self.path+'?'+query).status_code,400)

    def test_notifications_theme_and_navigation_retained(self):
        self.login()
        html=self.client.get(self.path).text
        for text in ['professional-notifications.js','theme-switch-v1.js','aria-controls="pw-notification-panel"','aria-current="page"','Mis guardias','Configuraciones']:
            self.assertIn(text,html)
        self.assertNotIn('href="/notificaciones"',html)
        self.assertIn(self.path,self.client.get('/profesional/oportunidades').text)
        self.assertNotIn('fetch(',html)

    def test_inactive_professional_rejected(self):
        from app.models.user import User
        with self.app.app_context():
            db.session.get(User,10).estado='SUSPENDIDO'
            db.session.commit()
        self.login()
        self.assertEqual(self.client.get(self.path).status_code,302)

    def test_missing_timezone_is_recoverable_not_a_reservation(self):
        from zoneinfo import ZoneInfoNotFoundError
        self.login()
        with patch('app.services.professional_urgencies_view_service.ZoneInfo',side_effect=ZoneInfoNotFoundError):
            result=self.client.get(self.path+'?vista=guardias')
            self.assertEqual(result.status_code,200)
            self.assertIn('Reintentar consulta',result.text)
            self.assertNotIn('type="date"',result.text)

if __name__ == '__main__': unittest.main()
