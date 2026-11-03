"""Urgencias manuales: ownership, truthful availability and protected contact."""
import re
import unittest
from unittest.mock import patch
from tests import test_emergency_entry as fixtures
from app import db
from app.models.professional import Professional
from app.models.whatsapp_contact_session import WhatsAppContactSession
from app.services.operation_view_service import build_emergency_directory_rows


class UrgencyWorkflowTest(unittest.TestCase):
    tearDown = fixtures.EmergencyEntryTest.tearDown
    login = fixtures.EmergencyEntryTest.login
    post = fixtures.EmergencyEntryTest.post
    counts = fixtures.EmergencyEntryTest.counts

    def setUp(self):
        fixtures.EmergencyEntryTest.setUp(self)
        with self.app.app_context():
            db.session.add(Professional(id=1, user_id=3, nombre='Técnico sintético', servicio='Electricidad',
                zona='Villa Lugano', perfil_completo=True, telefono='+5491100001001'))
            db.session.commit()

    def token(self):
        return re.search(r'name="csrf_token" value="([^"]+)"', self.client.get('/urgencias/directorio').text)[1]

    def test_real_request_confirmation_owned_and_read_only(self):
        self.login(1)
        response = self.post()
        self.assertEqual(response.status_code, 302)
        before = self.counts()
        with patch.object(db.session, 'commit') as commit:
            detail = self.client.get(response.location)
            self.assertEqual(detail.status_code, 200)
            self.assertIn('Solicitud #1 registrada', detail.text)
            self.assertIn('no se asignó ni convocó', detail.text)
            commit.assert_not_called()
        self.assertEqual(self.counts(), before)
        for uid in (None, 2, 3):
            with self.client.session_transaction() as session:
                session.clear()
                if uid: session['user_id'] = uid
            self.assertEqual(self.client.get(response.location).status_code, 404)

    def test_directory_no_phone_or_invented_availability(self):
        response = self.client.get('/urgencias/directorio')
        self.assertIn("form-action 'self' https://wa.me;", response.headers['Content-Security-Policy'])
        self.assertIn("form-action 'self';", self.client.get('/urgencias/nueva').headers['Content-Security-Policy'])
        self.assertIn('Disponibilidad por confirmar', response.text)
        for forbidden in ('5491100001001', 'tel:', 'Disponible segun perfil', 'Prioridad PRO', 'Urgencias ilimitadas'):
            self.assertNotIn(forbidden, response.text)
        self.assertIn('name="whatsapp_consent" value="on" required', response.text)
        self.assertIn('<summary>Contactar por WhatsApp</summary>', response.text)

    def test_filters_pagination_empty_and_invalid_request_id(self):
        self.assertIn('Técnico sintético', self.client.get('/urgencias/directorio?categoria=Electricidad&zona=Lugano').text)
        self.assertIn('No encontramos profesionales', self.client.get('/urgencias/directorio?categoria=Desconocido').text)
        self.assertIn('Anterior', self.client.get('/urgencias/directorio?page=2&per_page=1').text)
        self.assertEqual(self.client.get('/urgencias/directorio?page=oops').status_code, 200)
        self.login(1)
        for value in ('NaN', '-1', '999999999999999999999999999'):
            self.assertEqual(self.client.get('/urgencias/directorio?solicitud='+value).status_code, 404)
        self.assertEqual(self.client.get('/urgencias/directorio?solicitud=1&solicitud=2').status_code, 400)

    def test_contact_requires_consent_csrf_and_request_owner(self):
        self.login(1); self.post()
        data = dict(professional_id=1, operation_type='EMERGENCIA', entity_type='EmergencyRequest', entity_id=1)
        self.assertEqual(self.client.post('/whatsapp/iniciar',data=data).status_code, 400)
        data['csrf_token'] = self.token()
        self.assertEqual(self.client.post('/whatsapp/iniciar',data=data).status_code, 400)
        data['whatsapp_consent'] = 'on'
        with self.client.session_transaction() as session: session.clear()
        data['csrf_token'] = self.token()
        self.assertEqual(self.client.post('/whatsapp/iniciar',data=data).status_code, 403)
        self.login(2); data['csrf_token'] = self.token()
        self.assertEqual(self.client.post('/whatsapp/iniciar',data=data).status_code, 403)
        with self.app.app_context():
            db.session.get(fixtures.User, 2).estado = 'ACTIVO'
            db.session.commit()
        self.assertEqual(self.client.get('/urgencias/directorio?solicitud=1').status_code, 404)
        self.assertEqual(self.client.post('/whatsapp/iniciar',data=data).status_code, 403)
        self.login(1); data['csrf_token'] = self.token()
        r = self.client.post('/whatsapp/iniciar',data=data)
        self.assertEqual(r.status_code,302)
        self.assertTrue(r.location.startswith('https://wa.me/'))
        with self.app.app_context():
            self.assertEqual(WhatsAppContactSession.query.count(),1)
            self.assertTrue(WhatsAppContactSession.query.one().consent_given)

    def test_anonymous_contact_without_request_and_professional_pending(self):
        response = self.client.post('/whatsapp/iniciar',data=dict(csrf_token=self.token(),
            professional_id=1,operation_type='EMERGENCIA',whatsapp_consent='on'))
        self.assertEqual(response.status_code,302)
        self.login(3,'PROFESIONAL')
        page = self.client.get('/profesional/oportunidades/urgencias')
        self.assertEqual(page.status_code,200)
        self.assertNotIn('Revisar mi perfil y contacto',page.text)
        self.assertIn('todavía no está habilitada',page.text)
        self.assertEqual(self.client.get('/profesional/oportunidades/urgencias?solicitud=1').status_code,404)

    def test_pro_subscription_does_not_sort_as_availability(self):
        with self.app.app_context(), patch('app.services.operation_view_service.has_pro_access',return_value=True):
            rows = build_emergency_directory_rows('', '', None)
            self.assertTrue(rows[0]['badges']['pro'])
            self.assertEqual(rows[0]['availability']['primary'],'Disponibilidad por confirmar')
            self.assertIsNone(rows[0]['availability']['priority'])
            self.assertIs(rows[0]['phone']['whatsapp'],True)
