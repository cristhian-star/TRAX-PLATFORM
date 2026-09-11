from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
)
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.models.user import User
from app.services.subscription_service import has_pro_access
from app.services.verification_service import has_approved_verification
from app.services.payment_orchestration import (
    InMemoryPaymentOrchestrator,
    InvalidPaymentRequestError,
    PaymentObligation,
    PaymentOutcome,
)
from app.services.psp_simulator import (
    InMemoryPSPSimulator,
    ScenarioController,
    SimulationScenario,
)

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


_PAYMENT_SCENARIOS = {
    "APPROVED": SimulationScenario.APPROVED,
    "REJECTED": SimulationScenario.REJECTED,
    "PENDING": SimulationScenario.PENDING,
    "UNCERTAIN": SimulationScenario.UNCERTAIN,
}

_PAYMENT_RESULT_PRESENTATION = {
    PaymentOutcome.APPROVED: (
        "success",
        "Pago aprobado",
        "El adaptador informo una aprobacion financiera.",
    ),
    PaymentOutcome.REJECTED: (
        "danger",
        "Pago rechazado",
        "El adaptador informo un rechazo financiero.",
    ),
    PaymentOutcome.PENDING: (
        "warning",
        "Pago pendiente",
        "El intento existe, pero su resultado financiero sigue pendiente.",
    ),
    PaymentOutcome.RECONCILIATION_REQUIRED: (
        "warning",
        "Conciliacion requerida",
        "La respuesta de transporte fue incierta; no equivale a un rechazo.",
    ),
}


def _payment_form_values():
    return {
        "internal_reference": request.form.get("internal_reference", ""),
        "amount": request.form.get("amount", ""),
        "currency": request.form.get("currency", "ARS"),
        "idempotency_key": request.form.get("idempotency_key", ""),
        "scenario": request.form.get("scenario", "APPROVED"),
    }


def _payment_form_submission(values):
    errors = {}
    amount = None
    try:
        amount = Decimal(values["amount"].strip())
    except (InvalidOperation, AttributeError):
        errors["amount"] = "Ingresa un importe numerico valido."

    if not values["internal_reference"].strip():
        errors["internal_reference"] = "Ingresa una referencia interna."
    if not values["currency"].strip():
        errors["currency"] = "Ingresa una moneda."
    if not values["idempotency_key"].strip():
        errors["idempotency_key"] = "Ingresa una clave idempotente."
    elif values["idempotency_key"] != values["idempotency_key"].strip():
        errors["idempotency_key"] = "La clave no puede tener espacios al inicio o final."
    scenario = _PAYMENT_SCENARIOS.get(values["scenario"])
    if scenario is None:
        errors["scenario"] = "Selecciona un escenario valido."
    if errors:
        return None, None, errors

    try:
        obligation = PaymentObligation(
            internal_reference=values["internal_reference"],
            amount=amount,
            currency=values["currency"],
            idempotency_key=values["idempotency_key"],
        )
    except InvalidPaymentRequestError:
        errors["amount"] = "El importe debe ser mayor que cero y finito."
        return None, None, errors
    return obligation, scenario, errors


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


@dev.route("/dev/qa/payments/simulator", methods=["GET", "POST"])
def payment_simulator():
    _require_dev_qa_panel()

    values = {
        "internal_reference": "",
        "amount": "",
        "currency": "ARS",
        "idempotency_key": "",
        "scenario": "APPROVED",
    }
    errors = {}
    result = None
    presentation = None

    if request.method == "POST":
        values = _payment_form_values()
        obligation, scenario, errors = _payment_form_submission(values)
        if not errors:
            simulator = InMemoryPSPSimulator(
                id_factory=lambda: "dev-payment-attempt-001",
                clock=lambda: datetime.now(timezone.utc),
                scenario_controller=ScenarioController((scenario,)),
            )
            result = InMemoryPaymentOrchestrator(simulator).process(obligation)
            presentation = _PAYMENT_RESULT_PRESENTATION[result.outcome]

    return render_template(
        "dev_payment_simulator.html",
        form_values=values,
        errors=errors,
        result=result,
        presentation=presentation,
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
