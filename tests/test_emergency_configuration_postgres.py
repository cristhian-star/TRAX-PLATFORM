"""Run only against the explicitly disposable configuration database."""
import os
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from datetime import datetime, timezone
from urllib.parse import urlsplit
from unittest.mock import patch
from itsdangerous import TimestampSigner
import time

from app import create_app, db
from app.models.user import User
from app.models.professional import Professional
from app.models.verification_request import VerificationRequest
from app.models.emergency_configuration import EmergencyConfiguration
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.services import emergency_configuration_service as config
from app.services import emergency_reservation_service as reservations
from app.services import emergency_release_service as releases


@unittest.skipUnless(os.environ.get('CONFIG_QA_DATABASE_URL'), 'Disposable PostgreSQL required')
class ConfigurationPostgres(unittest.TestCase):
    def setUp(self):
        url=os.environ['CONFIG_QA_DATABASE_URL']; parsed=urlsplit(url)
        if (parsed.hostname,parsed.port,parsed.path) != ('127.0.0.1',15479,'/guardias_qa'):
            raise RuntimeError('Only exclusive configuration QA database allowed')
        os.environ['DATABASE_URL']=url
        self.app=create_app(initialize_schema=False)
        self.now=lambda:datetime(2030,12,30,12,tzinfo=timezone.utc)
        with self.app.app_context():
            self.assertEqual(db.session.execute(db.text('SELECT version_num FROM alembic_version')).scalar(),'20261028_01')
            user=User(nombre='QA sintético configuración',email=f'{uuid.uuid4()}@test.invalid',password='unused',rol='PROFESIONAL')
            db.session.add(user);db.session.flush();self.actor=user.id
            p=Professional(user_id=user.id,nombre='QA sintético',servicio='Plomería',zona='CABA',coverage_city='CABA',coverage_province='CABA',perfil_completo=True,estado_perfil='VERIFICADO')
            db.session.add(p);db.session.add(VerificationRequest(user_id=user.id,tipo_usuario='PROFESIONAL',estado='APROBADO'));db.session.commit();self.pid=p.id
            self.form=config.initial(self.actor)[1];self.form['package_amount']='150.25'

    def save(self, form):
        return config.save(self.actor,form,clock=self.now)

    def reserve(self, day='2030-12-31'):
        return reservations.reserve(self.actor,[day+'-GUARDIA_DIURNA'],True,reservations.issue_key(self.actor),clock=self.now)

    def test_same_command_concurrent_and_fresh_factory_persistence(self):
        barrier=Barrier(2)
        def worker(_):
            with self.app.app_context():
                barrier.wait(timeout=10);return self.save(self.form)
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(worker,[0,1]))
        self.assertEqual(sum(r['replay'] for r in results),1)
        restarted=create_app(initialize_schema=False)
        with restarted.app_context():
            self.assertEqual(str(db.session.get(EmergencyConfiguration,self.pid).package_amount),'150.25')
            self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor,operation=config.OPERATION).count(),1)

    def test_waiting_confirmation_detects_new_reservation(self):
        with self.app.app_context():
            self.reserve();self.form['coverage_city']='Otra zona'
            review=self.save(self.form);self.form.update(impact_key=review['impact_key'],accept_impact='on')
            reservations.lock_owner(self.actor)
            started=Event()
            def worker():
                with self.app.app_context():
                    started.set();return self.save(self.form)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(worker);self.assertTrue(started.wait(5))
                self.reserve('2031-01-01')
                result=future.result(timeout=10)
            self.assertFalse(result['saved']);self.assertEqual(len(result['impact']),2)
            self.assertTrue(all(s.invalidated_at is None for s in EmergencyShift.query.filter_by(professional_id=self.pid)))

    def test_waiting_confirmation_and_voluntary_release(self):
        with self.app.app_context():
            self.reserve();self.form['coverage_city']='Otra zona'
            review=self.save(self.form);self.form.update(impact_key=review['impact_key'],accept_impact='on')
            reservations.lock_owner(self.actor)
            shift=EmergencyShift.query.filter_by(professional_id=self.pid).one()
            key=releases.issue_release_key(self.actor,shift);sid=shift.id
            started=Event()
            def worker():
                with self.app.app_context():
                    started.set();return self.save(self.form)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(worker);self.assertTrue(started.wait(5))
                releases.release(self.actor,sid,key,clock=self.now)
                result=future.result(timeout=10)
                # A submitted review still has to match after the last affected
                # shift was released. Refresh the now-empty impact explicitly.
                self.assertFalse(result['saved']);self.assertEqual(result['impact'],[])
                self.form['impact_key']=result['impact_key']
                self.assertTrue(self.save(self.form)['saved'])
            self.assertIsNotNone(db.session.get(EmergencyShift,sid).invalidated_at)
            self.assertEqual(db.session.get(EmergencyShift,sid).version,2)

    def test_suspension_denies_waiting_save_and_replay(self):
        from app.services.user_service import suspend_user
        with self.app.app_context():
            self.save(self.form)
            reservations.lock_owner(self.actor);started=Event()
            def worker():
                with self.app.app_context():
                    started.set()
                    with self.assertRaises(PermissionError):self.save(self.form)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(worker);self.assertTrue(started.wait(5))
                suspend_user(self.actor);future.result(timeout=10)

    def test_atomic_rollback_then_confirmation(self):
        with self.app.app_context():
            self.reserve();self.form['coverage_city']='Otra zona'
            review=self.save(self.form);self.form.update(impact_key=review['impact_key'],accept_impact='on')
            with patch.object(db.session,'commit',side_effect=RuntimeError('QA rollback')):
                with self.assertRaises(RuntimeError):self.save(self.form)
            self.assertIsNone(db.session.get(EmergencyConfiguration,self.pid))
            self.assertEqual(db.session.get(Professional,self.pid).coverage_city,'CABA')
            shift=EmergencyShift.query.filter_by(professional_id=self.pid).one()
            self.assertIsNone(shift.invalidated_at)
            self.assertTrue(all(r.status=='PENDING' for r in EmergencyShiftReminder.query.filter_by(shift_id=shift.id)))
            self.save(self.form)
            self.assertIsNotNone(db.session.get(EmergencyShift,shift.id).invalidated_at)
            self.assertTrue(all(r.status=='SKIPPED' for r in EmergencyShiftReminder.query.filter_by(shift_id=shift.id)))

    def test_review_expires_while_waiting_for_affected_shift_lock(self):
        signing_time=[1700000000]
        with patch.object(TimestampSigner,'get_timestamp',side_effect=lambda:signing_time[0]):
            with self.app.app_context():
                self.reserve();self.form['coverage_city']='Otra zona'
                review=self.save(self.form)
                self.form.update(impact_key=review['impact_key'],accept_impact='on')
                shift=EmergencyShift.query.filter_by(professional_id=self.pid).with_for_update().one()
                sid=shift.id
                ready=Event();worker_pid=[]
                def worker():
                    with self.app.app_context():
                        worker_pid.append(db.session.execute(db.text('SELECT pg_backend_pid()')).scalar())
                        ready.set()
                        return self.save(self.form)
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(worker)
                    try:
                        self.assertTrue(ready.wait(5))
                        deadline=time.monotonic()+5
                        blocked=False
                        while time.monotonic()<deadline:
                            with db.engine.connect() as connection:
                                blocked=connection.execute(db.text("SELECT wait_event_type = 'Lock' FROM pg_stat_activity WHERE pid=:pid"),{'pid':worker_pid[0]}).scalar()
                            if blocked:break
                            time.sleep(.02)
                        self.assertTrue(blocked,'Worker must really wait on a PostgreSQL lock')
                        signing_time[0]+=901
                    finally:
                        db.session.rollback()  # Release only the test-held shift lock.
                    result=future.result(timeout=10)
                self.assertFalse(result['saved'])
                self.assertEqual(result['error'],config.IMPACT_EXPIRED_MESSAGE)
                self.assertIsNone(db.session.get(EmergencyConfiguration,self.pid))
                self.assertEqual(db.session.get(Professional,self.pid).coverage_city,'CABA')
                self.assertIsNone(db.session.get(EmergencyShift,sid).invalidated_at)
                self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor,operation=config.OPERATION).count(),0)
                self.assertTrue(all(r.status=='PENDING' for r in EmergencyShiftReminder.query.filter_by(shift_id=sid)))


if __name__=='__main__':unittest.main()
