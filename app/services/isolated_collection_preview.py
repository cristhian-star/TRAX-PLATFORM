"""Opt-in standalone preview factory. Never installed by create_app or a URL flag."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from decimal import Decimal
from secrets import token_hex
import re
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.models.professional import Professional
from app.models.contract_request import ContractRequest
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.payment_order_delivery_service import PaymentOrderDeliveryService


def reserved_url(result):
    return (result.provider == "fake" and result.live_mode is False
            and re.fullmatch(r"https://checkout\.example\.test/payment-orders/[0-9a-f]{64}", result.checkout_url) is not None)


class ConfirmedPreviewAdapter(InMemoryPSPPaymentOrderCreationAdapter):
    """Use the existing pre-claim hook to bind the locked amount to the review."""
    def prepare_payment_order(self, command):
        from flask import g
        from app.services.psp_payment_order_contract import PaymentOrderIdempotencyConflictError
        expected = g.get("collection_review_amount")
        if expected is None or command.amount != Decimal(expected):
            raise PaymentOrderIdempotencyConflictError("reviewed amount changed")
        return self


class IsolatedCollectionRuntime:
    def __init__(self, engine, directory, delivery):
        self.engine = engine
        self.directory = directory
        self.delivery = delivery

    def valid(self, engine):
        folder = self.directory.resolve()
        return (engine is self.engine and engine.url.drivername == "sqlite"
                and folder.parent == Path(gettempdir()).resolve()
                and folder.name.startswith("mandobra-collections-")
                and folder.is_dir() and not self.directory.is_symlink()
                and Path(engine.url.database).resolve() == folder / "preview.sqlite")


@contextmanager
def isolated_app(*, enable_simulation=False):
    if enable_simulation is not True:
        raise ValueError("Explicit isolated simulation opt-in required")
    with TemporaryDirectory(prefix="mandobra-collections-") as directory:
        folder = Path(directory).resolve()
        if folder.parent != Path(gettempdir()).resolve() or folder.is_symlink():
            raise ValueError("Invalid disposable directory")
        database = folder / "preview.sqlite"
        if database.exists():
            raise ValueError("Preview requires a new empty database")
        class PreviewConfig(TestingConfig):
            @classmethod
            def apply_runtime_config(cls, config):
                super().apply_runtime_config(config)
                config.update(SQLALCHEMY_DATABASE_URI="sqlite:///" + database.as_posix(),
                              SECRET_KEY=token_hex(32), ENV_NAME="testing", TESTING=True,
                              WTF_CSRF_ENABLED=True, E2E_DEMO_ENABLED=False,
                              ENABLE_DEV_QA_PANEL=False, REGISTER_DEV_ROUTES=False,
                              CHECKOUT_PRO_DELIVERY_ENABLED=True,
                              MERCADOPAGO_ORDER_WEBHOOK_ENABLED=False,
                              MERCADOPAGO_ORDER_RECONCILIATION_ENABLED=False,
                              PAYMENT_EFFECTS_ENABLED=False, TRANSACTIONAL_COMMISSION_ENABLED=False)
        app = create_app(config_class=PreviewConfig, initialize_schema=False)
        with app.app_context():
            engine = db.engine
            sessions = sessionmaker(bind=engine, expire_on_commit=False)
            adapter = ConfirmedPreviewAdapter()
            application = PaymentOrderApplicationService(session_factory=sessions, adapter=adapter)
            delivery = PaymentOrderDeliveryService(session_factory=sessions, application_service=application,
                                                  checkout_validator=reserved_url)
            runtime = IsolatedCollectionRuntime(engine, folder, delivery)
            if not runtime.valid(engine):
                raise ValueError("Database isolation validation failed")
            db.create_all()
            db.session.add_all([User(id=1,nombre="Profesional de prueba",email="profesional@example.test",
                password=generate_password_hash("Simulacion-local-2026!"),rol="PROFESIONAL"),
                User(id=2,nombre="Cliente sintético",email="cliente@example.test",password="disabled",rol="CLIENTE"),
                User(id=3,nombre="Otro profesional",email="otro@example.test",password="disabled",rol="PROFESIONAL")])
            db.session.flush()
            db.session.add_all([Professional(id=1,user_id=1,nombre="Profesional de prueba",servicio="Electricidad",zona="CABA"),
                                Professional(id=2,user_id=3,nombre="Otro profesional",servicio="Plomería",zona="CABA")])
            db.session.flush()
            db.session.add_all([ContractRequest(id=1,cliente_id=2,professional_id=1,professional_user_id=1,
                servicio="Revisión eléctrica — ejemplo",estado="CONFIRMADA",precio_acordado=Decimal("1250.50")),
                ContractRequest(id=2,cliente_id=2,professional_id=2,professional_user_id=3,
                servicio="Trabajo ajeno",estado="CONFIRMADA",precio_acordado=Decimal("2000.00")),
                ContractRequest(id=3,cliente_id=2,professional_id=1,professional_user_id=1,
                servicio="Trabajo sin confirmar",estado="EN_PROGRESO",precio_acordado=Decimal("3000.00"))])
            db.session.commit()
            app.extensions["isolated_collection_runtime"] = runtime
            app.extensions["payment_order_delivery_service"] = delivery
        @app.context_processor
        def simulation_context():
            from app.services.professional_collection_service import simulation_available
            return {"collection_simulation": simulation_available()}
        @app.before_request
        def enforce_isolation():
            from flask import abort
            if not runtime.valid(db.engine) or app.config.get("TESTING") is not True or app.config.get("ENV_NAME") != "testing":
                abort(503)
        @app.after_request
        def private_preview(response):
            response.headers["Cache-Control"] = "no-store, private"
            return response
        try:
            yield app
        finally:
            with app.app_context():
                db.session.remove()
                engine.dispose()
