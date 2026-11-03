"""Private calendar presentation; client inbox reception remains unavailable."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import abort

from app.services.emergency_shift_service import TIMEZONE_NAME, SHIFT_HOURS, GUARDIA_DIURNA, GUARDIA_NOCTURNA, reservation_window
from app.services.pro_time import utc_now


def urgency_context(args, *, clock=None):
    # Do not turn a client request id into a professional authorization.
    if 'solicitud' in args:
        abort(404)
    view = args.get('vista', 'solicitudes')
    if len(args.getlist('vista')) > 1 or view not in ('solicitudes', 'guardias', 'actividad'):
        abort(400)
    value = args.get('fecha')
    if value is not None:
        try:
            if len(args.getlist('fecha')) > 1 or len(value) != 10 or date.fromisoformat(value).isoformat() != value or date.fromisoformat(value) == date.max:
                raise ValueError
        except ValueError:
            abort(400)
    try:
        zone = ZoneInfo(TIMEZONE_NAME)
    except ZoneInfoNotFoundError:
        return dict(urgency_view=view, selected_date=None, today=None,
                    timezone_name=TIMEZONE_NAME, shift_blocks=[], timezone_error=True)
    now = (clock or utc_now)().astimezone(zone)
    today = now.date()
    value = value or today.isoformat()
    try:
        if len(args.getlist('fecha')) > 1 or len(value) != 10:
            raise ValueError
        day = date.fromisoformat(value)
        if day.isoformat() != value or day == date.max:
            raise ValueError
    except ValueError:
        abort(400)
    # Bound week arithmetic even for adversarial ISO dates near year 9999.
    monday = day - timedelta(days=day.weekday())
    if monday > date.max - timedelta(days=14):
        abort(400)
    first_week, end_day = reservation_window(now)
    last_week = end_day - timedelta(days=7)
    bounded_week = min(max(monday, first_week), last_week)
    redirect_date = bounded_week.isoformat() if monday != bounded_week else None
    if redirect_date:
        day = bounded_week
    monday = bounded_week
    week = []
    names = ('Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom')
    for offset in range(7):
        current = monday + timedelta(days=offset)
        shifts = []
        for kind, label in ((GUARDIA_DIURNA, 'Diurna'), (GUARDIA_NOCTURNA, 'Nocturna')):
            start = datetime.combine(current, time(SHIFT_HOURS[kind]), zone)
            end = start + timedelta(hours=12)
            shifts.append(dict(label=label, start=start, end=end,
                               key=f'{current.isoformat()}-{kind}',
                               selectable=now <= start - timedelta(minutes=2)))
        week.append(dict(day=current, label=names[offset], shifts=shifts))
    blocks = []
    for kind, label in ((GUARDIA_DIURNA, 'Diurno'), (GUARDIA_NOCTURNA, 'Nocturno')):
        start = datetime.combine(day, time(SHIFT_HOURS[kind]), zone)
        end = start + timedelta(hours=12)
        blocks.append(dict(label=label, start=start, end=end))
    return dict(urgency_view=view, selected_date=day.isoformat(),
                today=today, timezone_name=TIMEZONE_NAME, shift_blocks=blocks, timezone_error=False,
                week=week, week_start=monday, week_end=monday + timedelta(days=6),
                previous_week=(monday - timedelta(days=7)).isoformat() if monday > first_week else None,
                next_week=(monday + timedelta(days=7)).isoformat() if monday < last_week else None,
                redirect_date=redirect_date)


def reservation_context(actor, context, selected=()):
    from app import db
    from app.models.user import User
    from app.models.professional import Professional
    from app.models.emergency_shift import EmergencyShift
    from app.services.emergency_reservation_service import eligible, issue_key, naive
    from app.services.emergency_release_service import released_versions, issue_release_key, release_deadline
    user = db.session.get(User, actor)
    professional = Professional.query.filter_by(user_id=actor).first()
    allowed = eligible(user, professional)
    now = naive(utc_now())
    records = EmergencyShift.query.filter_by(professional_id=professional.id).order_by(EmergencyShift.starts_at).all() if professional else []
    indexed = {(r.day, r.kind): r for r in records}
    released = released_versions(actor, [r.id for r in records])
    for day in context.get('week', []):
        for block in day['shifts']:
            record = indexed.get((day['day'], block['key'][11:]))
            state = None
            if record:
                state = ('Liberada' if record.invalidated_at and (record.id, record.version) in released else 'Invalidada' if record.invalidated_at else 'Finalizada' if now >= record.ends_at
                         else 'En curso' if now >= record.starts_at and allowed else 'Programada' if allowed else 'No habilitada')
            block['reservation_state'] = state
            block['selectable'] = block['selectable'] and allowed and not record
            block['selected'] = block['selectable'] and block['key'] in selected
    active = [r for r in records if not r.invalidated_at and r.starts_at <= now < r.ends_at] if allowed else []
    scheduled = []
    if allowed and not context['timezone_error']:
        zone = ZoneInfo(TIMEZONE_NAME)
        for record in records:
            if record.invalidated_at or record.ends_at <= now:
                continue
            scheduled.append(dict(
                id=record.id, release_key=issue_release_key(actor, record),
                release_allowed=now < release_deadline(record),
                release_deadline=release_deadline(record).replace(tzinfo=timezone.utc).astimezone(zone),
                start=record.starts_at.replace(tzinfo=timezone.utc).astimezone(zone),
                end=record.ends_at.replace(tzinfo=timezone.utc).astimezone(zone),
                label='Diurna' if record.kind == GUARDIA_DIURNA else 'Nocturna',
                state='En curso' if record.starts_at <= now else 'Programada'))
    return dict(server_now=now.replace(tzinfo=timezone.utc).isoformat(), scheduled_shifts=scheduled, reservation_allowed=allowed and not context['timezone_error'], reservation_key=issue_key(actor),
                active_shift=active[0] if active else None, reservations=records,
                reservation_error=None, reservation_success=False)
