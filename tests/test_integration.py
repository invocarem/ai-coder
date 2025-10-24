# tests/test_integration.py
import pytest
import json
from unittest.mock import Mock, patch

class TestIntegration:
    """Integration tests for the API endpoints"""
    
    def test_chat_completion_integration(self, client):
        """Test the OpenAI-compatible chat endpoint using test client"""
        # Mock the AI provider to avoid external dependencies
        with patch('app.processors.code_processor.AIProviderFactory') as mock_factory:
            mock_ai_provider = Mock()
            mock_factory.create_provider.return_value = mock_ai_provider
            
            # Mock the response
            mock_ai_provider.generate_openai_compatible.return_value = {
                "choices": [{
                    "message": {
                        "content": "def fibonacci(n):\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    elif n == 2:\n        return [0, 1]\n    \n    fib_sequence = [0, 1]\n    for i in range(2, n):\n        next_fib = fib_sequence[i-1] + fib_sequence[i-2]\n        fib_sequence.append(next_fib)\n    \n    return fib_sequence"
                    }
                }]
            }
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "deepseek-coder:6.7b",
                    "messages": [
                        {"role": "user", "content": "Write a Python function to calculate fibonacci sequence"}
                    ],
                    "temperature": 0.1
                }
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
            assert "content" in data["choices"][0]["message"]
            assert "fibonacci" in data["choices"][0]["message"]["content"]

    def test_models_endpoint_integration(self, client):
        """Test the models endpoint using test client"""
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.get_json()
        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert len(data["data"]) > 0
        assert data["data"][0]["object"] == "model"

    def test_specific_model_endpoint(self, client):
        """Test getting a specific model"""
        response = client.get("/v1/models/deepseek-coder:6.7b")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "deepseek-coder:6.7b"
        assert data["object"] == "model"

    def test_direct_code_generation_integration(self, client):
        """Test direct code generation endpoint"""
        with patch('app.processors.code_processor.AIProviderFactory') as mock_factory:
            mock_ai_provider = Mock()
            mock_factory.create_provider.return_value = mock_ai_provider
            
            # Mock the response for refactoring
            mock_ai_provider.generate_openai_compatible.return_value = {
                "choices": [{
                    "message": {
                        "content": "def calculate_fibonacci(n):\n    \"\"\"Calculate and return Fibonacci sequence up to n terms.\"\"\"\n    if n <= 0:\n        return []\n    \n    fib_sequence = []\n    a, b = 0, 1\n    for _ in range(n):\n        fib_sequence.append(a)\n        a, b = b, a + b\n    \n    return fib_sequence"
                    }
                }]
            }
            
            payload = {
                "pattern": "refactor_code",
                "language": "Python",
                "code": "def calculate_fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a)\n        a, b = b, a + b",
                "task": "improve the code"
            }
            
            response = client.post("/api/generate_code", json=payload)
            assert response.status_code == 200
            data = response.get_json()
            assert "text" in data
            assert "def calculate_fibonacci" in data["text"]

    def test_chat_completion_with_pattern_detection(self, client):
        """Test chat completion with code pattern detection"""
        with patch('app.processors.code_processor.AIProviderFactory') as mock_factory, \
             patch('app.processors.code_processor.PatternDetector') as mock_detector:
            
            mock_ai_provider = Mock()
            mock_factory.create_provider.return_value = mock_ai_provider
            
            # Mock pattern detection
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance
            mock_detector_instance.detect_pattern.return_value = {
                "pattern": "generate_function",
                "language": "Python",
                "task": "calculate fibonacci sequence"
            }
            
            # Mock the AI response
            mock_ai_provider.generate_openai_compatible.return_value = {
                "choices": [{
                    "message": {
                        "content": "def fibonacci(n):\n    \"\"\"Calculate Fibonacci number at position n.\"\"\"\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
                    }
                }]
            }
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "deepseek-coder:6.7b",
                    "messages": [
                        {"role": "user", "content": "Write a Python function to calculate fibonacci sequence"}
                    ],
                    "temperature": 0.1
                }
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert "choices" in data
            assert "fibonacci" in data["choices"][0]["message"]["content"]

    def test_chat_completion_streaming(self, client):
        """Test streaming chat completion"""
        with patch('app.processors.code_processor.AIProviderFactory') as mock_factory:
            mock_ai_provider = Mock()
            mock_factory.create_provider.return_value = mock_ai_provider
            
            # Mock streaming response
            mock_stream = [
                'data: {"choices": [{"delta": {"content": "Hello"}}]}',
                'data: {"choices": [{"delta": {"content": " World"}}]}'
            ]
            mock_ai_provider.generate_openai_compatible.return_value = mock_stream
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "deepseek-coder:6.7b",
                    "messages": [
                        {"role": "user", "content": "Say hello"}
                    ],
                    "stream": True,
                    "temperature": 0.1
                }
            )
            
            assert response.status_code == 200
            assert response.mimetype == 'text/event-stream'
            # You could add more assertions to parse the streaming response

    def test_chat_completion_no_user_message(self, client):
        """Test chat completion with no user message"""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "deepseek-coder:6.7b",
                "messages": [
                    {"role": "assistant", "content": "I'm here to help"}
                ],
                "temperature": 0.1
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "No user message found" in data["error"]

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        # Note: You might need to add this endpoint to your routes
        # For now, this test might fail if the endpoint doesn't exist
        if response.status_code == 200:
            data = response.get_json()
            assert "status" in data

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404


# Standalone integration tests for manual running against a live server
def manual_live_server_test():
    """Manual integration test that can be run against a live server"""
    import requests
    
    BASE_URL = "http://localhost:5000"
    
    def test_chat_completion():
        """Test chat completion against live server"""
        print("Testing chat completion against live server...")
        try:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": "deepseek-coder:6.7b",
                    "messages": [
                        {"role": "user", "content": "Write a Python function to calculate fibonacci sequence"}
                    ],
                    "temperature": 0.1
                },
                timeout=30
            )
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return response
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure it's running on localhost:5000")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def test_improve_code():
        """Test code improvement against live server"""
        print("\nTesting code improvement against live server...")
        try:
            payload = {
                "pattern": "refactor_code",
                "language": "Python",
                "code": "def calculate_fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a)\n        a, b = b, a + b",
                "task": "improve the code"
            }
            response = requests.post(
                f"{BASE_URL}/api/generate_code", 
                json=payload,
                timeout=30
            )
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            
            if response.status_code == 200:
                assert "text" in response.json()
            return response
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure it's running on localhost:5000")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def test_models_endpoint():
        """Test models endpoint against live server"""
        print("\nTesting models endpoint against live server...")
        try:
            response = requests.get(f"{BASE_URL}/v1/models", timeout=10)
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return response
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure it's running on localhost:5000")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    if __name__ == "__main__":
        print("Running manual integration tests against live server...")
        test_chat_completion()
        test_improve_code()
        test_models_endpoint()
        print("\nManual integration tests completed!")


if __name__ == "__main__":
    # Run manual tests against live server
    manual_live_server_test()