from app import db


class CategoryRequest(db.Model):
    __tablename__ = "category_requests"

    id = db.Column(db.Integer, primary_key=True)
    nombre_rubro = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    email_notificacion = db.Column(db.String(120))
    estado = db.Column(db.String(50), default="PENDIENTE")