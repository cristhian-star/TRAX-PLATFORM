import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Sprint7NegotiationMigrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary.name) / "negotiation-migration.db"
        self.database_url = f"sqlite:///{database_path.as_posix()}"
        self.config = Config(str(PROJECT_ROOT / "alembic.ini"))
        self.previous_database_url = os.environ.get("DATABASE_URL")
        self.previous_secret_key = os.environ.get("SECRET_KEY")
        os.environ["DATABASE_URL"] = self.database_url
        os.environ["SECRET_KEY"] = "negotiation-migration-test"

    def tearDown(self):
        if self.previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.previous_database_url
        if self.previous_secret_key is None:
            os.environ.pop("SECRET_KEY", None)
        else:
            os.environ["SECRET_KEY"] = self.previous_secret_key
        self.temporary.cleanup()

    def _revision(self):
        engine = sa.create_engine(self.database_url)
        try:
            with engine.connect() as connection:
                return connection.execute(
                    sa.text("SELECT version_num FROM alembic_version")
                ).scalar_one()
        finally:
            engine.dispose()

    def _insert_phase2b_snapshot(self, engine, payload_hash):
        with engine.begin() as connection:
            client_id = connection.execute(
                sa.text(
                    "INSERT INTO users "
                    "(nombre, email, password, rol, estado) "
                    "VALUES ('Preflight Client', "
                    "'preflight-client@test.local', 'hash', "
                    "'CLIENTE', 'ACTIVO') RETURNING id"
                )
            ).scalar_one()
            professional_user_id = connection.execute(
                sa.text(
                    "INSERT INTO users "
                    "(nombre, email, password, rol, estado) "
                    "VALUES ('Preflight Professional', "
                    "'preflight-professional@test.local', 'hash', "
                    "'PROFESIONAL', 'ACTIVO') RETURNING id"
                )
            ).scalar_one()
            professional_id = connection.execute(
                sa.text(
                    "INSERT INTO professionals "
                    "(user_id, nombre, servicio, zona, perfil_completo, "
                    "estado_perfil) VALUES "
                    "(:user_id, 'Professional', 'Electricidad', 'CABA', "
                    "1, 'VERIFICADO') RETURNING id"
                ),
                {"user_id": professional_user_id},
            ).scalar_one()
            negotiation_id = connection.execute(
                sa.text(
                    "INSERT INTO contract_negotiations "
                    "(cliente_id, professional_id, professional_user_id, "
                    "servicio, state, contracting_mode, version, "
                    "current_terms_version) VALUES "
                    "(:client_id, :professional_id, "
                    ":professional_user_id, 'Servicio', 'OPEN', "
                    "'EXTERNAL', 1, 1) RETURNING id"
                ),
                {
                    "client_id": client_id,
                    "professional_id": professional_id,
                    "professional_user_id": professional_user_id,
                },
            ).scalar_one()
            snapshot_id = connection.execute(
                sa.text(
                    "INSERT INTO contract_negotiation_versions "
                    "(negotiation_id, version_no, actor_user_id, "
                    "description, scope, external_price, "
                    "estimated_start_at, estimated_end_at, observations, "
                    "payload_hash) VALUES "
                    "(:negotiation_id, 1, :actor_user_id, :description, "
                    ":scope, :external_price, :start_at, :end_at, "
                    ":observations, :payload_hash) RETURNING id"
                ),
                {
                    "negotiation_id": negotiation_id,
                    "actor_user_id": client_id,
                    "description": "Legacy description",
                    "scope": "Legacy scope",
                    "external_price": 10.0,
                    "start_at": datetime(2026, 8, 1, 10, 0),
                    "end_at": datetime(2026, 8, 2, 18, 0),
                    "observations": "Legacy observations",
                    "payload_hash": payload_hash,
                },
            ).scalar_one()
        return snapshot_id

    def _schema(self):
        engine = sa.create_engine(self.database_url)
        try:
            inspector = sa.inspect(engine)
            return {
                "tables": set(inspector.get_table_names()),
                "audit_columns": {
                    column["name"]
                    for column in inspector.get_columns("audit_logs")
                },
                "notification_columns": {
                    column["name"]
                    for column in inspector.get_columns(
                        "activity_notifications"
                    )
                },
                "checks": {
                    check["name"]
                    for check in inspector.get_check_constraints(
                        "contract_negotiations"
                    )
                }
                if inspector.has_table("contract_negotiations")
                else set(),
                "acceptance_foreign_keys": {
                    foreign_key["name"]
                    for foreign_key in inspector.get_foreign_keys(
                        "negotiation_acceptances"
                    )
                }
                if inspector.has_table("negotiation_acceptances")
                else set(),
            }
        finally:
            engine.dispose()

    def test_phase2a_upgrade_downgrade_upgrade_is_reversible(self):
        command.upgrade(self.config, "20260726_03")
        self.assertEqual(self._revision(), "20260726_03")
        self.assertNotIn("contract_negotiations", self._schema()["tables"])

        command.upgrade(self.config, "head")
        schema = self._schema()
        self.assertEqual(self._revision(), "20260726_06")
        self.assertTrue(
            {
                "contract_negotiations",
                "contract_negotiation_versions",
                "negotiation_acceptances",
                "negotiation_events",
            }.issubset(schema["tables"])
        )
        self.assertIn("negotiation_event_id", schema["audit_columns"])
        self.assertIn("negotiation_event_id", schema["notification_columns"])
        self.assertTrue(
            {
                "ck_contract_negotiations_agreed_is_current",
                "ck_contract_negotiations_agreed_state",
                "ck_contract_negotiations_contract_state",
            }.issubset(schema["checks"])
        )

        command.downgrade(self.config, "20260726_03")
        schema = self._schema()
        self.assertEqual(self._revision(), "20260726_03")
        self.assertNotIn("contract_negotiations", schema["tables"])
        self.assertNotIn("negotiation_event_id", schema["audit_columns"])
        self.assertNotIn(
            "negotiation_event_id",
            schema["notification_columns"],
        )

        command.upgrade(self.config, "head")
        self.assertEqual(self._revision(), "20260726_06")
        self.assertIn("contract_negotiations", self._schema()["tables"])

    def test_downgrade_with_protected_data_blocks_before_constraints_change(self):
        command.upgrade(self.config, "head")
        engine = sa.create_engine(self.database_url)
        try:
            with engine.begin() as connection:
                client_id = connection.execute(
                    sa.text(
                        "INSERT INTO users "
                        "(nombre, email, password, rol, estado) "
                        "VALUES ('Client', 'migration-client@test.local', "
                        "'hash', 'CLIENTE', 'ACTIVO') RETURNING id"
                    )
                ).scalar_one()
                professional_user_id = connection.execute(
                    sa.text(
                        "INSERT INTO users "
                        "(nombre, email, password, rol, estado) "
                        "VALUES ('Professional', "
                        "'migration-professional@test.local', "
                        "'hash', 'PROFESIONAL', 'ACTIVO') RETURNING id"
                    )
                ).scalar_one()
                professional_id = connection.execute(
                    sa.text(
                        "INSERT INTO professionals "
                        "(user_id, nombre, servicio, zona, perfil_completo, "
                        "estado_perfil) VALUES "
                        "(:user_id, 'Professional', 'Electricidad', 'CABA', "
                        "1, 'VERIFICADO') RETURNING id"
                    ),
                    {"user_id": professional_user_id},
                ).scalar_one()
                negotiation_id = connection.execute(
                    sa.text(
                        "INSERT INTO contract_negotiations "
                        "(cliente_id, professional_id, professional_user_id, "
                        "servicio, state, contracting_mode, version, "
                        "current_terms_version) VALUES "
                        "(:client_id, :professional_id, "
                        ":professional_user_id, 'Servicio', 'OPEN', "
                        "'EXTERNAL', 1, 1) RETURNING id"
                    ),
                    {
                        "client_id": client_id,
                        "professional_id": professional_id,
                        "professional_user_id": professional_user_id,
                    },
                ).scalar_one()
                version_id = connection.execute(
                    sa.text(
                        "INSERT INTO contract_negotiation_versions "
                        "(negotiation_id, version_no, actor_user_id, "
                        "description, scope, external_price, payload_hash) "
                        "VALUES (:negotiation_id, 1, :actor_user_id, "
                        "'Description', 'Scope', 10, :payload_hash) "
                        "RETURNING id"
                    ),
                    {
                        "negotiation_id": negotiation_id,
                        "actor_user_id": client_id,
                        "payload_hash": "0" * 64,
                    },
                ).scalar_one()
                connection.execute(
                    sa.text(
                        "INSERT INTO negotiation_acceptances "
                        "(negotiation_id, negotiation_version_id, "
                        "actor_user_id, party) VALUES "
                        "(:negotiation_id, :version_id, :actor_user_id, "
                        "'CLIENT')"
                    ),
                    {
                        "negotiation_id": negotiation_id,
                        "version_id": version_id,
                        "actor_user_id": client_id,
                    },
                )

            with self.assertRaisesRegex(RuntimeError, "Downgrade bloqueado"):
                command.downgrade(self.config, "20260726_04")

            self.assertEqual(self._revision(), "20260726_05")
            schema = self._schema()
            self.assertIn(
                "fk_negotiation_acceptances_version_negotiation",
                schema["acceptance_foreign_keys"],
            )
            with engine.connect() as connection:
                self.assertEqual(
                    connection.execute(
                        sa.text(
                            "SELECT COUNT(*) FROM negotiation_acceptances"
                        )
                    ).scalar_one(),
                    1,
                )
                trigger_names = {
                    row[0]
                    for row in connection.execute(
                        sa.text(
                            "SELECT name FROM sqlite_master "
                            "WHERE type = 'trigger'"
                        )
                    )
                }
                self.assertIn(
                    "trg_contract_negotiation_versions_immutable",
                    trigger_names,
                )
                self.assertIn(
                    "trg_negotiation_acceptances_coherent_insert",
                    trigger_names,
                )
        finally:
            engine.dispose()

    def test_upgrade_normalizes_legacy_hash_and_blocks_unknown_corruption(self):
        command.upgrade(self.config, "20260726_04")
        legacy_payload = {
            "description": "Legacy description",
            "scope": "Legacy scope",
            "external_price": Decimal("10.00"),
            "estimated_start_at": datetime(2026, 8, 1, 10, 0),
            "estimated_end_at": datetime(2026, 8, 2, 18, 0),
            "observations": "Legacy observations",
        }
        legacy_hash = hashlib.sha256(
            json.dumps(
                legacy_payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()
        canonical_payload = {
            **legacy_payload,
            "external_price": "10.00",
            "estimated_start_at": "2026-08-01T10:00:00.000000",
            "estimated_end_at": "2026-08-02T18:00:00.000000",
        }
        canonical_hash = hashlib.sha256(
            json.dumps(
                canonical_payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()

        engine = sa.create_engine(self.database_url)
        try:
            snapshot_id = self._insert_phase2b_snapshot(
                engine,
                legacy_hash,
            )
            command.upgrade(self.config, "head")
            self.assertEqual(self._revision(), "20260726_06")
            with engine.connect() as connection:
                stored_hash = connection.execute(
                    sa.text(
                        "SELECT payload_hash "
                        "FROM contract_negotiation_versions WHERE id = :id"
                    ),
                    {"id": snapshot_id},
                ).scalar_one()
            self.assertEqual(stored_hash, canonical_hash)
        finally:
            engine.dispose()

    def test_upgrade_blocks_unknown_snapshot_hash_before_schema_mutation(self):
        command.upgrade(self.config, "20260726_04")
        engine = sa.create_engine(self.database_url)
        try:
            snapshot_id = self._insert_phase2b_snapshot(
                engine,
                "f" * 64,
            )
            with self.assertRaisesRegex(RuntimeError, "hash incoherente"):
                command.upgrade(self.config, "head")
            self.assertEqual(self._revision(), "20260726_04")
            schema = self._schema()
            self.assertNotIn(
                "fk_negotiation_acceptances_version_negotiation",
                schema["acceptance_foreign_keys"],
            )
            with engine.connect() as connection:
                self.assertEqual(
                    connection.execute(
                        sa.text(
                            "SELECT payload_hash "
                            "FROM contract_negotiation_versions "
                            "WHERE id = :id"
                        ),
                        {"id": snapshot_id},
                    ).scalar_one(),
                    "f" * 64,
                )
                trigger_count = connection.execute(
                    sa.text(
                        "SELECT COUNT(*) FROM sqlite_master "
                        "WHERE type = 'trigger' "
                        "AND name LIKE 'trg_%negotiation%'"
                    )
                ).scalar_one()
                self.assertEqual(trigger_count, 0)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main(verbosity=2)
