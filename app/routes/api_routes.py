# app/routes/api_routes.py
from flask import Blueprint, request, jsonify
from ..processors.code_processor import CodeProcessor

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize code processor
code_processor = CodeProcessor()

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
        
        pattern = data.get('pattern', 'custom')
        if pattern not in valid_patterns:
            return jsonify({
                "error": f"Invalid pattern. Must be one of: {', '.join(valid_patterns)}"
            }), 400
        
        return code_processor.generate_code(data)
        
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
    Returns the status of the application and Ollama connection
    """
    return code_processor.health_check()

@api_bp.route('/api/models', methods=['GET'])
def list_models():
    """
    List available models from Ollama
    """
    try:
        models_info = code_processor.ollama_client.list_models()
        return jsonify(models_info)
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
        model_name = data.get('model')
        
        model_info = code_processor.ollama_client.get_model_info(model_name)
        return jsonify(model_info)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch model info: {str(e)}"}), 500

@api_bp.route('/api/patterns', methods=['GET'])
def list_patterns():
    """
    List all available code generation patterns
    """
    patterns = {
        "patterns": {
            "generate_function": "Write a function with type hints and docstring",
            "fix_bug": "Fix bugs in provided code",
            "explain_code": "Explain how code works", 
            "refactor_code": "Refactor code for readability and performance",
            "write_tests": "Write unit tests for code",
            "add_docs": "Add documentation and comments",
            "custom": "Use a custom prompt"
        },
        "supported_languages": [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", 
            "Rust", "PHP", "Ruby", "Swift", "TypeScript", "Bash", "Awk"
        ]
    }
    return jsonify(patterns)

@api_bp.route('/api/status', methods=['GET'])
def status():
    """
    Comprehensive status endpoint
    """
    health_status = code_processor.health_check().get_json()
    models_status = code_processor.ollama_client.list_models()
    
    status_info = {
        "application": "ai-coder",
        "status": health_status.get("status", "unknown"),
        "ollama_connected": health_status.get("ollama_connected", False),
        "default_model": code_processor.default_model,
        "available_models": models_status.get("models", []) if isinstance(models_status, dict) else [],
        "ollama_base_url": code_processor.ollama_client.base_url
    }
    
    return jsonify(status_info)