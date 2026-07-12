from datetime import datetime

from app import db
from app.models.activity_notification import ActivityNotification


CATEGORIA_PRESUPUESTOS = "PRESUPUESTOS"
CATEGORIA_EMERGENCIAS = "EMERGENCIAS"
CATEGORIA_PROPUESTAS = "PROPUESTAS"
CATEGORIA_CONTRATACIONES = "CONTRATACIONES"
CATEGORIA_CUENTA = "CUENTA"
CATEGORIA_SISTEMA = "SISTEMA"

CATEGORIAS = (
    CATEGORIA_PRESUPUESTOS,
    CATEGORIA_EMERGENCIAS,
    CATEGORIA_PROPUESTAS,
    CATEGORIA_CONTRATACIONES,
    CATEGORIA_CUENTA,
    CATEGORIA_SISTEMA,
)

PRIORIDAD_INFO = "INFO"
PRIORIDAD_RECORDATORIO = "RECORDATORIO"
PRIORIDAD_ACCION_REQUERIDA = "ACCION_REQUERIDA"

PRIORIDADES = (
    PRIORIDAD_INFO,
    PRIORIDAD_RECORDATORIO,
    PRIORIDAD_ACCION_REQUERIDA,
)

TIPO_PRESUPUESTO_PUBLICADO = "PRESUPUESTO_PUBLICADO"
TIPO_PRESUPUESTO_OFERTA_ENVIADA = "PRESUPUESTO_OFERTA_ENVIADA"
TIPO_PRESUPUESTO_OFERTA_RECIBIDA = "PRESUPUESTO_OFERTA_RECIBIDA"
TIPO_PRESUPUESTO_ADJUDICADO_CLIENTE = "PRESUPUESTO_ADJUDICADO_CLIENTE"
TIPO_PRESUPUESTO_ADJUDICADO_PROFESIONAL = "PRESUPUESTO_ADJUDICADO_PROFESIONAL"
TIPO_PRESUPUESTO_CANCELADO = "PRESUPUESTO_CANCELADO"
TIPO_PROPUESTA_PUBLICADA = "PROPUESTA_PUBLICADA"
TIPO_PROPUESTA_POSTULACION_ENVIADA = "PROPUESTA_POSTULACION_ENVIADA"
TIPO_PROPUESTA_POSTULACION_RECIBIDA = "PROPUESTA_POSTULACION_RECIBIDA"
TIPO_PROPUESTA_POSTULACION_ACEPTADA = "PROPUESTA_POSTULACION_ACEPTADA"
TIPO_PROPUESTA_POSTULACION_DESCARTADA = "PROPUESTA_POSTULACION_DESCARTADA"
TIPO_PROPUESTA_CANCELADA = "PROPUESTA_CANCELADA"
TIPO_EMERGENCIA_PUBLICADA = "EMERGENCIA_PUBLICADA"
TIPO_CUENTA_VERIFICADA = "CUENTA_VERIFICADA"
TIPO_PLAN_ACTUALIZADO = "PLAN_ACTUALIZADO"


def _validate_choice(value, allowed_values, field_label):
    if value not in allowed_values:
        raise ValueError(f"{field_label} invalido")


def crear_notificacion(
    user_id,
    tipo,
    categoria,
    titulo,
    mensaje,
    actor_user_id=None,
    url_destino=None,
    entity_type=None,
    entity_id=None,
    prioridad=PRIORIDAD_INFO,
    requiere_accion=False,
    commit=True,
):
    _validate_choice(categoria, CATEGORIAS, "Categoria")
    _validate_choice(prioridad, PRIORIDADES, "Prioridad")

    notification = ActivityNotification(
        user_id=user_id,
        actor_user_id=actor_user_id,
        tipo=tipo,
        categoria=categoria,
        titulo=titulo,
        mensaje=mensaje,
        url_destino=url_destino,
        entity_type=entity_type,
        entity_id=entity_id,
        prioridad=prioridad,
        requiere_accion=requiere_accion,
    )
    db.session.add(notification)

    if commit:
        db.session.commit()

    return notification


def registrar_evento(**kwargs):
    return crear_notificacion(**kwargs)


def obtener_notificaciones_usuario(user_id, filtro=None, limit=None, solo_no_leidas=False):
    query = ActivityNotification.query.filter_by(user_id=user_id)

    if solo_no_leidas:
        query = query.filter_by(leida=False)

    if filtro == "no-leidas":
        query = query.filter_by(leida=False)
    elif filtro == "accion":
        query = query.filter_by(requiere_accion=True)
    elif filtro == "info":
        query = query.filter_by(prioridad=PRIORIDAD_INFO)
    elif filtro == "recordatorios":
        query = query.filter_by(prioridad=PRIORIDAD_RECORDATORIO)

    query = query.order_by(ActivityNotification.created_at.desc(), ActivityNotification.id.desc())

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def obtener_no_leidas(user_id):
    return ActivityNotification.query.filter_by(user_id=user_id, leida=False).count()


def marcar_como_leida(notification_id, user_id):
    notification = ActivityNotification.query.filter_by(
        id=notification_id,
        user_id=user_id,
    ).first()

    if notification is None:
        return None

    if not notification.leida:
        notification.leida = True
        notification.read_at = datetime.utcnow()
        db.session.commit()

    return notification


def marcar_todas_como_leidas(user_id):
    notifications = ActivityNotification.query.filter_by(user_id=user_id, leida=False).all()
    now = datetime.utcnow()

    for notification in notifications:
        notification.leida = True
        notification.read_at = now

    db.session.commit()
    return len(notifications)


def formatear_fecha_notificacion(value):
    if not value:
        return "Sin fecha"

    return value.strftime("%d/%m/%Y")
