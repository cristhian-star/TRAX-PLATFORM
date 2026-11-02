"""Impact review lifetime: control signing time without changing the system clock."""
import unittest
from unittest.mock import patch
from itsdangerous import TimestampSigner, URLSafeSerializer
from flask import current_app
import html
import re
from datetime import datetime, timezone
from tests import test_emergency_configuration as fixtures
from app import db
from app.models.professional import Professional
from app.models.emergency_configuration import EmergencyConfiguration
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.models.audit_log import AuditLog
from app.models.activity_notification import ActivityNotification
from app.services import emergency_configuration_service as service
from app.services import emergency_reservation_service as reservations


class ImpactExpiryTest(unittest.TestCase):
    setUp = fixtures.ConfigurationTest.setUp
    tearDown = fixtures.ConfigurationTest.tearDown
    enable = fixtures.ConfigurationTest.enable
    login = fixtures.ConfigurationTest.login
    form = fixtures.ConfigurationTest.form
    save = fixtures.ConfigurationTest.save
    issued = 1700000000

    def prepare(self):
        self.enable()
        reservations.reserve(10,['2030-12-31-GUARDIA_DIURNA'],True,reservations.issue_key(10))
        form=self.form(coverage_city='Otra zona',notes='<b>Texto sintético</b>',package_amount='123.45')
        with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued):
            review=self.save(form)
        form.update(impact_key=review['impact_key'],accept_impact='on')
        return form

    def state(self):
        models=(Professional,EmergencyConfiguration,EmergencyShift,EmergencyShiftReminder,
                OperationCommand,AuditLog,ActivityNotification)
        return {m.__tablename__: sorted(repr(tuple(getattr(row,c.name) for c in m.__table__.columns))
                for row in m.query.all()) for m in models}

    def rejected_at(self, age):
        with self.app.app_context():
            form=self.prepare();before=self.state()
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+age):
                result=self.save(form)
            self.assertFalse(result['saved'])
            self.assertEqual(before,self.state())

    def test_reject_901_seconds_without_writes(self):
        self.rejected_at(901)

    def test_reject_306_days_without_writes(self):
        self.rejected_at(306*86400)

    def accepted_at(self, age):
        with self.app.app_context():
            form=self.prepare()
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+age):
                result=self.save(form)
            self.assertTrue(result['saved']);self.assertFalse(result['replay'])
            self.assertIsNotNone(EmergencyShift.query.one().invalidated_at)

    def test_recent_confirmation(self):
        self.accepted_at(0)

    def test_900_seconds_inclusive(self):
        self.accepted_at(900)

    def invalid_token(self, variant):
        with self.app.app_context():
            form=self.prepare();before=self.state()
            payload=service.signer('review').loads(form['impact_key'])
            if variant=='legacy':
                form['impact_key']=URLSafeSerializer(current_app.config['SECRET_KEY'],salt=service.OPERATION+'review').dumps(payload)
            elif variant=='tampered':
                form['impact_key']='x'+form['impact_key'][1:]
            elif variant=='actor':
                payload[0]=20
                with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued):
                    form['impact_key']=service.signer('review').dumps(payload)
            elif variant=='future':
                with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+1):
                    form['impact_key']=service.signer('review').dumps(payload)
            form['issued_at']=str(self.issued)  # Browser timestamps cannot repair a token.
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued):
                result=self.save(form)
            self.assertFalse(result['saved']);self.assertEqual(before,self.state())

    def test_legacy_untimed_token(self):self.invalid_token('legacy')
    def test_tampered_token(self):self.invalid_token('tampered')
    def test_foreign_actor_token(self):self.invalid_token('actor')
    def test_future_token(self):self.invalid_token('future')

    def test_completed_replay_after_expiry_has_no_duplicate_effects(self):
        with self.app.app_context():
            form=self.prepare()
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+1):
                self.assertTrue(self.save(form)['saved'])
            before=self.state()
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+306*86400):
                self.assertTrue(self.save(form)['replay'])
            self.assertEqual(before,self.state())

    def test_expired_review_even_when_shifts_no_longer_affected(self):
        with self.app.app_context():
            form=self.prepare();before=self.state()
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+901):
                result=service.save(10,form,clock=lambda:datetime(2032,1,1,tzinfo=timezone.utc))
            self.assertFalse(result['saved']);self.assertEqual(result['impact'],[])
            self.assertEqual(before,self.state())

    def test_new_shifts_and_snapshot_still_require_review(self):
        with self.app.app_context():
            form=self.prepare()
            reservations.reserve(10,['2031-01-01-GUARDIA_DIURNA'],True,reservations.issue_key(10))
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+1):
                result=self.save(form)
            self.assertFalse(result['saved']);self.assertEqual(len(result['impact']),2)
            self.save(self.form(notes='Cambio independiente de versión'))
            with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+2):
                with self.assertRaises(service.ConfigurationConflict):self.save(form)
            self.assertTrue(all(s.invalidated_at is None for s in EmergencyShift.query.all()))

    def test_http_expiry_preserves_escaped_fields_and_requires_fresh_acceptance(self):
        path='/profesional/urgencias/configuracion'
        # The test patch also covers Flask's timed session signer; issue that
        # synthetic session on the same controlled clock to keep it authenticated.
        with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued):
            self.login()
        with self.app.app_context():
            form=self.prepare();before=self.state()
        with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+901):
            response=self.client.post(path,data=form)
        self.assertEqual(response.status_code,409)
        self.assertIn(service.IMPACT_EXPIRED_MESSAGE,response.text)
        self.assertIn('&lt;b&gt;Texto sintético&lt;/b&gt;',response.text)
        self.assertIn('value="123.45"',response.text)
        checkbox=re.search(r'<input[^>]*name="accept_impact"[^>]*>',response.text).group()
        self.assertNotIn('checked',checkbox)
        form['impact_key']=html.unescape(re.search(r'name="impact_key" value="([^"]+)"',response.text).group(1))
        with self.app.app_context():self.assertEqual(before,self.state())
        form.pop('accept_impact')
        with patch.object(TimestampSigner,'get_timestamp',return_value=self.issued+902):
            response=self.client.post(path,data=form)
            self.assertEqual(response.status_code,200)
            with self.app.app_context():self.assertEqual(before,self.state())
            form['impact_key']=html.unescape(re.search(r'name="impact_key" value="([^"]+)"',response.text).group(1))
            form['accept_impact']='on'
            self.assertEqual(self.client.post(path,data=form).status_code,303)
        with self.app.app_context():self.assertIsNotNone(EmergencyShift.query.one().invalidated_at)


if __name__=='__main__':unittest.main()
