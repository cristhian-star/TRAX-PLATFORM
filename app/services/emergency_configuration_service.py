"""Owner-scoped configuration and reviewed coverage impact in one transaction."""
import hashlib
import json
import re
import secrets
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import current_app
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer, BadSignature, SignatureExpired
from app import db
from app.models.professional import Professional
from app.models.user import User
from app.models.emergency_configuration import EmergencyConfiguration
from app.models.emergency_shift import EmergencyShift
from app.models.operation_command import OperationCommand
from app.models.audit_log import AuditLog
from app.services.coverage_service import normalizar_cobertura
from app.services.emergency_reservation_service import lock_owner, invalidate_locked, naive
from app.services.pro_time import utc_now

OPERATION = 'EMERGENCY_CONFIG_SAVE'
IMPACT_MAX_AGE_SECONDS = 900
IMPACT_EXPIRED_MESSAGE = 'La revisión venció. Revisá nuevamente las guardias afectadas antes de confirmar'
COVERAGE = ('coverage_location','coverage_city','coverage_province','coverage_mode',
            'coverage_radius_km','coverage_notes','latitude','longitude','coverage_location_consent_at')
AMOUNTS = ('package_amount','visit_amount','diagnosis_amount')


class ConfigurationConflict(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def signer(salt):
    serializer = URLSafeTimedSerializer if salt == 'review' else URLSafeSerializer
    return serializer(current_app.config['SECRET_KEY'], salt=OPERATION + salt)


def authorize(user, professional):
    if not user or user.rol != 'PROFESIONAL' or user.estado != 'ACTIVO' or not professional:
        raise PermissionError('Necesitás una cuenta profesional activa y un perfil propio.')


def snapshot(professional, config):
    return digest({**{key:getattr(professional,key) for key in COVERAGE},
        'service':professional.servicio, 'state':professional.estado_perfil,
        'complete':professional.perfil_completo, 'version':config.version if config else 0})


def initial(actor):
    user = db.session.get(User, actor)
    professional = Professional.query.filter_by(user_id=actor).first()
    authorize(user, professional)
    config = db.session.get(EmergencyConfiguration, professional.id)
    values = {key: getattr(professional,key) if getattr(professional,key) is not None else '' for key in COVERAGE}
    values.update(mode=config.mode if config else 'PACKAGE', notes=config.notes if config else '',
                  discount_repair='on' if config and config.discount_repair else '', coordinate_action='keep')
    for field in AMOUNTS:
        amount = getattr(config,field) if config else None
        values[field] = str(amount) if amount is not None else ''
        values[field + '_free'] = 'on' if amount == 0 else ''
    values['form_key'] = signer('form').dumps([actor, secrets.token_hex(12), snapshot(professional,config)])
    return professional, values


def amount(form, field):
    if form.get(field + '_free') == 'on':
        return Decimal('0.00')
    raw = form.get(field, '').strip()
    if not raw:
        return None  # Missing is not free.
    if len(raw) > 13 or not re.fullmatch(r'[0-9]{1,10}([.,][0-9]{1,2})?', raw):
        raise ValueError('Usá importes ARS sin separadores de miles y con hasta dos decimales.')
    value = Decimal(raw.replace(',', '.'))
    if not value.is_finite() or not Decimal('0') < value <= Decimal('9999999999.99'):
        raise ValueError('El importe debe ser positivo; para gratuidad marcá Sin cargo.')
    return value.quantize(Decimal('.01'))


def tariff(form):
    mode = form.get('mode')
    if mode not in ('PACKAGE','SEPARATE'):
        raise ValueError('Elegí una modalidad de precio.')
    notes = form.get('notes', '').strip()
    if len(notes) > 2000:
        raise ValueError('Las aclaraciones admiten hasta 2000 caracteres.')
    applicable = ('package_amount',) if mode == 'PACKAGE' else ('visit_amount','diagnosis_amount')
    return dict(mode=mode, notes=notes, discount_repair=form.get('discount_repair') == 'on',
                repair_materials_separate=True, **{f:amount(form,f) if f in applicable else None for f in AMOUNTS})


def coverage(form, professional):
    old = {key:getattr(professional,key) for key in COVERAGE}
    merged = {key:form.get(key, old[key]) for key in COVERAGE if key not in ('latitude','longitude','coverage_location_consent_at')}
    # Normalizer accepts integer strings, including existing native integer radius.
    normalized = normalizar_cobertura(merged)
    # Preserve an unset mode on unrelated saves instead of defaulting it to RADIO.
    if 'coverage_mode' not in form or not form.get('coverage_mode') and old['coverage_mode'] is None:
        normalized['coverage_mode'] = old['coverage_mode']
    for key in ('latitude','longitude','coverage_location_consent_at'):
        normalized[key] = old[key]
    action = form.get('coordinate_action', 'keep')
    if action == 'remove':
        for key in ('latitude','longitude','coverage_location_consent_at'):
            normalized[key] = None
    elif action == 'update':
        if form.get('coverage_location_consent') != 'on' or not form.get('latitude') or not form.get('longitude'):
            raise ValueError('Elegí un centro y aceptá expresamente el uso de su ubicación.')
        coords = normalizar_cobertura({**merged, 'latitude':form['latitude'], 'longitude':form['longitude'], 'coverage_location_consent':'on'})
        normalized['latitude'], normalized['longitude'] = coords['latitude'], coords['longitude']
        # Timestamp is assigned only at the atomic save, never during review.
        normalized['coverage_location_consent_at'] = old['coverage_location_consent_at'] or 'ACCEPT_ON_SAVE'
    elif action != 'keep':
        raise ValueError('Acción de ubicación inválida.')
    return normalized


def affected(professional, instant):
    return EmergencyShift.query.filter(EmergencyShift.professional_id == professional.id,
        EmergencyShift.invalidated_at.is_(None), EmergencyShift.ends_at > naive(instant)).order_by(EmergencyShift.id).with_for_update().all()


def impact_label(shift):
    start = shift.starts_at.replace(tzinfo=timezone.utc)
    try:
        label = start.astimezone(ZoneInfo('America/Argentina/Buenos_Aires')).strftime('%d/%m/%Y %H:%M') + ' · Buenos Aires'
    except ZoneInfoNotFoundError:
        label = start.strftime('%d/%m/%Y %H:%M') + ' UTC (hora local no disponible)'
    return dict(id=shift.id, start=label, kind='Diurna' if shift.kind == 'GUARDIA_DIURNA' else 'Nocturna')


def save(actor, form, *, clock=None):
    try:
        user, professional = lock_owner(actor)
        authorize(user,professional)
        key = form.get('form_key','')
        try:
            if not isinstance(key, str) or len(key) > 500:
                raise ValueError
            signed = signer('form').loads(key)
            if len(key) > 500 or not isinstance(signed,list) or len(signed) != 3 or signed[0] != actor:
                raise ValueError
        except (BadSignature, ValueError, TypeError):
            raise ValueError('Formulario inválido. Volvé a abrir Configuración de urgencias.') from None
        # Hash only applicable tariff fields; irrelevant mode fields have no effect.
        prices = tariff(form)
        payload = {**prices, **{k:form[k] for k in (*COVERAGE,'coordinate_action','coverage_location_consent') if k in form and k != 'coverage_location_consent_at'}}
        payload_hash = digest(payload)
        command_key = digest(key)
        command = OperationCommand.query.filter_by(actor_user_id=actor, operation=OPERATION, idempotency_key=command_key).with_for_update().first()
        if command:
            if command.status != 'SUCCEEDED' or command.payload_hash != payload_hash:
                raise ConfigurationConflict('Este formulario ya se usó con otros datos. Volvé a abrir la configuración.')
            db.session.rollback()
            return {'saved':True, 'replay':True}
        config = EmergencyConfiguration.query.filter_by(professional_id=professional.id).populate_existing().with_for_update().first()
        if signed[2] != snapshot(professional,config):
            raise ConfigurationConflict('Tu perfil o configuración cambió. Volvé a abrir la pantalla antes de guardar.')
        proposed = coverage(form,professional)
        changed = any(getattr(professional,k) != v for k,v in proposed.items())
        instant = (clock or utc_now)()
        shifts = affected(professional,instant) if changed else []
        impact = [[s.id,s.version] for s in shifts]
        review_payload = [actor,signed[2],payload_hash,impact]
        # Validate only new mutations, after owner/configuration/affected-shift locks.
        # TimedSigner uses integer server seconds: ages 0..900 inclusive are valid;
        # future timestamps, legacy untimed tokens and ages >=901 are rejected.
        # Even an obsolete review whose shifts have ended must not authorize a save.
        if shifts or form.get('impact_key'):
            review_error = None
            try:
                reviewed = signer('review').loads(form.get('impact_key',''), max_age=IMPACT_MAX_AGE_SECONDS)
            except SignatureExpired:
                reviewed = None
                review_error = IMPACT_EXPIRED_MESSAGE
            except BadSignature:
                reviewed = None
                if form.get('impact_key'):
                    review_error = 'La revisión no es válida. Revisá nuevamente las guardias afectadas antes de confirmar'
            if reviewed != review_payload or form.get('accept_impact') != 'on':
                result = {'saved':False, 'impact_key':signer('review').dumps(review_payload),
                    'impact':[impact_label(s) for s in shifts], 'error':review_error}
                db.session.rollback()
                return result
        if changed:
            invalidate_locked(professional,actor,clock=lambda:instant)
            for field,value in proposed.items():
                setattr(professional,field,naive(instant) if value == 'ACCEPT_ON_SAVE' else value)
        if not config:
            config = EmergencyConfiguration(professional_id=professional.id,version=1)
            db.session.add(config)
        elif any(getattr(config,k) != v for k,v in prices.items()):
            config.version += 1
        for field,value in prices.items():
            setattr(config,field,value)
        correlation = str(uuid.uuid4())
        audit = AuditLog(actor_user_id=actor,target_user_id=actor,action=OPERATION,correlation_id=correlation,
            entity_type='EmergencyConfiguration',entity_id=professional.id,
            operation=OPERATION,idempotency_key=command_key,
            metadata_json={'coverage_changed':changed,'invalidated_shifts':impact,'configuration_version':config.version})
        db.session.add(audit); db.session.flush()
        db.session.add(OperationCommand(actor_user_id=actor,operation=OPERATION,idempotency_key=command_key,
            payload_hash=payload_hash,status='SUCCEEDED',correlation_id=correlation,result_entity_type='AuditLog',result_entity_id=audit.id,completed_at=naive(instant)))
        db.session.commit()
        return {'saved':True, 'replay':False}
    except Exception:
        db.session.rollback()
        raise
