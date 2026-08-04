import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Sprint7ContractReviewMigrationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary.name) / "contract-review-migration.db"
        self.database_url = f"sqlite:///{database_path.as_posix()}"
        self.config = Config(str(PROJECT_ROOT / "alembic.ini"))
        self.previous_database_url = os.environ.get("DATABASE_URL")
        self.previous_secret_key = os.environ.get("SECRET_KEY")
        os.environ["DATABASE_URL"] = self.database_url
        os.environ["SECRET_KEY"] = "contract-review-migration-test"
        self.engine = sa.create_engine(self.database_url)

    def tearDown(self):
        self.engine.dispose()
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
        with self.engine.connect() as connection:
            return connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()

    def _trigger_names(self):
        with self.engine.connect() as connection:
            return {
                row[0]
                for row in connection.execute(
                    sa.text(
                        "SELECT name FROM sqlite_master WHERE type='trigger'"
                    )
                )
            }

    def _create_party(self, connection, suffix):
        client_id = connection.execute(
            sa.text(
                "INSERT INTO users (nombre, email, password, rol, estado) "
                "VALUES (:name, :email, 'hash', 'CLIENTE', 'ACTIVO') "
                "RETURNING id"
            ),
            {
                "name": f"Client {suffix}",
                "email": f"client-{suffix}@migration.test",
            },
        ).scalar_one()
        professional_user_id = connection.execute(
            sa.text(
                "INSERT INTO users (nombre, email, password, rol, estado) "
                "VALUES (:name, :email, 'hash', 'PROFESIONAL', 'ACTIVO') "
                "RETURNING id"
            ),
            {
                "name": f"Professional {suffix}",
                "email": f"professional-{suffix}@migration.test",
            },
        ).scalar_one()
        professional_id = connection.execute(
            sa.text(
                "INSERT INTO professionals "
                "(user_id, nombre, servicio, zona, perfil_completo, "
                "estado_perfil) VALUES (:user_id, :name, 'Servicio', "
                "'CABA', 1, 'VERIFICADO') RETURNING id"
            ),
            {
                "user_id": professional_user_id,
                "name": f"Professional {suffix}",
            },
        ).scalar_one()
        return client_id, professional_user_id, professional_id

    def _create_contract(
        self,
        connection,
        client_id,
        professional_user_id,
        professional_id,
        *,
        state="CONFIRMADA",
        created_at=None,
        confirmed_at=None,
    ):
        created_at = created_at or datetime(2026, 7, 1, 10, 0)
        if confirmed_at is None and state == "CONFIRMADA":
            confirmed_at = created_at + timedelta(hours=1)
        return connection.execute(
            sa.text(
                "INSERT INTO contract_requests "
                "(cliente_id, professional_id, professional_user_id, "
                "source_type, servicio, estado, contracting_mode, version, "
                "fecha_creacion, confirmed_at) VALUES "
                "(:client_id, :professional_id, :professional_user_id, "
                "'DIRECT', 'Servicio', :state, 'EXTERNAL', 1, "
                ":created_at, :confirmed_at) RETURNING id"
            ),
            {
                "client_id": client_id,
                "professional_id": professional_id,
                "professional_user_id": professional_user_id,
                "state": state,
                "created_at": created_at,
                "confirmed_at": confirmed_at,
            },
        ).scalar_one()

    def _create_legacy_review(
        self,
        connection,
        client_id,
        professional_id,
        *,
        rating=5,
        created_at=None,
        comment="Legacy comment",
        state="VISIBLE",
    ):
        return connection.execute(
            sa.text(
                "INSERT INTO reviews "
                "(cliente_id, professional_id, rating, comentario, estado, "
                "created_at) VALUES (:client_id, :professional_id, :rating, "
                ":comment, :state, :created_at) RETURNING id"
            ),
            {
                "client_id": client_id,
                "professional_id": professional_id,
                "rating": rating,
                "comment": comment,
                "state": state,
                "created_at": created_at or datetime(2026, 7, 2, 10, 0),
            },
        ).scalar_one()

    def _create_contractual_review(
        self,
        connection,
        *,
        contract_id,
        client_id,
        professional_id,
        rating=5,
        correlation="00000000-0000-4000-8000-000000000001",
    ):
        return connection.execute(
            sa.text(
                "INSERT INTO reviews "
                "(contract_id, cliente_id, professional_id, rating, "
                "comentario, comment_public, origin, verification_status, "
                "comment_visibility_status, rating_eligibility_status, "
                "correlation_id, payload_hash, estado, created_at) VALUES "
                "(:contract_id, :client_id, :professional_id, :rating, "
                "'Contract review', 'Contract review', 'CONTRACTUAL', "
                "'VERIFIED', 'VISIBLE', 'ELIGIBLE', :correlation, "
                ":payload_hash, 'VISIBLE', :created_at) RETURNING id"
            ),
            {
                "contract_id": contract_id,
                "client_id": client_id,
                "professional_id": professional_id,
                "rating": rating,
                "correlation": correlation,
                "payload_hash": "a" * 64,
                "created_at": datetime(2026, 7, 3, 10, 0),
            },
        ).scalar_one()

    def _create_contractual_event(
        self,
        connection,
        *,
        review_id,
        contract_id,
        professional_user_id,
        rating=5,
        points=None,
        correlation="00000000-0000-4000-8000-000000000001",
    ):
        return connection.execute(
            sa.text(
                "INSERT INTO reputation_events "
                "(user_id, review_id, contract_id, source_type, event_type, "
                "event_value, origin, correlation_id, tipo_evento, puntos, "
                "descripcion, created_at) VALUES "
                "(:user_id, :review_id, :contract_id, 'CONTRACT_REVIEW', "
                "'REVIEW_RECORDED', :rating, 'CONTRACTUAL', :correlation, "
                "'REVIEW_RECORDED', :points, 'Observed rating', :created_at) "
                "RETURNING id"
            ),
            {
                "user_id": professional_user_id,
                "review_id": review_id,
                "contract_id": contract_id,
                "rating": rating,
                "correlation": correlation,
                "points": points,
                "created_at": datetime(2026, 7, 3, 10, 1),
            },
        ).scalar_one()

    def test_empty_upgrade_from_base_and_reupgrade_install_physical_objects(self):
        command.upgrade(self.config, "20260726_05")
        command.upgrade(self.config, "head")
        self.assertEqual(self._revision(), "20260726_06")
        inspector = sa.inspect(self.engine)
        review_columns = {c["name"] for c in inspector.get_columns("reviews")}
        event_columns = {
            c["name"] for c in inspector.get_columns("reputation_events")
        }
        self.assertTrue(
            {"contract_id", "origin", "legacy_metadata_json"}.issubset(
                review_columns
            )
        )
        self.assertTrue(
            {"review_id", "source_type", "event_value"}.issubset(event_columns)
        )
        self.assertTrue(
            {
                "trg_reviews_contract_integrity_insert_v1",
                "trg_reviews_contract_integrity_update_v1",
                "trg_reputation_events_integrity_insert_v1",
                "trg_reputation_events_integrity_update_v1",
            }.issubset(self._trigger_names())
        )
        command.downgrade(self.config, "20260726_05")
        self.assertEqual(self._revision(), "20260726_05")
        self.assertNotIn(
            "contract_id",
            {c["name"] for c in sa.inspect(self.engine).get_columns("reviews")},
        )
        command.upgrade(self.config, "head")
        self.assertEqual(self._revision(), "20260726_06")

    def test_legacy_classification_is_closed_reconciled_and_non_reputational(self):
        command.upgrade(self.config, "20260726_05")
        with self.engine.begin() as connection:
            c1, pu1, p1 = self._create_party(connection, "unique")
            contract1 = self._create_contract(connection, c1, pu1, p1)
            unique_review = self._create_legacy_review(connection, c1, p1)

            c2, pu2, p2 = self._create_party(connection, "duplicate")
            self._create_contract(connection, c2, pu2, p2)
            duplicate_a = self._create_legacy_review(connection, c2, p2)
            duplicate_b = self._create_legacy_review(
                connection, c2, p2, comment="Second competing review"
            )

            c3, _pu3, p3 = self._create_party(connection, "no-contract")
            no_candidate = self._create_legacy_review(connection, c3, p3)

            c4, pu4, p4 = self._create_party(connection, "invalid-rating")
            self._create_contract(connection, c4, pu4, p4)
            invalid_rating = self._create_legacy_review(
                connection, c4, p4, rating=6
            )
            connection.execute(
                sa.text(
                    "INSERT INTO reputation_events "
                    "(user_id, tipo_evento, puntos, descripcion, created_at) "
                    "VALUES (:user_id, 'REVIEW_POSITIVA', 10, 'Legacy', "
                    ":created_at)"
                ),
                {"user_id": pu1, "created_at": datetime(2026, 7, 2, 11, 0)},
            )

        command.upgrade(self.config, "head")
        with self.engine.connect() as connection:
            rows = {
                row.id: row
                for row in connection.execute(
                    sa.text(
                        "SELECT id, contract_id, rating, origin, "
                        "verification_status, rating_eligibility_status, "
                        "legacy_metadata_json FROM reviews"
                    ).columns(legacy_metadata_json=sa.JSON())
                )
            }
            self.assertEqual(
                (
                    rows[unique_review].contract_id,
                    rows[unique_review].verification_status,
                    rows[unique_review].rating_eligibility_status,
                ),
                (contract1, "VERIFIED", "ELIGIBLE"),
            )
            for review_id in (duplicate_a, duplicate_b):
                self.assertIsNone(rows[review_id].contract_id)
                self.assertEqual(
                    rows[review_id].legacy_metadata_json["classification_code"],
                    "DUPLICATE_FOR_CONTRACT",
                )
            self.assertEqual(
                rows[no_candidate].legacy_metadata_json["classification_code"],
                "NO_CANDIDATE",
            )
            self.assertIsNone(rows[invalid_rating].rating)
            self.assertEqual(
                rows[invalid_rating].legacy_metadata_json["original_rating"],
                6,
            )
            self.assertEqual(
                rows[invalid_rating].rating_eligibility_status,
                "EXCLUDED",
            )
            event = connection.execute(
                sa.text(
                    "SELECT source_type, origin, review_id FROM reputation_events"
                )
            ).one()
            self.assertEqual(event.source_type, "LEGACY_EVENT")
            self.assertEqual(event.origin, "LEGACY")
            self.assertIsNone(event.review_id)

        command.downgrade(self.config, "20260726_05")
        with self.engine.connect() as connection:
            restored = connection.execute(
                sa.text("SELECT rating FROM reviews WHERE id=:id"),
                {"id": invalid_rating},
            ).scalar_one()
            self.assertEqual(restored, 6)
            self.assertEqual(
                connection.execute(
                    sa.text("SELECT COUNT(*) FROM reviews")
                ).scalar_one(),
                5,
            )

    def test_sqlite_unique_checks_and_triggers_reject_incoherent_writes(self):
        command.upgrade(self.config, "head")
        connection = self.engine.connect()
        try:
            transaction = connection.begin()
            client, professional_user, professional = self._create_party(
                connection, "physical"
            )
            contract = self._create_contract(
                connection, client, professional_user, professional
            )
            review = self._create_contractual_review(
                connection,
                contract_id=contract,
                client_id=client,
                professional_id=professional,
            )
            self._create_contractual_event(
                connection,
                review_id=review,
                contract_id=contract,
                professional_user_id=professional_user,
            )
            transaction.commit()

            invalid_statements = (
                (
                    "INSERT INTO reviews (cliente_id, professional_id, rating, "
                    "origin, estado, created_at) VALUES (:client, :professional, "
                    "5, 'LEGACY', 'VISIBLE', :created)",
                    {},
                ),
                (
                    "UPDATE reviews SET rating=4 WHERE id=:review",
                    {},
                ),
                (
                    "INSERT INTO reputation_events "
                    "(user_id, source_type, tipo_evento, puntos, created_at) "
                    "VALUES (:professional_user, 'LEGACY_EVENT', 'X', 1, "
                    ":created)",
                    {},
                ),
                (
                    "UPDATE reputation_events SET event_value=4 "
                    "WHERE review_id=:review",
                    {},
                ),
                (
                    "INSERT INTO reputation_events "
                    "(user_id, review_id, contract_id, source_type, event_type, "
                    "event_value, origin, correlation_id, tipo_evento, puntos, "
                    "created_at) VALUES (:professional_user, NULL, :contract, "
                    "'CONTRACT_REVIEW', 'REVIEW_RECORDED', 5, 'CONTRACTUAL', "
                    "'00000000-0000-4000-8000-000000000099', "
                    "'REVIEW_RECORDED', 5, :created)",
                    {},
                ),
            )
            params = {
                "client": client,
                "professional": professional,
                "professional_user": professional_user,
                "contract": contract,
                "review": review,
                "created": datetime(2026, 7, 4, 10, 0),
            }
            for statement, extra in invalid_statements:
                with self.subTest(statement=statement[:30]):
                    with self.assertRaises(IntegrityError):
                        connection.execute(sa.text(statement), {**params, **extra})
                        connection.commit()
                    connection.rollback()
                    self.assertEqual(
                        connection.execute(sa.text("SELECT COUNT(*) FROM users")).scalar_one(),
                        2,
                    )

            with self.assertRaises(IntegrityError):
                self._create_contractual_review(
                    connection,
                    contract_id=contract,
                    client_id=client,
                    professional_id=professional,
                    correlation="00000000-0000-4000-8000-000000000002",
                )
                connection.commit()
            connection.rollback()
            self.assertEqual(
                connection.execute(sa.text("SELECT COUNT(*) FROM reviews")).scalar_one(),
                1,
            )
        finally:
            connection.close()

    def test_review_trigger_rejects_nonconfirmed_and_mismatched_contracts(self):
        command.upgrade(self.config, "head")
        connection = self.engine.connect()
        try:
            with connection.begin():
                client, professional_user, professional = self._create_party(
                    connection, "state"
                )
                contract = self._create_contract(
                    connection,
                    client,
                    professional_user,
                    professional,
                    state="COMPLETADA",
                )
            with self.assertRaises(IntegrityError):
                self._create_contractual_review(
                    connection,
                    contract_id=contract,
                    client_id=client,
                    professional_id=professional,
                )
                connection.commit()
            connection.rollback()
            with connection.begin():
                connection.execute(
                    sa.text(
                        "UPDATE contract_requests SET estado='CONFIRMADA', "
                        "confirmed_at=:confirmed WHERE id=:id"
                    ),
                    {"confirmed": datetime(2026, 7, 2), "id": contract},
                )
            with self.assertRaises(IntegrityError):
                self._create_contractual_review(
                    connection,
                    contract_id=contract,
                    client_id=client + 1000,
                    professional_id=professional,
                )
                connection.commit()
            connection.rollback()
            self.assertEqual(
                connection.execute(sa.text("SELECT COUNT(*) FROM reviews")).scalar_one(),
                0,
            )
        finally:
            connection.close()

    def test_downgrade_blocks_contractual_data_before_mutation(self):
        command.upgrade(self.config, "head")
        with self.engine.begin() as connection:
            client, professional_user, professional = self._create_party(
                connection, "downgrade-block"
            )
            contract = self._create_contract(
                connection, client, professional_user, professional
            )
            self._create_contractual_review(
                connection,
                contract_id=contract,
                client_id=client,
                professional_id=professional,
            )

        with self.assertRaisesRegex(RuntimeError, "reviews contractuales"):
            command.downgrade(self.config, "20260726_05")
        self.assertEqual(self._revision(), "20260726_06")
        self.assertIn(
            "trg_reviews_contract_integrity_insert_v1",
            self._trigger_names(),
        )
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.execute(sa.text("SELECT COUNT(*) FROM reviews")).scalar_one(),
                1,
            )

    def test_downgrade_blocks_moderated_legacy_data_before_mutation(self):
        command.upgrade(self.config, "20260726_05")
        with self.engine.begin() as connection:
            client, _professional_user, professional = self._create_party(
                connection, "moderated"
            )
            review = self._create_legacy_review(connection, client, professional)
        command.upgrade(self.config, "head")
        with self.engine.begin() as connection:
            connection.execute(
                sa.text(
                    "UPDATE reviews SET moderated_at=:now, "
                    "moderation_reason='Privacy' WHERE id=:id"
                ),
                {"now": datetime(2026, 8, 4), "id": review},
            )
        with self.assertRaisesRegex(RuntimeError, "moderacion posterior"):
            command.downgrade(self.config, "20260726_05")
        self.assertEqual(self._revision(), "20260726_06")
        self.assertIn("legacy_metadata_json", {
            column["name"] for column in sa.inspect(self.engine).get_columns("reviews")
        })

    def test_partial_schema_preflight_blocks_without_touching_data_or_revision(self):
        command.upgrade(self.config, "20260726_05")
        with self.engine.begin() as connection:
            client, _professional_user, professional = self._create_party(
                connection, "partial"
            )
            review = self._create_legacy_review(connection, client, professional)
            connection.execute(
                sa.text("ALTER TABLE reviews ADD COLUMN contract_id INTEGER")
            )
        with self.assertRaisesRegex(RuntimeError, "columnas parciales"):
            command.upgrade(self.config, "head")
        self.assertEqual(self._revision(), "20260726_05")
        with self.engine.connect() as connection:
            row = connection.execute(
                sa.text("SELECT rating, comentario FROM reviews WHERE id=:id"),
                {"id": review},
            ).one()
            self.assertEqual((row.rating, row.comentario), (5, "Legacy comment"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
