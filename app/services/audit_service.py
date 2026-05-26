from app import db
from app.models.audit_log import AuditLog


def create_audit_log(
    actor_user_id,
    action,
    target_user_id=None,
    description="",
    ip_address=None,
    user_agent=None,
):
    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.session.add(audit_log)
    db.session.commit()

    return audit_log


def get_recent_audit_logs(limit=100):
    return (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_user_audit_logs(user_id):
    return (
        AuditLog.query
        .filter(
            (AuditLog.actor_user_id == user_id)
            | (AuditLog.target_user_id == user_id)
        )
        .order_by(AuditLog.created_at.desc())
        .all()
    )
