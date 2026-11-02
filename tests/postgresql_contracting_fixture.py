"""Shared disposable PostgreSQL preparation, deliberately without test cases."""
import os
from pathlib import Path
from uuid import uuid4
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.budget_offer import BudgetOffer
from app.models.budget_request import BudgetRequest
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.proposal_application import ProposalApplication
from app.models.proposal_request import ProposalRequest
from app.models.user import User
from tests.alembic_head_validation import assert_database_at_repository_head

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PostgreSQLContractingFixture:
    """Consumers declare OWNER_ROLE and inherit unittest.TestCase themselves."""
    @classmethod
    def setUpClass(cls):
        postgres_url = os.environ.get("TRAX_POSTGRES_TEST_URL")
        allow_reset = os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET") == "1"
        if not postgres_url:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_URL es obligatorio para la suite PostgreSQL E2E"
            )
        url = make_url(postgres_url)
        if url.get_backend_name() not in ("postgresql", "postgres"):
            raise RuntimeError("TRAX_POSTGRES_TEST_URL debe apuntar a PostgreSQL")
        if not allow_reset:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_ALLOW_RESET=1 es obligatorio: la base sera truncada"
            )

        os.environ["DATABASE_URL"] = postgres_url
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.upgrade(config, "head")
        cls.app = create_app(initialize_schema=False)
        cls.app.config.update(TESTING=True)
        with cls.app.app_context():
            revisions = db.session.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalars().all()
            assert_database_at_repository_head(config, revisions)
            if db.engine.dialect.name != "postgresql":
                raise RuntimeError("La suite E2E no esta ejecutando PostgreSQL")


    def _truncate_database(self):
        with self.app.app_context():
            table_names = [
                table.name
                for table in reversed(db.metadata.sorted_tables)
                if table.name != "alembic_version"
            ]
            quoted = ", ".join(
                db.engine.dialect.identifier_preparer.quote(table)
                for table in table_names
            )
            db.session.execute(
                sa.text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
            )
            db.session.commit()


    def setUp(self):
        self._truncate_database()
        with self.app.app_context():
            suffix = uuid4().hex
            owner = User(
                nombre="PG Owner",
                email=f"pg-owner-{suffix}@test.local",
                password="hash",
                rol=self.OWNER_ROLE,
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="PG Professional",
                email=f"pg-professional-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all([owner, professional_user])
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="PG Professional",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(professional)
            db.session.flush()
            budget = BudgetRequest(
                cliente_id=owner.id,
                categoria="Electricidad",
                titulo="PG Budget",
                descripcion="PG budget source",
                zona="CABA",
                estado="ADJUDICADA",
            )
            proposal = ProposalRequest(
                cliente_id=owner.id,
                owner_user_id=owner.id,
                categoria="Construccion",
                titulo="PG Proposal",
                descripcion="PG proposal source",
                estado="CERRADA",
                hiring_mode="SINGLE",
            )
            db.session.add_all([budget, proposal])
            db.session.flush()
            offer = BudgetOffer(
                budget_request_id=budget.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                monto=100,
                mensaje="Oferta PG",
                plazo_estimado="1 dia",
                estado="ADJUDICADO",
            )
            application = ProposalApplication(
                proposal_id=proposal.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                mensaje="Postulacion PG",
                pretension_economica=200,
                estado="ACEPTADA",
            )
            db.session.add_all([offer, application])
            db.session.commit()
            self.assertEqual(owner.rol, self.OWNER_ROLE)
            print(f"{self._testMethodName}: persisted owner role={owner.rol}", flush=True)
            self.owner_id = owner.id
            self.professional_user_id = professional_user.id
            self.professional_id = professional.id
            self.offer_id = offer.id
            self.application_id = application.id


    def tearDown(self):
        self._truncate_database()


    def _counts(self):
        return {
            "contracts": ContractRequest.query.count(),
            "commands": OperationCommand.query.count(),
            "events": ContractEvent.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
        }

