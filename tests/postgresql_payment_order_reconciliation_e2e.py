"""Independent disposable PostgreSQL gate; never run against trax_db."""
import os
from pathlib import Path
import re
import unittest
from unittest.mock import Mock, patch

from alembic import command
from alembic.config import Config
import sqlalchemy as sa
from sqlalchemy.engine import make_url

from app import create_app, db
from app.config.config import TestingConfig
from app.models.payment_order import PaymentOrder
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.mercadopago_order_query_adapter import MercadoPagoOrderQueryAdapter, OrderQueryContext
from app.services.payment_order_reconciliation_service import PaymentOrderReconciliationProcessor
from tests import test_mercadopago_order_reconciliation as cases
from tests.test_payment_order_application import TrackingSessionFactory, seed_contract


def guarded_engine(url, allow_reset):
    if allow_reset != "1" or not isinstance(url, str) or not url:
        raise RuntimeError("Gate bloqueado: falta URL o autorizacion explicita")
    parsed = make_url(url)
    if (parsed.get_backend_name() != "postgresql" or parsed.query
            or not isinstance(parsed.database, str)
            or len(parsed.database.encode()) > 63
            or re.fullmatch(r"trax_order_reconciliation_test(?:_[a-z0-9]+)*", parsed.database) is None):
        raise RuntimeError("Gate bloqueado: base PostgreSQL descartable invalida")
    return sa.create_engine(parsed)


class PostgreSQLOrderReconciliationGate(cases.ReconciliationTest):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("TRAX_POSTGRES_ORDER_RECONCILIATION_TEST_URL")
        cls.engine = guarded_engine(cls.url, os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET"))
        cls.config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        with patch.dict(os.environ, {"DATABASE_URL": cls.url}):
            command.upgrade(cls.config, "head")

    @classmethod
    def tearDownClass(cls):
        try:
            with patch.dict(os.environ, {"DATABASE_URL": cls.url}):
                command.downgrade(cls.config, "base")
            with cls.engine.begin() as connection:
                connection.execute(sa.text("DROP TABLE alembic_version"))
        finally:
            cls.engine.dispose()

    def setUp(self):
        url = self.url
        class LocalConfig(TestingConfig):
            @classmethod
            def apply_runtime_config(cls, config):
                super().apply_runtime_config(config)
                config["SQLALCHEMY_DATABASE_URI"] = url
        self.app = create_app(config_class=LocalConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        # URL was checked before connecting or modifying this disposable schema.
        with self.engine.begin() as connection:
            for table in reversed(db.metadata.sorted_tables):
                connection.execute(table.delete())
        self.factory = TrackingSessionFactory(self.engine)
        self.actor, _, _, self.professional, self.contract = seed_contract(self.factory.Session)
        self.now = cases.NOW.replace(tzinfo=None)
        service = PaymentOrderApplicationService(session_factory=self.factory, adapter=InMemoryPSPPaymentOrderCreationAdapter(), clock=lambda: cases.NOW)
        service.create_order(actor_user_id=self.actor, contract_request_id=self.contract)
        with self.factory.Session.begin() as session:
            order = session.query(PaymentOrder).one()
            order.provider, order.external_order_id = "mercadopago", "ORD123"
            self.order_id, self.reference = order.id, order.external_reference
            self.context = OrderQueryContext(order.id, order.professional_id, order.external_order_id, order.external_reference, order.amount, order.currency, order.live_mode, order.expires_at)
        self.content = cases.payload(self.context)
        self.oauth = Mock(side_effect=self.credential)
        self.transport = Mock(side_effect=self.remote)
        self.adapter = MercadoPagoOrderQueryAdapter(self.oauth, self.transport)
        self.processor = PaymentOrderReconciliationProcessor(session_factory=self.factory, adapter=self.adapter, enabled=True, clock=lambda: self.now)

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()


if __name__ == "__main__":
    unittest.main(defaultTest="PostgreSQLOrderReconciliationGate")
