from datetime import timedelta
from decimal import Decimal
from html.parser import HTMLParser
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image
import segno
from flask import g

from app import create_app, db
from app.config.config import Config, TestingConfig
from app.models.contract_request import ContractRequest
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.models.professional import Professional
from app.models.user import User
from app.services import mercadopago_payment_query_http as http
from app.services.mercadopago_order_creation_adapter import (
    MercadoPagoOrderConfiguration, ProfessionalOAuthCredential,
)
from app.services.payment_order_delivery_service import build_checkout_delivery_service
from tests.test_payment_order_application import TrackingSessionFactory, seed_contract
from tests.test_mercadopago_order_creation_adapter import NOW, TOKEN, URL


class CheckoutHTML(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.inputs = {}
        self.links = []
        self.images = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input":
            self.inputs[attrs.get("name")] = attrs.get("value")
        if tag == "a":
            self.links.append(attrs.get("href"))
        if tag == "img":
            self.images.append(attrs.get("src"))


class PaymentOrderDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = (Path(self.temporary.name) / "delivery.db").as_posix()

        class LocalConfig(TestingConfig):
            WTF_CSRF_ENABLED = True
            CHECKOUT_PRO_DELIVERY_ENABLED = True

            @classmethod
            def apply_runtime_config(cls, config):
                super().apply_runtime_config(config)
                config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{path}"

        self.app = create_app(config_class=LocalConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.engine = db.engine
        self.factory = TrackingSessionFactory(self.engine)
        self.actor, self.customer, self.other, self.professional, self.contract = seed_contract(self.factory.Session)
        self.now = NOW
        self.oauth = Mock(return_value=ProfessionalOAuthCredential(self.professional, TOKEN, False, "ARS"))
        self.fee = Mock(return_value=Decimal("25.00"))
        self.transport = Mock(side_effect=self.response)
        self.delivery = self.build_service()
        self.app.extensions["payment_order_delivery_service"] = self.delivery
        self.client = self.app.test_client()
        self.path = f"/contratacion/{self.contract}/orden-de-cobro"
        self.login(self.actor)

    def tearDown(self):
        db.session.remove()
        self.engine.dispose()
        self.context.pop()
        self.temporary.cleanup()

    def build_service(self, **changes):
        settings = dict(session_factory=self.factory, oauth_provider=self.oauth,
                        commission_policy=self.fee, transport=self.transport,
                        configuration=MercadoPagoOrderConfiguration(enabled=True),
                        clock=lambda: self.now)
        settings.update(changes)
        return build_checkout_delivery_service(**settings)

    def response(self, **request):
        self.assertEqual(self.factory.open_sessions, 0)
        self.assertEqual(self.engine.pool.checkedout(), 0)
        payload = json.loads(request["body"])
        return http.MercadoPagoHTTPResponse(201, (("Content-Type", "application/json"),),
            json.dumps(dict(id="ORD123", checkout_url=URL, currency="ARS",
                            external_reference=payload["external_reference"],
                            total_amount=payload["total_amount"])).encode())

    def login(self, actor):
        # This fixture holds an outer app context; clear Flask-WTF's per-context
        # cache when changing the session so the next token belongs to that actor.
        g.pop("csrf_token", None)
        with self.client.session_transaction() as session:
            session.clear()
            if actor is not None:
                session["user_id"] = actor

    def csrf(self):
        return CheckoutHTML(self.client.get("/login").get_data(as_text=True)).inputs["csrf_token"]

    def post(self, **extra):
        return self.client.post(self.path, data={"csrf_token": self.csrf(), **extra})

    def counts(self):
        with self.factory.Session() as session:
            return tuple(session.query(model).count() for model in (
                PaymentObligation, PaymentOrderReservation, PaymentOrder,
            ))

    def assert_private(self, response):
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_creation_double_submit_refresh_and_exact_qr_link(self):
        for _ in range(2):
            response = self.post()
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["Location"], self.path)
            self.assert_private(response)
        for _ in range(2):
            page = self.client.get(self.path)
            self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        parsed = CheckoutHTML(html)
        self.assertIn(URL, parsed.links)
        self.assertIn(self.path + "/qr.png", parsed.images)
        self.assertIn("no confirma un pago", html)
        self.assertNotIn(TOKEN, html)
        self.assertNotIn("creation-", html)
        self.assert_private(page)
        with patch("app.services.payment_order_delivery_service.segno.make_qr", wraps=segno.make_qr) as encoder:
            png = self.client.get(self.path + "/qr.png")
        encoder.assert_called_once_with(URL, error="m")
        self.assertEqual(png.status_code, 200)
        self.assertEqual(png.mimetype, "image/png")
        self.assertTrue(png.data.startswith(b"\x89PNG\r\n\x1a\n"))
        image = Image.open(BytesIO(png.data))
        image.verify()
        expected = BytesIO()
        segno.make_qr(URL, error="m").save(expected, kind="png", scale=5, border=4,
                                        dark="black", light="white")
        self.assertEqual(png.data, expected.getvalue())
        self.assert_private(png)
        self.assertNotIn("ETag", png.headers)
        self.assertEqual(self.counts(), (1, 1, 1))
        self.transport.assert_called_once()
        self.oauth.assert_called_once_with(self.professional)
        self.fee.assert_called_once()

    def test_get_without_order_never_creates_or_calls_providers(self):
        for path in (self.path, self.path + "/qr.png"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 503)
            self.assert_private(response)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.transport.assert_not_called()
        self.oauth.assert_not_called()

    def test_anonymous_all_endpoints_redirect_without_side_effects(self):
        self.login(None)
        # Regenerate CSRF for the anonymous session.
        token = self.csrf()
        for method, path in (("GET", self.path), ("GET", self.path + "/qr.png"), ("POST", self.path)):
            response = self.client.open(path, method=method, data={"csrf_token": token})
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.headers["Location"])
            self.assert_private(response)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.transport.assert_not_called()

    def test_customer_and_other_professional_have_no_access(self):
        self.assertEqual(self.post().status_code, 303)
        for actor in (self.customer, self.other):
            self.login(actor)
            for method, path in (("GET", self.path), ("GET", self.path + "/qr.png"), ("POST", self.path)):
                response = self.client.open(path, method=method, data={"csrf_token": self.csrf()})
                self.assertEqual(response.status_code, 403)
                self.assertNotIn(URL, response.get_data(as_text=True))
                self.assert_private(response)
        self.transport.assert_called_once()

    def test_inactive_actor_is_rejected(self):
        with self.factory.Session.begin() as session:
            session.get(User, self.actor).estado = "INACTIVO"
        db.session.remove()
        self.assertEqual(self.client.get(self.path).status_code, 302)
        self.transport.assert_not_called()

    def test_profile_owner_and_confirmed_state_rechecked(self):
        for field, value in (("professional_user_id", self.other), ("estado", "COMPLETADA")):
            with self.factory.Session.begin() as session:
                setattr(session.get(ContractRequest, self.contract), field, value)
            self.assertEqual(self.post().status_code, 403)
            with self.factory.Session.begin() as session:
                contract = session.get(ContractRequest, self.contract)
                contract.professional_user_id, contract.estado = self.actor, "CONFIRMADA"
        with self.factory.Session.begin() as session:
            session.get(Professional, self.professional).user_id = self.other
        self.assertEqual(self.post().status_code, 403)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.transport.assert_not_called()

    def test_csrf_missing_or_invalid_is_400_without_claim(self):
        for data in ({}, {"csrf_token": "invalid"}):
            response = self.client.post(self.path, data=data)
            self.assertEqual(response.status_code, 400)
            self.assert_private(response)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.transport.assert_not_called()

    def test_feature_flag_false_and_non_boolean_fail_closed(self):
        for flag in (False, "true", 1):
            self.app.config["CHECKOUT_PRO_DELIVERY_ENABLED"] = flag
            for method, path in (("GET", self.path), ("GET", self.path + "/qr.png"), ("POST", self.path)):
                response = self.client.open(path, method=method, data={"csrf_token": self.csrf()})
                self.assertEqual(response.status_code, 503)
                self.assert_private(response)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.oauth.assert_not_called()
        self.transport.assert_not_called()

    def test_defaults_and_missing_composition_make_no_psp_call(self):
        self.assertFalse(Config.CHECKOUT_PRO_DELIVERY_ENABLED)
        with patch.dict(os.environ, {}, clear=True):
            config = {}
            Config.apply_runtime_config(config)
            self.assertIs(config["CHECKOUT_PRO_DELIVERY_ENABLED"], False)
        self.app.extensions.pop("payment_order_delivery_service")
        self.assertEqual(self.post().status_code, 503)
        self.app.extensions["payment_order_delivery_service"] = self.build_service(configuration=None)
        self.assertEqual(self.post().status_code, 503)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.oauth.assert_not_called()
        self.transport.assert_not_called()

    def test_oauth_and_commission_failure_before_claim_are_neutral(self):
        for provider in (self.oauth, self.fee):
            provider.side_effect = RuntimeError(TOKEN)
            response = self.post()
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(TOKEN, response.get_data(as_text=True))
            provider.side_effect = None
            self.assertEqual(self.counts(), (0, 0, 0))
        self.transport.assert_not_called()

    def test_browser_fields_cannot_override_command_or_identity(self):
        self.assertEqual(self.post(amount="1.00", professional_id=self.other,
                                   actor_user_id=self.other, idempotency_key="browser-key").status_code, 303)
        request = self.transport.call_args.kwargs
        self.assertEqual(json.loads(request["body"])["total_amount"], "1250.50")
        self.assertNotEqual(request["headers"]["X-Idempotency-Key"], "browser-key")
        self.oauth.assert_called_once_with(self.professional)

    def test_expired_checkout_post_and_qr_never_delivered_or_renewed(self):
        self.assertEqual(self.post().status_code, 303)
        self.now += timedelta(hours=72)
        for response in (self.client.get(self.path), self.client.get(self.path + "/qr.png"), self.post()):
            self.assertEqual(response.status_code, 410)
            self.assertNotIn(URL, response.get_data(as_text=True))
            self.assert_private(response)
        self.transport.assert_called_once()
        self.assertEqual(self.counts(), (1, 1, 1))

    def test_cancelled_checkout_not_delivered(self):
        self.assertEqual(self.post().status_code, 303)
        with self.factory.Session.begin() as session:
            order = session.query(PaymentOrder).one()
            order.status = "CANCELLED"
            order.closed_at = order.cancelled_at = (NOW + timedelta(hours=1)).replace(tzinfo=None)
        for response in (self.client.get(self.path), self.client.get(self.path + "/qr.png"), self.post()):
            self.assertEqual(response.status_code, 410)
        self.transport.assert_called_once()

    def test_timeout_then_replay_keeps_key_and_block(self):
        self.transport.side_effect = TimeoutError(TOKEN)
        response = self.post()
        self.assertEqual(response.status_code, 409)
        with self.factory.Session() as session:
            reservation = session.query(PaymentOrderReservation).one()
            original_key = reservation.idempotency_key
            self.assertEqual(reservation.status, "UNCERTAIN")
        for response in (self.post(), self.client.get(self.path), self.client.get(self.path + "/qr.png")):
            self.assertEqual(response.status_code, 409)
            self.assertNotIn(TOKEN, response.get_data(as_text=True))
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().idempotency_key, original_key)
        self.transport.assert_called_once()
        self.assertEqual(self.counts(), (1, 1, 0))

    def test_in_progress_claim_has_no_qr_or_second_call(self):
        self.transport.side_effect = TimeoutError(TOKEN)
        self.post()
        with self.factory.Session.begin() as session:
            reservation = session.query(PaymentOrderReservation).one()
            reservation.status, reservation.finished_at = "CALL_IN_PROGRESS", None
        for response in (self.post(), self.client.get(self.path), self.client.get(self.path + "/qr.png")):
            self.assertEqual(response.status_code, 409)
        self.transport.assert_called_once()

    def test_get_does_not_recheck_providers_or_confirm_payment(self):
        self.post()
        self.oauth.side_effect = AssertionError("no OAuth on GET")
        self.fee.side_effect = AssertionError("no commission on GET")
        self.assertEqual(self.client.get(self.path).status_code, 200)
        self.assertEqual(self.client.get(self.path + "/qr.png").status_code, 200)
        self.transport.assert_called_once()
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrder).one().status, "ACTIVE")
            self.assertEqual(session.get(ContractRequest, self.contract).estado, "CONFIRMADA")

    def test_hostile_persisted_url_never_presented_or_encoded(self):
        self.post()
        for url in ("https://evil.test/", "https://evil.test@www.mercadopago.com.ar/", "javascript:alert(1)",
                    "https://www.mercadopago.com.ar:SENSITIVE_PORT/"):
            with self.factory.Session.begin() as session:
                session.query(PaymentOrder).one().checkout_url = url
            with patch("app.services.payment_order_delivery_service.segno.make_qr") as encoder:
                for path in (self.path, self.path + "/qr.png"):
                    response = self.client.get(path)
                    self.assertNotEqual(response.status_code, 200)
                    self.assertNotIn(url, response.get_data(as_text=True))
                    self.assertNotIn("SENSITIVE_PORT", response.get_data(as_text=True))
                encoder.assert_not_called()
        self.transport.assert_called_once()

    def test_expiration_during_qr_generation_returns_no_image(self):
        self.post()
        real_encoder = segno.make_qr

        def slow_encoder(*args, **kwargs):
            image = real_encoder(*args, **kwargs)
            self.now += timedelta(hours=72)
            return image

        with patch("app.services.payment_order_delivery_service.segno.make_qr", side_effect=slow_encoder):
            response = self.client.get(self.path + "/qr.png")
        self.assertEqual(response.status_code, 410)
        self.assertNotEqual(response.mimetype, "image/png")
        self.transport.assert_called_once()

    def test_expiration_during_template_render_returns_no_checkout(self):
        self.post()
        from app.routes import payment_order_delivery_routes as routes
        render = routes.render_template

        def slow_render(*args, **kwargs):
            page = render(*args, **kwargs)
            if kwargs.get("checkout") is not None:
                self.now += timedelta(hours=72)
            return page

        with patch.object(routes, "render_template", side_effect=slow_render):
            response = self.client.get(self.path)
        self.assertEqual(response.status_code, 410)
        self.assertNotIn(URL, response.get_data(as_text=True))

    def test_unexpected_errors_do_not_expose_secrets(self):
        with patch.object(self.delivery, "create_order", side_effect=RuntimeError(TOKEN)):
            response = self.post()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(TOKEN, response.get_data(as_text=True))
        self.assert_private(response)

    def test_contract_button_and_disabled_message(self):
        page = self.client.get(f"/contratacion/{self.contract}").get_data(as_text=True)
        self.assertIn(self.path, page)
        self.assertIn('name="csrf_token"', page)
        self.app.config["CHECKOUT_PRO_DELIVERY_ENABLED"] = False
        page = self.client.get(f"/contratacion/{self.contract}").get_data(as_text=True)
        self.assertNotIn(self.path, page)
        self.assertIn("Checkout no disponible", page)

    def test_large_amount_is_presented_without_float_rounding(self):
        from app.services.payment_order_delivery_service import CheckoutPresentation
        amount = Decimal("12345678901234567890.12")
        checkout = CheckoutPresentation(amount, NOW + timedelta(hours=72), URL)
        from decimal import localcontext
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(checkout.amount_text, "12345678901234567890.12")

    def test_changed_price_is_conflict_without_new_call(self):
        self.post()
        with self.factory.Session.begin() as session:
            session.get(ContractRequest, self.contract).precio_acordado = Decimal("1250.51")
        for response in (self.post(), self.client.get(self.path), self.client.get(self.path + "/qr.png")):
            self.assertEqual(response.status_code, 409)
            self.assertNotIn(URL, response.get_data(as_text=True))
        self.transport.assert_called_once()

    def test_hostile_or_malformed_remote_success_keeps_block(self):
        self.transport.side_effect = None
        self.transport.return_value = http.MercadoPagoHTTPResponse(
            201, (("Content-Type", "application/json"),), b'{"checkout_url":"SENSITIVE_BAD_URL"}',
        )
        for response in (self.post(), self.post(), self.client.get(self.path + "/qr.png")):
            self.assertEqual(response.status_code, 409)
            self.assertNotIn("SENSITIVE_BAD_URL", response.get_data(as_text=True))
        self.transport.assert_called_once()
        self.assertEqual(self.counts(), (1, 1, 0))

    def test_qr_is_revalidated_even_with_conditional_headers(self):
        self.post()
        response = self.client.get(self.path + "/qr.png", headers={"If-None-Match": "old"})
        self.assertEqual(response.status_code, 200)
        self.now += timedelta(hours=72)
        response = self.client.get(self.path + "/qr.png", headers={"If-None-Match": "old"})
        self.assertEqual(response.status_code, 410)
        self.assert_private(response)
        self.transport.assert_called_once()

    def test_query_escaping_preserves_exact_url_in_link_and_qr(self):
        url = URL + "&source=professional"

        def response_with_query(**request):
            response = self.response(**request)
            payload = json.loads(response.body)
            payload["checkout_url"] = url
            return http.MercadoPagoHTTPResponse(response.status_code, response.headers,
                                               json.dumps(payload).encode())

        self.transport.side_effect = response_with_query
        self.assertEqual(self.post().status_code, 303)
        html = self.client.get(self.path).get_data(as_text=True)
        self.assertIn("&amp;source=professional", html)
        self.assertIn(url, CheckoutHTML(html).links)
        with patch("app.services.payment_order_delivery_service.segno.make_qr", wraps=segno.make_qr) as encoder:
            self.assertEqual(self.client.get(self.path + "/qr.png").status_code, 200)
        encoder.assert_called_once_with(url, error="m")
        self.transport.assert_called_once()


if __name__ == "__main__":
    unittest.main()
