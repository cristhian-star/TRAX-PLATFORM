import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[1]


class PaymentAttemptPSPIdentityMigrationTest(unittest.TestCase):
    def test_upgrade_downgrade_upgrade_preserves_legacy_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            url = f"sqlite:///{(Path(temporary) / 'identity.db').as_posix()}"
            previous = os.environ.get("DATABASE_URL")
            os.environ["DATABASE_URL"] = url
            engine = sa.create_engine(url)
            config = Config(str(ROOT / "alembic.ini"))
            try:
                script = ScriptDirectory.from_config(config)
                self.assertEqual(script.get_heads(), ["20260911_02"])
                command.upgrade(config, "20260911_01")
                with engine.begin() as connection:
                    obligation = connection.execute(sa.text(
                        "INSERT INTO payment_obligations (internal_reference,amount,currency,created_at) "
                        "VALUES ('legacy',1,'ARS','2026-09-11') RETURNING id"
                    )).scalar_one()
                    connection.execute(sa.text(
                        "INSERT INTO payment_attempts (obligation_id,idempotency_key,external_attempt_id,"
                        "financial_status,orchestration_result,requires_reconciliation,created_at,updated_at) "
                        "VALUES (:id,'legacy-key','legacy-external','PENDING','PENDING',0,'2026-09-11','2026-09-11')"
                    ), {"id": obligation})
                command.upgrade(config, "head")
                with engine.connect() as connection:
                    row = connection.execute(sa.text(
                        "SELECT psp_provider,psp_live_mode,external_attempt_id FROM payment_attempts"
                    )).one()
                self.assertEqual(tuple(row), (None, None, "legacy-external"))
                command.downgrade(config, "20260911_01")
                self.assertNotIn("psp_provider", {c["name"] for c in sa.inspect(engine).get_columns("payment_attempts")})
                command.upgrade(config, "head")
                self.assertIn("psp_provider", {c["name"] for c in sa.inspect(engine).get_columns("payment_attempts")})
            finally:
                engine.dispose()
                if previous is None:
                    os.environ.pop("DATABASE_URL", None)
                else:
                    os.environ["DATABASE_URL"] = previous


if __name__ == "__main__":
    unittest.main()
