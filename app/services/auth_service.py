from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.user import User


ALLOWED_PUBLIC_REGISTRATION_ROLES = {"CLIENTE", "PROFESIONAL"}


def register_user(nombre, email, password, rol="CLIENTE"):
    if rol not in ALLOWED_PUBLIC_REGISTRATION_ROLES:
        return None

    normalized_email = (email or "").strip().lower()
    existing_user = User.query.filter_by(email=normalized_email).first()

    if existing_user:
        return None

    user = User(
        nombre=nombre,
        email=normalized_email,
        password=generate_password_hash(password),
        rol=rol
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None

    return user


def authenticate_user(email, password):
    normalized_email = (email or "").strip().lower()
    user = User.query.filter_by(email=normalized_email).first()

    if user and check_password_hash(user.password, password):
        return user

    return None
