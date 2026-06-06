from urllib.parse import urlsplit

from flask import Blueprint, render_template, request, redirect, session, url_for
from app.services.auth_service import register_user, authenticate_user
from app import limiter

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


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def register():
    next_url = _safe_next_url(request.values.get("next"))

    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        rol = request.form.get("rol", "CLIENTE")

        user = register_user(nombre, email, password, rol)

        if user is None:
            return render_template(
                "register.html",
                error="Este email ya está registrado. Iniciá sesión o usá otro email.",
                next_url=next_url,
            )

        if next_url:
            return redirect(url_for("auth.login", next=next_url))

        return redirect("/login")

    return render_template("register.html", next_url=next_url)


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login():
    next_url = _safe_next_url(request.values.get("next"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = authenticate_user(email, password)

        if user is None:
            return render_template(
                "login.html",
                error="Credenciales incorrectas",
                next_url=next_url,
            )

        session["user_id"] = user.id
        session["user_name"] = user.nombre
        session["user_role"] = user.rol

        return redirect(next_url or "/")

    return render_template("login.html", next_url=next_url)


@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")
