from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import tempfile
import unittest

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from app.services.payment_order_application_service import PaymentOrderApplicationService
from tests.test_payment_order_application import seed_contract


class PaymentOrderApplicationMigrationTest(unittest.TestCase):
    def test_upgrade_downgrade_upgrade_preserves_legacy_and_payment_orders(self):
        with tempfile.TemporaryDirectory() as temporary:
            url = f"sqlite:///{(Path(temporary) / 'migration.db').as_posix()}"
            previous = os.environ.get("DATABASE_URL")
            os.environ["DATABASE_URL"] = url
            engine = sa.create_engine(url)
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            try:
                scripts = ScriptDirectory.from_config(config)
                heads = scripts.get_heads()
                self.assertEqual(heads, ["20260917_01"])
                self.assertEqual(scripts.get_revision(heads[0]).down_revision, "20260916_01")
                command.upgrade(config, "20260916_01")
                with engine.begin() as connection:
                    connection.execute(sa.text(
                        "INSERT INTO payment_obligations (internal_reference,amount,currency,created_at) "
                        "VALUES ('legacy',1,'ARS','2026-09-17 12:00:00')"
                    ))
                command.upgrade(config, "head")
                Session = sessionmaker(bind=engine, expire_on_commit=False)
                actor, _, _, _, contract = seed_contract(Session)
                service = PaymentOrderApplicationService(
                    session_factory=Session,
                    adapter=InMemoryPSPPaymentOrderCreationAdapter(),
                    clock=lambda: datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc),
                )
                result = service.create_order(actor_user_id=actor, contract_request_id=contract)
                with Session() as session:
                    self.assertIsNone(session.query(PaymentObligation).filter_by(internal_reference="legacy").one().contract_request_id)
                    self.assertEqual(session.query(PaymentOrder).one().local_order_id, result.local_order_id)
                with self.assertRaises(IntegrityError):
                    with Session.begin() as session:
                        session.add(PaymentObligation(
                            contract_request_id=contract, internal_reference="duplicate",
                            amount=Decimal("1"), currency="ARS",
                        ))
                        session.flush()
                with engine.connect() as connection:
                    connection.execute(sa.text("PRAGMA foreign_keys=ON"))
                    connection.commit()
                    with self.assertRaises(IntegrityError):
                        connection.execute(sa.text(
                            "INSERT INTO payment_obligations "
                            "(contract_request_id,internal_reference,amount,currency,created_at) "
                            "VALUES (999999,'invalid-fk',1,'ARS','2026-09-17 12:00:00')"
                        ))
                    connection.rollback()
                    connection.execute(sa.text("PRAGMA foreign_keys=OFF"))
                    connection.commit()
                command.downgrade(config, "20260916_01")
                self.assertNotIn("payment_order_reservations", sa.inspect(engine).get_table_names())
                self.assertNotIn("contract_request_id", {
                    item["name"] for item in sa.inspect(engine).get_columns("payment_obligations")
                })
                with engine.connect() as connection:
                    self.assertEqual(connection.execute(sa.text("SELECT count(*) FROM payment_orders")).scalar_one(), 1)
                    self.assertEqual(connection.execute(sa.text("SELECT count(*) FROM payment_obligations")).scalar_one(), 2)
                command.upgrade(config, "head")
                with engine.connect() as connection:
                    self.assertEqual(connection.execute(sa.text(
                        "SELECT count(*) FROM payment_obligations WHERE contract_request_id IS NULL"
                    )).scalar_one(), 2)
            finally:
                engine.dispose()
                if previous is None:
                    os.environ.pop("DATABASE_URL", None)
                else:
                    os.environ["DATABASE_URL"] = previous


if __name__ == "__main__":
    unittest.main()
