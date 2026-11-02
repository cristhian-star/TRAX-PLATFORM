"""Isolated integration of the real UI, canonical 4D POST and durable 4B services."""
import re
import unittest
from io import BytesIO
from unittest.mock import patch
import segno
from app import db
from app.models.user import User
from app.models.contract_request import ContractRequest
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.models.payment_effect import PaymentEffectDecision
from app.services.isolated_collection_preview import isolated_app
from app.services.professional_collection_service import simulation_available


class CollectionUXTest(unittest.TestCase):
    def setUp(self):
        self.network = patch('socket.socket.connect', side_effect=AssertionError('external network'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.preview = isolated_app(enable_simulation=True)
        self.app = self.preview.__enter__()
        self.client = self.app.test_client()
        self.login(1)
        self.post_url = '/contratacion/1/orden-de-cobro'
        self.base = '/profesional/facturacion/cobro'

    def tearDown(self):
        self.preview.__exit__(None, None, None)

    def login(self, user):
        with self.client.session_transaction() as session:
            session.clear()
            if user: session['user_id'] = user

    def form(self):
        html = self.client.get(self.base+'/1').text
        return {name: re.search('name="'+name+'" value="([^"]+)"', html).group(1)
                for name in ['csrf_token','review_token']}

    def create(self, **extra):
        return self.client.post(self.post_url, data={**self.form(), **extra})

    def test_selector_owner_and_available_contracts(self):
        html=self.client.get(self.base).text
        self.assertIn('Revisión eléctrica',html)
        self.assertNotIn('Trabajo ajeno',html)
        self.assertNotIn('Trabajo sin confirmar',html)
        self.assertIn('SIMULACIÓN',html)
        for query in ['page=0','page=-1','page=1&page=2','page='+'9'*50]:
            self.assertEqual(self.client.get(self.base+'?'+query).status_code,400)

    def test_roles_direct_urls_and_inactive(self):
        for user,status in [(None,302),(2,403),(3,403)]:
            self.login(user)
            self.assertEqual(self.client.get(self.base+'/1').status_code,status)
            self.assertEqual(self.client.get(self.post_url).status_code,status)
        self.login(1)
        with self.app.app_context():
            db.session.get(User,1).estado='SUSPENDIDO';db.session.commit()
        self.assertEqual(self.client.get(self.base).status_code,302)

    def test_confirmation_revalidates_amount_state_owner_and_csrf(self):
        form=self.form()
        self.assertEqual(self.client.post(self.post_url,data={'review_token':form['review_token']}).status_code,400)
        with self.app.app_context():
            c=db.session.get(ContractRequest,1);c.precio_acordado=1500;db.session.commit()
        self.assertEqual(self.client.post(self.post_url,data=form).status_code,409)
        form=self.form()
        with self.app.app_context():
            db.session.get(ContractRequest,1).estado='EN_PROGRESO';db.session.commit()
        self.assertEqual(self.client.post(self.post_url,data=form).status_code,403)
        with self.app.app_context():
            self.assertEqual(PaymentOrder.query.count(),0)

    def test_replay_uses_same_order_canonical_amount_and_exact_qr(self):
        form=self.form()
        for _ in range(2):
            response=self.client.post(self.post_url,data={**form,'amount':'1','currency':'USD','professional_id':'2','next':'https://example.test'})
            self.assertEqual(response.status_code,303)
            self.assertEqual(response.location,self.post_url)
        result=self.client.get(self.post_url)
        self.assertIn('ARS 1250.50',result.text)
        self.assertIn('professional-workspace.css',result.text)
        with self.app.app_context():
            self.assertEqual(PaymentOrder.query.count(),1)
            self.assertEqual(PaymentOrderReservation.query.count(),1)
            self.assertEqual(PaymentEffectDecision.query.count(),0)
            url=PaymentOrder.query.one().checkout_url
        self.assertIn('value="'+url+'"',result.text)
        qr=self.client.get(self.post_url+'/qr.png')
        buffer=BytesIO();segno.make_qr(url,error='m').save(buffer,kind='png',scale=5,border=4,dark='black',light='white')
        self.assertEqual(qr.data,buffer.getvalue())
        self.assertEqual(qr.headers['Cache-Control'],'no-store, private')
        self.assertEqual(result.headers['Referrer-Policy'],'no-referrer')

    def test_reads_do_not_create_or_call_provider(self):
        runtime=self.app.extensions['isolated_collection_runtime']
        with patch.object(runtime.delivery._application._adapter,'create_payment_order',side_effect=AssertionError('provider')):
            for path in [self.base,self.base+'/1','/profesional/facturacion/ordenes',self.post_url,self.post_url+'/qr.png']:
                self.client.get(path)
        with self.app.app_context(): self.assertEqual(PaymentOrder.query.count(),0)

    def test_history_empty_own_error_and_unavailable(self):
        history='/profesional/facturacion/ordenes'
        self.assertIn('Todavía no generaste',self.client.get(history).text)
        self.create()
        self.assertIn('ACTIVE',self.client.get(history).text)
        self.login(3)
        self.assertNotIn('Orden #1',self.client.get(history).text)
        self.login(1)
        from sqlalchemy.exc import SQLAlchemyError
        with patch('app.services.professional_collection_service.require_active_actor',side_effect=SQLAlchemyError('private details')):
            response=self.client.get(history)
            self.assertIn('Reintentar consulta',response.text)
            self.assertNotIn('private details',response.text)
        self.app.extensions.pop('payment_order_delivery_service')
        self.assertIn('Disponible próximamente',self.client.get(self.base).text)

    def test_uncertainty_preserves_claim_and_has_no_retry(self):
        runtime=self.app.extensions['isolated_collection_runtime']
        adapter=runtime.delivery._application._adapter
        form=self.form()
        with patch.object(adapter,'create_payment_order',side_effect=TimeoutError) as call:
            self.assertEqual(self.client.post(self.post_url,data=form).status_code,409)
            self.assertEqual(self.client.post(self.post_url,data=form).status_code,409)
            self.assertEqual(call.call_count,1)
        with self.app.app_context():
            self.assertEqual(PaymentOrderReservation.query.count(),1)
            self.assertIn(PaymentOrderReservation.query.one().status,['UNCERTAIN','CALL_IN_PROGRESS'])
        self.assertIn('Generación bloqueada',self.client.get('/profesional/facturacion/ordenes').text)
        self.assertNotIn('Confirmar generación simulada',self.client.get(self.base+'/1').text)
        r=self.client.get(self.post_url)
        self.assertNotIn('collection-url',r.text)
        self.assertNotIn('/qr.png',r.text)

    def test_cancelled_order_cannot_deliver(self):
        self.create()
        with self.app.app_context():
            order=PaymentOrder.query.one()
            order.status='CANCELLED';order.cancelled_at=order.created_at;order.closed_at=order.created_at
            db.session.commit()
        self.assertEqual(self.client.get(self.post_url).status_code,410)
        self.assertEqual(self.client.get(self.post_url+'/qr.png').status_code,410)

    def test_factory_fails_closed_and_never_uses_environment_database(self):
        with self.assertRaises(ValueError):
            with isolated_app(): pass
        with self.app.app_context():
            self.assertTrue(simulation_available())
            self.app.config['TESTING']=False
            self.assertFalse(simulation_available())
            self.app.config['TESTING']=True
            self.assertFalse(self.app.extensions['isolated_collection_runtime'].valid(object()))
        self.assertFalse(self.app.config['PAYMENT_EFFECTS_ENABLED'])
        self.assertFalse(self.app.config['MERCADOPAGO_ORDER_RECONCILIATION_ENABLED'])
        self.assertFalse(self.app.config['MERCADOPAGO_ORDER_WEBHOOK_ENABLED'])

    def test_context_owner_change_is_denied_after_review(self):
        form=self.form()
        with self.app.app_context():
            db.session.get(ContractRequest,1).professional_user_id=3
            db.session.commit()
        self.assertEqual(self.client.post(self.post_url,data=form).status_code,403)
        with self.app.app_context(): self.assertEqual(PaymentOrder.query.count(),0)

    def test_expired_order_and_reads_after_success_do_not_call_provider(self):
        from datetime import datetime,timezone,timedelta
        self.create()
        runtime=self.app.extensions['isolated_collection_runtime']
        with patch.object(runtime.delivery._application._adapter,'create_payment_order',side_effect=AssertionError('read calls PSP')):
            self.assertEqual(self.client.get(self.post_url).status_code,200)
            self.assertEqual(self.client.get(self.post_url+'/qr.png').status_code,200)
            self.assertEqual(self.client.get('/profesional/facturacion/ordenes').status_code,200)
        runtime.delivery._clock=lambda: datetime.now(timezone.utc)+timedelta(days=4)
        self.assertEqual(self.client.get(self.post_url).status_code,410)
        self.assertEqual(self.client.get(self.post_url+'/qr.png').status_code,410)

    def test_environment_cannot_select_shared_database(self):
        import os
        from pathlib import Path
        with patch.dict(os.environ, {'DATABASE_URL':'postgresql://invalid.invalid/shared','E2E_DEMO_ENABLED':'true'}):
            with isolated_app(enable_simulation=True) as other:
                self.assertTrue(other.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'))
                self.assertFalse(other.config['E2E_DEMO_ENABLED'])
                location=Path(other.config['SQLALCHEMY_DATABASE_URI'][10:])
                self.assertTrue(location.exists())
            self.assertFalse(location.exists())

    def test_price_change_after_http_review_is_rejected_by_existing_prepare_hook(self):
        form=self.form()
        import app.services.professional_collection_service as view
        original=view.check_review
        def change_after_review(*args):
            card=original(*args)
            db.session.get(ContractRequest,1).precio_acordado=1800
            db.session.commit()
            return card
        with patch.object(view,'check_review',side_effect=change_after_review):
            self.assertEqual(self.client.post(self.post_url,data=form).status_code,409)
        with self.app.app_context():
            self.assertEqual(PaymentOrder.query.count(),0)
            self.assertEqual(PaymentOrderReservation.query.count(),0)
