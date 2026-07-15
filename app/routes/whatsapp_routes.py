from flask import Blueprint, abort, redirect, request, session

from app.services.whatsapp_contact_service import (
    actualizar_estado,
    crear_sesion,
    generar_url,
)
from app.models.whatsapp_contact_session import WhatsAppContactSession


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


@whatsapp.route("/whatsapp/iniciar", methods=["POST"])
def iniciar_whatsapp():
    if request.form.get("whatsapp_consent") != "on":
        return "Debes aceptar el consentimiento para continuar", 400

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
        return str(error), 400

    return redirect(whatsapp_url)
