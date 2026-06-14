from datetime import datetime
import re

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app.models.user import User
from app.services.audit_service import create_audit_log
from app.services.budget_service import create_budget_request
from app.services.contract_service import (
    accept_contract,
    cancel_contract,
    complete_contract,
    confirm_contract,
    create_contract,
    get_contract_by_id,
    reject_contract,
    start_contract,
)
from app.services.emergency_service import create_emergency_request
from app.services.proposal_service import create_proposal_request
from app.services.professional_service import (
    get_professional_by_id,
    search_emergency_professionals,
)
from app.services.review_service import (
    get_professional_average_rating,
    get_professional_reviews,
)
from app.services.subscription_service import has_pro_access
from app.services.user_service import is_user_active
from app.services.verification_service import has_approved_verification
from app.utils.decorators import login_required, pro_required, profile_complete_required, role_required, verified_required

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


def _get_query_prefill(*field_names):
    return {
        field_name: _empty_to_none(request.args.get(field_name)) or ""
        for field_name in field_names
    }


def _get_emergency_professional_data(professional):
    user_id = professional.user_id
    phone_digits = re.sub(r"\D", "", professional.telefono or "")
    is_pro = has_pro_access(user_id) if user_id else False
    is_verified = has_approved_verification(user_id) if user_id else False
    reviews = get_professional_reviews(professional.id)

    return {
        "professional": professional,
        "badges": {
            "work": True,
            "pro": is_pro,
            "verified": is_verified,
        },
        "rating": {
            "average": get_professional_average_rating(professional.id),
            "count": len(reviews),
        },
        "phone": {
            "whatsapp": phone_digits or None,
            "call": f"+{phone_digits}" if phone_digits else None,
        },
        "priority": (
            2 if is_pro and is_verified
            else 1 if is_pro or is_verified
            else 0
        ),
    }


def _audit_contract_action(action, contract, description):
    target_user_id = (
        contract.cliente_id
        if session["user_id"] == contract.professional_user_id
        else contract.professional_user_id
    )
    create_audit_log(
        actor_user_id=session["user_id"],
        target_user_id=target_user_id,
        action=action,
        description=description,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )


def _load_contract_or_404(contract_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        abort(404)
    return contract


def _require_assigned_professional(contract):
    if contract.professional_user_id != session["user_id"]:
        abort(403)


def _require_client_owner(contract):
    if contract.cliente_id != session["user_id"]:
        abort(403)


@operations.route("/contratacion/nueva", methods=["GET", "POST"])
@login_required
def nueva_contratacion():
    if request.method == "POST":
        professional_id_raw = request.form.get("professional_id")

        try:
            professional_id = int(professional_id_raw)
        except (TypeError, ValueError):
            return "ID de profesional invalido", 400

        professional = get_professional_by_id(professional_id)

        if professional is None:
            return "Profesional no encontrado", 404

        if professional.user_id is None:
            return "Perfil profesional sin propietario asociado", 409

        if professional.user_id == session["user_id"]:
            return "No podes contratar tu propio perfil", 400

        contract = create_contract(
            cliente_id=session["user_id"],
            professional_id=professional.id,
            professional_user_id=professional.user_id,
            servicio=request.form.get("servicio"),
            descripcion=_empty_to_none(request.form.get("descripcion")),
            precio_acordado=_empty_to_none(request.form.get("precio_acordado")),
            fecha_inicio=_parse_datetime(request.form.get("fecha_inicio")),
            fecha_fin=_parse_datetime(request.form.get("fecha_fin"))
        )

        return redirect(f"/contratacion/{contract.id}")

    return render_template("nueva_contratacion.html")


@operations.route("/contratacion/<int:id>")
@login_required
def contract_detail(id):
    contract = _load_contract_or_404(id)
    is_client = contract.cliente_id == session["user_id"]
    is_professional = contract.professional_user_id == session["user_id"]

    if not is_client and not is_professional:
        abort(403)

    return render_template(
        "contract_detail.html",
        contract=contract,
        client_user=User.query.filter_by(id=contract.cliente_id).first(),
        professional_user=User.query.filter_by(id=contract.professional_user_id).first(),
        is_client=is_client,
        is_professional=is_professional,
    )


@operations.route("/contratacion/<int:id>/aceptar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def aceptar_contratacion(id):
    contract = _load_contract_or_404(id)
    _require_assigned_professional(contract)
    try:
        contract = accept_contract(id, session["user_id"])
    except ValueError as error:
        return str(error), 400
    _audit_contract_action("CONTRACT_ACCEPTED", contract, f"Contratacion #{id} aceptada.")
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/rechazar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def rechazar_contratacion(id):
    contract = _load_contract_or_404(id)
    _require_assigned_professional(contract)
    try:
        contract = reject_contract(id, session["user_id"])
    except ValueError as error:
        return str(error), 400
    _audit_contract_action("CONTRACT_REJECTED", contract, f"Contratacion #{id} rechazada.")
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/iniciar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def iniciar_contratacion(id):
    contract = _load_contract_or_404(id)
    _require_assigned_professional(contract)
    try:
        contract = start_contract(id)
    except ValueError as error:
        return str(error), 400
    _audit_contract_action("CONTRACT_STARTED", contract, f"Contratacion #{id} iniciada.")
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/completar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def completar_contratacion(id):
    contract = _load_contract_or_404(id)
    _require_assigned_professional(contract)
    try:
        contract = complete_contract(id)
    except ValueError as error:
        return str(error), 400
    _audit_contract_action("CONTRACT_COMPLETED", contract, f"Contratacion #{id} completada.")
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/confirmar", methods=["POST"])
@login_required
def confirmar_contratacion(id):
    contract = _load_contract_or_404(id)
    _require_client_owner(contract)
    try:
        contract = confirm_contract(id)
    except ValueError as error:
        return str(error), 400
    _audit_contract_action("CONTRACT_CONFIRMED", contract, f"Contratacion #{id} confirmada por cliente.")
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/cancelar", methods=["POST"])
@login_required
def cancelar_contratacion(id):
    contract = _load_contract_or_404(id)
    _require_client_owner(contract)
    try:
        contract = cancel_contract(id)
    except ValueError as error:
        return str(error), 400
    _audit_contract_action("CONTRACT_CANCELLED", contract, f"Contratacion #{id} cancelada por cliente.")
    return redirect(f"/contratacion/{id}")


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

    return render_template(
        "nuevo_presupuesto.html",
        form_data=_get_query_prefill("categoria", "zona", "descripcion"),
    )


@operations.route("/emergencias/nueva", methods=["GET", "POST"])
def nueva_emergencia():
    if request.method == "POST":
        categoria = _empty_to_none(request.form.get("categoria"))
        zona = _empty_to_none(request.form.get("zona"))
        descripcion = _empty_to_none(request.form.get("descripcion"))

        if not categoria or not zona or not descripcion:
            return "Categoria, zona y descripcion son requeridas", 400

        redirect_values = {
            "categoria": categoria,
            "zona": zona,
        }

        current_user = User.query.get(session.get("user_id")) if session.get("user_id") else None

        if is_user_active(current_user):
            emergency_request = create_emergency_request(
                cliente_id=current_user.id,
                categoria=categoria,
                descripcion=descripcion,
                zona=zona,
                prioridad=request.form.get("prioridad") or "ALTA",
            )
            redirect_values["solicitud"] = emergency_request.id
        else:
            redirect_values["consulta_anonima"] = "1"

        return redirect(
            url_for(
                "operations.directorio_emergencias",
                **redirect_values,
            )
        )

    return render_template(
        "nueva_emergencia.html",
        form_data=_get_query_prefill("categoria", "zona", "descripcion"),
    )


@operations.route("/emergencias/directorio", methods=["GET"])
def directorio_emergencias():
    categoria = _empty_to_none(request.args.get("categoria")) or ""
    zona = _empty_to_none(request.args.get("zona")) or ""
    professionals = search_emergency_professionals(categoria, zona)
    professional_rows = sorted(
        (_get_emergency_professional_data(professional) for professional in professionals),
        key=lambda row: (-row["priority"], row["professional"].nombre.casefold()),
    )

    return render_template(
        "directorio_emergencias.html",
        professional_rows=professional_rows,
        categoria=categoria,
        zona=zona,
        request_created=bool(request.args.get("solicitud")),
        anonymous_search=request.args.get("consulta_anonima") == "1",
    )


@operations.route("/propuestas/nueva", methods=["GET", "POST"])
@login_required
@pro_required
@profile_complete_required
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

    return render_template(
        "nueva_propuesta.html",
        form_data=_get_query_prefill("categoria", "ubicacion"),
    )
