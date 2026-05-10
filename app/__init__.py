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
    
    from app.models.user import User
    from app.models.professional import Professional
    
    from app.models.category import Category
    from app.models.category_request import CategoryRequest

    with app.app_context():
        db.create_all()

    return app