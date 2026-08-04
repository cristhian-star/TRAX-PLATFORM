"""Mandatory PostgreSQL E2E suite for Sprint 7 Phase 2A.

This module is intentionally outside unittest's ``test_*.py`` discovery.
CI must execute it explicitly with a disposable PostgreSQL database because
the suite migrates and truncates that database.
"""

import os
import sys
import threading
import time
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
os.environ.setdefault("SECRET_KEY", "postgres-contracting-e2e")

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.budget_offer import BudgetOffer
from app.models.budget_request import BudgetRequest
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.proposal_application import ProposalApplication
from app.models.proposal_request import ProposalRequest
from app.models.user import User
from app.services import contract_service, contracting_core_service
from app.services.contract_service import (
    ContractConflictError,
    IdempotencyConflictError,
    accept_contract,
    create_contract,
)
from app.services.contracting_core_service import (
    create_contract_from_budget_offer,
    create_contract_from_proposal_application,
)

class Sprint7ContractingPostgreSQLConcurrencyE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not POSTGRES_URL:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_URL es obligatorio para la suite PostgreSQL E2E"
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
            self_revision = db.session.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            if self_revision != "20260726_05":
                raise RuntimeError(f"Revision Alembic inesperada: {self_revision}")
            if db.engine.dialect.name != "postgresql":
                raise RuntimeError("La suite E2E no esta ejecutando PostgreSQL")

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
            owner = User(
                nombre="PG Owner",
                email=f"pg-owner-{suffix}@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="PG Professional",
                email=f"pg-professional-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all([owner, professional_user])
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="PG Professional",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(professional)
            db.session.flush()
            budget = BudgetRequest(
                cliente_id=owner.id,
                categoria="Electricidad",
                titulo="PG Budget",
                descripcion="PG budget source",
                zona="CABA",
                estado="ADJUDICADA",
            )
            proposal = ProposalRequest(
                cliente_id=owner.id,
                owner_user_id=owner.id,
                categoria="Construccion",
                titulo="PG Proposal",
                descripcion="PG proposal source",
                estado="CERRADA",
                hiring_mode="SINGLE",
            )
            db.session.add_all([budget, proposal])
            db.session.flush()
            offer = BudgetOffer(
                budget_request_id=budget.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                monto=100,
                mensaje="Oferta PG",
                plazo_estimado="1 dia",
                estado="ADJUDICADO",
            )
            application = ProposalApplication(
                proposal_id=proposal.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                mensaje="Postulacion PG",
                pretension_economica=200,
                estado="ACEPTADA",
            )
            db.session.add_all([offer, application])
            db.session.commit()
            self.owner_id = owner.id
            self.professional_user_id = professional_user.id
            self.professional_id = professional.id
            self.offer_id = offer.id
            self.application_id = application.id

    def tearDown(self):
        self._truncate_database()

    def _direct_kwargs(self, key, **overrides):
        values = {
            "cliente_id": self.owner_id,
            "professional_id": self.professional_id,
            "professional_user_id": self.professional_user_id,
            "servicio": "Servicio PG",
            "actor_user_id": self.owner_id,
            "idempotency_key": key,
        }
        values.update(overrides)
        return values

    def _run_two(self, calls, patch_target=None):
        barrier = threading.Barrier(2, timeout=10)
        backend_pids = []
        results = [None, None]
        errors = [None, None]

        def worker(index):
            with self.app.app_context():
                backend_pids.append(
                    db.session.execute(sa.text("SELECT pg_backend_pid()")).scalar_one()
                )
                try:
                    result = calls[index]()
                    if isinstance(result, ContractRequest):
                        result = result.id
                    elif hasattr(result, "contract"):
                        result = result.contract.id
                    results[index] = result
                except Exception as error:
                    errors[index] = error
                finally:
                    # Proves the scoped session remains usable after success/conflict.
                    User.query.count()
                    db.session.remove()

        if patch_target:
            module, attribute = patch_target
            original = getattr(module, attribute)

            def coordinated(*args, **kwargs):
                barrier.wait()
                return original(*args, **kwargs)

            patcher = patch.object(module, attribute, side_effect=coordinated)
        else:
            patcher = None

        if patcher:
            patcher.start()
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(worker, index)
                    for index in range(2)
                ]
                for future in futures:
                    future.result(timeout=30)
        finally:
            if patcher:
                patcher.stop()

        self.assertEqual(len(set(backend_pids)), 2)
        print(
            f"{self._testMethodName}: pg_backend_pid={sorted(backend_pids)}",
            flush=True,
        )
        return results, errors

    def _counts(self):
        return {
            "contracts": ContractRequest.query.count(),
            "commands": OperationCommand.query.count(),
            "events": ContractEvent.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
        }

    def test_double_direct_create_same_key_and_payload_recovers_unique_race(self):
        key = "pg-direct-same-key-0001"
        calls = [
            lambda: create_contract(**self._direct_kwargs(key)),
            lambda: create_contract(**self._direct_kwargs(key)),
        ]
        results, errors = self._run_two(
            calls,
            (contract_service, "_begin_command"),
        )

        self.assertEqual(errors, [None, None])
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            self.assertEqual(
                self._counts(),
                {
                    "contracts": 1,
                    "commands": 1,
                    "events": 1,
                    "audits": 1,
                    "notifications": 1,
                },
            )

    def test_same_key_different_payload_has_one_winner_and_no_partial_effects(self):
        key = "pg-direct-payload-conflict-0001"
        calls = [
            lambda: create_contract(**self._direct_kwargs(key, servicio="Payload A")),
            lambda: create_contract(**self._direct_kwargs(key, servicio="Payload B")),
        ]
        results, errors = self._run_two(
            calls,
            (contract_service, "_begin_command"),
        )

        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(sum(isinstance(error, IdempotencyConflictError) for error in errors), 1)
        with self.app.app_context():
            self.assertEqual(self._counts(), {
                "contracts": 1,
                "commands": 1,
                "events": 1,
                "audits": 1,
                "notifications": 1,
            })

    def test_double_transition_same_version_serializes_with_for_update(self):
        with self.app.app_context():
            contract_id = create_contract(
                **self._direct_kwargs("pg-transition-base-0001")
            ).id

        calls = [
            lambda: accept_contract(
                contract_id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="pg-accept-version-a-0001",
            ),
            lambda: accept_contract(
                contract_id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="pg-accept-version-b-0001",
            ),
        ]
        results, errors = self._run_two(calls, (contract_service, "_lock_contract"))

        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(sum(isinstance(error, ContractConflictError) for error in errors), 1)
        with self.app.app_context():
            contract = db.session.get(ContractRequest, contract_id)
            self.assertEqual((contract.estado, contract.version), ("ACEPTADA", 2))
            self.assertEqual(self._counts(), {
                "contracts": 1,
                "commands": 2,
                "events": 2,
                "audits": 2,
                "notifications": 2,
            })
            self.assertEqual(
                sorted(event.sequence_no for event in contract.events),
                [1, 2],
            )

    def test_two_keys_same_transition_create_only_one_committed_command(self):
        with self.app.app_context():
            contract_id = create_contract(
                **self._direct_kwargs("pg-two-keys-base-0001")
            ).id
        calls = [
            lambda: accept_contract(
                contract_id,
                self.professional_user_id,
                idempotency_key="pg-two-keys-accept-a-0001",
            ),
            lambda: accept_contract(
                contract_id,
                self.professional_user_id,
                idempotency_key="pg-two-keys-accept-b-0001",
            ),
        ]
        results, errors = self._run_two(calls, (contract_service, "_lock_contract"))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(sum(isinstance(error, ValueError) for error in errors), 1)
        with self.app.app_context():
            self.assertEqual(self._counts(), {
                "contracts": 1,
                "commands": 2,
                "events": 2,
                "audits": 2,
                "notifications": 2,
            })

    def test_double_budget_contract_creation_uses_two_sessions(self):
        def create_and_commit():
            result = create_contract_from_budget_offer(
                self.offer_id,
                actor_user_id=self.owner_id,
            )
            db.session.commit()
            return result

        results, errors = self._run_two(
            [create_and_commit, create_and_commit],
            (contracting_core_service, "require_active_actor"),
        )
        self.assertEqual(errors, [None, None])
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            self.assertEqual(self._counts(), {
                "contracts": 1,
                "commands": 0,
                "events": 2,
                "audits": 1,
                "notifications": 2,
            })

    def test_double_proposal_contract_creation_uses_two_sessions(self):
        def create_and_commit():
            result = create_contract_from_proposal_application(
                self.application_id,
                actor_user_id=self.owner_id,
            )
            db.session.commit()
            return result

        results, errors = self._run_two(
            [create_and_commit, create_and_commit],
            (contracting_core_service, "require_active_actor"),
        )
        self.assertEqual(errors, [None, None])
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            self.assertEqual(self._counts(), {
                "contracts": 1,
                "commands": 0,
                "events": 2,
                "audits": 1,
                "notifications": 2,
            })

    def test_second_retry_waits_while_first_command_is_processing(self):
        key = "pg-processing-race-0001"
        entered_completion = threading.Event()
        release_completion = threading.Event()
        second_finished = threading.Event()
        original_complete = contract_service._complete_command
        results = []
        errors = []
        backend_pids = []

        def hold_completion(*args, **kwargs):
            entered_completion.set()
            if not release_completion.wait(timeout=10):
                raise TimeoutError("No se libero el primer comando")
            return original_complete(*args, **kwargs)

        def worker(mark_second=False):
            with self.app.app_context():
                backend_pids.append(
                    db.session.execute(sa.text("SELECT pg_backend_pid()")).scalar_one()
                )
                try:
                    results.append(
                        create_contract(**self._direct_kwargs(key)).id
                    )
                except Exception as error:
                    errors.append(error)
                finally:
                    if mark_second:
                        second_finished.set()
                    User.query.count()
                    db.session.remove()

        with patch.object(
            contract_service,
            "_complete_command",
            side_effect=hold_completion,
        ):
            first = threading.Thread(target=worker)
            first.start()
            self.assertTrue(entered_completion.wait(timeout=10))
            second = threading.Thread(target=worker, kwargs={"mark_second": True})
            second.start()
            time.sleep(0.3)
            self.assertFalse(second_finished.is_set())
            release_completion.set()
            first.join(timeout=15)
            second.join(timeout=15)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(len(set(backend_pids)), 2)
        print(
            f"{self._testMethodName}: pg_backend_pid={sorted(backend_pids)}",
            flush=True,
        )
        self.assertEqual(errors, [])
        self.assertEqual(results[0], results[1])
        with self.app.app_context():
            self.assertEqual(self._counts(), {
                "contracts": 1,
                "commands": 1,
                "events": 1,
                "audits": 1,
                "notifications": 1,
            })

    def test_real_notification_constraint_failure_rolls_back_every_effect(self):
        original_add = contract_service._add_contract_notification

        def add_invalid_notification(*args, **kwargs):
            original_add(*args, **kwargs)
            notification = next(
                item
                for item in db.session.new
                if isinstance(item, ActivityNotification)
            )
            notification.delivery_status = "INVALID"

        with self.app.app_context(), patch.object(
            contract_service,
            "_add_contract_notification",
            side_effect=add_invalid_notification,
        ):
            with self.assertRaises(IntegrityError):
                create_contract(
                    **self._direct_kwargs("pg-real-constraint-rollback-0001")
                )
            self.assertEqual(User.query.count(), 2)
            self.assertEqual(self._counts(), {
                "contracts": 0,
                "commands": 0,
                "events": 0,
                "audits": 0,
                "notifications": 0,
            })


if __name__ == "__main__":
    unittest.main(verbosity=2)
