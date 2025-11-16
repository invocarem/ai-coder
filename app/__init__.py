from flask import Flask
from .config import load_config
import logging
import os
import json

def create_app():
    app = Flask(__name__)
    
    # Load configuration (this also loads .env file)
    config = load_config()
    
    # Configure logging using the new helper
    from .config import setup_logging
    setup_logging(config)

    from app.processors.processor_router import ProcessorRouter
    processor_router = ProcessorRouter(config)
    processor_router.initialize_processors()

    logger = logging.getLogger(__name__)
    logger.info(f"Processor router initialized: {processor_router._initialized}")
    logger.info(f"Available processors: {list(processor_router.processors.keys())}")
    
    # Store processor_router in app config
    app.config['processor_router'] = processor_router
    
    # Also store as direct attribute for backup
    app.processor_router = processor_router
    
    # Configure JSON encoding from config
    app.config['JSON_AS_ASCII'] = config.get("JSON_AS_ASCII", False)
    app.config['JSONIFY_MIMETYPE'] = config.get("JSONIFY_MIMETYPE", "application/json; charset=utf-8")
    app.json_encoder = json.JSONEncoder  # type: ignore
    app.json.ensure_ascii = config.get("JSON_ENSURE_ASCII", False)  # type: ignore

    # Register blueprints
    from .routes.api_routes import api_bp
    from .routes.openai_routes import openai_bp
    from .routes.psalm_routes import psalm_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(openai_bp)
    app.register_blueprint(psalm_bp)
    
    return app