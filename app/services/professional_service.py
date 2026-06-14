from app import db
from app.models.professional import Professional
from app.models.user import User


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


def search_emergency_professionals(categoria="", zona=""):
    query = (
        Professional.query
        .join(User, Professional.user_id == User.id)
        .filter(
            User.estado == "ACTIVO",
            Professional.perfil_completo.is_(True),
        )
    )

    if categoria:
        query = query.filter(
            db.or_(
                Professional.servicio.ilike(f"%{categoria}%"),
                Professional.especialidad.ilike(f"%{categoria}%"),
            )
        )

    if zona:
        query = query.filter(Professional.zona.ilike(f"%{zona}%"))

    return query.order_by(Professional.nombre.asc()).all()


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
    logo_url=None,
    cover_url=None,
    gallery_urls=None,
    google_drive_url=None,
    website_url=None,
    instagram_url=None,
    tiktok_url=None,
    youtube_url=None,
    other_links=None,
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
    professional.logo_url = logo_url
    professional.cover_url = cover_url
    professional.gallery_urls = gallery_urls
    professional.google_drive_url = google_drive_url
    professional.website_url = website_url
    professional.instagram_url = instagram_url
    professional.tiktok_url = tiktok_url
    professional.youtube_url = youtube_url
    professional.other_links = other_links
    professional.estado_perfil = "PENDIENTE_VERIFICACION"
    professional.perfil_completo = True

    db.session.commit()

    return professional
