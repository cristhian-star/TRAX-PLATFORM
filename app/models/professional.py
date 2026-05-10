from app import db


class Professional(db.Model):
    __tablename__ = "professionals"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    servicio = db.Column(db.String(120), nullable=False)
    zona = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(50))
    descripcion = db.Column(db.Text)