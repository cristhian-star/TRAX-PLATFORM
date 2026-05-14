from flask import Blueprint, render_template, request, redirect, session
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
from app.utils.decorators import login_required, role_required
from app.services.subscription_service import has_pro_access
from app.services.verification_service import has_approved_verification
from app.services.reputation_service import add_reputation_event, get_user_reputation_score
from app.services.review_service import (
    create_review,
    get_professional_average_rating,
    get_professional_reviews
)

main = Blueprint("main", __name__)


def _entity_value(entity, key, default=None):
    if isinstance(entity, dict):
        return entity.get(key, default)

    return getattr(entity, key, default)


def _professional_user_id(professional):
    return _entity_value(
        professional,
        "user_id",
        _entity_value(professional, "id")
    )


def _get_professional_badges(professional):
    user_id = _professional_user_id(professional)

    if not user_id:
        return {
            "work": True,
            "pro": False,
            "verified": False,
            "reputation_score": 0,
        }

    return {
        "work": True,
        "pro": has_pro_access(user_id),
        "verified": has_approved_verification(user_id),
        "reputation_score": get_user_reputation_score(user_id),
    }




def _get_professional_rating(professional_id):
    reviews = get_professional_reviews(professional_id)

    return {
        "average": get_professional_average_rating(professional_id),
        "count": len(reviews),
    }


def _get_professionals_ratings(professionals):
    return {
        _entity_value(professional, "id", index): _get_professional_rating(
            _entity_value(professional, "id", index)
        )
        for index, professional in enumerate(professionals, start=1)
    }

def _get_professionals_badges(professionals):
    return {
        _entity_value(professional, "id", index): _get_professional_badges(professional)
        for index, professional in enumerate(professionals, start=1)
    }


@main.route("/")
def home():
    if session.get("user_id"):
        return render_template("home_logged.html")

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
        zona=zona,
        professional_badges=_get_professionals_badges(resultados),
        professional_ratings=_get_professionals_ratings(resultados)
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
        zona=zona,
        professional_badges=_get_professionals_badges(resultados),
        professional_ratings=_get_professionals_ratings(resultados)
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



@main.route("/profesional/<int:id>/review", methods=["GET", "POST"])
@login_required
def crear_review(id):
    profesional = get_professional_by_id(id)

    if profesional is None:
        return "Profesional no encontrado", 404

    if request.method == "POST":
        rating = int(request.form.get("rating", 0))
        comentario = request.form.get("comentario")

        create_review(
            cliente_id=session["user_id"],
            professional_id=id,
            rating=rating,
            comentario=comentario
        )

        professional_user_id = _professional_user_id(profesional)

        if rating >= 4:
            add_reputation_event(
                professional_user_id,
                "REVIEW_POSITIVA",
                10,
                "Review positiva recibida"
            )
        elif rating <= 2:
            add_reputation_event(
                professional_user_id,
                "REVIEW_NEGATIVA",
                -5,
                "Review negativa recibida"
            )

        return redirect(f"/profesional/{id}")

    return render_template(
        "crear_review.html",
        profesional=profesional,
        professional_id=id
    )

@main.route("/profesional/<int:id>")
def perfil_profesional(id):
    profesional = get_professional_by_id(id)

    if profesional is None:
        return "Profesional no encontrado", 404

    return render_template(
        "perfil_profesional.html",
        profesional=profesional,
        profile_badges=_get_professional_badges(profesional),
        reviews=get_professional_reviews(id),
        average_rating=get_professional_average_rating(id),
        review_count=len(get_professional_reviews(id))
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
