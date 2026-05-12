from flask import Blueprint, render_template, request, redirect
from app.services.category_service import (
    request_category,
    get_category_requests_summary,
    approve_category
)
from app.services.professional_service import (
    create_professional,
    search_professionals,
    get_professional_by_id
)
from app.utils.decorators import role_required

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("home.html")


@main.route("/buscar", methods=["GET"])
def buscar():
    servicio = request.args.get("servicio", "")
    zona = request.args.get("zona", "")

    resultados = search_professionals(servicio, zona)

    return render_template(
        "resultados.html",
        resultados=resultados,
        servicio=servicio,
        zona=zona
    )


@main.route("/resultados")
def listado_profesionales():
    servicio = request.args.get("servicio", "")
    zona = request.args.get("zona", "")

    resultados = search_professionals(servicio, zona)

    return render_template(
        "listado_profesionales.html",
        resultados=resultados,
        servicio=servicio,
        zona=zona
    )


@main.route("/mercados")
def mercados():
    return render_template("mercados.html")


@main.route("/profesional/dashboard")
@role_required("PROFESIONAL")
def profesional_dashboard():
    return render_template("profesional_dashboard.html")


@main.route("/cliente/dashboard")
@role_required("CLIENTE")
def cliente_dashboard():
    return render_template("cliente_dashboard.html")


@main.route("/admin/dashboard")
@role_required("SUPER_ADMIN")
def admin_dashboard():
    return render_template("admin_dashboard.html")


@main.route("/profesional/<int:id>")
def perfil_profesional(id):
    profesional = get_professional_by_id(id)

    if profesional is None:
        return "Profesional no encontrado", 404

    return render_template(
        "perfil_profesional.html",
        profesional=profesional
    )


@main.route("/profesionales/nuevo", methods=["GET"])
def nuevo_profesional():
    return render_template("nuevo_profesional.html")


@main.route("/profesionales/crear", methods=["POST"])
def guardar_profesional():
    nombre = request.form.get("nombre")
    servicio = request.form.get("servicio")
    zona = request.form.get("zona")
    telefono = request.form.get("telefono")
    descripcion = request.form.get("descripcion")

    create_professional(nombre, servicio, zona, telefono, descripcion)

    return "Profesional creado correctamente"


@main.route("/rubros/solicitar", methods=["POST"])
def guardar_solicitud_rubro():
    nombre_rubro = request.form.get("nombre_rubro")
    descripcion = request.form.get("descripcion_rubro")
    email_notificacion = request.form.get("email_notificacion")

    cantidad = request_category(
        nombre_rubro,
        descripcion,
        email_notificacion
    )

    return render_template(
        "rubro_solicitado.html",
        nombre_rubro=nombre_rubro,
        cantidad=cantidad
    )


@main.route("/admin/rubros")
@role_required("SUPER_ADMIN")
def admin_rubros():
    rubros = get_category_requests_summary()
    return render_template("admin_rubros.html", rubros=rubros)

@main.route("/admin/rubros/aprobar/<nombre_rubro>", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_aprobar_rubro(nombre_rubro):
    approve_category(nombre_rubro)
    return redirect("/admin/rubros")
