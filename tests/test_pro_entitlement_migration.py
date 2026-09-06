import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ProEntitlementMigrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = Path(self.temporary.name) / "pro-entitlement.db"
        self.url = f"sqlite:///{path.as_posix()}"
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

    def _columns(self):
        return {item["name"] for item in sa.inspect(self.engine).get_columns("subscriptions")}

    def test_upgrade_preserves_legacy_null_validates_sources_and_downgrades(self):
        command.upgrade(self.config, "20260726_07")
        with self.engine.begin() as connection:
            user_id = connection.execute(
                sa.text(
                    "INSERT INTO users (nombre,email,password,rol,estado) "
                    "VALUES ('Legacy','legacy@migration.test','hash','PROFESIONAL','ACTIVO') RETURNING id"
                )
            ).scalar_one()
            connection.execute(
                sa.text(
                    "INSERT INTO subscriptions "
                    "(user_id,plan,estado,started_at,expires_at,auto_renew) "
                    "VALUES (:user,'PRO','ACTIVA','2026-01-01','2030-01-01',0)"
                ),
                {"user": user_id},
            )

        command.upgrade(self.config, "20260904_01")
        self.assertIn("source_type", self._columns())
        with self.engine.begin() as connection:
            self.assertIsNone(
                connection.execute(sa.text("SELECT source_type FROM subscriptions")).scalar_one()
            )
        with self.engine.begin() as connection:
            self.assertIsNone(
                connection.execute(sa.text("SELECT source_type FROM subscriptions")).scalar_one()
            )
            connection.execute(
                sa.text("UPDATE subscriptions SET source_type='TRANSACTIONAL'")
            )
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    sa.text("UPDATE subscriptions SET source_type='ADMINISTRATIVE'")
                )

        command.downgrade(self.config, "20260726_07")
        self.assertNotIn("source_type", self._columns())
        command.upgrade(self.config, "20260904_01")
        self.assertIn("source_type", self._columns())


if __name__ == "__main__":
    unittest.main()
