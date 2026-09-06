from datetime import datetime, timezone


def utc_now():
    """Return the current timezone-aware UTC instant."""
    return datetime.now(timezone.utc)


def as_utc_naive(value):
    """Normalize a timestamp for legacy DateTime columns stored as UTC naive."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
