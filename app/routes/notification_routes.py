from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app.services.notification_service import (
    formatear_fecha_notificacion,
    marcar_como_leida,
    marcar_todas_como_leidas,
    obtener_notificaciones_usuario,
)
from app.utils.decorators import login_required

notifications = Blueprint("notifications", __name__)


@notifications.route("/notificaciones", methods=["GET"])
@login_required
def notification_center():
    filtro = request.args.get("filtro", "todas")
    allowed_filters = {"todas", "no-leidas", "accion", "info", "recordatorios"}
    if filtro not in allowed_filters:
        filtro = "todas"

    return render_template(
        "notificaciones.html",
        notifications=obtener_notificaciones_usuario(
            session["user_id"],
            filtro=None if filtro == "todas" else filtro,
        ),
        filtro=filtro,
        format_notification_date=formatear_fecha_notificacion,
    )


@notifications.route("/notificaciones/<int:id>/leer", methods=["POST"])
@login_required
def mark_notification_read(id):
    notification = marcar_como_leida(id, session["user_id"])
    if notification is None:
        abort(404)

    next_url = request.form.get("next") or url_for("notifications.notification_center")
    return redirect(next_url)


@notifications.route("/notificaciones/marcar-todas-leidas", methods=["POST"])
@login_required
def mark_all_notifications_read():
    marcar_todas_como_leidas(session["user_id"])
    return redirect(url_for("notifications.notification_center"))
