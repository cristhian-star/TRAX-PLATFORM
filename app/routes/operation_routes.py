from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app import db
from app.models.user import User
from app.services.budget_service import (
    MAX_OFFERS_PER_REQUEST,
    award_budget_offer,
    cancel_budget_request,
    create_budget_offer,
    create_budget_request,
    get_budget_offers,
    get_open_budget_requests,
    get_offer_allowance,
)
from app.services.contract_service import (
    audit_contract_action,
    accept_contract,
    cancel_contract,
    complete_contract,
    confirm_contract,
    create_contract,
    get_contract_detail_context,
    get_contract_or_error,
    require_assigned_professional,
    require_client_owner,
    reject_contract,
    start_contract,
)
from app.services.emergency_service import create_emergency_request
from app.services.proposal_service import (
    accept_application,
    apply_to_proposal,
    cancel_proposal,
    create_proposal_request,
    discard_application,
    get_open_proposals,
)
from app.services.professional_service import (
    get_professional_by_id,
)
from app.services.operation_notification_service import (
    notify_budget_awarded,
    notify_budget_cancelled,
    notify_budget_created,
    notify_budget_offer_created,
    notify_emergency_created,
    notify_proposal_accepted,
    notify_proposal_application_created,
    notify_proposal_cancelled,
    notify_proposal_created,
    notify_proposal_discarded,
)
from app.services.operation_policy_service import (
    get_budget_request_or_error,
    get_proposal_or_error,
    require_budget_owner,
)
from app.services.operation_request_service import (
    build_budget_form_data,
    build_proposal_form_data,
    empty_to_none,
    get_query_prefill,
    get_request_coordinates,
    parse_date,
    parse_datetime,
    validate_budget_form_data,
    validate_proposal_form_data,
)
from app.services.operation_view_service import (
    build_budget_detail_context,
    build_client_budget_request_rows,
    build_emergency_directory_rows,
    build_professional_budget_offer_rows,
    build_proposal_detail_context,
    build_proposal_taxonomy_options,
)
from app.services.user_service import is_user_active
from app.utils.decorators import login_required, profile_complete_required, role_required

operations = Blueprint("operations", __name__)


def _load_contract_or_404(contract_id):
    try:
        return get_contract_or_error(contract_id)
    except LookupError:
        abort(404)


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
            descripcion=empty_to_none(request.form.get("descripcion")),
            precio_acordado=empty_to_none(request.form.get("precio_acordado")),
            fecha_inicio=parse_datetime(request.form.get("fecha_inicio")),
            fecha_fin=parse_datetime(request.form.get("fecha_fin"))
        )

        return redirect(f"/contratacion/{contract.id}")

    return render_template("nueva_contratacion.html")


@operations.route("/contratacion/<int:id>")
@login_required
def contract_detail(id):
    contract = _load_contract_or_404(id)
    try:
        context = get_contract_detail_context(contract, session["user_id"])
    except PermissionError:
        abort(403)

    return render_template(
        "contract_detail.html",
        **context,
    )


@operations.route("/contratacion/<int:id>/aceptar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def aceptar_contratacion(id):
    contract = _load_contract_or_404(id)
    try:
        require_assigned_professional(contract, session["user_id"])
        contract = accept_contract(id, session["user_id"])
    except ValueError as error:
        return str(error), 400
    except PermissionError:
        abort(403)
    audit_contract_action(
        "CONTRACT_ACCEPTED",
        contract,
        session["user_id"],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        description=f"Contratacion #{id} aceptada.",
    )
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/rechazar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def rechazar_contratacion(id):
    contract = _load_contract_or_404(id)
    try:
        require_assigned_professional(contract, session["user_id"])
        contract = reject_contract(id, session["user_id"])
    except ValueError as error:
        return str(error), 400
    except PermissionError:
        abort(403)
    audit_contract_action(
        "CONTRACT_REJECTED",
        contract,
        session["user_id"],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        description=f"Contratacion #{id} rechazada.",
    )
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/iniciar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def iniciar_contratacion(id):
    contract = _load_contract_or_404(id)
    try:
        require_assigned_professional(contract, session["user_id"])
        contract = start_contract(id)
    except ValueError as error:
        return str(error), 400
    except PermissionError:
        abort(403)
    audit_contract_action(
        "CONTRACT_STARTED",
        contract,
        session["user_id"],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        description=f"Contratacion #{id} iniciada.",
    )
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/completar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def completar_contratacion(id):
    contract = _load_contract_or_404(id)
    try:
        require_assigned_professional(contract, session["user_id"])
        contract = complete_contract(id)
    except ValueError as error:
        return str(error), 400
    except PermissionError:
        abort(403)
    audit_contract_action(
        "CONTRACT_COMPLETED",
        contract,
        session["user_id"],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        description=f"Contratacion #{id} completada.",
    )
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/confirmar", methods=["POST"])
@login_required
def confirmar_contratacion(id):
    contract = _load_contract_or_404(id)
    try:
        require_client_owner(contract, session["user_id"])
        contract = confirm_contract(id)
    except ValueError as error:
        return str(error), 400
    except PermissionError:
        abort(403)
    audit_contract_action(
        "CONTRACT_CONFIRMED",
        contract,
        session["user_id"],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        description=f"Contratacion #{id} confirmada por cliente.",
    )
    return redirect(f"/contratacion/{id}")


@operations.route("/contratacion/<int:id>/cancelar", methods=["POST"])
@login_required
def cancelar_contratacion(id):
    contract = _load_contract_or_404(id)
    try:
        require_client_owner(contract, session["user_id"])
        contract = cancel_contract(id)
    except ValueError as error:
        return str(error), 400
    except PermissionError:
        abort(403)
    audit_contract_action(
        "CONTRACT_CANCELLED",
        contract,
        session["user_id"],
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        description=f"Contratacion #{id} cancelada por cliente.",
    )
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
        form_data = build_budget_form_data(request.form)
        form_error = validate_budget_form_data(form_data)
        if form_error:
            return render_template(
                "nuevo_presupuesto.html",
                form_data=form_data,
                error=form_error,
                is_anonymous=is_anonymous,
            ), 400

        try:
            estimated_date = parse_date(form_data["fecha_estimada"])
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
            notify_budget_created(budget_request)

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
            **get_query_prefill(request.args, "categoria", "zona", "titulo", "descripcion"),
            "fecha_estimada": empty_to_none(request.args.get("fecha_estimada")) or "",
            "urgencia": empty_to_none(request.args.get("urgencia")) or "NORMAL",
        },
        is_anonymous=is_anonymous,
    )


@operations.route("/presupuestos/mis-solicitudes", methods=["GET"])
@login_required
@role_required("CLIENTE")
def mis_solicitudes_presupuesto():
    request_rows, estado_filtro = build_client_budget_request_rows(
        session["user_id"],
        empty_to_none(request.args.get("estado")) or "activas",
    )

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
    return render_template(
        "mis_presupuestos_enviados.html",
        offer_rows=build_professional_budget_offer_rows(session["user_id"]),
        max_offers=MAX_OFFERS_PER_REQUEST,
    )


@operations.route("/presupuestos", methods=["GET"])
@login_required
@role_required("PROFESIONAL")
def marketplace_presupuestos():
    categoria = empty_to_none(request.args.get("categoria")) or ""
    zona = empty_to_none(request.args.get("zona")) or ""
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
    try:
        budget_request = get_budget_request_or_error(id)
        require_budget_owner(budget_request, session["user_id"])
    except LookupError:
        abort(404)
    except PermissionError:
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
    try:
        budget_request = get_budget_request_or_error(id)
    except LookupError:
        abort(404)

    current_user_id = session["user_id"]

    return render_template(
        "detalle_presupuesto.html",
        **build_budget_detail_context(budget_request, current_user_id, request.args),
    )


@operations.route("/presupuestos/<int:id>/ofertar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@profile_complete_required
def ofertar_presupuesto(id):
    cobra_visita = empty_to_none(request.form.get("cobra_visita")) or "no"
    precio_visita = empty_to_none(request.form.get("precio_visita"))
    monto_desde = empty_to_none(request.form.get("monto_desde"))
    monto_hasta = empty_to_none(request.form.get("monto_hasta"))
    plazo_estimado = empty_to_none(request.form.get("plazo_estimado"))
    condiciones = empty_to_none(request.form.get("condiciones"))

    if not monto_desde or not monto_hasta or not plazo_estimado:
        return redirect(url_for(
            "operations.detalle_presupuesto",
            id=id,
            error="Completa monto desde, monto hasta y plazo estimado.",
        ))

    try:
        offer = create_budget_offer(
            budget_request_id=id,
            professional_user_id=session["user_id"],
            cobra_visita=cobra_visita,
            precio_visita=precio_visita,
            monto_desde=monto_desde,
            monto_hasta=monto_hasta,
            plazo_estimado=plazo_estimado,
            condiciones=condiciones,
        )
        notify_budget_offer_created(offer)
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
        offer = award_budget_offer(
            budget_request_id=id,
            offer_id=presupuesto_id,
            cliente_id=session["user_id"],
        )
        notify_budget_awarded(offer)
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
        budget_request = cancel_budget_request(
            budget_request_id=id,
            cliente_id=session["user_id"],
        )
        notify_budget_cancelled(budget_request)
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
        categoria = empty_to_none(request.form.get("categoria"))
        zona = empty_to_none(request.form.get("zona"))
        descripcion = empty_to_none(request.form.get("descripcion"))

        if not categoria or not zona or not descripcion:
            return "Categoria, zona y descripcion son requeridas", 400

        redirect_values = {
            "categoria": categoria,
            "zona": zona,
        }
        coordinates = get_request_coordinates(request.form)
        if coordinates is not None:
            redirect_values["latitude"] = coordinates[0]
            redirect_values["longitude"] = coordinates[1]

        current_user = User.query.get(session.get("user_id")) if session.get("user_id") else None

        if is_user_active(current_user):
            emergency_request = create_emergency_request(
                cliente_id=current_user.id,
                categoria=categoria,
                descripcion=descripcion,
                zona=zona,
                prioridad=request.form.get("prioridad") or "ALTA",
            )
            notify_emergency_created(emergency_request)
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
        form_data=get_query_prefill(request.args, "categoria", "zona", "descripcion"),
    )


@operations.route("/emergencias/directorio", methods=["GET"])
def directorio_emergencias():
    categoria = empty_to_none(request.args.get("categoria")) or ""
    zona = empty_to_none(request.args.get("zona")) or ""
    coordinates = get_request_coordinates(request.args)
    professional_rows = build_emergency_directory_rows(categoria, zona, coordinates)

    return render_template(
        "directorio_emergencias.html",
        professional_rows=professional_rows,
        categoria=categoria,
        zona=zona,
        has_geographic_context=coordinates is not None,
        emergency_request_id=request.args.get("solicitud"),
        request_created=bool(request.args.get("solicitud")),
        anonymous_search=request.args.get("consulta_anonima") == "1",
    )


@operations.route("/propuestas/nueva", methods=["GET", "POST"])
@login_required
def nueva_propuesta():
    taxonomy_options = build_proposal_taxonomy_options()

    if request.method == "POST":
        form_data = build_proposal_form_data(request.form)
        form_error = validate_proposal_form_data(form_data)
        if form_error:
            return render_template(
                "nueva_propuesta.html",
                form_data=form_data,
                taxonomy=taxonomy_options,
                error=form_error,
            ), 400

        try:
            proposal_request = create_proposal_request(
                owner_user_id=session["user_id"],
                industria=form_data["industria"],
                categoria=form_data["categoria"],
                rubro=form_data["rubro"],
                especialidad=form_data["especialidad"],
                titulo=form_data["titulo"],
                descripcion=form_data["descripcion"],
                ubicacion=form_data["ubicacion"],
                modalidad=form_data["modalidad"],
                cantidad_profesionales=int(form_data["cantidad_profesionales"] or 1),
                presupuesto_estimado=form_data["presupuesto_estimado"],
                fecha_inicio_estimada=parse_date(form_data["fecha_inicio_estimada"]),
                fecha_limite_postulacion=parse_date(form_data["fecha_limite_postulacion"]),
            )
            notify_proposal_created(proposal_request)
        except ValueError as error:
            return render_template(
                "nueva_propuesta.html",
                form_data=form_data,
                taxonomy=taxonomy_options,
                error=str(error),
            ), 400

        return redirect(url_for("operations.detalle_propuesta", id=proposal_request.id, publicada="1"))

    return render_template(
        "nueva_propuesta.html",
        form_data=get_query_prefill(request.args, "categoria", "ubicacion"),
        taxonomy=taxonomy_options,
    )


@operations.route("/propuestas", methods=["GET"])
def marketplace_propuestas():
    industria = empty_to_none(request.args.get("industria")) or ""
    categoria = empty_to_none(request.args.get("categoria")) or ""
    rubro = empty_to_none(request.args.get("rubro")) or ""
    ubicacion = empty_to_none(request.args.get("ubicacion")) or ""
    proposals = get_open_proposals(
        industria=industria,
        categoria=categoria,
        rubro=rubro,
        ubicacion=ubicacion,
    )

    return render_template(
        "listado_propuestas.html",
        proposals=proposals,
        filters={
            "industria": industria,
            "categoria": categoria,
            "rubro": rubro,
            "ubicacion": ubicacion,
        },
        taxonomy=build_proposal_taxonomy_options(include_specialties=False),
    )


@operations.route("/propuestas/<int:id>", methods=["GET"])
def detalle_propuesta(id):
    try:
        proposal = get_proposal_or_error(id)
    except LookupError:
        abort(404)

    return render_template(
        "detalle_propuesta.html",
        **build_proposal_detail_context(proposal, session.get("user_id"), request.args),
    )


@operations.route("/propuestas/<int:id>/postular", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@profile_complete_required
def postular_propuesta(id):
    mensaje = empty_to_none(request.form.get("mensaje"))
    experiencia_relevante = empty_to_none(request.form.get("experiencia_relevante"))
    disponibilidad = empty_to_none(request.form.get("disponibilidad"))
    pretension_economica = empty_to_none(request.form.get("pretension_economica"))

    if not mensaje:
        return redirect(url_for("operations.detalle_propuesta", id=id, error="Completa un mensaje para postularte."))

    try:
        application = apply_to_proposal(
            proposal_id=id,
            professional_user_id=session["user_id"],
            mensaje=mensaje,
            experiencia_relevante=experiencia_relevante,
            disponibilidad=disponibilidad,
            pretension_economica=pretension_economica,
        )
        notify_proposal_application_created(application)
    except ValueError as error:
        return redirect(url_for("operations.detalle_propuesta", id=id, error=str(error)))

    return redirect(url_for("operations.detalle_propuesta", id=id, postulada="1"))


@operations.route("/propuestas/<int:id>/aceptar/<int:application_id>", methods=["POST"])
@login_required
def aceptar_postulacion(id, application_id):
    try:
        application = accept_application(id, application_id, session["user_id"])
        notify_proposal_accepted(application)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return redirect(url_for("operations.detalle_propuesta", id=id, error=str(error)))

    return redirect(url_for("operations.detalle_propuesta", id=id))


@operations.route("/propuestas/<int:id>/descartar/<int:application_id>", methods=["POST"])
@login_required
def descartar_postulacion(id, application_id):
    try:
        application = discard_application(id, application_id, session["user_id"])
        notify_proposal_discarded(application)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return redirect(url_for("operations.detalle_propuesta", id=id, error=str(error)))

    return redirect(url_for("operations.detalle_propuesta", id=id))


@operations.route("/propuestas/<int:id>/cancelar", methods=["POST"])
@login_required
def cancelar_propuesta(id):
    try:
        proposal = cancel_proposal(id, session["user_id"])
        notify_proposal_cancelled(proposal)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return redirect(url_for("operations.detalle_propuesta", id=id, error=str(error)))

    return redirect(url_for("operations.detalle_propuesta", id=id))
