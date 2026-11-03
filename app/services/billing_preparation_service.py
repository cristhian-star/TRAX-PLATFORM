"""Internal commands. Caller owns commit/rollback, including the audit rows.

No routes register these commands yet. An IntegrityError or StaleDataError must
roll back the entire caller transaction; never retry with a new request key.
"""
from uuid import UUID

from app import db
from app.models.audit_log import AuditLog
from app.models.billing_preparation import BillingProfile, BillingDraft
from app.services.billing_access_policy import require_billing_actor, BillingAccessDenied
from app.services.billing_preparation import prepare_profile, prepare_draft, BillingValidationError


class BillingConflict(ValueError):
    pass


def _audit(actor, action, entity_id=None):
    db.session.add(AuditLog(actor_user_id=actor, action=action,
                           entity_type="billing_preparation", entity_id=entity_id))


def save_profile(*, actor_user_id, expected_version, now=None, **values):
    actor = require_billing_actor(actor_user_id, writing=True, now=now)
    prepared = prepare_profile(**values)
    profile = db.session.get(BillingProfile, actor, populate_existing=True)
    if type(expected_version) is not int or expected_version < 0:
        raise BillingValidationError("expected_version")
    if profile is None:
        if expected_version != 0:
            raise BillingConflict("Revisá nuevamente el perfil.")
        profile = BillingProfile(owner_user_id=actor, cuit=prepared.cuit,
                                 legal_name=prepared.legal_name, fiscal_address=prepared.fiscal_address)
        db.session.add(profile)
    else:
        if expected_version != profile.version or prepared.cuit != profile.cuit:
            raise BillingConflict("Revisá nuevamente el perfil; el cambio de CUIT no está habilitado.")
        profile.legal_name = prepared.legal_name
        profile.fiscal_address = prepared.fiscal_address
    _audit(actor, "BILLING_PROFILE_DECLARED", actor)
    db.session.flush()
    return {"version": profile.version, "verification_status": profile.verification_status}


def create_draft(*, actor_user_id, request_key, now=None, **values):
    actor = require_billing_actor(actor_user_id, writing=True, now=now)
    if not isinstance(request_key, str):
        raise BillingValidationError("request_key")
    try:
        if str(UUID(request_key)) != request_key:
            raise ValueError
    except (ValueError, AttributeError):
        raise BillingValidationError("request_key") from None
    prepared = prepare_draft(**values)
    profile = db.session.get(BillingProfile, actor, populate_existing=True)
    if profile is None:
        raise BillingValidationError("profile")
    payload = {name: getattr(prepared, name) for name in (
        "description", "amount", "recipient_name", "service_from", "service_to")}
    existing = BillingDraft.query.filter_by(owner_user_id=actor, request_key=request_key).first()
    if existing is not None:
        if any(getattr(existing, name) != value for name, value in payload.items()):
            raise BillingConflict("La solicitud ya existe con otro contenido.")
        return {"id": existing.id, "status": existing.status}
    draft = BillingDraft(owner_user_id=actor, request_key=request_key,
                         profile_version=profile.version, **payload)
    db.session.add(draft)
    db.session.flush()
    _audit(actor, "BILLING_INTERNAL_DRAFT_CREATED", draft.id)
    db.session.flush()
    return {"id": draft.id, "status": draft.status}


def read_draft(*, actor_user_id, draft_id):
    actor = require_billing_actor(actor_user_id)
    if type(draft_id) is not int or draft_id <= 0:
        raise BillingAccessDenied("Acceso no disponible.")
    draft = BillingDraft.query.filter_by(id=draft_id, owner_user_id=actor).first()
    if draft is None:
        raise BillingAccessDenied("Acceso no disponible.")
    return {name: getattr(draft, name) for name in (
        "id", "description", "amount", "recipient_name", "service_from", "service_to", "status")}
