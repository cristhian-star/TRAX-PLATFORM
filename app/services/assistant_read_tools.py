"""Internal local read dispatcher; deliberately not registered as HTTP/MCP API.

Only trusted server code may create ActorContext. Model JSON goes in arguments,
never in context. Within HTTP requests the current session must also match context.
No conversations, shared private caches, provider clients or business writes.
"""
from dataclasses import dataclass
import json
from flask import has_request_context, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.routing import BuildError
from app import db
from app.models.user import User
from app.services.user_service import ALLOWED_ROLES
from app.services import assistant_help_service as help_service
from app.services import assistant_work_record_reader as records
from app.services.assistant_contracts import validate, InvalidInput, MAX_OUTPUT_BYTES, OUTPUT_DATA_SCHEMAS, conforms


@dataclass(frozen=True)
class ActorContext:
    """Server-only identity. Never construct this from a tool call or model output."""
    user_id: int


class AccessError(Exception):
    def __init__(self, code):
        self.code = code


MESSAGES = {
    "INVALID_INPUT": "Solicitud inválida.",
    "UNAUTHENTICATED": "Iniciá sesión para consultar.",
    "FORBIDDEN": "No tenés acceso a esta consulta.",
    "NOT_FOUND": "Registro no encontrado.",
    "UNAVAILABLE": "La consulta no está disponible. Usá el recorrido web habitual.",
    "LIMIT_EXCEEDED": "La consulta excede el límite de respuesta.",
}


def error(code):
    return {"status": "error", "error": {"code": code, "message": MESSAGES[code]}}


def actor(context):
    if context is None:
        identity = session.get("user_id") if has_request_context() else None
    elif type(context) is ActorContext:
        identity = context.user_id
        if has_request_context():
            current_identity = session.get("user_id")
            if type(current_identity) is not int or current_identity != identity:
                raise AccessError("UNAUTHENTICATED")
    else:
        raise AccessError("UNAUTHENTICATED")
    if type(identity) is not int or not 1 <= identity <= 2147483647:
        raise AccessError("UNAUTHENTICATED")
    # Refresh persisted role/state even when the identity map already contains User.
    user = User.query.populate_existing().filter_by(id=identity).first()
    if user is None:
        raise AccessError("UNAUTHENTICATED")
    if user.estado != "ACTIVO" or user.rol not in ALLOWED_ROLES:
        raise AccessError("FORBIDDEN")
    return user


def execute(name, arguments, *, context=None):
    """Returns status ok/empty/error; absent and foreign records both use NOT_FOUND.

    Invoke with a clean SQLAlchemy session. Refuse pending writes without flushing,
    committing or rolling back the caller's transaction. Infrastructure errors leave
    transaction recovery to the caller; this boundary never commits business state.
    """
    try:
        args = validate(name, arguments)
        if db.session.new or db.session.dirty or db.session.deleted:
            return error("UNAVAILABLE")
        with db.session.no_autoflush:
            user = actor(context)
            if name == "help.search":
                result = help_service.search(args["query"], user.rol, args.get("limit", 3))
            else:
                if user.rol != "PROFESIONAL":
                    return error("FORBIDDEN")
                reader = {"work_records.list": records.list_records,
                          "work_records.get": records.get_record,
                          "followups.list": records.list_followups}[name]
                result = reader(user.id, args)
        if not conforms(result, OUTPUT_DATA_SCHEMAS[name]):
            return error("UNAVAILABLE")
        response = {"status": "empty" if "items" in result and not result["items"] else "ok", "data": result}
        if len(json.dumps(response, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_OUTPUT_BYTES:
            return error("LIMIT_EXCEEDED")
        return response
    except InvalidInput:
        return error("INVALID_INPUT")
    except AccessError as exc:
        return error(exc.code)
    except PermissionError:
        return error("FORBIDDEN")
    except LookupError:
        return error("NOT_FOUND")
    except (SQLAlchemyError, help_service.HelpUnavailable, BuildError, UnicodeError):
        return error("UNAVAILABLE")
