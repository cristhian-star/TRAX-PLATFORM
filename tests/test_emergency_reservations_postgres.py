"""Explicit disposable PostgreSQL gate; never falls back to a shared database."""
import os
import unittest
import uuid
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timezone
from urllib.parse import urlsplit


@unittest.skipUnless(os.environ.get('GUARDIAS_QA_DATABASE_URL'), 'Exclusive PostgreSQL URL required')
class PostgresReservations(unittest.TestCase):
    def setUp(self):
        url=os.environ['GUARDIAS_QA_DATABASE_URL']
        parsed=urlsplit(url)
        if parsed.hostname not in ('127.0.0.1','localhost') or parsed.path != '/guardias_qa' or parsed.port != 55479:
            raise RuntimeError('Only the explicitly disposable guardias_qa instance is allowed')
        os.environ['DATABASE_URL']=url
        from app import create_app,db
        from app.models.user import User
        from app.models.professional import Professional
        from app.models.verification_request import VerificationRequest
        from app.services import emergency_reservation_service as service
        self.app=create_app(initialize_schema=False)
        self.db=db;self.service=service
        with self.app.app_context():
            user=User(nombre='QA sintético',email=f'{uuid.uuid4()}@test.invalid',password='unused',rol='PROFESIONAL')
            db.session.add(user);db.session.flush();self.actor=user.id
            p=Professional(user_id=user.id,nombre='QA',servicio='Electricidad',zona='CABA',coverage_city='CABA',coverage_province='CABA',perfil_completo=True,estado_perfil='VERIFICADO')
            db.session.add(p);db.session.add(VerificationRequest(user_id=user.id,tipo_usuario='PROFESIONAL',estado='APROBADO'));db.session.commit()
            self.pid=p.id;self.key=service.issue_key(user.id)
        for target in ('app.services.emergency_reservation_service.utc_now',
                       'app.services.professional_urgencies_view_service.utc_now'):
            mocked = patch(target, return_value=datetime(2030,12,30,12,tzinfo=timezone.utc))
            mocked.start()
            self.addCleanup(mocked.stop)
        self.values=['2030-12-31-GUARDIA_DIURNA','2030-12-31-GUARDIA_NOCTURNA']

    def race(self,keys):
        barrier=Barrier(2)
        def worker(key):
            with self.app.app_context():
                barrier.wait(timeout=10)
                try:return self.service.reserve(self.actor,self.values,True,key)
                except self.service.ReservationConflict:return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(worker,keys))

    def test_concurrent_same_key_and_application_restart(self):
        result=self.race([self.key,self.key]);self.assertEqual(result[0],result[1])
        from app import create_app
        from app.models.emergency_shift import EmergencyShift
        from app.models.operation_command import OperationCommand
        from app.models.audit_log import AuditLog
        from app.models.activity_notification import ActivityNotification
        restarted=create_app(initialize_schema=False)
        with restarted.app_context():
            self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),2)
            self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor,operation=self.service.OPERATION).count(),1)
            self.assertEqual(AuditLog.query.filter_by(actor_user_id=self.actor,action='EMERGENCY_SHIFTS_RESERVED').count(),1)
            self.assertEqual(ActivityNotification.query.filter_by(user_id=self.actor,tipo='GUARDIAS_RESERVADAS').count(),1)
        client=restarted.test_client()
        with client.session_transaction() as session:session['user_id']=self.actor;session['user_role']='PROFESIONAL'
        response=client.get('/profesional/oportunidades/urgencias?vista=guardias&fecha=2030-12-31')
        self.assertEqual(response.status_code,200);self.assertIn('Programada',response.text)

    def test_concurrent_distinct_keys_no_duplicate(self):
        with self.app.app_context():key2=self.service.issue_key(self.actor)
        results=self.race([self.key,key2]);self.assertEqual(results.count('conflict'),1)
        from app.models.emergency_shift import EmergencyShift
        with self.app.app_context():self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),2)

    def test_transaction_rollback_and_partially_conflicting_batch(self):
        from unittest.mock import patch
        from app.models.emergency_shift import EmergencyShift,EmergencyShiftReminder
        from app.models.operation_command import OperationCommand
        with self.app.app_context():
            with patch.object(self.service,'crear_notificacion',side_effect=RuntimeError('synthetic failure')):
                with self.assertRaises(RuntimeError):self.service.reserve(self.actor,self.values,True,self.key)
            self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),0)
            self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor,operation=self.service.OPERATION).count(),0)
            self.service.reserve(self.actor,self.values,True,self.key)
            with self.assertRaises(self.service.ReservationConflict):
                self.service.reserve(self.actor,[self.values[0],'2031-01-01-GUARDIA_DIURNA'],True,self.service.issue_key(self.actor))
            self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),2)

    def test_waiting_reservation_revalidates_after_suspension(self):
        from app.services.user_service import suspend_user
        from threading import Event
        from app.models.emergency_shift import EmergencyShift
        started=Event()
        def worker():
            with self.app.app_context():
                started.set()
                try:self.service.reserve(self.actor,self.values,True,self.key)
                except PermissionError:return 'denied'
                return 'unexpected success'
        with self.app.app_context():
            self.service.lock_owner(self.actor)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(worker)
                self.assertTrue(started.wait(timeout=5))
                suspend_user(self.actor)
                self.assertEqual(future.result(timeout=10),'denied')
            self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),0)

    def test_window_rejection_atomic_and_legacy_replay(self):
        from app.models.emergency_shift import EmergencyShift
        from app.models.operation_command import OperationCommand
        with self.app.app_context():
            for outside in ('2030-12-29-GUARDIA_DIURNA','2031-01-27-GUARDIA_DIURNA'):
                with self.assertRaisesRegex(ValueError, 'tres semanas'):
                    self.service.reserve(self.actor,[self.values[0],outside],True,self.key)
                self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),0)
                self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor).count(),0)
            first=self.service.reserve(self.actor,self.values,True,self.key)
            later=lambda:datetime(2031,2,3,12,tzinfo=timezone.utc)
            self.assertEqual(self.service.reserve(self.actor,self.values,True,self.key,clock=later),first)
            self.assertEqual(EmergencyShift.query.filter_by(professional_id=self.pid).count(),2)
            self.assertTrue(all(r.invalidated_at is None for r in EmergencyShift.query.filter_by(professional_id=self.pid)))

    def test_concurrent_reminders(self):
        from app.models.activity_notification import ActivityNotification
        with self.app.app_context():self.service.reserve(self.actor,self.values,True,self.key)
        barrier=Barrier(2)
        def worker(_):
            with self.app.app_context():
                barrier.wait(timeout=10)
                return self.service.dispatch_reminders(clock=lambda:datetime(2030,12,31,4,tzinfo=timezone.utc))
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(worker,[1,2]))
        with self.app.app_context():
            self.assertEqual(ActivityNotification.query.filter_by(user_id=self.actor,tipo='GUARDIA_RECORDATORIO').count(),1)

if __name__=='__main__':unittest.main()
