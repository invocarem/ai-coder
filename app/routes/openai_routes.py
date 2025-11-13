# app/routes/openai_routes.py
from flask import Blueprint, request, jsonify, current_app
from app.processors.processor_router import ProcessorRouter
import time
import logging
import requests

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

    # Determine if we should bypass pattern routing (needed for VS Code Cline/tooling scenarios)
    passthrough_keys = ('tools', 'functions', 'tool_choice', 'response_format', 'stream_options')
    should_passthrough = any(key in data and data[key] for key in passthrough_keys)
    if not should_passthrough:
        for message in messages:
            if isinstance(message, dict) and message.get('tool_calls'):
                should_passthrough = True
                break

    if should_passthrough:
        logger.info("Bypassing pattern detection for OpenAI-compatible request with tooling metadata")
        try:
            processor_router = current_app.config['processor_router']
        except KeyError:
            return jsonify({"error": "Processor router not initialized"}), 500

        ai_provider = getattr(processor_router, "ai_provider", None)
        if ai_provider is None:
            return jsonify({"error": "AI provider not initialized"}), 500

        forward_options = {
            "temperature": data.get('temperature', 0.1),
            "top_p": data.get('top_p', 0.9),
            "max_tokens": data.get('max_tokens', 4096),
            "tools": data.get('tools'),
            "functions": data.get('functions'),
            "tool_choice": data.get('tool_choice'),
            "response_format": data.get('response_format'),
            "logit_bias": data.get('logit_bias'),
            "user": data.get('user'),
            "stop": data.get('stop'),
            "n": data.get('n'),
            "presence_penalty": data.get('presence_penalty'),
            "frequency_penalty": data.get('frequency_penalty'),
            "stream_options": data.get('stream_options'),
            "seed": data.get('seed')
        }
        # Remove None values so providers don't receive unsupported keys
        forward_options = {k: v for k, v in forward_options.items() if v is not None}

        logger.debug("Starting passthrough sanitization for %d messages", len(messages))

        sanitized_messages = []
        known_tool_call_ids = set()
        for message in messages:
            if not isinstance(message, dict):
                sanitized_messages.append(message)
                continue

            role = message.get('role')

            if role == 'assistant':
                tool_calls = message.get('tool_calls') or []
                for tool_call in tool_calls:
                    call_id = tool_call.get('id')
                    if call_id:
                        known_tool_call_ids.add(call_id)
                if tool_calls:
                    logger.debug(
                        "Assistant message includes %d tool call(s); tracking ids: %s",
                        len(tool_calls),
                        list(known_tool_call_ids)
                    )
                sanitized_messages.append(message)
                continue

            if role == 'tool':
                call_id = message.get('tool_call_id')
                if call_id and call_id in known_tool_call_ids:
                    logger.debug("Forwarding tool response for call id %s", call_id)
                    sanitized_messages.append(message)
                else:
                    logger.warning(
                        "Dropping tool message without matching assistant tool call. tool_call_id=%s",
                        call_id
                    )
                continue

            sanitized_messages.append(message)

        logger.debug(
            "Passthrough sanitization completed; forwarding %d messages (dropped %d). Known tool call ids: %s",
            len(sanitized_messages),
            len(messages) - len(sanitized_messages),
            list(known_tool_call_ids)
        )

        try:
            response = ai_provider.generate_openai_compatible(
                sanitized_messages,
                model,
                stream=stream,
                **forward_options
            )
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else 500
            response_text = http_err.response.text if http_err.response else str(http_err)
            logger.error(
                "Upstream OpenAI-compatible provider returned HTTP %s: %s",
                status_code,
                response_text[:500]
            )
            return jsonify({
                "error": "Upstream provider rejected request",
                "status_code": status_code,
                "upstream_response": response_text
            }), status_code
        except Exception as exc:
            logger.exception("Failed to forward OpenAI-compatible request: %s", exc)
            return jsonify({"error": f"Failed to forward OpenAI-compatible request: {str(exc)}"}), 500

        if stream:
            def passthrough_stream():
                for chunk in response:
                    if chunk is None:
                        continue
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode('utf-8', errors='ignore')
                    # `iter_lines` strips newlines; re-add so SSE clients behave correctly
                    yield f"{chunk}\n"

            return current_app.response_class(
                passthrough_stream(),
                mimetype='text/event-stream'
            )

        return jsonify(response)
    
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