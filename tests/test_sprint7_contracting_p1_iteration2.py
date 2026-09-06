import os
import unittest
from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.budget_offer import BudgetOffer
from app.models.budget_request import BudgetRequest
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.proposal_application import ProposalApplication
from app.models.proposal_request import ProposalRequest
from app.models.user import User
from app.services.contracting_core_service import (
    create_contract_from_budget_offer,
    create_contract_from_proposal_application,
)
from app.services.proposal_service import accept_application


class Sprint7ContractingP1Iteration2Test(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            users = [
                User(
                    nombre="Owner",
                    email="p1-owner@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Other",
                    email="p1-other@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Suspended",
                    email="p1-suspended@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="SUSPENDIDO",
                ),
                User(
                    nombre="Banned",
                    email="p1-banned@test.local",
                    password="hash",
                    rol="CLIENTE",
                    estado="BANEADO",
                ),
                User(
                    nombre="Admin",
                    email="p1-admin@test.local",
                    password="hash",
                    rol="SUPER_ADMIN",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Professional",
                    email="p1-professional@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
                User(
                    nombre="Professional 2",
                    email="p1-professional-2@test.local",
                    password="hash",
                    rol="PROFESIONAL",
                    estado="ACTIVO",
                ),
            ]
            db.session.add_all(users)
            db.session.flush()
            (
                owner,
                other,
                suspended,
                banned,
                admin,
                professional_user,
                second_professional_user,
            ) = users
            professional = Professional(
                user_id=professional_user.id,
                nombre="Professional P1",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            second_professional = Professional(
                user_id=second_professional_user.id,
                nombre="Professional P1 2",
                servicio="Pintura",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add_all([professional, second_professional])
            db.session.flush()

            budget = BudgetRequest(
                cliente_id=owner.id,
                categoria="Electricidad",
                titulo="Tablero P1",
                descripcion="Instalar tablero",
                zona="CABA",
                estado="ADJUDICADA",
            )
            proposal = ProposalRequest(
                cliente_id=owner.id,
                owner_user_id=owner.id,
                categoria="Construccion",
                titulo="Ceramicos P1",
                descripcion="Colocar ceramicos",
                hiring_mode=ProposalRequest.HIRING_MODE_SINGLE,
                estado="CERRADA",
            )
            db.session.add_all([budget, proposal])
            db.session.flush()
            offer = BudgetOffer(
                budget_request_id=budget.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                monto=100,
                mensaje="Oferta",
                plazo_estimado="3 dias",
                estado="ADJUDICADO",
            )
            application = ProposalApplication(
                proposal_id=proposal.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                mensaje="Puedo hacerlo",
                pretension_economica=300,
                estado="ACEPTADA",
            )
            second_application = ProposalApplication(
                proposal_id=proposal.id,
                professional_id=second_professional.id,
                professional_user_id=second_professional_user.id,
                mensaje="Tambien puedo",
                pretension_economica=350,
                estado="DESCARTADA",
            )
            db.session.add_all([offer, application, second_application])
            db.session.commit()

            self.owner_id = owner.id
            self.other_id = other.id
            self.suspended_id = suspended.id
            self.banned_id = banned.id
            self.admin_id = admin.id
            self.professional_user_id = professional_user.id
            self.offer_id = offer.id
            self.proposal_id = proposal.id
            self.application_id = application.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _creators(self):
        return (
            (create_contract_from_budget_offer, self.offer_id),
            (create_contract_from_proposal_application, self.application_id),
        )

    def _assert_effect_counts(self, contracts):
        self.assertEqual(ContractRequest.query.count(), contracts)
        self.assertEqual(ContractEvent.query.count(), contracts * 2)
        self.assertEqual(AuditLog.query.count(), contracts)
        self.assertEqual(ActivityNotification.query.count(), contracts * 2)

    def test_derived_creators_require_active_client_owner_actor(self):
        with self.app.app_context():
            invalid_actors = (
                None,
                999999,
                self.suspended_id,
                self.banned_id,
                self.admin_id,
                self.professional_user_id,
                self.other_id,
            )
            for creator, source_id in self._creators():
                for actor_id in invalid_actors:
                    with self.subTest(
                        creator=creator.__name__,
                        actor_id=actor_id,
                    ), self.assertRaises(PermissionError):
                        creator(source_id, actor_user_id=actor_id)
            self._assert_effect_counts(0)

    def test_invalid_actor_is_rejected_before_derived_replay(self):
        with self.app.app_context():
            for creator, source_id in self._creators():
                first = creator(source_id, actor_user_id=self.owner_id)
                db.session.commit()
                for actor_id in (
                    None,
                    999999,
                    self.suspended_id,
                    self.banned_id,
                    self.admin_id,
                    self.professional_user_id,
                    self.other_id,
                ):
                    with self.subTest(
                        creator=creator.__name__,
                        actor_id=actor_id,
                    ), self.assertRaises(PermissionError):
                        creator(source_id, actor_user_id=actor_id)
                self.assertIsNotNone(db.session.get(ContractRequest, first.contract.id))
            self._assert_effect_counts(2)

    def test_owner_status_is_rechecked_before_replay(self):
        with self.app.app_context():
            result = create_contract_from_budget_offer(
                self.offer_id,
                actor_user_id=self.owner_id,
            )
            db.session.commit()
            owner = db.session.get(User, self.owner_id)
            owner.estado = "SUSPENDIDO"
            db.session.commit()

            with self.assertRaises(PermissionError):
                create_contract_from_budget_offer(
                    self.offer_id,
                    actor_user_id=self.owner_id,
                )
            self.assertIsNotNone(db.session.get(ContractRequest, result.contract.id))
            self._assert_effect_counts(1)

    def test_sequential_replay_returns_same_contract_and_exact_effects(self):
        with self.app.app_context():
            for creator, source_id in self._creators():
                first = creator(source_id, actor_user_id=self.owner_id)
                second = creator(source_id, actor_user_id=self.owner_id)
                db.session.commit()
                third = creator(source_id, actor_user_id=self.owner_id)
                self.assertEqual(first.contract.id, second.contract.id)
                self.assertEqual(first.contract.id, third.contract.id)
                self.assertTrue(first.created)
                self.assertFalse(second.created)
                self.assertFalse(third.created)
            self._assert_effect_counts(2)

    def test_unique_race_recovery_keeps_session_reusable_and_no_duplicates(self):
        with self.app.app_context():
            from app.services import contracting_core_service

            cases = (
                (
                    create_contract_from_budget_offer,
                    self.offer_id,
                    "_budget_contract",
                ),
                (
                    create_contract_from_proposal_application,
                    self.application_id,
                    "_proposal_contract",
                ),
            )
            for creator, source_id, lookup_name in cases:
                existing = creator(source_id, actor_user_id=self.owner_id).contract
                db.session.commit()
                with patch.object(
                    contracting_core_service,
                    lookup_name,
                    side_effect=[None, existing],
                ):
                    recovered = creator(source_id, actor_user_id=self.owner_id)
                self.assertEqual(recovered.contract.id, existing.id)
                self.assertFalse(recovered.created)
                self.assertEqual(User.query.count(), 7)
            self._assert_effect_counts(2)

    def test_multiple_is_rejected_by_orm_and_raw_sql_constraint(self):
        with self.app.app_context():
            proposal = db.session.get(ProposalRequest, self.proposal_id)
            proposal.hiring_mode = "MULTIPLE"
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            with self.assertRaises(IntegrityError):
                db.session.execute(
                    text(
                        "UPDATE proposal_requests "
                        "SET hiring_mode = 'MULTIPLE' WHERE id = :proposal_id"
                    ),
                    {"proposal_id": self.proposal_id},
                )
            db.session.rollback()
            self.assertEqual(
                db.session.get(ProposalRequest, self.proposal_id).hiring_mode,
                ProposalRequest.HIRING_MODE_SINGLE,
            )

    def test_acceptance_service_rejects_multiple_before_source_mutation(self):
        with self.app.app_context():
            proposal = db.session.get(ProposalRequest, self.proposal_id)
            application = db.session.get(ProposalApplication, self.application_id)
            proposal.hiring_mode = "MULTIPLE"
            application.estado = "POSTULADA"
            proposal.estado = "PUBLICADA"

            with self.assertRaises(ValueError):
                accept_application(
                    self.proposal_id,
                    self.application_id,
                    self.owner_id,
                )

            self.assertEqual(
                db.session.get(ProposalRequest, self.proposal_id).estado,
                "CERRADA",
            )
            self.assertEqual(
                db.session.get(ProposalApplication, self.application_id).estado,
                "ACEPTADA",
            )
            self._assert_effect_counts(0)

    @unittest.skip(
        "SQLite in-memory no ofrece bloqueo de filas ni sesiones independientes "
        "equivalentes a PostgreSQL"
    )
    def test_real_concurrent_independent_sessions(self):
        pass


if __name__ == "__main__":
    unittest.main()
