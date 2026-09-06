import re
from dataclasses import dataclass, field

from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.terms_acceptance import TermsAcceptance
from app.models.user import User
from app.services.user_service import is_user_active


ALLOWED_PUBLIC_REGISTRATION_ROLES = {"CLIENTE", "PROFESIONAL"}
CURRENT_TERMS_VERSION = "2026-07"
CURRENT_TERMS_TYPE = "terms_and_privacy"
MIN_PASSWORD_LENGTH = 8
MAX_NAME_LENGTH = 120
MAX_EMAIL_LENGTH = 120
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class AuthValidationResult:
    valid: bool
    values: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)
    general_error: str | None = None


def normalize_email(email):
    return (email or "").strip().lower()


def validate_password(password):
    password = password or ""
    if len(password) < MIN_PASSWORD_LENGTH:
        return "La contraseña debe tener al menos 8 caracteres."

    return None


def validate_login_form(form):
    email = normalize_email(form.get("email"))
    password = form.get("password") or ""
    errors = {}

    if not email:
        errors["email"] = "Ingresa tu email."
    elif len(email) > MAX_EMAIL_LENGTH or not EMAIL_PATTERN.match(email):
        errors["email"] = "Ingresa un email valido."

    if not password:
        errors["password"] = "Ingresa tu contraseña."

    return AuthValidationResult(
        valid=not errors,
        values={"email": email, "password": password},
        errors=errors,
    )


def validate_registration_form(form):
    nombre = (form.get("nombre") or "").strip()
    email = normalize_email(form.get("email"))
    password = form.get("password") or ""
    password_confirm = form.get("password_confirm") or ""
    rol = form.get("rol") or "CLIENTE"
    terms_accepted = form.get("terms_accepted") == "on"
    errors = {}

    if not nombre:
        errors["nombre"] = "Ingresa tu nombre."
    elif len(nombre) > MAX_NAME_LENGTH:
        errors["nombre"] = "El nombre no puede superar 120 caracteres."

    if not email:
        errors["email"] = "Ingresa tu email."
    elif len(email) > MAX_EMAIL_LENGTH or not EMAIL_PATTERN.match(email):
        errors["email"] = "Ingresa un email valido."

    password_error = validate_password(password)
    if password_error:
        errors["password"] = password_error

    if not password_confirm:
        errors["password_confirm"] = "Confirma tu contraseña."
    elif password and password_confirm != password:
        errors["password_confirm"] = "Las contraseñas no coinciden."

    if rol not in ALLOWED_PUBLIC_REGISTRATION_ROLES:
        errors["rol"] = "Selecciona un tipo de cuenta valido."

    if not terms_accepted:
        errors["terms_accepted"] = "Acepta los términos y la privacidad para continuar."

    values = {
        "nombre": nombre,
        "email": email,
        "password": password,
        "rol": rol,
        "terms_accepted": terms_accepted,
    }
    return AuthValidationResult(valid=not errors, values=values, errors=errors)


def register_user(nombre, email, password, rol="CLIENTE", ip_address=None, user_agent=None, terms_accepted=False):
    form_result = validate_registration_form({
        "nombre": nombre,
        "email": email,
        "password": password,
        "password_confirm": password,
        "rol": rol,
        "terms_accepted": "on" if terms_accepted else "",
    })
    if not form_result.valid:
        return None

    normalized_email = form_result.values["email"]
    if User.query.filter_by(email=normalized_email).first():
        return None

    user = User(
        nombre=form_result.values["nombre"],
        email=normalized_email,
        password=generate_password_hash(password),
        rol=form_result.values["rol"],
    )

    try:
        db.session.add(user)
        db.session.flush()
        db.session.add(TermsAcceptance(
            user_id=user.id,
            tipo_termino=CURRENT_TERMS_TYPE,
            version=CURRENT_TERMS_VERSION,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:255] or None,
        ))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None
    except Exception:
        db.session.rollback()
        raise

    return user


def register_user_from_form(form, ip_address=None, user_agent=None):
    result = validate_registration_form(form)
    if not result.valid:
        return result, None

    if User.query.filter_by(email=result.values["email"]).first():
        result.valid = False
        result.errors["email"] = "No pudimos crear la cuenta con esos datos."
        result.general_error = "Revisá los datos ingresados o iniciá sesión si ya tenés cuenta."
        return result, None

    user = register_user(
        result.values["nombre"],
        result.values["email"],
        result.values["password"],
        result.values["rol"],
        ip_address=ip_address,
        user_agent=user_agent,
        terms_accepted=True,
    )
    if user is None:
        result.valid = False
        result.general_error = "No pudimos crear la cuenta con esos datos."
        return result, None

    return result, user


def authenticate_user(email, password):
    normalized_email = normalize_email(email)
    user = User.query.filter_by(email=normalized_email).first()

    if user and is_user_active(user) and check_password_hash(user.password, password or ""):
        return user

    return None
