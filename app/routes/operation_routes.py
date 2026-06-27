from datetime import datetime
import re

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app import db
from app.models.user import User
from app.services.audit_service import create_audit_log
from app.models.professional import Professional
from app.services.budget_service import (
    MAX_OFFERS_PER_REQUEST,
    award_budget_offer,
    cancel_budget_request,
    create_budget_offer,
    create_budget_request,
    get_client_budget_requests_with_counts,
    get_budget_offers,
    get_budget_request_by_id,
    get_open_budget_requests,
    get_offer_allowance,
    get_professional_budget_offers,
)
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


def _parse_date(value):
    value = _empty_to_none(value)

    if value is None:
        return None

    return datetime.strptime(value, "%Y-%m-%d").date()


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
    average_rating = get_professional_average_rating(professional.id)

    return {
        "professional": professional,
        "badges": {
            "work": True,
            "pro": is_pro,
            "verified": is_verified,
        },
        "rating": {
            "average": average_rating,
            "count": len(reviews),
        },
        "phone": {
            "whatsapp": phone_digits or None,
            "call": f"+{phone_digits}" if phone_digits else None,
        },
        "availability": {
            "primary": "Disponible segun perfil",
            "secondary": "Guardia no configurada",
            "priority": "Prioridad PRO" if is_pro else None,
        },
        "sort": {
            "pro": 1 if is_pro else 0,
            "verified": 1 if is_verified else 0,
            "rating": average_rating or 0,
        },
    }


def _get_budget_offer_data(offer):
    professional = offer.professional
    reviews = get_professional_reviews(professional.id)
    user_id = professional.user_id
    phone_digits = re.sub(r"\D", "", professional.telefono or "")

    return {
        "offer": offer,
        "professional": professional,
        "badges": {
            "work": True,
            "pro": has_pro_access(user_id) if user_id else False,
            "verified": has_approved_verification(user_id) if user_id else False,
        },
        "rating": {
            "average": get_professional_average_rating(professional.id),
            "count": len(reviews),
        },
        "phone": {
            "whatsapp": phone_digits or None,
        },
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
def nuevo_presupuesto():
    current_user = (
        db.session.get(User, session.get("user_id"))
        if session.get("user_id")
        else None
    )
    is_anonymous = not is_user_active(current_user)

    if request.method == "POST":
        form_data = {
            "categoria": _empty_to_none(request.form.get("categoria")) or "",
            "zona": _empty_to_none(request.form.get("zona")) or "",
            "titulo": _empty_to_none(request.form.get("titulo")) or "",
            "descripcion": _empty_to_none(request.form.get("descripcion")) or "",
            "fecha_estimada": _empty_to_none(request.form.get("fecha_estimada")) or "",
            "urgencia": _empty_to_none(request.form.get("urgencia")) or "NORMAL",
        }

        if not all(
            form_data[field]
            for field in ("categoria", "zona", "titulo", "descripcion")
        ):
            return render_template(
                "nuevo_presupuesto.html",
                form_data=form_data,
                error="Completa categoria, zona, titulo y descripcion.",
                is_anonymous=is_anonymous,
            ), 400

        if form_data["urgencia"] not in ("BAJA", "NORMAL", "ALTA"):
            return render_template(
                "nuevo_presupuesto.html",
                form_data=form_data,
                error="Selecciona una urgencia valida.",
                is_anonymous=is_anonymous,
            ), 400

        try:
            estimated_date = _parse_date(form_data["fecha_estimada"])
        except ValueError:
            return render_template(
                "nuevo_presupuesto.html",
                form_data=form_data,
                error="La fecha estimada no es valida.",
                is_anonymous=is_anonymous,
            ), 400

        if not is_anonymous:
            budget_request = create_budget_request(
                cliente_id=current_user.id,
                categoria=form_data["categoria"],
                titulo=form_data["titulo"],
                descripcion=form_data["descripcion"],
                zona=form_data["zona"],
                fecha_estimada=estimated_date,
                urgencia=form_data["urgencia"],
            )

            return redirect(url_for("operations.confirmacion_presupuesto", id=budget_request.id))

        return render_template(
            "nuevo_presupuesto.html",
            form_data=form_data,
            anonymous_preview={
                **form_data,
                "fecha_estimada_display": (
                    estimated_date.strftime("%d/%m/%Y")
                    if estimated_date
                    else "A coordinar"
                ),
            },
            is_anonymous=True,
        )

    return render_template(
        "nuevo_presupuesto.html",
        form_data={
            **_get_query_prefill("categoria", "zona", "titulo", "descripcion"),
            "fecha_estimada": _empty_to_none(request.args.get("fecha_estimada")) or "",
            "urgencia": _empty_to_none(request.args.get("urgencia")) or "NORMAL",
        },
        is_anonymous=is_anonymous,
    )


@operations.route("/presupuestos/mis-solicitudes", methods=["GET"])
@login_required
@role_required("CLIENTE")
def mis_solicitudes_presupuesto():
    estado_filtro = _empty_to_none(request.args.get("estado")) or "activas"
    estados_por_filtro = {
        "activas": ("ABIERTO", "COTIZANDO"),
        "adjudicadas": ("ADJUDICADA",),
        "canceladas": ("CANCELADA",),
        "todas": None,
    }
    if estado_filtro not in estados_por_filtro:
        estado_filtro = "activas"

    request_rows = [
        {
            "budget_request": budget_request,
            "offer_count": offer_count,
        }
        for budget_request, offer_count in get_client_budget_requests_with_counts(
            session["user_id"],
            estados=estados_por_filtro[estado_filtro],
        )
    ]

    return render_template(
        "mis_solicitudes_presupuesto.html",
        request_rows=request_rows,
        max_offers=MAX_OFFERS_PER_REQUEST,
        estado_filtro=estado_filtro,
    )


@operations.route("/presupuestos/mis-enviados", methods=["GET"])
@login_required
@role_required("PROFESIONAL")
def mis_presupuestos_enviados():
    offer_rows = []

    for offer in get_professional_budget_offers(session["user_id"]):
        budget_request = offer.budget_request
        client = db.session.get(User, budget_request.cliente_id)
        offer_rows.append({
            "offer": offer,
            "budget_request": budget_request,
            "client": client,
            "offer_count": len(budget_request.offers),
        })

    return render_template(
        "mis_presupuestos_enviados.html",
        offer_rows=offer_rows,
        max_offers=MAX_OFFERS_PER_REQUEST,
    )


@operations.route("/presupuestos", methods=["GET"])
@login_required
@role_required("PROFESIONAL")
def marketplace_presupuestos():
    categoria = _empty_to_none(request.args.get("categoria")) or ""
    zona = _empty_to_none(request.args.get("zona")) or ""
    budget_requests = get_open_budget_requests(categoria, zona)

    return render_template(
        "listado_presupuestos.html",
        budget_requests=budget_requests,
        categoria=categoria,
        zona=zona,
        offer_allowance=get_offer_allowance(session["user_id"]),
    )


@operations.route("/presupuestos/<int:id>/confirmacion", methods=["GET"])
@login_required
@role_required("CLIENTE")
def confirmacion_presupuesto(id):
    budget_request = get_budget_request_by_id(id)
    if budget_request is None:
        abort(404)
    if budget_request.cliente_id != session["user_id"]:
        abort(403)

    offer_count = len(get_budget_offers(id))

    return render_template(
        "confirmacion_presupuesto.html",
        budget_request=budget_request,
        offer_count=offer_count,
        max_offers=MAX_OFFERS_PER_REQUEST,
    )


@operations.route("/presupuestos/<int:id>", methods=["GET"])
@login_required
def detalle_presupuesto(id):
    budget_request = get_budget_request_by_id(id)
    if budget_request is None:
        abort(404)

    current_user_id = session["user_id"]
    current_user = db.session.get(User, current_user_id)
    is_owner = budget_request.cliente_id == current_user_id
    current_professional = Professional.query.filter_by(user_id=current_user_id).first()
    is_professional = (
        current_user is not None
        and current_user.rol == "PROFESIONAL"
        and current_professional is not None
    )
    offers = get_budget_offers(id)
    own_offer = next(
        (
            offer
            for offer in offers
            if offer.professional_user_id == current_user_id
        ),
        None,
    )

    return render_template(
        "detalle_presupuesto.html",
        budget_request=budget_request,
        offer_rows=[_get_budget_offer_data(offer) for offer in offers] if is_owner else [],
        offer_count=len(offers),
        max_offers=MAX_OFFERS_PER_REQUEST,
        is_owner=is_owner,
        is_professional=is_professional,
        own_offer=own_offer,
        offer_allowance=get_offer_allowance(current_user_id) if is_professional else None,
        offer_error=request.args.get("error"),
        offer_sent=request.args.get("enviado") == "1",
        awarded=request.args.get("adjudicado") == "1",
    )


@operations.route("/presupuestos/<int:id>/ofertar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@profile_complete_required
def ofertar_presupuesto(id):
    cobra_visita = _empty_to_none(request.form.get("cobra_visita")) or "no"
    precio_visita = _empty_to_none(request.form.get("precio_visita"))
    monto_desde = _empty_to_none(request.form.get("monto_desde"))
    monto_hasta = _empty_to_none(request.form.get("monto_hasta"))
    plazo_estimado = _empty_to_none(request.form.get("plazo_estimado"))
    condiciones = _empty_to_none(request.form.get("condiciones"))

    if not monto_desde or not monto_hasta or not plazo_estimado:
        return redirect(url_for(
            "operations.detalle_presupuesto",
            id=id,
            error="Completa monto desde, monto hasta y plazo estimado.",
        ))

    try:
        create_budget_offer(
            budget_request_id=id,
            professional_user_id=session["user_id"],
            cobra_visita=cobra_visita,
            precio_visita=precio_visita,
            monto_desde=monto_desde,
            monto_hasta=monto_hasta,
            plazo_estimado=plazo_estimado,
            condiciones=condiciones,
        )
    except ValueError as error:
        return redirect(url_for(
            "operations.detalle_presupuesto",
            id=id,
            error=str(error),
        ))

    return redirect(url_for("operations.detalle_presupuesto", id=id, enviado="1"))


@operations.route(
    "/presupuestos/<int:id>/adjudicar/<int:presupuesto_id>",
    methods=["POST"],
)
@login_required
def adjudicar_presupuesto(id, presupuesto_id):
    try:
        award_budget_offer(
            budget_request_id=id,
            offer_id=presupuesto_id,
            cliente_id=session["user_id"],
        )
    except PermissionError:
        abort(403)
    except ValueError as error:
        return redirect(url_for(
            "operations.detalle_presupuesto",
            id=id,
            error=str(error),
        ))

    return redirect(url_for(
        "operations.detalle_presupuesto",
        id=id,
        adjudicado="1",
    ))


@operations.route("/presupuestos/<int:id>/cancelar", methods=["POST"])
@login_required
@role_required("CLIENTE")
def cancelar_presupuesto(id):
    try:
        cancel_budget_request(
            budget_request_id=id,
            cliente_id=session["user_id"],
        )
    except PermissionError:
        abort(403)
    except ValueError as error:
        return redirect(url_for(
            "operations.detalle_presupuesto",
            id=id,
            error=str(error),
        ))

    return redirect(url_for("operations.mis_solicitudes_presupuesto", estado="canceladas"))


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
        key=lambda row: (
            -row["sort"]["pro"],
            -row["sort"]["verified"],
            -row["sort"]["rating"],
            row["professional"].nombre.casefold(),
        ),
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
