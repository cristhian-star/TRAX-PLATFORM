from app import db
from app.models.user import User
from app.services.emergency_reservation_service import lock_owner, invalidate_locked


ALLOWED_ROLES = {"CLIENTE", "PROFESIONAL", "SUPER_ADMIN"}


def is_user_active(user):
    return user is not None and user.estado == "ACTIVO"


def get_all_users():
    return User.query.order_by(User.id.asc()).all()


def update_user_role(user_id, new_role):
    if new_role not in ALLOWED_ROLES:
        raise ValueError("Rol de usuario invalido")

    user, professional = lock_owner(user_id)

    if user is None:
        return None

    if user.rol != new_role:
        invalidate_locked(professional, user_id)
    user.rol = new_role
    db.session.commit()

    return user


def suspend_user(user_id, motivo=""):
    user, professional = lock_owner(user_id)

    if user is None:
        return None

    invalidate_locked(professional, user_id)
    user.estado = "SUSPENDIDO"
    user.motivo_estado = motivo or None
    db.session.commit()

    return user


def reactivate_user(user_id):
    user, professional = lock_owner(user_id)

    if user is None:
        return None

    user.estado = "ACTIVO"
    user.motivo_estado = None
    db.session.commit()

    return user


def ban_user(user_id, motivo=""):
    user, professional = lock_owner(user_id)

    if user is None:
        return None

    invalidate_locked(professional, user_id)
    user.estado = "BANEADO"
    user.motivo_estado = motivo or None
    db.session.commit()

    return user
