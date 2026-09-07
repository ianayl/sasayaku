from flask import Flask
from flask_cors import CORS
from routes import api_bp

def create_backend():
    backend = Flask(__name__)
    CORS(backend)

    # Register blueprints
    backend.register_blueprint(api_bp)

    return backend
