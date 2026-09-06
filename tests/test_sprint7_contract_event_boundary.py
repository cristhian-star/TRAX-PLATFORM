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
from app.models.user import User
from app.services import contract_service, contracting_core_service
from app.services.contract_service import create_contract


class Sprint7ContractEventBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            client = User(
                nombre="Boundary client",
                email="boundary-client@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="Boundary professional",
                email="boundary-professional@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all([client, professional_user])
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="Boundary professional",
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
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_direct(self):
        return create_contract(
            cliente_id=self.client_id,
            professional_id=self.professional_id,
            professional_user_id=self.professional_user_id,
            servicio="Boundary contract",
            actor_user_id=self.client_id,
            idempotency_key="boundary-direct-create-0001",
        )

    def _assert_direct_effects(self):
        self.assertEqual(ContractRequest.query.count(), 1)
        self.assertEqual(ContractEvent.query.count(), 1)
        self.assertEqual(AuditLog.query.count(), 1)
        self.assertEqual(ActivityNotification.query.count(), 1)

    def test_external_generic_event_import_is_unavailable(self):
        namespace = {}
        with self.assertRaises(ImportError):
            exec(
                "from app.services.contracting_core_service "
                "import create_contract_event",
                namespace,
            )
        self.assertNotIn("create_contract_event", contracting_core_service.__all__)
        self.assertFalse(hasattr(contracting_core_service, "create_contract_event"))

    def test_no_legacy_alias_or_alternate_service_exposes_generic_event_writer(self):
        for module in (contracting_core_service, contract_service):
            exposed = {
                name
                for name in dir(module)
                if not name.startswith("_") and "contract_event" in name.lower()
            }
            self.assertEqual(exposed, set())

    def test_fabricated_created_to_confirmed_event_cannot_be_appended(self):
        with self.app.app_context():
            contract = self._create_direct()
            with self.assertRaises(AttributeError):
                getattr(contracting_core_service, "create_contract_event")(
                    contract,
                    ContractEvent.CONTRACT_CONFIRMED,
                    actor_user_id=self.client_id,
                    previous_status="CREADA",
                    new_status="CONFIRMADA",
                )
            self.assertEqual(contract.estado, "CREADA")
            self._assert_direct_effects()

    def test_null_actor_and_arbitrary_final_state_are_not_accepted_by_private_derived_flow(self):
        with self.app.app_context():
            base_kwargs = {
                "cliente_id": self.client_id,
                "professional_id": self.professional_id,
                "professional_user_id": self.professional_user_id,
                "servicio": "Invalid derived",
                "descripcion": None,
                "precio_acordado": None,
                "source_type": ContractRequest.SOURCE_BUDGET,
                "source_id": 999,
                "created_from_event": ContractEvent.CREATED_FROM_BUDGET,
                "professional_message": "Invalid",
                "budget_offer_id": 999,
            }
            with self.assertRaises(PermissionError):
                contracting_core_service._create_contract(
                    **base_kwargs,
                    actor_user_id=None,
                )
            with self.assertRaises(TypeError):
                contracting_core_service._create_contract(
                    **base_kwargs,
                    actor_user_id=self.client_id,
                    new_status="CONFIRMADA",
                )
            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertEqual(ContractEvent.query.count(), 0)
            self.assertEqual(AuditLog.query.count(), 0)
            self.assertEqual(ActivityNotification.query.count(), 0)

    def test_mismatched_source_event_is_rejected_before_any_effect(self):
        with self.app.app_context():
            with self.assertRaises(ValueError):
                contracting_core_service._create_contract(
                    cliente_id=self.client_id,
                    professional_id=self.professional_id,
                    professional_user_id=self.professional_user_id,
                    servicio="Invalid source",
                    descripcion=None,
                    precio_acordado=None,
                    source_type=ContractRequest.SOURCE_BUDGET,
                    source_id=999,
                    created_from_event=ContractEvent.CREATED_FROM_PROPOSAL,
                    actor_user_id=self.client_id,
                    professional_message="Invalid",
                    budget_offer_id=999,
                )
            self.assertEqual(ContractRequest.query.count(), 0)
            self.assertEqual(ContractEvent.query.count(), 0)
            self.assertEqual(AuditLog.query.count(), 0)
            self.assertEqual(ActivityNotification.query.count(), 0)

    def test_valid_canonical_creation_keeps_exact_trace_counts(self):
        with self.app.app_context():
            contract = self._create_direct()
            event = ContractEvent.query.filter_by(contract_id=contract.id).one()
            audit = AuditLog.query.filter_by(contract_id=contract.id).one()
            notification = ActivityNotification.query.filter_by(
                entity_id=contract.id
            ).one()

            self.assertEqual(event.event_type, ContractEvent.CONTRACT_CREATED)
            self.assertEqual(event.new_status, contract.estado)
            self.assertEqual(event.sequence_no, 1)
            self.assertIsNotNone(event.correlation_id)
            self.assertEqual(audit.event_id, event.id)
            self.assertEqual(audit.correlation_id, event.correlation_id)
            self.assertEqual(notification.contract_event_id, event.id)
            self.assertEqual(notification.correlation_id, event.correlation_id)
            self._assert_direct_effects()


if __name__ == "__main__":
    unittest.main()
