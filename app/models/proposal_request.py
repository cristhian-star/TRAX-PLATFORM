from datetime import datetime

from app import db


class ProposalRequest(db.Model):
    __tablename__ = "proposal_requests"

    HIRING_MODE_SINGLE = "SINGLE"
    HIRING_MODE_MULTIPLE = "MULTIPLE"

    HIRING_MODES = (
        HIRING_MODE_SINGLE,
        HIRING_MODE_MULTIPLE,
    )

    ESTADOS = (
        "PUBLICADA",
        "CERRADA",
        "CANCELADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    industria = db.Column(db.String(120))
    categoria = db.Column(db.String(120), nullable=False)
    rubro = db.Column(db.String(120))
    especialidad = db.Column(db.String(120))
    titulo = db.Column(db.String(160))
    descripcion = db.Column(db.Text)
    ubicacion = db.Column(db.String(120))
    modalidad = db.Column(db.String(80))
    cantidad_profesionales = db.Column(db.Integer, nullable=False, default=1)
    presupuesto_estimado = db.Column(db.Numeric(10, 2))
    fecha_inicio_estimada = db.Column(db.Date)
    fecha_limite_postulacion = db.Column(db.Date)
    fecha_limite = db.Column(db.DateTime)
    hiring_mode = db.Column(db.String(20), nullable=False, default=HIRING_MODE_SINGLE)
    estado = db.Column(db.String(50), nullable=False, default="PUBLICADA")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    owner = db.relationship("User", foreign_keys=[owner_user_id])
    applications = db.relationship(
        "ProposalApplication",
        back_populates="proposal",
        cascade="all, delete-orphan",
        lazy="select",
    )
