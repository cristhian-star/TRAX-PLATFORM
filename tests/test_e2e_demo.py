from datetime import timedelta
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from io import BytesIO

from app import create_app, db
from app.config.config import TestingConfig, ProductionConfig
from app.models.contract_request import ContractRequest
from app.models.payment_order import PaymentOrder
from app.models.payment_order_reconciliation import PaymentOrderReconciliationEvidence as Evidence
from app.models.payment_effect import TransactionalCreditGrant as Grant
from app.models.professional import Professional
from app.models.user import User
from app.services.contract_service import (
    create_contract, accept_contract, start_contract, declare_work_completed, confirm_completion,
)
from app.services.simulated_mercadopago_demo import enabled, DEMO_CONTRACT_KEY
from scripts.dev_seed_professionals import seed_professionals
from scripts.dev_seed_e2e import seed_scenario


class E2EDemoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = (Path(self.tmp.name) / "mandobra_stabilization_db.sqlite").as_posix()

        class LocalConfig(TestingConfig):
            @classmethod
            def apply_runtime_config(cls, config):
                super().apply_runtime_config(config)
                config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{path}"
                config["E2E_DEMO_ENABLED"] = True
                config["ENABLE_DEV_QA_PANEL"] = True
                config["E2E_DEMO_PROJECT"] = "mandobra_stabilization"
                config["E2E_DEMO_ORIGIN"] = "http://127.0.0.1:5050"

        self.gate = patch("app.services.simulated_mercadopago_demo.enabled", return_value=True)
        self.gate.start()
        self.app = create_app(config_class=LocalConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        seed_professionals()
        client = User.query.filter_by(email="cliente.demo@trax.local").one()
        owner = User.query.filter_by(email="plomeria.work@demo.trax.local").one()
        professional = Professional.query.filter_by(user_id=owner.id).one()
        self.client_id, self.owner_id, self.professional_id = client.id, owner.id, professional.id
        self.contract = create_contract(
            cliente_id=client.id, professional_id=professional.id,
            professional_user_id=owner.id, servicio="Plomería simulada",
            descripcion=DEMO_CONTRACT_KEY, precio_acordado="1000.00",
            actor_user_id=client.id, idempotency_key=DEMO_CONTRACT_KEY,
        )
        self.contract_id = self.contract.id
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.context.pop()
        self.gate.stop()
        self.tmp.cleanup()

    def login(self, user_id):
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = user_id
            session["user_role"] = "CLIENTE" if user_id == self.client_id else "PROFESIONAL"

    def confirmed(self):
        accept_contract(self.contract_id, self.owner_id, idempotency_key="e2e-accept-contract-001")
        start_contract(self.contract_id, self.owner_id, idempotency_key="e2e-start-contract-001")
        declare_work_completed(self.contract_id, self.owner_id, idempotency_key="e2e-complete-contract-001")
        confirm_completion(self.contract_id, self.client_id, idempotency_key="e2e-confirm-contract-001")

    def test_full_simulation_is_durable_and_replay_is_single_credit(self):
        self.confirmed()
        self.login(self.owner_id)
        first = self.client.post("/dev/e2e/order")
        self.assertEqual(first.status_code, 303)
        self.assertEqual(self.client.post("/dev/e2e/order").status_code, 303)
        self.assertEqual(PaymentOrder.query.count(), 1)
        checkout = self.client.get("/dev/e2e/order")
        self.assertEqual(checkout.status_code, 200)
        order = PaymentOrder.query.one()
        self.assertTrue(order.external_order_id.startswith("sim-"))
        self.assertFalse(order.live_mode)
        self.assertEqual(order.provider, "mercadopago")
        self.assertIn(order.checkout_url.encode(), checkout.data)
        qr = self.client.get("/dev/e2e/order/qr.png")
        self.assertEqual(qr.status_code, 200)
        self.assertEqual(Image.open(BytesIO(qr.data)).format, "PNG")
        self.login(self.client_id)
        path = "/dev/e2e/checkout/" + order.external_order_id
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.post(path + "/approve").status_code, 303)
        self.assertEqual(self.client.post(path + "/approve").status_code, 303)
        self.assertEqual(Evidence.query.count(), 1)
        self.assertEqual(Evidence.query.one().timing, "BEFORE_LOCAL_EXPIRY")
        self.assertEqual(Evidence.query.one().payment_order_id, order.id)
        self.assertEqual(Evidence.query.one().snapshot["id"], order.external_order_id)
        self.assertEqual(Evidence.query.one().snapshot["external_reference"], order.external_reference)
        self.assertEqual(Evidence.query.one().snapshot["currency"], "ARS")
        self.login(self.owner_id)
        self.assertEqual(self.client.post("/dev/e2e/apply").status_code, 303)
        self.assertEqual(self.client.post("/dev/e2e/apply").status_code, 303)
        self.assertEqual(Grant.query.count(), 1)
        self.assertEqual(Grant.query.one().expires_at - Grant.query.one().starts_at, timedelta(days=30))
        self.assertIn(b"SIMULACI", self.client.get("/dev/e2e/").data)

    def test_wrong_actor_and_out_of_order_are_rejected(self):
        self.login(self.client_id)
        self.assertEqual(self.client.post("/dev/e2e/order").status_code, 403)
        self.login(self.owner_id)
        self.assertEqual(self.client.post("/dev/e2e/order").status_code, 403)
        self.assertEqual(self.client.post("/dev/e2e/apply").status_code, 409)
        self.confirmed()
        self.assertEqual(self.client.post("/dev/e2e/order").status_code, 303)
        self.assertEqual(self.client.post("/dev/e2e/apply").status_code, 409)
        self.assertEqual(Grant.query.count(), 0)

    def test_csrf_and_ownership(self):
        self.confirmed()
        self.login(self.owner_id)
        self.app.config["WTF_CSRF_ENABLED"] = True
        self.assertEqual(self.client.post("/dev/e2e/order").status_code, 400)
        page = self.client.get("/dev/e2e/")
        import re
        token = re.search(rb'name="csrf_token" value="([^"]+)"', page.data).group(1).decode()
        self.assertEqual(self.client.post("/dev/e2e/order", data={"csrf_token": token}).status_code, 303)
        self.login(self.client_id)
        self.assertEqual(self.client.get("/dev/e2e/order").status_code, 403)
        self.assertEqual(self.client.get("/dev/e2e/order/qr.png").status_code, 403)
        self.login(User.query.filter_by(email="electricidad.pro@demo.trax.local").one().id)
        self.assertEqual(self.client.get("/dev/e2e/").status_code, 403)

    def test_qr_encoder_receives_exact_link_and_no_external_http(self):
        self.confirmed()
        self.login(self.owner_id)
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")) as network:
            self.assertEqual(self.client.post("/dev/e2e/order").status_code, 303)
            with patch("app.services.payment_order_delivery_service.segno.make_qr", wraps=__import__("segno").make_qr) as encoder:
                self.assertEqual(self.client.get("/dev/e2e/order/qr.png").status_code, 200)
                encoder.assert_called_once()
                self.assertEqual(encoder.call_args.args[0], PaymentOrder.query.one().checkout_url)
            network.assert_not_called()

    def test_routes_disappear_when_flag_is_disabled(self):
        self.app.config["E2E_DEMO_ENABLED"] = False
        self.login(self.owner_id)
        with patch("app.routes.e2e_demo_routes.enabled", return_value=False):
            self.assertEqual(self.client.get("/dev/e2e/").status_code, 404)
            self.assertEqual(self.client.post("/dev/e2e/order").status_code, 404)

    def test_seed_replay_keeps_single_contract_and_owner(self):
        first = seed_scenario()
        second = seed_scenario()
        self.assertEqual(first, self.contract_id)
        self.assertEqual(second, self.contract_id)
        self.assertEqual(ContractRequest.query.filter_by(descripcion=DEMO_CONTRACT_KEY).count(), 1)

    def test_gate_requires_disposable_project_and_container(self):
        config = dict(ENV_NAME="development", E2E_DEMO_ENABLED=True,
                      ENABLE_DEV_QA_PANEL=True,
                      E2E_DEMO_PROJECT="mandobra_stabilization",
                      E2E_DEMO_ORIGIN="http://127.0.0.1:5050",
                      SQLALCHEMY_DATABASE_URI="postgresql://x/mandobra_stabilization_db")
        with patch("app.services.simulated_mercadopago_demo.Path.exists", return_value=True):
            self.assertTrue(enabled(config))
            for key, value in (("ENV_NAME", "production"), ("ENABLE_DEV_QA_PANEL", False),
                               ("E2E_DEMO_ENABLED", False),
                               ("E2E_DEMO_PROJECT", "other"), ("E2E_DEMO_ORIGIN", "http://other"),
                               ("SQLALCHEMY_DATABASE_URI", "postgresql://x/trax_db")):
                changed = dict(config, **{key: value})
                self.assertFalse(enabled(changed))
        with patch("app.services.simulated_mercadopago_demo.Path.exists", return_value=False):
            self.assertFalse(enabled(config))
        with patch("app.services.simulated_mercadopago_demo.enabled", return_value=False):
            disabled = create_app(config_class=TestingConfig)
        self.assertFalse(any(rule.rule.startswith("/dev/e2e") for rule in disabled.url_map.iter_rules()))
        with patch.dict(os.environ, {
            "APP_ENV": "production", "SECRET_KEY": "synthetic-production-gate-check",
            "DATABASE_URL": "sqlite:///:memory:", "E2E_DEMO_ENABLED": "true",
        }, clear=True):
            production = create_app(config_class=ProductionConfig)
        self.assertFalse(any(rule.rule.startswith("/dev/e2e") for rule in production.url_map.iter_rules()))
