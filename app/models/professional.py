from app import db


class Professional(db.Model):
    __tablename__ = "professionals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    user = db.relationship("User", back_populates="professional_profile")
    nombre = db.Column(db.String(120), nullable=False)
    servicio = db.Column(db.String(120), nullable=False)
    zona = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(50))
    descripcion = db.Column(db.Text)