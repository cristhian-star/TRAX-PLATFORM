import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.exc import IntegrityError


ROOT = Path(__file__).resolve().parents[1]


class PaymentOrderPersistenceMigrationTest(unittest.TestCase):
    def test_upgrade_downgrade_upgrade_preserves_existing_rows_and_constraints(self):
        with tempfile.TemporaryDirectory() as temporary:
            url = f"sqlite:///{(Path(temporary) / 'payment-orders.db').as_posix()}"
            previous = os.environ.get("DATABASE_URL")
            os.environ["DATABASE_URL"] = url
            engine = sa.create_engine(url)
            config = Config(str(ROOT / "alembic.ini"))
            try:
                script = ScriptDirectory.from_config(config)
                self.assertEqual(script.get_heads(), ["20260916_01"])
                command.upgrade(config, "20260911_02")
                with engine.begin() as connection:
                    user_id = connection.execute(sa.text(
                        "INSERT INTO users (nombre,email,password,rol,estado) "
                        "VALUES ('Pro','pro@example.test','hash','PROFESIONAL','ACTIVO') "
                        "RETURNING id"
                    )).scalar_one()
                    professional_id = connection.execute(sa.text(
                        "INSERT INTO professionals (user_id,nombre,servicio,zona,"
                        "whatsapp_contact_preference,estado_perfil,perfil_completo) "
                        "VALUES (:user_id,'Pro','Service','CABA','AUTO','INCOMPLETO',0) "
                        "RETURNING id"
                    ), {"user_id": user_id}).scalar_one()
                    obligation_id = connection.execute(sa.text(
                        "INSERT INTO payment_obligations "
                        "(internal_reference,amount,currency,created_at) "
                        "VALUES ('obligation-legacy',1250.50,'ARS','2026-09-16 12:00:00') "
                        "RETURNING id"
                    )).scalar_one()

                command.upgrade(config, "head")
                self.assertIn("payment_orders", sa.inspect(engine).get_table_names())
                insert_order = sa.text(
                    "INSERT INTO payment_orders "
                    "(obligation_id,professional_id,local_order_id,external_reference,"
                    "idempotency_key,amount,currency,concept,provider,live_mode,"
                    "external_order_id,checkout_url,status,created_at,expires_at,"
                    "closed_at,cancelled_at,updated_at) VALUES "
                    "(:obligation_id,:professional_id,:local_order_id,:external_reference,"
                    ":idempotency_key,:amount,:currency,'Service','fake',0,"
                    ":external_order_id,'https://checkout.example.test/order',:status,"
                    "'2026-09-16 12:00:00',:expires_at,:closed_at,:cancelled_at,"
                    "'2026-09-16 12:00:00')"
                )
                with engine.begin() as connection:
                    connection.execute(insert_order, {
                        "obligation_id": obligation_id,
                        "professional_id": professional_id,
                        "local_order_id": "local-valid",
                        "external_reference": "external-valid",
                        "idempotency_key": "idempotency-key-valid",
                        "amount": 1250.50,
                        "currency": "ARS",
                        "external_order_id": "provider-valid",
                        "status": "CANCELLED",
                        "expires_at": "2026-09-19 12:00:00",
                        "closed_at": "2026-09-16 13:00:00",
                        "cancelled_at": "2026-09-16 13:00:00",
                    })

                invalid_cases = (
                    {"status": "ACTIVE", "closed_at": "2026-09-16 13:00:00", "cancelled_at": None},
                    {"status": "ACTIVE", "closed_at": None, "cancelled_at": "2026-09-16 13:00:00"},
                    {"status": "EXPIRED", "closed_at": None, "cancelled_at": None},
                    {"status": "EXPIRED", "closed_at": "2026-09-19 12:00:00", "cancelled_at": "2026-09-16 13:00:00"},
                    {"status": "CANCELLED", "closed_at": None, "cancelled_at": "2026-09-16 13:00:00"},
                    {"status": "CANCELLED", "closed_at": "2026-09-16 13:00:00", "cancelled_at": None},
                    {"status": "CANCELLED", "closed_at": "2026-09-16 13:00:00", "cancelled_at": "2026-09-16 14:00:00"},
                    {"amount": 0},
                    {"amount": 1.001},
                    {"currency": "USD"},
                    {"expires_at": "2026-09-19 11:00:00"},
                )
                for index, changes in enumerate(invalid_cases):
                    values = {
                            "obligation_id": obligation_id,
                            "professional_id": professional_id,
                            "local_order_id": f"local-invalid-{index}",
                            "external_reference": f"external-invalid-{index}",
                            "idempotency_key": f"idempotency-key-invalid-{index}",
                            "amount": 1250.50,
                            "currency": "ARS",
                            "external_order_id": f"provider-invalid-{index}",
                            "status": "CANCELLED",
                            "expires_at": "2026-09-19 12:00:00",
                            "closed_at": "2026-09-16 13:00:00",
                            "cancelled_at": "2026-09-16 13:00:00",
                    }
                    values.update(changes)
                    with self.subTest(changes=changes):
                        with self.assertRaises(IntegrityError):
                            with engine.begin() as connection:
                                connection.execute(insert_order, values)

                command.downgrade(config, "20260911_02")
                inspector = sa.inspect(engine)
                self.assertNotIn("payment_orders", inspector.get_table_names())
                with engine.connect() as connection:
                    self.assertEqual(
                        connection.execute(sa.text(
                            "SELECT internal_reference FROM payment_obligations"
                        )).scalar_one(),
                        "obligation-legacy",
                    )
                command.upgrade(config, "head")
                self.assertIn("payment_orders", sa.inspect(engine).get_table_names())
            finally:
                engine.dispose()
                if previous is None:
                    os.environ.pop("DATABASE_URL", None)
                else:
                    os.environ["DATABASE_URL"] = previous


if __name__ == "__main__":
    unittest.main()
