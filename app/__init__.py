from flask import Flask

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = 'trax_secret_key'

    # Blueprints
    from app.routes.main_routes import main
    app.register_blueprint(main)

    return app