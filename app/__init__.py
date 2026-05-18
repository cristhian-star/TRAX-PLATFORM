import os
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-only-insecure-secret-key"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trax.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar DB
    db.init_app(app)
    csrf.init_app(app)

    # Blueprints
    from app.routes.main_routes import main
    app.register_blueprint(main)
    
    from app.routes.auth_routes import auth
    app.register_blueprint(auth)

    from app.routes.operation_routes import operations
    app.register_blueprint(operations)
    
    from app.models.user import User
    from app.models.professional import Professional
    
    from app.models.category import Category
    from app.models.category_request import CategoryRequest
    from app.models.contract_request import ContractRequest
    from app.models.budget_request import BudgetRequest
    from app.models.emergency_request import EmergencyRequest
    from app.models.proposal_request import ProposalRequest
    from app.models.verification_request import VerificationRequest
    from app.models.review import Review
    from app.models.abuse_report import AbuseReport
    from app.models.terms_acceptance import TermsAcceptance
    from app.models.subscription import Subscription
    from app.models.reputation_event import ReputationEvent

    with app.app_context():
        db.create_all()

    return app
