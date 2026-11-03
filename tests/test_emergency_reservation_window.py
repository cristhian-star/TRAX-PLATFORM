"""Four-week policy at local calendar, HTTP and transactional boundaries."""
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch
from werkzeug.datastructures import MultiDict

from app import db
from app.models.emergency_shift import EmergencyShift
from app.models.operation_command import OperationCommand
from app.services import emergency_reservation_service as service
from app.services.emergency_shift_service import reservation_window
from app.services.professional_urgencies_view_service import urgency_context
from tests import test_emergency_reservations as fixtures
from tests import test_professional_workspace_ux as workspace


class ReservationWindowTest(unittest.TestCase):
    setUp = workspace.ProfessionalWorkspaceTest.setUp
    tearDown = workspace.ProfessionalWorkspaceTest.tearDown
    login = workspace.ProfessionalWorkspaceTest.login
    enable = fixtures.ReservationTest.enable
    instant = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
    path = '/profesional/oportunidades/urgencias'

    def test_calendar_endpoints_and_last_night(self):
        with self.app.test_request_context():
            for value, previous, following in [('2026-10-26',None,'2026-11-02'),
                                                ('2026-11-16','2026-11-09',None)]:
                vm=urgency_context(MultiDict({'fecha':value}),clock=lambda:self.instant)
                self.assertEqual(vm['previous_week'],previous)
                self.assertEqual(vm['next_week'],following)
                self.assertEqual(len(vm['week']),7)
            night=vm['week'][-1]['shifts'][-1]
            self.assertEqual(night['start'].date(),date(2026,11,22))
            self.assertEqual(night['end'].date(),date(2026,11,23))
        with self.app.app_context():
            self.enable()
            service.reserve(10,['2026-11-22-GUARDIA_NOCTURNA'],True,service.issue_key(10),clock=lambda:self.instant)
            self.assertEqual(EmergencyShift.query.one().ends_at,datetime(2026,11,23,10))

    def test_local_monday_rollover_and_year_boundary(self):
        cases=[(datetime(2026,10,26,2,59,59,tzinfo=timezone.utc),date(2026,10,19),date(2026,11,16)),
               (datetime(2026,10,26,3,tzinfo=timezone.utc),date(2026,10,26),date(2026,11,23)),
               (datetime(2026,12,31,12,tzinfo=timezone.utc),date(2026,12,28),date(2027,1,25))]
        for instant,start,end in cases:
            self.assertEqual(reservation_window(instant),(start,end))

    def test_get_clamps_both_ends_without_writes_and_disabled_controls(self):
        self.login()
        with patch('app.services.professional_urgencies_view_service.utc_now',return_value=self.instant), patch.object(db.session,'commit',side_effect=AssertionError('GET wrote')):
            for requested,target,control in [('2026-10-19','2026-10-26','anterior'),('2026-11-23','2026-11-16','siguiente')]:
                response=self.client.get(self.path+'?vista=guardias&fecha='+requested)
                self.assertEqual(response.status_code,302)
                self.assertEqual(response.location,self.path+'?vista=guardias&fecha='+target)
                html=self.client.get(response.location).text
                self.assertIn('disabled aria-label="Semana '+control+'"',html)
            for view in ('guardias','solicitudes'):
                html=self.client.get(self.path+'?vista='+view).text
                for removed in ('Tu presencia en la búsqueda manual','Revisar mi perfil y contacto','Consultar el directorio público'):
                    self.assertNotIn(removed,html)
            self.assertIn('Tu guardia',html)
            self.assertIn('Ver mis guardias',html)

    def test_post_outside_both_ends_has_no_partial_effects(self):
        self.login()
        with self.app.app_context():
            self.enable();key=service.issue_key(10)
        with patch('app.services.emergency_reservation_service.utc_now',return_value=self.instant), patch('app.services.professional_urgencies_view_service.utc_now',return_value=self.instant):
            for outside in ('2026-10-25','2026-11-23'):
                response=self.client.post('/profesional/guardias/reservar',data={
                    'blocks':['2026-10-27-GUARDIA_DIURNA',outside+'-GUARDIA_DIURNA'],
                    'accepted':'yes','reservation_key':key,'vista':'guardias','fecha':'2026-10-26'})
                self.assertEqual(response.status_code,400)
                self.assertIn('tres semanas siguientes',response.text)
                with self.app.app_context():
                    self.assertEqual(EmergencyShift.query.count(),0)
                    self.assertEqual(OperationCommand.query.count(),0)

    def test_open_form_rechecks_clock_after_lock(self):
        # Sunday form becomes Monday: its old week is no longer allowed.
        before=datetime(2026,11,2,2,59,tzinfo=timezone.utc)
        after=datetime(2026,11,2,3,tzinfo=timezone.utc)
        with self.app.test_request_context():
            vm=urgency_context(MultiDict({'fecha':'2026-10-26'}),clock=lambda:before)
            self.assertEqual(vm['week_start'],date(2026,10,26))
        with self.app.app_context():
            self.enable();key=service.issue_key(10);locked=[]
            original=service.lock_owner
            def lock(actor):
                result=original(actor);locked.append(True);return result
            def clock():
                self.assertTrue(locked);return after
            with patch.object(service,'lock_owner',side_effect=lock):
                with self.assertRaisesRegex(ValueError,'tres semanas'):
                    service.reserve(10,['2026-11-01-GUARDIA_NOCTURNA'],True,key,clock=clock)
            self.assertEqual(EmergencyShift.query.count(),0)

    def test_replay_and_existing_outside_records_preserved(self):
        with self.app.app_context():
            self.enable();key=service.issue_key(10)
            values=['2026-11-22-GUARDIA_NOCTURNA']
            first=service.reserve(10,values,True,key,clock=lambda:self.instant)
            # Previously confirmed future reservation remains even when clock puts it outside.
            earlier=self.instant-timedelta(days=28)
            self.assertEqual(service.reserve(10,values,True,key,clock=lambda:earlier),first)
            later=self.instant+timedelta(days=35)
            self.assertEqual(service.reserve(10,values,True,key,clock=lambda:later),first)
            self.assertEqual(EmergencyShift.query.count(),1)
            self.assertIsNone(EmergencyShift.query.one().invalidated_at)
            self.assertEqual(OperationCommand.query.count(),1)


if __name__ == '__main__':
    unittest.main()
