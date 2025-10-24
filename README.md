# AI Coder

A Flask-based AI code generation service that provides intelligent code assistance through multiple AI providers (Ollama, OpenAI, Mistral). The service supports various code generation patterns including function generation, bug fixing, code refactoring, documentation, and testing.

## Features

- **Multiple AI Providers**: Support for Ollama (local), OpenAI, and Mistral AI providers
- **Code Generation Patterns**: 
  - Generate functions with type hints and documentation
  - Fix bugs in existing code
  - Refactor code for better readability and performance
  - Explain how code works
  - Write comprehensive unit tests
  - Add documentation and comments
  - Custom prompts for specialized tasks
- **OpenAI-Compatible API**: Full compatibility with OpenAI's chat completions API
- **Streaming Support**: Real-time streaming responses for better user experience
- **Multi-Language Support**: Python, JavaScript, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, TypeScript, Bash, Awk
- **Pattern Detection**: Automatic detection of code generation patterns from natural language
- **Batch Processing**: Handle multiple requests efficiently

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ai-coder
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables** (create a `.env` file):
```bash
# AI Provider Configuration
AI_PROVIDER=ollama  # or openai, mistral
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=deepseek-coder:6.7b

# OpenAI Configuration (if using OpenAI)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_api_key

# Mistral Configuration (if using Mistral)
MISTRAL_BASE_URL=https://api.mistral.ai/v1
MISTRAL_API_KEY=your_mistral_api_key

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Request Configuration
REQUEST_TIMEOUT=120
MAX_TOKENS=4096
DEFAULT_TEMPERATURE=0.1
DEFAULT_TOP_P=0.9
```

## Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:5000` by default.

### API Endpoints

#### 1. Generate Code (Main Endpoint)
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "generate_function",
    "language": "Python",
    "task": "sort a list of integers"
  }'
```

#### 2. OpenAI-Compatible Chat Completions
```bash
curl -X POST http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-coder:6.7b",
    "messages": [
      {"role": "user", "content": "Write a Python function to calculate fibonacci sequence"}
    ],
    "temperature": 0.1
  }'
```

#### 3. Using Different Patterns with /api/generate_code

All code generation uses the main `/api/generate_code` endpoint with different `pattern` values:

**Generate Function**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "generate_function",
    "language": "Python",
    "task": "calculate the factorial of a number"
  }'
```

**Refactor Code**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "refactor_code",
    "language": "Python",
    "code": "def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i]\n    return total"
  }'
```

**Fix Bug**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "fix_bug",
    "language": "Python",
    "code": "def divide(a, b):\n    return a / b",
    "issue": "division by zero error"
  }'
```

**Explain Code**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "explain_code",
    "language": "Python",
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
  }'
```

**Write Tests**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "write_tests",
    "language": "Python",
    "code": "def add(a, b):\n    return a + b"
  }'
```

**Add Documentation**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "add_docs",
    "language": "Python",
    "code": "def calculate_area(radius):\n    return 3.14159 * radius * radius"
  }'
```

**Custom Prompt**:
```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "custom",
    "prompt": "Write a Python function that implements a binary search algorithm with detailed comments"
  }'
```

#### 4. Convenience Endpoints (Alternative)

The API also provides convenience endpoints that internally use `/api/generate_code`:

**Generate Function** (convenience):
```bash
curl -X POST http://127.0.0.1:5000/api/generate_function \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Python",
    "task": "calculate the factorial of a number"
  }'
```

**Refactor Code** (convenience):
```bash
curl -X POST http://127.0.0.1:5000/api/refactor_code \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Python",
    "code": "def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i]\n    return total"
  }'
```

**Fix Bug** (convenience):
```bash
curl -X POST http://127.0.0.1:5000/api/fix_bug \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Python",
    "code": "def divide(a, b):\n    return a / b",
    "issue": "division by zero error"
  }'
```

**Explain Code** (convenience):
```bash
curl -X POST http://127.0.0.1:5000/api/explain_code \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Python",
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
  }'
```

**Write Tests** (convenience):
```bash
curl -X POST http://127.0.0.1:5000/api/write_tests \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Python",
    "code": "def add(a, b):\n    return a + b"
  }'
```

**Add Documentation** (convenience):
```bash
curl -X POST http://127.0.0.1:5000/api/add_docs \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Python",
    "code": "def calculate_area(radius):\n    return 3.14159 * radius * radius"
  }'
```

#### 5. Status and Information Endpoints

**Health Check**:
```bash
curl http://127.0.0.1:5000/api/health
```

**List Available Models**:
```bash
curl http://127.0.0.1:5000/api/models
```

**List Supported Patterns**:
```bash
curl http://127.0.0.1:5000/api/patterns
```

**Application Status**:
```bash
curl http://127.0.0.1:5000/api/status
```

### Supported Patterns

| Pattern | Description | Required Fields |
|---------|-------------|----------------|
| `generate_function` | Generate a function with type hints and docstring | `language`, `task` |
| `fix_bug` | Fix bugs in provided code | `language`, `code`, `issue` |
| `explain_code` | Explain how code works | `language`, `code` |
| `refactor_code` | Refactor code for readability and performance | `language`, `code` |
| `write_tests` | Write unit tests for code | `language`, `code` |
| `add_docs` | Add documentation and comments | `language`, `code` |
| `custom` | Use a custom prompt | `prompt` |

### Streaming Responses

Enable streaming for real-time responses:

```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "generate_function",
    "language": "Python",
    "task": "implement quicksort algorithm",
    "stream": true
  }'
```

## Testing

### First Test:

```bash
curl -X POST http://127.0.0.1:5000/api/generate_code \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "generate_function",
    "language": "Python",
    "task": "sort a list of integers"
  }'
```

### VS Code Continue Integration:

```
write_code in awk: sort an array of strings by letters
```

### Running Test Scripts

```bash
# Run the test client
python tests/test_client.py

# Run test scripts
python tests/test_scripts.py
```

### Automated Testing

```bash
# Run pytest tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## Configuration

The application uses a flexible configuration system that supports:

- **Environment Variables**: Set via `.env` file or system environment
- **Multiple AI Providers**: Easy switching between Ollama, OpenAI, and Mistral
- **Customizable Parameters**: Temperature, top_p, max_tokens, timeout settings
- **Flask Configuration**: Host, port, debug mode settings

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `ollama` | AI provider to use (ollama, openai, mistral) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `DEFAULT_MODEL` | `deepseek-coder:6.7b` | Default model to use |
| `REQUEST_TIMEOUT` | `120` | Request timeout in seconds |
| `MAX_TOKENS` | `4096` | Maximum tokens to generate |
| `DEFAULT_TEMPERATURE` | `0.1` | Default temperature for generation |
| `DEFAULT_TOP_P` | `0.9` | Default top_p for generation |

## Project Structure

```
ai-coder/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration management
│   ├── processors/
│   │   └── code_processor.py    # Main code processing logic
│   ├── routes/
│   │   ├── api_routes.py        # Main API endpoints
│   │   └── openai_routes.py     # OpenAI-compatible endpoints
│   └── utils/
│       ├── ai_provider.py       # AI provider abstractions
│       └── pattern_detector.py  # Pattern detection logic
├── tests/
│   ├── test_client.py          # Test client examples
│   └── test_scripts.py         # Test scripts
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development

### Adding New AI Providers

1. Create a new provider class in `app/utils/ai_provider.py`
2. Implement the `AIProvider` abstract base class
3. Add the provider to the `AIProviderFactory`
4. Update configuration options

### Adding New Patterns

1. Add the pattern to `prompt_patterns` in `CodeProcessor`
2. Update validation logic in `_validate_pattern_data`
3. Add convenience endpoint if needed
4. Update documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Check the configuration and logs
- Ensure your AI provider is properly configured and running