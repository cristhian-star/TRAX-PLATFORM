import os
import re
import unittest


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
from app.services.contract_service import (
    IdempotencyConflictError,
    create_contract,
)


class Sprint7ContractingP0Iteration1Test(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.http = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.client_user = User(
                nombre="Cliente",
                email="p0-client@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            self.other_client = User(
                nombre="Otro cliente",
                email="p0-other-client@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            self.suspended_client = User(
                nombre="Cliente suspendido",
                email="p0-suspended@test.local",
                password="hash",
                rol="CLIENTE",
                estado="SUSPENDIDO",
            )
            self.professional_user = User(
                nombre="Profesional",
                email="p0-professional@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all(
                [
                    self.client_user,
                    self.other_client,
                    self.suspended_client,
                    self.professional_user,
                ]
            )
            db.session.flush()
            self.professional = Professional(
                user_id=self.professional_user.id,
                nombre="Profesional P0",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(self.professional)
            db.session.commit()
            self.client_id = self.client_user.id
            self.other_client_id = self.other_client.id
            self.suspended_client_id = self.suspended_client.id
            self.professional_user_id = self.professional_user.id
            self.professional_id = self.professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _kwargs(self, **overrides):
        values = {
            "cliente_id": self.client_id,
            "professional_id": self.professional_id,
            "professional_user_id": self.professional_user_id,
            "servicio": "Instalacion P0",
            "actor_user_id": self.client_id,
            "idempotency_key": "direct-create-p0-0001",
        }
        values.update(overrides)
        return values

    def _assert_no_effects(self):
        self.assertEqual(ContractRequest.query.count(), 0)
        self.assertEqual(OperationCommand.query.count(), 0)
        self.assertEqual(ContractEvent.query.count(), 0)
        self.assertEqual(AuditLog.query.count(), 0)
        self.assertEqual(ActivityNotification.query.count(), 0)

    def _assert_single_creation_effects(self):
        self.assertEqual(ContractRequest.query.count(), 1)
        self.assertEqual(OperationCommand.query.count(), 1)
        self.assertEqual(ContractEvent.query.count(), 1)
        self.assertEqual(AuditLog.query.count(), 1)
        self.assertEqual(ActivityNotification.query.count(), 1)

    def _login_client(self):
        with self.http.session_transaction() as session:
            session["user_id"] = self.client_id
            session["user_role"] = "CLIENTE"
            session["user_name"] = "Cliente"

    def _post_data(self, key_marker=True, **overrides):
        values = {
            "professional_id": str(self.professional_id),
            "servicio": "Instalacion P0",
        }
        if key_marker is not False:
            values["idempotency_key"] = key_marker
        values.update(overrides)
        return values

    def test_actor_is_required_and_never_inferred_from_client(self):
        with self.app.app_context():
            with self.assertRaises(TypeError):
                values = self._kwargs()
                values.pop("actor_user_id")
                create_contract(**values)
            with self.assertRaises(PermissionError):
                create_contract(**self._kwargs(actor_user_id=None))
            self._assert_no_effects()

    def test_nonexistent_suspended_wrong_role_and_non_owner_actors_are_rejected(self):
        with self.app.app_context():
            cases = (
                {"actor_user_id": 999999},
                {
                    "actor_user_id": self.suspended_client_id,
                    "cliente_id": self.suspended_client_id,
                },
                {
                    "actor_user_id": self.professional_user_id,
                    "cliente_id": self.professional_user_id,
                },
                {"actor_user_id": self.other_client_id},
            )
            for index, overrides in enumerate(cases):
                with self.subTest(case=index), self.assertRaises(PermissionError):
                    create_contract(
                        **self._kwargs(
                            idempotency_key=f"direct-actor-negative-{index:04d}",
                            **overrides,
                        )
                    )
            self._assert_no_effects()

    def test_authorization_is_rechecked_before_idempotent_replay(self):
        with self.app.app_context():
            contract = create_contract(**self._kwargs())
            actor = db.session.get(User, self.client_id)
            actor.estado = "SUSPENDIDO"
            db.session.commit()

            with self.assertRaises(PermissionError):
                create_contract(**self._kwargs())

            self.assertEqual(db.session.get(ContractRequest, contract.id).id, contract.id)
            self._assert_single_creation_effects()

    def test_service_rejects_missing_empty_and_invalid_idempotency_keys(self):
        with self.app.app_context():
            values_without_key = self._kwargs()
            values_without_key.pop("idempotency_key")
            with self.assertRaises(TypeError):
                create_contract(**values_without_key)

            invalid_values = (
                None,
                "",
                "short",
                " invalid-key-0001",
                "invalid key with spaces",
                "invalid/key/000001",
                "x" * 161,
            )
            for invalid_key in invalid_values:
                with self.subTest(key=invalid_key), self.assertRaises(ValueError):
                    create_contract(**self._kwargs(idempotency_key=invalid_key))
            self._assert_no_effects()

    def test_service_replay_has_exactly_one_set_of_effects(self):
        with self.app.app_context():
            first = create_contract(**self._kwargs())
            second = create_contract(**self._kwargs())
            self.assertEqual(first.id, second.id)
            self._assert_single_creation_effects()

    def test_service_same_key_with_different_payload_conflicts_without_partial_effects(self):
        with self.app.app_context():
            create_contract(**self._kwargs())
            with self.assertRaises(IdempotencyConflictError):
                create_contract(
                    **self._kwargs(servicio="Otro alcance contractual")
                )
            self._assert_single_creation_effects()

    def test_http_post_rejects_missing_empty_and_invalid_keys(self):
        self._login_client()
        cases = (
            self._post_data(key_marker=False),
            self._post_data(key_marker=""),
            self._post_data(key_marker="invalid key"),
        )
        for data in cases:
            with self.subTest(data=data):
                response = self.http.post("/contratacion/nueva", data=data)
                self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            self._assert_no_effects()

    def test_form_key_is_stable_for_two_sequential_posts(self):
        self._login_client()
        form_response = self.http.get("/contratacion/nueva")
        self.assertEqual(form_response.status_code, 200)
        match = re.search(
            rb'name="idempotency_key" value="([^"]+)"',
            form_response.data,
        )
        self.assertIsNotNone(match)
        idempotency_key = match.group(1).decode("ascii")

        data = self._post_data(key_marker=idempotency_key)
        first = self.http.post("/contratacion/nueva", data=data)
        second = self.http.post("/contratacion/nueva", data=data)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(first.headers["Location"], second.headers["Location"])

        with self.app.app_context():
            self._assert_single_creation_effects()

    def test_http_header_key_supports_replay_and_payload_conflict(self):
        self._login_client()
        headers = {"Idempotency-Key": "direct-header-p0-0001"}
        data = self._post_data(key_marker=False)

        first = self.http.post("/contratacion/nueva", data=data, headers=headers)
        replay = self.http.post("/contratacion/nueva", data=data, headers=headers)
        conflict = self.http.post(
            "/contratacion/nueva",
            data=self._post_data(
                key_marker=False,
                servicio="Payload HTTP diferente",
            ),
            headers=headers,
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(replay.status_code, 302)
        self.assertEqual(conflict.status_code, 409)
        with self.app.app_context():
            self._assert_single_creation_effects()


if __name__ == "__main__":
    unittest.main()
