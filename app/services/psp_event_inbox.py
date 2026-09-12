from datetime import timezone

from sqlalchemy.exc import IntegrityError

from app.models.psp_event import PSPEventRecord
from app.services.psp_event_contract import PSPEvent


IDENTITY_CONSTRAINT = "uq_psp_event_inbox_identity"


class PSPEventConflictError(ValueError):
    pass


class PSPEventNotFoundError(LookupError):
    pass


def register_or_get_event(session, event):
    if not isinstance(event, PSPEvent):
        raise TypeError("event must be PSPEvent")
    existing = get_event_by_identity(
        session, event.provider, event.test_mode, event.external_event_id,
        required=False,
    )
    if existing is not None:
        return _matching(existing, event)
    record = PSPEventRecord(**event.__dict__) if hasattr(event, "__dict__") else PSPEventRecord(
        **{name: getattr(event, name) for name in event.__slots__}
    )
    if session.get_bind().dialect.name == "sqlite":
        session.add(record)
        session.flush()
        return record
    try:
        with session.begin_nested():
            session.add(record)
            session.flush()
        return record
    except IntegrityError as exc:
        if not _is_identity_violation(exc):
            raise
        existing = get_event_by_identity(
            session, event.provider, event.test_mode, event.external_event_id,
            required=False,
        )
        if existing is None:
            raise
        return _matching(existing, event)


def get_event(session, event_id):
    record = session.get(PSPEventRecord, event_id)
    if record is None:
        raise PSPEventNotFoundError("PSP event not found")
    return record


def get_event_by_identity(session, provider, test_mode, external_event_id, *, required=True):
    record = session.query(PSPEventRecord).filter_by(
        provider=provider, test_mode=test_mode, external_event_id=external_event_id
    ).one_or_none()
    if record is None and required:
        raise PSPEventNotFoundError("PSP event not found")
    return record


def _instant(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _matching(record, event):
    actual = (
        record.provider, record.external_event_id, record.topic, record.action,
        record.external_resource_id, record.test_mode, _instant(record.occurred_at),
        record.payload_hash,
    )
    expected = (
        event.provider, event.external_event_id, event.topic, event.action,
        event.external_resource_id, event.test_mode, _instant(event.occurred_at),
        event.payload_hash,
    )
    if actual != expected:
        raise PSPEventConflictError("PSP event identity has different canonical content")
    return record


def _is_identity_violation(error):
    driver_error = error.orig
    sqlstate = getattr(driver_error, "sqlstate", None) or getattr(driver_error, "pgcode", None)
    diagnostic = getattr(driver_error, "diag", None)
    return (
        sqlstate == "23505"
        and getattr(diagnostic, "constraint_name", None) == IDENTITY_CONSTRAINT
    )
