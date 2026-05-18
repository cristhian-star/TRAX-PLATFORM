from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default="CLIENTE")
    professional_profile = db.relationship(
        "Professional",
        back_populates="user",
        uselist=False
    )
