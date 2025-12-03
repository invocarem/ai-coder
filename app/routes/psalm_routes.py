from flask import Blueprint, request, jsonify, current_app
from app.processors.psalm_rag_processor import PsalmRAGProcessor

# Create blueprint
psalm_bp = Blueprint('psalm', __name__)

# Get the psalm processor instance
def get_psalm_processor():
    """Get the initialized PsalmRAGProcessor instance from current app context"""
    if not hasattr(current_app, 'config') or 'processor_router' not in current_app.config:
        # This might happen during app initialization
        # In production, this should be initialized in create_app()
        raise RuntimeError("Processor router not initialized in app context")
    return current_app.config['processor_router'].processors['psalm_processor']

@psalm_bp.route('/api/query_psalm', methods=['POST'])
def query_psalm():
    """
    Convenience endpoint for querying Psalms with Augustine commentary
    Expected JSON payload:
    {
        "psalm_number": 1,
        "verse_number": 1,  # optional
        "question": "How does Augustine interpret the three verbs?",  # optional
        "model": "optional model override",
        "stream": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        psalm_number = data.get('psalm_number')
        
        if not psalm_number:
            return jsonify({"error": "psalm_number is required"}), 400
        
        # Create payload for psalm_rag_processor
        payload = {
            "pattern": "augustine_psalm_query",
            "psalm_number": psalm_number,
            "verse_number": data.get('verse_number'),
            "question": data.get('question', ''),
            "model": data.get('model'),
            "stream": data.get('stream', False),
            "temperature": data.get('temperature', 0.1),
            "max_tokens": data.get('max_tokens', 2000)
        }
        
        # Get the processor instance
        psalm_processor = get_psalm_processor()
        
        # Call processor and handle response
        result = psalm_processor.process(payload, payload.get('model'), payload.get('stream'), data)
        
        # Handle streaming response
        if payload.get('stream', False) and hasattr(result, '__iter__') and not isinstance(result, (str, dict, list)):
            # Return the generator directly for streaming
            return result
            
        # Handle regular response
        if isinstance(result, tuple) and len(result) == 2:
            payload, status_code = result
            return jsonify(payload), status_code
        else:
            return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@psalm_bp.route('/api/analyze_psalm_word', methods=['POST'])
def analyze_psalm_word():
    """
    Convenience endpoint for analyzing words in Psalms
    Expected JSON payload:
    {
        "word_form": "abiit",
        "psalm_number": 1,
        "verse_number": 1,  # optional
        "question": "What does this word mean?",  # optional
        "model": "optional model override",
        "stream": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        word_form = data.get('word_form')
        psalm_number = data.get('psalm_number')
        
        if not word_form or not psalm_number:
            return jsonify({"error": "word_form and psalm_number are required"}), 400
        
        # Create payload for psalm_rag_processor
        payload = {
            "pattern": "psalm_word_analysis",
            "word_form": word_form,
            "psalm_number": psalm_number,
            "verse_number": data.get('verse_number'),
            "question": data.get('question', ''),
            "model": data.get('model'),
            "stream": data.get('stream', False),
            "temperature": data.get('temperature', 0.1),
            "max_tokens": data.get('max_tokens', 2000)
        }
        
        # Get the processor instance
        psalm_processor = get_psalm_processor()
        
        # Call processor and handle response
        result = psalm_processor.process(payload, payload.get('model'), payload.get('stream'), data)
        
        # Handle streaming response
        if payload.get('stream', False) and hasattr(result, '__iter__') and not isinstance(result, (str, dict, list)):
            # Return the generator directly for streaming
            return result
            
        # Handle regular response
        if isinstance(result, tuple) and len(result) == 2:
            payload, status_code = result
            return jsonify(payload), status_code
        else:
            return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@psalm_bp.route('/api/psalm_health', methods=['GET'])
def psalm_health():
    """Health check for Psalm RAG system"""
    try:
        psalm_processor = get_psalm_processor()
        result = psalm_processor.health_check()
        
        # Handle regular response
        if isinstance(result, tuple) and len(result) == 2:
            payload, status_code = result
            return jsonify(payload), status_code
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500
