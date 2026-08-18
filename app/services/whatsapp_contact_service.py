from datetime import datetime
import re
from urllib.parse import quote_plus

from app import db
from app.models.budget_offer import BudgetOffer
from app.models.emergency_request import EmergencyRequest
from app.models.professional import Professional
from app.models.proposal_application import ProposalApplication
from app.models.whatsapp_contact_session import WhatsAppContactSession
from app.services.notification_service import (
    CATEGORIA_CUENTA,
    PRIORIDAD_INFO,
    registrar_evento,
)


OPERATION_PROFILE = "PERFIL_PROFESIONAL"
OPERATION_EMERGENCY = "EMERGENCIA"
OPERATION_BUDGET_AWARDED = "PRESUPUESTO_ADJUDICADO"
OPERATION_PROPOSAL_ACCEPTED = "PROPUESTA_ACEPTADA"
OPERATION_DIRECT_CONTACT = "CONTACTO_DIRECTO"

VALID_OPERATIONS = {
    OPERATION_PROFILE,
    OPERATION_EMERGENCY,
    OPERATION_BUDGET_AWARDED,
    OPERATION_PROPOSAL_ACCEPTED,
    OPERATION_DIRECT_CONTACT,
}

ENTITY_BUDGET_OFFER = "BudgetOffer"
ENTITY_EMERGENCY_REQUEST = "EmergencyRequest"
ENTITY_PROPOSAL_APPLICATION = "ProposalApplication"

TIPO_WHATSAPP_CONTACTO_INICIADO = "WHATSAPP_CONTACTO_INICIADO"

IDENTIFIER_USERNAME = "USERNAME"
IDENTIFIER_PHONE = "PHONE"
WHATSAPP_USERNAME_MAX_LENGTH = 64
WHATSAPP_USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._]{2,63}$")


def _sanitize_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if not 8 <= len(digits) <= 15:
        return None

    return digits


def normalizar_whatsapp_username(value):
    if value is None:
        return None

    username = value.strip().lower()
    if not username:
        return None

    if username.startswith("@"):
        username = username[1:]

    username = username.strip()
    if not username:
        return None

    if any(token in username for token in ("://", "wa.me", "whatsapp.com", "/", "?", "#")):
        raise ValueError("El username de WhatsApp no debe ser una URL")

    if any(character.isspace() for character in username):
        raise ValueError("El username de WhatsApp no debe contener espacios")

    if len(username) > WHATSAPP_USERNAME_MAX_LENGTH:
        raise ValueError(f"El username de WhatsApp admite hasta {WHATSAPP_USERNAME_MAX_LENGTH} caracteres")

    if not WHATSAPP_USERNAME_PATTERN.match(username):
        raise ValueError("El username de WhatsApp solo admite letras, numeros, punto y guion bajo")

    return username


def validar_whatsapp_username(value):
    try:
        return normalizar_whatsapp_username(value) is not None
    except ValueError:
        return False


def normalizar_preferencia_contacto(value):
    preference = (value or Professional.WHATSAPP_CONTACT_AUTO).strip().upper()
    if preference not in Professional.WHATSAPP_CONTACT_PREFERENCES:
        raise ValueError("Preferencia de contacto por WhatsApp invalida")

    return preference


def _mask_phone(value):
    phone = _sanitize_phone(value)
    if not phone:
        return None

    if len(phone) <= 4:
        return "*" * len(phone)

    return f"{'*' * max(len(phone) - 4, 0)}{phone[-4:]}"


def _mask_username(value):
    username = normalizar_whatsapp_username(value)
    if not username:
        return None

    if len(username) <= 3:
        return f"@{username[0]}**"

    return f"@{username[:2]}***{username[-1]}"


def obtener_tipo_identificador(identifier_data):
    return identifier_data["type"] if identifier_data else None


def resolver_identificador_contacto(professional):
    if professional is None:
        raise ValueError("Profesional no encontrado")

    phone = _sanitize_phone(professional.telefono)
    username = normalizar_whatsapp_username(professional.whatsapp_username)
    preference = normalizar_preferencia_contacto(professional.whatsapp_contact_preference)

    uses_username_conceptually = (
        preference == Professional.WHATSAPP_CONTACT_USERNAME
        or (preference == Professional.WHATSAPP_CONTACT_AUTO and username)
    )

    if uses_username_conceptually and username:
        if not phone:
            raise ValueError("WhatsApp requiere telefono como fallback tecnico hasta que usernames tengan URL publica estable")

        return {
            "type": IDENTIFIER_USERNAME,
            "identifier": username,
            "masked": _mask_username(username),
            "technical_type": IDENTIFIER_PHONE,
            "technical_identifier": phone,
            "uses_phone_url": True,
            "fallback_reason": "WhatsApp no ofrece URL publica estable para abrir chats por username.",
        }

    if preference == Professional.WHATSAPP_CONTACT_USERNAME and not username:
        if not phone:
            raise ValueError("Configura un username de WhatsApp valido o habilita el telefono como fallback")

        return {
            "type": IDENTIFIER_PHONE,
            "identifier": phone,
            "masked": _mask_phone(phone),
            "technical_type": IDENTIFIER_PHONE,
            "technical_identifier": phone,
            "uses_phone_url": True,
            "fallback_reason": "Preferencia username sin username valido; se uso telefono como fallback seguro.",
        }

    if not phone:
        raise ValueError("WhatsApp no disponible para este profesional")

    return {
        "type": IDENTIFIER_PHONE,
        "identifier": phone,
        "masked": _mask_phone(phone),
        "technical_type": IDENTIFIER_PHONE,
        "technical_identifier": phone,
        "uses_phone_url": True,
        "fallback_reason": None,
    }


def _build_message(professional, operation_type):
    operation_labels = {
        OPERATION_PROFILE: "tu perfil profesional en MANDOBRA",
        OPERATION_EMERGENCY: "una emergencia publicada en MANDOBRA",
        OPERATION_BUDGET_AWARDED: "un presupuesto adjudicado en MANDOBRA",
        OPERATION_PROPOSAL_ACCEPTED: "una propuesta aceptada en MANDOBRA",
        OPERATION_DIRECT_CONTACT: "MANDOBRA",
    }
    context = operation_labels.get(operation_type, "MANDOBRA")
    return f"Hola {professional.nombre}, te contacto desde {context}."


def buscar_sesion(session_id):
    return db.session.get(WhatsAppContactSession, session_id)


def _get_professional_or_error(professional_id):
    professional = db.session.get(Professional, professional_id)

    if professional is None:
        raise ValueError("Profesional no encontrado")
    if professional.user_id is None:
        raise ValueError("Perfil profesional sin propietario asociado")
    resolver_identificador_contacto(professional)

    return professional


def validar_operacion(
    operation_type,
    professional_id,
    actor_user_id=None,
    entity_type=None,
    entity_id=None,
):
    if operation_type not in VALID_OPERATIONS:
        raise ValueError("Operacion de WhatsApp invalida")

    professional = _get_professional_or_error(professional_id)

    if actor_user_id and professional.user_id == actor_user_id:
        raise PermissionError("No podes iniciar WhatsApp con tu propio perfil profesional")

    if operation_type in (OPERATION_PROFILE, OPERATION_DIRECT_CONTACT):
        return professional

    if operation_type == OPERATION_EMERGENCY:
        if entity_id:
            emergency = db.session.get(EmergencyRequest, entity_id)
            if emergency is None:
                raise ValueError("Emergencia no encontrada")
            if actor_user_id and emergency.cliente_id != actor_user_id:
                raise PermissionError("Solo el cliente dueno puede iniciar este contacto")
        return professional

    if operation_type == OPERATION_BUDGET_AWARDED:
        if entity_type != ENTITY_BUDGET_OFFER or not entity_id:
            raise ValueError("Presupuesto adjudicado invalido")
        offer = db.session.get(BudgetOffer, entity_id)
        if offer is None or offer.professional_id != professional.id:
            raise ValueError("Presupuesto adjudicado no encontrado")
        if offer.estado != "ADJUDICADO":
            raise PermissionError("Solo se puede contactar por WhatsApp a presupuestos adjudicados")
        if not actor_user_id or offer.budget_request.cliente_id != actor_user_id:
            raise PermissionError("Solo el cliente dueno puede iniciar este contacto")
        return professional

    if operation_type == OPERATION_PROPOSAL_ACCEPTED:
        if entity_type != ENTITY_PROPOSAL_APPLICATION or not entity_id:
            raise ValueError("Postulacion aceptada invalida")
        application = db.session.get(ProposalApplication, entity_id)
        if application is None or application.professional_id != professional.id:
            raise ValueError("Postulacion aceptada no encontrada")
        if application.estado != "ACEPTADA":
            raise PermissionError("Solo se puede contactar por WhatsApp a postulaciones aceptadas")
        owner_id = application.proposal.owner_user_id or application.proposal.cliente_id
        if not actor_user_id or owner_id != actor_user_id:
            raise PermissionError("Solo el publicador puede iniciar este contacto")
        return professional

    raise ValueError("Operacion de WhatsApp invalida")


def crear_sesion(
    professional_id,
    operation_type,
    client_user_id=None,
    entity_type=None,
    entity_id=None,
    consent_given=False,
    metadata_json=None,
    commit=True,
):
    if not consent_given:
        raise PermissionError("Debes aceptar el consentimiento para continuar")

    professional = validar_operacion(
        operation_type=operation_type,
        professional_id=professional_id,
        actor_user_id=client_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    identifier_data = resolver_identificador_contacto(professional)
    now = datetime.utcnow()
    contact_session = WhatsAppContactSession(
        client_user_id=client_user_id,
        professional_id=professional.id,
        operation_type=operation_type,
        entity_type=entity_type,
        entity_id=entity_id,
        status=WhatsAppContactSession.STATUS_INICIADA,
        contact_identifier_type=identifier_data["type"],
        contact_identifier_masked=identifier_data["masked"],
        consent_given=True,
        consent_at=now,
        last_status_at=now,
        metadata_json=metadata_json,
    )
    db.session.add(contact_session)
    db.session.flush()
    _registrar_notificaciones(contact_session, professional)

    if commit:
        db.session.commit()

    return contact_session


def generar_url(contact_session):
    professional = contact_session.professional
    identifier_data = resolver_identificador_contacto(professional)
    phone = identifier_data["technical_identifier"]

    if not phone:
        raise ValueError("WhatsApp no disponible para este profesional")

    message = quote_plus(_build_message(professional, contact_session.operation_type))
    return f"https://wa.me/{phone}?text={message}"


def actualizar_estado(contact_session, status, commit=True):
    if status not in WhatsAppContactSession.STATUSES:
        raise ValueError("Estado de WhatsApp invalido")

    contact_session.status = status
    contact_session.last_status_at = datetime.utcnow()

    if commit:
        db.session.commit()

    return contact_session


def obtener_contactos_cliente(user_id, limit=5):
    return (
        WhatsAppContactSession.query
        .filter_by(client_user_id=user_id)
        .order_by(WhatsAppContactSession.initiated_at.desc(), WhatsAppContactSession.id.desc())
        .limit(limit)
        .all()
    )


def obtener_contactos_profesional(professional_id, limit=5):
    return (
        WhatsAppContactSession.query
        .filter_by(professional_id=professional_id)
        .order_by(WhatsAppContactSession.initiated_at.desc(), WhatsAppContactSession.id.desc())
        .limit(limit)
        .all()
    )


def _registrar_notificaciones(contact_session, professional):
    if professional.user_id:
        registrar_evento(
            user_id=professional.user_id,
            actor_user_id=contact_session.client_user_id,
            tipo=TIPO_WHATSAPP_CONTACTO_INICIADO,
            categoria=CATEGORIA_CUENTA,
            titulo="Un cliente inicio contacto por WhatsApp",
            mensaje="Un cliente inicio contacto directo por WhatsApp desde MANDOBRA.",
            url_destino="/profesional/dashboard",
            entity_type="WhatsAppContactSession",
            entity_id=contact_session.id,
            prioridad=PRIORIDAD_INFO,
            commit=False,
        )

    if contact_session.client_user_id:
        registrar_evento(
            user_id=contact_session.client_user_id,
            actor_user_id=contact_session.client_user_id,
            tipo=TIPO_WHATSAPP_CONTACTO_INICIADO,
            categoria=CATEGORIA_CUENTA,
            titulo="Iniciaste contacto por WhatsApp",
            mensaje=f"Iniciaste contacto con {professional.nombre}.",
            url_destino=f"/profesional/{professional.id}",
            entity_type="WhatsAppContactSession",
            entity_id=contact_session.id,
            prioridad=PRIORIDAD_INFO,
            commit=False,
        )
