from app import db
from app.models.emergency_request import EmergencyRequest


ACTIVE_STATUSES = (
    "ABIERTA",
    "ASIGNADA",
    "EN_CAMINO",
)


def create_emergency_request(cliente_id, categoria, descripcion, zona, prioridad):
    emergency_request = EmergencyRequest(
        cliente_id=cliente_id,
        categoria=categoria,
        descripcion=descripcion,
        zona=zona,
        prioridad=prioridad
    )

    db.session.add(emergency_request)
    db.session.commit()

    return emergency_request


def get_active_emergencies():
    return (
        EmergencyRequest.query
        .filter(EmergencyRequest.estado.in_(ACTIVE_STATUSES))
        .order_by(EmergencyRequest.fecha_creacion.desc())
        .all()
    )


def assign_professional(emergency_request_id, professional_id=None):
    emergency_request = EmergencyRequest.query.get(emergency_request_id)

    if emergency_request is None:
        return None

    if hasattr(emergency_request, "professional_id"):
        emergency_request.professional_id = professional_id

    emergency_request.estado = "ASIGNADA"
    db.session.commit()

    return emergency_request


def update_emergency_status(emergency_request_id, estado):
    if estado not in EmergencyRequest.ESTADOS:
        raise ValueError("Estado de emergencia invalido")

    emergency_request = EmergencyRequest.query.get(emergency_request_id)

    if emergency_request is None:
        return None

    emergency_request.estado = estado
    db.session.commit()

    return emergency_request
