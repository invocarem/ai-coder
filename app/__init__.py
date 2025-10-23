from flask import Flask
from .config import load_config

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_mapping(load_config())
    
    # Register blueprints
    from .routes.api_routes import api_bp
    from .routes.openai_routes import openai_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(openai_bp)
    
    return app