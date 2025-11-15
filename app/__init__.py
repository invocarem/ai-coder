from flask import Flask
from .config import load_config
import logging
import os
import json

def create_app():
    app = Flask(__name__)
    
    # Load configuration (this also loads .env file)
    config = load_config()
    
    # Determine logging level based on VERBOSE and SHOW_INFO from config
    VERBOSE = config.get("VERBOSE", False)
    SHOW_INFO = config.get("SHOW_INFO", False)

    if VERBOSE:
        log_level = logging.DEBUG
    elif SHOW_INFO:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    stream_log_path = config.get("STREAM_DEBUG_LOG") or os.getenv("STREAM_DEBUG_LOG")
    if stream_log_path:
        stream_logger = logging.getLogger("stream_debug")
        abs_path = os.path.abspath(stream_log_path)
        if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == abs_path
                   for handler in stream_logger.handlers):
            file_handler = logging.FileHandler(abs_path, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            stream_logger.addHandler(file_handler)
        stream_logger.setLevel(logging.INFO)
        stream_logger.propagate = False

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
