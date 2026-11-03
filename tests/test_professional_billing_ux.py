"""PROF-UX-003 presentation only, isolated SQLite fixtures."""
import unittest
from unittest.mock import patch
from sqlalchemy import event
from app import db
from app.models.user import User
import tests.test_professional_workspace_ux as fixtures


class ProfessionalBillingTest(unittest.TestCase):
    setUp = fixtures.ProfessionalWorkspaceTest.setUp
    tearDown = fixtures.ProfessionalWorkspaceTest.tearDown
    login = fixtures.ProfessionalWorkspaceTest.login
    paths = ['/profesional/facturacion' + suffix for suffix in ['', '/factura', '/cobro', '/configuracion']]

    def test_every_destination_requires_active_persisted_professional(self):
        for path in self.paths:
            self.assertEqual(self.client.get(path).status_code, 302)
        self.login(30, 'PROFESIONAL')
        for path in self.paths:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.login()
        for path in self.paths:
            self.assertEqual(self.client.get(path).status_code, 200)
        for state in ['SUSPENDIDO', 'BANEADO']:
            with self.app.app_context():
                db.session.get(User, 10).estado = state
                db.session.commit()
            for path in self.paths:
                self.login()
                self.assertEqual(self.client.get(path).status_code, 302)

    def test_links_destinations_return_and_navigation(self):
        self.login()
        html = self.client.get(self.paths[0]).text
        for path in self.paths[1:]:
            self.assertIn('href="' + path + '"', html)
            prepared = self.client.get(path).text
            self.assertIn('href="/profesional/facturacion" aria-current="page"', prepared)
            self.assertIn('Volver a Facturación y cobros', prepared)
            self.assertIn('Disponible próximamente', prepared)
            self.assertNotIn('name="amount"', prepared)
        self.assertIn('Crear factura', html)
        self.assertIn('Crear cobro', html)
        self.assertNotIn('href="#"', html.split('<main')[1].split('</main>')[0])

    def test_navigation_does_not_write_or_call_financial_services(self):
        self.login()
        statements = []
        def record(conn, cursor, statement, parameters, context, many):
            statements.append(statement.strip().upper())
        with self.app.app_context():
            engine = db.engine
        event.listen(engine, 'before_cursor_execute', record)
        try:
            with patch.object(db.session, 'commit', side_effect=AssertionError('commit')), patch(
                'app.services.payment_order_delivery_service.PaymentOrderDeliveryService.create_order',
                side_effect=AssertionError('financial command')):
                for path in self.paths:
                    self.assertEqual(self.client.get(path).status_code, 200)
            self.assertFalse(any(s.startswith(('INSERT', 'UPDATE', 'DELETE')) for s in statements))
        finally:
            event.remove(engine, 'before_cursor_execute', record)

    def test_unavailable_is_not_empty_paid_or_mock_history(self):
        self.login()
        html = self.client.get(self.paths[0] + '?professional_id=202').text
        main = html.split('<main')[1].split('</main>')[0]
        self.assertIn('Tu historial estará disponible próximamente', main)
        for fake in ['$35.000', '$85.000', '$110.000', 'María G.', 'Diego R.', 'Laura M.', 'Cobrado', 'qr.png']:
            self.assertNotIn(fake, main)
        self.assertNotIn('Otro Técnico', html)
        self.assertNotIn('Trabajo ajeno', html)
        self.assertIn('suscripción a MANDOBRA', main)

    def test_post_is_not_a_financial_action_and_unknown_destination_is_404(self):
        self.login()
        for path in self.paths:
            self.assertEqual(self.client.post(path).status_code, 405)
        self.assertEqual(self.client.get('/profesional/facturacion/emitir').status_code, 404)

    def test_content_and_links_are_server_rendered_without_script_dependency(self):
        self.login(40)
        html = self.client.get(self.paths[0]).text
        self.assertIn('Crear factura', html)
        self.assertIn('professional-workspace-nojs.css', html)
        self.assertIn('professional-notifications.js', html)
        self.assertIn('professional-navigation.js', html)
        self.assertIn('professional-billing.css', html)
        self.assertIn('<details class="pw-mobile-menu">', html)


class CollectionPreparedFallbackTest(unittest.TestCase):
    """Normal application, disposable SQLite: HTTP flags cannot compose a simulator."""
    setUp = fixtures.ProfessionalWorkspaceTest.setUp
    tearDown = fixtures.ProfessionalWorkspaceTest.tearDown
    login = fixtures.ProfessionalWorkspaceTest.login
    paths = (
        '/profesional/facturacion/cobro/1',
        '/profesional/facturacion/cobro/1?enable_simulation=1',
        '/profesional/facturacion/ordenes',
        '/profesional/facturacion/ordenes?simulation=true',
    )

    def assert_prepared_fallback(self, path):
        from app.models.payment_order import PaymentOrder
        from app.models.payment_obligation import PaymentObligation
        from app.models.payment_order_reservation import PaymentOrderReservation
        from app.services.professional_collection_service import simulation_available

        self.login()
        with self.app.app_context():
            engine = db.engine
            self.assertEqual(engine.url.drivername, 'sqlite')
            self.assertIn(engine.url.database, (None, '', ':memory:'))
            self.assertFalse(simulation_available())
        self.assertNotIn('isolated_collection_runtime', self.app.extensions)
        self.assertNotIn('payment_order_delivery_service', self.app.extensions)
        statements = []

        def record(conn, cursor, statement, parameters, context, many):
            statements.append(statement.strip().upper())

        event.listen(engine, 'before_cursor_execute', record)
        try:
            with patch.object(db.session, 'commit', side_effect=AssertionError('GET commit')), patch(
                'app.services.payment_order_delivery_service.PaymentOrderDeliveryService.create_order',
                side_effect=AssertionError('financial command')) as create_order, patch(
                'app.services.in_memory_psp_payment_order_creation_adapter.InMemoryPSPPaymentOrderCreationAdapter.create_payment_order',
                side_effect=AssertionError('adapter call')) as adapter, patch(
                'socket.socket.connect', side_effect=AssertionError('network call')):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, '/profesional/facturacion/cobro')
                prepared = self.client.get(path, follow_redirects=True)
                self.assertEqual(prepared.status_code, 200)
                self.assertEqual(len(prepared.history), 1)
                self.assertEqual(prepared.request.path, '/profesional/facturacion/cobro')
                self.assertIn('Disponible próximamente', prepared.text)
                self.assertNotIn('SIMULACIÓN', prepared.text)
                self.assertNotIn('review_token', prepared.text)
                self.assertNotIn('qr.png', prepared.text)
                create_order.assert_not_called()
                adapter.assert_not_called()
            with self.app.app_context():
                self.assertFalse(simulation_available())
                for model in (PaymentOrder, PaymentObligation, PaymentOrderReservation):
                    self.assertEqual(model.query.count(), 0)
            self.assertFalse(any(s.startswith(('INSERT', 'UPDATE', 'DELETE', 'REPLACE'))
                                 for s in statements))
        finally:
            event.remove(engine, 'before_cursor_execute', record)

    def test_review_falls_back_to_prepared(self):
        self.assert_prepared_fallback(self.paths[0])

    def test_review_query_cannot_enable_simulation(self):
        self.assert_prepared_fallback(self.paths[1])

    def test_history_falls_back_to_prepared(self):
        self.assert_prepared_fallback(self.paths[2])

    def test_history_query_cannot_enable_simulation(self):
        self.assert_prepared_fallback(self.paths[3])

    def test_fallbacks_preserve_anonymous_and_persisted_client_restrictions(self):
        for path in self.paths:
            with self.subTest(actor='anonymous', path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.location.startswith('/login'))
        self.login(30, 'PROFESIONAL')  # Forged session role cannot override persisted CLIENTE.
        for path in self.paths:
            with self.subTest(actor='client', path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
