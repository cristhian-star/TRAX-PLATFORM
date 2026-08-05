"""Mandatory disposable-PostgreSQL gate for contractual reviews.

This module is intentionally outside ``test_*.py`` discovery. It upgrades,
truncates, downgrades, and re-upgrades the database named by
``TRAX_POSTGRES_TEST_URL``. The reset opt-in is mandatory.
"""

import os
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

POSTGRES_URL = os.environ.get("TRAX_POSTGRES_TEST_URL")
ALLOW_RESET = os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET") == "1"
if POSTGRES_URL:
    os.environ["DATABASE_URL"] = POSTGRES_URL
os.environ.setdefault("SECRET_KEY", "postgres-contract-review-e2e")

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.reputation_event import ReputationEvent
from app.models.review import Review
from app.models.user import User
from app.services import contract_review_service
from app.services.contract_review_service import (
    ContractReviewConflictError,
    ContractReviewIdempotencyConflictError,
    create_contract_review,
)


class ContractReviewPostgreSQLGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not POSTGRES_URL:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_URL es obligatorio para el gate de reviews"
            )
        url = make_url(POSTGRES_URL)
        if url.get_backend_name() not in ("postgresql", "postgres"):
            raise RuntimeError("TRAX_POSTGRES_TEST_URL debe apuntar a PostgreSQL")
        if not ALLOW_RESET:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_ALLOW_RESET=1 es obligatorio: la base sera truncada"
            )
        cls.config = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.upgrade(cls.config, "head")
        cls.app = create_app(initialize_schema=False)
        cls.app.config.update(TESTING=True)
        with cls.app.app_context():
            revision = db.session.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            if revision != "20260726_07":
                raise RuntimeError(f"Revision Alembic inesperada: {revision}")
            if db.engine.dialect.name != "postgresql":
                raise RuntimeError("El gate no esta ejecutando PostgreSQL")
            version = db.session.execute(sa.text("SHOW server_version")).scalar_one()
            print(f"PostgreSQL server_version={version}", flush=True)

    def _truncate_database(self):
        with self.app.app_context():
            table_names = [
                table.name
                for table in reversed(db.metadata.sorted_tables)
                if table.name != "alembic_version"
            ]
            quoted = ", ".join(
                db.engine.dialect.identifier_preparer.quote(table)
                for table in table_names
            )
            db.session.execute(
                sa.text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
            )
            db.session.commit()

    def setUp(self):
        self._truncate_database()
        with self.app.app_context():
            suffix = uuid4().hex
            client = User(
                nombre="PG Review Client",
                email=f"review-client-{suffix}@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            other_client = User(
                nombre="PG Other Client",
                email=f"review-other-{suffix}@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="PG Review Professional",
                email=f"review-professional-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all([client, other_client, professional_user])
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="PG Review Professional",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(professional)
            db.session.flush()
            contract = ContractRequest(
                cliente_id=client.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                source_type=ContractRequest.SOURCE_DIRECT,
                servicio="Servicio confirmado",
                estado="CONFIRMADA",
                contracting_mode="EXTERNAL",
                version=5,
                confirmed_at=datetime(2026, 8, 1, 12, 0),
            )
            db.session.add(contract)
            db.session.commit()
            self.client_id = client.id
            self.other_client_id = other_client.id
            self.professional_user_id = professional_user.id
            self.professional_id = professional.id
            self.contract_id = contract.id

    def tearDown(self):
        self._truncate_database()

    def _create(self, key, *, rating=5, comment="Excelente trabajo"):
        return create_contract_review(
            actor_user_id=self.client_id,
            contract_id=self.contract_id,
            rating=rating,
            comment=comment,
            idempotency_key=key,
        )

    def _counts(self):
        return {
            "reviews": Review.query.count(),
            "reputation_events": ReputationEvent.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
            "commands": OperationCommand.query.count(),
            "contract_events": ContractEvent.query.count(),
        }

    def _run_two_services(self, calls):
        barrier = threading.Barrier(2, timeout=10)
        backend_pids = [None, None]
        connection_ids = [None, None]
        results = [None, None]
        errors = [None, None]
        reusable = [False, False]
        original = contract_review_service._lock_contract

        def coordinated(*args, **kwargs):
            barrier.wait()
            return original(*args, **kwargs)

        def worker(index):
            with self.app.app_context():
                connection = db.session.connection()
                connection_ids[index] = id(connection.connection)
                backend_pids[index] = db.session.execute(
                    sa.text("SELECT pg_backend_pid()")
                ).scalar_one()
                try:
                    results[index] = calls[index]().id
                except Exception as error:
                    errors[index] = error
                finally:
                    reusable[index] = User.query.count() == 3
                    db.session.remove()

        with patch.object(
            contract_review_service,
            "_lock_contract",
            side_effect=coordinated,
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(worker, index) for index in range(2)]
                for future in futures:
                    future.result(timeout=30)
        self.assertEqual(len(set(backend_pids)), 2)
        self.assertEqual(len(set(connection_ids)), 2)
        self.assertEqual(reusable, [True, True])
        print(
            f"{self._testMethodName}: pg_backend_pid={sorted(backend_pids)} "
            f"connection_ids={connection_ids}",
            flush=True,
        )
        return results, errors

    def _assert_one_complete_effect_set(self):
        self.assertEqual(
            self._counts(),
            {
                "reviews": 1,
                "reputation_events": 1,
                "audits": 1,
                "notifications": 1,
                "commands": 1,
                "contract_events": 0,
            },
        )
        event = ReputationEvent.query.one()
        review = Review.query.one()
        self.assertEqual(event.event_value, review.rating)
        self.assertIn(event.event_value, (1, 2, 3, 4, 5))
        self.assertIsNone(event.puntos)

    def test_physical_objects_are_installed_and_service_creates_neutral_fact(self):
        with self.app.app_context():
            trigger_names = {
                row[0]
                for row in db.session.execute(
                    sa.text(
                        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal "
                        "AND tgrelid IN ('reviews'::regclass, "
                        "'reputation_events'::regclass)"
                    )
                )
            }
            self.assertEqual(
                trigger_names,
                {
                    "trg_reviews_contract_integrity_v2",
                    "trg_reputation_events_integrity_v2",
                },
            )
            constraint_names = {
                row[0]
                for row in db.session.execute(
                    sa.text(
                        "SELECT conname FROM pg_constraint WHERE conrelid IN "
                        "('reviews'::regclass, 'reputation_events'::regclass)"
                    )
                )
            }
            self.assertTrue(
                {
                    "uq_reviews_contract_id",
                    "uq_reputation_events_review_id",
                    "ck_reviews_contractual_integrity",
                    "ck_reputation_events_contract_review_integrity",
                    "ck_reviews_origin_required_v2",
                    "ck_reputation_events_discriminators_required_v2",
                }.issubset(constraint_names)
            )
            review = self._create("pg-review-physical-success-0001")
            self.assertEqual(review.contract_id, self.contract_id)
            self._assert_one_complete_effect_set()

    def test_same_key_same_payload_concurrently_replays_one_review(self):
        calls = [
            lambda: self._create("pg-review-same-key-0001"),
            lambda: self._create("pg-review-same-key-0001"),
        ]
        results, errors = self._run_two_services(calls)
        self.assertEqual(errors, [None, None])
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            self._assert_one_complete_effect_set()

    def test_same_key_different_payload_concurrently_conflicts_without_partial_work(self):
        calls = [
            lambda: self._create("pg-review-payload-key-0001", rating=5),
            lambda: self._create("pg-review-payload-key-0001", rating=4),
        ]
        results, errors = self._run_two_services(calls)
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(
            sum(
                isinstance(error, ContractReviewIdempotencyConflictError)
                for error in errors
            ),
            1,
        )
        with self.app.app_context():
            self._assert_one_complete_effect_set()

    def test_different_keys_same_contract_concurrently_commit_one_command(self):
        calls = [
            lambda: self._create("pg-review-different-key-a-0001"),
            lambda: self._create("pg-review-different-key-b-0001"),
        ]
        results, errors = self._run_two_services(calls)
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(
            sum(isinstance(error, ContractReviewConflictError) for error in errors),
            1,
        )
        with self.app.app_context():
            self._assert_one_complete_effect_set()

    def test_unique_constraint_collides_across_independent_sessions(self):
        barrier = threading.Barrier(2, timeout=10)
        pids = [None, None]
        errors = [None, None]
        reusable = [False, False]
        with self.app.app_context():
            engine = db.engine
        Session = sessionmaker(bind=engine, expire_on_commit=False)

        def worker(index):
            session = Session()
            try:
                pids[index] = session.execute(
                    sa.text("SELECT pg_backend_pid()")
                ).scalar_one()
                review = Review(
                    contract_id=self.contract_id,
                    cliente_id=self.client_id,
                    professional_id=self.professional_id,
                    rating=5,
                    comentario=f"Physical collision {index}",
                    comment_public=f"Physical collision {index}",
                    origin="CONTRACTUAL",
                    verification_status="VERIFIED",
                    comment_visibility_status="VISIBLE",
                    rating_eligibility_status="ELIGIBLE",
                    correlation_id=f"00000000-0000-4000-8000-00000000001{index}",
                    payload_hash=str(index) * 64,
                    estado="VISIBLE",
                )
                session.add(review)
                barrier.wait()
                session.commit()
            except Exception as error:
                errors[index] = error
                session.rollback()
            finally:
                reusable[index] = session.query(User).count() == 3
                session.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker, index) for index in range(2)]
            for future in futures:
                future.result(timeout=30)
        self.assertEqual(len(set(pids)), 2)
        self.assertEqual(sum(error is None for error in errors), 1)
        self.assertEqual(sum(isinstance(error, IntegrityError) for error in errors), 1)
        self.assertEqual(reusable, [True, True])
        print(
            f"{self._testMethodName}: pg_backend_pid={sorted(pids)}",
            flush=True,
        )
        with self.app.app_context():
            self.assertEqual(Review.query.count(), 1)
            self.assertEqual(ReputationEvent.query.count(), 0)

    def test_real_trigger_error_rolls_back_every_effect_and_session_recovers(self):
        with self.app.app_context():
            original = contract_review_service._create_review

            def create_incoherent(*args, **kwargs):
                review = original(*args, **kwargs)
                review.cliente_id = self.other_client_id
                return review

            with patch.object(
                contract_review_service,
                "_create_review",
                side_effect=create_incoherent,
            ):
                with self.assertRaises(IntegrityError):
                    self._create("pg-review-real-trigger-rollback-0001")
            self.assertEqual(
                self._counts(),
                {
                    "reviews": 0,
                    "reputation_events": 0,
                    "audits": 0,
                    "notifications": 0,
                    "commands": 0,
                    "contract_events": 0,
                },
            )
            self.assertEqual(User.query.count(), 3)

    def test_direct_sql_cannot_create_legacy_event_or_contract_points(self):
        with self.app.app_context():
            review = self._create("pg-review-direct-sql-0001")
            baseline = self._counts()
            with self.assertRaises(IntegrityError):
                db.session.execute(
                    sa.text(
                        "INSERT INTO reputation_events "
                        "(user_id, source_type, tipo_evento, puntos, created_at) "
                        "VALUES (:user_id, 'LEGACY_EVENT', 'X', 1, NOW())"
                    ),
                    {"user_id": self.professional_user_id},
                )
                db.session.commit()
            db.session.rollback()
            with self.assertRaises(IntegrityError):
                db.session.execute(
                    sa.text(
                        "UPDATE reputation_events SET puntos=5 WHERE review_id=:id"
                    ),
                    {"id": review.id},
                )
                db.session.commit()
            db.session.rollback()
            self.assertEqual(self._counts(), baseline)
            self.assertEqual(User.query.count(), 3)

    def test_null_and_unknown_discriminator_attacks_are_physically_rejected(self):
        with self.app.app_context():
            created_contract = ContractRequest(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                source_type=ContractRequest.SOURCE_DIRECT,
                servicio="Contrato no confirmado",
                estado="CREADA",
                contracting_mode="EXTERNAL",
                version=1,
            )
            completed_contract = ContractRequest(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                source_type=ContractRequest.SOURCE_DIRECT,
                servicio="Contrato completado",
                estado="COMPLETADA",
                contracting_mode="EXTERNAL",
                version=1,
            )
            cancelled_contract = ContractRequest(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                source_type=ContractRequest.SOURCE_DIRECT,
                servicio="Contrato cancelado",
                estado="CANCELADA",
                contracting_mode="EXTERNAL",
                version=1,
            )
            db.session.add_all(
                [created_contract, completed_contract, cancelled_contract]
            )
            crossed_user = User(
                nombre="PG Crossed Professional",
                email=f"crossed-{uuid4().hex}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add(crossed_user)
            db.session.flush()
            crossed_professional = Professional(
                user_id=crossed_user.id,
                nombre="PG Crossed Professional",
                servicio="Otro servicio",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(crossed_professional)
            db.session.flush()
            mismatched_owner_contract = ContractRequest(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=crossed_user.id,
                source_type=ContractRequest.SOURCE_DIRECT,
                servicio="Contrato con ownership incoherente",
                estado="CONFIRMADA",
                contracting_mode="EXTERNAL",
                version=1,
            )
            db.session.add(mismatched_owner_contract)
            db.session.commit()
            review_sql = sa.text(
                "INSERT INTO reviews (contract_id, cliente_id, professional_id, "
                "rating, comentario, comment_public, origin, verification_status, "
                "comment_visibility_status, rating_eligibility_status, "
                "correlation_id, payload_hash, estado, created_at) VALUES "
                "(:contract, :client, :professional, 5, 'Attack', 'Attack', "
                ":origin, 'VERIFIED', 'VISIBLE', 'ELIGIBLE', :correlation, "
                ":payload_hash, 'VISIBLE', NOW())"
            )
            review_common = {
                "contract": self.contract_id,
                "client": self.client_id,
                "professional": self.professional_id,
                "origin": "CONTRACTUAL",
                "correlation": "00000000-0000-4000-8000-000000000730",
                "payload_hash": "a" * 64,
            }
            for attack in (
                {"contract": None, "origin": None},
                {"contract": created_contract.id, "origin": None},
                {"origin": None},
                {"origin": None, "client": self.other_client_id},
                {"contract": created_contract.id},
                {"contract": completed_contract.id},
                {"contract": cancelled_contract.id},
                {"contract": mismatched_owner_contract.id},
                {"client": self.other_client_id},
                {"professional": crossed_professional.id},
                {"origin": "UNKNOWN"},
                {"origin": "LEGACY"},
            ):
                with self.subTest(review_attack=attack):
                    with self.assertRaises(IntegrityError):
                        db.session.execute(review_sql, {**review_common, **attack})
                        db.session.commit()
                    db.session.rollback()
                    self.assertEqual(Review.query.count(), 0)
                    self.assertEqual(User.query.count(), 4)
                    self.assertEqual(
                        db.session.execute(
                            sa.text("SELECT version_num FROM alembic_version")
                        ).scalar_one(),
                        "20260726_07",
                    )

            orm_attack = Review(
                contract_id=self.contract_id,
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                rating=5,
                comentario="ORM null",
                comment_public="ORM null",
                origin=None,
                verification_status="VERIFIED",
                comment_visibility_status="VISIBLE",
                rating_eligibility_status="ELIGIBLE",
                correlation_id="00000000-0000-4000-8000-000000000731",
                payload_hash="b" * 64,
                estado="VISIBLE",
            )
            db.session.add(orm_attack)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            self.assertEqual(User.query.count(), 4)

            db.session.execute(review_sql, review_common)
            db.session.commit()
            review = Review.query.one()
            for invalid_origin in (None, "UNKNOWN"):
                with self.subTest(review_update_origin=invalid_origin):
                    with self.assertRaises(IntegrityError):
                        db.session.execute(
                            sa.text("UPDATE reviews SET origin=:origin WHERE id=:id"),
                            {"origin": invalid_origin, "id": review.id},
                        )
                        db.session.commit()
                    db.session.rollback()
                    self.assertEqual(Review.query.one().origin, "CONTRACTUAL")
                    self.assertEqual(User.query.count(), 4)

            event_sql = sa.text(
                "INSERT INTO reputation_events (user_id, review_id, contract_id, "
                "source_type, event_type, event_value, origin, correlation_id, "
                "tipo_evento, puntos, created_at) VALUES (:user, :review, "
                ":contract, :source, :event_type, :event_value, :origin, "
                ":correlation, 'REVIEW_RECORDED', :points, NOW())"
            )
            event_common = {
                "user": self.professional_user_id,
                "review": review.id,
                "contract": self.contract_id,
                "source": "CONTRACT_REVIEW",
                "event_type": "REVIEW_RECORDED",
                "event_value": 5,
                "origin": "CONTRACTUAL",
                "correlation": review.correlation_id,
                "points": None,
            }
            for attack in (
                {"source": None},
                {"origin": None},
                {"event_type": None},
                {"event_value": None},
                {"event_type": "UNKNOWN"},
                {"event_value": 0},
                {"event_value": 6},
                {"contract": None},
                {"review": None},
                {"review": None, "contract": None},
                {"points": 5},
                {"source": "LEGACY_EVENT", "origin": "LEGACY"},
                {"source": "UNKNOWN"},
                {"origin": "UNKNOWN"},
            ):
                with self.subTest(event_attack=attack):
                    with self.assertRaises(IntegrityError):
                        db.session.execute(event_sql, {**event_common, **attack})
                        db.session.commit()
                    db.session.rollback()
                    self.assertEqual(ReputationEvent.query.count(), 0)
                    self.assertEqual(User.query.count(), 4)
                    self.assertEqual(
                        db.session.execute(
                            sa.text("SELECT version_num FROM alembic_version")
                        ).scalar_one(),
                        "20260726_07",
                    )

            db.session.execute(event_sql, event_common)
            db.session.commit()
            event = ReputationEvent.query.one()
            for column, value in (
                ("source_type", None),
                ("origin", None),
                ("source_type", "UNKNOWN"),
                ("origin", "UNKNOWN"),
            ):
                with self.subTest(event_update=column, value=value):
                    with self.assertRaises(IntegrityError):
                        db.session.execute(
                            sa.text(
                                f"UPDATE reputation_events SET {column}=:value WHERE id=:id"
                            ),
                            {"value": value, "id": event.id},
                        )
                        db.session.commit()
                    db.session.rollback()
                    self.assertEqual(ReputationEvent.query.count(), 1)
                    self.assertEqual(User.query.count(), 4)
                    self.assertEqual(
                        db.session.execute(
                            sa.text("SELECT version_num FROM alembic_version")
                        ).scalar_one(),
                        "20260726_07",
                    )
            self.assertEqual(Review.query.count(), 1)
            self.assertEqual(ReputationEvent.query.count(), 1)
            self.assertEqual(User.query.count(), 4)

    def test_postgresql_legacy_upgrade_downgrade_reupgrade_preserves_rating(self):
        with self.app.app_context():
            db.session.remove()
        command.downgrade(self.config, "20260726_05")
        engine = sa.create_engine(POSTGRES_URL)
        try:
            with engine.begin() as connection:
                client = connection.execute(
                    sa.text(
                        "INSERT INTO users (nombre, email, password, rol, estado) "
                        "VALUES ('Legacy Client', :email, 'hash', 'CLIENTE', "
                        "'ACTIVO') RETURNING id"
                    ),
                    {"email": f"legacy-client-{uuid4().hex}@test.local"},
                ).scalar_one()
                professional_user = connection.execute(
                    sa.text(
                        "INSERT INTO users (nombre, email, password, rol, estado) "
                        "VALUES ('Legacy Professional', :email, 'hash', "
                        "'PROFESIONAL', 'ACTIVO') RETURNING id"
                    ),
                    {"email": f"legacy-professional-{uuid4().hex}@test.local"},
                ).scalar_one()
                professional = connection.execute(
                    sa.text(
                        "INSERT INTO professionals (user_id, nombre, servicio, "
                        "zona, perfil_completo, estado_perfil) VALUES "
                        "(:user_id, 'Legacy Professional', 'Servicio', 'CABA', "
                        "TRUE, 'VERIFICADO') RETURNING id"
                    ),
                    {"user_id": professional_user},
                ).scalar_one()
                review = connection.execute(
                    sa.text(
                        "INSERT INTO reviews (cliente_id, professional_id, "
                        "rating, comentario, estado, created_at) VALUES "
                        "(:client, :professional, 6, 'Invalid legacy rating', "
                        "'VISIBLE', NOW()) RETURNING id"
                    ),
                    {"client": client, "professional": professional},
                ).scalar_one()
            command.upgrade(self.config, "head")
            with engine.connect() as connection:
                row = connection.execute(
                    sa.text(
                        "SELECT rating, origin, legacy_metadata_json "
                        "FROM reviews WHERE id=:id"
                    ),
                    {"id": review},
                ).one()
                self.assertIsNone(row.rating)
                self.assertEqual(row.origin, "LEGACY")
                self.assertEqual(row.legacy_metadata_json["original_rating"], 6)
            command.downgrade(self.config, "20260726_05")
            with engine.connect() as connection:
                self.assertEqual(
                    connection.execute(
                        sa.text("SELECT rating FROM reviews WHERE id=:id"),
                        {"id": review},
                    ).scalar_one(),
                    6,
                )
            command.upgrade(self.config, "head")
        finally:
            engine.dispose()

    def test_postgresql_06_historical_then_07_converges_with_direct_head(self):
        with self.app.app_context():
            db.session.remove()
        command.downgrade(self.config, "20260726_05")
        engine = sa.create_engine(POSTGRES_URL)
        try:
            with engine.begin() as connection:
                replacement_user = connection.execute(
                    sa.text(
                        "INSERT INTO users (nombre, email, password, rol, estado) "
                        "VALUES ('Replacement owner', :email, 'hash', "
                        "'PROFESIONAL', 'ACTIVO') RETURNING id"
                    ),
                    {"email": f"replacement-owner-{uuid4().hex}@test.local"},
                ).scalar_one()
                connection.execute(
                    sa.text("UPDATE professionals SET user_id=:user WHERE id=:id"),
                    {"user": replacement_user, "id": self.professional_id},
                )
                legacy_review = connection.execute(
                    sa.text(
                        "INSERT INTO reviews (cliente_id, professional_id, "
                        "rating, comentario, estado, created_at) VALUES "
                        "(:client, :professional, 5, 'Ownership convergence', "
                        "'VISIBLE', NOW()) RETURNING id"
                    ),
                    {
                        "client": self.client_id,
                        "professional": self.professional_id,
                    },
                ).scalar_one()

            command.upgrade(self.config, "20260726_06")
            with engine.connect() as connection:
                historical = connection.execute(
                    sa.text(
                        "SELECT contract_id, legacy_metadata_json FROM reviews "
                        "WHERE id=:id"
                    ),
                    {"id": legacy_review},
                ).one()
                self.assertEqual(historical.contract_id, self.contract_id)
                self.assertEqual(
                    historical.legacy_metadata_json["classification_code"],
                    "LINKED_UNIQUE",
                )

            command.upgrade(self.config, "20260726_07")

            def snapshot():
                with engine.connect() as connection:
                    row = connection.execute(
                        sa.text(
                            "SELECT contract_id, verification_status, "
                            "rating_eligibility_status, legacy_metadata_json "
                            "FROM reviews WHERE id=:id"
                        ),
                        {"id": legacy_review},
                    ).one()
                    triggers = tuple(
                        connection.execute(
                            sa.text(
                                "SELECT tgname FROM pg_trigger "
                                "WHERE NOT tgisinternal AND tgname LIKE '%_v2' "
                                "ORDER BY tgname"
                            )
                        ).scalars()
                    )
                    checks = tuple(
                        connection.execute(
                            sa.text(
                                "SELECT conname FROM pg_constraint "
                                "WHERE conname IN "
                                "('ck_reviews_origin_required_v2', "
                                "'ck_reputation_events_discriminators_required_v2') "
                                "ORDER BY conname"
                            )
                        ).scalars()
                    )
                    revision = connection.execute(
                        sa.text("SELECT version_num FROM alembic_version")
                    ).scalar_one()
                    event_count = connection.execute(
                        sa.text("SELECT COUNT(*) FROM reputation_events")
                    ).scalar_one()
                    return tuple(row), triggers, checks, revision, event_count

            scenario_a = snapshot()
            self.assertIsNone(scenario_a[0][0])
            self.assertEqual(scenario_a[0][1:3], ("UNVERIFIED", "EXCLUDED"))
            self.assertEqual(
                scenario_a[0][3]["classification_code"],
                "IDENTITY_INCONSISTENT",
            )
            self.assertEqual(scenario_a[3], "20260726_07")
            self.assertEqual(scenario_a[4], 0)

            command.downgrade(self.config, "20260726_05")
            command.upgrade(self.config, "head")
            scenario_b = snapshot()
            self.assertEqual(scenario_b, scenario_a)
        finally:
            command.upgrade(self.config, "head")
            engine.dispose()


if __name__ == "__main__":
    unittest.main(verbosity=2)
