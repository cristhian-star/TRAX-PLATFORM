from app import db


class Professional(db.Model):
    __tablename__ = "professionals"

    WHATSAPP_CONTACT_AUTO = "AUTO"
    WHATSAPP_CONTACT_USERNAME = "USERNAME"
    WHATSAPP_CONTACT_PHONE = "PHONE"

    WHATSAPP_CONTACT_PREFERENCES = (
        WHATSAPP_CONTACT_AUTO,
        WHATSAPP_CONTACT_USERNAME,
        WHATSAPP_CONTACT_PHONE,
    )

    ESTADOS_PERFIL = (
        "INCOMPLETO",
        "PENDIENTE_VERIFICACION",
        "OBSERVADO",
        "VERIFICADO",
        "RECHAZADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    user = db.relationship("User", back_populates="professional_profile")
    nombre = db.Column(db.String(120), nullable=False)
    servicio = db.Column(db.String(120), nullable=False)
    zona = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    especialidad = db.Column(db.String(120))
    anios_experiencia = db.Column(db.Integer)
    tipo_credencial = db.Column(db.String(120))
    numero_credencial = db.Column(db.String(120))
    certificaciones_text = db.Column(db.Text)
    portfolio_urls = db.Column(db.Text)
    logo_url = db.Column(db.Text)
    cover_url = db.Column(db.Text)
    gallery_urls = db.Column(db.Text)
    google_drive_url = db.Column(db.Text)
    website_url = db.Column(db.Text)
    instagram_url = db.Column(db.Text)
    tiktok_url = db.Column(db.Text)
    youtube_url = db.Column(db.Text)
    other_links = db.Column(db.Text)
    whatsapp_username = db.Column(db.String(64))
    whatsapp_contact_preference = db.Column(db.String(20), nullable=False, default=WHATSAPP_CONTACT_AUTO)
    coverage_location = db.Column(db.String(160))
    coverage_city = db.Column(db.String(120))
    coverage_province = db.Column(db.String(120))
    coverage_radius_km = db.Column(db.Integer)
    coverage_mode = db.Column(db.String(50))
    coverage_notes = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    coverage_location_consent_at = db.Column(db.DateTime)
    estado_perfil = db.Column(db.String(50), nullable=False, default="INCOMPLETO")
    perfil_completo = db.Column(db.Boolean, nullable=False, default=False)
