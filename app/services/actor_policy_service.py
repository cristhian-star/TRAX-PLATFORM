from app import db
from app.models.user import User


def require_active_actor(actor_user_id, allowed_roles):
    if actor_user_id is None:
        raise PermissionError("Actor autenticado requerido")

    actor = db.session.get(User, actor_user_id)
    if actor is None or actor.estado != "ACTIVO":
        raise PermissionError("Actor autenticado activo requerido")
    if actor.rol not in frozenset(allowed_roles):
        raise PermissionError("Rol no habilitado para esta operacion")
    return actor


def require_client_owner_actor(actor_user_id, owner_user_id):
    actor = require_active_actor(actor_user_id, ("CLIENTE",))
    if actor.id != owner_user_id:
        raise PermissionError("Solo el cliente propietario puede ejecutar esta operacion")
    return actor
