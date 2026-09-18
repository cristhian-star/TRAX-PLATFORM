"""Explicit, disabled-by-default credit effects over committed 4E evidence."""
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from decimal import Decimal, localcontext
import hashlib
import json
import re

from sqlalchemy import update, cast, Numeric

from app.models.payment_order import PaymentOrder
from app.models.professional import Professional
from app.models.user import User
from app.models.verification_request import VerificationRequest
from app.models.subscription import Subscription
from app.models.psp_event import PSPEventRecord
from app.models.payment_order_reconciliation import (
    PaymentOrderReconciliationEvidence as Evidence,
    PaymentOrderReconciliationWork as Work,
    PaymentOrderReconciliationAttempt as Attempt,
    PaymentOrderReconciliationQuarantine as Quarantine,
)
from app.models.payment_effect import (
    TransactionalCreditPolicy as PolicyRecord, PaymentEffectDecision as Decision,
    TransactionalCommission as Commission, TransactionalCreditLot as Lot,
    TransactionalCreditGrant as Grant, TransactionalCreditAllocation as Allocation,
    PaymentEffectAudit as Audit,
    PaymentEffectPaymentClaim as PaymentClaim,
)
from app.services.payment_order_reconciliation_service import _context, utcnow, insert_once
from app.services.pro_time import as_utc_naive


_FAILED = object()
_VERSION = re.compile(r"[A-Za-z0-9_.-]{1,80}", re.ASCII)
_IDENTITY = re.compile(r"[A-Za-z0-9_-]{1,160}", re.ASCII)


def _safe(function, *args):
    try:
        return function(*args)
    except Exception:
        return _FAILED


def _money(value):
    if (type(value) is not Decimal or not value.is_finite() or value <= 0
            or value >= Decimal("1e62") or value.as_tuple().exponent < -2):
        raise ValueError("invalid explicit credit amount")


@dataclass(frozen=True, slots=True)
class CreditPolicy:
    version: str
    monthly_price: Decimal
    currency: str

    def __post_init__(self):
        if type(self.version) is not str or not _VERSION.fullmatch(self.version) or self.currency != "ARS":
            raise ValueError("invalid explicit credit policy")
        _money(self.monthly_price)


@dataclass(frozen=True, slots=True)
class EffectiveCommission:
    """Trusted settlement attestation, never inferred from marketplace_fee."""
    evidence_id: int
    snapshot_hash: str
    payment_order_id: int
    professional_id: int
    external_order_id: str
    external_identity: str
    net_amount: Decimal
    currency: str
    live_mode: bool
    effective_at: datetime
    paid_at: datetime


class PaymentEffectUnavailableError(RuntimeError):
    pass


class PaymentEffectService:
    def __init__(self, *, session_factory, policy_provider=None, commission_provider=None,
                 effects_enabled=False, commission_enabled=False, clock=utcnow):
        if (not callable(session_factory) or not callable(clock)
                or type(effects_enabled) is not bool or type(commission_enabled) is not bool
                or (policy_provider is not None and not callable(policy_provider))
                or (commission_provider is not None and not callable(commission_provider))):
            raise ValueError("invalid payment effect configuration")
        self._sessions, self._clock = session_factory, clock
        self._policy, self._commission = policy_provider, commission_provider
        self._enabled, self._commission_enabled = effects_enabled, commission_enabled

    def __repr__(self):
        return "PaymentEffectService(enabled=<configured>)"

    def apply_evidence(self, evidence_id):
        if not self._enabled:
            return "DISABLED"
        result = _safe(self._apply, evidence_id)
        if result is _FAILED:
            raise PaymentEffectUnavailableError("payment effects temporarily unavailable")
        return result

    def _apply(self, evidence_id):
        # Providers run with no local transaction/connection held; revalidate below.
        with self._sessions() as session:
            evidence = session.get(Evidence, evidence_id)
            if evidence is None:
                return "NOT_ELIGIBLE"
            event = session.get(PSPEventRecord, evidence.event_id)
            context = _context(session, event)
            digest = evidence.snapshot_hash
        if context is None:
            return "NOT_ELIGIBLE"
        policy = _safe(self._policy, context.professional_id) if self._policy else None
        proof = _safe(self._commission, evidence_id) if self._commission and self._commission_enabled else None
        with self._sessions() as session, session.begin(), localcontext() as decimal_context:
            decimal_context.prec = 128
            # User lock serializes all sources/obligations of this professional.
            user = _lock_owner(session, context.professional_id)
            session.query(PaymentOrder).filter_by(id=context.payment_order_id).populate_existing().with_for_update().one()
            session.execute(update(PaymentOrder).where(PaymentOrder.id == context.payment_order_id).values(
                amount=PaymentOrder.amount, updated_at=PaymentOrder.updated_at))
            evidence = session.get(Evidence, evidence_id, populate_existing=True)
            now = as_utc_naive(self._clock())
            if session.query(Decision.id).join(Evidence, Decision.evidence_id == Evidence.id).filter(
                Evidence.payment_order_id == context.payment_order_id, Decision.status == "PENDING_REVIEW",
            ).first():
                return _decision(session, evidence_id, context.professional_id, "PENDING_REVIEW", "UNRESOLVED_REVIEW", now)
            reason = _classify(session, evidence, context, digest, now)
            if reason is not None:
                status = "NOT_ELIGIBLE" if reason == "NOT_ACCREDITED" else "PENDING_REVIEW"
                _pending_commission(session, context, evidence_id, status)
                return _decision(session, evidence_id, context.professional_id, status, reason, now)
            if not _eligible(session, user):
                return _decision(session, evidence_id, context.professional_id, "NOT_ELIGIBLE", "OWNER_NOT_ELIGIBLE", now)
            if type(policy) is not CreditPolicy or not self._commission_enabled:
                _pending_commission(session, context, evidence_id, "PENDING_POLICY")
                return _decision(session, evidence_id, context.professional_id, "PENDING_POLICY", "POLICY_UNAVAILABLE", now)
            if not _valid_proof(proof, evidence, context, now):
                _pending_commission(session, context, evidence_id, "PENDING_POLICY")
                return _decision(session, evidence_id, context.professional_id, "PENDING_POLICY", "COMMISSION_UNAVAILABLE", now)
            effective_at = as_utc_naive(proof.effective_at)
            paid_at = as_utc_naive(proof.paid_at)
            if paid_at >= context.expires_at:
                _pending_commission(session, context, evidence_id, "PENDING_REVIEW")
                return _decision(session, evidence_id, context.professional_id, "PENDING_REVIEW", "LATE_PAYMENT", now)
            if _active(session, user.id, paid_at, source="SUBSCRIPTION"):
                prior = session.query(Commission).filter_by(payment_order_id=context.payment_order_id).one_or_none()
                if prior is not None and prior.status == "EFFECTIVE":
                    return _decision(session, evidence_id, context.professional_id, "PENDING_REVIEW", "PAID_SOURCE_CONTRADICTION", now)
                _pending_commission(session, context, evidence_id, "EXEMPT")
                return _decision(session, evidence_id, context.professional_id, "EXEMPT", "PAID_SUBSCRIPTION", now)
            insert_once(session, PolicyRecord, dict(version=policy.version, currency=policy.currency,
                        threshold=policy.monthly_price), ["version"])
            stored = session.query(PolicyRecord).filter_by(version=policy.version).populate_existing().with_for_update().one()
            if stored.threshold != policy.monthly_price or stored.currency != policy.currency:
                return _decision(session, evidence_id, context.professional_id, "PENDING_REVIEW", "POLICY_VERSION_CONFLICT", now)
            existing = session.query(Commission).filter_by(payment_order_id=context.payment_order_id).one_or_none()
            if existing is not None and existing.status == "EFFECTIVE":
                same = (existing.external_identity == proof.external_identity and existing.net_amount == proof.net_amount
                        and existing.currency == proof.currency and existing.effective_at == effective_at
                        and existing.paid_at == paid_at)
                return _decision(session, evidence_id, context.professional_id, "REPLAY" if same else "PENDING_REVIEW",
                                 "ALREADY_ACCRUED" if same else "COMMISSION_CONTRADICTION", now)
            if existing is not None and existing.status == "EXEMPT":
                return _decision(session, evidence_id, context.professional_id, "EXEMPT", "PAID_SUBSCRIPTION", now)
            collision = session.query(Commission).filter_by(provider="mercadopago", live_mode=context.live_mode, external_identity=proof.external_identity).one_or_none()
            if collision is not None:
                return _decision(session, evidence_id, context.professional_id, "PENDING_REVIEW", "COMMISSION_IDENTITY_COLLISION", now)
            for payment in sorted(evidence.snapshot["transactions"]["payments"], key=lambda row: row["id"]):
                values = dict(provider="mercadopago", live_mode=context.live_mode, external_payment_id=payment["id"],
                              payment_order_id=context.payment_order_id, evidence_id=evidence_id)
                insert_once(session, PaymentClaim, values, ["provider", "live_mode", "external_payment_id"])
                claimed = session.query(PaymentClaim).filter_by(provider="mercadopago", live_mode=context.live_mode,
                                                               external_payment_id=payment["id"]).one()
                if claimed.payment_order_id != context.payment_order_id:
                    return _decision(session, evidence_id, context.professional_id, "PENDING_REVIEW", "PAYMENT_IDENTITY_COLLISION", now)
            if existing is None:
                existing = Commission(payment_order_id=context.payment_order_id, evidence_id=evidence_id,
                                      professional_id=context.professional_id, provider="mercadopago", live_mode=context.live_mode)
                session.add(existing)
            existing.status, existing.policy_version = "EFFECTIVE", policy.version
            existing.external_identity, existing.net_amount = proof.external_identity, proof.net_amount
            existing.currency, existing.effective_at = policy.currency, effective_at
            existing.paid_at = paid_at
            session.flush()
            session.add(Lot(commission_id=existing.id, professional_id=context.professional_id,
                            policy_version=policy.version, original_amount=proof.net_amount,
                            remaining_amount=proof.net_amount, credited_at=now, expires_at=now + timedelta(days=40)))
            session.flush()
            _, consumed_at = _consume(session, context.professional_id, user, policy, self._clock)
            return _decision(session, evidence_id, context.professional_id, "ACCRUED", "EFFECTIVE_COMMISSION", consumed_at)

    def consume_credit(self, professional_id):
        if not self._enabled or not self._commission_enabled:
            return "DISABLED"
        result = _safe(self._consume_credit, professional_id)
        if result is _FAILED:
            raise PaymentEffectUnavailableError("payment effects temporarily unavailable")
        return result

    def _consume_credit(self, professional_id):
        policy = _safe(self._policy, professional_id) if self._policy else None
        if type(policy) is not CreditPolicy:
            return "PENDING_POLICY"
        with self._sessions() as session, session.begin(), localcontext() as decimal_context:
            decimal_context.prec = 128
            user = _lock_owner(session, professional_id)
            if not _eligible(session, user):
                return "NOT_ELIGIBLE"
            stored = session.get(PolicyRecord, policy.version)
            if stored is None:
                return "PENDING_POLICY"
            if stored.threshold != policy.monthly_price or stored.currency != policy.currency:
                return "PENDING_REVIEW"
            return _consume(session, professional_id, user, policy, self._clock)[0]


def _lock_owner(session, professional_id):
    professional = session.get(Professional, professional_id)
    if professional is None or professional.user_id is None:
        raise ValueError("invalid credit owner")
    user = session.query(User).filter_by(id=professional.user_id).populate_existing().with_for_update().one()
    # Write first on SQLite; transactions never persist a read-only savepoint.
    session.execute(update(User).where(User.id == user.id).values(estado=User.estado))
    return session.get(User, user.id, populate_existing=True)


def _eligible(session, user):
    return (user.rol == "PROFESIONAL" and user.estado == "ACTIVO"
            and session.query(VerificationRequest.id).filter_by(user_id=user.id, tipo_usuario="PROFESIONAL", estado="APROBADO").with_for_update().first() is not None)


def _active(session, user_id, now, source=None):
    query = session.query(Subscription).filter(
        Subscription.user_id == user_id, Subscription.plan == "PRO", Subscription.estado == "ACTIVA",
        Subscription.source_type.in_(Subscription.SOURCE_TYPES), Subscription.started_at <= now,
        Subscription.expires_at > now,
    )
    if source:
        query = query.filter(Subscription.source_type == source)
    return query.first() is not None


def _classify(session, evidence, context, digest, now):
    event = session.get(PSPEventRecord, evidence.event_id)
    work = session.query(Work).filter_by(event_id=evidence.event_id).one_or_none()
    attempt = session.get(Attempt, evidence.attempt_id)
    if (_context(session, event) != context or evidence.payment_order_id != context.payment_order_id
            or evidence.snapshot_hash != digest or work is None or work.status != "DONE"
            or attempt is None or attempt.work_id != work.id or attempt.outcome != "RECONCILED"):
        return "EVIDENCE_NOT_VERIFIED"
    if session.query(Quarantine.id).join(PSPEventRecord, PSPEventRecord.id == Quarantine.event_id).filter(
        PSPEventRecord.external_resource_id == context.external_order_id,
        PSPEventRecord.provider == "mercadopago", PSPEventRecord.test_mode == (not context.live_mode),
    ).first():
        return "QUARANTINED_RESOURCE"
    facts = session.query(Evidence).filter_by(payment_order_id=context.payment_order_id).all()
    for fact in facts:
        snapshot = fact.snapshot
        encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(encoded).hexdigest() != fact.snapshot_hash:
            return "EVIDENCE_CONTRADICTION"
        transactions = snapshot["transactions"]
        if (transactions["refunds"] or transactions["chargebacks"]
                or snapshot["status"] in ("refunded", "charged_back", "canceled")
                or snapshot["status_detail"] in ("refunded", "partially_refunded", "reimbursed")):
            return "REVERSAL_PRESENT"
    if evidence.timing != "BEFORE_LOCAL_EXPIRY":
        return "PAYMENT_TIMING_UNCERTAIN" if evidence.timing == "UNKNOWN" else "LATE_PAYMENT"
    snapshot = evidence.snapshot
    if (snapshot["id"] != context.external_order_id or snapshot["external_reference"] != context.external_reference
            or snapshot["currency"] != "ARS" or snapshot["live_mode"] is not context.live_mode
            or Decimal(snapshot["total_amount"]) != context.amount):
        return "EVIDENCE_CONTRADICTION"
    payments = snapshot["transactions"]["payments"]
    if (snapshot["status"] != "processed" or snapshot["status_detail"] != "accredited"
            or Decimal(snapshot["total_paid_amount"]) != context.amount or not payments
            or any(payment["status"] != "processed" or payment["status_detail"] != "accredited"
                   or Decimal(payment["paid_amount"]) != Decimal(payment["amount"]) for payment in payments)
            or sum((Decimal(payment["paid_amount"]) for payment in payments), Decimal(0)) != context.amount):
        return "NOT_ACCREDITED"
    if evidence.observed_at > now:
        return "EVIDENCE_CONTRADICTION"
    return None


def _valid_proof(proof, evidence, context, now):
    def validate():
        if (type(proof) is not EffectiveCommission or proof.evidence_id != evidence.id
                or proof.snapshot_hash != evidence.snapshot_hash or proof.payment_order_id != context.payment_order_id
                or proof.professional_id != context.professional_id or proof.external_order_id != context.external_order_id
                or proof.currency != "ARS" or type(proof.live_mode) is not bool or proof.live_mode is not context.live_mode
                or type(proof.external_identity) is not str or not _IDENTITY.fullmatch(proof.external_identity)):
            return False
        _money(proof.net_amount)
        effective = as_utc_naive(proof.effective_at)
        paid = as_utc_naive(proof.paid_at)
        created = as_utc_naive(datetime.fromisoformat(evidence.snapshot["created_date"]))
        return proof.net_amount <= context.amount and created <= paid <= effective <= now
    return _safe(validate) is True


def _pending_commission(session, context, evidence_id, status):
    if status == "NOT_ELIGIBLE":
        return
    record = session.query(Commission).filter_by(payment_order_id=context.payment_order_id).one_or_none()
    if record is None:
        session.add(Commission(payment_order_id=context.payment_order_id, evidence_id=evidence_id,
                               professional_id=context.professional_id, status=status,
                               provider="mercadopago", live_mode=context.live_mode))
    elif record.status not in ("EFFECTIVE", "EXEMPT"):
        record.status = status


def _decision(session, evidence_id, professional_id, status, reason, now):
    record = session.query(Decision).filter_by(evidence_id=evidence_id).one_or_none()
    if record is None:
        session.add(Decision(evidence_id=evidence_id, status=status, reason=reason, observed_at=now))
        changed = True
    else:
        changed = record.status != status or record.reason != reason
        record.status, record.reason, record.observed_at = status, reason, now
    if changed:
        session.add(Audit(professional_id=professional_id, evidence_id=evidence_id, operation=reason, occurred_at=now))
    return status


def _consume(session, professional_id, user, policy, clock):
    # Lock every candidate before sampling the time used for eligibility/effects.
    stored = session.query(PolicyRecord).filter_by(version=policy.version).populate_existing().with_for_update().one()
    lots = session.query(Lot).filter(
        Lot.professional_id == professional_id, cast(Lot.remaining_amount, Numeric) > 0,
    ).order_by(Lot.credited_at, Lot.id).populate_existing().with_for_update().all()
    commissions = [session.get(Commission, lot.commission_id) for lot in lots]
    for order_id in sorted({commission.payment_order_id for commission in commissions}):
        session.query(PaymentOrder).filter_by(id=order_id).populate_existing().with_for_update().one()
        session.execute(update(PaymentOrder).where(PaymentOrder.id == order_id).values(
            amount=PaymentOrder.amount, updated_at=PaymentOrder.updated_at))
    session.query(Subscription).filter_by(user_id=user.id).populate_existing().with_for_update().all()
    eligible = _eligible(session, user)
    now = as_utc_naive(clock())
    if not eligible:
        return "NOT_ELIGIBLE", now
    if stored.threshold != policy.monthly_price or stored.currency != policy.currency:
        return "PENDING_REVIEW", now
    # A lot may expire while waiting for any of the locks above.
    lots = [lot for lot in lots if lot.expires_at > now and lot.remaining_amount > 0]
    if _active(session, user.id, now):
        return "ACTIVE_PERIOD", now
    if session.query(Subscription.id).filter(
        Subscription.user_id == user.id, Subscription.plan == "PRO", Subscription.estado == "ACTIVA",
        Subscription.source_type.in_(Subscription.SOURCE_TYPES),
        Subscription.started_at < now + timedelta(days=30), Subscription.expires_at > now,
    ).first():
        return "PENDING_REVIEW", now  # Never overlap an already funded future source.
    if any(lot.policy_version != policy.version for lot in lots):
        return "PENDING_REVIEW", now  # Price changes have no approved conversion policy.
    # Reversals and later quarantine freeze affected contributions; never erase them.
    for lot in lots:
        commission = session.get(Commission, lot.commission_id)
        evidence = session.get(Evidence, commission.evidence_id)
        context = _context(session, session.get(PSPEventRecord, evidence.event_id))
        if context is None or _classify(session, evidence, context, evidence.snapshot_hash, now) is not None:
            return "PENDING_REVIEW", now
        if session.query(Decision.id).join(Evidence, Decision.evidence_id == Evidence.id).filter(
            Evidence.payment_order_id == commission.payment_order_id, Decision.status == "PENDING_REVIEW",
        ).first():
            return "PENDING_REVIEW", now
    if sum((lot.remaining_amount for lot in lots), Decimal(0)) < policy.monthly_price:
        return "INSUFFICIENT_CREDITS", now
    subscription = Subscription(user_id=user.id, plan="PRO", estado="ACTIVA", source_type="TRANSACTIONAL",
                                started_at=now, expires_at=now + timedelta(days=30), auto_renew=False)
    session.add(subscription)
    session.flush()
    grant = Grant(professional_id=professional_id, policy_version=policy.version, subscription_id=subscription.id,
                  starts_at=now, expires_at=subscription.expires_at, credits_consumed=1)
    session.add(grant)
    session.flush()
    needed = policy.monthly_price
    for lot in lots:
        amount = min(lot.remaining_amount, needed)
        if amount > 0:
            lot.remaining_amount -= amount
            needed -= amount
            session.add(Allocation(grant_id=grant.id, lot_id=lot.id, amount=amount))
        if needed == 0:
            break
    session.add(Audit(professional_id=professional_id, grant_id=grant.id, operation="CREDIT_CONSUMED_30_DAYS", occurred_at=now))
    return "GRANTED", now


def build_payment_effect_service(*, app, session_factory, policy_provider=None, commission_provider=None, clock=utcnow):
    service = PaymentEffectService(session_factory=session_factory, policy_provider=policy_provider,
        commission_provider=commission_provider, clock=clock,
        effects_enabled=app.config.get("PAYMENT_EFFECTS_ENABLED") is True,
        commission_enabled=app.config.get("TRANSACTIONAL_COMMISSION_ENABLED") is True)
    app.extensions["payment_effect_service"] = service
    return service
