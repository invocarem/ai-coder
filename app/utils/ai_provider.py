# app/utils/ai_provider.py
from abc import ABC, abstractmethod
import requests
import json
import time
from typing import Dict, Any, Generator

class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def generate_openai_compatible(self, messages: list, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        pass

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str, timeout: float):
        self.base_url = base_url
        self.timeout = timeout

    def generate(self, prompt: str, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get('temperature', 0.1),
                "top_p": kwargs.get('top_p', 0.9),
                "top_k": kwargs.get('top_k', 40),
                "num_predict": kwargs.get('max_tokens', 4096)
            }
        }
        
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

    def generate_openai_compatible(self, messages: list, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        # Convert messages to Ollama format
        conversation = []
        for msg in messages:
            conversation.append(f"{msg['role']}: {msg['content']}")
        
        prompt = "\n".join(conversation) + "\nassistant: "
        
        return self.generate(prompt, model, stream, **kwargs)

class OpenAIProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str, timeout: float):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, prompt: str, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        # For OpenAI, we use the chat completion endpoint
        messages = [{"role": "user", "content": prompt}]
        return self.generate_openai_compatible(messages, model, stream, **kwargs)

    def generate_openai_compatible(self, messages: list, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": kwargs.get('temperature', 0.1),
            "max_tokens": kwargs.get('max_tokens', 4096),
            "top_p": kwargs.get('top_p', 0.9)
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout,
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return response.iter_lines(decode_unicode=True)
        else:
            return response.json()

class MistralProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str, timeout: float):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, prompt: str, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        messages = [{"role": "user", "content": prompt}]
        return self.generate_openai_compatible(messages, model, stream, **kwargs)

    def generate_openai_compatible(self, messages: list, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": kwargs.get('temperature', 0.1),
            "max_tokens": kwargs.get('max_tokens', 4096),
            "top_p": kwargs.get('top_p', 0.9)
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout,
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return response.iter_lines(decode_unicode=True)
        else:
            return response.json()

class AIProviderFactory:
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> AIProvider:
        provider_type = config.get("AI_PROVIDER", "ollama")
        
        if provider_type == "openai":
            return OpenAIProvider(
                base_url=config["OPENAI_BASE_URL"],
                api_key=config["OPENAI_API_KEY"],
                timeout=config["REQUEST_TIMEOUT"]
            )
        elif provider_type == "mistral":
            return MistralProvider(
                base_url=config["MISTRAL_BASE_URL"],
                api_key=config["MISTRAL_API_KEY"],
                timeout=config["REQUEST_TIMEOUT"]
            )
        else:  # ollama (default)
            return OllamaProvider(
                base_url=config["OLLAMA_BASE_URL"],
                timeout=config["REQUEST_TIMEOUT"]
            )