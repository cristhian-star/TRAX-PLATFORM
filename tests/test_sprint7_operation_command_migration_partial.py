import os
import tempfile
import unittest
import gc
from contextlib import contextmanager
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Sprint7OperationCommandPartialMigrationTest(unittest.TestCase):
    def setUp(self):
        handle, path = tempfile.mkstemp(prefix="trax-p1-05-", suffix=".db")
        os.close(handle)
        self.database_path = Path(path)
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        self.engine = sa.create_engine(self.database_url)
        self._alembic("upgrade", "20260726_01")

    def tearDown(self):
        self.engine.dispose()
        gc.collect()
        self.database_path.unlink(missing_ok=True)

    @contextmanager
    def _database_environment(self):
        old_database_url = os.environ.get("DATABASE_URL")
        old_secret = os.environ.get("SECRET_KEY")
        os.environ["DATABASE_URL"] = self.database_url
        os.environ["SECRET_KEY"] = "migration-partial-test"
        try:
            yield
        finally:
            if old_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old_database_url
            if old_secret is None:
                os.environ.pop("SECRET_KEY", None)
            else:
                os.environ["SECRET_KEY"] = old_secret

    def _alembic(self, action, revision):
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        with self._database_environment():
            getattr(command, action)(config, revision)

    def _create_partial_table(
        self,
        *,
        actor_type="INTEGER",
        actor_nullable=False,
        full_columns=True,
        existing_actor_index=False,
    ):
        nullable = "" if actor_nullable else " NOT NULL"
        if not full_columns:
            definition = "id INTEGER NOT NULL PRIMARY KEY"
        else:
            definition = f"""
                id INTEGER NOT NULL PRIMARY KEY,
                actor_user_id {actor_type}{nullable},
                operation VARCHAR(80) NOT NULL,
                idempotency_key VARCHAR(160) NOT NULL,
                payload_hash VARCHAR(64) NOT NULL,
                status VARCHAR(20) NOT NULL,
                result_entity_type VARCHAR(80),
                result_entity_id INTEGER,
                correlation_id VARCHAR(36) NOT NULL,
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                failure_code VARCHAR(80)
            """
        with self.engine.begin() as connection:
            connection.execute(
                sa.text(f"CREATE TABLE operation_commands ({definition})")
            )
            if existing_actor_index:
                connection.execute(
                    sa.text(
                        "CREATE INDEX ix_operation_commands_actor_user_id "
                        "ON operation_commands (actor_user_id)"
                    )
                )

    def _revision(self):
        with self.engine.connect() as connection:
            return connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()

    def _assert_complete_structure(self):
        inspector = sa.inspect(self.engine)
        columns = {
            column["name"]: column
            for column in inspector.get_columns("operation_commands")
        }
        self.assertEqual(
            set(columns),
            {
                "id",
                "actor_user_id",
                "operation",
                "idempotency_key",
                "payload_hash",
                "status",
                "result_entity_type",
                "result_entity_id",
                "correlation_id",
                "created_at",
                "completed_at",
                "failure_code",
            },
        )
        for required in (
            "id",
            "actor_user_id",
            "operation",
            "idempotency_key",
            "payload_hash",
            "status",
            "correlation_id",
            "created_at",
        ):
            self.assertFalse(columns[required]["nullable"])

        foreign_keys = {
            item["name"]: item
            for item in inspector.get_foreign_keys("operation_commands")
        }
        self.assertIn("fk_operation_commands_actor_user_id", foreign_keys)
        self.assertEqual(
            foreign_keys["fk_operation_commands_actor_user_id"]["constrained_columns"],
            ["actor_user_id"],
        )
        uniques = {
            item["name"]: item
            for item in inspector.get_unique_constraints("operation_commands")
        }
        self.assertEqual(
            uniques["uq_operation_commands_actor_operation_key"]["column_names"],
            ["actor_user_id", "operation", "idempotency_key"],
        )
        checks = {
            item["name"]: item
            for item in inspector.get_check_constraints("operation_commands")
        }
        self.assertIn("ck_operation_commands_status", checks)
        indexes = {
            item["name"]: item
            for item in inspector.get_indexes("operation_commands")
        }
        self.assertEqual(
            indexes["ix_operation_commands_actor_user_id"]["column_names"],
            ["actor_user_id"],
        )
        self.assertEqual(
            indexes["ix_operation_commands_correlation_id"]["column_names"],
            ["correlation_id"],
        )

    def test_existing_table_with_missing_columns_is_repaired_when_empty(self):
        self._create_partial_table(full_columns=False)

        self._alembic("upgrade", "20260726_02")

        self.assertEqual(self._revision(), "20260726_02")
        self._assert_complete_structure()

    def test_nullable_column_and_missing_fk_unique_check_are_repaired(self):
        self._create_partial_table(actor_nullable=True)

        self._alembic("upgrade", "20260726_02")

        self._assert_complete_structure()

    def test_existing_expected_index_is_preserved_and_missing_index_is_added(self):
        self._create_partial_table(existing_actor_index=True)

        self._alembic("upgrade", "20260726_02")

        self._assert_complete_structure()

    def test_incompatible_schema_blocks_before_other_phase2a_changes(self):
        self._create_partial_table(actor_type="VARCHAR(50)")
        with self.engine.begin() as connection:
            connection.execute(
                sa.text(
                    "INSERT INTO operation_commands "
                    "(id, actor_user_id, operation, idempotency_key, payload_hash, "
                    "status, correlation_id, created_at) "
                    "VALUES (7, 'bad', 'CREATE', 'partial-key-0001', :payload_hash, "
                    "'PROCESSING', '00000000-0000-0000-0000-000000000001', "
                    "CURRENT_TIMESTAMP)"
                ),
                {"payload_hash": "0" * 64},
            )

        with self.assertRaises(RuntimeError):
            self._alembic("upgrade", "20260726_02")

        inspector = sa.inspect(self.engine)
        self.assertEqual(self._revision(), "20260726_01")
        self.assertNotIn(
            "contracting_mode",
            {column["name"] for column in inspector.get_columns("contract_requests")},
        )
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.execute(
                    sa.text("SELECT COUNT(*) FROM operation_commands")
                ).scalar_one(),
                1,
            )

    def test_missing_required_columns_with_data_blocks_without_data_loss(self):
        self._create_partial_table(full_columns=False)
        with self.engine.begin() as connection:
            connection.execute(sa.text("INSERT INTO operation_commands (id) VALUES (9)"))

        with self.assertRaises(RuntimeError):
            self._alembic("upgrade", "20260726_02")

        self.assertEqual(self._revision(), "20260726_01")
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.execute(
                    sa.text("SELECT id FROM operation_commands")
                ).scalar_one(),
                9,
            )

    def test_upgrade_can_resume_after_repaired_schema_loses_one_index(self):
        self._create_partial_table(actor_nullable=True)
        self._alembic("upgrade", "20260726_02")
        with self.engine.begin() as connection:
            connection.execute(
                sa.text("DROP INDEX ix_operation_commands_correlation_id")
            )
            connection.execute(
                sa.text(
                    "UPDATE alembic_version SET version_num = '20260726_01'"
                )
            )

        self._alembic("upgrade", "20260726_02")

        self.assertEqual(self._revision(), "20260726_02")
        self._assert_complete_structure()

    def test_partial_downgrade_with_missing_index_is_restartable(self):
        self._alembic("upgrade", "20260726_02")
        with self.engine.begin() as connection:
            connection.execute(
                sa.text("DROP INDEX ix_operation_commands_correlation_id")
            )

        self._alembic("downgrade", "20260726_01")
        self.assertEqual(self._revision(), "20260726_01")
        self.assertFalse(sa.inspect(self.engine).has_table("operation_commands"))

        self._alembic("upgrade", "20260726_02")
        self._assert_complete_structure()

    def test_partial_downgrade_with_operation_table_already_removed_resumes(self):
        self._alembic("upgrade", "20260726_02")
        with self.engine.begin() as connection:
            connection.execute(sa.text("DROP TABLE operation_commands"))

        self._alembic("downgrade", "20260726_01")

        self.assertEqual(self._revision(), "20260726_01")
        self.assertFalse(sa.inspect(self.engine).has_table("operation_commands"))


if __name__ == "__main__":
    unittest.main()
