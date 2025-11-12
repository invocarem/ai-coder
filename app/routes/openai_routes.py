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

    # Convert to string if it's not already
    if isinstance(user_message, list):
        # If it's a list of message parts, join them
        user_message = ' '.join(str(item) for item in user_message)
    elif not isinstance(user_message, str):
        user_message = str(user_message)

    from app.utils.pattern_detector import PatternDetector
    pattern_detector = PatternDetector()
    pattern_data = pattern_detector.detect_pattern(user_message)
    
    # If no pattern detected in current message, check conversation history for processor specification
    if not pattern_data or not pattern_data.get('processor'):
        # Look through all messages (including assistant responses) for processor specification
        for message in messages:
            content = message.get('content', '')
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            elif not isinstance(content, str):
                content = str(content)

            if '### processor:' in content.lower():
                # Found a processor specification in conversation history
                historical_pattern_data = pattern_detector.detect_pattern(content)
                if historical_pattern_data and historical_pattern_data.get('processor'):
                    # Use the processor from history, but keep current message's content
                    logger.info(f"Found processor '{historical_pattern_data.get('processor')}' in conversation history")
                    
                    # Restructure pattern_data to match what router expects
                    if not pattern_data:
                        # Create proper detection_result structure
                        pattern_data = {
                            'processor': historical_pattern_data.get('processor'),
                            'pattern_data': {
                                'pattern': 'custom',
                                'prompt': user_message
                            },
                            'specified_processor': True
                        }
                    else:
                        # Convert current pattern_data to proper structure
                        pattern_data = {
                            'processor': historical_pattern_data.get('processor'),
                            'pattern_data': pattern_data if isinstance(pattern_data, dict) else {'pattern': 'custom', 'prompt': user_message},
                            'specified_processor': True
                        }
                    break
    
    # Ensure pattern_data is in the right format for router
    if pattern_data and isinstance(pattern_data, dict) and 'processor' in pattern_data:
        # Already in correct format
        pass
    elif pattern_data and isinstance(pattern_data, dict):
        # Convert to detection_result format
        pattern_data = {
            'processor': pattern_data.get('processor'),
            'pattern_data': {k: v for k, v in pattern_data.items() if k != 'processor'},
            'specified_processor': bool(pattern_data.get('processor'))
        }
    else:
        # No pattern detected, create default
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
    processor_router = current_app.config['processor_router']

    try: 
        # Get default model from code processor
        default_model = processor_router.get_default_model()
    except Exception as e:
        logger.error("Failed to obtain default model: %s", e)
        # Fallback to a hard‑coded model name if something goes really wrong
        default_model = "deepseek-coder:6.7b"
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