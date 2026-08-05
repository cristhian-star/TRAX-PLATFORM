from urllib.parse import urlsplit

from flask import Blueprint, abort, render_template, request, redirect, session
from app.services.audit_service import create_audit_log, get_recent_audit_logs
from app.services.abuse_report_service import (
    create_abuse_report,
    get_open_reports,
    update_report_status
)
from app.services.category_service import (
    request_category,
    get_category_requests_summary,
    approve_category,
    get_explorable_categories,
)
from app.services.professional_service import (
    create_professional,
    complete_professional_profile,
    get_professional_by_user_id,
    search_professionals,
    get_professional_by_id
)
from app.utils.decorators import login_required, profile_complete_required, role_required
from app.utils.security import (
    ip_rate_limit_key,
    normalize_limited_text,
    paginate_items,
    user_rate_limit_key,
)
from app import limiter
from app.models.user import User
from app.models.professional_media import ProfessionalMedia
from app.services.subscription_service import cancel_subscription, has_pro_access, upgrade_to_pro
from app.services.verification_service import (
    create_or_update_professional_verification_request,
    create_verification_request,
    get_pending_verifications,
    has_approved_verification,
    update_verification_status
)
from app.services.reputation_service import get_user_reputation_score
from app.services.user_service import (
    ban_user,
    get_all_users,
    is_user_active,
    reactivate_user,
    suspend_user,
    update_user_role,
)
from app.services.review_service import (
    get_professional_average_rating,
    get_professional_reputation_metrics,
    get_professional_reviews,
)
from app.services.contract_review_moderation_service import (
    MODERATION_REASONS,
    exclude_contract_review_rating,
    get_pending_contract_review_moderation,
    moderate_contract_review_comment,
    report_contract_review,
)
from app.services.budget_service import (
    get_offer_allowance,
    get_professional_budget_offers,
)
from app.services.notification_service import (
    formatear_fecha_notificacion,
    obtener_notificaciones_usuario,
)
from app.services.coverage_service import (
    normalizar_cobertura,
    obtener_cobertura_profesional,
    obtener_opciones_radio,
)
from app.services.geographic_matching_service import (
    normalizar_coordenadas,
)
from app.services.google_maps_config_service import obtener_google_maps_api_key
from app.services.professional_media_service import (
    build_professional_media_context,
    get_pending_media,
    get_private_media_items,
    get_professionals_avatar_context,
    moderate_professional_media,
    reorder_professional_gallery,
    set_gallery_primary,
    soft_delete_professional_media,
    update_professional_media_metadata,
    upload_professional_media,
)
from app.services.whatsapp_contact_service import (
    normalizar_preferencia_contacto,
    normalizar_whatsapp_username,
    obtener_contactos_profesional,
)
from app.services.formal_negotiation_policy import (
    build_formal_negotiation_eligibility_map,
    evaluate_formal_negotiation_eligibility,
)
from app.services.client_dashboard_service import build_client_dashboard_context
from app.services.professional_view_service import (
    build_matching_results,
    calculate_private_profile_completion,
    get_professional_badges,
    get_professionals_badges,
    get_professionals_ratings,
    professional_user_id as get_professional_user_id,
    sort_professionals_for_listing,
)
from app.models.proposal_application import ProposalApplication

main = Blueprint("main", __name__)


EVIDENCE_OPTIONS = (
    ("fotos_trabajando", "Fotos del profesional ejecutando su profesion", "Link a fotos del profesional trabajando"),
    ("videos_trabajando", "Videos del profesional ejecutando su profesion", "Link a video o carpeta de Drive"),
    ("fotos_certificados", "Fotos de certificados", "Link a carpeta o archivo de certificados"),
    ("matricula_profesional", "Matricula profesional si posee", "Numero, link o referencia de matricula"),
    ("titulo_tecnico", "Titulo tecnico", "Link o referencia de titulo tecnico"),
    ("titulo_universitario", "Titulo universitario o de grado", "Link o referencia de titulo universitario"),
    ("material_adicional", "Material probatorio adicional", "Link externo, Drive o referencia adicional"),
)


def _empty_to_none(value):
    if value is None:
        return None

    value = value.strip()
    return value or None


def _parse_optional_int(value):
    value = _empty_to_none(value)

    if value is None:
        return None

    return int(value)


def _normalize_url(value, field_label, https_only=False):
    value = _empty_to_none(value)

    if value is None:
        return None

    parsed = urlsplit(value)
    allowed_schemes = {"https"} if https_only else {"http", "https"}

    if parsed.scheme.lower() not in allowed_schemes or not parsed.netloc:
        scheme_hint = "HTTPS" if https_only else "HTTP o HTTPS"
        raise ValueError(f"{field_label} debe ser una URL {scheme_hint} valida")

    return value


def _normalize_url_list(values, field_label, max_items=None, https_only=False):
    normalized = []

    for value in values:
        value = _empty_to_none(value)
        if value is None:
            continue

        normalized.append(_normalize_url(value, field_label, https_only=https_only))

    if max_items is not None and len(normalized) > max_items:
        raise ValueError(f"{field_label} admite hasta {max_items} URLs")

    return "\n".join(normalized) or None


def _build_evidence_text(form):
    selected_options = set(form.getlist("evidencia_opciones"))
    evidence_lines = []

    for key, label, _placeholder in EVIDENCE_OPTIONS:
        if key not in selected_options:
            continue

        detail = _empty_to_none(form.get(f"evidencia_{key}")) or "Sin detalle informado"
        evidence_lines.append(f"{label}: {detail}")

    return "\n".join(evidence_lines) or None


def _parse_ordered_ids(values):
    ordered_ids = []
    for value in values:
        value = _empty_to_none(value)
        if value is None:
            continue
        ordered_ids.append(int(value))

    return ordered_ids


def _profile_media_redirect():
    return redirect("/profesional/perfil/completar?media=1")


def _get_query_coordinates():
    latitude = request.args.get("latitude") or request.args.get("latitud") or request.args.get("lat")
    longitude = request.args.get("longitude") or request.args.get("longitud") or request.args.get("lng")
    return normalizar_coordenadas(latitude, longitude)


def _get_admin_user_rows():
    users = get_all_users()

    return [
        {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "rol": user.rol,
            "estado": user.estado,
            "motivo_estado": user.motivo_estado,
            "is_active": is_user_active(user),
            "reputation_score": get_user_reputation_score(user.id),
            "is_pro": has_pro_access(user.id),
            "is_verified": has_approved_verification(user.id),
        }
        for user in users
    ]


def _audit_admin_action(action, target_user_id=None, description=""):
    create_audit_log(
        actor_user_id=session["user_id"],
        action=action,
        target_user_id=target_user_id,
        description=description,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )


def _update_admin_user_role(user_id, new_role):
    target_user = User.query.get(user_id)

    if target_user is None:
        return "Usuario no encontrado", 404

    if (
        target_user.id == session.get("user_id")
        and target_user.rol == "SUPER_ADMIN"
        and new_role != "SUPER_ADMIN"
        and User.query.filter_by(rol="SUPER_ADMIN", estado="ACTIVO").count() <= 1
    ):
        return "No podes degradar al unico SUPER_ADMIN activo", 400

    previous_role = target_user.rol
    update_user_role(user_id, new_role)
    _audit_admin_action(
        "USER_ROLE_CHANGED",
        target_user_id=user_id,
        description=f"Rol actualizado de {previous_role} a {new_role}.",
    )
    return redirect("/admin/usuarios")


@main.route("/")
def home():
    if session.get("user_id"):
        return render_template("home_logged.html")

    return render_template("home.html")


@main.route("/buscar", methods=["GET"])
@limiter.limit("60 per minute", key_func=ip_rate_limit_key)
def buscar():
    servicio = normalize_limited_text(request.args.get("servicio", ""))
    zona = normalize_limited_text(request.args.get("zona", ""))

    resultados = search_professionals(servicio, zona)
    coordinates = _get_query_coordinates()
    professional_badges = get_professionals_badges(resultados)
    professional_ratings = get_professionals_ratings(resultados)
    matching_results = build_matching_results(resultados, coordinates)
    resultados = sort_professionals_for_listing(
        resultados,
        professional_badges,
        professional_ratings,
        matching_results,
        coordinates,
    )
    resultados = paginate_items(resultados)
    professional_media = get_professionals_avatar_context(resultados)
    formal_negotiation_eligibility = (
        build_formal_negotiation_eligibility_map(
            resultados,
            session.get("user_id"),
        )
    )

    return render_template(
        "resultados.html",
        resultados=resultados,
        servicio=servicio,
        zona=zona,
        professional_badges=professional_badges,
        professional_ratings=professional_ratings,
        matching_results=matching_results,
        professional_media=professional_media,
        formal_negotiation_eligibility=formal_negotiation_eligibility,
        has_geographic_context=coordinates is not None,
    )


@main.route("/resultados")
@limiter.limit("60 per minute", key_func=ip_rate_limit_key)
def listado_profesionales():
    servicio = normalize_limited_text(request.args.get("servicio", ""))
    zona = normalize_limited_text(request.args.get("zona", ""))

    resultados = search_professionals(servicio, zona)
    coordinates = _get_query_coordinates()
    professional_badges = get_professionals_badges(resultados)
    professional_ratings = get_professionals_ratings(resultados)
    matching_results = build_matching_results(resultados, coordinates)
    resultados = sort_professionals_for_listing(
        resultados,
        professional_badges,
        professional_ratings,
        matching_results,
        coordinates,
    )
    resultados = paginate_items(resultados)
    professional_media = get_professionals_avatar_context(resultados)
    formal_negotiation_eligibility = (
        build_formal_negotiation_eligibility_map(
            resultados,
            session.get("user_id"),
        )
    )

    return render_template(
        "listado_profesionales.html",
        resultados=resultados,
        servicio=servicio,
        zona=zona,
        professional_badges=professional_badges,
        professional_ratings=professional_ratings,
        matching_results=matching_results,
        professional_media=professional_media,
        formal_negotiation_eligibility=formal_negotiation_eligibility,
        has_geographic_context=coordinates is not None,
    )


@main.route("/explorar")
@limiter.limit("60 per minute", key_func=ip_rate_limit_key)
def explorar_rubros():
    industria = normalize_limited_text(request.args.get("industria", ""))
    rubro_seleccionado = normalize_limited_text(request.args.get("rubro", ""))
    rubros_disponibles = get_explorable_categories()
    rubros = rubros_disponibles

    if industria:
        rubros = [
            rubro
            for rubro in rubros
            if rubro["industria"].casefold() == industria.casefold()
        ]

    if rubro_seleccionado:
        rubros = [
            rubro
            for rubro in rubros
            if rubro["nombre"].casefold() == rubro_seleccionado.casefold()
        ]

    return render_template(
        "explorar_rubros.html",
        rubros=paginate_items(rubros),
        rubros_disponibles=rubros_disponibles,
        industria=industria,
        rubro_seleccionado=rubro_seleccionado,
    )


@main.route("/mercados")
def mercados():
    return render_template("mercados.html")


@main.route("/planes")
def planes():
    return render_template("planes.html")




@main.route("/profesional/pro/upgrade", methods=["GET", "POST"])
@login_required
@role_required("PROFESIONAL")
@profile_complete_required
def upgrade_pro():
    user_id = session["user_id"]
    reputation_score = get_user_reputation_score(user_id)
    is_verified = has_approved_verification(user_id)
    is_pro = has_pro_access(user_id)
    is_eligible = reputation_score >= 100 or is_verified
    error = None

    if request.method == "POST":
        if is_eligible:
            upgrade_to_pro(user_id)
            return redirect("/profesional/dashboard?pro_upgraded=1")

        error = "Necesitas reputacion minima de 100 puntos o verificacion aprobada para pasar a TRAX PRO."

    return render_template(
        "solicitar_upgrade_pro.html",
        reputation_score=reputation_score,
        is_verified=is_verified,
        is_pro=is_pro,
        is_eligible=is_eligible,
        error=error
    )

@main.route("/profesional/perfil/completar", methods=["GET", "POST"])
@login_required
@role_required("PROFESIONAL")
def completar_perfil_profesional():
    user_id = session["user_id"]
    professional = get_professional_by_user_id(user_id)

    if request.method == "POST":
        especialidad = _empty_to_none(request.form.get("especialidad"))

        if not especialidad:
            return "Especialidad requerida", 400

        try:
            anios_experiencia = _parse_optional_int(request.form.get("anios_experiencia"))
        except ValueError:
            return "Anios de experiencia invalidos", 400

        evidence_text = _build_evidence_text(request.form)
        certificaciones_text = _empty_to_none(request.form.get("certificaciones_text"))
        portfolio_urls = _empty_to_none(request.form.get("portfolio_urls"))

        try:
            coverage_data = normalizar_cobertura(request.form)
            logo_url = _normalize_url(
                request.form.get("logo_url"),
                "Logo",
                https_only=True,
            )
            cover_url = _normalize_url(
                request.form.get("cover_url"),
                "Portada",
                https_only=True,
            )
            gallery_urls = _normalize_url_list(
                request.form.getlist("gallery_urls"),
                "Galeria",
                max_items=12,
                https_only=True,
            )
            google_drive_url = _normalize_url(
                request.form.get("google_drive_url"),
                "Google Drive",
            )
            website_url = _normalize_url(
                request.form.get("website_url"),
                "Sitio web",
            )
            instagram_url = _normalize_url(
                request.form.get("instagram_url"),
                "Instagram",
            )
            tiktok_url = _normalize_url(
                request.form.get("tiktok_url"),
                "TikTok",
            )
            youtube_url = _normalize_url(
                request.form.get("youtube_url"),
                "YouTube",
            )
            other_links = _normalize_url_list(
                request.form.get("other_links", "").splitlines(),
                "Otros enlaces",
            )
            whatsapp_username = normalizar_whatsapp_username(request.form.get("whatsapp_username"))
            whatsapp_contact_preference = normalizar_preferencia_contacto(
                request.form.get("whatsapp_contact_preference")
            )
        except ValueError as error:
            return str(error), 400

        professional = complete_professional_profile(
            user_id=user_id,
            nombre=session.get("user_name", "Profesional TRAX"),
            especialidad=especialidad,
            anios_experiencia=anios_experiencia,
            tipo_credencial=_empty_to_none(request.form.get("tipo_credencial")),
            numero_credencial=_empty_to_none(request.form.get("numero_credencial")),
            certificaciones_text=certificaciones_text,
            portfolio_urls=portfolio_urls,
            logo_url=logo_url,
            cover_url=cover_url,
            gallery_urls=gallery_urls,
            google_drive_url=google_drive_url,
            website_url=website_url,
            instagram_url=instagram_url,
            tiktok_url=tiktok_url,
            youtube_url=youtube_url,
            other_links=other_links,
            whatsapp_username=whatsapp_username,
            whatsapp_contact_preference=whatsapp_contact_preference,
            **coverage_data,
        )

        create_or_update_professional_verification_request(
            user_id=user_id,
            certificado_oficio=certificaciones_text,
            titulo_profesional=_empty_to_none(request.form.get("tipo_credencial")),
            material_probatorio=evidence_text or portfolio_urls,
            observaciones=(
                f"Especialidad: {professional.especialidad}\n"
                f"Anios de experiencia: {professional.anios_experiencia or 0}\n"
                f"Portfolio: {professional.portfolio_urls or 'No informado'}"
            )
        )

        return redirect("/profesional/dashboard?profile_completed=1")

    return render_template(
        "completar_perfil_profesional.html",
        professional=professional,
        evidence_options=EVIDENCE_OPTIONS,
        is_pro=has_pro_access(user_id),
        is_verified=has_approved_verification(user_id),
        average_rating=get_professional_average_rating(professional.id) if professional else None,
        review_count=len(get_professional_reviews(professional.id)) if professional else 0,
        coverage=obtener_cobertura_profesional(professional),
        coverage_radius_options=obtener_opciones_radio(),
        google_maps_api_key=obtener_google_maps_api_key(),
        professional_media=build_professional_media_context(professional),
        private_media_items=get_private_media_items(professional),
        profile_completion=calculate_private_profile_completion(
            professional,
            has_approved_verification(user_id),
        ),
    )


@main.route("/profesional/media/avatar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("20 per hour", key_func=user_rate_limit_key)
def subir_avatar_profesional():
    image = request.files.get("image")
    if image is None:
        return "Imagen requerida", 400

    try:
        upload_professional_media(
            session["user_id"],
            image,
            ProfessionalMedia.TYPE_AVATAR,
            title=request.form.get("title"),
            description=request.form.get("description"),
            alt_text=request.form.get("alt_text"),
            category=request.form.get("category"),
        )
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/media/portada", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("20 per hour", key_func=user_rate_limit_key)
def subir_portada_profesional():
    image = request.files.get("image")
    if image is None:
        return "Imagen requerida", 400

    try:
        upload_professional_media(
            session["user_id"],
            image,
            ProfessionalMedia.TYPE_COVER,
            title=request.form.get("title"),
            description=request.form.get("description"),
            alt_text=request.form.get("alt_text"),
            category=request.form.get("category"),
        )
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/media/galeria", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def subir_galeria_profesional():
    image = request.files.get("image")
    if image is None:
        return "Imagen requerida", 400

    try:
        upload_professional_media(
            session["user_id"],
            image,
            ProfessionalMedia.TYPE_GALLERY,
            title=request.form.get("title"),
            description=request.form.get("description"),
            alt_text=request.form.get("alt_text"),
            category=request.form.get("category"),
        )
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/media/<int:id>/editar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("60 per hour", key_func=user_rate_limit_key)
def editar_media_profesional(id):
    try:
        update_professional_media_metadata(
            session["user_id"],
            id,
            title=request.form.get("title"),
            description=request.form.get("description"),
            alt_text=request.form.get("alt_text"),
            category=request.form.get("category"),
        )
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/media/reordenar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def reordenar_media_profesional():
    try:
        ordered_ids = _parse_ordered_ids(request.form.getlist("media_ids"))
        reorder_professional_gallery(session["user_id"], ordered_ids)
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/media/<int:id>/principal", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def marcar_media_principal(id):
    try:
        set_gallery_primary(session["user_id"], id)
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/media/<int:id>/eliminar", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def eliminar_media_profesional(id):
    try:
        soft_delete_professional_media(session["user_id"], id)
    except PermissionError:
        return "No autorizado", 403
    except ValueError as error:
        return str(error), 400

    return _profile_media_redirect()


@main.route("/profesional/verificacion/solicitar", methods=["GET", "POST"])
@login_required
@role_required("PROFESIONAL")
def solicitar_verificacion():
    if request.method == "POST":
        create_verification_request(
            user_id=session["user_id"],
            tipo_usuario=request.form.get("tipo_usuario"),
            documento_identidad=request.form.get("documento_identidad"),
            certificado_oficio=request.form.get("certificado_oficio"),
            titulo_profesional=request.form.get("titulo_profesional"),
            material_probatorio=request.form.get("material_probatorio"),
            observaciones=request.form.get("observaciones")
        )

        return redirect("/profesional/dashboard?verification_requested=1")

    return render_template(
        "solicitar_verificacion.html",
        is_verified=has_approved_verification(session.get("user_id"))
    )

@main.route("/profesional/dashboard")
@role_required("PROFESIONAL")
def profesional_dashboard():
    user_id = session.get("user_id")
    professional = get_professional_by_user_id(user_id)
    reviews = get_professional_reviews(professional.id) if professional else []
    average_rating = get_professional_average_rating(professional.id) if professional else None
    budget_offers = get_professional_budget_offers(user_id) if user_id else []
    awarded_budget_offers = [
        offer for offer in budget_offers if offer.estado == "ADJUDICADO"
    ]
    proposal_applications = (
        ProposalApplication.query
        .filter_by(professional_user_id=user_id)
        .order_by(ProposalApplication.created_at.desc(), ProposalApplication.id.desc())
        .all()
        if user_id else []
    )
    accepted_proposal_applications = [
        application for application in proposal_applications if application.estado == "ACEPTADA"
    ]
    coverage = obtener_cobertura_profesional(professional)

    recommendations = []
    if not professional:
        recommendations.append("Completa tu perfil profesional para aparecer en el marketplace.")
    else:
        if not professional.perfil_completo:
            recommendations.append("Completa datos clave de tu oficio y experiencia.")
        if not professional.descripcion:
            recommendations.append("Agrega una descripcion clara de tus servicios.")
        if not professional.perfil_completo:
            recommendations.append("Revisa que tu perfil publico este completo antes de competir por mas oportunidades.")
        if not has_approved_verification(user_id):
            recommendations.append("Solicita verificacion para reforzar confianza en contrataciones.")
        if not reviews:
            recommendations.append("Impulsa tus primeras reseÃ±as cerrando trabajos dentro de TRAX.")
        if not coverage["configured"]:
            recommendations.append("Configura tu zona de cobertura para que los clientes entiendan donde trabajas.")

    return render_template(
        "profesional_dashboard.html",
        verification_requested=request.args.get("verification_requested") == "1",
        profile_completed=request.args.get("profile_completed") == "1",
        professional=professional,
        is_profile_complete=bool(professional and professional.perfil_completo),
        is_verified=has_approved_verification(session.get("user_id")),
        is_pro=has_pro_access(session.get("user_id")),
        pro_upgraded=request.args.get("pro_upgraded") == "1",
        average_rating=average_rating,
        review_count=len(reviews),
        budget_offers_count=len(budget_offers),
        awarded_budget_offers_count=len(awarded_budget_offers),
        proposal_applications_count=len(proposal_applications),
        accepted_proposal_applications_count=len(accepted_proposal_applications),
        offer_allowance=get_offer_allowance(user_id) if user_id else None,
        coverage=coverage,
        recommendations=recommendations,
        whatsapp_contact_sessions=obtener_contactos_profesional(professional.id, limit=5)
        if professional else [],
        recent_activity=obtener_notificaciones_usuario(user_id, limit=5) if user_id else [],
        format_notification_date=formatear_fecha_notificacion,
    )


@main.route("/cliente/dashboard")
@role_required("CLIENTE")
def cliente_dashboard():
    user_id = session.get("user_id")
    return render_template(
        "cliente_dashboard.html",
        **build_client_dashboard_context(user_id),
    )


@main.route("/admin/dashboard")
@role_required("SUPER_ADMIN")
def admin_dashboard():
    return render_template("admin_dashboard.html")




@main.route("/reportar/usuario/<int:id>", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per day", methods=["POST"], key_func=user_rate_limit_key)
def reportar_usuario(id):
    profesional = get_professional_by_id(id)

    if profesional is None:
        return "Usuario no encontrado", 404

    if request.method == "POST":
        professional_user_id = get_professional_user_id(profesional)

        if not professional_user_id:
            return "Perfil profesional sin propietario asociado", 409

        if professional_user_id == session["user_id"]:
            return "No podes reportarte a vos mismo", 400

        create_abuse_report(
            reporter_id=session["user_id"],
            reported_user_id=professional_user_id,
            motivo=request.form.get("motivo"),
            descripcion=request.form.get("descripcion")
        )

        return redirect(f"/profesional/{id}?reported=1")

    return render_template(
        "reportar_usuario.html",
        profesional=profesional,
        reported_user_id=id
    )

@main.route("/profesional/<int:id>/review", methods=["GET", "POST"])
def crear_review(id):
    return (
        "El flujo legacy de resenas fue retirado. "
        "Las reviews se crean desde una contratacion confirmada.",
        410,
    )

@main.route("/profesional/<int:id>")
def perfil_profesional(id):
    profesional = get_professional_by_id(id)

    if profesional is None:
        return "Profesional no encontrado", 404

    reviews = get_professional_reviews(id)
    reputation_metrics = get_professional_reputation_metrics(id)
    formal_negotiation_allowed = (
        evaluate_formal_negotiation_eligibility(
            session.get("user_id"),
            profesional,
        ).allowed
    )

    return render_template(
        "perfil_profesional.html",
        profesional=profesional,
        profile_badges=get_professional_badges(profesional),
        reviews=reviews,
        average_rating=reputation_metrics.average_eligible_rating,
        review_count=reputation_metrics.eligible_rating_count,
        reputation_metrics=reputation_metrics,
        coverage=obtener_cobertura_profesional(profesional),
        google_maps_api_key=obtener_google_maps_api_key(),
        professional_media=build_professional_media_context(profesional),
        formal_negotiation_allowed=formal_negotiation_allowed,
        report_created=request.args.get("reported") == "1"
    )


@main.route("/profesionales/nuevo", methods=["GET"])
@login_required
def nuevo_profesional():
    if get_professional_by_user_id(session["user_id"]):
        return redirect("/profesional/perfil/completar")

    return render_template("nuevo_profesional.html")


@main.route("/profesionales/crear", methods=["POST"])
@login_required
def guardar_profesional():
    nombre = request.form.get("nombre")
    servicio = request.form.get("servicio")
    zona = request.form.get("zona")
    telefono = request.form.get("telefono")
    descripcion = request.form.get("descripcion")

    professional = create_professional(
        session["user_id"],
        nombre,
        servicio,
        zona,
        telefono,
        descripcion
    )

    if professional is None:
        return redirect("/profesional/perfil/completar")

    return "Profesional creado correctamente"


@main.route("/rubros/solicitar", methods=["POST"])
@limiter.limit("5 per hour", key_func=ip_rate_limit_key)
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




@main.route("/admin/usuarios")
@role_required("SUPER_ADMIN")
def admin_usuarios():
    return render_template(
        "admin_usuarios.html",
        usuarios=_get_admin_user_rows()
    )

@main.route("/admin/usuarios/<int:id>/rol/cliente", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_rol_cliente(id):
    return _update_admin_user_role(id, "CLIENTE")


@main.route("/admin/usuarios/<int:id>/rol/profesional", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_rol_profesional(id):
    return _update_admin_user_role(id, "PROFESIONAL")


@main.route("/admin/usuarios/<int:id>/rol/super-admin", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_rol_super_admin(id):
    return _update_admin_user_role(id, "SUPER_ADMIN")


@main.route("/admin/usuarios/<int:id>/suspender", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_suspender(id):
    if id == session.get("user_id"):
        return "No podes suspender tu propia cuenta", 400

    motivo = request.form.get("motivo", "")
    if suspend_user(id, motivo) is None:
        return "Usuario no encontrado", 404

    _audit_admin_action("USER_SUSPENDED", id, motivo or "Cuenta suspendida por administracion.")
    return redirect("/admin/usuarios")


@main.route("/admin/usuarios/<int:id>/reactivar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_reactivar(id):
    if reactivate_user(id) is None:
        return "Usuario no encontrado", 404

    _audit_admin_action("USER_REACTIVATED", id, "Cuenta reactivada por administracion.")
    return redirect("/admin/usuarios")


@main.route("/admin/usuarios/<int:id>/banear", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_banear(id):
    if id == session.get("user_id"):
        return "No podes banear tu propia cuenta", 400

    motivo = request.form.get("motivo", "")
    if ban_user(id, motivo) is None:
        return "Usuario no encontrado", 404

    _audit_admin_action("USER_BANNED", id, motivo or "Cuenta baneada por administracion.")
    return redirect("/admin/usuarios")


@main.route("/admin/usuarios/<int:id>/activar-pro", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_activar_pro(id):
    if User.query.get(id) is None:
        return "Usuario no encontrado", 404

    upgrade_to_pro(id)
    _audit_admin_action("USER_PRO_ACTIVATED", id, "Acceso TRAX PRO activado.")
    return redirect("/admin/usuarios")


@main.route("/admin/usuarios/<int:id>/quitar-pro", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_usuario_quitar_pro(id):
    if User.query.get(id) is None:
        return "Usuario no encontrado", 404

    subscription = cancel_subscription(id)
    if subscription is not None:
        _audit_admin_action("USER_PRO_REMOVED", id, "Acceso TRAX PRO removido.")
    return redirect("/admin/usuarios")


@main.route("/admin/auditoria")
@role_required("SUPER_ADMIN")
def admin_auditoria():
    return render_template("admin_auditoria.html", audit_logs=get_recent_audit_logs())


@main.route("/admin/moderacion")
@role_required("SUPER_ADMIN")
def admin_moderacion():
    return render_template(
        "admin_moderacion.html",
        reportes=get_open_reports(),
        verificaciones=get_pending_verifications(),
        media_pendientes=get_pending_media(),
        contract_reviews=get_pending_contract_review_moderation(
            actor_user_id=session["user_id"]
        ),
        contract_review_moderation_reasons=sorted(MODERATION_REASONS),
    )


@main.route("/reviews/<int:id>/reportar", methods=["POST"])
@login_required
def reportar_review_contractual(id):
    try:
        review = report_contract_review(id, actor_user_id=session["user_id"])
    except LookupError:
        abort(404)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return str(error), 400
    return redirect(f"/profesional/{review.professional_id}#review-{review.id}")


@main.route("/admin/reviews/<int:id>/comentario", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_moderar_comentario_review(id):
    try:
        moderate_contract_review_comment(
            id,
            actor_user_id=session["user_id"],
            action=request.form.get("action"),
            reason=request.form.get("reason"),
            redacted_comment=request.form.get("redacted_comment"),
        )
    except LookupError:
        abort(404)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return str(error), 400
    return redirect("/admin/moderacion")


@main.route("/admin/reviews/<int:id>/rating/excluir", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_excluir_rating_review(id):
    try:
        exclude_contract_review_rating(
            id,
            actor_user_id=session["user_id"],
            reason=request.form.get("reason"),
        )
    except LookupError:
        abort(404)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return str(error), 400
    return redirect("/admin/moderacion")


@main.route("/admin/reportes/<int:id>/resolver", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_resolver_reporte(id):
    report = update_report_status(id, "RESUELTO", reviewed_by=session.get("user_id"))
    if report is not None:
        _audit_admin_action("REPORT_RESOLVED", report.reported_user_id, f"Reporte #{id} resuelto.")
    return redirect("/admin/moderacion")


@main.route("/admin/reportes/<int:id>/descartar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_descartar_reporte(id):
    report = update_report_status(id, "DESCARTADO", reviewed_by=session.get("user_id"))
    if report is not None:
        _audit_admin_action("REPORT_DISCARDED", report.reported_user_id, f"Reporte #{id} descartado.")
    return redirect("/admin/moderacion")


@main.route("/admin/media/<int:id>/publicar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_publicar_media(id):
    media = moderate_professional_media(
        id,
        ProfessionalMedia.STATUS_PUBLISHED,
        admin_user_id=session.get("user_id"),
        reason=request.form.get("motivo"),
    )
    if media is not None:
        _audit_admin_action("PROFESSIONAL_MEDIA_PUBLISHED", media.professional.user_id, f"Media #{id} publicada.")
    return redirect("/admin/moderacion")


@main.route("/admin/media/<int:id>/rechazar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_rechazar_media(id):
    media = moderate_professional_media(
        id,
        ProfessionalMedia.STATUS_REJECTED,
        admin_user_id=session.get("user_id"),
        reason=request.form.get("motivo"),
    )
    if media is not None:
        _audit_admin_action("PROFESSIONAL_MEDIA_REJECTED", media.professional.user_id, f"Media #{id} rechazada.")
    return redirect("/admin/moderacion")


@main.route("/admin/media/<int:id>/ocultar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_ocultar_media(id):
    media = moderate_professional_media(
        id,
        ProfessionalMedia.STATUS_HIDDEN,
        admin_user_id=session.get("user_id"),
        reason=request.form.get("motivo"),
    )
    if media is not None:
        _audit_admin_action("PROFESSIONAL_MEDIA_HIDDEN", media.professional.user_id, f"Media #{id} ocultada.")
    return redirect("/admin/moderacion")


@main.route("/admin/media/<int:id>/restaurar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_restaurar_media(id):
    media = moderate_professional_media(
        id,
        ProfessionalMedia.STATUS_PUBLISHED,
        admin_user_id=session.get("user_id"),
        reason=request.form.get("motivo"),
    )
    if media is not None:
        _audit_admin_action("PROFESSIONAL_MEDIA_RESTORED", media.professional.user_id, f"Media #{id} restaurada.")
    return redirect("/admin/moderacion")


@main.route("/admin/verificaciones/<int:id>/aprobar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_aprobar_verificacion(id):
    verification = update_verification_status(id, "APROBADO", reviewer_id=session.get("user_id"))
    if verification is not None:
        _audit_admin_action("VERIFICATION_APPROVED", verification.user_id, f"Verificacion #{id} aprobada.")
    return redirect("/admin/moderacion")


@main.route("/admin/verificaciones/<int:id>/observar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_observar_verificacion(id):
    verification = update_verification_status(id, "OBSERVADO", reviewer_id=session.get("user_id"))
    if verification is not None:
        _audit_admin_action("VERIFICATION_OBSERVED", verification.user_id, f"Verificacion #{id} observada.")
    return redirect("/admin/moderacion")


@main.route("/admin/verificaciones/<int:id>/rechazar", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_rechazar_verificacion(id):
    verification = update_verification_status(id, "RECHAZADO", reviewer_id=session.get("user_id"))
    if verification is not None:
        _audit_admin_action("VERIFICATION_REJECTED", verification.user_id, f"Verificacion #{id} rechazada.")
    return redirect("/admin/moderacion")

@main.route("/admin/rubros")
@role_required("SUPER_ADMIN")
def admin_rubros():
    rubros = get_category_requests_summary()
    return render_template("admin_rubros.html", rubros=rubros)

@main.route("/admin/rubros/aprobar/<nombre_rubro>", methods=["POST"])
@role_required("SUPER_ADMIN")
@limiter.limit("30 per hour", key_func=user_rate_limit_key)
def admin_aprobar_rubro(nombre_rubro):
    approve_category(nombre_rubro)
    return redirect("/admin/rubros")
