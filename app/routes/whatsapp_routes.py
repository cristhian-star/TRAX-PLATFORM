from flask import Blueprint, abort, jsonify, redirect, request, session

from app.services.whatsapp_contact_service import (
    actualizar_estado,
    crear_sesion,
    generar_url,
)
from app.models.whatsapp_contact_session import WhatsAppContactSession
from app import limiter
from app.utils.security import user_or_ip_rate_limit_key


whatsapp = Blueprint("whatsapp", __name__)


def _empty_to_none(value):
    if value is None:
        return None

    value = value.strip()
    return value or None


def _parse_optional_int(value):
    value = _empty_to_none(value)

    if value is None:
        return None

    return int(value)


def _wants_json_response():
    return (
        request.accept_mimetypes.best == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.is_json
    )


def _error_response(message, status_code):
    if _wants_json_response():
        return jsonify({"error": message}), status_code

    return message, status_code


@whatsapp.route("/whatsapp/iniciar", methods=["POST"])
@limiter.limit("10 per hour", key_func=user_or_ip_rate_limit_key)
def iniciar_whatsapp():
    if request.form.get("whatsapp_consent") != "on":
        return _error_response("Debes aceptar el consentimiento para continuar", 400)

    try:
        contact_session = crear_sesion(
            professional_id=int(request.form.get("professional_id")),
            operation_type=request.form.get("operation_type"),
            client_user_id=session.get("user_id"),
            entity_type=_empty_to_none(request.form.get("entity_type")),
            entity_id=_parse_optional_int(request.form.get("entity_id")),
            consent_given=True,
            metadata_json={
                "source_path": request.referrer,
            },
            commit=False,
        )
        whatsapp_url = generar_url(contact_session)
        actualizar_estado(
            contact_session,
            WhatsAppContactSession.STATUS_CONTACTO_ABIERTO,
            commit=True,
        )
    except PermissionError:
        abort(403)
    except (TypeError, ValueError) as error:
        return _error_response(str(error), 400)

    if _wants_json_response():
        return jsonify({
            "whatsapp_url": whatsapp_url,
            "status": contact_session.status,
        })

    return redirect(whatsapp_url)
