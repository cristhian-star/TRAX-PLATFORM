import os
import unittest


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
from app.models.user import User
from app.services.budget_service import award_budget_offer


class Sprint7BudgetToContractTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(nombre="Cliente", email="cliente-budget@test.local", password="hash", rol="CLIENTE")
            self.other_user = User(nombre="Otro", email="otro-budget@test.local", password="hash", rol="CLIENTE")
            self.professional_user = User(nombre="Pro", email="pro-budget@test.local", password="hash", rol="PROFESIONAL")
            db.session.add_all([self.client_user, self.other_user, self.professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Nexo Budget",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.flush()
            self.budget_request = BudgetRequest(
                cliente_id=self.client_user.id,
                categoria="Electricidad",
                titulo="Tablero",
                descripcion="Instalar tablero",
                zona="CABA",
                estado="PUBLICADA",
            )
            db.session.add(self.budget_request)
            db.session.flush()
            self.offer = BudgetOffer(
                budget_request_id=self.budget_request.id,
                professional_id=self.professional.id,
                professional_user_id=self.professional_user.id,
                monto=100,
                monto_desde=100,
                monto_hasta=120,
                mensaje="Oferta",
                plazo_estimado="3 dias",
            )
            db.session.add(self.offer)
            db.session.commit()
            self.client_id = self.client_user.id
            self.other_id = self.other_user.id
            self.professional_id = self.professional.id
            self.professional_user_id = self.professional_user.id
            self.budget_request_id = self.budget_request.id
            self.offer_id = self.offer.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_awarding_budget_offer_creates_exactly_one_contract_with_references(self):
        with self.app.app_context():
            award_budget_offer(self.budget_request_id, self.offer_id, self.client_id)
            award_budget_offer(self.budget_request_id, self.offer_id, self.client_id)

            contracts = ContractRequest.query.all()
            self.assertEqual(len(contracts), 1)
            contract = contracts[0]
            self.assertEqual(contract.source_type, ContractRequest.SOURCE_BUDGET)
            self.assertEqual(contract.source_id, self.offer_id)
            self.assertEqual(contract.budget_offer_id, self.offer_id)
            self.assertIsNone(contract.proposal_application_id)
            self.assertEqual(contract.cliente_id, self.client_id)
            self.assertEqual(contract.professional_id, self.professional_id)
            self.assertEqual(contract.professional_user_id, self.professional_user_id)
            self.assertEqual(contract.estado, "CREADA")
            self.assertEqual(BudgetOffer.query.get(self.offer_id).estado, "ADJUDICADO")
            self.assertEqual(BudgetRequest.query.get(self.budget_request_id).estado, "ADJUDICADA")

    def test_budget_contract_creates_events_audit_and_notifications(self):
        with self.app.app_context():
            award_budget_offer(self.budget_request_id, self.offer_id, self.client_id)
            contract = ContractRequest.query.one()

            self.assertEqual(
                ContractEvent.query.filter_by(
                    contract_id=contract.id,
                    event_type=ContractEvent.CREATED_FROM_BUDGET,
                ).count(),
                1,
            )
            self.assertEqual(AuditLog.query.filter_by(action=ContractEvent.CREATED_FROM_BUDGET).count(), 1)
            self.assertGreaterEqual(ActivityNotification.query.filter_by(entity_id=contract.id).count(), 2)

            award_budget_offer(self.budget_request_id, self.offer_id, self.client_id)
            self.assertEqual(ContractEvent.query.filter_by(contract_id=contract.id).count(), 2)
            self.assertEqual(AuditLog.query.filter_by(action=ContractEvent.CREATED_FROM_BUDGET).count(), 1)
            self.assertEqual(ActivityNotification.query.filter_by(entity_id=contract.id).count(), 2)

    def test_unrelated_user_cannot_award_budget_offer(self):
        with self.app.app_context():
            with self.assertRaises(PermissionError):
                award_budget_offer(self.budget_request_id, self.offer_id, self.other_id)
            self.assertEqual(ContractRequest.query.count(), 0)

    def test_award_rolls_back_offer_state_when_contract_creation_fails(self):
        with self.app.app_context():
            from app.services import budget_service

            original_creator = budget_service.create_contract_from_budget_offer

            def failing_creator(*args, **kwargs):
                raise RuntimeError("fallo simulado")

            budget_service.create_contract_from_budget_offer = failing_creator
            try:
                with self.assertRaises(RuntimeError):
                    award_budget_offer(self.budget_request_id, self.offer_id, self.client_id)
            finally:
                budget_service.create_contract_from_budget_offer = original_creator

            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertNotEqual(BudgetOffer.query.get(self.offer_id).estado, "ADJUDICADO")
            self.assertEqual(BudgetRequest.query.get(self.budget_request_id).estado, "PUBLICADA")


if __name__ == "__main__":
    unittest.main()
