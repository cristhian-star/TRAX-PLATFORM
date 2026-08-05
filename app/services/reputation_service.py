from app import db
from app.models.reputation_event import ReputationEvent


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
