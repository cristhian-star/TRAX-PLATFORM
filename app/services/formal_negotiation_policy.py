from dataclasses import dataclass

from app import db
from app.models.professional import Professional
from app.models.user import User
from app.models.verification_request import VerificationRequest


@dataclass(frozen=True)
class FormalNegotiationEligibility:
    allowed: bool
    reason: str


def _approved_verification(user_id, user_type):
    return (
        VerificationRequest.query.filter_by(
            user_id=user_id,
            tipo_usuario=user_type,
            estado="APROBADO",
        ).first()
        is not None
    )


def evaluate_formal_negotiation_eligibility(
    actor_user_id,
    professional_or_id,
):
    professional = (
        professional_or_id
        if isinstance(professional_or_id, Professional)
        else db.session.get(Professional, professional_or_id)
    )
    if professional is None:
        return FormalNegotiationEligibility(False, "PROFESSIONAL_NOT_FOUND")

    actor = db.session.get(User, actor_user_id) if actor_user_id else None
    if actor is None:
        return FormalNegotiationEligibility(False, "AUTHENTICATION_REQUIRED")
    if actor.estado != "ACTIVO":
        return FormalNegotiationEligibility(False, "ACTOR_NOT_ACTIVE")
    if actor.rol != "CLIENTE":
        return FormalNegotiationEligibility(False, "CLIENT_ROLE_REQUIRED")
    if not _approved_verification(actor.id, "CLIENTE"):
        return FormalNegotiationEligibility(False, "CLIENT_VERIFICATION_REQUIRED")
    if professional.user_id == actor.id:
        return FormalNegotiationEligibility(False, "SELF_NEGOTIATION_FORBIDDEN")

    professional_user = (
        db.session.get(User, professional.user_id)
        if professional.user_id
        else None
    )
    if (
        professional_user is None
        or professional_user.estado != "ACTIVO"
        or professional_user.rol != "PROFESIONAL"
    ):
        return FormalNegotiationEligibility(False, "PROFESSIONAL_NOT_ACTIVE")
    if (
        not professional.perfil_completo
        or professional.estado_perfil != "VERIFICADO"
        or not _approved_verification(
            professional_user.id,
            "PROFESIONAL",
        )
    ):
        return FormalNegotiationEligibility(False, "PROFESSIONAL_NOT_ENABLED")

    return FormalNegotiationEligibility(True, "ELIGIBLE")


def require_formal_negotiation_eligibility(
    actor_user_id,
    professional_or_id,
):
    eligibility = evaluate_formal_negotiation_eligibility(
        actor_user_id,
        professional_or_id,
    )
    if not eligibility.allowed:
        raise PermissionError(
            "La cuenta no esta habilitada para iniciar un acuerdo formal"
        )
    return eligibility


def build_formal_negotiation_eligibility_map(
    professionals,
    actor_user_id,
):
    return {
        professional.id: evaluate_formal_negotiation_eligibility(
            actor_user_id,
            professional,
        ).allowed
        for professional in professionals
    }


__all__ = (
    "FormalNegotiationEligibility",
    "evaluate_formal_negotiation_eligibility",
    "require_formal_negotiation_eligibility",
    "build_formal_negotiation_eligibility_map",
)
