from flask import Flask
from .config import load_config
import logging

def create_app():
    app = Flask(__name__)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = load_config()

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
    
    # Register blueprints
    from .routes.api_routes import api_bp
    from .routes.openai_routes import openai_bp
    from .routes.psalm_routes import psalm_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(openai_bp)
    app.register_blueprint(psalm_bp)
    
    return app