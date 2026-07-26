from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.proposal_application import ProposalApplication
from app.models.proposal_request import ProposalRequest
from app.services.contracting_core_service import create_contract_from_proposal_application


OPEN_STATUSES = (
    "PUBLICADA",
)


@dataclass(frozen=True)
class ProposalAcceptanceResult:
    application: ProposalApplication
    contract: object
    created: bool
    state_changed: bool


def _parse_decimal(value, field_label, required=False):
    if value is None or str(value).strip() == "":
        if required:
            raise ValueError(f"{field_label} es requerido")
        return None

    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_label} no es valido") from None

    if parsed < 0:
        raise ValueError(f"{field_label} no puede ser negativo")

    return parsed


def create_proposal_request(
    owner_user_id,
    industria,
    categoria,
    rubro,
    especialidad,
    titulo,
    descripcion,
    ubicacion,
    modalidad,
    cantidad_profesionales,
    presupuesto_estimado=None,
    fecha_inicio_estimada=None,
    fecha_limite_postulacion=None,
):
    proposal_request = ProposalRequest(
        cliente_id=owner_user_id,
        owner_user_id=owner_user_id,
        industria=industria,
        categoria=categoria,
        rubro=rubro,
        especialidad=especialidad,
        titulo=titulo,
        descripcion=descripcion,
        ubicacion=ubicacion,
        modalidad=modalidad,
        cantidad_profesionales=cantidad_profesionales or 1,
        presupuesto_estimado=_parse_decimal(presupuesto_estimado, "El presupuesto estimado"),
        fecha_inicio_estimada=fecha_inicio_estimada,
        fecha_limite_postulacion=fecha_limite_postulacion,
        estado="PUBLICADA",
    )

    db.session.add(proposal_request)
    db.session.commit()

    return proposal_request


def get_open_proposals(industria=None, categoria=None, rubro=None, ubicacion=None):
    query = ProposalRequest.query.filter(ProposalRequest.estado.in_(OPEN_STATUSES))

    if industria:
        query = query.filter(ProposalRequest.industria.ilike(f"%{industria}%"))
    if categoria:
        query = query.filter(ProposalRequest.categoria.ilike(f"%{categoria}%"))
    if rubro:
        query = query.filter(ProposalRequest.rubro.ilike(f"%{rubro}%"))
    if ubicacion:
        query = query.filter(ProposalRequest.ubicacion.ilike(f"%{ubicacion}%"))

    return query.order_by(ProposalRequest.created_at.desc(), ProposalRequest.id.desc()).all()


def get_proposal_by_id(proposal_id):
    return db.session.get(ProposalRequest, proposal_id)


def get_proposal_applications(proposal_id):
    return (
        ProposalApplication.query
        .filter_by(proposal_id=proposal_id)
        .order_by(ProposalApplication.created_at.desc(), ProposalApplication.id.desc())
        .all()
    )


def get_professional_application(proposal_id, professional_user_id):
    return ProposalApplication.query.filter_by(
        proposal_id=proposal_id,
        professional_user_id=professional_user_id,
    ).first()


def apply_to_proposal(
    proposal_id,
    professional_user_id,
    mensaje,
    experiencia_relevante=None,
    disponibilidad=None,
    pretension_economica=None,
):
    proposal = ProposalRequest.query.filter_by(id=proposal_id).with_for_update().first()
    if proposal is None:
        raise ValueError("Propuesta no encontrada")

    owner_id = proposal.owner_user_id or proposal.cliente_id
    if owner_id == professional_user_id:
        raise ValueError("No podes postularte a tu propia propuesta")
    if proposal.estado not in OPEN_STATUSES:
        raise ValueError("Esta propuesta ya no recibe postulaciones")

    professional = Professional.query.filter_by(user_id=professional_user_id).first()
    if professional is None or not professional.perfil_completo:
        raise ValueError("Necesitas completar tu perfil profesional para postularte")

    if get_professional_application(proposal.id, professional_user_id):
        raise ValueError("Ya te postulaste a esta propuesta")

    application = ProposalApplication(
        proposal_id=proposal.id,
        professional_id=professional.id,
        professional_user_id=professional_user_id,
        mensaje=mensaje,
        experiencia_relevante=experiencia_relevante,
        disponibilidad=disponibilidad,
        pretension_economica=_parse_decimal(pretension_economica, "La pretension economica"),
        estado="POSTULADA",
    )

    db.session.add(application)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Ya te postulaste a esta propuesta") from None

    return application


def accept_application(proposal_id, application_id, owner_user_id):
    try:
        proposal = ProposalRequest.query.filter_by(id=proposal_id).with_for_update().first()
        if proposal is None:
            raise ValueError("Propuesta no encontrada")
        if (proposal.owner_user_id or proposal.cliente_id) != owner_user_id:
            raise PermissionError("Solo el publicador puede gestionar postulaciones")

        application = ProposalApplication.query.filter_by(
            id=application_id,
            proposal_id=proposal.id,
        ).first()
        if application is None:
            raise ValueError("Postulacion no encontrada")

        if application.estado == "ACEPTADA":
            contract_result = create_contract_from_proposal_application(application.id, actor_user_id=owner_user_id)
            db.session.commit()
            return ProposalAcceptanceResult(
                application=application,
                contract=contract_result.contract,
                created=contract_result.created,
                state_changed=False,
            )
        if proposal.estado in ("CANCELADA", "CERRADA"):
            raise ValueError("Esta propuesta ya no permite aceptar postulaciones")
        if application.estado in ("DESCARTADA", "RECHAZADA"):
            raise ValueError("No se puede aceptar una postulacion descartada")

        application.estado = "ACEPTADA"
        if proposal.hiring_mode == ProposalRequest.HIRING_MODE_SINGLE:
            for other_application in proposal.applications:
                if other_application.id != application.id and other_application.estado == "POSTULADA":
                    other_application.estado = "DESCARTADA"
            proposal.estado = "CERRADA"

        contract_result = create_contract_from_proposal_application(application.id, actor_user_id=owner_user_id)
        db.session.commit()
        return ProposalAcceptanceResult(
            application=application,
            contract=contract_result.contract,
            created=contract_result.created,
            state_changed=True,
        )
    except IntegrityError:
        db.session.rollback()
        existing = ContractRequest.query.filter_by(proposal_application_id=application_id).first()
        if existing is not None and existing.cliente_id == owner_user_id:
            application = db.session.get(ProposalApplication, application_id)
            return ProposalAcceptanceResult(
                application=application,
                contract=existing,
                created=False,
                state_changed=False,
            )
        raise
    except Exception:
        db.session.rollback()
        raise


def discard_application(proposal_id, application_id, owner_user_id):
    proposal = ProposalRequest.query.filter_by(id=proposal_id).with_for_update().first()
    if proposal is None:
        raise ValueError("Propuesta no encontrada")
    if (proposal.owner_user_id or proposal.cliente_id) != owner_user_id:
        raise PermissionError("Solo el publicador puede gestionar postulaciones")

    application = ProposalApplication.query.filter_by(
        id=application_id,
        proposal_id=proposal.id,
    ).first()
    if application is None:
        raise ValueError("Postulacion no encontrada")
    if application.estado != "ACEPTADA":
        application.estado = "DESCARTADA"

    db.session.commit()
    return application


def cancel_proposal(proposal_id, owner_user_id):
    proposal = ProposalRequest.query.filter_by(id=proposal_id).with_for_update().first()
    if proposal is None:
        raise ValueError("Propuesta no encontrada")
    if (proposal.owner_user_id or proposal.cliente_id) != owner_user_id:
        raise PermissionError("Solo el publicador puede cancelar esta propuesta")
    if proposal.estado == "CANCELADA":
        return proposal

    proposal.estado = "CANCELADA"
    db.session.commit()
    return proposal


def close_proposal(proposal_request_id):
    proposal_request = ProposalRequest.query.get(proposal_request_id)

    if proposal_request is None:
        return None

    proposal_request.estado = "CERRADA"
    db.session.commit()

    return proposal_request
