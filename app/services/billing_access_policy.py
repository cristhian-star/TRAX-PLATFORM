"""Reuse entitlement policy without embedding commercial rules in fiscal code."""
from app import db
from app.models.user import User
from app.services.subscription_service import has_pro_access


class BillingAccessDenied(PermissionError):
    pass


def require_billing_actor(actor_user_id, *, writing=False, now=None):
    if type(actor_user_id) is not int or actor_user_id <= 0:
        raise BillingAccessDenied("Acceso no disponible.")
    actor = db.session.get(User, actor_user_id, populate_existing=True)
    if actor is None or actor.rol != "PROFESIONAL" or actor.estado != "ACTIVO":
        raise BillingAccessDenied("Acceso no disponible.")
    if writing and not has_pro_access(actor_user_id, now=now):
        raise BillingAccessDenied("Se requiere PRO vigente.")
    return actor.id
