import os
import unittest


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.user import User
from app.services.contract_service import (
    accept_contract,
    confirm_contract,
    create_contract,
    reject_contract,
    start_contract,
)
from app.services.contracting_core_service import create_contract_event


class Sprint7ContractingCoreTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(nombre="Cliente", email="cliente-core@test.local", password="hash", rol="CLIENTE")
            self.professional_user = User(nombre="Pro", email="pro-core@test.local", password="hash", rol="PROFESIONAL")
            db.session.add_all([self.client_user, self.professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Nexo Core",
                servicio="Electricidad",
                zona="CABA",
                telefono="+5491100000000",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.commit()
            self.client_id = self.client_user.id
            self.professional_user_id = self.professional_user.id
            self.professional_id = self.professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self, user_id, role):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id
            session["user_role"] = role
            session["user_name"] = "Test"

    def test_direct_contract_keeps_working_and_records_source_event_and_audit(self):
        with self.app.app_context():
            contract = create_contract(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                servicio="Instalacion",
            )

            self.assertEqual(contract.source_type, ContractRequest.SOURCE_DIRECT)
            self.assertEqual(contract.estado, "CREADA")
            self.assertEqual(ContractEvent.query.filter_by(contract_id=contract.id).count(), 1)
            self.assertEqual(AuditLog.query.filter_by(action=ContractEvent.CONTRACT_CREATED).count(), 1)

    def test_professional_must_accept_contract_after_creation_and_invalid_transition_still_fails(self):
        with self.app.app_context():
            contract = create_contract(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                servicio="Instalacion",
            )
            contract_id = contract.id
            self.assertEqual(contract.estado, "CREADA")

            accepted = accept_contract(contract_id, self.professional_user_id)
            self.assertEqual(accepted.estado, "ACEPTADA")
            self.assertEqual(
                ContractEvent.query.filter_by(
                    contract_id=contract_id,
                    event_type=ContractEvent.CONTRACT_ACCEPTED,
                ).count(),
                1,
            )
            event = ContractEvent.query.filter_by(
                contract_id=contract_id,
                event_type=ContractEvent.CONTRACT_ACCEPTED,
            ).one()
            audit_log = AuditLog.query.filter_by(
                contract_id=contract_id,
                action=ContractEvent.CONTRACT_ACCEPTED,
            ).one()
            self.assertEqual(audit_log.event_id, event.id)
            self.assertEqual(audit_log.entity_type, "ContractRequest")
            with self.assertRaises(ValueError):
                reject_contract(contract_id, self.professional_user_id)

    def test_direct_contract_route_still_creates_contract(self):
        self._login(self.client_id, "CLIENTE")

        response = self.client.post(
            "/contratacion/nueva",
            data={
                "professional_id": str(self.professional_id),
                "servicio": "Instalacion",
            },
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            contract = ContractRequest.query.one()
            self.assertEqual(contract.source_type, ContractRequest.SOURCE_DIRECT)

    def test_contract_transitions_require_authorized_actor(self):
        with self.app.app_context():
            intruder = User(nombre="Ajeno", email="intruder-core@test.local", password="hash", rol="PROFESIONAL")
            db.session.add(intruder)
            db.session.commit()
            contract = create_contract(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                servicio="Instalacion",
            )

            with self.assertRaises(PermissionError):
                accept_contract(contract.id, intruder.id)
            with self.assertRaises(PermissionError):
                start_contract(contract.id, intruder.id)
            with self.assertRaises(PermissionError):
                confirm_contract(contract.id, intruder.id)
            with self.assertRaises(PermissionError):
                start_contract(contract.id, None)

            self.assertEqual(ContractRequest.query.get(contract.id).estado, "CREADA")

    def test_contract_event_metadata_uses_closed_non_sensitive_schema(self):
        with self.app.app_context():
            contract = create_contract(
                cliente_id=self.client_id,
                professional_id=self.professional_id,
                professional_user_id=self.professional_user_id,
                servicio="Instalacion",
            )
            event = create_contract_event(
                contract,
                ContractEvent.CONTRACT_STARTED,
                actor_user_id=self.professional_user_id,
                metadata_json={
                    "source_type": ContractRequest.SOURCE_DIRECT,
                    "token": "secreto",
                    "nested": {"password": "no"},
                },
            )

            self.assertEqual(event.metadata_json, {"source_type": ContractRequest.SOURCE_DIRECT})


if __name__ == "__main__":
    unittest.main()
