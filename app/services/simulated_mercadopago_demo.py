"""Disposable, explicitly gated local scenario. Never contacts a PSP."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url

from app import db
from app.models.contract_request import ContractRequest
from app.models.payment_order import PaymentOrder
from app.models.psp_event import PSPEventRecord
from app.models.payment_order_reconciliation import (
    PaymentOrderReconciliationEvidence as Evidence,
    PaymentOrderReconciliationWork as Work,
)
from app.models.payment_effect import (
    PaymentEffectDecision as Decision, TransactionalCommission as Commission,
    TransactionalCreditGrant as Grant,
)
from app.services.mercadopago_order_query_adapter import parse_order_snapshot
from app.services.payment_effect_service import CreditPolicy, EffectiveCommission, PaymentEffectService
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.payment_order_delivery_service import PaymentOrderDeliveryService
from app.services.payment_order_reconciliation_service import (
    PaymentOrderReconciliationProcessor, receive_order_event,
)
from app.services.psp_event_contract import PSPEvent
from app.services.psp_payment_order_contract import (
    PaymentOrderCreationResult, validate_payment_order_creation_result,
)


DEMO_PROJECT = "mandobra_stabilization"
DEMO_ORIGIN = "http://127.0.0.1:5050"
DEMO_POLICY = CreditPolicy("simulated-pro-100-v1", Decimal("100.00"), "ARS")
DEMO_COMMISSION = Decimal("100.00")
DEMO_CONTRACT_KEY = "e2e-demo-punto-agua-v1"


def enabled(config):
    try:
        database = make_url(config.get("SQLALCHEMY_DATABASE_URI", "")).database
    except Exception:
        database = None
    return (
        config.get("ENV_NAME") in ("development", "testing")
        and config.get("ENABLE_DEV_QA_PANEL") is True
        and config.get("E2E_DEMO_ENABLED") is True
        and config.get("E2E_DEMO_PROJECT") == DEMO_PROJECT
        and config.get("E2E_DEMO_ORIGIN") == DEMO_ORIGIN
        and database == "mandobra_stabilization_db"
        and Path("/.dockerenv").exists()
    )


def _sessions():
    return sessionmaker(bind=db.engine, expire_on_commit=False)


class SimulatedMercadoPagoOrderCreationAdapter:
    @property
    def checkout_url_policy(self):
        return _local_checkout

    def create_payment_order(self, command):
        digest = sha256(command.idempotency_key.encode("ascii")).hexdigest()[:32]
        result = PaymentOrderCreationResult(
            local_order_id=command.local_order_id,
            obligation_reference=command.obligation_reference,
            external_reference=command.external_reference,
            amount=command.amount, currency=command.currency, concept=command.concept,
            idempotency_key=command.idempotency_key,
            created_at=command.created_at, expires_at=command.expires_at,
            external_order_id=f"sim-{digest}",
            checkout_url=f"{DEMO_ORIGIN}/dev/e2e/checkout/sim-{digest}",
            provider="mercadopago", live_mode=False,
            checkout_url_policy=_local_checkout,
        )
        return validate_payment_order_creation_result(command, result)


def _local_checkout(result):
    return (
        result.provider == "mercadopago" and result.live_mode is False
        and result.external_order_id.startswith("sim-")
        and result.checkout_url == f"{DEMO_ORIGIN}/dev/e2e/checkout/{result.external_order_id}"
    )


def delivery():
    factory = _sessions()
    return PaymentOrderDeliveryService(
        session_factory=factory,
        application_service=PaymentOrderApplicationService(
            session_factory=factory, adapter=SimulatedMercadoPagoOrderCreationAdapter(),
        ),
        checkout_validator=_local_checkout,
    )


class SimulatedMercadoPagoOrderQueryAdapter:
    def query_order(self, context):
        if not context.external_order_id.startswith("sim-") or context.live_mode is not False:
            raise ValueError("not a simulated order")
        now = datetime.now(timezone.utc)
        created = min(now - timedelta(seconds=1), context.expires_at.replace(tzinfo=timezone.utc) - timedelta(seconds=2))
        payload = {
            "id": context.external_order_id,
            "external_reference": context.external_reference,
            "user_id": "424242", "type": "online", "processing_mode": "manual",
            "currency": "ARS", "live_mode": False,
            "total_amount": format(context.amount, ".2f"),
            "total_paid_amount": format(context.amount, ".2f"),
            "status": "processed", "status_detail": "accredited",
            "created_date": created.isoformat(),
            "last_updated_date": now.isoformat(),
            "transactions": {"payments": [{
                "id": "sim-payment-" + context.external_order_id[4:],
                "amount": format(context.amount, ".2f"),
                "paid_amount": format(context.amount, ".2f"),
                "status": "processed", "status_detail": "accredited",
            }], "refunds": [], "chargebacks": []},
        }
        return parse_order_snapshot(payload, context, "424242")


def _simulated_timing(snapshot, context):
    return ("BEFORE_LOCAL_EXPIRY" if snapshot.remote_created_at < snapshot.remote_updated_at < context.expires_at
            and snapshot.content["status"] == "processed" else "UNKNOWN")


def _commission_proof(evidence_id):
    with _sessions()() as session:
        evidence = session.get(Evidence, evidence_id)
        if evidence is None or evidence.timing != "BEFORE_LOCAL_EXPIRY":
            return None
        order = session.get(PaymentOrder, evidence.payment_order_id)
        if order is None or not order.external_order_id.startswith("sim-") or order.live_mode:
            return None
        paid_at = datetime.fromisoformat(evidence.snapshot["last_updated_date"])
        if paid_at.tzinfo is not None:
            paid_at = paid_at.astimezone(timezone.utc).replace(tzinfo=None)
        effective_at = max(paid_at, datetime.now(timezone.utc).replace(tzinfo=None))
        return EffectiveCommission(
            evidence.id, evidence.snapshot_hash, order.id, order.professional_id,
            order.external_order_id, "sim-settlement-" + order.external_order_id[4:],
            DEMO_COMMISSION, "ARS", False, effective_at, paid_at,
        )


def _effect_service():
    return PaymentEffectService(
        session_factory=_sessions(), policy_provider=lambda _: DEMO_POLICY,
        commission_provider=_commission_proof, effects_enabled=True,
        commission_enabled=True,
    )


def _processor():
    return PaymentOrderReconciliationProcessor(
        session_factory=_sessions(), adapter=SimulatedMercadoPagoOrderQueryAdapter(),
        enabled=True, simulated_timing=_simulated_timing,
    )


def _order_for_contract(contract_id):
    from app.models.payment_obligation import PaymentObligation
    with _sessions()() as session:
        return (session.query(PaymentOrder)
                .join(PaymentObligation, PaymentOrder.obligation_id == PaymentObligation.id)
                .filter(PaymentObligation.contract_request_id == contract_id)
                .one_or_none())


def simulate_payment(contract_id):
    order = _order_for_contract(contract_id)
    if order is None or not order.external_order_id.startswith("sim-") or order.live_mode:
        raise ValueError("simulated order unavailable")
    if order.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise ValueError("simulated order expired")
    event_identity = "sim-event-" + order.external_order_id[4:]
    with _sessions()() as session, session.begin():
        existing = session.query(PSPEventRecord).filter_by(
            provider="mercadopago", test_mode=True, external_event_id=event_identity,
        ).one_or_none()
        if existing is None:
            now = datetime.now(timezone.utc)
            event = PSPEvent(
                provider="mercadopago", external_event_id=event_identity,
                topic="order", action="order.processed",
                external_resource_id=order.external_order_id, test_mode=True,
                occurred_at=now, received_at=now,
                payload_hash=sha256(event_identity.encode("ascii")).hexdigest(),
            )
            event_id = receive_order_event(session, event)
        else:
            event_id = existing.id
        work_id = session.query(Work.id).filter_by(event_id=event_id).scalar()
    if work_id is None:
        raise ValueError("simulated event unavailable")
    return _processor().process(work_id)


def apply_effect(contract_id):
    order = _order_for_contract(contract_id)
    if order is None or not order.external_order_id.startswith("sim-") or order.live_mode:
        raise ValueError("simulated order unavailable")
    with _sessions()() as session:
        evidence = session.query(Evidence).filter_by(payment_order_id=order.id).one_or_none()
        if evidence is None:
            raise ValueError("simulated reconciliation required")
        evidence_id = evidence.id
    return _effect_service().apply_evidence(evidence_id)


def progress(contract_id):
    with _sessions()() as session:
        contract = session.get(ContractRequest, contract_id)
        if contract is None:
            raise ValueError("simulated contract unavailable")
        order = _order_for_contract(contract_id)
        evidence = (session.query(Evidence).filter_by(payment_order_id=order.id).one_or_none()
                    if order is not None else None)
        decision = (session.query(Decision).filter_by(evidence_id=evidence.id).one_or_none()
                    if evidence is not None else None)
        commission = (session.query(Commission).filter_by(payment_order_id=order.id).one_or_none()
                      if order is not None else None)
        grants = (session.query(Grant).filter_by(professional_id=contract.professional_id).count())
        return dict(contract=contract.estado, order=order.external_order_id if order else None,
                    payment="APROBADO SIMULADO" if evidence else "PENDIENTE",
                    reconciliation=evidence.timing if evidence else "PENDIENTE",
                    commission=commission.status if commission else "PENDIENTE",
                    credit=decision.status if decision else "PENDIENTE", grants=grants)
