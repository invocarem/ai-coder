from flask import Blueprint, request, jsonify
from app.processors.psalm_rag_processor import PsalmRAGProcessor

# Create blueprint
psalm_bp = Blueprint('psalm', __name__)

# Initialize processor (you'll need to pass the AI provider)
# This should be initialized in your main app file and imported here

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
            "pattern": "psalm_query",
            "psalm_number": psalm_number,
            "verse_number": data.get('verse_number'),
            "question": data.get('question', ''),
            "model": data.get('model'),
            "stream": data.get('stream', False),
            "temperature": data.get('temperature', 0.1),
            "max_tokens": data.get('max_tokens', 2000)
        }
        
        # Get the processor instance (you'll need to manage this)
        psalm_processor = get_psalm_processor()
        return psalm_processor.process(payload, payload.get('model'), payload.get('stream'), data)
        
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
        return psalm_processor.process(payload, payload.get('model'), payload.get('stream'), data)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@psalm_bp.route('/api/psalm_health', methods=['GET'])
def psalm_health():
    """Health check for Psalm RAG system"""
    try:
        psalm_processor = get_psalm_processor()
        return psalm_processor.health_check()
    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500

# Helper function to get the processor instance
def get_psalm_processor():
    """
    This function should return the initialized PsalmRAGProcessor instance.
    You'll need to manage this in your main app file.
    """
    from app import get_psalm_processor as get_processor
    return get_processor()