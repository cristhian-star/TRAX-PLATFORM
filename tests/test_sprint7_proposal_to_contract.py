import os
import unittest


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.proposal_application import ProposalApplication
from app.models.proposal_request import ProposalRequest
from app.models.user import User
from app.services.proposal_service import accept_application


class Sprint7ProposalToContractTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.owner = User(nombre="Owner", email="owner-proposal@test.local", password="hash", rol="CLIENTE")
            self.other = User(nombre="Other", email="other-proposal@test.local", password="hash", rol="CLIENTE")
            self.professional_user = User(nombre="Pro", email="pro-proposal@test.local", password="hash", rol="PROFESIONAL")
            self.second_professional_user = User(nombre="Pro 2", email="pro2-proposal@test.local", password="hash", rol="PROFESIONAL")
            db.session.add_all([self.owner, self.other, self.professional_user, self.second_professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Nexo Proposal",
                servicio="Albanileria",
                zona="CABA",
                perfil_completo=True,
            )
            self.second_professional = Professional(
                user_id=self.second_professional_user.id,
                nombre="Nexo Proposal 2",
                servicio="Pintura",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add_all([self.professional, self.second_professional])
            db.session.flush()
            self.proposal = ProposalRequest(
                cliente_id=self.owner.id,
                owner_user_id=self.owner.id,
                categoria="Construccion",
                titulo="Ceramicos",
                descripcion="Colocar ceramicos",
                estado="PUBLICADA",
            )
            db.session.add(self.proposal)
            db.session.flush()
            self.application = ProposalApplication(
                proposal_id=self.proposal.id,
                professional_id=self.professional.id,
                professional_user_id=self.professional_user.id,
                mensaje="Puedo hacerlo",
                pretension_economica=300,
            )
            self.second_application = ProposalApplication(
                proposal_id=self.proposal.id,
                professional_id=self.second_professional.id,
                professional_user_id=self.second_professional_user.id,
                mensaje="Tambien puedo",
                pretension_economica=350,
            )
            db.session.add_all([self.application, self.second_application])
            db.session.commit()
            self.owner_id = self.owner.id
            self.other_id = self.other.id
            self.professional_id = self.professional.id
            self.professional_user_id = self.professional_user.id
            self.proposal_id = self.proposal.id
            self.application_id = self.application.id
            self.second_application_id = self.second_application.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_accepting_proposal_application_creates_exactly_one_contract_with_references(self):
        with self.app.app_context():
            accept_application(self.proposal_id, self.application_id, self.owner_id)
            accept_application(self.proposal_id, self.application_id, self.owner_id)

            contracts = ContractRequest.query.all()
            self.assertEqual(len(contracts), 1)
            contract = contracts[0]
            self.assertEqual(contract.source_type, ContractRequest.SOURCE_PROPOSAL)
            self.assertEqual(contract.source_id, self.application_id)
            self.assertEqual(contract.proposal_application_id, self.application_id)
            self.assertIsNone(contract.budget_offer_id)
            self.assertEqual(contract.cliente_id, self.owner_id)
            self.assertEqual(contract.professional_id, self.professional_id)
            self.assertEqual(contract.professional_user_id, self.professional_user_id)
            self.assertEqual(contract.estado, "CREADA")
            self.assertEqual(ProposalApplication.query.get(self.application_id).estado, "ACEPTADA")
            self.assertEqual(ProposalRequest.query.get(self.proposal_id).estado, "CERRADA")
            self.assertEqual(ProposalApplication.query.get(self.second_application_id).estado, "DESCARTADA")

    def test_proposal_contract_creates_events_audit_and_notifications(self):
        with self.app.app_context():
            accept_application(self.proposal_id, self.application_id, self.owner_id)
            contract = ContractRequest.query.one()

            self.assertEqual(
                ContractEvent.query.filter_by(
                    contract_id=contract.id,
                    event_type=ContractEvent.CREATED_FROM_PROPOSAL,
                ).count(),
                1,
            )
            self.assertEqual(AuditLog.query.filter_by(action=ContractEvent.CREATED_FROM_PROPOSAL).count(), 1)
            self.assertGreaterEqual(ActivityNotification.query.filter_by(entity_id=contract.id).count(), 2)

            accept_application(self.proposal_id, self.application_id, self.owner_id)
            self.assertEqual(ContractEvent.query.filter_by(contract_id=contract.id).count(), 2)
            self.assertEqual(AuditLog.query.filter_by(action=ContractEvent.CREATED_FROM_PROPOSAL).count(), 1)
            self.assertEqual(ActivityNotification.query.filter_by(entity_id=contract.id).count(), 2)

    def test_unrelated_user_cannot_accept_application(self):
        with self.app.app_context():
            with self.assertRaises(PermissionError):
                accept_application(self.proposal_id, self.application_id, self.other_id)
            self.assertEqual(ContractRequest.query.count(), 0)

    def test_single_hiring_mode_rejects_accepting_discarded_application(self):
        with self.app.app_context():
            accept_application(self.proposal_id, self.application_id, self.owner_id)

            with self.assertRaises(ValueError):
                accept_application(self.proposal_id, self.second_application_id, self.owner_id)

            self.assertEqual(ContractRequest.query.count(), 1)

    def test_accept_application_rolls_back_state_when_contract_creation_fails(self):
        with self.app.app_context():
            from app.services import proposal_service

            original_creator = proposal_service.create_contract_from_proposal_application

            def failing_creator(*args, **kwargs):
                raise RuntimeError("fallo simulado")

            proposal_service.create_contract_from_proposal_application = failing_creator
            try:
                with self.assertRaises(RuntimeError):
                    accept_application(self.proposal_id, self.application_id, self.owner_id)
            finally:
                proposal_service.create_contract_from_proposal_application = original_creator

            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertEqual(ProposalApplication.query.get(self.application_id).estado, "POSTULADA")
            self.assertEqual(ProposalApplication.query.get(self.second_application_id).estado, "POSTULADA")
            self.assertEqual(ProposalRequest.query.get(self.proposal_id).estado, "PUBLICADA")


if __name__ == "__main__":
    unittest.main()
