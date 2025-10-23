# app/utils/ollama_client.py
import json
import time
import requests
from flask import jsonify, Response

class OllamaClient:
    def __init__(self, config):
        self.base_url = config["OLLAMA_BASE_URL"]
        self.timeout = config["REQUEST_TIMEOUT"]
        self.default_model = config["DEFAULT_MODEL"]

    def generate(self, payload, stream=False):
        """Direct Ollama generate call"""
        response = requests.post(
            f"{self.base_url}/api/generate", 
            json=payload, 
            timeout=self.timeout,
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return response.iter_lines(decode_unicode=True)
        else:
            return response.json()

    def generate_openai_compatible(self, payload, stream, model):
        """Generate OpenAI-compatible response"""
        if stream:
            return self._generate_streaming_response(payload, model)
        else:
            return self._generate_non_streaming_response(payload, model)

    def _generate_streaming_response(self, payload, model):
        """Generate streaming response in OpenAI format"""
        def generate():
            response = requests.post(
                f"{self.base_url}/api/generate", 
                json=payload, 
                stream=True, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        ollama_data = json.loads(line)
                        content = ollama_data.get("response", "")
                        if content:
                            openai_chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": content},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                    except json.JSONDecodeError:
                        continue
            
            # Send final done chunk
            done_chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk", 
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(done_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return Response(generate(), mimetype='text/event-stream')

    def _generate_non_streaming_response(self, payload, model):
        """Generate non-streaming response in OpenAI format"""
        response = requests.post(
            f"{self.base_url}/api/generate", 
            json=payload, 
            timeout=self.timeout
        )
        response.raise_for_status()
        result = response.json()
        
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
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        })

    def check_health(self):
        """Check if Ollama is reachable"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", 
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self):
        """Get list of available models from Ollama"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_model_info(self, model_name=None):
        """Get information about a specific model"""
        model_to_check = model_name or self.default_model
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"model": model_to_check},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def chat_completion(self, messages, model=None, stream=False, temperature=0.1, max_tokens=4096):
        """Direct chat completion with Ollama (alternative to generate)"""
        model_to_use = model or self.default_model
        
        # Convert messages to Ollama format
        conversation = []
        for msg in messages:
            conversation.append(f"{msg['role']}: {msg['content']}")
        
        prompt = "\n".join(conversation) + "\nassistant: "
        
        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        return self.generate_openai_compatible(payload, stream, model_to_use)