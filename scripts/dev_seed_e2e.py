"""Explicit idempotent fixture; never run during normal Compose startup."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app, db
from sqlalchemy import text
from app.models.user import User
from app.models.professional import Professional
from app.models.contract_request import ContractRequest
from app.services.contract_service import create_contract
from app.services.simulated_mercadopago_demo import DEMO_CONTRACT_KEY, enabled
from scripts.dev_seed_professionals import seed_professionals


def seed_scenario():
    seed_professionals()
    client = User.query.filter_by(email="cliente.demo@trax.local").one()
    professional_user = User.query.filter_by(email="plomeria.work@demo.trax.local").one()
    professional = Professional.query.filter_by(user_id=professional_user.id).one()
    contract = create_contract(
        cliente_id=client.id, professional_id=professional.id,
        professional_user_id=professional_user.id, servicio="Plomería simulada",
        descripcion=DEMO_CONTRACT_KEY, precio_acordado="1000.00",
        actor_user_id=client.id, idempotency_key=DEMO_CONTRACT_KEY,
    )
    assert ContractRequest.query.filter_by(descripcion=DEMO_CONTRACT_KEY).count() == 1
    return contract.id


def main():
    app = create_app()
    if not enabled(app.config):
        raise SystemExit("E2E demo fixture unavailable")
    with app.app_context():
        if db.session.execute(text("select current_database()")).scalar() != "mandobra_stabilization_db":
            raise SystemExit("Unexpected database")
        contract_id = seed_scenario()
        print(f"SIMULACIÓN: contrato {contract_id}")


if __name__ == "__main__":
    main()
