"""Atomic reservation application service; no dispatch/assignment of client requests."""
import hashlib
import json
import secrets
import uuid
import unicodedata
from datetime import date, datetime, timezone, timedelta
from itsdangerous import URLSafeSerializer, BadSignature
from flask import current_app
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.user import User
from app.models.professional import Professional
from app.models.verification_request import VerificationRequest
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.models.audit_log import AuditLog
from app.services.emergency_shift_service import plan_shifts, reservation_window
from app.services.pro_time import utc_now
from app.services.notification_service import crear_notificacion

OPERATION = 'EMERGENCY_SHIFT_RESERVE'
DESTINATION = '/profesional/oportunidades/urgencias?vista=guardias'


class ReservationConflict(ValueError):
    pass


def naive(value):
    if value.utcoffset() is None:
        raise ValueError('Se requiere reloj UTC con zona.')
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def issue_key(actor):
    return URLSafeSerializer(current_app.config['SECRET_KEY'], salt=OPERATION).dumps([actor, secrets.token_hex(16)])


def validate_key(actor, key):
    try:
        if not isinstance(key, str) or len(key) > 160:
            raise ValueError
        data = URLSafeSerializer(current_app.config['SECRET_KEY'], salt=OPERATION).loads(key)
        if not isinstance(data, list) or len(data) != 2 or data[0] != actor:
            raise ValueError
    except (BadSignature, ValueError, TypeError):
        raise ValueError('Formulario inválido. Recargá la página.') from None


def lock_owner(actor):
    # All eligibility writers acquire this same order before changing state.
    with db.session.no_autoflush:
        user = User.query.filter_by(id=actor).populate_existing().with_for_update().first()
        professional = Professional.query.filter_by(user_id=actor).populate_existing().with_for_update().first()
    return user, professional


def valid_text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 120 and not any(unicodedata.category(c).startswith('C') for c in value)


def eligible(user, professional):
    return bool(user and user.estado == 'ACTIVO' and user.rol == 'PROFESIONAL'
                and professional and professional.perfil_completo and professional.estado_perfil == 'VERIFICADO'
                and all(valid_text(v) for v in (professional.servicio, professional.coverage_city, professional.coverage_province))
                and VerificationRequest.query.filter_by(user_id=user.id, tipo_usuario='PROFESIONAL', estado='APROBADO').first())


def invalidate_locked(professional, actor, *, clock=utc_now):
    """Composable; caller owns commit and already holds user/profile locks."""
    if not professional:
        return
    now = naive(clock())
    shifts = EmergencyShift.query.filter(EmergencyShift.professional_id == professional.id,
        EmergencyShift.invalidated_at.is_(None), EmergencyShift.ends_at > now).order_by(EmergencyShift.id).with_for_update().all()
    for shift in shifts:
        shift.invalidated_at = now
        shift.version += 1
        db.session.add(AuditLog(actor_user_id=actor, target_user_id=professional.user_id,
            action='EMERGENCY_SHIFT_INVALIDATED', entity_type='EmergencyShift', entity_id=shift.id))
        for reminder in EmergencyShiftReminder.query.filter_by(shift_id=shift.id, status='PENDING').with_for_update().all():
            reminder.status = 'SKIPPED'
            reminder.processed_at = now


def parse_blocks(values):
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= 14:
        raise ValueError('Elegí entre uno y catorce turnos.')
    blocks = []
    for value in values:
        if not isinstance(value, str) or len(value) > 45:
            raise ValueError('Turno inválido.')
        try:
            day = date.fromisoformat(value[:10])
            kind = value[11:]
            if day.isoformat() != value[:10] or value[10] != '-' or day - timedelta(days=day.weekday()) > date.max - timedelta(days=14):
                raise ValueError
        except (ValueError, IndexError):
            raise ValueError('Turno inválido.') from None
        blocks.append((day, kind))
    if len(set(blocks)) != len(blocks):
        raise ValueError('No repitas un turno en la selección.')
    return sorted(blocks)


def reserve(actor, values, accepted, key, *, clock=None):
    try:
        user, professional = lock_owner(actor)
        if not eligible(user, professional):
            raise PermissionError('Tu cuenta necesita perfil completo, verificación profesional y oficio/cobertura válidos.')
        validate_key(actor, key)
        blocks = parse_blocks(values)
        if accepted is not True:
            raise ValueError('Debés aceptar expresamente las condiciones.')
        payload = [[day.isoformat(), kind] for day, kind in blocks]
        payload_hash = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
        command = OperationCommand.query.filter_by(actor_user_id=actor, operation=OPERATION, idempotency_key=key).with_for_update().first()
        if command:
            if command.payload_hash != payload_hash or command.status != 'SUCCEEDED':
                raise ReservationConflict('La clave ya se utilizó con otra selección.')
            audit = db.session.get(AuditLog, command.result_entity_id)
            if command.result_entity_type != 'AuditLog' or not audit or audit.actor_user_id != actor:
                raise ReservationConflict('No se pudo recuperar la confirmación original.')
            result = dict(audit.metadata_json)
            db.session.rollback()  # Read-only replay releases locks, no new effects.
            return result
        # Read the effective clock only after owner/command locks and authorized replay.
        instant = (clock or utc_now)()
        first_day, end_day = reservation_window(instant)
        if any(not first_day <= day < end_day for day, _ in blocks):
            raise ValueError('Elegí turnos de la semana actual o de las tres semanas siguientes.')
        plans = plan_shifts(blocks, accepted=True, clock=lambda: instant)
        now = naive(plans[0].booked_at)
        # Profile lock serializes all writers for this owner, including empty calendars.
        for day, kind in blocks:
            if EmergencyShift.query.filter_by(professional_id=professional.id, day=day, kind=kind).first():
                raise ReservationConflict('Uno de los turnos ya fue registrado. Revisá tu calendario.')
        command = OperationCommand(actor_user_id=actor, operation=OPERATION, idempotency_key=key,
            payload_hash=payload_hash, status='PROCESSING', correlation_id=str(uuid.uuid4()))
        db.session.add(command)
        ids = []
        for (day, kind), plan in zip(blocks, plans):
            shift = EmergencyShift(professional_id=professional.id, day=day, kind=kind,
                starts_at=naive(plan.starts_at), ends_at=naive(plan.ends_at), cutoff_at=naive(plan.cutoff_at),
                accepted_at=now, commitment_version=plan.commitment_version)
            db.session.add(shift)
            db.session.flush()
            ids.append(shift.id)
            for reminder_kind, due in plan.reminders:
                db.session.add(EmergencyShiftReminder(shift_id=shift.id, kind=reminder_kind, due_at=naive(due)))
        result = dict(version=1, shift_ids=ids, confirmed_at=now.isoformat(), blocks=payload)
        audit = AuditLog(actor_user_id=actor, target_user_id=actor, action='EMERGENCY_SHIFTS_RESERVED',
            entity_type='EmergencyShiftBatch', operation=OPERATION, correlation_id=command.correlation_id,
            idempotency_key=key, metadata_json=result)
        db.session.add(audit)
        db.session.flush()
        crear_notificacion(actor, 'GUARDIAS_RESERVADAS', 'EMERGENCIAS', 'Guardias programadas',
            f'Se registraron {len(ids)} turnos. Consultá las fechas en Mis guardias.',
            url_destino=DESTINATION, commit=False)
        command.status = 'SUCCEEDED'
        command.result_entity_type = 'AuditLog'
        command.result_entity_id = audit.id
        command.completed_at = now
        db.session.commit()
        return result
    except IntegrityError:
        db.session.rollback()
        # No unrelated integrity failure is converted into successful replay.
        raise ReservationConflict('No se pudo guardar la selección. Revisá el calendario y reintentá con la misma clave.') from None
    except Exception:
        db.session.rollback()
        raise


def dispatch_reminders(*, clock=utc_now, limit=100):
    """Run periodically; overdue notices are skipped, never sent retroactively.

    A T-6 notice is valid until T-1; T-1 until start. Creation omits past offsets.
    Locks match reservation/invalidation order. State and notification commit together.
    """
    now = naive(clock())
    ids = [r.id for r in EmergencyShiftReminder.query.filter_by(status='PENDING').filter(
        EmergencyShiftReminder.due_at <= now).order_by(EmergencyShiftReminder.id).limit(limit).all()]
    db.session.rollback()
    sent = 0
    for rid in ids:
        try:
            reminder = db.session.get(EmergencyShiftReminder, rid)
            shift = db.session.get(EmergencyShift, reminder.shift_id)
            professional = db.session.get(Professional, shift.professional_id)
            actor = professional.user_id
            user, professional = lock_owner(actor)
            shift = EmergencyShift.query.filter_by(id=shift.id).populate_existing().with_for_update().one()
            reminder = EmergencyShiftReminder.query.filter_by(id=rid).populate_existing().with_for_update().one()
            now = naive(clock())
            if reminder.status != 'PENDING' or reminder.due_at > now:
                db.session.rollback()
                continue
            expires = shift.starts_at - timedelta(hours=1) if reminder.kind == 'T_MINUS_6H' else shift.starts_at
            if shift.invalidated_at or not eligible(user, professional) or now >= expires:
                reminder.status = 'SKIPPED'
            else:
                crear_notificacion(actor, 'GUARDIA_RECORDATORIO', 'EMERGENCIAS', 'Tu guardia se aproxima',
                    'Revisá el horario de tu guardia en Mis guardias.', url_destino=DESTINATION,
                    entity_type='EmergencyShift', entity_id=shift.id, prioridad='RECORDATORIO', commit=False)
                reminder.status = 'SENT'
                sent += 1
            reminder.processed_at = now
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    return sent


def register_shift_cli(app):
    @app.cli.command('dispatch-shift-reminders')
    def dispatch():
        """Dispatch due internal shift reminders (schedule once a minute)."""
        import click
        click.echo(f'Recordatorios enviados: {dispatch_reminders()}')
