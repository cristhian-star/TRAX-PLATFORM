"""Version-bound voluntary release; caller cannot release a later reservation."""
import hashlib
import uuid
from datetime import timedelta
from flask import current_app
from itsdangerous import URLSafeSerializer, BadSignature
from app import db
from app.models.emergency_shift import EmergencyShift, EmergencyShiftReminder
from app.models.operation_command import OperationCommand
from app.models.audit_log import AuditLog
from app.services import emergency_reservation_service as reservations
from app.services.pro_time import utc_now

OPERATION = 'EMERGENCY_SHIFT_RELEASE'


def release_deadline(shift):
    return shift.starts_at - timedelta(hours=12)


def issue_release_key(actor, shift):
    return URLSafeSerializer(current_app.config['SECRET_KEY'], salt=OPERATION).dumps(
        [actor, shift.id, shift.version])


def released_versions(actor, ids):
    """Durable release reasons, separate from eligibility invalidation."""
    if not ids:
        return set()
    events = AuditLog.query.filter_by(actor_user_id=actor, action=OPERATION,
        entity_type='EmergencyShift').filter(AuditLog.entity_id.in_(ids)).all()
    return {(event.entity_id, (event.metadata_json or {}).get('released_version')) for event in events}


def release(actor, shift_id, key, *, clock=None):
    try:
        user, professional = reservations.lock_owner(actor)
        if not reservations.eligible(user, professional):
            raise PermissionError('Tu cuenta no está habilitada para gestionar guardias.')
        shift = EmergencyShift.query.filter_by(id=shift_id, professional_id=professional.id).populate_existing().with_for_update().first()
        if not shift:
            raise PermissionError('No podés gestionar este turno.')
        try:
            if not isinstance(key, str) or len(key) > 160:
                raise ValueError
            payload = URLSafeSerializer(current_app.config['SECRET_KEY'], salt=OPERATION).loads(key)
            if not isinstance(payload, list) or len(payload) != 3 or payload[:2] != [actor, shift_id] or type(payload[2]) is not int:
                raise ValueError
        except (BadSignature, TypeError, ValueError):
            raise ValueError('Formulario inválido. Recargá Mis guardias.') from None
        command = OperationCommand.query.filter_by(actor_user_id=actor, operation=OPERATION,
            idempotency_key=key).with_for_update().first()
        if command:
            audit = db.session.get(AuditLog, command.result_entity_id)
            if command.status != 'SUCCEEDED' or command.result_entity_type != 'AuditLog' or not audit or audit.actor_user_id != actor or audit.entity_id != shift_id:
                raise reservations.ReservationConflict('No se pudo recuperar la liberación original.')
            result = dict(audit.metadata_json)
            db.session.rollback()
            return result
        now = reservations.naive((clock or utc_now)())  # Effective time after owner/shift locks.
        if shift.version != payload[2] or shift.invalidated_at:
            raise reservations.ReservationConflict('El turno cambió. Recargá Mis guardias.')
        if now >= release_deadline(shift):
            raise ValueError('El plazo para liberar terminó: faltan 12 horas o menos para el inicio.')
        result = dict(shift_id=shift.id, released_version=shift.version + 1,
            released_at=now.isoformat(), accepted_at=shift.accepted_at.isoformat(),
            starts_at=shift.starts_at.isoformat(), ends_at=shift.ends_at.isoformat())
        shift.invalidated_at = now
        shift.version += 1
        for reminder in EmergencyShiftReminder.query.filter_by(shift_id=shift.id, status='PENDING').with_for_update().all():
            reminder.status = 'SKIPPED'
            reminder.processed_at = now
        command = OperationCommand(actor_user_id=actor, operation=OPERATION, idempotency_key=key,
            payload_hash=hashlib.sha256(key.encode()).hexdigest(), status='SUCCEEDED',
            correlation_id=str(uuid.uuid4()), completed_at=now, result_entity_type='AuditLog')
        audit = AuditLog(actor_user_id=actor, target_user_id=actor, action=OPERATION,
            entity_type='EmergencyShift', entity_id=shift.id, operation=OPERATION,
            correlation_id=command.correlation_id, idempotency_key=key, metadata_json=result)
        db.session.add(audit)
        db.session.flush()
        command.result_entity_id = audit.id
        db.session.add(command)
        reservations.crear_notificacion(actor, 'GUARDIA_LIBERADA', 'EMERGENCIAS', 'Liberación de guardia registrada',
            'El turno quedó liberado. Sus recordatorios pendientes se dejaron sin efecto.',
            url_destino=reservations.DESTINATION, commit=False)
        db.session.commit()
        return result
    except Exception:
        db.session.rollback()
        raise
