from app import db
from app.models.professional import Professional


def get_professional_by_user_id(user_id):
    return Professional.query.filter_by(user_id=user_id).first()


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

def complete_professional_profile(
    user_id,
    nombre,
    especialidad,
    anios_experiencia=None,
    tipo_credencial=None,
    numero_credencial=None,
    certificaciones_text=None,
    portfolio_urls=None,
):
    professional = get_professional_by_user_id(user_id)

    if professional is None:
        professional = Professional(
            user_id=user_id,
            nombre=nombre,
            servicio=especialidad,
            zona="Sin definir",
        )
        db.session.add(professional)

    professional.especialidad = especialidad
    professional.servicio = especialidad
    professional.anios_experiencia = anios_experiencia
    professional.tipo_credencial = tipo_credencial
    professional.numero_credencial = numero_credencial
    professional.certificaciones_text = certificaciones_text
    professional.portfolio_urls = portfolio_urls
    professional.estado_perfil = "PENDIENTE_VERIFICACION"
    professional.perfil_completo = True

    db.session.commit()

    return professional
