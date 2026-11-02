"""Explicit destructive gate: only disposable work_records_qa on 55482."""
import os
import unittest
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from datetime import datetime, timezone
from unittest.mock import patch
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from app import create_app, db
from app.models.user import User
from app.models.professional import Professional
from app.models.work_record import WorkRecord, WorkReminder
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.services import work_record_service as service
from tests.test_work_records import data, follow, NOW

DUE=datetime(2026,11,4,12,tzinfo=timezone.utc)


class WorkRecordsPostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url=make_url(os.environ['TRAX_POSTGRES_TEST_URL'])
        if (url.host,url.port,url.database)!=('127.0.0.1',55482,'work_records_qa') or os.environ.get('TRAX_POSTGRES_TEST_ALLOW_RESET')!='1':
            raise RuntimeError('Exclusive disposable PostgreSQL required')
        os.environ['DATABASE_URL']=str(url.render_as_string(hide_password=False))
        cls.config=Config('alembic.ini')
        command.upgrade(cls.config,'head')
        cls.app=create_app();cls.app.config.update(TESTING=True)

    def setUp(self):
        with self.app.app_context():
            names=', '.join(db.engine.dialect.identifier_preparer.quote(t.name) for t in reversed(db.metadata.sorted_tables))
            db.session.execute(sa.text('TRUNCATE TABLE '+names+' RESTART IDENTITY CASCADE'));db.session.commit()
            db.session.add_all([User(id=1,nombre='Client QA',email='client@qa.invalid',password='x',rol='CLIENTE',estado='ACTIVO'),User(id=2,nombre='Pro QA',email='pro@qa.invalid',password='x',rol='PROFESIONAL',estado='ACTIVO')]);db.session.flush()
            db.session.add(Professional(id=1,user_id=2,nombre='Pro QA',servicio='QA',zona='QA',perfil_completo=True));db.session.commit()

    def race(self,call):
        barrier=Barrier(2)
        def run(i):
            with self.app.app_context():
                barrier.wait(timeout=10)
                try:return call(i)
                except service.WorkConflict:return 'conflict'
                finally:db.session.remove()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(run,[0,1]))

    def test_double_create_and_payload_conflict(self):
        key=str(uuid.uuid4())
        ids=self.race(lambda i:service.save_record(2,follow(),key,clock=lambda:NOW))
        self.assertEqual(ids[0],ids[1])
        with self.app.app_context():
            self.assertEqual(WorkRecord.query.count(),1);self.assertEqual(WorkReminder.query.count(),1)
        key2=str(uuid.uuid4())
        results=self.race(lambda i:service.save_record(2,data(title=str(i)),key2,clock=lambda:NOW))
        self.assertEqual(results.count('conflict'),1)

    def test_two_edits_conflict(self):
        with self.app.app_context():rid=service.save_record(2,data(),str(uuid.uuid4()),clock=lambda:NOW)
        results=self.race(lambda i:service.save_record(2,data(title=str(i)),str(uuid.uuid4()),rid,1,clock=lambda:NOW))
        self.assertEqual(results.count('conflict'),1)
        with self.app.app_context():self.assertEqual(db.session.get(WorkRecord,rid).version,2)

    def test_two_dispatchers_once(self):
        with self.app.app_context():service.save_record(2,follow(),str(uuid.uuid4()),clock=lambda:NOW)
        results=self.race(lambda i:service.dispatch_work_reminders(clock=lambda:DUE))
        self.assertEqual(sum(results),1)
        with self.app.app_context():self.assertEqual(ActivityNotification.query.count(),1)

    def test_edit_lock_blocks_old_dispatch(self):
        with self.app.app_context():rid=service.save_record(2,follow(),str(uuid.uuid4()),clock=lambda:NOW)
        held=Event();release=Event()
        original=service.authorize
        def locked(actor,lock=False):
            result=original(actor,lock)
            if lock:held.set();release.wait(10)
            return result
        def edit():
            with self.app.app_context():
                with patch.object(service,'authorize',side_effect=locked):return service.save_record(2,data(),str(uuid.uuid4()),rid,1,clock=lambda:NOW)
        def dispatch():
            with self.app.app_context():return service.dispatch_work_reminders(clock=lambda:DUE)
        with ThreadPoolExecutor(max_workers=2) as pool:
            editing=pool.submit(edit);self.assertTrue(held.wait(5));sending=pool.submit(dispatch)
            try:
                waiting=False
                with self.app.app_context():
                    with db.engine.connect() as connection:
                        deadline=time.monotonic()+5
                        while time.monotonic()<deadline:
                            waiting=bool(connection.execute(sa.text("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'")).scalar())
                            if waiting:break
                            time.sleep(0.05)
                self.assertTrue(waiting,'Dispatcher must actually wait for the edit transaction lock')
            finally:release.set()
            editing.result(timeout=15);self.assertEqual(sending.result(timeout=15),0)
        with self.app.app_context():self.assertEqual(ActivityNotification.query.count(),0)

    def test_transaction_failure_recovery_and_restart(self):
        with self.app.app_context():
            with patch.object(db.session,'commit',side_effect=RuntimeError('crash')):
                with self.assertRaises(RuntimeError):service.save_record(2,follow(),str(uuid.uuid4()),clock=lambda:NOW)
            self.assertEqual(WorkRecord.query.count(),0);self.assertEqual(WorkReminder.query.count(),0)
            rid=service.save_record(2,follow(),str(uuid.uuid4()),clock=lambda:NOW)
            with patch.object(service,'crear_notificacion',side_effect=RuntimeError('crash')):
                with self.assertRaises(RuntimeError):service.dispatch_work_reminders(clock=lambda:DUE)
            self.assertEqual(WorkReminder.query.one().status,'PENDING');db.session.remove();db.engine.dispose()
        app2=create_app();app2.config.update(TESTING=True)
        with app2.app_context():
            self.assertEqual(db.session.get(WorkRecord,rid).title,'Trabajo sintético')
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:DUE),1)
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:DUE),0)

    def test_migration_previous_data_downgrade_upgrade(self):
        with self.app.app_context():
            service.save_record(2,data(),str(uuid.uuid4()),clock=lambda:NOW);db.session.remove();db.engine.dispose()
        command.downgrade(self.config,'20261028_01')
        with self.app.app_context():self.assertEqual(User.query.count(),2);db.session.remove()
        command.upgrade(self.config,'head')
        with self.app.app_context():
            self.assertEqual(User.query.count(),2);self.assertEqual(WorkRecord.query.count(),0)
            self.assertEqual(db.session.execute(sa.text('SELECT version_num FROM alembic_version')).scalar(),'20261030_01')
