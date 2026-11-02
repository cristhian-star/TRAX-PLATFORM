"""Private work records. Owner lock serializes writes and reminder dispatch."""
import hashlib
import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from app import db
from app.models.user import User
from app.models.professional import Professional
from app.models.contract_request import ContractRequest
from app.models.work_record import WorkRecord, WorkFollowup, WorkReminder
from app.models.operation_command import OperationCommand
from app.models.audit_log import AuditLog
from app.services.pro_time import utc_now, as_utc_naive
from app.services.notification_service import crear_notificacion

LIMITS = dict(title=160, client_name=160, contact=254, location=300, notes=10000, reason=300)
ZONE = 'America/Argentina/Buenos_Aires'
OPERATION = 'PRIVATE_WORK_SAVE'
FOLLOW_FIELDS = ('enabled','reason','tentative_date','remind_self','remind_client','advance_days','notice_time')


class WorkConflict(ValueError):
    pass


def local_today(clock=utc_now):
    return clock().astimezone(ZoneInfo(ZONE)).date()


def authorize(actor, lock=False):
    query = User.query.filter_by(id=actor)
    if lock:
        query = query.populate_existing().with_for_update()
    user = query.first()
    if not user or user.rol != 'PROFESIONAL' or user.estado != 'ACTIVO':
        raise PermissionError('Acceso profesional requerido.')
    return user


def own_record(actor, record_id, lock=False):
    authorize(actor)
    query = WorkRecord.query.filter_by(id=record_id, owner_user_id=actor)
    if lock:
        query = query.populate_existing().with_for_update()
    row = query.first()
    if not row:
        raise LookupError('Registro no encontrado.')
    return row


def linked_client(actor, contract_id, lock=False):
    if not contract_id:
        return None
    prof = Professional.query.filter_by(user_id=actor).first()
    query = ContractRequest.query.filter_by(id=contract_id, professional_id=prof.id if prof else -1, professional_user_id=actor)
    if lock:
        query = query.populate_existing().with_for_update()
    contract = query.first()
    if not contract:
        raise ValueError('Cliente vinculado: seleccioná un contrato propio accesible.')
    client = db.session.get(User, contract.cliente_id)
    if not client or client.estado != 'ACTIVO' or client.rol != 'CLIENTE':
        raise ValueError('La cuenta del cliente vinculado no está disponible.')
    return client


def client_options(actor):
    authorize(actor)
    return db.session.query(ContractRequest.id, User.nombre).join(
        Professional, ContractRequest.professional_id == Professional.id).join(
        User, ContractRequest.cliente_id == User.id).filter(
        Professional.user_id == actor, ContractRequest.professional_user_id == actor, User.estado == 'ACTIVO', User.rol == 'CLIENTE').order_by(ContractRequest.id.desc()).all()


def flag(value):
    if value in (None, '', False):
        return False
    if value in (True, 'on', '1'):
        return True
    raise ValueError('Opción de seguimiento inválida.')


def parse_day(value, label):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(f'{label}: ingresá una fecha válida.') from None


def normalize(data):
    result = {}
    for name, limit in LIMITS.items():
        value = data.get(name, '')
        if not isinstance(value, str):
            raise ValueError(f'{name}: texto inválido.')
        value = value.strip()
        if len(value) > limit:
            raise ValueError(f'{name}: máximo {limit} caracteres.')
        if name in ('title','notes') and not value:
            raise ValueError('Completá el título y el registro del trabajo.')
        result[name] = value
    result['work_date'] = parse_day(data.get('work_date'), 'Fecha del trabajo')
    raw = data.get('contract_id') or ''
    if raw and (not str(raw).isascii() or not str(raw).isdigit() or len(str(raw)) > 10):
        raise ValueError('Cliente vinculado inválido.')
    result['contract_id'] = int(raw) if raw else None
    result['enabled'] = flag(data.get('enabled'))
    for name in ('remind_self','remind_client'):
        result[name] = flag(data.get(name)) if result['enabled'] else False
    if result['enabled']:
        if not result['reason']:
            raise ValueError('Completá el motivo del seguimiento.')
        result['tentative_date'] = parse_day(data.get('tentative_date'), 'Fecha tentativa')
        if str(data.get('advance_days','1')) not in ('0','1','7'):
            raise ValueError('Anticipación inválida.')
        result['advance_days'] = int(data.get('advance_days','1'))
        raw_time = data.get('notice_time','09:00')
        try:
            if not isinstance(raw_time, str) or len(raw_time) != 5:
                raise ValueError
            time.fromisoformat(raw_time)
        except ValueError:
            raise ValueError('Hora del aviso inválida.') from None
        result['notice_time'] = raw_time
    else:
        result.update(reason='', tentative_date=None, advance_days=1, notice_time='09:00')
    return result


def record_data(row):
    fields = ('title','work_date','client_name','contact','location','notes','contract_id')
    result = {n: getattr(row,n) for n in fields}
    f = row.followup
    result.update({n:getattr(f,n) for n in FOLLOW_FIELDS})
    return {k:(v.isoformat() if isinstance(v,date) else v) for k,v in result.items()}


def save_record(actor, data, key, record_id=None, expected_version=None, *, clock=utc_now):
    try:
        with db.session.no_autoflush:
            authorize(actor, lock=True)
            row = own_record(actor, record_id, lock=True) if record_id else None
            try:
                uuid.UUID(str(key))
            except (ValueError, TypeError, AttributeError):
                raise ValueError('Formulario inválido. Recargá la página.') from None
            values = normalize(data)
            payload = json.dumps([record_id, expected_version, values], sort_keys=True, default=str)
            digest = hashlib.sha256(payload.encode()).hexdigest()
            command = OperationCommand.query.filter_by(actor_user_id=actor,operation=OPERATION,idempotency_key=key).first()
            if command:
                if command.payload_hash != digest or command.status != 'SUCCEEDED':
                    raise WorkConflict('Este envío ya fue utilizado con otro contenido. Recargá el formulario.')
                return command.result_entity_id
            if row and str(expected_version) != str(row.version):
                raise WorkConflict('El registro cambió en otra sesión. Tus datos se conservaron; revisá la versión actual antes de editar nuevamente.')
            client = linked_client(actor, values['contract_id'], lock=True)
            if values['remind_client'] and not client:
                raise ValueError('Para avisar al cliente vinculá un contrato propio válido.')
            f = row.followup if row else None
            changed = not f or any(getattr(f,n) != values[n] for n in FOLLOW_FIELDS) or row.contract_id != values['contract_id']
            now = clock()
            due = None
            if changed and values['enabled']:
                if values['tentative_date'] < local_today(lambda: now):
                    raise ValueError('La fecha tentativa nueva no puede ser anterior a hoy.')
                if values['remind_self'] or values['remind_client']:
                    day = values['tentative_date'] - timedelta(days=values['advance_days'])
                    due = datetime.combine(day,time.fromisoformat(values['notice_time']),ZoneInfo(ZONE)).astimezone(timezone.utc)
                    if due <= now:
                        raise ValueError('El aviso debe ser futuro. Corregí fecha, anticipación u hora.')
            if not row:
                row = WorkRecord(owner_user_id=actor, created_at=as_utc_naive(now), version=1)
                db.session.add(row)
            else:
                row.version += 1
            for n in ('title','work_date','client_name','contact','location','notes','contract_id'):
                setattr(row,n,values[n])
            row.updated_at = as_utc_naive(now)
            db.session.flush()
            if changed:
                if f:
                    f.version += 1
                else:
                    f = WorkFollowup(record_id=row.id, version=1)
                    db.session.add(f)
                for n in FOLLOW_FIELDS:
                    setattr(f,n,values[n])
                pending = WorkReminder.query.filter_by(record_id=row.id,status='PENDING').with_for_update().all()
                for r in pending:
                    r.status='CANCELLED'; r.processed_at=as_utc_naive(now)
                if due:
                    for enabled, audience, recipient in ((values['remind_self'],'SELF',actor),(values['remind_client'],'CLIENT',client.id if client else None)):
                        if enabled:
                            db.session.add(WorkReminder(record_id=row.id,followup_version=f.version,recipient_id=recipient,audience=audience,due_at=as_utc_naive(due),status='PENDING'))
            db.session.add(AuditLog(actor_user_id=actor, action='PRIVATE_WORK_SAVED',entity_type='WorkRecord',entity_id=row.id))
            db.session.add(OperationCommand(actor_user_id=actor,operation=OPERATION,idempotency_key=key,payload_hash=digest,status='SUCCEEDED',result_entity_type='WorkRecord',result_entity_id=row.id,correlation_id=str(uuid.uuid4()),completed_at=as_utc_naive(now)))
            result = row.id
            db.session.commit()
            return result
    except Exception:
        db.session.rollback()
        raise


def list_records(actor, args):
    authorize(actor)
    values = {n:args.get(n,'').strip() for n in ('q','client','from','to','follow','page')}
    for n in values:
        if hasattr(args,'getlist') and len(args.getlist(n)) > 1:
            raise ValueError('No repitas los filtros.')
    if any(len(v)>160 for v in values.values()):
        raise ValueError('Filtro demasiado largo.')
    try:
        page = int(values['page'] or 1)
        if not 1 <= page <= 100000:
            raise ValueError
    except ValueError:
        raise ValueError('Página inválida.') from None
    if values['follow'] not in ('','with','without'):
        raise ValueError('Filtro de seguimiento inválido.')
    start = parse_day(values['from'],'Desde') if values['from'] else None
    end = parse_day(values['to'],'Hasta') if values['to'] else None
    if start and end and start>end:
        raise ValueError('Desde no puede ser posterior a Hasta.')
    query = WorkRecord.query.filter_by(owner_user_id=actor).join(WorkFollowup).options(joinedload(WorkRecord.followup))
    if values['q']:
        query=query.filter(or_(WorkRecord.title.contains(values['q'],autoescape=True), WorkRecord.notes.contains(values['q'],autoescape=True)))
    if values['client']:query=query.filter(WorkRecord.client_name.contains(values['client'],autoescape=True))
    if start:query=query.filter(WorkRecord.work_date>=start)
    if end:query=query.filter(WorkRecord.work_date<=end)
    if values['follow']:query=query.filter(WorkFollowup.enabled == (values['follow']=='with'))
    total=query.count()
    rows=query.order_by(WorkRecord.work_date.desc(),WorkRecord.id.desc()).offset((page-1)*10).limit(10).all()
    return dict(rows=rows,total=total,page=page,has_next=page*10<total,filters=values)


def dispatch_work_reminders(*, clock=utc_now, limit=100):
    now = as_utc_naive(clock())
    candidates = db.session.query(WorkReminder.id,WorkReminder.record_id,WorkRecord.owner_user_id).join(WorkRecord).filter(WorkReminder.status=='PENDING',WorkReminder.due_at<=now).order_by(WorkReminder.due_at,WorkReminder.id).limit(limit).all()
    db.session.rollback()
    sent=0
    for rid,record_id,actor in candidates:
        try:
            # Same lock order as saves: owner -> record -> contract -> reminder.
            user=User.query.filter_by(id=actor).populate_existing().with_for_update().first()
            row=WorkRecord.query.filter_by(id=record_id).populate_existing().with_for_update().one()
            f=WorkFollowup.query.filter_by(record_id=record_id).populate_existing().first()
            try:
                client=linked_client(actor,row.contract_id,lock=True)
            except ValueError:
                client=None
            r=WorkReminder.query.filter_by(id=rid).populate_existing().with_for_update().one()
            current=clock(); current_naive=as_utc_naive(current)
            if r.status!='PENDING' or r.due_at>current_naive:
                db.session.rollback(); continue
            valid=bool(user and user.rol=='PROFESIONAL' and user.estado=='ACTIVO' and f.enabled and r.followup_version==f.version and f.tentative_date>=local_today(lambda:current))
            valid=valid and ((r.audience=='SELF' and f.remind_self and r.recipient_id==actor) or (r.audience=='CLIENT' and f.remind_client and client and r.recipient_id==client.id))
            if valid:
                message=f'{user.nombre}: {f.reason}. Fecha tentativa: {f.tentative_date:%d/%m/%Y}. La visita se coordina con el cliente.'
                notification=crear_notificacion(r.recipient_id,'TRABAJO_SEGUIMIENTO','SISTEMA','Próximo seguimiento',message,actor_user_id=actor,
                    url_destino=f'/profesional/trabajos/registros/{row.id}' if r.audience=='SELF' else None,
                    prioridad='RECORDATORIO',commit=False)
                notification.idempotency_key=f'work-reminder:{r.id}'
                db.session.flush()
                r.notification_id=notification.id;r.status='SENT';sent+=1
            else:
                r.status='SKIPPED'
            r.processed_at=current_naive
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    return sent


def register_work_cli(app):
    @app.cli.command('dispatch-work-reminders')
    def dispatch():
        """Run every minute; notifications and delivery state commit atomically."""
        import click
        click.echo(f'Recordatorios enviados: {dispatch_work_reminders()}')
