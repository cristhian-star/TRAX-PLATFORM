"""Release gate uses only the disposable database guarded by reservation fixtures."""
import os
import unittest
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest.mock import patch
from tests import test_emergency_reservations_postgres as fixtures
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.audit_log import AuditLog
from app.models.operation_command import OperationCommand
from app.services import emergency_release_service as release_service


@unittest.skipUnless(os.environ.get('GUARDIAS_QA_DATABASE_URL'), 'Exclusive PostgreSQL URL required')
class PostgresRelease(unittest.TestCase):
    setUp = fixtures.PostgresReservations.setUp

    def book(self):
        self.service.reserve(self.actor, self.values, True, self.key)
        shift = EmergencyShift.query.filter_by(professional_id=self.pid, kind='GUARDIA_DIURNA').one()
        return shift.id, release_service.issue_release_key(self.actor, shift)

    def test_concurrent_replay_single_effect(self):
        with self.app.app_context(): sid, key = self.book()
        barrier = Barrier(2)
        def worker(_):
            with self.app.app_context():
                barrier.wait(timeout=10)
                return release_service.release(self.actor, sid, key,
                    clock=lambda: datetime(2030,12,30,12,tzinfo=timezone.utc))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, range(2)))
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            self.assertEqual(AuditLog.query.filter_by(actor_user_id=self.actor, action=release_service.OPERATION).count(), 1)
            self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor, operation=release_service.OPERATION).count(), 1)
            self.assertTrue(all(r.status == 'SKIPPED' for r in EmergencyShiftReminder.query.filter_by(shift_id=sid)))
            with self.assertRaises(self.service.ReservationConflict):
                self.service.reserve(self.actor, self.values, True, self.service.issue_key(self.actor))

    def test_effective_clock_after_waiting_for_lock(self):
        with self.app.app_context(): sid, key = self.book()
        started = Event()
        boundary = datetime(2030,12,30,22,tzinfo=timezone.utc)
        current = [boundary - timedelta(seconds=1)]
        def worker():
            with self.app.app_context():
                started.set()
                try: release_service.release(self.actor, sid, key, clock=lambda: current[0])
                except ValueError: return 'blocked'
                return 'incorrect'
        with self.app.app_context():
            self.service.lock_owner(self.actor)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(worker)
                self.assertTrue(started.wait(5))
                current[0] = boundary
                self.db.session.rollback()
                self.assertEqual(future.result(timeout=10), 'blocked')
            self.assertIsNone(self.db.session.get(EmergencyShift, sid).invalidated_at)

    def test_atomic_rollback_and_ownership(self):
        with self.app.app_context():
            sid, key = self.book()
            with self.assertRaises(PermissionError):
                release_service.release(-1, sid, key)
            with patch.object(self.service, 'crear_notificacion', side_effect=RuntimeError('synthetic rollback')):
                with self.assertRaises(RuntimeError):
                    release_service.release(self.actor, sid, key, clock=lambda: datetime(2030,12,30,12,tzinfo=timezone.utc))
            self.assertIsNone(self.db.session.get(EmergencyShift, sid).invalidated_at)
            self.assertEqual(OperationCommand.query.filter_by(actor_user_id=self.actor, operation=release_service.OPERATION).count(), 0)
            self.assertTrue(all(r.status == 'PENDING' for r in EmergencyShiftReminder.query.filter_by(shift_id=sid)))
