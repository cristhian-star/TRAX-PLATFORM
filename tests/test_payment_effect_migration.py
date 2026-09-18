import io
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


TABLES = {"payment_effect_payment_claims","transactional_credit_policies", "payment_effect_decisions", "transactional_commissions",
          "transactional_credit_lots", "transactional_credit_grants", "transactional_credit_allocations", "payment_effect_audit"}


class PaymentEffectMigrationTest(unittest.TestCase):
    def test_upgrade_downgrade_upgrade_preserves_evidence_and_has_single_head(self):
        with tempfile.TemporaryDirectory() as temporary:
            url = f"sqlite:///{(Path(temporary)/'effects.db').as_posix()}"
            config = Config(str(Path(__file__).resolve().parents[1]/"alembic.ini"))
            scripts = ScriptDirectory.from_config(config)
            self.assertEqual(scripts.get_heads(),["20260917_03"])
            self.assertEqual(scripts.get_revision("20260917_03").down_revision,"20260917_02")
            engine = sa.create_engine(url)
            try:
                with patch.dict(os.environ,{"DATABASE_URL":url}):
                    command.upgrade(config,"20260917_02")
                    with engine.begin() as connection:
                        connection.execute(sa.text("INSERT INTO psp_event_inbox (provider,external_event_id,topic,action,external_resource_id,test_mode,received_at,payload_hash) VALUES ('mercadopago','history','order','order.updated','ORDhistory',1,'2026-09-17',:digest)"),{"digest":"a"*64})
                        connection.execute(sa.text("INSERT INTO payment_order_reconciliation_work (event_id,status,attempt_count,next_attempt_at,created_at) VALUES (1,'QUEUED',0,'2026-09-17','2026-09-17')"))
                    command.upgrade(config,"head")
                    self.assertTrue(TABLES.issubset(sa.inspect(engine).get_table_names()))
                    with engine.begin() as connection:
                        connection.execute(sa.text("INSERT INTO transactional_credit_policies (version,currency,threshold) VALUES ('explicit','ARS','100.00')"))
                    for sql in ("UPDATE transactional_credit_policies SET threshold='0'",
                                "UPDATE transactional_credit_policies SET currency='USD'",
                                "INSERT INTO transactional_credit_policies (version,currency,threshold) VALUES ('explicit','ARS','100.00')"):
                        with self.assertRaises(IntegrityError),engine.begin() as connection:
                            connection.execute(sa.text(sql))
                    command.downgrade(config,"20260917_02")
                    self.assertFalse(TABLES.intersection(sa.inspect(engine).get_table_names()))
                    with engine.connect() as connection:
                        self.assertEqual(connection.execute(sa.text("SELECT status FROM payment_order_reconciliation_work")).scalar_one(),"QUEUED")
                        self.assertEqual(connection.execute(sa.text("SELECT external_event_id FROM psp_event_inbox")).scalar_one(),"history")
                    command.upgrade(config,"head")
                    self.assertTrue(TABLES.issubset(sa.inspect(engine).get_table_names()))
            finally:
                engine.dispose()

    def test_postgresql_ddl_compiles_offline_without_connecting(self):
        config = Config(str(Path(__file__).resolve().parents[1]/"alembic.ini"),output_buffer=io.StringIO())
        with patch.dict(os.environ,{"DATABASE_URL":"postgresql://unused:unused@localhost/disposable_offline"}):
            command.upgrade(config,"20260917_02:20260917_03",sql=True)
        ddl=config.output_buffer.getvalue()
        self.assertIn("interval '40 days'",ddl)
        self.assertIn("interval '30 days'",ddl)
        self.assertIn("NUMERIC(64, 2)",ddl)
        self.assertNotIn("julianday",ddl)
        self.assertNotIn('CONSTRAINT "None"',ddl)
