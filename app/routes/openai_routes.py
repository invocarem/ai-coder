# app/routes/openai_routes.py
from flask import Blueprint, request, jsonify
from app.processors.code_processor import CodeProcessor
import time
import logging

# Create blueprint
openai_bp = Blueprint('openai', __name__)

# Initialize code processor
code_processor = CodeProcessor()

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
    data = request.json

    # Extract messages from the request
    messages = data.get('messages', [])
    model = data.get('model', code_processor.default_model)
    stream = data.get('stream', False)
    
    # Get the last user message (usually the most recent one)
    user_message = ""
    for message in reversed(messages):
        if message.get('role') == 'user':
            user_message = message.get('content', '')
            break
    
    if not user_message:
        return jsonify({"error": "No user message found"}), 400
    
    logger.info(f"OpenAI-compatible request received:")
    logger.info(f"  Model: {model}")
    logger.info(f"  Stream: {stream}")
    logger.info(f"  User message length: {len(user_message)}")
    
    # Analyze the message to detect patterns
    pattern_data = code_processor.pattern_detector.detect_pattern(user_message)
    
    if pattern_data:
        logger.info(f"PATTERN DETECTED: {pattern_data['pattern']}")
        if 'language' in pattern_data:
            logger.info(f"  Language: {pattern_data['language']}")
        if 'code' in pattern_data and pattern_data['code']:
            logger.info(f"  Code length: {len(pattern_data['code'])}")
    else:
        print("PATTERN: None")

    if pattern_data:
        # Use the generate_code endpoint logic
        return code_processor._handle_pattern_request(pattern_data, model, stream, data)
    else:
        return code_processor._handle_direct_request(user_message, model, stream, data)

@openai_bp.route('/v1/models', methods=['GET'])
def list_models():
    """
    OpenAI-compatible models endpoint
    """
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": code_processor.default_model,
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