# test_client.py
import requests

def test_chat_completion():
    response = requests.post(
        "http://localhost:5000/v1/chat/completions",
        json={
            "model": "deepseek-coder:6.7b",
            "messages": [
                {"role": "user", "content": "Write a Python function to calculate fibonacci sequence"}
            ],
            "temperature": 0.1
        }
    )
    print(response.json())

def test_improve_code():
    payload = {
        "pattern": "refactor_code",
        "language": "Python",
        "code": "def calculate_fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a)\n        a, b = b, a + b",
        "task": "improve the code"
    }
    response = requests.post("http://localhost:5000/api/generate_code", json=payload)
    print(response.json())
    assert response.status_code == 200
    assert "text" in response.json()


if __name__ == "__main__":
    test_chat_completion()
    test_improve_code()
