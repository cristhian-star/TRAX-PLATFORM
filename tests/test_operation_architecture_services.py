import os
import unittest
from types import SimpleNamespace


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import create_app, db
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.user import User
from app.services.contract_service import (
    get_contract_detail_context,
    require_assigned_professional,
    require_client_owner,
)
from app.services.operation_request_service import (
    build_budget_form_data,
    build_proposal_form_data,
    validate_budget_form_data,
    validate_proposal_form_data,
)
from app.services.operation_view_service import build_budget_offer_data


class OperationRequestServiceTest(unittest.TestCase):
    def test_budget_form_defaults_match_route_behavior(self):
        form_data = build_budget_form_data({
            "categoria": " Electricidad ",
            "zona": " CABA ",
            "titulo": " Tablero ",
            "descripcion": " Revisar tablero ",
        })

        self.assertEqual(form_data["categoria"], "Electricidad")
        self.assertEqual(form_data["urgencia"], "NORMAL")
        self.assertIsNone(validate_budget_form_data(form_data))

    def test_budget_form_requires_core_fields(self):
        form_data = build_budget_form_data({"categoria": "Electricidad"})

        self.assertEqual(
            validate_budget_form_data(form_data),
            "Completa categoria, zona, titulo y descripcion.",
        )

    def test_proposal_form_requires_visible_business_fields(self):
        form_data = build_proposal_form_data({
            "industria": "Construccion",
            "categoria": "Electricidad",
        })

        self.assertEqual(
            validate_proposal_form_data(form_data),
            "Completa industria, categoria, rubro, titulo, descripcion, ubicacion y modalidad.",
        )


class OperationRouteAndOwnershipTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(
                nombre="Cliente",
                email="cliente@test.local",
                password="hash",
                rol="CLIENTE",
            )
            self.other_user = User(
                nombre="Otro",
                email="otro@test.local",
                password="hash",
                rol="CLIENTE",
            )
            self.professional_user = User(
                nombre="Profesional",
                email="pro@test.local",
                password="hash",
                rol="PROFESIONAL",
            )
            db.session.add_all([self.client_user, self.other_user, self.professional_user])
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Nexo Electrico",
                servicio="Electricidad",
                zona="CABA",
                telefono="+54 9 11 0000-1001",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.flush()
            self.contract = ContractRequest(
                cliente_id=self.client_user.id,
                professional_id=self.professional.id,
                professional_user_id=self.professional_user.id,
                servicio="Electricidad",
                estado="CREADA",
            )
            db.session.add(self.contract)
            db.session.commit()
            self.client_user_id = self.client_user.id
            self.other_user_id = self.other_user.id
            self.professional_user_id = self.professional_user.id
            self.contract_id = self.contract.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login_as(self, user_id, role="CLIENTE"):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_name"] = "Test"
            sess["user_role"] = role

    def test_contract_detail_allows_owner_client(self):
        self._login_as(self.client_user_id, "CLIENTE")

        response = self.client.get(f"/contratacion/{self.contract_id}")

        self.assertEqual(response.status_code, 200)

    def test_contract_detail_rejects_unrelated_user(self):
        self._login_as(self.other_user_id, "CLIENTE")

        response = self.client.get(f"/contratacion/{self.contract_id}")

        self.assertEqual(response.status_code, 403)

    def test_professional_can_accept_assigned_contract(self):
        self._login_as(self.professional_user_id, "PROFESIONAL")

        response = self.client.post(f"/contratacion/{self.contract_id}/aceptar")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            contract = db.session.get(ContractRequest, self.contract_id)
            self.assertEqual(contract.estado, "ACEPTADA")

    def test_invalid_contract_transition_returns_bad_request(self):
        self._login_as(self.professional_user_id, "PROFESIONAL")
        self.client.post(f"/contratacion/{self.contract_id}/aceptar")

        response = self.client.post(f"/contratacion/{self.contract_id}/rechazar")

        self.assertEqual(response.status_code, 400)

    def test_contract_ownership_helpers_accept_and_reject_expected_users(self):
        with self.app.app_context():
            contract = db.session.get(ContractRequest, self.contract_id)

            require_client_owner(contract, self.client_user_id)
            require_assigned_professional(contract, self.professional_user_id)

            with self.assertRaises(PermissionError):
                require_client_owner(contract, self.other_user_id)
            with self.assertRaises(PermissionError):
                require_assigned_professional(contract, self.other_user_id)

    def test_contract_detail_context_marks_roles(self):
        with self.app.app_context():
            contract = db.session.get(ContractRequest, self.contract_id)
            context = get_contract_detail_context(contract, self.professional_user_id)

            self.assertFalse(context["is_client"])
            self.assertTrue(context["is_professional"])


class OperationViewServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_budget_offer_view_model_masks_phone_as_digits_for_template_compatibility(self):
        professional = SimpleNamespace(
            id=1,
            user_id=None,
            telefono="+54 9 11 0000-1001",
        )
        offer = SimpleNamespace(professional=professional)

        row = build_budget_offer_data(offer)

        self.assertEqual(row["phone"]["whatsapp"], "5491100001001")
        self.assertEqual(row["badges"]["work"], True)


if __name__ == "__main__":
    unittest.main()
