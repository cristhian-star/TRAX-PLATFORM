from urllib.parse import urlsplit

from flask import Blueprint, redirect, render_template, request, session

from app import limiter
from app.services.auth_service import (
    authenticate_user,
    register_user_from_form,
    validate_login_form,
)
from app.utils.security import ip_rate_limit_key

auth = Blueprint("auth", __name__)


def _safe_next_url(value):
    if not value:
        return None

    parsed = urlsplit(value)

    if (
        parsed.scheme
        or parsed.netloc
        or not value.startswith("/")
        or value.startswith("//")
        or "\\" in value
    ):
        return None

    return value


def _start_session(user):
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    session["user_name"] = user.nombre
    session["user_role"] = user.rol


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"], key_func=ip_rate_limit_key)
def register():
    next_url = _safe_next_url(request.values.get("next"))

    if request.method == "POST":
        result, user = register_user_from_form(
            request.form,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )

        if user is None:
            return render_template(
                "register.html",
                error=result.general_error or "Revisa los datos para crear tu cuenta.",
                errors=result.errors,
                form_values=result.values,
                next_url=next_url,
            ), 400

        _start_session(user)

        if user.rol == "PROFESIONAL":
            return redirect("/profesional/perfil/completar")

        return redirect(next_url or "/")

    return render_template(
        "register.html",
        next_url=next_url,
        errors={},
        form_values={"rol": "CLIENTE"},
    )


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes", methods=["POST"], key_func=ip_rate_limit_key)
def login():
    next_url = _safe_next_url(request.values.get("next"))

    if request.method == "POST":
        result = validate_login_form(request.form)
        if not result.valid:
            return render_template(
                "login.html",
                error="Revisa los datos para continuar.",
                errors=result.errors,
                form_values=result.values,
                next_url=next_url,
            ), 400

        user = authenticate_user(result.values["email"], result.values["password"])

        if user is None:
            return render_template(
                "login.html",
                error="No pudimos validar esos datos. Revisa el email o la contrasena.",
                errors={"credentials": "No pudimos validar esos datos."},
                form_values={"email": result.values["email"]},
                next_url=next_url,
            ), 401

        _start_session(user)

        return redirect(next_url or "/")

    return render_template("login.html", next_url=next_url, errors={}, form_values={})


@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")
