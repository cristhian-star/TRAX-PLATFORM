from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    session,
)

from app.models.user import User
from app.services.subscription_service import has_pro_access
from app.services.verification_service import has_approved_verification

dev = Blueprint("dev", __name__)


def _is_dev_qa_panel_enabled():
    return bool(
        current_app.config.get("ENABLE_DEV_QA_PANEL")
        and current_app.config.get("ENV_NAME")
        in ("development", "testing")
    )


def _require_dev_qa_panel():
    if not _is_dev_qa_panel_enabled():
        abort(404)


def _user_row(user):
    professional = user.professional_profile

    return {
        "id": user.id,
        "nombre": user.nombre,
        "email": user.email,
        "rol": user.rol,
        "estado": user.estado,
        "has_professional_profile": professional is not None,
        "professional_profile_complete": bool(professional and professional.perfil_completo),
        "professional_service": professional.servicio if professional else None,
        "professional_profile_id": professional.id if professional else None,
        "professional_profile_url": (
            f"/profesional/{professional.id}" if professional else None
        ),
        "is_pro": has_pro_access(user.id),
        "is_verified": has_approved_verification(user.id),
        "login_allowed": bool(
            user.estado == "ACTIVO"
            and user.rol in ("CLIENTE", "PROFESIONAL")
            and (user.rol != "PROFESIONAL" or professional is not None)
        ),
    }


@dev.route("/dev/qa", methods=["GET"])
def qa_panel():
    _require_dev_qa_panel()

    users = User.query.order_by(User.rol.asc(), User.nombre.asc(), User.id.asc()).all()

    return render_template(
        "dev_qa_panel.html",
        users=[_user_row(user) for user in users],
        current_user_id=session.get("user_id"),
        current_user_name=session.get("user_name"),
        current_user_role=session.get("user_role"),
    )


@dev.route("/dev/qa/login/<int:user_id>", methods=["POST"])
def qa_login(user_id):
    _require_dev_qa_panel()

    user = User.query.get_or_404(user_id)
    professional = user.professional_profile
    if (
        user.estado != "ACTIVO"
        or user.rol not in ("CLIENTE", "PROFESIONAL")
        or (user.rol == "PROFESIONAL" and professional is None)
    ):
        abort(403)
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.nombre
    session["user_role"] = user.rol

    if user.rol == "PROFESIONAL":
        return redirect(f"/profesional/{professional.id}")
    return redirect("/resultados")


@dev.route("/dev/qa/logout", methods=["POST"])
def qa_logout():
    _require_dev_qa_panel()

    session.clear()
    return redirect("/dev/qa")
