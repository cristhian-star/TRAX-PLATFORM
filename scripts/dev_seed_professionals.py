import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models.professional import Professional
from app.models.user import User
from app.services.pro_time import as_utc_naive, utc_now


DEMO_PASSWORD = os.environ.get("TRAX_DEMO_PASSWORD", "TraxDemo2026!")
DEMO_MARKER = "[DEV_SEED_PROFESSIONALS_V1]"
QA_PRO_EMAIL = "electricidad.pro@demo.trax.local"
QA_PRO_DURATION = timedelta(days=365)

DEMO_CLIENT = {
    "email": "cliente.demo@trax.local",
    "nombre": "Cliente Demo MANDOBRA",
}

DEMO_PROFESSIONALS = (
    {
        "email": "electricidad.pro@demo.trax.local",
        "nombre": "Nexo Electrico",
        "servicio": "Electricidad",
        "especialidad": "Electricista matriculado",
        "zona": "CABA y Zona Norte",
        "telefono": "5491100001001",
        "descripcion": (
            "Instalaciones electricas, tableros, mantenimiento preventivo "
            "y diagnostico para hogares, comercios y consorcios."
        ),
        "anios_experiencia": 12,
        "tipo_credencial": "Matricula profesional",
        "numero_credencial": "DEV-ELEC-001",
        "certificaciones_text": (
            "Credenciales demo para validar la presentacion visual. "
            "No representan una habilitacion real."
        ),
        "portfolio_urls": "\n".join(
            (
                "https://drive.google.com/drive/folders/TRAX_DEMO_ELECTRICIDAD",
                "https://example.com/trax-demo/nexo-electrico",
                "https://www.youtube.com/@trax-demo-electricidad",
            )
        ),
        "is_pro": True,
        "reputation_events": (
            ("VERIFICACION_APROBADA", 30, "Verificacion demo aprobada"),
            ("TRABAJO_COMPLETADO", 45, "Trabajos demo completados"),
            ("REVIEW_POSITIVA", 15, "Valoraciones demo positivas"),
        ),
    },
    {
        "email": "plomeria.work@demo.trax.local",
        "nombre": "Punto Agua",
        "servicio": "Plomeria",
        "especialidad": "Plomero residencial y comercial",
        "zona": "CABA",
        "telefono": "5491100001002",
        "descripcion": (
            "Reparaciones de perdidas, instalaciones sanitarias, mantenimiento "
            "y soluciones de plomeria para viviendas y locales."
        ),
        "anios_experiencia": 8,
        "tipo_credencial": "Certificado de oficio",
        "numero_credencial": "DEV-PLOM-002",
        "certificaciones_text": (
            "Certificacion demo de oficio para visualizar credenciales en MANDOBRA."
        ),
        "portfolio_urls": "\n".join(
            (
                "https://example.com/trax-demo/punto-agua",
                "https://www.instagram.com/trax.demo.plomeria/",
            )
        ),
        "is_pro": False,
        "reputation_events": (
            ("VERIFICACION_APROBADA", 20, "Verificacion demo aprobada"),
            ("TRABAJO_COMPLETADO", 25, "Trabajos demo completados"),
        ),
    },
    {
        "email": "refrigeracion.pro@demo.trax.local",
        "nombre": "Clima Tecnico",
        "servicio": "Refrigeracion A/C",
        "especialidad": "Tecnico en refrigeracion y climatizacion",
        "zona": "CABA y GBA",
        "telefono": "5491100001003",
        "descripcion": (
            "Instalacion, mantenimiento y reparacion de equipos de aire "
            "acondicionado y sistemas de refrigeracion."
        ),
        "anios_experiencia": 10,
        "tipo_credencial": "Titulo tecnico",
        "numero_credencial": "DEV-REFR-003",
        "certificaciones_text": (
            "Titulo tecnico demo y capacitaciones de climatizacion para QA visual."
        ),
        "portfolio_urls": "\n".join(
            (
                "https://drive.google.com/drive/folders/TRAX_DEMO_REFRIGERACION",
                "https://example.com/trax-demo/clima-tecnico",
                "https://www.tiktok.com/@trax.demo.refrigeracion",
            )
        ),
        "is_pro": True,
        "reputation_events": (
            ("VERIFICACION_APROBADA", 30, "Verificacion demo aprobada"),
            ("TRABAJO_COMPLETADO", 40, "Trabajos demo completados"),
            ("REVIEW_POSITIVA", 10, "Valoraciones demo positivas"),
        ),
    },
)


def _load_optional_models():
    models = {}

    try:
        from app.models.subscription import Subscription

        models["subscription"] = Subscription
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.models.verification_request import VerificationRequest

        models["verification"] = VerificationRequest
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.models.reputation_event import ReputationEvent

        models["reputation"] = ReputationEvent
    except (ImportError, ModuleNotFoundError):
        pass

    return models


def _upsert_user(data):
    user = User.query.filter_by(email=data["email"]).first()
    created = user is None

    if created:
        user = User(
            nombre=data["nombre"],
            email=data["email"],
            password=generate_password_hash(DEMO_PASSWORD),
            rol="PROFESIONAL",
            estado="ACTIVO",
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.nombre = data["nombre"]
        user.rol = "PROFESIONAL"
        user.estado = "ACTIVO"
        user.motivo_estado = None
        user.password = generate_password_hash(DEMO_PASSWORD)

    return user, created


def _upsert_demo_client():
    user = User.query.filter_by(email=DEMO_CLIENT["email"]).first()
    created = user is None

    if created:
        user = User(
            nombre=DEMO_CLIENT["nombre"],
            email=DEMO_CLIENT["email"],
            password=generate_password_hash(DEMO_PASSWORD),
            rol="CLIENTE",
            estado="ACTIVO",
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.nombre = DEMO_CLIENT["nombre"]
        user.rol = "CLIENTE"
        user.estado = "ACTIVO"
        user.motivo_estado = None
        user.password = generate_password_hash(DEMO_PASSWORD)

    return user, created


def _upsert_professional(user, data):
    professional = Professional.query.filter_by(user_id=user.id).first()
    created = professional is None

    if created:
        professional = Professional(user_id=user.id)
        db.session.add(professional)

    professional.nombre = data["nombre"]
    professional.servicio = data["servicio"]
    professional.especialidad = data["especialidad"]
    professional.zona = data["zona"]
    professional.telefono = data["telefono"]
    professional.descripcion = data["descripcion"]
    professional.anios_experiencia = data["anios_experiencia"]
    professional.tipo_credencial = data["tipo_credencial"]
    professional.numero_credencial = data["numero_credencial"]
    professional.certificaciones_text = data["certificaciones_text"]
    professional.portfolio_urls = data["portfolio_urls"]
    professional.perfil_completo = True
    professional.estado_perfil = "VERIFICADO"

    return professional, created


def _sync_demo_pro_subscription(
    subscription_model,
    user_id,
    should_have_pro,
    now=None,
):
    evaluated_at = as_utc_naive(now or utc_now())
    pro_subscriptions = (
        subscription_model.query
        .filter_by(user_id=user_id, plan="PRO")
        .order_by(subscription_model.started_at.desc())
        .all()
    )
    qa_source = next(
        (
            item for item in pro_subscriptions
            if item.source_type == "SUBSCRIPTION"
        ),
        None,
    )

    created = False
    if should_have_pro and qa_source is None:
        qa_source = subscription_model(
            user_id=user_id,
            plan="PRO",
            estado="ACTIVA",
            started_at=evaluated_at,
            source_type="SUBSCRIPTION",
            expires_at=evaluated_at + QA_PRO_DURATION,
            auto_renew=False,
        )
        db.session.add(qa_source)
        pro_subscriptions.append(qa_source)
        created = True

    qa_source_is_current = (
        qa_source is not None
        and qa_source.estado == "ACTIVA"
        and qa_source.expires_at is not None
        and as_utc_naive(qa_source.expires_at) > evaluated_at
    )
    for subscription in pro_subscriptions:
        if should_have_pro and subscription is qa_source:
            subscription.estado = "ACTIVA"
            subscription.source_type = "SUBSCRIPTION"
            if not qa_source_is_current:
                subscription.started_at = evaluated_at
                subscription.expires_at = evaluated_at + QA_PRO_DURATION
            subscription.auto_renew = False
        elif subscription.estado == "ACTIVA":
            subscription.estado = "CANCELADA"
            subscription.auto_renew = False

    return created


def _ensure_verification(verification_model, user_id, data):
    approved = (
        verification_model.query
        .filter_by(user_id=user_id, tipo_usuario="PROFESIONAL", estado="APROBADO")
        .order_by(verification_model.created_at.desc())
        .first()
    )

    if approved is None:
        approved = verification_model(
            user_id=user_id,
            tipo_usuario="PROFESIONAL",
            certificado_oficio=data["certificaciones_text"],
            titulo_profesional=data["tipo_credencial"],
            material_probatorio=data["portfolio_urls"],
            estado="APROBADO",
            observaciones=f"{DEMO_MARKER} Verificacion aprobada para datos demo.",
            reviewed_at=datetime.now(timezone.utc),
        )
        db.session.add(approved)
        return True

    return False


def _ensure_client_verification(verification_model, user_id):
    approved = (
        verification_model.query
        .filter_by(
            user_id=user_id,
            tipo_usuario="CLIENTE",
            estado="APROBADO",
        )
        .order_by(verification_model.created_at.desc())
        .first()
    )
    if approved is not None:
        return False

    db.session.add(
        verification_model(
            user_id=user_id,
            tipo_usuario="CLIENTE",
            documento_identidad="DEV-CLIENT-IDENTITY",
            estado="APROBADO",
            observaciones=(
                f"{DEMO_MARKER} Verificacion cliente aprobada para QA local."
            ),
            reviewed_at=datetime.now(timezone.utc),
        )
    )
    return True


def seed_professionals(now=None):
    optional_models = _load_optional_models()
    summary = {
        "users_created": 0,
        "clients_created": 0,
        "professionals_created": 0,
        "subscriptions_created": 0,
        "verifications_created": 0,
        "reputation_events_created": 0,
    }

    demo_client, client_created = _upsert_demo_client()
    summary["users_created"] += int(client_created)
    summary["clients_created"] += int(client_created)
    print(
        f"{'CREADO' if client_created else 'ACTUALIZADO'} "
        f"{demo_client.nombre} <{demo_client.email}>"
    )
    verification_model = optional_models.get("verification")
    if verification_model is not None:
        summary["verifications_created"] += int(
            _ensure_client_verification(
                verification_model,
                demo_client.id,
            )
        )

    for data in DEMO_PROFESSIONALS:
        user, user_created = _upsert_user(data)
        professional, professional_created = _upsert_professional(user, data)

        summary["users_created"] += int(user_created)
        summary["professionals_created"] += int(professional_created)

        subscription_model = optional_models.get("subscription")
        if subscription_model is not None:
            summary["subscriptions_created"] += int(
                _sync_demo_pro_subscription(
                    subscription_model,
                    user.id,
                    data["email"] == QA_PRO_EMAIL,
                    now=now,
                )
            )

        verification_model = optional_models.get("verification")
        if verification_model is not None:
            summary["verifications_created"] += int(
                _ensure_verification(verification_model, user.id, data)
            )

        print(
            f"{'CREADO' if professional_created else 'ACTUALIZADO'} "
            f"{professional.nombre} <{user.email}>"
        )

    db.session.commit()
    return summary


def main():
    environment = (
        os.environ.get("APP_ENV")
        or os.environ.get("FLASK_ENV")
        or os.environ.get("TRAX_ENV")
        or "development"
    ).strip().lower()
    if environment in ("production", "prod"):
        raise SystemExit(
            "Seed QA bloqueado en produccion sin excepciones."
        )

    app = create_app()

    with app.app_context():
        try:
            summary = seed_professionals()
        except Exception:
            db.session.rollback()
            raise

    print("Seed DEV completado.")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("Reejecutar el script no crea duplicados.")


if __name__ == "__main__":
    main()
