from flask import Flask, jsonify, request, session
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config.config import get_config_class

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_class=None, initialize_schema=False):
    app = Flask(__name__)

    config_class = config_class or get_config_class()
    config_class.validate()
    app.config.from_object(config_class)
    config_class.apply_runtime_config(app.config)

    # Inicializar DB
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Blueprints
    from app.routes.main_routes import main
    app.register_blueprint(main)
    
    from app.routes.auth_routes import auth
    app.register_blueprint(auth)

    from app.routes.operation_routes import operations
    app.register_blueprint(operations)

    from app.routes.notification_routes import notifications
    app.register_blueprint(notifications)

    from app.routes.whatsapp_routes import whatsapp
    app.register_blueprint(whatsapp)

    if app.config.get("REGISTER_DEV_ROUTES"):
        from app.routes.dev_routes import dev
        app.register_blueprint(dev)
    
    from app.models.user import User
    from app.models.professional import Professional
    
    from app.models.category import Category
    from app.models.category_request import CategoryRequest
    from app.models.contract_request import ContractRequest
    from app.models.budget_request import BudgetRequest
    from app.models.budget_offer import BudgetOffer
    from app.models.emergency_request import EmergencyRequest
    from app.models.proposal_request import ProposalRequest
    from app.models.proposal_application import ProposalApplication
    from app.models.verification_request import VerificationRequest
    from app.models.review import Review
    from app.models.abuse_report import AbuseReport
    from app.models.terms_acceptance import TermsAcceptance
    from app.models.subscription import Subscription
    from app.models.reputation_event import ReputationEvent
    from app.models.audit_log import AuditLog
    from app.models.activity_notification import ActivityNotification
    from app.models.whatsapp_contact_session import WhatsAppContactSession

    if initialize_schema:
        if not app.config.get("ALLOW_SCHEMA_CREATE_ALL"):
            raise RuntimeError(
                "db.create_all() solo esta permitido en tests o desarrollo explicito. "
                "Usa Alembic para administrar el esquema."
            )
        with app.app_context():
            db.create_all()

    @app.context_processor
    def inject_notification_navbar():
        if not session.get("user_id"):
            return {
                "navbar_notifications": [],
                "navbar_unread_notifications": 0,
            }

        from app.services.notification_service import (
            obtener_no_leidas,
            obtener_notificaciones_usuario,
        )

        user_id = session["user_id"]
        return {
            "navbar_notifications": obtener_notificaciones_usuario(user_id, limit=5),
            "navbar_unread_notifications": obtener_no_leidas(user_id),
        }

    def _safe_error_response(status_code, message):
        if app.config.get("TESTING") or request.accept_mimetypes.best == "application/json" or request.is_json:
            return jsonify({"error": message}), status_code

        return f"{status_code} - {message}", status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        return _safe_error_response(400, "Solicitud invalida")

    @app.errorhandler(403)
    def handle_forbidden(error):
        return _safe_error_response(403, "Acceso no autorizado")

    @app.errorhandler(404)
    def handle_not_found(error):
        return _safe_error_response(404, "Recurso no encontrado")

    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        return _safe_error_response(413, "La solicitud supera el limite permitido")

    @app.errorhandler(429)
    def handle_rate_limit(error):
        return _safe_error_response(429, "Se excedio el limite de solicitudes")

    @app.errorhandler(500)
    def handle_internal_error(error):
        return _safe_error_response(500, "Error interno")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error

        app.logger.error("Error inesperado procesando la solicitud")
        return handle_internal_error(error)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers.pop("X-Powered-By", None)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://maps.googleapis.com https://maps.gstatic.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://maps.googleapis.com https://maps.gstatic.com; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        if app.config.get("ENV_NAME") == "production" and request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    return app
