from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Initialise SQLite DB (creates tables + migrates old JSON history)
    from app.services.history_service import init_db
    init_db()

    # Register Blueprints
    from app.routes import bp
    app.register_blueprint(bp)

    return app
