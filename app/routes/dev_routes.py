import os

from flask import Blueprint, abort, redirect, render_template, session

from app.models.user import User
from app.services.subscription_service import has_pro_access
from app.services.verification_service import has_approved_verification

dev = Blueprint("dev", __name__)


_TRUE_VALUES = {"1", "true", "yes", "on"}
_PRODUCTION_VALUES = {"production", "prod"}


def _env_value(name):
    return os.environ.get(name, "").strip().lower()


def _is_dev_qa_panel_enabled():
    explicitly_enabled = _env_value("ENABLE_DEV_QA_PANEL") in _TRUE_VALUES

    if not explicitly_enabled:
        return False

    if _env_value("FLASK_ENV") in _PRODUCTION_VALUES:
        return False

    if _env_value("APP_ENV") in _PRODUCTION_VALUES:
        return False

    return True


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
        "is_pro": has_pro_access(user.id),
        "is_verified": has_approved_verification(user.id),
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
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.nombre
    session["user_role"] = user.rol

    return redirect("/")


@dev.route("/dev/qa/logout", methods=["POST"])
def qa_logout():
    _require_dev_qa_panel()

    session.clear()
    return redirect("/dev/qa")
