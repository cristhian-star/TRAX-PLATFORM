from app import db


class ProposalRequest(db.Model):
    __tablename__ = "proposal_requests"

    ESTADOS = (
        "ABIERTA",
        "RECIBIENDO_PROPUESTAS",
        "ADJUDICADA",
        "CERRADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    categoria = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    presupuesto_estimado = db.Column(db.Numeric(10, 2))
    fecha_limite = db.Column(db.DateTime)
    estado = db.Column(db.String(50), nullable=False, default="ABIERTA")
