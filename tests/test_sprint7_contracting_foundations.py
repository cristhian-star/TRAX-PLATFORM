import os
import unittest
from unittest.mock import patch


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.user import User
from app.services import contract_service
from app.services.contract_service import (
    ContractConflictError,
    IdempotencyConflictError,
    TRANSITIONS,
    accept_contract,
    cancel_contract,
    confirm_completion,
    create_contract,
    declare_work_completed,
    reject_contract,
    start_contract,
)


class Sprint7ContractingFoundationsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(
                nombre="Cliente",
                email="cliente-foundations@test.local",
                password="hash",
                rol="CLIENTE",
            )
            self.professional_user = User(
                nombre="Profesional",
                email="pro-foundations@test.local",
                password="hash",
                rol="PROFESIONAL",
            )
            self.other_professional = User(
                nombre="Profesional ajeno",
                email="other-pro-foundations@test.local",
                password="hash",
                rol="PROFESIONAL",
            )
            self.other_client = User(
                nombre="Cliente ajeno",
                email="other-client-foundations@test.local",
                password="hash",
                rol="CLIENTE",
            )
            db.session.add_all(
                [
                    self.client_user,
                    self.professional_user,
                    self.other_professional,
                    self.other_client,
                ]
            )
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Nexo Foundations",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.commit()
            self.client_id = self.client_user.id
            self.professional_user_id = self.professional_user.id
            self.other_professional_id = self.other_professional.id
            self.other_client_id = self.other_client.id
            self.professional_id = self.professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_contract(self, key="foundation-create-0001"):
        return create_contract(
            cliente_id=self.client_id,
            professional_id=self.professional_id,
            professional_user_id=self.professional_user_id,
            servicio="Instalacion",
            actor_user_id=self.client_id,
            idempotency_key=key,
        )

    def test_contracting_mode_state_catalog_and_transition_matrix(self):
        expected = {
            "CREADA": {"ACEPTADA", "RECHAZADA", "CANCELADA"},
            "ACEPTADA": {"EN_PROGRESO", "CANCELADA"},
            "EN_PROGRESO": {"COMPLETADA", "CANCELADA"},
            "COMPLETADA": {"CONFIRMADA", "CORRECCION_SOLICITADA", "CANCELADA"},
            "CORRECCION_SOLICITADA": {"EN_PROGRESO", "COMPLETADA", "CANCELADA"},
            "CONFIRMADA": set(),
            "RECHAZADA": set(),
            "CANCELADA": set(),
        }
        self.assertEqual(
            {state: set(targets) for state, targets in TRANSITIONS.items()},
            expected,
        )
        self.assertEqual(ContractRequest.TERMINAL_STATES, ("CONFIRMADA", "RECHAZADA", "CANCELADA"))
        self.assertNotIn("CERRADA", ContractRequest.ESTADOS)
        with self.app.app_context():
            contract = self._create_contract()
            self.assertEqual(contract.contracting_mode, "EXTERNAL")
            self.assertEqual(contract.version, 1)

    def test_full_success_path_correlates_command_event_audit_and_notification(self):
        with self.app.app_context():
            contract = self._create_contract("foundation-create-success")
            transitions = (
                (accept_contract, self.professional_user_id, "accept-success"),
                (start_contract, self.professional_user_id, "start-success"),
                (declare_work_completed, self.professional_user_id, "complete-success"),
                (confirm_completion, self.client_id, "confirm-success"),
            )
            for operation, actor_id, key in transitions:
                previous_version = contract.version
                contract = operation(
                    contract.id,
                    actor_id,
                    expected_version=previous_version,
                    idempotency_key=key,
                )

                command = OperationCommand.query.filter_by(
                    actor_user_id=actor_id,
                    idempotency_key=key,
                ).one()
                event = ContractEvent.query.filter_by(
                    contract_id=contract.id,
                    correlation_id=command.correlation_id,
                ).one()
                audit = AuditLog.query.filter_by(
                    event_id=event.id,
                    correlation_id=command.correlation_id,
                ).one()
                notification = ActivityNotification.query.filter_by(
                    contract_event_id=event.id,
                    correlation_id=command.correlation_id,
                ).one()

                self.assertEqual(command.status, "SUCCEEDED")
                self.assertEqual(command.result_entity_id, contract.id)
                self.assertEqual(audit.operation, command.operation)
                self.assertEqual(notification.channel, "INTERNAL")
                self.assertEqual(notification.delivery_status, "DELIVERED")
                self.assertEqual(contract.version, previous_version + 1)

            self.assertEqual(contract.estado, "CONFIRMADA")
            with self.assertRaises(ValueError):
                cancel_contract(
                    contract.id,
                    self.client_id,
                    expected_version=contract.version,
                    idempotency_key="terminal-cancel",
                )

            sequences = [
                event.sequence_no
                for event in ContractEvent.query.filter_by(contract_id=contract.id)
                .order_by(ContractEvent.sequence_no)
                .all()
            ]
            self.assertEqual(sequences, list(range(1, len(sequences) + 1)))

    def test_reject_is_terminal_and_does_not_allow_acceptance(self):
        with self.app.app_context():
            contract = self._create_contract()
            contract = reject_contract(
                contract.id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="reject-terminal",
            )
            self.assertEqual(contract.estado, "RECHAZADA")
            with self.assertRaises(ValueError):
                accept_contract(
                    contract.id,
                    self.professional_user_id,
                    expected_version=2,
                    idempotency_key="accept-after-reject",
                )

    def test_ownership_role_and_missing_actor_are_enforced_inside_service(self):
        with self.app.app_context():
            contract = self._create_contract()
            with self.assertRaises(PermissionError):
                accept_contract(contract.id, self.other_professional_id)
            with self.assertRaises(PermissionError):
                accept_contract(contract.id, self.client_id)
            with self.assertRaises(PermissionError):
                accept_contract(contract.id, None)

            accept_contract(
                contract.id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="owner-accept",
            )
            start_contract(
                contract.id,
                self.professional_user_id,
                expected_version=2,
                idempotency_key="owner-start",
            )
            declare_work_completed(
                contract.id,
                self.professional_user_id,
                expected_version=3,
                idempotency_key="owner-complete",
            )
            with self.assertRaises(PermissionError):
                confirm_completion(contract.id, self.other_client_id)
            with self.assertRaises(PermissionError):
                confirm_completion(contract.id, self.professional_user_id)

    def test_idempotent_replay_returns_result_without_duplicate_effects(self):
        with self.app.app_context():
            contract = self._create_contract()
            first = accept_contract(
                contract.id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="accept-idempotent",
            )
            second = accept_contract(
                contract.id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="accept-idempotent",
            )
            self.assertEqual(first.id, second.id)
            self.assertEqual(second.estado, "ACEPTADA")
            self.assertEqual(
                OperationCommand.query.filter_by(idempotency_key="accept-idempotent").count(),
                1,
            )
            self.assertEqual(
                ContractEvent.query.filter_by(
                    contract_id=contract.id,
                    event_type=ContractEvent.CONTRACT_ACCEPTED,
                ).count(),
                1,
            )
            self.assertEqual(
                ActivityNotification.query.filter_by(
                    tipo=ContractEvent.CONTRACT_ACCEPTED,
                    entity_id=contract.id,
                ).count(),
                1,
            )

    def test_same_idempotency_key_with_different_payload_conflicts(self):
        with self.app.app_context():
            contract = self._create_contract()
            accept_contract(
                contract.id,
                self.professional_user_id,
                expected_version=1,
                idempotency_key="payload-conflict",
            )
            with self.assertRaises(IdempotencyConflictError):
                accept_contract(
                    contract.id,
                    self.professional_user_id,
                    expected_version=2,
                    idempotency_key="payload-conflict",
                )

    def test_processing_command_and_stale_version_return_conflict(self):
        with self.app.app_context():
            contract = self._create_contract()
            payload_hash = contract_service._normalized_payload_hash(
                {
                    "contract_id": contract.id,
                    "expected_version": 1,
                    "operation": contract_service.OPERATION_ACCEPT,
                }
            )
            db.session.add(
                OperationCommand(
                    actor_user_id=self.professional_user_id,
                    operation=contract_service.OPERATION_ACCEPT,
                    idempotency_key="processing-command",
                    payload_hash=payload_hash,
                    status=OperationCommand.STATUS_PROCESSING,
                    correlation_id="00000000-0000-0000-0000-000000000001",
                )
            )
            db.session.commit()
            with self.assertRaises(ContractConflictError):
                accept_contract(
                    contract.id,
                    self.professional_user_id,
                    expected_version=1,
                    idempotency_key="processing-command",
                )

            with self.assertRaises(ContractConflictError):
                accept_contract(
                    contract.id,
                    self.professional_user_id,
                    expected_version=99,
                    idempotency_key="stale-version",
                )
            self.assertEqual(db.session.get(ContractRequest, contract.id).estado, "CREADA")

    def test_each_internal_failure_rolls_back_and_session_remains_reusable(self):
        failure_points = (
            "_create_transition_event",
            "_add_audit",
            "_add_contract_notification",
            "_complete_command",
        )
        for index, failure_point in enumerate(failure_points):
            with self.subTest(failure_point=failure_point), self.app.app_context():
                db.drop_all()
                db.create_all()
                client = User(
                    nombre=f"Cliente {index}",
                    email=f"rollback-client-{index}@test.local",
                    password="hash",
                    rol="CLIENTE",
                )
                professional_user = User(
                    nombre=f"Pro {index}",
                    email=f"rollback-pro-{index}@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                )
                db.session.add_all([client, professional_user])
                db.session.flush()
                professional = Professional(
                    user_id=professional_user.id,
                    nombre=f"Rollback {index}",
                    servicio="Electricidad",
                    zona="CABA",
                    perfil_completo=True,
                )
                db.session.add(professional)
                db.session.commit()
                contract = create_contract(
                    cliente_id=client.id,
                    professional_id=professional.id,
                    professional_user_id=professional_user.id,
                    servicio="Rollback",
                    actor_user_id=client.id,
                    idempotency_key=f"foundation-rollback-create-{index}",
                )
                contract_id = contract.id

                with patch.object(
                    contract_service,
                    failure_point,
                    side_effect=RuntimeError("fallo inyectado"),
                ):
                    with self.assertRaises(RuntimeError):
                        accept_contract(
                            contract_id,
                            professional_user.id,
                            expected_version=1,
                            idempotency_key=f"rollback-{index}",
                        )

                stored = db.session.get(ContractRequest, contract_id)
                self.assertEqual(stored.estado, "CREADA")
                self.assertEqual(stored.version, 1)
                self.assertEqual(
                    OperationCommand.query.filter_by(
                        idempotency_key=f"rollback-{index}"
                    ).count(),
                    0,
                )
                self.assertEqual(
                    ContractEvent.query.filter_by(
                        contract_id=contract_id,
                        event_type=ContractEvent.CONTRACT_ACCEPTED,
                    ).count(),
                    0,
                )

                recovered = accept_contract(
                    contract_id,
                    professional_user.id,
                    expected_version=1,
                    idempotency_key=f"rollback-retry-{index}",
                )
                self.assertEqual(recovered.estado, "ACEPTADA")

    def test_failure_immediately_after_command_creation_rolls_back_command(self):
        with self.app.app_context():
            contract = self._create_contract()
            original_begin = contract_service._begin_command

            def fail_after_begin(*args, **kwargs):
                original_begin(*args, **kwargs)
                raise RuntimeError("fallo despues de crear OperationCommand")

            with patch.object(
                contract_service,
                "_begin_command",
                side_effect=fail_after_begin,
            ):
                with self.assertRaises(RuntimeError):
                    accept_contract(
                        contract.id,
                        self.professional_user_id,
                        expected_version=1,
                        idempotency_key="rollback-after-command",
                    )

            self.assertEqual(
                OperationCommand.query.filter_by(
                    idempotency_key="rollback-after-command"
                ).count(),
                0,
            )
            self.assertEqual(
                db.session.get(ContractRequest, contract.id).estado,
                "CREADA",
            )


if __name__ == "__main__":
    unittest.main()
