# app.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
OLLAMA_URL = "http://100.71.199.46:11434/api/generate"

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
        "model": "deepseek-coder:6.7b",
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
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return jsonify({"text": response.json()["response"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

