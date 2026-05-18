from flask import Blueprint, render_template, request, redirect, session
from app.services.auth_service import register_user, authenticate_user
from app import limiter

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        rol = request.form.get("rol", "CLIENTE")

        user = register_user(nombre, email, password, rol)

        if user is None:
            return render_template(
                "register.html",
                error="Este email ya está registrado. Iniciá sesión o usá otro email."
            )

        return redirect("/login")

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = authenticate_user(email, password)

        if user is None:
            return "Credenciales incorrectas"

        session["user_id"] = user.id
        session["user_name"] = user.nombre
        session["user_role"] = user.rol

        return redirect("/")

    return render_template("login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")
