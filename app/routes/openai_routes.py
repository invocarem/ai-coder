# app/routes/openai_routes.py
from flask import Blueprint, request, jsonify, current_app, Response
from app.processors.processor_router import ProcessorRouter
import time
import logging
import requests
import json

openai_bp = Blueprint('openai', __name__)
logger = logging.getLogger(__name__)


def _handle_passthrough_request(data, messages, model, stream):
    """
    Handle OpenAI-compatible passthrough requests with tooling metadata
    """
    logger.info("### PASSTHROUGH: Starting passthrough request")
    
    try:
        processor_router = current_app.config['processor_router']
        ai_provider = getattr(processor_router, "ai_provider", None)
        
        if ai_provider is None:
            logger.error("### PASSTHROUGH: AI provider not available")
            return jsonify({"error": "AI provider not initialized"}), 500
            
    except KeyError:
        logger.error("### PASSTHROUGH: Processor router not found")
        return jsonify({"error": "Processor router not initialized"}), 500

    # Prepare forward options
    forward_options = {
        "temperature": data.get('temperature', 0.1),
        "top_p": data.get('top_p', 0.9),
        "max_tokens": data.get('max_tokens', 4096),
    }
    
    # Add optional fields if present
    optional_keys = ['tools', 'functions', 'tool_choice', 'response_format', 'stream_options']
    for key in optional_keys:
        if key in data and data[key]:
            forward_options[key] = data[key]
            logger.debug("### PASSTHROUGH: Including %s in forward options", key)

    logger.info("### PASSTHROUGH: Calling AI provider, stream=%s, model=%s", stream, model)
    debug_payload = {
        "model": model,
        "messages": messages,
        **forward_options
    }
    logger.debug("### PASSTHROUGH: Full request payload:\n%s", json.dumps(debug_payload, indent=2, ensure_ascii=False))

    try:
        response = ai_provider.generate_openai_compatible(
            messages,
            model,
            stream=stream,
            **forward_options
        )

        logger.info("### PASSTHROUGH: AI provider response received")
        logger.info("### PASSTHROUGH: Response type: %s", type(response))

        if stream:
            return _handle_passthrough_streaming(response, model)
        else:
            return _handle_passthrough_non_streaming(response, model)

    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code if http_err.response else 500
        response_text = http_err.response.text if http_err.response else str(http_err)
        logger.error(
            "### PASSTHROUGH: Upstream provider returned HTTP %s: %s",
            status_code,
            response_text[:500]
        )
        return jsonify({
            "error": "Upstream provider rejected request",
            "status_code": status_code,
            "upstream_response": response_text
        }), status_code
        
    except Exception as exc:
        logger.exception("### PASSTHROUGH: Failed to forward request: %s", exc)
        return jsonify({"error": f"Failed to forward request: {str(exc)}"}), 500
    

def _handle_passthrough_streaming(response, model):
    logger.info("### PASSTHROUGH: Handling streaming response")

    def generate():
        for raw in response:
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8', errors='replace')

            # llama.cpp sends lines like:  data: {"choices":[{"delta":{"content":"你好"}}]}
            if raw.startswith("data: "):
                payload = raw[6:].strip()
                if payload and payload != "[DONE]":
                    try:
                        data = json.loads(payload)          # parse
                        # fix content field in-place
                        for c in data.get("choices", []):
                            if "delta" in c and "content" in c["delta"]:
                                c["delta"]["content"] = (
                                    c["delta"]["content"]
                                    .encode('latin1')      # undo llama.cpp mistake
                                    .decode('utf-8', errors='replace')
                                )
                            if "message" in c and "content" in c["message"]:
                                c["message"]["content"] = (
                                    c["message"]["content"]
                                    .encode('latin1')
                                    .decode('utf-8', errors='replace')
                                )
                        raw = "data: " + json.dumps(data, ensure_ascii=False)
                    except Exception:
                        pass                                # leave line untouched
            yield raw + "\n"

    return current_app.response_class(
        generate(),
        mimetype="text/event-stream; charset=utf-8"
    )    



def _handle_passthrough_non_streaming(response, model):
    """
    Handle non-streaming passthrough response with proper UTF-8 encoding
    """
    logger.info("### PASSTHROUGH: Handling non-streaming response")
    
    if not isinstance(response, dict):
        logger.warning("### PASSTHROUGH: Unexpected response type: %s", type(response))
        return jsonify({"error": "Unexpected response format from AI provider"}), 500

    logger.info("### PASSTHROUGH: Response keys: %s", list(response.keys()))
    
    # Debug log the content
    if 'choices' in response and response['choices']:
        content = response['choices'][0].get('message', {}).get('content', '')
        logger.info("### PASSTHROUGH: Response content preview: %s", repr(content[:200]))
        logger.info("### PASSTHROUGH: Content contains Chinese chars: %s", any('\u4e00' <= char <= '\u9fff' for char in content))
    
    # Ensure UTF-8 encoding
    json_str = json.dumps(response, ensure_ascii=False)
    logger.info("### PASSTHROUGH: JSON response length: %d", len(json_str))
    
    return Response(
        json_str,
        mimetype='application/json; charset=utf-8',
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )


def _should_passthrough(data, messages):
    """
    Determine if request should bypass pattern detection
    """
    passthrough_keys = ('tools', 'functions', 'tool_choice', 'response_format', 'stream_options')
    
    # Check for tooling metadata in request data
    if any(key in data and data[key] for key in passthrough_keys):
        logger.debug("### PASSTHROUGH: Triggered by request data keys")
        return True
    
    # Check for tool_calls in messages
    for message in messages:
        if isinstance(message, dict) and message.get('tool_calls'):
            logger.debug("### PASSTHROUGH: Triggered by tool_calls in messages")
            return True
    
    return False


@openai_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI-compatible endpoint that uses pattern detection
    """
    data = request.json or {}
    messages = data.get('messages', [])
    model = data.get('model', 'deepseek-coder:6.7b')
    stream = data.get('stream', False)

    # Check if we should use passthrough
    if _should_passthrough(data, messages):
        return _handle_passthrough_request(data, messages, model, stream)

    # PATTERN DETECTION PATH (your existing code)
    logger.info("### PATTERN: Using pattern detection path")
    
    # Get the last user message
    user_message = ""
    for message in reversed(messages):
        if message.get('role') == 'user':
            user_message = message.get('content', '')
            break

    if not user_message:
        return jsonify({"error": "No user message found"}), 400

    # Convert to string if needed
    if isinstance(user_message, list):
        user_message = ' '.join(str(item) for item in user_message)
    elif not isinstance(user_message, str):
        user_message = str(user_message)

    from app.utils.pattern_detector import PatternDetector
    pattern_detector = PatternDetector()
    pattern_data = pattern_detector.detect_pattern(user_message)
    
    # Handle conversation history for processor specification
    if not pattern_data or not pattern_data.get('processor'):
        for message in messages:
            content = message.get('content', '')
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            elif not isinstance(content, str):
                content = str(content)

            if '### processor:' in content.lower():
                historical_pattern_data = pattern_detector.detect_pattern(content)
                if historical_pattern_data and historical_pattern_data.get('processor'):
                    logger.info(f"### PATTERN: Found processor in history: {historical_pattern_data.get('processor')}")
                    
                    if not pattern_data:
                        pattern_data = {
                            'processor': historical_pattern_data.get('processor'),
                            'pattern_data': {'pattern': 'custom', 'prompt': user_message},
                            'specified_processor': True
                        }
                    else:
                        pattern_data = {
                            'processor': historical_pattern_data.get('processor'),
                            'pattern_data': pattern_data,
                            'specified_processor': True
                        }
                    break
    
    # Ensure pattern_data is in the right format
    if pattern_data and isinstance(pattern_data, dict) and 'processor' in pattern_data:
        pass  # Already correct format
    elif pattern_data and isinstance(pattern_data, dict):
        pattern_data = {
            'processor': pattern_data.get('processor'),
            'pattern_data': {k: v for k, v in pattern_data.items() if k != 'processor'},
            'specified_processor': bool(pattern_data.get('processor'))
        }
    else:
        pattern_data = {'pattern': 'custom', 'prompt': user_message}
    
    logger.info(f"### PATTERN: Request details - Model: {model}, Stream: {stream}")
    logger.info(f"### PATTERN: User message preview: {user_message[:100]}...")

    try:
        processor_router = current_app.config['processor_router']
        return processor_router.route_request(pattern_data, model, stream, data)
    except KeyError:
        return jsonify({"error": "Processor router not initialized"}), 500
    except Exception as e:
        logger.error(f"### PATTERN: Error in chat_completions: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@openai_bp.route('/v1/models', methods=['GET'])
def list_models():
    """
    OpenAI-compatible models endpoint
    """
    processor_router = current_app.config['processor_router']

    try: 
        default_model = processor_router.get_default_model()
    except Exception as e:
        logger.error("Failed to obtain default model: %s", e)
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