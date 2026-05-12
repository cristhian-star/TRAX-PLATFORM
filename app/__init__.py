from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = "trax_secret_key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trax.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar DB
    db.init_app(app)

    # Blueprints
    from app.routes.main_routes import main
    app.register_blueprint(main)
    
    from app.routes.auth_routes import auth
    app.register_blueprint(auth)
    
    from app.models.user import User
    from app.models.professional import Professional
    
    from app.models.category import Category
    from app.models.category_request import CategoryRequest
    from app.models.contract_request import ContractRequest
    from app.models.budget_request import BudgetRequest
    from app.models.emergency_request import EmergencyRequest
    from app.models.proposal_request import ProposalRequest

    with app.app_context():
        db.create_all()

    return app
