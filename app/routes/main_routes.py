from app.database.db import buscar_profesionales, crear_profesional, solicitar_rubro, obtener_profesional_por_id
from app.database.db import aprobar_rubro, obtener_rubros_activos
from app.database.db import get_connection
from app.database.db import buscar_profesionales, crear_profesional, solicitar_rubro
from app.database.db import buscar_profesionales, crear_profesional
from flask import Blueprint, render_template, request, redirect
from app.database.db import buscar_profesionales

main = Blueprint("main", __name__)

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

@main.route("/admin/rubros/aprobar/<nombre_rubro>", methods=["POST"])
def admin_aprobar_rubro(nombre_rubro):
    aprobar_rubro(nombre_rubro)
    return redirect("/admin/rubros")

@main.route("/admin/rubros")
def admin_rubros():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            nombre_rubro,
            COUNT(*) as total,
            MAX(estado) as estado
        FROM solicitudes_rubros
        GROUP BY nombre_rubro
        ORDER BY total DESC
    """)

    rubros = cursor.fetchall()
    conn.close()

    return render_template("admin_rubros.html", rubros=rubros)

@main.route("/rubros/solicitar", methods=["POST"])
def guardar_solicitud_rubro():
    nombre_rubro = request.form.get("nombre_rubro")
    descripcion = request.form.get("descripcion_rubro")
    email_notificacion = request.form.get("email_notificacion")

    cantidad = solicitar_rubro(nombre_rubro, descripcion, email_notificacion)

    return render_template(
        "rubro_solicitado.html",
        nombre_rubro=nombre_rubro,
        cantidad=cantidad
    )

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

@main.route("/profesional/<int:id>")
def perfil_profesional(id):
    profesional = obtener_profesional_por_id(id)

    if profesional is None:
        return "Profesional no encontrado", 404

    return render_template("perfil_profesional.html", profesional=profesional)
