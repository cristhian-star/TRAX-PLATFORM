import os
import re
import sys
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.psp_event import PSPEventRecord
from app.services.psp_event_contract import PSPEvent
from app.services.psp_event_inbox import PSPEventConflictError, register_or_get_event
from tests.alembic_head_validation import assert_database_at_repository_head


DATABASE_PATTERN = re.compile(r"trax_psp_event_test(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?")


def _guarded_engine(url, allow_reset):
    if allow_reset != "1" or not isinstance(url, str) or not url:
        raise RuntimeError("Gate bloqueado: falta URL o autorizacion explicita")
    parsed = make_url(url)
    name = parsed.database
    if (
        parsed.get_backend_name() != "postgresql" or parsed.query
        or not isinstance(name, str) or len(name.encode("utf-8")) > 63
        or DATABASE_PATTERN.fullmatch(name) is None
    ):
        raise RuntimeError("Gate bloqueado: base PostgreSQL descartable invalida")
    return sa.create_engine(parsed)


class PostgreSQLPSPEventInboxGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("TRAX_POSTGRES_PSP_EVENT_TEST_URL")
        cls.engine = _guarded_engine(cls.url, os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET"))
        cls.config = Config(str(ROOT / "alembic.ini"))
        cls.previous_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = cls.url
        command.upgrade(cls.config, "head")
        with cls.engine.connect() as connection:
            revisions = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalars().all()
        assert_database_at_repository_head(cls.config, revisions)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)

    @classmethod
    def tearDownClass(cls):
        try:
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
        with self.engine.begin() as connection:
            connection.execute(sa.text("TRUNCATE TABLE psp_event_inbox RESTART IDENTITY"))

    @staticmethod
    def _event(**changes):
        values = dict(
            provider="provider", external_event_id="opaque/event", topic="payment",
            action="payment.updated", external_resource_id="resource-1", test_mode=True,
            occurred_at=datetime(2026, 9, 11, 20, tzinfo=timezone.utc),
            received_at=datetime(2026, 9, 11, 20, 1, tzinfo=timezone.utc),
            payload_hash="a" * 64,
        )
        values.update(changes)
        return PSPEvent(**values)

    def test_migration_upgrade_downgrade_upgrade(self):
        command.downgrade(self.config, "20260910_01")
        self.assertNotIn("psp_event_inbox", sa.inspect(self.engine).get_table_names())
        command.upgrade(self.config, "head")
        self.assertIn("psp_event_inbox", sa.inspect(self.engine).get_table_names())

    def test_concurrent_redelivery_with_different_received_at_converges_to_one_row(self):
        barrier = threading.Barrier(2)
        results = []

        received_times = (
            datetime(2026, 9, 11, 20, 1, tzinfo=timezone.utc),
            datetime(2026, 9, 11, 22, 1, tzinfo=timezone.utc),
        )

        def worker(received_at):
            session = self.Session()
            try:
                barrier.wait()
                row = register_or_get_event(
                    session, self._event(received_at=received_at)
                )
                session.commit()
                results.append(("ok", row.id, row.received_at))
            except Exception as exc:
                session.rollback()
                results.append(("error", exc, None))
            finally:
                session.close()

        threads = [threading.Thread(target=worker, args=(value,)) for value in received_times]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)
            self.assertFalse(thread.is_alive())
        self.assertEqual([kind for kind, _, _ in results], ["ok", "ok"])
        self.assertEqual(len({value for _, value, _ in results}), 1)
        with self.Session() as session:
            rows = session.query(PSPEventRecord).all()
            self.assertEqual(len(rows), 1)
            stored_received_at = rows[0].received_at.replace(tzinfo=timezone.utc)
            self.assertIn(stored_received_at, received_times)

    def test_conflict_rollback_visibility_and_session_recovery(self):
        session = self.Session()
        row = register_or_get_event(session, self._event())
        session.commit()
        with self.Session() as independent:
            self.assertIsNotNone(independent.get(PSPEventRecord, row.id))
        with self.assertRaises(PSPEventConflictError):
            register_or_get_event(session, self._event(action="payment.created"))
        session.rollback()
        register_or_get_event(session, self._event(external_event_id="recovered"))
        session.commit()
        self.assertEqual(session.query(PSPEventRecord).count(), 2)
        session.close()


if __name__ == "__main__":
    unittest.main()
