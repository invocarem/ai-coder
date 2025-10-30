# app/routes/api_routes.py
from flask import Blueprint, request, jsonify

# Create blueprint
api_bp = Blueprint('api', __name__)



@api_bp.route('/api/analyze_latin', methods=['POST'])
def analyze_latin():
    """
    Analyze Latin words and grammar
    Expected JSON payload:
    {
        "word": "egredior",
        "analysis_type": "conjugate|decline|translate|comprehensive",
        "context": "biblical|classical|general"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        word = data.get('word', '')
        if not word:
            return jsonify({"error": "Latin word is required"}), 400
        
        # Create pattern data for processor
        pattern_data = {
            'pattern': 'latin_analysis',
            'latin_word': word,
            'analysis_type': data.get('analysis_type', 'comprehensive'),
            'context': data.get('context', 'general')
        }
        
        return current_app.processor_router.route_request(
            pattern_data, 
            code_processor.default_model, 
            False, 
            data
        )
        
    except Exception as e:
        return jsonify({"error": f"Latin analysis failed: {str(e)}"}), 500

@api_bp.route('/api/generate_code', methods=['POST'])
def generate_code():
    """
    Generate code based on various patterns
    Expected JSON payload:
    {
        "pattern": "generate_function|fix_bug|explain_code|refactor_code|write_tests|add_docs|custom",
        "language": "Python|JavaScript|Java|...",
        "code": "optional code string",
        "task": "optional task description", 
        "issue": "optional issue description",
        "prompt": "custom prompt when pattern is 'custom'",
        "model": "optional model override",
        "stream": "optional streaming flag"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required data
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate pattern
        valid_patterns = [
            'generate_function', 'fix_bug', 'explain_code', 
            'refactor_code', 'write_tests', 'add_docs', 'custom'
        ]
        
        pattern_data = {
            "pattern": "write_code",
            "language": language,
            "task": task,
            **data
        }
        
        return current_app.processor_router.route_request(
            pattern_data,
            data.get('model', 'deepseek-coder:6.7b'),
            data.get('stream', False),
            data
        )
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/generate_function', methods=['POST'])
def generate_function():
    """
    Convenience endpoint specifically for generating functions
    Expected JSON payload:
    {
        "language": "Python|JavaScript|...",
        "task": "description of what the function should do",
        "model": "optional model override"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        language = data.get('language', 'Python')
        task = data.get('task', '')
        
        if not task:
            return jsonify({"error": "Task description is required"}), 400
        
        # Create payload for generate_code
        payload = {
            "pattern": "generate_function",
            "language": language,
            "task": task,
            "model": data.get('model'),
            "stream": data.get('stream', False)
        }
        
        return code_processor.generate_code(payload)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/refactor_code', methods=['POST'])
def refactor_code():
    """
    Convenience endpoint specifically for refactoring code
    Expected JSON payload:
    {
        "language": "Python|JavaScript|...", 
        "code": "code to refactor",
        "model": "optional model override"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        language = data.get('language', 'Python')
        code = data.get('code', '')
        
        if not code:
            return jsonify({"error": "Code is required for refactoring"}), 400
        
        # Create payload for generate_code
        payload = {
            "pattern": "refactor_code",
            "language": language,
            "code": code,
            "model": data.get('model'),
            "stream": data.get('stream', False)
        }
        
        return code_processor.generate_code(payload)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/fix_bug', methods=['POST'])
def fix_bug():
    """
    Convenience endpoint specifically for fixing bugs
    Expected JSON payload:
    {
        "language": "Python|JavaScript|...",
        "code": "buggy code",
        "issue": "description of the issue",
        "model": "optional model override" 
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        language = data.get('language', 'Python')
        code = data.get('code', '')
        issue = data.get('issue', 'Unknown issue')
        
        if not code:
            return jsonify({"error": "Code is required for bug fixing"}), 400
        
        # Create payload for generate_code
        payload = {
            "pattern": "fix_bug",
            "language": language,
            "code": code,
            "issue": issue,
            "model": data.get('model'),
            "stream": data.get('stream', False)
        }
        
        return code_processor.generate_code(payload)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/explain_code', methods=['POST'])
def explain_code():
    """
    Convenience endpoint specifically for explaining code
    Expected JSON payload:
    {
        "language": "Python|JavaScript|...",
        "code": "code to explain",
        "model": "optional model override"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        language = data.get('language', 'Python')
        code = data.get('code', '')
        
        if not code:
            return jsonify({"error": "Code is required for explanation"}), 400
        
        # Create payload for generate_code
        payload = {
            "pattern": "explain_code",
            "language": language,
            "code": code,
            "model": data.get('model'),
            "stream": data.get('stream', False)
        }
        
        return code_processor.generate_code(payload)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/write_tests', methods=['POST'])
def write_tests():
    """
    Convenience endpoint specifically for writing tests
    Expected JSON payload:
    {
        "language": "Python|JavaScript|...",
        "code": "code to test",
        "model": "optional model override"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        language = data.get('language', 'Python')
        code = data.get('code', '')
        
        if not code:
            return jsonify({"error": "Code is required for writing tests"}), 400
        
        # Create payload for generate_code
        payload = {
            "pattern": "write_tests",
            "language": language,
            "code": code,
            "model": data.get('model'),
            "stream": data.get('stream', False)
        }
        
        return code_processor.generate_code(payload)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/add_docs', methods=['POST'])
def add_docs():
    """
    Convenience endpoint specifically for adding documentation
    Expected JSON payload:
    {
        "language": "Python|JavaScript|...",
        "code": "code to document",
        "model": "optional model override"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        language = data.get('language', 'Python')
        code = data.get('code', '')
        
        if not code:
            return jsonify({"error": "Code is required for adding documentation"}), 400
        
        # Create payload for generate_code
        payload = {
            "pattern": "add_docs",
            "language": language,
            "code": code,
            "model": data.get('model'),
            "stream": data.get('stream', False)
        }
        
        return code_processor.generate_code(payload)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns the status of the application and AI provider connection
    """
    return code_processor.health_check()

@api_bp.route('/api/models', methods=['GET'])
def list_models():
    """
    List available models
    """
    try:
        # Use the processor info to get available models
        processor_info = code_processor.get_processor_info()
        return jsonify({
            "models": [{
                "name": processor_info["default_model"],
                "modified_at": "2024-01-01T00:00:00.000000000-07:00",
                "size": 0,  # Unknown size
                "digest": "sha256:unknown"
            }]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch models: {str(e)}"}), 500

@api_bp.route('/api/model_info', methods=['POST'])
def get_model_info():
    """
    Get information about a specific model
    Expected JSON payload:
    {
        "model": "model name (optional, uses default if not provided)"
    }
    """
    try:
        data = request.get_json() or {}
        model_name = data.get('model', code_processor.default_model)
        
        # Return basic model info
        model_info = {
            "model": model_name,
            "default_model": code_processor.default_model,
            "provider": code_processor.config.get("AI_PROVIDER", "ollama"),
            "max_tokens": code_processor.config.get("MAX_TOKENS", 4096),
            "default_temperature": code_processor.config.get("DEFAULT_TEMPERATURE", 0.1)
        }
        return jsonify(model_info)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch model info: {str(e)}"}), 500

@api_bp.route('/api/patterns', methods=['GET'])
def list_patterns():
    """
    List all available code generation patterns
    """
    try:
        patterns_info = code_processor.get_supported_patterns()
        return jsonify({
            "patterns": patterns_info,
            "supported_languages": [
                "Python", "JavaScript", "Java", "C++", "C#", "Go", 
                "Rust", "PHP", "Ruby", "Swift", "TypeScript", "Bash", "Awk"
            ]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch patterns: {str(e)}"}), 500

@api_bp.route('/api/status', methods=['GET'])
def status():
    """
    Comprehensive status endpoint
    """
    try:
        health_status = code_processor.health_check().get_json()
        processor_info = code_processor.get_processor_info()
        patterns_info = code_processor.get_supported_patterns()
        
        status_info = {
            "application": "ai-coder",
            "status": health_status.get("status", "unknown"),
            "ai_provider": health_status.get("ai_provider", "unknown"),
            "provider_connected": health_status.get("provider_connected", False),
            "default_model": processor_info.get("default_model", "unknown"),
            "supported_patterns": list(patterns_info.keys()),
            "max_tokens": processor_info.get("max_tokens", 4096),
            "default_temperature": processor_info.get("default_temperature", 0.1)
        }
        
        return jsonify(status_info)
    except Exception as e:
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500

@api_bp.route('/api/info', methods=['GET'])
def get_processor_info():
    """
    Get detailed processor information
    """
    try:
        info = code_processor.get_processor_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": f"Failed to get processor info: {str(e)}"}), 500

@api_bp.route('/api/batch/generate', methods=['POST'])
def batch_generate_code():
    """
    Process multiple code generation requests in batch
    Expected JSON payload:
    [
        {
            "pattern": "generate_function",
            "language": "Python", 
            "task": "sort list"
        },
        {
            "pattern": "fix_bug", 
            "language": "Python",
            "code": "def broken(): return x",
            "issue": "undefined variable"
        }
    ]
    """
    try:
        requests_data = request.get_json() or []
        if not isinstance(requests_data, list):
            return jsonify({"error": "Expected a list of requests"}), 400
            
        return code_processor.batch_process(requests_data)
        
    except Exception as e:
        return jsonify({"error": f"Batch processing failed: {str(e)}"}), 500