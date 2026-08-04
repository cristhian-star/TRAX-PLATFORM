import os
import unittest

from sqlalchemy.exc import IntegrityError


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

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
from app.models.verification_request import VerificationRequest
from app.services.contract_service import IdempotencyConflictError
from app.services.negotiation_service import (
    NegotiationConflictError,
    accept_negotiation_terms,
    cancel_negotiation,
    finalize_negotiation_contract,
    get_negotiation_for_actor,
    initiate_direct_negotiation,
    propose_negotiation_terms,
    reject_negotiation,
)


class Sprint7NegotiationMVPTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.http = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            users = [
                User(
                    nombre="Cliente",
                    email="neg-client@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Otro cliente",
                    email="neg-other@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Suspendido",
                    email="neg-suspended@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="SUSPENDIDO",
                ),
                User(
                    nombre="Profesional",
                    email="neg-professional@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
            ]
            db.session.add_all(users)
            db.session.flush()
            professional = Professional(
                user_id=users[3].id,
                nombre="Profesional MVP",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
                estado_perfil="VERIFICADO",
            )
            db.session.add(professional)
            db.session.add_all(
                [
                    VerificationRequest(
                        user_id=users[0].id,
                        tipo_usuario="CLIENTE",
                        estado="APROBADO",
                    ),
                    VerificationRequest(
                        user_id=users[3].id,
                        tipo_usuario="PROFESIONAL",
                        estado="APROBADO",
                    ),
                ]
            )
            db.session.commit()
            self.client_id = users[0].id
            self.other_client_id = users[1].id
            self.suspended_id = users[2].id
            self.professional_user_id = users[3].id
            self.professional_id = professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _init_kwargs(self, **overrides):
        values = {
            "cliente_id": self.client_id,
            "professional_id": self.professional_id,
            "servicio": "Instalacion electrica",
            "description": "Instalar tablero nuevo",
            "scope": "Materiales y mano de obra",
            "external_price": "125000.00",
            "observations": "Pago externo a TRAX",
            "actor_user_id": self.client_id,
            "idempotency_key": "negotiation-init-mvp-0001",
        }
        values.update(overrides)
        return values

    def _initiate(self, **overrides):
        return initiate_direct_negotiation(**self._init_kwargs(**overrides))

    def _accept(self, negotiation, actor_id, key):
        return accept_negotiation_terms(
            negotiation.id,
            actor_user_id=actor_id,
            expected_version=negotiation.version,
            terms_version=negotiation.current_terms_version,
            idempotency_key=key,
        )

    def _agree(self):
        negotiation = self._initiate()
        negotiation = self._accept(
            negotiation,
            self.client_id,
            "negotiation-accept-client-0001",
        )
        negotiation = self._accept(
            negotiation,
            self.professional_user_id,
            "negotiation-accept-professional-0001",
        )
        self.assertEqual(negotiation.state, ContractNegotiation.STATE_AGREED)
        return negotiation

    def _assert_initial_counts(self):
        self.assertEqual(ContractNegotiation.query.count(), 1)
        self.assertEqual(ContractNegotiationVersion.query.count(), 1)
        self.assertEqual(NegotiationAcceptance.query.count(), 0)
        self.assertEqual(NegotiationEvent.query.count(), 1)
        self.assertEqual(OperationCommand.query.count(), 1)
        self.assertEqual(AuditLog.query.count(), 1)
        self.assertEqual(ActivityNotification.query.count(), 1)
        self.assertEqual(ContractRequest.query.count(), 0)
        self.assertEqual(ContractEvent.query.count(), 0)

    def test_actor_is_explicit_active_and_owner(self):
        with self.app.app_context():
            for actor_id in (None, 999999, self.suspended_id):
                with self.assertRaises(PermissionError):
                    self._initiate(actor_user_id=actor_id)
            with self.assertRaises(PermissionError):
                self._initiate(actor_user_id=self.other_client_id)
            self.assertEqual(ContractNegotiation.query.count(), 0)

    def test_professional_and_unrelated_users_cannot_access_or_mutate(self):
        with self.app.app_context():
            negotiation = self._initiate()
            with self.assertRaises(PermissionError):
                get_negotiation_for_actor(
                    negotiation.id,
                    actor_user_id=self.other_client_id,
                )
            with self.assertRaises(PermissionError):
                accept_negotiation_terms(
                    negotiation.id,
                    actor_user_id=self.other_client_id,
                    expected_version=1,
                    terms_version=1,
                    idempotency_key="negotiation-unauthorized-0001",
                )
            self._assert_initial_counts()

    def test_authorization_precedes_replay(self):
        with self.app.app_context():
            negotiation = self._initiate()
            actor = db.session.get(User, self.client_id)
            actor.estado = "SUSPENDIDO"
            db.session.commit()
            with self.assertRaises(PermissionError):
                self._initiate()
            self.assertEqual(ContractNegotiation.query.count(), 1)
            self.assertEqual(OperationCommand.query.count(), 1)

    def test_exact_replay_and_payload_conflict(self):
        with self.app.app_context():
            first = self._initiate()
            second = self._initiate()
            self.assertEqual(first.id, second.id)
            self._assert_initial_counts()
            with self.assertRaises(IdempotencyConflictError):
                self._initiate(scope="Un alcance diferente")
            self._assert_initial_counts()

    def test_new_version_logically_invalidates_previous_acceptance(self):
        with self.app.app_context():
            negotiation = self._initiate()
            negotiation = self._accept(
                negotiation,
                self.client_id,
                "negotiation-accept-before-change",
            )
            negotiation = propose_negotiation_terms(
                negotiation.id,
                description="Descripcion revisada",
                scope="Alcance revisado",
                external_price="130000",
                observations=None,
                actor_user_id=self.professional_user_id,
                expected_version=negotiation.version,
                idempotency_key="negotiation-propose-v2-0001",
            )
            self.assertEqual(negotiation.current_terms_version, 2)
            current = ContractNegotiationVersion.query.filter_by(
                negotiation_id=negotiation.id,
                version_no=2,
            ).one()
            self.assertEqual(
                NegotiationAcceptance.query.filter_by(
                    negotiation_version_id=current.id
                ).count(),
                0,
            )
            self.assertEqual(NegotiationAcceptance.query.count(), 1)
            self.assertEqual(ContractNegotiationVersion.query.count(), 2)
            with self.assertRaises(NegotiationConflictError):
                accept_negotiation_terms(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=negotiation.version,
                    terms_version=1,
                    idempotency_key="negotiation-accept-stale-v1",
                )

    def test_both_parties_must_accept_same_version(self):
        with self.app.app_context():
            negotiation = self._agree()
            self.assertEqual(negotiation.agreed_terms_version, 1)
            self.assertEqual(NegotiationAcceptance.query.count(), 2)
            self.assertEqual(NegotiationEvent.query.count(), 4)
            self.assertEqual(AuditLog.query.count(), 4)
            self.assertEqual(ActivityNotification.query.count(), 3)
            self.assertEqual(ContractEvent.query.count(), 0)

    def test_only_client_cancels_and_only_professional_rejects(self):
        with self.app.app_context():
            negotiation = self._initiate()
            with self.assertRaises(PermissionError):
                cancel_negotiation(
                    negotiation.id,
                    actor_user_id=self.professional_user_id,
                    expected_version=1,
                    idempotency_key="negotiation-bad-cancel-0001",
                )
            cancelled = cancel_negotiation(
                negotiation.id,
                actor_user_id=self.client_id,
                expected_version=1,
                idempotency_key="negotiation-cancel-0001",
            )
            self.assertEqual(cancelled.state, ContractNegotiation.STATE_CANCELLED)

        with self.app.app_context():
            db.session.remove()
            negotiation = self._initiate(
                idempotency_key="negotiation-init-for-reject"
            )
            with self.assertRaises(PermissionError):
                reject_negotiation(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=1,
                    idempotency_key="negotiation-bad-reject-0001",
                )
            rejected = reject_negotiation(
                negotiation.id,
                actor_user_id=self.professional_user_id,
                expected_version=1,
                idempotency_key="negotiation-reject-0001",
            )
            self.assertEqual(rejected.state, ContractNegotiation.STATE_REJECTED)

    def test_finalize_is_atomic_idempotent_and_exact(self):
        with self.app.app_context():
            negotiation = self._agree()
            agreed_version = negotiation.version
            contract = finalize_negotiation_contract(
                negotiation.id,
                actor_user_id=self.client_id,
                expected_version=agreed_version,
                terms_version=1,
                idempotency_key="negotiation-finalize-0001",
            )
            replay = finalize_negotiation_contract(
                negotiation.id,
                actor_user_id=self.client_id,
                expected_version=agreed_version,
                terms_version=1,
                idempotency_key="negotiation-finalize-0001",
            )
            self.assertEqual(contract.id, replay.id)
            self.assertEqual(contract.estado, "CREADA")
            self.assertEqual(contract.source_type, "DIRECT")
            self.assertEqual(contract.contracting_mode, "EXTERNAL")
            stored = db.session.get(ContractNegotiation, negotiation.id)
            self.assertEqual(stored.state, ContractNegotiation.STATE_CONTRACTED)
            self.assertEqual(stored.contract_id, contract.id)
            self.assertEqual(ContractRequest.query.count(), 1)
            self.assertEqual(ContractEvent.query.count(), 1)
            self.assertEqual(NegotiationEvent.query.count(), 5)
            self.assertEqual(OperationCommand.query.count(), 4)
            self.assertEqual(AuditLog.query.count(), 6)
            self.assertEqual(ActivityNotification.query.count(), 4)
            self.assertEqual(
                NegotiationEvent.query.filter_by(
                    event_type=NegotiationEvent.CONTRACT_CREATED
                ).count(),
                1,
            )

    def test_finalize_requires_client_current_version_and_two_acceptances(self):
        with self.app.app_context():
            negotiation = self._initiate()
            with self.assertRaises(PermissionError):
                finalize_negotiation_contract(
                    negotiation.id,
                    actor_user_id=self.professional_user_id,
                    expected_version=1,
                    terms_version=1,
                    idempotency_key="negotiation-finalize-by-pro",
                )
            with self.assertRaises(ValueError):
                finalize_negotiation_contract(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=1,
                    terms_version=1,
                    idempotency_key="negotiation-finalize-too-early",
                )
            self.assertEqual(ContractRequest.query.count(), 0)

    def test_real_constraint_failure_rolls_back_all_finalize_effects(self):
        with self.app.app_context():
            from app.services import negotiation_service

            negotiation = self._agree()
            counts_before = {
                "commands": OperationCommand.query.count(),
                "negotiation_events": NegotiationEvent.query.count(),
                "audits": AuditLog.query.count(),
                "notifications": ActivityNotification.query.count(),
            }
            original = negotiation_service._create_contract_effects

            def create_with_invalid_notification(*args, **kwargs):
                contract = original(*args, **kwargs)
                db.session.add(
                    ActivityNotification(
                        user_id=self.professional_user_id,
                        tipo="INVALID_CHANNEL",
                        categoria="CONTRATACIONES",
                        titulo="Constraint",
                        mensaje="Debe fallar",
                        channel="SMS",
                        delivery_status="DELIVERED",
                        attempt_count=0,
                        prioridad="INFO",
                        requiere_accion=False,
                    )
                )
                return contract

            negotiation_service._create_contract_effects = (
                create_with_invalid_notification
            )
            try:
                with self.assertRaises(IntegrityError):
                    finalize_negotiation_contract(
                        negotiation.id,
                        actor_user_id=self.client_id,
                        expected_version=negotiation.version,
                        terms_version=1,
                        idempotency_key="negotiation-finalize-constraint",
                    )
            finally:
                negotiation_service._create_contract_effects = original

            stored = db.session.get(ContractNegotiation, negotiation.id)
            self.assertEqual(stored.state, ContractNegotiation.STATE_AGREED)
            self.assertIsNone(stored.contract_id)
            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertEqual(ContractEvent.query.count(), 0)
            self.assertEqual(OperationCommand.query.count(), counts_before["commands"])
            self.assertEqual(
                NegotiationEvent.query.count(),
                counts_before["negotiation_events"],
            )
            self.assertEqual(AuditLog.query.count(), counts_before["audits"])
            self.assertEqual(
                ActivityNotification.query.count(),
                counts_before["notifications"],
            )

    def test_minimal_http_flow_and_ownership(self):
        with self.app.app_context():
            pass
        with self.http.session_transaction() as browser_session:
            browser_session["user_id"] = self.client_id
            browser_session["user_role"] = "CLIENTE"
        response = self.http.post(
            "/negociacion/nueva",
            data={
                "professional_id": str(self.professional_id),
                "servicio": "Demo",
                "description": "Descripcion demo",
                "scope": "Alcance demo",
                "external_price": "1000",
                "idempotency_key": "negotiation-http-init-0001",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/negociacion/", response.location)
        detail = self.http.get(response.location)
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"Terminos vigentes", detail.data)
        self.assertIn(b"Pendiente", detail.data)

        with self.http.session_transaction() as browser_session:
            browser_session["user_id"] = self.other_client_id
            browser_session["user_role"] = "CLIENTE"
        self.assertEqual(self.http.get(response.location).status_code, 403)


if __name__ == "__main__":
    unittest.main()
