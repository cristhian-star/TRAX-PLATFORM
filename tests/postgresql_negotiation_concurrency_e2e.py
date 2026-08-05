"""Mandatory PostgreSQL concurrency gate for Sprint 7 Phase 2B MVP.

This module is intentionally outside normal ``test_*.py`` discovery. It
requires an exclusive disposable PostgreSQL database because it migrates and
truncates that database.
"""

import os
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

POSTGRES_URL = os.environ.get("TRAX_POSTGRES_TEST_URL")
ALLOW_RESET = os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET") == "1"
if POSTGRES_URL:
    os.environ["DATABASE_URL"] = POSTGRES_URL
os.environ.setdefault("SECRET_KEY", "postgres-negotiation-e2e")

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_negotiation import ContractNegotiation
from app.models.contract_negotiation_version import ContractNegotiationVersion
from app.models.contract_request import ContractRequest
from app.models.negotiation_acceptance import NegotiationAcceptance
from app.models.negotiation_event import NegotiationEvent
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.user import User
from app.services import negotiation_service
from app.services.negotiation_service import (
    NegotiationConflictError,
    accept_negotiation_terms,
    finalize_negotiation_contract,
    initiate_direct_negotiation,
    propose_negotiation_terms,
)


class Sprint7NegotiationPostgreSQLConcurrencyE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not POSTGRES_URL:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_URL es obligatorio para el gate PostgreSQL 2B"
            )
        url = make_url(POSTGRES_URL)
        if url.get_backend_name() not in ("postgresql", "postgres"):
            raise RuntimeError("TRAX_POSTGRES_TEST_URL debe apuntar a PostgreSQL")
        if not ALLOW_RESET:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_ALLOW_RESET=1 es obligatorio: la base sera truncada"
            )

        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.upgrade(config, "head")
        cls.app = create_app(initialize_schema=False)
        cls.app.config.update(TESTING=True)
        with cls.app.app_context():
            revision = db.session.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            if revision != "20260726_07":
                raise RuntimeError(f"Revision Alembic inesperada: {revision}")
            if db.engine.dialect.name != "postgresql":
                raise RuntimeError("El gate 2B no esta ejecutando PostgreSQL")

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
                nombre="PG Negotiation Client",
                email=f"pg-neg-client-{suffix}@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="PG Negotiation Professional",
                email=f"pg-neg-professional-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all([client, professional_user])
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="PG Negotiation Professional",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(professional)
            db.session.commit()
            self.client_id = client.id
            self.professional_user_id = professional_user.id
            self.professional_id = professional.id

    def tearDown(self):
        self._truncate_database()

    def _initiate(self):
        return initiate_direct_negotiation(
            cliente_id=self.client_id,
            professional_id=self.professional_id,
            servicio="Servicio negociado PG",
            description="Descripcion negociada",
            scope="Alcance negociado",
            external_price="150000.00",
            observations="Sin pagos dentro de TRAX",
            actor_user_id=self.client_id,
            idempotency_key="pg-negotiation-init-0001",
        )

    def _agree(self):
        negotiation = self._initiate()
        negotiation = accept_negotiation_terms(
            negotiation.id,
            actor_user_id=self.client_id,
            expected_version=negotiation.version,
            terms_version=negotiation.current_terms_version,
            idempotency_key="pg-negotiation-client-accept-0001",
        )
        negotiation = accept_negotiation_terms(
            negotiation.id,
            actor_user_id=self.professional_user_id,
            expected_version=negotiation.version,
            terms_version=negotiation.current_terms_version,
            idempotency_key="pg-negotiation-professional-accept-0001",
        )
        return negotiation

    def _counts(self):
        return {
            "negotiations": ContractNegotiation.query.count(),
            "versions": ContractNegotiationVersion.query.count(),
            "acceptances": NegotiationAcceptance.query.count(),
            "negotiation_events": NegotiationEvent.query.count(),
            "contracts": ContractRequest.query.count(),
            "contract_events": ContractEvent.query.count(),
            "commands": OperationCommand.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
        }

    def _run_two(self, calls, patch_target):
        barrier = threading.Barrier(2, timeout=10)
        backend_pids = [None, None]
        connection_ids = [None, None]
        results = [None, None]
        errors = [None, None]
        session_reusable = [False, False]
        original = getattr(*patch_target)

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
                    value = calls[index]()
                    results[index] = value.id
                except Exception as error:
                    errors[index] = error
                finally:
                    session_reusable[index] = User.query.count() == 2
                    db.session.remove()

        with patch.object(
            patch_target[0],
            patch_target[1],
            side_effect=coordinated,
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(worker, index)
                    for index in range(2)
                ]
                for future in futures:
                    future.result(timeout=30)

        self.assertEqual(len(set(backend_pids)), 2)
        self.assertEqual(len(set(connection_ids)), 2)
        self.assertEqual(session_reusable, [True, True])
        print(
            f"{self._testMethodName}: pg_backend_pid={sorted(backend_pids)} "
            f"connection_ids={connection_ids}",
            flush=True,
        )
        return results, errors

    def test_two_concurrent_acceptances_serialize_and_stale_one_can_retry(self):
        with self.app.app_context():
            negotiation = self._initiate()
            negotiation_id = negotiation.id
            expected_version = negotiation.version
            terms_version = negotiation.current_terms_version

        calls = [
            lambda: accept_negotiation_terms(
                negotiation_id,
                actor_user_id=self.client_id,
                expected_version=expected_version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-race-client-0001",
            ),
            lambda: accept_negotiation_terms(
                negotiation_id,
                actor_user_id=self.professional_user_id,
                expected_version=expected_version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-race-professional-0001",
            ),
        ]
        results, errors = self._run_two(
            calls,
            (negotiation_service, "_lock_negotiation"),
        )

        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(
            sum(isinstance(error, NegotiationConflictError) for error in errors),
            1,
        )
        losing_actor = (
            self.client_id if results[0] is None else self.professional_user_id
        )
        with self.app.app_context():
            negotiation = db.session.get(ContractNegotiation, negotiation_id)
            self.assertEqual(negotiation.version, 2)
            self.assertEqual(
                self._counts(),
                {
                    "negotiations": 1,
                    "versions": 1,
                    "acceptances": 1,
                    "negotiation_events": 2,
                    "contracts": 0,
                    "contract_events": 0,
                    "commands": 2,
                    "audits": 2,
                    "notifications": 2,
                },
            )
            negotiation = accept_negotiation_terms(
                negotiation_id,
                actor_user_id=losing_actor,
                expected_version=negotiation.version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-race-retry-0001",
            )
            self.assertEqual(negotiation.state, ContractNegotiation.STATE_AGREED)
            self.assertEqual(
                self._counts(),
                {
                    "negotiations": 1,
                    "versions": 1,
                    "acceptances": 2,
                    "negotiation_events": 4,
                    "contracts": 0,
                    "contract_events": 0,
                    "commands": 3,
                    "audits": 4,
                    "notifications": 3,
                },
            )

    def test_concurrent_finalize_same_key_replays_exactly_one_contract(self):
        with self.app.app_context():
            negotiation = self._agree()
            negotiation_id = negotiation.id
            expected_version = negotiation.version
            terms_version = negotiation.current_terms_version

        calls = [
            lambda: finalize_negotiation_contract(
                negotiation_id,
                actor_user_id=self.client_id,
                expected_version=expected_version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-finalize-same-0001",
            ),
            lambda: finalize_negotiation_contract(
                negotiation_id,
                actor_user_id=self.client_id,
                expected_version=expected_version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-finalize-same-0001",
            ),
        ]
        results, errors = self._run_two(
            calls,
            (negotiation_service, "_lock_negotiation"),
        )

        self.assertEqual(errors, [None, None])
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            negotiation = db.session.get(ContractNegotiation, negotiation_id)
            self.assertEqual(
                (negotiation.state, negotiation.contract_id),
                (ContractNegotiation.STATE_CONTRACTED, results[0]),
            )
            self.assertEqual(
                self._counts(),
                {
                    "negotiations": 1,
                    "versions": 1,
                    "acceptances": 2,
                    "negotiation_events": 5,
                    "contracts": 1,
                    "contract_events": 1,
                    "commands": 4,
                    "audits": 6,
                    "notifications": 4,
                },
            )

    def test_concurrent_finalize_different_keys_commits_only_one_command(self):
        with self.app.app_context():
            negotiation = self._agree()
            negotiation_id = negotiation.id
            expected_version = negotiation.version
            terms_version = negotiation.current_terms_version

        calls = [
            lambda: finalize_negotiation_contract(
                negotiation_id,
                actor_user_id=self.client_id,
                expected_version=expected_version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-finalize-key-a-0001",
            ),
            lambda: finalize_negotiation_contract(
                negotiation_id,
                actor_user_id=self.client_id,
                expected_version=expected_version,
                terms_version=terms_version,
                idempotency_key="pg-negotiation-finalize-key-b-0001",
            ),
        ]
        results, errors = self._run_two(
            calls,
            (negotiation_service, "_lock_negotiation"),
        )

        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(
            sum(isinstance(error, NegotiationConflictError) for error in errors),
            1,
        )
        with self.app.app_context():
            self.assertEqual(
                self._counts(),
                {
                    "negotiations": 1,
                    "versions": 1,
                    "acceptances": 2,
                    "negotiation_events": 5,
                    "contracts": 1,
                    "contract_events": 1,
                    "commands": 4,
                    "audits": 6,
                    "notifications": 4,
                },
            )

    def test_real_postgresql_constraint_rolls_back_finalize_and_session_recovers(self):
        with self.app.app_context():
            negotiation = self._agree()
            negotiation_id = negotiation.id
            expected_version = negotiation.version
            terms_version = negotiation.current_terms_version

            original = negotiation_service._create_contract_effects

            def add_invalid_notification(*args, **kwargs):
                contract = original(*args, **kwargs)
                notification = next(
                    item
                    for item in db.session.new
                    if isinstance(item, ActivityNotification)
                    and item.contract_event_id is not None
                )
                notification.delivery_status = "INVALID"
                return contract

            with patch.object(
                negotiation_service,
                "_create_contract_effects",
                side_effect=add_invalid_notification,
            ):
                with self.assertRaises(IntegrityError):
                    finalize_negotiation_contract(
                        negotiation_id,
                        actor_user_id=self.client_id,
                        expected_version=expected_version,
                        terms_version=terms_version,
                        idempotency_key="pg-negotiation-finalize-rollback-0001",
                    )

            negotiation = db.session.get(ContractNegotiation, negotiation_id)
            self.assertEqual(negotiation.state, ContractNegotiation.STATE_AGREED)
            self.assertIsNone(negotiation.contract_id)
            self.assertEqual(User.query.count(), 2)
            self.assertEqual(
                self._counts(),
                {
                    "negotiations": 1,
                    "versions": 1,
                    "acceptances": 2,
                    "negotiation_events": 4,
                    "contracts": 0,
                    "contract_events": 0,
                    "commands": 3,
                    "audits": 4,
                    "notifications": 3,
                },
            )

    def test_concurrent_proposals_leave_one_new_version_and_no_partial_command(self):
        with self.app.app_context():
            negotiation = self._initiate()
            negotiation_id = negotiation.id
            expected_version = negotiation.version

        calls = [
            lambda: propose_negotiation_terms(
                negotiation_id,
                description="Propuesta concurrente A",
                scope="Alcance concurrente A",
                external_price="151000",
                actor_user_id=self.client_id,
                expected_version=expected_version,
                idempotency_key="pg-negotiation-proposal-race-a-0001",
            ),
            lambda: propose_negotiation_terms(
                negotiation_id,
                description="Propuesta concurrente B",
                scope="Alcance concurrente B",
                external_price="152000",
                actor_user_id=self.professional_user_id,
                expected_version=expected_version,
                idempotency_key="pg-negotiation-proposal-race-b-0001",
            ),
        ]
        results, errors = self._run_two(
            calls,
            (negotiation_service, "_lock_negotiation"),
        )
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(
            sum(isinstance(error, NegotiationConflictError) for error in errors),
            1,
        )
        with self.app.app_context():
            negotiation = db.session.get(ContractNegotiation, negotiation_id)
            self.assertEqual(
                (negotiation.current_terms_version, negotiation.version),
                (2, 2),
            )
            self.assertEqual(
                self._counts(),
                {
                    "negotiations": 1,
                    "versions": 2,
                    "acceptances": 0,
                    "negotiation_events": 2,
                    "contracts": 0,
                    "contract_events": 0,
                    "commands": 2,
                    "audits": 2,
                    "notifications": 2,
                },
            )

    def test_postgresql_snapshot_trigger_and_service_hash_guard(self):
        with self.app.app_context():
            negotiation = self._initiate()
            terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=negotiation.id
            ).one()
            original_price = terms.external_price

            terms.external_price = 1
            with self.assertRaisesRegex(ValueError, "inmutable"):
                db.session.flush()
            db.session.rollback()
            terms = db.session.get(ContractNegotiationVersion, terms.id)
            self.assertEqual(terms.external_price, original_price)

            with self.assertRaises(IntegrityError):
                db.session.execute(
                    sa.text(
                        "UPDATE contract_negotiation_versions "
                        "SET description = 'SQL mutation' WHERE id = :id"
                    ),
                    {"id": terms.id},
                )
                db.session.commit()
            db.session.rollback()

            db.session.execute(
                sa.text(
                    "ALTER TABLE contract_negotiation_versions "
                    "DISABLE TRIGGER "
                    "trg_contract_negotiation_versions_immutable"
                )
            )
            try:
                db.session.execute(
                    sa.text(
                        "UPDATE contract_negotiation_versions "
                        "SET payload_hash = :payload_hash WHERE id = :id"
                    ),
                    {"payload_hash": "f" * 64, "id": terms.id},
                )
            finally:
                db.session.execute(
                    sa.text(
                        "ALTER TABLE contract_negotiation_versions "
                        "ENABLE TRIGGER "
                        "trg_contract_negotiation_versions_immutable"
                    )
                )
                db.session.commit()

            baseline = self._counts()
            with self.assertRaises(NegotiationConflictError):
                accept_negotiation_terms(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=1,
                    terms_version=1,
                    idempotency_key="pg-negotiation-corrupt-hash-0001",
                )
            self.assertEqual(self._counts(), baseline)

    def test_postgresql_rejects_incoherent_acceptances_from_orm_and_sql(self):
        with self.app.app_context():
            first = self._initiate()
            first_terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=first.id
            ).one()

            invalid_orm = NegotiationAcceptance(
                negotiation_id=first.id,
                negotiation_version_id=first_terms.id,
                actor_user_id=self.client_id,
                party=NegotiationAcceptance.PARTY_PROFESSIONAL,
            )
            db.session.add(invalid_orm)
            with self.assertRaises(ValueError):
                db.session.flush()
            db.session.rollback()

            invalid_sql_rows = (
                (self.client_id, "PROFESSIONAL"),
                (self.professional_user_id, "CLIENT"),
            )
            for actor_id, party in invalid_sql_rows:
                with self.subTest(party=party):
                    with self.assertRaises(IntegrityError):
                        db.session.execute(
                            sa.text(
                                "INSERT INTO negotiation_acceptances "
                                "(negotiation_id, negotiation_version_id, "
                                "actor_user_id, party) VALUES "
                                "(:negotiation_id, :version_id, "
                                ":actor_user_id, :party)"
                            ),
                            {
                                "negotiation_id": first.id,
                                "version_id": first_terms.id,
                                "actor_user_id": actor_id,
                                "party": party,
                            },
                        )
                        db.session.commit()
                    db.session.rollback()

            second = initiate_direct_negotiation(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                servicio="Segunda negociacion PG",
                description="Segunda descripcion",
                scope="Segundo alcance",
                external_price="160000",
                actor_user_id=self.client_id,
                idempotency_key="pg-negotiation-integrity-second-0001",
            )
            second_terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=second.id
            ).one()
            with self.assertRaises(IntegrityError):
                db.session.execute(
                    sa.text(
                        "INSERT INTO negotiation_acceptances "
                        "(negotiation_id, negotiation_version_id, "
                        "actor_user_id, party) VALUES "
                        "(:negotiation_id, :version_id, :actor_user_id, "
                        "'CLIENT')"
                    ),
                    {
                        "negotiation_id": first.id,
                        "version_id": second_terms.id,
                        "actor_user_id": self.client_id,
                    },
                )
                db.session.commit()
            db.session.rollback()

            first = propose_negotiation_terms(
                first.id,
                description="Version dos PG",
                scope="Alcance dos PG",
                external_price="170000",
                actor_user_id=self.client_id,
                expected_version=first.version,
                idempotency_key="pg-negotiation-integrity-v2-0001",
            )
            with self.assertRaises(IntegrityError):
                db.session.execute(
                    sa.text(
                        "INSERT INTO negotiation_acceptances "
                        "(negotiation_id, negotiation_version_id, "
                        "actor_user_id, party) VALUES "
                        "(:negotiation_id, :version_id, :actor_user_id, "
                        "'CLIENT')"
                    ),
                    {
                        "negotiation_id": first.id,
                        "version_id": first_terms.id,
                        "actor_user_id": self.client_id,
                    },
                )
                db.session.commit()
            db.session.rollback()
            self.assertEqual(NegotiationAcceptance.query.count(), 0)

    def test_downgrade_with_data_preserves_revision_triggers_and_constraints(self):
        with self.app.app_context():
            self._initiate()
            db.session.remove()

        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        with self.assertRaisesRegex(RuntimeError, "Downgrade bloqueado"):
            command.downgrade(config, "20260726_04")

        with self.app.app_context():
            revision = db.session.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            self.assertEqual(revision, "20260726_07")
            trigger_names = {
                row[0]
                for row in db.session.execute(
                    sa.text(
                        "SELECT tgname FROM pg_trigger "
                        "WHERE NOT tgisinternal AND tgrelid IN ("
                        "'contract_negotiation_versions'::regclass, "
                        "'negotiation_acceptances'::regclass)"
                    )
                )
            }
            self.assertIn(
                "trg_contract_negotiation_versions_immutable",
                trigger_names,
            )
            self.assertIn(
                "trg_negotiation_acceptances_coherent",
                trigger_names,
            )
            constraint_names = {
                row[0]
                for row in db.session.execute(
                    sa.text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'negotiation_acceptances'::regclass"
                    )
                )
            }
            self.assertIn(
                "fk_negotiation_acceptances_version_negotiation",
                constraint_names,
            )
            self.assertEqual(ContractNegotiation.query.count(), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
