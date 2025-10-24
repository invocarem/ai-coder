# app/routes/__init__.py

# Make routes a package
from .openai_routes import openai_bp
from .api_routes import api_bp

# This allows: from app.routes import openai_bp