from datetime import datetime

from flask import Blueprint, render_template, request, session

from app.services.budget_service import create_budget_request
from app.services.contract_service import create_contract
from app.services.emergency_service import create_emergency_request
from app.services.proposal_service import create_proposal_request
from app.utils.decorators import login_required

operations = Blueprint("operations", __name__)


def _empty_to_none(value):
    if value is None:
        return None

    value = value.strip()
    return value or None


def _parse_datetime(value):
    value = _empty_to_none(value)

    if value is None:
        return None

    return datetime.fromisoformat(value)


@operations.route("/contratacion/nueva", methods=["GET", "POST"])
@login_required
def nueva_contratacion():
    if request.method == "POST":
        contract = create_contract(
            cliente_id=session["user_id"],
            professional_id=request.form.get("professional_id"),
            servicio=request.form.get("servicio"),
            descripcion=_empty_to_none(request.form.get("descripcion")),
            precio_acordado=_empty_to_none(request.form.get("precio_acordado")),
            fecha_inicio=_parse_datetime(request.form.get("fecha_inicio")),
            fecha_fin=_parse_datetime(request.form.get("fecha_fin"))
        )

        return render_template("nueva_contratacion.html", created=contract)

    return render_template("nueva_contratacion.html")


@operations.route("/presupuestos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_presupuesto():
    if request.method == "POST":
        budget_request = create_budget_request(
            cliente_id=session["user_id"],
            categoria=request.form.get("categoria"),
            descripcion=request.form.get("descripcion"),
            zona=request.form.get("zona")
        )

        return render_template("nuevo_presupuesto.html", created=budget_request)

    return render_template("nuevo_presupuesto.html")


@operations.route("/emergencias/nueva", methods=["GET", "POST"])
@login_required
def nueva_emergencia():
    if request.method == "POST":
        emergency_request = create_emergency_request(
            cliente_id=session["user_id"],
            categoria=request.form.get("categoria"),
            descripcion=request.form.get("descripcion"),
            zona=request.form.get("zona"),
            prioridad=request.form.get("prioridad")
        )

        return render_template("nueva_emergencia.html", created=emergency_request)

    return render_template("nueva_emergencia.html")


@operations.route("/propuestas/nueva", methods=["GET", "POST"])
@login_required
def nueva_propuesta():
    if request.method == "POST":
        proposal_request = create_proposal_request(
            cliente_id=session["user_id"],
            categoria=request.form.get("categoria"),
            descripcion=request.form.get("descripcion"),
            presupuesto_estimado=_empty_to_none(request.form.get("presupuesto_estimado")),
            fecha_limite=_parse_datetime(request.form.get("fecha_limite"))
        )

        return render_template("nueva_propuesta.html", created=proposal_request)

    return render_template("nueva_propuesta.html")
