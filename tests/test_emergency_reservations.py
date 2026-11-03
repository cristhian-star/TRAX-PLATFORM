import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from tests import test_professional_workspace_ux as workspace_tests
from app import db
from app.models.professional import Professional
from app.models.verification_request import VerificationRequest
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.models.activity_notification import ActivityNotification
from app.services import emergency_reservation_service as service


class ReservationTest(unittest.TestCase):
    def setUp(self):
        workspace_tests.ProfessionalWorkspaceTest.setUp(self)
        for target in ('app.services.emergency_reservation_service.utc_now',
                       'app.services.professional_urgencies_view_service.utc_now'):
            mocked = patch(target, return_value=datetime(2030,12,30,12,tzinfo=timezone.utc))
            mocked.start()
            self.addCleanup(mocked.stop)
    tearDown = workspace_tests.ProfessionalWorkspaceTest.tearDown
    login = workspace_tests.ProfessionalWorkspaceTest.login

    def enable(self):
        p = db.session.get(Professional,101)
        p.estado_perfil='VERIFICADO';p.coverage_city='CABA';p.coverage_province='CABA'
        db.session.add(VerificationRequest(user_id=10,tipo_usuario='PROFESIONAL',estado='APROBADO'))
        db.session.commit()

    def test_batch_replay_conflict_and_no_partial_batch(self):
        with self.app.app_context():
            self.enable(); key=service.issue_key(10)
            values=['2030-12-31-GUARDIA_DIURNA','2030-12-31-GUARDIA_NOCTURNA']
            clock=lambda:datetime(2030,12,30,tzinfo=timezone.utc)
            first=service.reserve(10,values,True,key,clock=clock)
            self.assertEqual(service.reserve(10,list(reversed(values)),True,key,clock=clock),first)
            self.assertEqual(EmergencyShift.query.count(),2)
            self.assertEqual(OperationCommand.query.count(),1)
            self.assertEqual(ActivityNotification.query.count(),1)
            with self.assertRaises(service.ReservationConflict):
                service.reserve(10,[values[0]],True,key,clock=clock)
            with self.assertRaises(service.ReservationConflict):
                service.reserve(10,[values[0],'2031-01-01-GUARDIA_DIURNA'],True,service.issue_key(10),clock=clock)
            self.assertEqual(EmergencyShift.query.count(),2)
            self.assertEqual(EmergencyShift.query.order_by(EmergencyShift.id.desc()).first().ends_at,datetime(2031,1,1,10))

    def test_validation_and_rollback(self):
        with self.app.app_context():
            self.enable();key=service.issue_key(10);values=['2030-01-01-GUARDIA_DIURNA']
            clock=lambda:datetime(2029,12,31,tzinfo=timezone.utc)
            for accepted,token,blocks in [(False,key,values),(True,service.issue_key(20),values),(True,key,['bad']),(True,key,values*2)]:
                with self.assertRaises(ValueError): service.reserve(10,blocks,accepted,token,clock=clock)
            with patch.object(service,'crear_notificacion',side_effect=RuntimeError('forced rollback')):
                with self.assertRaises(RuntimeError):service.reserve(10,values,True,key,clock=clock)
            self.assertEqual(EmergencyShift.query.count(),0)
            self.assertEqual(OperationCommand.query.count(),0)
            service.reserve(10,values,True,key,clock=clock)
            self.assertEqual(EmergencyShift.query.count(),1)

    def test_suspension_restoration_never_resurrects(self):
        from app.services.user_service import suspend_user,reactivate_user
        with self.app.app_context():
            self.enable();key=service.issue_key(10)
            service.reserve(10,['2030-01-01-GUARDIA_DIURNA'],True,key,clock=lambda:datetime(2029,12,31,tzinfo=timezone.utc))
            suspend_user(10);reactivate_user(10)
            self.assertIsNotNone(EmergencyShift.query.one().invalidated_at)
            self.assertTrue(all(r.status=='SKIPPED' for r in EmergencyShiftReminder.query.all()))

    def test_revocation_and_profile_change_invalidate_current_and_future(self):
        from app.services.verification_service import update_verification_status
        from app.services.professional_service import complete_professional_profile
        with self.app.app_context():
            self.enable()
            service.reserve(10,['2030-01-01-GUARDIA_DIURNA','2030-01-02-GUARDIA_NOCTURNA'],True,service.issue_key(10),clock=lambda:datetime(2029,12,31,tzinfo=timezone.utc))
            verification=VerificationRequest.query.filter_by(user_id=10).one()
            update_verification_status(verification.id,'RECHAZADO')
            self.assertTrue(all(r.invalidated_at is not None for r in EmergencyShift.query.all()))
            update_verification_status(verification.id,'APROBADO')
            self.assertTrue(all(r.invalidated_at is not None for r in EmergencyShift.query.all()))
            service.reserve(10,['2030-01-03-GUARDIA_DIURNA'],True,service.issue_key(10),clock=lambda:datetime(2029,12,31,tzinfo=timezone.utc))
            complete_professional_profile(10,'QA','Plomería',coverage_city='CABA',coverage_province='CABA')
            self.assertTrue(all(r.invalidated_at is not None for r in EmergencyShift.query.all()))

    def test_current_and_finished_are_derived_on_read(self):
        from app.services.professional_urgencies_view_service import urgency_context,reservation_context
        from werkzeug.datastructures import MultiDict
        with self.app.app_context():
            self.enable()
            service.reserve(10,['2030-01-01-GUARDIA_DIURNA'],True,service.issue_key(10),clock=lambda:datetime(2029,12,31,tzinfo=timezone.utc))
            for instant, expected in [(datetime(2030,1,1,10,tzinfo=timezone.utc),'En curso'),(datetime(2030,1,1,22,tzinfo=timezone.utc),'Finalizada')]:
                with self.app.test_request_context(),patch('app.services.professional_urgencies_view_service.utc_now',return_value=instant):
                    context=urgency_context(MultiDict({'fecha':'2030-01-01'}),clock=lambda:instant)
                    reservation_context(10,context)
                    block=context['week'][1]['shifts'][0]
                    self.assertEqual(block['reservation_state'],expected)

    def test_scheduled_panel_real_dates_ownership_and_invalidated_exclusion(self):
        with self.app.app_context():
            self.enable()
            values=['2030-12-31-GUARDIA_DIURNA','2030-12-31-GUARDIA_NOCTURNA','2031-01-01-GUARDIA_DIURNA']
            service.reserve(10,values,True,service.issue_key(10))
            invalid=EmergencyShift.query.filter_by(day=datetime(2031,1,1).date()).one()
            invalid.invalidated_at=datetime(2030,12,30,13)
            db.session.commit()
        self.login()
        with patch.object(db.session,'commit',side_effect=AssertionError('GET wrote')):
            html=self.client.get('/profesional/oportunidades/urgencias?vista=guardias').text
        panel=html.split('<h2>Guardias programadas</h2>')[1].split('</section>')[0]
        self.assertIn('Diurna · 31/12/2030',panel)
        self.assertIn('Nocturna · 31/12/2030',panel)
        self.assertIn('Finaliza el 01/01/2031',panel)
        self.assertNotIn('Diurna · 01/01/2031',panel)
        with patch('app.services.professional_urgencies_view_service.utc_now',return_value=datetime(2031,1,1,1,tzinfo=timezone.utc)):
            panel=self.client.get('/profesional/oportunidades/urgencias?vista=guardias').text.split('<h2>Guardias programadas</h2>')[1].split('</section>')[0]
            self.assertIn('En curso',panel)
            self.assertNotIn('Diurna · 31/12/2030',panel)
        self.login(20)
        panel=self.client.get('/profesional/oportunidades/urgencias?vista=guardias').text.split('<h2>Guardias programadas</h2>')[1].split('</section>')[0]
        self.assertNotIn('31/12/2030',panel)
        self.assertIn('No tenés guardias programadas',panel)

    def test_reminders_exactly_once_and_stale_skip(self):
        with self.app.app_context():
            self.enable();service.reserve(10,['2030-01-01-GUARDIA_DIURNA'],True,service.issue_key(10),clock=lambda:datetime(2029,12,31,tzinfo=timezone.utc))
            clock=lambda:datetime(2030,1,1,4,tzinfo=timezone.utc)
            self.assertEqual(service.dispatch_reminders(clock=clock),1)
            self.assertEqual(service.dispatch_reminders(clock=clock),0)
            self.assertEqual(service.dispatch_reminders(clock=lambda:datetime(2030,1,1,10,tzinfo=timezone.utc)),0)
            self.assertEqual(sorted(r.status for r in EmergencyShiftReminder.query.all()),['SENT','SKIPPED'])

    def test_http_roles_csrf_and_native_success(self):
        path='/profesional/guardias/reservar'
        self.assertEqual(self.client.post(path).status_code,302)
        self.login(30,'PROFESIONAL');self.assertEqual(self.client.post(path).status_code,403)
        self.login()
        with self.app.app_context():self.enable();key=service.issue_key(10)
        data={'blocks':['2030-12-31-GUARDIA_DIURNA'],'accepted':'yes','reservation_key':key,'vista':'guardias','fecha':'2030-12-31'}
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post(path,data=data).status_code,400)
        self.app.config['WTF_CSRF_ENABLED']=False
        response=self.client.post(path,data=data)
        self.assertEqual(response.status_code,200)
        self.assertIn('Guardias confirmadas y guardadas',response.text)
        self.assertIn('Programada',response.text)
        self.assertEqual(self.client.post(path,data=data).status_code,200)
        with self.app.app_context():self.assertEqual(EmergencyShift.query.count(),1)
        self.login(20)
        self.assertNotIn('Programada',self.client.get('/profesional/oportunidades/urgencias?vista=guardias&fecha=2030-12-31').text)

    def test_strict_eligibility_and_authorization_before_replay(self):
        from app.services.user_service import suspend_user
        with self.app.app_context():
            key=service.issue_key(10);values=['2030-12-31-GUARDIA_DIURNA']
            with self.assertRaises(PermissionError):service.reserve(10,values,True,key)
            self.enable();service.reserve(10,values,True,key)
            suspend_user(10)
            with self.assertRaises(PermissionError):service.reserve(10,values,True,key)

if __name__=='__main__':unittest.main()
