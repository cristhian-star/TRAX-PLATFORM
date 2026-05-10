from flask import Blueprint, render_template, request
from app.database.db import (
    get_connection,
    buscar_profesionales,
    crear_profesional,
    solicitar_rubro,
    obtener_profesional_por_id
)

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("home.html")


@main.route("/buscar", methods=["GET"])
def buscar():
    servicio = request.args.get("servicio", "")
    zona = request.args.get("zona", "")

    resultados = buscar_profesionales(servicio, zona)

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

    resultados = buscar_profesionales(servicio, zona)

    return render_template(
        "listado_profesionales.html",
        resultados=resultados,
        servicio=servicio,
        zona=zona
    )


@main.route("/profesional/<int:id>")
def perfil_profesional(id):
    profesional = obtener_profesional_por_id(id)

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

    crear_profesional(nombre, servicio, zona, telefono, descripcion)

    return "Profesional creado correctamente"


@main.route("/rubros/solicitar", methods=["POST"])
def guardar_solicitud_rubro():
    nombre_rubro = request.form.get("nombre_rubro")
    descripcion = request.form.get("descripcion_rubro")
    email_notificacion = request.form.get("email_notificacion")

    cantidad = solicitar_rubro(
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
def admin_rubros():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre_rubro, COUNT(*) as total, estado
        FROM solicitudes_rubros
        GROUP BY LOWER(nombre_rubro)
        ORDER BY total DESC
    """)

    rubros = cursor.fetchall()
    conn.close()

    return render_template("admin_rubros.html", rubros=rubros)