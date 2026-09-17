from datetime import timedelta
from decimal import Decimal
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app import create_app, db
from app.config.config import TestingConfig
from app.models.audit_log import AuditLog
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reservation import PaymentOrderReservation
from app.services import mercadopago_payment_query_http as http
from app.services.mercadopago_order_creation_adapter import (
    MercadoPagoOrderConfiguration, MercadoPagoOrderConfigurationError,
    ProfessionalOAuthCredential, build_mercadopago_order_service,
)
from app.services.payment_order_application_service import PaymentOrderExpiredError
from app.services.psp_payment_order_contract import PaymentOrderCreationUncertainError
from tests.test_payment_order_application import TrackingSessionFactory, seed_contract
from tests.test_mercadopago_order_creation_adapter import NOW, TOKEN, URL


class OrderApplicationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = (Path(self.temporary.name) / "orders.db").as_posix()

        class LocalConfig(TestingConfig):
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
        self.actor, _, _, self.professional, self.contract = seed_contract(self.factory.Session)
        self.now = NOW
        self.oauth = Mock(side_effect=self._credential)
        self.fee = Mock(side_effect=self._commission)
        self.transport = Mock(side_effect=self._response)
        self.configuration = MercadoPagoOrderConfiguration(enabled=True)
        self.service = self._service()

    def tearDown(self):
        db.session.remove()
        self.engine.dispose()
        self.context.pop()
        self.temporary.cleanup()

    def _credential(self, professional):
        self.assertEqual(professional, self.professional)
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        return ProfessionalOAuthCredential(professional, TOKEN, False, "ARS")

    def _commission(self, command):
        self.assertEqual(command.professional_id, self.professional)
        self.assertEqual(command.amount, Decimal("1250.50"))
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        return Decimal("25")

    def _response(self, **request):
        self.assertEqual(self.factory.open_sessions, 0)
        self.assertEqual(self.engine.pool.checkedout(), 0)
        with self.factory.Session() as session:
            claim = session.query(PaymentOrderReservation).one()
            self.assertEqual(claim.status, "CALL_IN_PROGRESS")
            self.assertEqual(request["headers"]["X-Idempotency-Key"], claim.idempotency_key)
            payload = json.loads(request["body"])
            self.assertEqual(payload["external_reference"], claim.external_reference)
            self.assertEqual(payload["expiration_time"], "PT72H")
            self.assertEqual(request["headers"]["Authorization"], f"Bearer {TOKEN}")
            self.assertNotIn("Sensitive service description", request["body"].decode())
            return http.MercadoPagoHTTPResponse(201, (("Content-Type", "application/json"),),
                json.dumps({
                    "id": "ORD123", "checkout_url": URL, "currency": "ARS",
                    "total_amount": payload["total_amount"],
                    "external_reference": claim.external_reference,
                    "created_date": (self.now + timedelta(seconds=2)).isoformat(),
                }).encode())

    def _service(self, **changes):
        kwargs = dict(
            session_factory=self.factory, configuration=self.configuration,
            oauth_provider=self.oauth, commission_policy=self.fee,
            transport=self.transport, clock=lambda: self.now,
        )
        kwargs.update(changes)
        return build_mercadopago_order_service(**kwargs)

    def create(self):
        return self.service.create_order(actor_user_id=self.actor, contract_request_id=self.contract)

    def counts(self):
        with self.factory.Session() as session:
            return tuple(session.query(model).count() for model in (
                PaymentObligation, PaymentOrderReservation, PaymentOrder, AuditLog
            ))

    def test_http_adapter_to_application_persistence_and_restart_replay(self):
        result = self.create()
        self.assertEqual(self.counts(), (1, 1, 1, 1))
        self.assertEqual((result.external_order_id, result.checkout_url), ("ORD123", URL))
        self.assertEqual(result.created_at, NOW)
        self.assertEqual(result.expires_at, NOW + timedelta(hours=72))
        self.service = self._service()
        self.assertEqual(self.create(), result)
        self.transport.assert_called_once()
        self.oauth.assert_called_once_with(self.professional)
        self.fee.assert_called_once()
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().status, "SUCCEEDED")

    def test_missing_oauth_fee_or_wrong_receiver_fails_before_writes(self):
        for oauth, fee in (
            (None, Decimal("25")),
            (ProfessionalOAuthCredential(self.professional + 1, TOKEN, False, "ARS"), Decimal("25")),
            (ProfessionalOAuthCredential(self.professional, TOKEN, False, "ARS"), None),
        ):
            self.service = self._service(oauth_provider=lambda _: oauth, commission_policy=lambda _: fee)
            with self.subTest(oauth=repr(oauth), fee=fee), self.assertRaises(MercadoPagoOrderConfigurationError):
                self.create()
            self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.transport.assert_not_called()

    def test_prerequisite_provider_failure_rolls_back_existing_obligation_without_claim(self):
        with self.factory.Session.begin() as session:
            session.add(PaymentObligation(
                contract_request_id=self.contract, internal_reference="existing-obligation",
                amount=Decimal("1250.50"), currency="ARS",
            ))
        self.oauth.side_effect = RuntimeError(TOKEN)
        with self.assertRaises(MercadoPagoOrderConfigurationError):
            self.create()
        self.assertEqual(self.counts(), (1, 0, 0, 0))
        self.transport.assert_not_called()

    def test_default_configuration_is_disabled_before_providers_and_claim(self):
        self.service = self._service(configuration=None)
        with self.assertRaises(MercadoPagoOrderConfigurationError):
            self.create()
        self.assertEqual(self.counts(), (0, 0, 0, 0))
        self.oauth.assert_not_called()
        self.fee.assert_not_called()
        self.transport.assert_not_called()

    def test_timeout_keeps_key_and_blocks_next_service_without_retry(self):
        self.transport.side_effect = TimeoutError(TOKEN)
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self.create()
        with self.factory.Session() as session:
            claim = session.query(PaymentOrderReservation).one()
            original = claim.idempotency_key
            self.assertEqual(claim.status, "UNCERTAIN")
        self.service = self._service()
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self.create()
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().idempotency_key, original)
        self.assertEqual(self.counts(), (1, 1, 0, 0))
        self.transport.assert_called_once()

    def test_rejections_invalid_response_and_http_failure_all_keep_block(self):
        for status in (400, 401, 409, 423, 429, 500, 201):
            with self.subTest(status=status):
                # Independent disposable schema per scenario.
                db.session.remove()
                db.drop_all()
                db.create_all()
                self.actor, _, _, self.professional, self.contract = seed_contract(self.factory.Session)
                self.transport.reset_mock()
                self.transport.side_effect = None
                self.transport.return_value = http.MercadoPagoHTTPResponse(status, (), b"{")
                with self.assertRaises(PaymentOrderCreationUncertainError):
                    self.create()
                with self.assertRaises(PaymentOrderCreationUncertainError):
                    self.create()
                self.assertEqual(self.counts(), (1, 1, 0, 0))
                self.transport.assert_called_once()

    def test_persistence_failure_keeps_claim_after_one_http_call(self):
        with patch("app.services.payment_order_application_service.register_or_get_payment_order",
                   side_effect=RuntimeError("storage unavailable")):
            with self.assertRaises(PaymentOrderCreationUncertainError):
                self.create()
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrderReservation).one().status, "CALL_IN_PROGRESS")
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self.create()
        self.assertEqual(self.counts(), (1, 1, 0, 0))
        self.transport.assert_called_once()

    def test_expired_replay_returns_no_checkout_and_makes_no_http_call(self):
        result = self.create()
        self.now = result.expires_at
        with self.assertRaises(PaymentOrderExpiredError):
            self.create()
        self.assertEqual(self.counts(), (1, 1, 1, 1))
        self.transport.assert_called_once()

    def test_replay_crossing_expiration_after_read_does_not_deliver_checkout(self):
        result = self.create()
        original = self.service._prepare

        def delayed_read(*args):
            stored = original(*args)
            self.now = result.expires_at
            return stored

        with patch.object(self.service, "_prepare", side_effect=delayed_read):
            with self.assertRaises(PaymentOrderExpiredError):
                self.create()
        self.transport.assert_called_once()

    def test_result_completing_after_local_expiration_is_saved_but_not_delivered(self):
        def late_response(**request):
            result = self._response(**request)
            self.now += timedelta(hours=72)
            return result

        self.transport.side_effect = late_response
        with self.assertRaises(PaymentOrderExpiredError):
            self.create()
        self.assertEqual(self.counts(), (1, 1, 1, 2))
        with self.factory.Session() as session:
            self.assertEqual(session.query(PaymentOrder).one().status, "EXPIRED")
        with self.assertRaises(PaymentOrderExpiredError):
            self.create()
        self.transport.assert_called_once()

    def test_unauthorized_actor_never_resolves_oauth_or_fee(self):
        with self.assertRaises(PermissionError):
            self.service.create_order(actor_user_id=999999, contract_request_id=self.contract)
        self.oauth.assert_not_called()
        self.fee.assert_not_called()
        self.transport.assert_not_called()


if __name__ == "__main__":
    unittest.main()
