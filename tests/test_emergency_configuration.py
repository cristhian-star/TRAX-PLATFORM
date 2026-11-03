import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch
from tests import test_emergency_reservations as fixtures
from app import db
from app.models.professional import Professional
from app.models.emergency_configuration import EmergencyConfiguration
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.services import emergency_configuration_service as service
from app.services import emergency_reservation_service as reservations


class ConfigurationTest(unittest.TestCase):
    setUp = fixtures.ReservationTest.setUp
    tearDown = fixtures.ReservationTest.tearDown
    login = fixtures.ReservationTest.login
    enable = fixtures.ReservationTest.enable

    def form(self, **values):
        _, form = service.initial(10)
        form.update(values)
        return form

    def save(self, form):
        return service.save(10,form,clock=lambda:datetime(2030,12,30,12,tzinfo=timezone.utc))

    def test_modes_free_incomplete_and_inapplicable_values(self):
        with self.app.app_context():
            self.save(self.form(package_amount='123.45',visit_amount='NaN'))
            config = db.session.get(EmergencyConfiguration,101)
            self.assertEqual(config.package_amount,Decimal('123.45'))
            self.save(self.form(mode='SEPARATE',visit_amount_free='on',diagnosis_amount='',package_amount='Infinity'))
            config = db.session.get(EmergencyConfiguration,101)
            self.assertEqual(config.visit_amount,0); self.assertIsNone(config.diagnosis_amount)
            self.assertIsNone(config.package_amount)
            self.assertTrue(config.repair_materials_separate)

    def test_invalid_amounts_each_applicable_field(self):
        with self.app.app_context():
            for field in service.AMOUNTS:
                for value in ('NaN','sNaN','Infinity','-Infinity','-1','abc','1.000,50','10000000000','1.234','0'):
                    with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                        self.save(self.form(mode='PACKAGE' if field=='package_amount' else 'SEPARATE',**{field:value}))
            self.assertEqual(EmergencyConfiguration.query.count(),0)

    def test_tariffs_only_and_noop_preserve_shifts_coordinates_and_consent(self):
        with self.app.app_context():
            self.enable()
            p=db.session.get(Professional,101);p.latitude=-34.6;p.longitude=-58.4;p.coverage_location_consent_at=datetime(2030,1,1);db.session.commit()
            reservations.reserve(10,['2030-12-31-GUARDIA_DIURNA'],True,reservations.issue_key(10))
            form=self.form(package_amount='200',notes='Tarifa QA')
            for field in service.COVERAGE: form.pop(field,None)
            self.save(form)
            self.save(self.form())
            p=db.session.get(Professional,101)
            self.assertEqual(p.latitude,-34.6);self.assertEqual(p.coverage_location_consent_at,datetime(2030,1,1))
            self.assertIsNone(EmergencyShift.query.one().invalidated_at)

    def test_impact_revalidated_and_atomic(self):
        with self.app.app_context():
            self.enable()
            reservations.reserve(10,['2030-12-31-GUARDIA_DIURNA'],True,reservations.issue_key(10))
            form=self.form(coverage_city='Otra zona')
            review=self.save(form);self.assertFalse(review['saved']);self.assertEqual(len(review['impact']),1)
            self.assertEqual(db.session.get(Professional,101).coverage_city,'CABA')
            reservations.reserve(10,['2031-01-01-GUARDIA_DIURNA'],True,reservations.issue_key(10))
            form.update(impact_key=review['impact_key'],accept_impact='on')
            revised=self.save(form);self.assertFalse(revised['saved']);self.assertEqual(len(revised['impact']),2)
            form['impact_key']=revised['impact_key']
            with patch.object(db.session,'commit',side_effect=RuntimeError('rollback')):
                with self.assertRaises(RuntimeError): self.save(form)
            self.assertTrue(all(s.invalidated_at is None for s in EmergencyShift.query.all()))
            self.assertEqual(db.session.get(Professional,101).coverage_city,'CABA')
            self.assertTrue(self.save(form)['saved'])
            self.assertTrue(all(s.invalidated_at for s in EmergencyShift.query.all()))
            self.assertTrue(all(r.status=='SKIPPED' for r in EmergencyShiftReminder.query.all()))
            self.assertTrue(self.save(form)['replay'])
            self.assertEqual(OperationCommand.query.filter_by(operation=service.OPERATION).count(),1)

    def test_stale_form_and_explicit_coordinate_actions(self):
        with self.app.app_context():
            old=self.form()
            with self.assertRaises(ValueError): self.save(self.form(coordinate_action='update',latitude='-34',longitude='-58'))
            self.save(self.form(coordinate_action='update',latitude='-34',longitude='-58',coverage_location_consent='on'))
            with self.assertRaises(service.ConfigurationConflict): self.save(old)
            self.save(self.form(coordinate_action='remove'))
            self.assertIsNone(db.session.get(Professional,101).latitude)
            self.assertIsNone(db.session.get(Professional,101).coverage_location_consent_at)

    def test_http_access_csrf_error_escape_and_get_readonly(self):
        path='/profesional/urgencias/configuracion'
        self.assertEqual(self.client.get(path).status_code,302)
        self.login(30,'PROFESIONAL');self.assertEqual(self.client.get(path).status_code,403)
        self.login()
        with patch.object(db.session,'commit',side_effect=AssertionError('GET write')):
            self.assertEqual(self.client.get(path).status_code,200)
        with self.app.app_context(): form=self.form(package_amount='NaN',notes='<script>unsafe</script>')
        response=self.client.post(path,data=form)
        self.assertEqual(response.status_code,400);self.assertIn('&lt;script&gt;',response.text)
        form['package_amount']='10'
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post(path,data=form).status_code,400)
        self.app.config['WTF_CSRF_ENABLED']=False
        self.login(20)
        self.assertEqual(self.client.post(path,data=form).status_code,400)
        self.login()
        self.assertEqual(self.client.post(path,data=form).status_code,303)
        self.assertIn('Configuración de urgencias',self.client.get('/profesional/perfil/completar').text)
        for view in ('solicitudes','guardias'):
            self.assertIn('href="'+path+'"',self.client.get('/profesional/oportunidades/urgencias?vista='+view).text)

    def test_canonical_radius_limits_coordinates_and_public_approximation(self):
        from app.services.coverage_service import obtener_centro_publico_aproximado
        with self.app.app_context():
            for radius in ('0','201','1.5','NaN'):
                with self.assertRaises(ValueError):self.save(self.form(coverage_radius_km=radius))
            for lat,lng in [('NaN','-58'),('91','-58'),('-34','181')]:
                with self.assertRaises(ValueError):self.save(self.form(coordinate_action='update',latitude=lat,longitude=lng,coverage_location_consent='on'))
            self.save(self.form(coverage_radius_km='200',coordinate_action='update',latitude='-34.612345',longitude='-58.412345',coverage_location_consent='on'))
            p=db.session.get(Professional,101)
            self.assertEqual(p.coverage_radius_km,200)
            self.assertNotEqual(obtener_centro_publico_aproximado(p),(p.latitude,p.longitude))

    def test_replay_does_not_bypass_persisted_inactive_account(self):
        from app.models.user import User
        with self.app.app_context():
            form=self.form(package_amount='100');self.save(form)
            db.session.get(User,10).estado='SUSPENDIDO';db.session.commit()
            with self.assertRaises(PermissionError):self.save(form)


if __name__=='__main__': unittest.main()
