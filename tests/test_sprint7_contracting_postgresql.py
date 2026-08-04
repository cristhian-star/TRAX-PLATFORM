import os
import unittest
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError


POSTGRES_TEST_URL = os.environ.get("TRAX_POSTGRES_TEST_URL")


@unittest.skipUnless(
    POSTGRES_TEST_URL,
    "TRAX_POSTGRES_TEST_URL requerido para validacion PostgreSQL",
)
class Sprint7ContractingPostgreSQLTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(POSTGRES_TEST_URL, pool_pre_ping=True)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        suffix = uuid4().hex
        with self.engine.begin() as connection:
            self.client_id = connection.execute(
                text(
                    "INSERT INTO users (nombre, email, password, rol, estado) "
                    "VALUES ('PG Client', :email, 'hash', 'CLIENTE', 'ACTIVO') "
                    "RETURNING id"
                ),
                {"email": f"pg-client-{suffix}@test.local"},
            ).scalar_one()
            self.professional_user_id = connection.execute(
                text(
                    "INSERT INTO users (nombre, email, password, rol, estado) "
                    "VALUES ('PG Professional', :email, 'hash', 'PROFESIONAL', 'ACTIVO') "
                    "RETURNING id"
                ),
                {"email": f"pg-professional-{suffix}@test.local"},
            ).scalar_one()
            self.professional_id = connection.execute(
                text(
                    "INSERT INTO professionals "
                    "(user_id, nombre, servicio, zona, perfil_completo, estado_perfil) "
                    "VALUES (:user_id, 'PG Profile', 'Electricidad', 'CABA', true, 'VERIFICADO') "
                    "RETURNING id"
                ),
                {"user_id": self.professional_user_id},
            ).scalar_one()
            self.contract_id = connection.execute(
                text(
                    "INSERT INTO contract_requests "
                    "(cliente_id, professional_id, professional_user_id, source_type, "
                    "servicio, estado, contracting_mode, version, fecha_creacion) "
                    "VALUES (:client_id, :professional_id, :professional_user_id, "
                    "'DIRECT', 'PG Contract', 'CREADA', 'EXTERNAL', 1, now()) "
                    "RETURNING id"
                ),
                {
                    "client_id": self.client_id,
                    "professional_id": self.professional_id,
                    "professional_user_id": self.professional_user_id,
                },
            ).scalar_one()

    def tearDown(self):
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM activity_notifications "
                    "WHERE entity_type = 'ContractRequest' AND entity_id = :contract_id"
                ),
                {"contract_id": self.contract_id},
            )
            connection.execute(
                text("DELETE FROM audit_logs WHERE contract_id = :contract_id"),
                {"contract_id": self.contract_id},
            )
            connection.execute(
                text("DELETE FROM contract_events WHERE contract_id = :contract_id"),
                {"contract_id": self.contract_id},
            )
            connection.execute(
                text(
                    "DELETE FROM operation_commands "
                    "WHERE actor_user_id IN (:client_id, :professional_user_id) "
                    "OR (result_entity_type = 'ContractRequest' "
                    "AND result_entity_id = :contract_id)"
                ),
                {
                    "contract_id": self.contract_id,
                    "client_id": self.client_id,
                    "professional_user_id": self.professional_user_id,
                },
            )
            connection.execute(
                text("DELETE FROM contract_requests WHERE id = :contract_id"),
                {"contract_id": self.contract_id},
            )
            connection.execute(
                text("DELETE FROM professionals WHERE id = :professional_id"),
                {"professional_id": self.professional_id},
            )
            connection.execute(
                text("DELETE FROM users WHERE id IN (:client_id, :professional_user_id)"),
                {
                    "client_id": self.client_id,
                    "professional_user_id": self.professional_user_id,
                },
            )

    def _assert_contract_check_rejects(self, column, value):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        f"UPDATE contract_requests SET {column} = :value "
                        "WHERE id = :contract_id"
                    ),
                    {"value": value, "contract_id": self.contract_id},
                )

    def test_contract_checks_are_enforced_physically(self):
        self._assert_contract_check_rejects("contracting_mode", "PROTECTED")
        self._assert_contract_check_rejects("version", 0)
        self._assert_contract_check_rejects("estado", "CERRADA")

    def test_event_sequence_and_idempotency_are_unique(self):
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO contract_events "
                    "(contract_id, event_type, actor_user_id, sequence_no, "
                    "idempotency_key, created_at) "
                    "VALUES (:contract_id, 'CONTRACT_CREATED', :actor_id, 1, "
                    "'pg-event-key', now())"
                ),
                {
                    "contract_id": self.contract_id,
                    "actor_id": self.client_id,
                },
            )

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO contract_events "
                        "(contract_id, event_type, actor_user_id, sequence_no, created_at) "
                        "VALUES (:contract_id, 'CONTRACT_ACCEPTED', :actor_id, 1, now())"
                    ),
                    {
                        "contract_id": self.contract_id,
                        "actor_id": self.professional_user_id,
                    },
                )

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO contract_events "
                        "(contract_id, event_type, actor_user_id, sequence_no, "
                        "idempotency_key, created_at) "
                        "VALUES (:contract_id, 'CONTRACT_ACCEPTED', :actor_id, 2, "
                        "'pg-event-key', now())"
                    ),
                    {
                        "contract_id": self.contract_id,
                        "actor_id": self.professional_user_id,
                    },
                )

    def test_select_for_update_prevents_concurrent_overwrite(self):
        first = self.engine.connect()
        second = self.engine.connect()
        first_transaction = first.begin()
        try:
            first.execute(
                text(
                    "SELECT id FROM contract_requests "
                    "WHERE id = :contract_id FOR UPDATE"
                ),
                {"contract_id": self.contract_id},
            )
            second.execute(text("SET lock_timeout = '250ms'"))
            with self.assertRaises(OperationalError):
                second.execute(
                    text(
                        "UPDATE contract_requests SET version = version + 1 "
                        "WHERE id = :contract_id"
                    ),
                    {"contract_id": self.contract_id},
                )
        finally:
            second.rollback()
            first_transaction.rollback()
            second.close()
            first.close()

    def test_command_notification_uniqueness_and_notification_fk(self):
        with self.engine.begin() as connection:
            event_id = connection.execute(
                text(
                    "INSERT INTO contract_events "
                    "(contract_id, event_type, actor_user_id, sequence_no, created_at) "
                    "VALUES (:contract_id, 'CONTRACT_CREATED', :actor_id, 1, now()) "
                    "RETURNING id"
                ),
                {
                    "contract_id": self.contract_id,
                    "actor_id": self.client_id,
                },
            ).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO operation_commands "
                    "(actor_user_id, operation, idempotency_key, payload_hash, status, "
                    "correlation_id, created_at) "
                    "VALUES (:actor_id, 'ACCEPT_CONTRACT', 'pg-command-key', :payload_hash, "
                    "'PROCESSING', '00000000-0000-0000-0000-000000000010', now())"
                ),
                {"actor_id": self.professional_user_id, "payload_hash": "0" * 64},
            )
            connection.execute(
                text(
                    "INSERT INTO activity_notifications "
                    "(user_id, actor_user_id, contract_event_id, template_key, channel, "
                    "delivery_status, attempt_count, tipo, categoria, titulo, mensaje, "
                    "entity_type, entity_id, prioridad, requiere_accion, leida, created_at) "
                    "VALUES (:recipient_id, :actor_id, :event_id, 'CONTRACT_CREATED', "
                    "'INTERNAL', 'DELIVERED', 0, 'CONTRACT_CREATED', 'CONTRATACIONES', "
                    "'Contrato', 'Contrato creado', 'ContractRequest', :contract_id, "
                    "'INFO', false, false, now())"
                ),
                {
                    "recipient_id": self.professional_user_id,
                    "actor_id": self.client_id,
                    "event_id": event_id,
                    "contract_id": self.contract_id,
                },
            )

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO operation_commands "
                        "(actor_user_id, operation, idempotency_key, payload_hash, status, "
                        "correlation_id, created_at) "
                        "VALUES (:actor_id, 'ACCEPT_CONTRACT', 'pg-command-key', "
                        ":payload_hash, 'PROCESSING', "
                        "'00000000-0000-0000-0000-000000000011', now())"
                    ),
                    {"actor_id": self.professional_user_id, "payload_hash": "1" * 64},
                )

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO activity_notifications "
                        "(user_id, actor_user_id, contract_event_id, template_key, channel, "
                        "delivery_status, attempt_count, tipo, categoria, titulo, mensaje, "
                        "entity_type, entity_id, prioridad, requiere_accion, leida, created_at) "
                        "SELECT user_id, actor_user_id, contract_event_id, template_key, "
                        "channel, delivery_status, attempt_count, tipo, categoria, titulo, "
                        "mensaje, entity_type, entity_id, prioridad, requiere_accion, leida, "
                        "now() FROM activity_notifications "
                        "WHERE contract_event_id = :event_id"
                    ),
                    {"event_id": event_id},
                )

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE activity_notifications SET contract_event_id = 999999999 "
                        "WHERE contract_event_id = :event_id"
                    ),
                    {"event_id": event_id},
                )


if __name__ == "__main__":
    unittest.main()
