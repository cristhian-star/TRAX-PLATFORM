import hashlib
import hmac
import os
import re
import sys
import unittest
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
    TIMESTAMP = "1742505638683"

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
        db.session.query(PSPEventRecord).delete()
        db.session.commit()

    @classmethod
    def _signature(cls, data_id="123456"):
        manifest = (
            f"id:{data_id.lower()};request-id:{cls.REQUEST_ID};"
            f"ts:{cls.TIMESTAMP};"
        )
        return hmac.new(
            cls.SECRET.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()

    @classmethod
    def _body(cls, **changes):
        body = {
            "id": 9001,
            "type": "payment",
            "action": "payment.updated",
            "data": {"id": "123456"},
            "live_mode": False,
            "date_created": "2026-09-12T20:59:00Z",
            "api_version": "v1",
        }
        body.update(changes)
        return body

    def _post(self, **changes):
        return self.client.post(
            "/api/webhooks/mercadopago?data.id=123456&type=payment",
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
        conflict = self._post(action="payment.created")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(first.get_json(), replay.get_json())
        self.assertEqual(conflict.status_code, 409)
        db.session.expire_all()
        rows = db.session.query(PSPEventRecord).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].action, "payment.updated")

    def test_failed_persistence_rolls_back_and_session_recovers(self):
        invalid = PSPEventRecord(
            provider="mercadopago",
            external_event_id="invalid",
            topic="payment",
            action="payment.updated",
            external_resource_id="123456",
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
