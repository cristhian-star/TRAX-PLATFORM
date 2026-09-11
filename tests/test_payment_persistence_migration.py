import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.exc import IntegrityError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PaymentPersistenceMigrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        database = Path(self.temporary.name) / "payment-persistence.db"
        self.url = f"sqlite:///{database.as_posix()}"
        self.config = Config(str(PROJECT_ROOT / "alembic.ini"))
        self.previous_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = self.url
        self.engine = sa.create_engine(self.url)

    def tearDown(self):
        self.engine.dispose()
        if self.previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.previous_url
        self.temporary.cleanup()

    def _tables(self):
        return set(sa.inspect(self.engine).get_table_names())

    def test_upgrade_downgrade_upgrade_and_constraints(self):
        script = ScriptDirectory.from_config(self.config)
        self.assertEqual(script.get_heads(), ["20260910_01"])
        command.upgrade(self.config, "20260904_01")
        self.assertNotIn("payment_obligations", self._tables())

        command.upgrade(self.config, "head")
        self.assertIn("payment_obligations", self._tables())
        self.assertIn("payment_attempts", self._tables())
        with self.engine.begin() as connection:
            obligation_id = connection.execute(
                sa.text(
                    "INSERT INTO payment_obligations "
                    "(internal_reference,amount,currency,created_at) "
                    "VALUES ('migration-ref',123456789.123456789,'ARS','2026-09-10') "
                    "RETURNING id"
                )
            ).scalar_one()
            connection.execute(
                sa.text(
                    "INSERT INTO payment_attempts "
                    "(obligation_id,idempotency_key,external_attempt_id,financial_status,"
                    "orchestration_result,requires_reconciliation,created_at,updated_at) "
                    "VALUES (:obligation,'migration-key',NULL,NULL,"
                    "'RECONCILIATION_REQUIRED',1,'2026-09-10','2026-09-10')"
                ),
                {"obligation": obligation_id},
            )
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    sa.text(
                        "INSERT INTO payment_obligations "
                        "(internal_reference,amount,currency,created_at) "
                        "VALUES ('invalid',0,'ARS','2026-09-10')"
                    )
                )

        command.downgrade(self.config, "20260904_01")
        self.assertNotIn("payment_attempts", self._tables())
        self.assertNotIn("payment_obligations", self._tables())
        command.upgrade(self.config, "head")
        self.assertIn("payment_attempts", self._tables())
        self.assertIn("payment_obligations", self._tables())


if __name__ == "__main__":
    unittest.main()
