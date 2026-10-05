"""Persisted eligibility shared by proposal commands and presentation."""
from dataclasses import dataclass

from app import db
from app.models.user import User
from app.models.professional import Professional
from app.services.user_service import is_user_active
from app.services.verification_service import has_approved_verification


MESSAGES = {
    "AUTH_REQUIRED": "Iniciá sesión como profesional para postularte.",
    "ACCOUNT_INACTIVE": "Tu cuenta debe estar activa para postularte.",
    "ROLE_NOT_PROFESSIONAL": "Solo los profesionales pueden postularse.",
    "PROFILE_INCOMPLETE": "Completá tu perfil profesional para postularte.",
    "VERIFICATION_REQUIRED": "Necesitás una verificación aprobada para postularte.",
    "ELIGIBLE": "Podés postularte a esta propuesta.",
}


@dataclass(frozen=True)
class ProposalEligibility:
    eligible: bool
    reason: str

    @property
    def message(self):
        return MESSAGES[self.reason]


def proposal_application_eligibility(user_id):
    if user_id is None:
        return ProposalEligibility(False, "AUTH_REQUIRED")
    user = db.session.get(User, user_id)
    if not is_user_active(user):
        return ProposalEligibility(False, "ACCOUNT_INACTIVE")
    if user.rol != "PROFESIONAL":
        return ProposalEligibility(False, "ROLE_NOT_PROFESSIONAL")
    professional = Professional.query.filter_by(user_id=user_id).first()
    if professional is None or not professional.perfil_completo:
        return ProposalEligibility(False, "PROFILE_INCOMPLETE")
    if not has_approved_verification(user_id):
        return ProposalEligibility(False, "VERIFICATION_REQUIRED")
    return ProposalEligibility(True, "ELIGIBLE")
