import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError


TABLES = {
    "payment_order_reconciliation_work", "payment_order_reconciliation_attempts",
    "payment_order_reconciliation_evidence", "payment_order_reconciliation_quarantine",
}


class ReconciliationMigrationTest(unittest.TestCase):
    def test_single_head_upgrade_downgrade_upgrade_preserves_legacy(self):
        with tempfile.TemporaryDirectory() as temporary:
            url = f"sqlite:///{(Path(temporary) / 'migration.db').as_posix()}"
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            engine = sa.create_engine(url)
            try:
                with patch.dict(os.environ, {"DATABASE_URL": url}):
                    scripts = ScriptDirectory.from_config(config)
                    self.assertEqual(scripts.get_heads(), ["20260917_03"])
                    self.assertEqual(scripts.get_revision("20260917_02").down_revision, "20260917_01")
                    command.upgrade(config, "20260917_01")
                    with engine.begin() as connection:
                        connection.execute(sa.text("INSERT INTO psp_event_inbox (provider,external_event_id,topic,action,external_resource_id,test_mode,occurred_at,received_at,payload_hash) VALUES ('mercadopago','historical','payment','payment.updated','123',1,NULL,'2026-09-17 20:00:00',:digest)"), {"digest": "a" * 64})
                    command.upgrade(config, "head")
                    self.assertTrue(TABLES.issubset(sa.inspect(engine).get_table_names()))
                    with engine.begin() as connection:
                        connection.execute(sa.text("INSERT INTO payment_order_reconciliation_work (event_id,status,attempt_count,next_attempt_at,created_at) VALUES (1,'QUEUED',0,'2026-09-17 20:00:00','2026-09-17 20:00:00')"))
                    for sql in (
                        "UPDATE payment_order_reconciliation_work SET attempt_count=9",
                        "UPDATE payment_order_reconciliation_work SET status='PROCESSING'",
                        "INSERT INTO payment_order_reconciliation_work (event_id,status,attempt_count,next_attempt_at,created_at) VALUES (1,'QUEUED',0,'2026-09-17','2026-09-17')",
                    ):
                        with self.assertRaises(IntegrityError), engine.begin() as connection:
                            connection.execute(sa.text(sql))
                    command.downgrade(config, "20260917_01")
                    self.assertFalse(TABLES.intersection(sa.inspect(engine).get_table_names()))
                    with engine.connect() as connection:
                        self.assertEqual(connection.execute(sa.text("SELECT external_event_id FROM psp_event_inbox")).scalar_one(), "historical")
                    command.upgrade(config, "head")
                    self.assertTrue(TABLES.issubset(sa.inspect(engine).get_table_names()))
            finally:
                engine.dispose()
