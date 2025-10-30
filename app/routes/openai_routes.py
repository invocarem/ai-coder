# app/routes/openai_routes.py
from flask import Blueprint, request, jsonify, current_app
from app.processors.processor_router import ProcessorRouter
import time
import logging

openai_bp = Blueprint('openai', __name__)
logger = logging.getLogger(__name__)



@openai_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI-compatible endpoint that uses pattern detection
    
    Expected JSON payload (OpenAI format):
    {
        "model": "model-name",
        "messages": [
            {"role": "user", "content": "message content"}
        ],
        "stream": false,
        "temperature": 0.1,
        "max_tokens": 4096
    }
    """
    data = request.json or {}

    # Extract messages from the request
    messages = data.get('messages', [])
    model = data.get('model', 'deepseek-coder:6.7b')
    stream = data.get('stream', False)
    
    # Get the last user message (usually the most recent one)
    user_message = ""
    for message in reversed(messages):
        if message.get('role') == 'user':
            user_message = message.get('content', '')
            break
    
    if not user_message:
        return jsonify({"error": "No user message found"}), 400

    from app.utils.pattern_detector import PatternDetector
    pattern_detector = PatternDetector()
    pattern_data = pattern_detector.detect_pattern(user_message)
    
    if not pattern_data:
        pattern_data = {'pattern': 'custom', 'prompt': user_message}
    
    logger.info(f"OpenAI-compatible request received:")
    logger.info(f"  Model: {model}")
    logger.info(f"  Stream: {stream}")
    logger.info(f"  User message length: {len(user_message)}")
    logger.info(f"  User message preview: {user_message[:100]}...")

    try:
        # Get processor_router from app config
        processor_router = current_app.config['processor_router']
        
        # Use router instead of direct processor
        return processor_router.route_request(pattern_data, model, stream, data)
    except KeyError:
        return jsonify({"error": "Processor router not initialized"}), 500
    except Exception as e:
        logger.error(f"Error in chat_completions: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    
    
@openai_bp.route('/v1/models', methods=['GET'])
def list_models():
    """
    OpenAI-compatible models endpoint
    """
    # Get processor_router from the app context
    processor_router = current_app.processor_router
    
    # Ensure processors are initialized
    if not processor_router._initialized:
        processor_router.initialize_processors()
    
    # Get default model from code processor
    default_model = processor_router.processors['code'].default_model
    
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": default_model,
                "object": "model", 
                "created": int(time.time()),
                "owned_by": "local"
            }
        ]
    })

@openai_bp.route('/v1/models/<model_name>', methods=['GET'])
def get_model(model_name):
    """
    OpenAI-compatible model details endpoint
    """
    return jsonify({
        "id": model_name,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "local"
    })