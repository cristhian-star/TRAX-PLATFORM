from app import db
from app.models.professional import Professional


def create_professional(user_id, nombre, servicio, zona, telefono, descripcion):
    existing_professional = Professional.query.filter_by(user_id=user_id).first()

    if existing_professional:
        return None

    professional = Professional(
        user_id=user_id,
        nombre=nombre,
        servicio=servicio,
        zona=zona,
        telefono=telefono,
        descripcion=descripcion
    )

    db.session.add(professional)
    db.session.commit()

    return professional


def search_professionals(servicio="", zona=""):
    query = Professional.query

    if servicio:
        query = query.filter(Professional.servicio.ilike(f"%{servicio}%"))

    if zona:
        query = query.filter(Professional.zona.ilike(f"%{zona}%"))

    return query.all()


def get_professional_by_id(professional_id):
    return Professional.query.get(professional_id)