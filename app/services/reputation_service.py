from app import db
from app.models.reputation_event import ReputationEvent


def _valid_event_types():
    if hasattr(ReputationEvent, "TIPOS"):
        return ReputationEvent.TIPOS

    if hasattr(ReputationEvent, "TIPOS_EVENTO"):
        return ReputationEvent.TIPOS_EVENTO

    return None


def add_reputation_event(user_id, tipo_evento, puntos, descripcion=""):
    event_types = _valid_event_types()

    if event_types is not None and tipo_evento not in event_types:
        raise ValueError("Tipo de evento de reputacion invalido")

    reputation_event = ReputationEvent(
        user_id=user_id,
        tipo_evento=tipo_evento,
        puntos=puntos,
        descripcion=descripcion
    )

    db.session.add(reputation_event)
    db.session.commit()

    return reputation_event


def get_user_reputation_score(user_id):
    score = (
        db.session.query(db.func.coalesce(db.func.sum(ReputationEvent.puntos), 0))
        .filter_by(user_id=user_id)
        .scalar()
    )

    return int(score or 0)


def get_user_reputation_events(user_id):
    return (
        ReputationEvent.query
        .filter_by(user_id=user_id)
        .order_by(ReputationEvent.created_at.desc())
        .all()
    )