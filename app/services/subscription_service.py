from datetime import datetime

from app import db
from app.models.subscription import Subscription


def _validate_plan(plan):
    if hasattr(Subscription, "PLANES") and plan not in Subscription.PLANES:
        raise ValueError("Plan de suscripcion invalido")


def _validate_status(estado):
    if hasattr(Subscription, "ESTADOS") and estado not in Subscription.ESTADOS:
        raise ValueError("Estado de suscripcion invalido")


def create_subscription(user_id, plan="FREE"):
    _validate_plan(plan)
    _validate_status("ACTIVA")

    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        estado="ACTIVA",
        started_at=datetime.utcnow()
    )

    db.session.add(subscription)
    db.session.commit()

    return subscription


def get_active_subscription(user_id):
    return (
        Subscription.query
        .filter_by(user_id=user_id, estado="ACTIVA")
        .order_by(Subscription.started_at.desc())
        .first()
    )


def upgrade_to_pro(user_id):
    _validate_plan("PRO")
    _validate_status("ACTIVA")

    subscription = get_active_subscription(user_id)

    if subscription is None:
        return create_subscription(user_id, plan="PRO")

    subscription.plan = "PRO"
    subscription.estado = "ACTIVA"
    db.session.commit()

    return subscription


def cancel_subscription(user_id):
    _validate_status("CANCELADA")

    subscription = get_active_subscription(user_id)

    if subscription is None:
        return None

    subscription.estado = "CANCELADA"
    subscription.auto_renew = False
    db.session.commit()

    return subscription


def has_pro_access(user_id):
    subscription = get_active_subscription(user_id)

    if subscription is None:
        return False

    return subscription.plan in ("PRO", "ENTERPRISE")