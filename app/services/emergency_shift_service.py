"""Pure shift planning; this module neither reserves nor dispatches anything."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.pro_time import utc_now


TIMEZONE_NAME = "America/Argentina/Buenos_Aires"
GUARDIA_DIURNA = "GUARDIA_DIURNA"
GUARDIA_NOCTURNA = "GUARDIA_NOCTURNA"
SHIFT_HOURS = {GUARDIA_DIURNA: 7, GUARDIA_NOCTURNA: 19}
COMMITMENT_VERSION = "emergency-shift-v1"
REMINDER_OFFSETS = (("T_MINUS_6H", timedelta(hours=6)),
                    ("T_MINUS_1H", timedelta(hours=1)))


class ShiftValidationError(ValueError):
    """Public, sanitized validation error for this pure service."""


def _validate_block(day, kind):
    if type(day) is not date or type(kind) is not str or kind not in SHIFT_HOURS:
        raise ShiftValidationError("Fecha o turno inválido.")
    if day == date.max and kind == GUARDIA_NOCTURNA:
        raise ShiftValidationError("Fecha o turno inválido.")
    return day, kind


def _utc(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ShiftValidationError("Se requiere un instante con zona horaria.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class ShiftPlan:
    kind: str
    starts_at: datetime
    ends_at: datetime
    cutoff_at: datetime
    booked_at: datetime
    accepted_at: datetime
    commitment_version: str
    late: bool
    reminders: tuple
    omitted_reminders: tuple
    confirmation: str


def plan_shift(day, kind, *, accepted, clock=utc_now, local_zone=None):
    """Validate one block using the server clock, without rounding timestamps.

    local_zone is an explicit test seam. Production uses IANA, with no fixed-offset
    fallback. The caller must persist acceptance atomically before confirming.
    """
    day, kind = _validate_block(day, kind)
    if accepted is not True:
        raise ShiftValidationError("Debés aceptar expresamente el compromiso de guardia.")
    zone = local_zone if local_zone is not None else ZoneInfo(TIMEZONE_NAME)
    start = datetime.combine(day, time(SHIFT_HOURS[kind]), zone)
    end_day = day + timedelta(days=1) if kind == GUARDIA_NOCTURNA else day
    end = datetime.combine(end_day, time(7 if kind == GUARDIA_NOCTURNA else 19), zone)
    starts_at, ends_at = _utc(start), _utc(end)
    cutoff = starts_at - timedelta(minutes=2)
    now = _utc(clock())
    if now > cutoff:
        raise ShiftValidationError("El período de inscripción finalizó.")
    reminders = tuple((key, starts_at - delta) for key, delta in REMINDER_OFFSETS
                      if now < starts_at - delta)
    omitted = tuple(key for key, delta in REMINDER_OFFSETS
                    if now >= starts_at - delta)
    next_day = " (día siguiente)" if end.date() != start.date() else ""
    confirmation = (
        f"Tu guardia comienza el {start:%d/%m/%Y} a las {start:%H:%M} y finaliza "
        f"el {end:%d/%m/%Y} a las {end:%H:%M}{next_day}. "
        f"Zona horaria: {TIMEZONE_NAME}. Al confirmarla, te comprometés a permanecer "
        "atento a las solicitudes y medios de contacto habilitados durante todo el turno."
    )
    return ShiftPlan(kind, starts_at, ends_at, cutoff, now, now, COMMITMENT_VERSION,
                     now >= starts_at - timedelta(hours=1), reminders, omitted,
                     confirmation)


def plan_shifts(blocks, *, accepted, clock=utc_now, local_zone=None):
    """Validate a batch with a single instant; DB uniqueness remains mandatory."""
    # Only built-in lists/tuples are accepted; no arbitrary iterators are consumed.
    if type(blocks) not in (list, tuple):
        raise ShiftValidationError("La colección de turnos debe ser una lista o tupla.")
    if not blocks:
        raise ShiftValidationError("Seleccioná al menos un turno.")
    normalized = []
    for block in blocks:
        if type(block) not in (list, tuple) or len(block) != 2:
            raise ShiftValidationError("Cada bloque debe contener fecha y turno.")
        normalized.append(_validate_block(block[0], block[1]))
    blocks = tuple(normalized)
    if len(set(blocks)) != len(blocks):
        raise ShiftValidationError("No podés reservar dos veces el mismo bloque.")
    now = _utc(clock())
    return tuple(plan_shift(day, kind, accepted=accepted, clock=lambda: now,
                            local_zone=local_zone) for day, kind in blocks)
