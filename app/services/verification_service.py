from datetime import datetime

from app import db
from app.models.verification_request import VerificationRequest


def create_verification_request(
    user_id,
    tipo_usuario,
    documento_identidad=None,
    certificado_oficio=None,
    titulo_profesional=None,
    material_probatorio=None,
    observaciones=None
):
    verification_request = VerificationRequest(
        user_id=user_id,
        tipo_usuario=tipo_usuario,
        documento_identidad=documento_identidad,
        certificado_oficio=certificado_oficio,
        titulo_profesional=titulo_profesional,
        material_probatorio=material_probatorio,
        observaciones=observaciones
    )

    db.session.add(verification_request)
    db.session.commit()

    return verification_request


def create_or_update_professional_verification_request(
    user_id,
    documento_identidad=None,
    certificado_oficio=None,
    titulo_profesional=None,
    material_probatorio=None,
    observaciones=None
):
    verification_request = (
        VerificationRequest.query
        .filter_by(user_id=user_id, tipo_usuario="PROFESIONAL", estado="PENDIENTE")
        .order_by(VerificationRequest.created_at.desc())
        .first()
    )

    if verification_request is None:
        return create_verification_request(
            user_id=user_id,
            tipo_usuario="PROFESIONAL",
            documento_identidad=documento_identidad,
            certificado_oficio=certificado_oficio,
            titulo_profesional=titulo_profesional,
            material_probatorio=material_probatorio,
            observaciones=observaciones
        )

    verification_request.documento_identidad = documento_identidad
    verification_request.certificado_oficio = certificado_oficio
    verification_request.titulo_profesional = titulo_profesional
    verification_request.material_probatorio = material_probatorio
    verification_request.observaciones = observaciones
    verification_request.reviewed_at = None
    verification_request.reviewer_id = None
    db.session.commit()

    return verification_request


def get_pending_verifications():
    return (
        VerificationRequest.query
        .filter_by(estado="PENDIENTE")
        .order_by(VerificationRequest.created_at.asc())
        .all()
    )


def has_approved_verification(user_id):
    return (
        VerificationRequest.query
        .filter_by(user_id=user_id, estado="APROBADO")
        .first()
        is not None
    )


def update_verification_status(
    verification_request_id,
    estado,
    reviewer_id=None,
    observaciones=None
):
    if estado not in VerificationRequest.ESTADOS:
        raise ValueError("Estado de verificacion invalido")

    verification_request = VerificationRequest.query.get(verification_request_id)

    if verification_request is None:
        return None

    verification_request.estado = estado
    verification_request.reviewer_id = reviewer_id
    verification_request.observaciones = observaciones
    verification_request.reviewed_at = datetime.utcnow()
    db.session.commit()

    return verification_request
