import os
from datetime import timedelta
from flask import Flask, session
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def create_app(initialize_schema=True):
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-only-insecure-secret-key"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///trax.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = False

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

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://maps.googleapis.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://maps.googleapis.com https://maps.gstatic.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        return response

    return app
