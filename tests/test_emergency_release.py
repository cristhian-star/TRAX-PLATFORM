import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from tests import test_emergency_reservations as reservation_tests
from app import db
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.models.audit_log import AuditLog
from app.services import emergency_reservation_service as reservations
from app.services import emergency_release_service as service


class ReleaseTest(unittest.TestCase):
    setUp = reservation_tests.ReservationTest.setUp
    tearDown = reservation_tests.ReservationTest.tearDown
    login = reservation_tests.ReservationTest.login
    enable = reservation_tests.ReservationTest.enable

    def book(self, kind='GUARDIA_DIURNA'):
        self.enable()
        self.values = ['2030-12-31-' + kind]
        self.reserve_key = reservations.issue_key(10)
        reservations.reserve(10, self.values, True, self.reserve_key)
        shift = EmergencyShift.query.one()
        return shift.id, service.issue_release_key(10, shift)

    def test_day_and_night_strict_boundary(self):
        with self.app.app_context():
            sid, key = self.book()
            shift = db.session.get(EmergencyShift, sid)
            boundary = service.release_deadline(shift).replace(tzinfo=timezone.utc)
            for offset in (0, 1, 12 * 3600):
                with self.subTest(offset=offset), self.assertRaises(ValueError):
                    service.release(10, sid, key, clock=lambda: boundary + timedelta(seconds=offset))
            service.release(10, sid, key, clock=lambda: boundary - timedelta(microseconds=1))
            self.assertIsNotNone(db.session.get(EmergencyShift, sid).invalidated_at)
            reservations.reserve(10, ['2030-12-31-GUARDIA_NOCTURNA'], True, reservations.issue_key(10))
            night = EmergencyShift.query.filter_by(kind='GUARDIA_NOCTURNA').one()
            night_key = service.issue_release_key(10, night)
            boundary = datetime(2030, 12, 31, 10, tzinfo=timezone.utc)
            with self.assertRaises(ValueError):
                service.release(10, night.id, night_key, clock=lambda: boundary)
            service.release(10, night.id, night_key, clock=lambda: boundary - timedelta(seconds=1))

    def test_replay_preserves_release_and_rebooking_is_rejected(self):
        with self.app.app_context():
            sid, key = self.book()
            first = service.release(10, sid, key, clock=lambda: datetime(2030,12,30,12,tzinfo=timezone.utc))
            self.assertTrue(all(r.status == 'SKIPPED' for r in EmergencyShiftReminder.query.all()))
            reservations.reserve(10, self.values, True, self.reserve_key)
            self.assertIsNotNone(db.session.get(EmergencyShift, sid).invalidated_at)
            with self.assertRaises(reservations.ReservationConflict):
                reservations.reserve(10, self.values, True, reservations.issue_key(10))
            self.assertEqual(service.release(10, sid, key), first)
            self.assertIsNotNone(db.session.get(EmergencyShift, sid).invalidated_at)
            self.assertEqual(EmergencyShift.query.count(), 1)
            self.assertEqual(AuditLog.query.filter_by(action=service.OPERATION).count(), 1)

    def test_rollback_and_no_administrative_resurrection(self):
        with self.app.app_context():
            sid, key = self.book()
            with patch.object(reservations, 'crear_notificacion', side_effect=RuntimeError('rollback')):
                with self.assertRaises(RuntimeError):
                    service.release(10, sid, key, clock=lambda: datetime(2030,12,30,12,tzinfo=timezone.utc))
            self.assertIsNone(db.session.get(EmergencyShift, sid).invalidated_at)
            self.assertEqual(OperationCommand.query.filter_by(operation=service.OPERATION).count(), 0)
            user, professional = reservations.lock_owner(10)
            reservations.invalidate_locked(professional, 10, clock=lambda: datetime(2030,12,30,12,tzinfo=timezone.utc))
            db.session.commit()
            with self.assertRaises(reservations.ReservationConflict):
                reservations.reserve(10, self.values, True, reservations.issue_key(10))
            with self.assertRaises(reservations.ReservationConflict):
                service.release(10, sid, key)

    def test_native_http_security_and_release(self):
        with self.app.app_context():
            sid, key = self.book()
        path = f'/profesional/guardias/{sid}/liberar'
        data = {'release_key': key, 'vista': 'guardias'}
        self.assertEqual(self.client.post(path, data=data).status_code, 302)
        self.login(30, 'PROFESIONAL')
        self.assertEqual(self.client.post(path, data=data).status_code, 403)
        self.login(20)
        self.assertEqual(self.client.post(path, data=data).status_code, 403)
        self.login()
        self.assertEqual(self.client.post(path, data={**data, 'release_key': 'tampered'}).status_code, 400)
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.assertEqual(self.client.post(path, data=data).status_code, 400)
        self.app.config['WTF_CSRF_ENABLED'] = False
        with patch.object(service, 'utc_now', return_value=datetime(2030,12,30,12,tzinfo=timezone.utc)):
            response = self.client.post(path, data=data)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Liberación registrada.', response.text)
            self.assertIn('Liberada', response.text)
        with self.app.app_context():
            self.assertEqual(AuditLog.query.filter_by(action=service.OPERATION).count(), 1)

    def test_view_has_separate_forms_and_disabled_boundary(self):
        from html.parser import HTMLParser
        class Forms(HTMLParser):
            def __init__(self):
                super().__init__(); self.depth = 0; self.nested = False; self.release = False; self.disabled = None; self.blocks = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'form':
                    self.depth += 1; self.nested |= self.depth > 1
                    self.release = 'data-release-form' in attrs
                if tag == 'button' and self.release: self.disabled = 'disabled' in attrs
                if attrs.get('name') == 'blocks': self.blocks.append(attrs.get('form'))
            def handle_endtag(self, tag):
                if tag == 'form': self.depth -= 1; self.release = False
        with self.app.app_context():
            self.book()
        self.login()
        for instant, disabled in [(datetime(2030,12,30,12,tzinfo=timezone.utc), False),
                                  (datetime(2030,12,30,22,tzinfo=timezone.utc), True)]:
            with patch('app.services.professional_urgencies_view_service.utc_now', return_value=instant):
                response = self.client.get('/profesional/oportunidades/urgencias?vista=guardias')
            parser = Forms(); parser.feed(response.text)
            self.assertFalse(parser.nested)
            self.assertEqual(parser.disabled, disabled)
            self.assertEqual(set(parser.blocks), {'pu-reservation-form'})

    def test_late_reservation_warns_and_cannot_be_released(self):
        with self.app.app_context():
            self.enable()
            instant = datetime(2030,12,31,9,58,tzinfo=timezone.utc)
            reservations.reserve(10, ['2030-12-31-GUARDIA_DIURNA'], True,
                reservations.issue_key(10), clock=lambda: instant)
            shift = EmergencyShift.query.one()
            with self.assertRaises(ValueError):
                service.release(10, shift.id, service.issue_release_key(10, shift), clock=lambda: instant)
            self.assertIsNone(db.session.get(EmergencyShift, shift.id).invalidated_at)
        self.login()
        html = self.client.get('/profesional/oportunidades/urgencias?vista=guardias').text
        self.assertIn('Si al confirmar faltan 12 horas o menos', html)
        self.assertLess(html.index('Si al confirmar faltan 12 horas o menos'), html.index('>Confirmar turnos'))


if __name__ == '__main__':
    unittest.main()
