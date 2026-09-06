import inspect
import unittest
from unittest.mock import patch

from app import create_app, db
from app.config.config import TestingConfig
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.reputation_event import ReputationEvent
from app.models.review import Review
from app.models.user import User
from app.services import contract_review_service, reputation_service
from app.services.contract_review_service import (
    ContractReviewConflictError,
    ContractReviewIdempotencyConflictError,
    ContractReviewIntegrityError,
    OPERATION_CREATE_CONTRACT_REVIEW,
    create_contract_review,
)


class ContractReviewServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=True)
        with self.app.app_context():
            users = (
                User(
                    nombre="Cliente owner",
                    email="review-owner@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Otro cliente",
                    email="review-other@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Cliente suspendido",
                    email="review-suspended-client@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="SUSPENDIDO",
                ),
                User(
                    nombre="Profesional activo",
                    email="review-professional@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Profesional alternativo",
                    email="review-professional-other@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Profesional suspendido",
                    email="review-professional-suspended@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                    estado="SUSPENDIDO",
                ),
            )
            db.session.add_all(users)
            db.session.flush()
            profiles = (
                Professional(
                    user_id=users[3].id,
                    nombre="Perfil principal",
                    servicio="Electricidad",
                    zona="CABA",
                ),
                Professional(
                    user_id=users[5].id,
                    nombre="Perfil suspendido",
                    servicio="Plomeria",
                    zona="CABA",
                ),
                Professional(
                    user_id=None,
                    nombre="Perfil huerfano",
                    servicio="Pintura",
                    zona="CABA",
                ),
            )
            db.session.add_all(profiles)
            db.session.commit()
            self.owner_id = users[0].id
            self.other_client_id = users[1].id
            self.suspended_client_id = users[2].id
            self.professional_user_id = users[3].id
            self.other_professional_user_id = users[4].id
            self.suspended_professional_user_id = users[5].id
            self.professional_id = profiles[0].id
            self.suspended_professional_id = profiles[1].id
            self.orphan_professional_id = profiles[2].id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _contract(
        self,
        *,
        estado="CONFIRMADA",
        cliente_id=None,
        professional_id=None,
        professional_user_id=None,
        servicio="Servicio confirmado",
    ):
        contract = ContractRequest(
            cliente_id=cliente_id or self.owner_id,
            professional_id=professional_id or self.professional_id,
            professional_user_id=(
                self.professional_user_id
                if professional_user_id is None
                else professional_user_id
            ),
            servicio=servicio,
            estado=estado,
        )
        db.session.add(contract)
        db.session.commit()
        return contract

    def _create(self, contract, key="contract-review-service-key-0001", **overrides):
        values = {
            "actor_user_id": self.owner_id,
            "contract_id": contract.id,
            "rating": 5,
            "comment": "Trabajo completado correctamente",
            "idempotency_key": key,
        }
        values.update(overrides)
        return create_contract_review(**values)

    def _counts(self):
        return {
            "reviews": Review.query.count(),
            "reputation_events": ReputationEvent.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
            "commands": OperationCommand.query.count(),
            "contract_events": ContractEvent.query.count(),
        }

    def test_actor_must_exist_be_active_client_and_owner(self):
        with self.app.app_context():
            contract = self._contract()
            cases = (
                (None, PermissionError),
                (999999, PermissionError),
                (self.suspended_client_id, PermissionError),
                (self.professional_user_id, PermissionError),
                (self.other_client_id, PermissionError),
            )
            for actor_id, error_type in cases:
                with self.subTest(actor_id=actor_id):
                    with self.assertRaises(error_type):
                        self._create(
                            contract,
                            key=f"contract-review-actor-{str(actor_id):0>6}",
                            actor_user_id=actor_id,
                        )
                    self.assertEqual(self._counts()["commands"], 0)

    def test_only_confirmed_contract_is_eligible_and_closed_is_rejected(self):
        with self.app.app_context():
            for index, estado in enumerate(
                ("CREADA", "ACEPTADA", "EN_PROGRESO", "COMPLETADA"),
                start=1,
            ):
                contract = self._contract(estado=estado, servicio=f"Estado {estado}")
                with self.subTest(estado=estado):
                    with self.assertRaises(ValueError):
                        self._create(
                            contract,
                            key=f"contract-review-state-{index:04d}",
                        )

            legacy_closed = self._contract(servicio="Estado legacy")
            legacy_closed.estado = "CERRADA"
            with db.session.no_autoflush:
                with self.assertRaises(ValueError):
                    self._create(
                        legacy_closed,
                        key="contract-review-state-closed",
                    )

            confirmed = self._contract(servicio="Estado confirmado")
            review = self._create(
                confirmed,
                key="contract-review-state-confirmed",
            )
            self.assertEqual(review.contract_id, confirmed.id)

    def test_professional_identity_must_be_complete_and_coherent(self):
        with self.app.app_context():
            missing_profile_contract = self._contract(servicio="Perfil inexistente")
            with patch.object(
                contract_review_service,
                "_load_professional",
                return_value=None,
            ):
                with self.assertRaises(ContractReviewIntegrityError):
                    self._create(
                        missing_profile_contract,
                        key="contract-review-missing-profile",
                    )

            orphan_contract = self._contract(
                professional_id=self.orphan_professional_id,
                professional_user_id=self.professional_user_id,
                servicio="Perfil sin usuario",
            )
            with self.assertRaises(ContractReviewIntegrityError):
                self._create(
                    orphan_contract,
                    key="contract-review-orphan-profile",
                )

            incoherent_contract = self._contract(
                professional_user_id=self.other_professional_user_id,
                servicio="Identidad incoherente",
            )
            with self.assertRaises(ContractReviewIntegrityError):
                self._create(
                    incoherent_contract,
                    key="contract-review-incoherent-professional",
                )

    def test_suspended_professional_can_receive_historical_review(self):
        with self.app.app_context():
            contract = self._contract(
                professional_id=self.suspended_professional_id,
                professional_user_id=self.suspended_professional_user_id,
                servicio="Contrato historico",
            )
            review = self._create(
                contract,
                key="contract-review-suspended-professional",
            )
            event = ReputationEvent.query.filter_by(review_id=review.id).one()
            self.assertEqual(event.user_id, self.suspended_professional_user_id)

    def test_rating_and_idempotency_key_are_required_and_valid(self):
        with self.app.app_context():
            contract = self._contract()
            for rating in (0, 6, True, "5"):
                with self.subTest(rating=rating):
                    with self.assertRaises(ValueError):
                        self._create(
                            contract,
                            key="contract-review-invalid-rating",
                            rating=rating,
                        )
            for key in (None, "", "short"):
                with self.subTest(key=key):
                    with self.assertRaises(ValueError):
                        self._create(contract, key=key)
            self.assertEqual(self._counts()["commands"], 0)

    def test_comment_normalization_is_deterministic_and_empty_becomes_null(self):
        with self.app.app_context():
            first_contract = self._contract(servicio="Comentario normalizado")
            first = self._create(
                first_contract,
                key="contract-review-normalized-comment",
                comment="  Ｈola\r\nmundo  ",
            )
            self.assertEqual(first.comentario, "Hola\nmundo")
            self.assertEqual(first.comment_public, "Hola\nmundo")

            second_contract = self._contract(servicio="Comentario vacio")
            second = self._create(
                second_contract,
                key="contract-review-empty-comment",
                comment=" \r\n  ",
            )
            self.assertIsNone(second.comentario)
            self.assertIsNone(second.comment_public)

    def test_success_creates_exact_atomic_neutral_effects_without_contract_event(self):
        with self.app.app_context():
            contract = self._contract()
            review = self._create(
                contract,
                key="contract-review-exact-effects",
                correlation_id="7e49935e-99cc-4428-bf92-590d0996f1c0",
            )
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
            command = OperationCommand.query.one()
            event = ReputationEvent.query.one()
            audit = AuditLog.query.one()
            notification = ActivityNotification.query.one()
            self.assertEqual(command.operation, OPERATION_CREATE_CONTRACT_REVIEW)
            self.assertEqual(command.result_entity_type, "Review")
            self.assertEqual(command.result_entity_id, review.id)
            self.assertEqual(command.status, OperationCommand.STATUS_SUCCEEDED)
            self.assertEqual(review.correlation_id, command.correlation_id)
            self.assertEqual(event.event_value, 5)
            self.assertIsNone(event.puntos)
            self.assertEqual(event.source_type, "CONTRACT_REVIEW")
            self.assertEqual(event.event_type, "REVIEW_RECORDED")
            self.assertEqual(event.origin, "CONTRACTUAL")
            self.assertEqual(audit.entity_type, "Review")
            self.assertEqual(audit.entity_id, review.id)
            self.assertEqual(notification.entity_type, "Review")
            self.assertEqual(notification.entity_id, review.id)
            self.assertEqual(
                {
                    review.correlation_id,
                    event.correlation_id,
                    audit.correlation_id,
                    notification.correlation_id,
                    command.correlation_id,
                },
                {"7e49935e-99cc-4428-bf92-590d0996f1c0"},
            )

    def test_exact_replay_returns_same_review_without_duplicate_effects(self):
        with self.app.app_context():
            contract = self._contract()
            first = self._create(contract, key="contract-review-exact-replay")
            correlation_id = first.correlation_id
            replay = self._create(
                contract,
                key="contract-review-exact-replay",
                correlation_id="d565d4de-f3ca-4385-a65f-e8321fa5b812",
            )
            self.assertEqual(replay.id, first.id)
            self.assertEqual(replay.correlation_id, correlation_id)
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

    def test_same_key_with_different_payload_conflicts_without_effects(self):
        with self.app.app_context():
            contract = self._contract()
            self._create(contract, key="contract-review-payload-conflict")
            counts = self._counts()
            with self.assertRaises(ContractReviewIdempotencyConflictError):
                self._create(
                    contract,
                    key="contract-review-payload-conflict",
                    rating=4,
                )
            self.assertEqual(self._counts(), counts)

    def test_different_key_on_reviewed_contract_is_domain_conflict(self):
        with self.app.app_context():
            contract = self._contract()
            self._create(contract, key="contract-review-first-intention")
            counts = self._counts()
            with self.assertRaises(ContractReviewConflictError):
                self._create(contract, key="contract-review-second-intention")
            self.assertEqual(self._counts(), counts)

    def test_two_contracts_allow_two_reviews(self):
        with self.app.app_context():
            first_contract = self._contract(servicio="Primer contrato")
            second_contract = self._contract(servicio="Segundo contrato")
            first = self._create(
                first_contract,
                key="contract-review-two-contracts-1",
            )
            second = self._create(
                second_contract,
                key="contract-review-two-contracts-2",
            )
            self.assertNotEqual(first.id, second.id)
            self.assertEqual(Review.query.count(), 2)

    def test_processing_command_returns_recoverable_conflict(self):
        with self.app.app_context():
            contract = self._contract()
            comment = contract_review_service._normalize_comment("En proceso")
            payload_hash = contract_review_service._payload_hash(
                contract_review_service._canonical_payload(
                    contract.id,
                    5,
                    comment,
                )
            )
            db.session.add(
                OperationCommand(
                    actor_user_id=self.owner_id,
                    operation=OPERATION_CREATE_CONTRACT_REVIEW,
                    idempotency_key="contract-review-processing-command",
                    payload_hash=payload_hash,
                    status=OperationCommand.STATUS_PROCESSING,
                    correlation_id="f0980faf-26eb-4919-b29c-77538ba158f7",
                )
            )
            db.session.commit()
            with self.assertRaises(ContractReviewConflictError):
                self._create(
                    contract,
                    key="contract-review-processing-command",
                    comment="En proceso",
                )
            self.assertEqual(Review.query.count(), 0)

    def test_lost_or_incoherent_command_result_is_integrity_error(self):
        with self.app.app_context():
            contract = self._contract(servicio="Resultado perdido")
            payload_hash = contract_review_service._payload_hash(
                contract_review_service._canonical_payload(
                    contract.id,
                    5,
                    contract_review_service._normalize_comment("Perdido"),
                )
            )
            db.session.add(
                OperationCommand(
                    actor_user_id=self.owner_id,
                    operation=OPERATION_CREATE_CONTRACT_REVIEW,
                    idempotency_key="contract-review-lost-result",
                    payload_hash=payload_hash,
                    status=OperationCommand.STATUS_SUCCEEDED,
                    result_entity_type="Review",
                    result_entity_id=999999,
                    correlation_id="0304e60e-1030-4f91-807c-d83bd0b79744",
                )
            )
            db.session.commit()
            with self.assertRaises(ContractReviewIntegrityError):
                self._create(
                    contract,
                    key="contract-review-lost-result",
                    comment="Perdido",
                )
            self.assertEqual(Review.query.count(), 0)

    def test_existing_result_for_another_contract_is_integrity_error(self):
        with self.app.app_context():
            target_contract = self._contract(servicio="Contrato objetivo")
            other_contract = self._contract(servicio="Contrato ajeno")
            correlation_id = "231e84fe-fb73-4265-a957-94fd6bd39783"
            payload_hash = contract_review_service._payload_hash(
                contract_review_service._canonical_payload(
                    target_contract.id,
                    5,
                    contract_review_service._normalize_comment("Incoherente"),
                )
            )
            foreign_review = Review(
                contract_id=other_contract.id,
                cliente_id=self.owner_id,
                professional_id=self.professional_id,
                rating=5,
                comentario="Incoherente",
                comment_public="Incoherente",
                origin=Review.ORIGIN_CONTRACTUAL,
                verification_status=Review.VERIFICATION_VERIFIED,
                comment_visibility_status=Review.COMMENT_VISIBLE,
                rating_eligibility_status=Review.RATING_ELIGIBLE,
                correlation_id=correlation_id,
                payload_hash=payload_hash,
            )
            db.session.add(foreign_review)
            db.session.flush()
            db.session.add(
                OperationCommand(
                    actor_user_id=self.owner_id,
                    operation=OPERATION_CREATE_CONTRACT_REVIEW,
                    idempotency_key="contract-review-incoherent-result",
                    payload_hash=payload_hash,
                    status=OperationCommand.STATUS_SUCCEEDED,
                    result_entity_type="Review",
                    result_entity_id=foreign_review.id,
                    correlation_id=correlation_id,
                )
            )
            db.session.commit()

            with self.assertRaises(ContractReviewIntegrityError):
                self._create(
                    target_contract,
                    key="contract-review-incoherent-result",
                    comment="Incoherente",
                )
            self.assertEqual(
                Review.query.filter_by(contract_id=target_contract.id).count(),
                0,
            )

    def test_authorization_is_rechecked_before_replay(self):
        with self.app.app_context():
            contract = self._contract()
            review = self._create(
                contract,
                key="contract-review-authorization-replay",
            )
            owner = db.session.get(User, self.owner_id)
            owner.estado = "SUSPENDIDO"
            db.session.commit()
            with self.assertRaises(PermissionError):
                self._create(
                    contract,
                    key="contract-review-authorization-replay",
                )
            self.assertEqual(Review.query.count(), 1)
            self.assertEqual(db.session.get(Review, review.id).id, review.id)

    def test_each_derived_failure_rolls_back_and_session_is_reusable(self):
        helpers = (
            "_create_reputation_event",
            "_create_audit_log",
            "_create_notification",
            "_complete_command",
        )
        with self.app.app_context():
            for index, helper_name in enumerate(helpers, start=1):
                contract = self._contract(servicio=f"Rollback {helper_name}")
                key = f"contract-review-rollback-{index:04d}"
                counts_before = self._counts()
                with self.subTest(helper=helper_name):
                    with patch.object(
                        contract_review_service,
                        helper_name,
                        side_effect=RuntimeError(f"forced {helper_name}"),
                    ):
                        with self.assertRaises(RuntimeError):
                            self._create(contract, key=key)
                    self.assertEqual(self._counts(), counts_before)
                    retry = self._create(contract, key=key)
                    self.assertEqual(retry.contract_id, contract.id)
                    self.assertEqual(
                        db.session.query(User).count(),
                        6,
                    )

    def test_internal_effect_helpers_do_not_commit(self):
        helper_names = (
            "_create_review",
            "_create_reputation_event",
            "_create_audit_log",
            "_create_notification",
            "_complete_command",
        )
        for helper_name in helper_names:
            with self.subTest(helper=helper_name):
                source = inspect.getsource(
                    getattr(contract_review_service, helper_name)
                )
                self.assertNotIn(".commit(", source)

    def test_new_service_never_calls_legacy_arbitrary_points_mutator(self):
        with self.app.app_context():
            contract = self._contract()
            self.assertFalse(hasattr(reputation_service, "add_reputation_event"))
            self.assertNotIn(
                "add_reputation_event",
                inspect.getsource(contract_review_service),
            )
            review = self._create(
                contract,
                key="contract-review-no-legacy-mutator",
            )
            event = ReputationEvent.query.filter_by(review_id=review.id).one()
            self.assertIsNone(event.puntos)


if __name__ == "__main__":
    unittest.main()
