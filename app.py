# app.py
from flask import Flask, request, jsonify
import requests
import time
import os
from dotenv import load_dotenv

app = Flask(__name__)


def loadenv(env_path: str | None = None) -> dict:
    """Load environment variables from a .env file (optional) and return a dict
    with configuration values. The function will populate the following keys:
      - OLLAMA_BASE_URL: base URL for Ollama API (default kept from original)
      - DEFAULT_MODEL: model name to use when not provided by request
      - REQUEST_TIMEOUT: default timeout (seconds) for requests to Ollama

    If env_path is provided, it will be passed to python-dotenv's load_dotenv.
    Returns a dict with the three configuration values already parsed to the
    expected types.
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    cfg = {}
    cfg["OLLAMA_BASE_URL"] = os.getenv("OLLAMA_BASE_URL", "http://100.71.199.46:11434")
    # Allow the env var name to be OLLAMA_MODEL or OLLAMA_DEFAULT_MODEL for compatibility
    cfg["DEFAULT_MODEL"] = os.getenv("OLLAMA_MODEL", os.getenv("OLLAMA_DEFAULT_MODEL", "deepseek-coder:6.7b"))
    # REQUEST_TIMEOUT should be an int/float seconds; default 120
    try:
        cfg["REQUEST_TIMEOUT"] = float(os.getenv("OLLAMA_TIMEOUT", os.getenv("OLLAMA_REQUEST_TIMEOUT", "120")))
    except Exception:
        cfg["REQUEST_TIMEOUT"] = 120.0

    return cfg


# Load environment configuration at import time
CFG = loadenv()
OLLAMA_BASE_URL = CFG["OLLAMA_BASE_URL"]
DEFAULT_MODEL = CFG["DEFAULT_MODEL"]
REQUEST_TIMEOUT = CFG["REQUEST_TIMEOUT"]

# Define prompt templates
PROMPT_PATTERNS = {
    "generate_function": "Write a {language} function to {task}. Include type hints and docstring.",
    "fix_bug": "Fix this {language} code: ```{code}```. The issue is: {issue}.",
    "explain_code": "Explain how this {language} code works: ```{code}```.",
    "refactor_code": "Refactor this {language} code for better readability and performance: ```{code}```.",
    "write_tests": "Write unit tests for this {language} function: ```{code}```.",
    "add_docs": "Add docstring and comments to this {language} code: ```{code}```.",
    "custom": "{prompt}"  # For custom prompts
}

@app.route('/api/generate_code', methods=['POST'])
def generate_code():
    data = request.json
    pattern = data.get('pattern', 'custom')
    language = data.get('language', 'Python')
    code = data.get('code', '')
    task = data.get('task', '')
    issue = data.get('issue', '')
    prompt = data.get('prompt', '')

    # Fill the prompt template
    if pattern == "custom":
        filled_prompt = prompt
    else:
        filled_prompt = PROMPT_PATTERNS[pattern].format(
            language=language, code=code, task=task, issue=issue
        )

    # Send to Ollama
    payload = {
        "model": os.getenv("OLLAMA_MODEL", DEFAULT_MODEL),
        "prompt": filled_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 4096
        }
    }

    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return jsonify({"text": response.json()["response"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New OpenAI-compatible chat completions endpoint
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible endpoint for VS Code extensions"""
    data = request.json

    # Extract messages from the request
    messages = data.get('messages', [])
    model = data.get('model', DEFAULT_MODEL)
    stream = data.get('stream', False)
    
    # Convert messages to a single prompt
    prompt = ""
    for message in messages:
        role = message.get('role', 'user')
        content = message.get('content', '')
        prompt += f"{role}: {content}\n"
    
    prompt += "assistant: "
    
    # Prepare payload for Ollama
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": data.get('temperature', 0.1),
            "top_p": data.get('top_p', 0.9),
            "top_k": 40,
            "num_predict": data.get('max_tokens', 4096)
        }
    }
    
    try:
        if stream:
            # Handle streaming response
            def generate():
                response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, stream=True, timeout=REQUEST_TIMEOUT)
                for line in response.iter_lines():
                    if line:
                        yield f"data: {line}\n\n"
                yield "data: [DONE]\n\n"
            
            return app.response_class(generate(), mimetype='text/plain')
        else:
            # Handle non-streaming response
            response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            # Format response in OpenAI format
            return jsonify({
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["response"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,  # You might want to calculate these
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=REQUEST_TIMEOUT)
        return jsonify({"status": "healthy", "ollama_connected": response.status_code == 200})
    except:
        return jsonify({"status": "unhealthy", "ollama_connected": False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
