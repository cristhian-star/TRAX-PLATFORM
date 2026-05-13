from app import db
from app.models.terms_acceptance import TermsAcceptance


def accept_terms(user_id, tipo_termino, version, ip_address=None, user_agent=None):
    terms_acceptance = TermsAcceptance(
        user_id=user_id,
        tipo_termino=tipo_termino,
        version=version,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.session.add(terms_acceptance)
    db.session.commit()

    return terms_acceptance


def has_accepted_terms(user_id, tipo_termino, version):
    return (
        TermsAcceptance.query
        .filter_by(
            user_id=user_id,
            tipo_termino=tipo_termino,
            version=version
        )
        .first()
        is not None
    )
