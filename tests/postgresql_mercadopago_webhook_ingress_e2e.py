import hashlib
import hmac
import os
import re
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.config.config import TestingConfig
from app.models.psp_event import PSPEventRecord
from app.models.payment_order_reconciliation import PaymentOrderReconciliationWork as Work, PaymentOrderReconciliationAttempt as Attempt, PaymentOrderReconciliationEvidence as Evidence, PaymentOrderReconciliationQuarantine as Quarantine
from tests.alembic_head_validation import assert_database_at_repository_head


DATABASE_PATTERN = re.compile(
    r"trax_mp_webhook_test(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?"
)


def _guarded_engine(url, allow_reset):
    if allow_reset != "1" or not isinstance(url, str) or not url:
        raise RuntimeError("Gate bloqueado: falta URL o autorizacion explicita")
    parsed = make_url(url)
    name = parsed.database
    if (
        parsed.get_backend_name() != "postgresql"
        or parsed.query
        or not isinstance(name, str)
        or len(name.encode("utf-8")) > 63
        or DATABASE_PATTERN.fullmatch(name) is None
    ):
        raise RuntimeError("Gate bloqueado: base PostgreSQL descartable invalida")
    return sa.create_engine(parsed)


class PostgreSQLMercadoPagoWebhookIngressGate(unittest.TestCase):
    SECRET = "fictional-postgresql-ingress-secret"
    REQUEST_ID = "request-postgresql-123"
    NOW = datetime(2026, 9, 17, 20, tzinfo=timezone.utc)
    TIMESTAMP = str(int(NOW.timestamp() * 1000))

    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("TRAX_POSTGRES_MP_WEBHOOK_TEST_URL")
        cls.engine = _guarded_engine(
            cls.url, os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET")
        )
        cls.config = Config(str(ROOT / "alembic.ini"))
        cls.previous_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = cls.url
        command.upgrade(cls.config, "head")
        with cls.engine.connect() as connection:
            revisions = connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalars().all()
        assert_database_at_repository_head(cls.config, revisions)
        cls.app = create_app(config_class=TestingConfig)
        cls.app.config["MERCADOPAGO_WEBHOOK_SECRET"] = cls.SECRET
        cls.app.config["MERCADOPAGO_ORDER_WEBHOOK_ENABLED"] = True
        cls.context = cls.app.app_context()
        cls.context.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        try:
            db.session.remove()
            cls.context.pop()
            command.downgrade(cls.config, "base")
            with cls.engine.begin() as connection:
                connection.execute(sa.text("DROP TABLE alembic_version"))
            if sa.inspect(cls.engine).get_table_names():
                raise AssertionError("la base descartable no quedo limpia")
        finally:
            cls.engine.dispose()
            if cls.previous_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = cls.previous_url

    def setUp(self):
        db.session.rollback()
        for model in (Evidence, Attempt, Quarantine, Work, PSPEventRecord):
            db.session.query(model).delete()
        db.session.commit()
        self.clock_patch = patch("app.routes.mercadopago_webhook_routes._utc_now", return_value=self.NOW)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)

    @classmethod
    def _signature(cls, data_id="ORD123456"):
        manifest = (
            f"id:{data_id};request-id:{cls.REQUEST_ID};"
            f"ts:{cls.TIMESTAMP};"
        )
        return hmac.new(
            cls.SECRET.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()

    @classmethod
    def _body(cls, **changes):
        body = {
            "id": 9001,
            "type": "order",
            "action": "order.updated",
            "data": {"id": "ORD123456"},
            "live_mode": False,
            "date_created": "2026-09-12T20:59:00Z",
            "api_version": "v1",
        }
        body.update(changes)
        return body

    def _post(self, **changes):
        return self.client.post(
            "/api/webhooks/mercadopago?data.id=ORD123456&type=order",
            headers={
                "X-Signature": (
                    f"ts={self.TIMESTAMP},v1={self._signature()}"
                ),
                "X-Request-Id": self.REQUEST_ID,
            },
            json=self._body(**changes),
        )

    def test_new_replay_and_conflict_are_atomic_on_postgresql(self):
        first = self._post()
        replay = self._post()
        conflict = self._post(action="order.created")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(first.get_json(), replay.get_json())
        self.assertEqual(conflict.status_code, 200)
        self.assertEqual(db.session.query(Quarantine).count(), 1)
        db.session.expire_all()
        rows = db.session.query(PSPEventRecord).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].action, "order.updated")

    def test_failed_persistence_rolls_back_and_session_recovers(self):
        invalid = PSPEventRecord(
            provider="mercadopago",
            external_event_id="invalid",
            topic="order",
            action="order.updated",
            external_resource_id="ORD123456",
            test_mode=True,
            received_at=sa.func.now(),
            payload_hash="short",
        )
        db.session.add(invalid)
        response = self._post()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(db.session.query(PSPEventRecord).count(), 0)
        self.assertEqual(self._post().status_code, 200)
        self.assertEqual(db.session.query(PSPEventRecord).count(), 1)


if __name__ == "__main__":
    unittest.main()
