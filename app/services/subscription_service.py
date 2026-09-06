from app import db
from app.models.subscription import Subscription
from app.models.user import User
from app.models.verification_request import VerificationRequest
from app.services.pro_time import as_utc_naive, utc_now


def _validate_plan(plan):
    if hasattr(Subscription, "PLANES") and plan not in Subscription.PLANES:
        raise ValueError("Plan de suscripcion invalido")


def _validate_status(estado):
    if hasattr(Subscription, "ESTADOS") and estado not in Subscription.ESTADOS:
        raise ValueError("Estado de suscripcion invalido")


def create_subscription(user_id, plan="FREE"):
    _validate_plan(plan)
    _validate_status("ACTIVA")

    if plan == "PRO":
        raise RuntimeError("La activacion manual de MANDOBRA PRO no esta disponible")

    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        estado="ACTIVA",
        started_at=as_utc_naive(utc_now()),
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
    raise RuntimeError("La activacion manual de MANDOBRA PRO no esta disponible")


def cancel_subscription(user_id, now=None):
    _validate_status("CANCELADA")
    evaluated_at = as_utc_naive(now or utc_now())

    subscriptions = (
        Subscription.query
        .filter(
            Subscription.user_id == user_id,
            Subscription.plan == "PRO",
            Subscription.estado == "ACTIVA",
            Subscription.source_type.in_(Subscription.SOURCE_TYPES),
            Subscription.expires_at.isnot(None),
            Subscription.expires_at > evaluated_at,
        )
        .all()
    )

    if not subscriptions:
        return None

    for subscription in subscriptions:
        subscription.estado = "CANCELADA"
        subscription.auto_renew = False
    return subscriptions[0]


def has_pro_access(user_id, now=None):
    user = db.session.get(User, user_id)
    if user is None or user.rol != "PROFESIONAL" or user.estado != "ACTIVO":
        return False

    approved = (
        VerificationRequest.query
        .filter_by(
            user_id=user_id,
            tipo_usuario="PROFESIONAL",
            estado="APROBADO",
        )
        .first()
    )
    if approved is None:
        return False

    evaluated_at = as_utc_naive(now or utc_now())
    return (
        Subscription.query
        .filter(
            Subscription.user_id == user_id,
            Subscription.plan == "PRO",
            Subscription.estado == "ACTIVA",
            Subscription.source_type.in_(Subscription.SOURCE_TYPES),
            Subscription.expires_at.isnot(None),
            Subscription.expires_at > evaluated_at,
        )
        .first()
        is not None
    )
