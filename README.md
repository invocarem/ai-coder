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

### **Clone the repository**

```bash
git clone <repository-url>
cd ai-coder
```

### **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **Install dependencies**

```bash
pip install -r requirements.txt
```

#### **Set up environment variables** (create a `.env` file)

```bash
# AI Provider Configuration
AI_PROVIDER=ollama  # or openai, mistral, llamacpp
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

| Pattern             | Description                                       | Required Fields             |
| ------------------- | ------------------------------------------------- | --------------------------- |
| `generate_function` | Generate a function with type hints and docstring | `language`, `task`          |
| `fix_bug`           | Fix bugs in provided code                         | `language`, `code`, `issue` |
| `explain_code`      | Explain how code works                            | `language`, `code`          |
| `refactor_code`     | Refactor code for readability and performance     | `language`, `code`          |
| `write_tests`       | Write unit tests for code                         | `language`, `code`          |
| `add_docs`          | Add documentation and comments                    | `language`, `code`          |
| `custom`            | Use a custom prompt                               | `prompt`                    |

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

### First Test

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

## Test Suite

The project includes a comprehensive test suite with unit tests and integration tests:

### Unit Tests

The unit tests (`tests/test_code_processor.py`) provide comprehensive coverage of the `CodeProcessor` class functionality:

**Test Coverage:**

- ✅ **Initialization Tests**: Verify proper setup of AI providers and configuration
- ✅ **Code Generation Tests**: Test all code generation patterns (generate_function, fix_bug, explain_code, refactor_code, write_tests, add_docs, custom)
- ✅ **Validation Tests**: Test input validation for required fields and error handling
- ✅ **Response Format Tests**: Test both OpenAI and Ollama response format handling
- ✅ **Streaming Tests**: Test real-time streaming response functionality
- ✅ **Error Handling Tests**: Test AI provider connection errors and exception handling
- ✅ **Chat Completion Tests**: Test OpenAI-compatible chat completions with pattern detection
- ✅ **Health Check Tests**: Test system health monitoring
- ✅ **Batch Processing Tests**: Test multiple request handling
- ✅ **Pattern Detection Tests**: Test automatic pattern recognition from natural language

**Running Unit Tests:**

```bash
# Run all unit tests
pytest tests/test_code_processor.py -v

# Run with coverage
pytest tests/test_code_processor.py --cov=app.processors.code_processor

# Run specific test categories
pytest tests/test_code_processor.py::TestCodeProcessor::test_generate_code_success -v
```

### Integration Tests

The integration tests (`tests/test_integration.py`) test the complete API endpoints and workflows:

**Integration Test Coverage:**

- ✅ **Chat Completion Integration**: Test OpenAI-compatible endpoints with mocked AI providers
- ✅ **Models Endpoint**: Test model listing and specific model retrieval
- ✅ **Code Generation Integration**: Test direct code generation through API endpoints
- ✅ **Pattern Detection Integration**: Test automatic pattern detection in chat completions
- ✅ **Streaming Integration**: Test streaming responses through API endpoints
- ✅ **Error Handling Integration**: Test error responses and validation through API
- ✅ **Health Check Integration**: Test health monitoring endpoints

**Running Integration Tests:**

```bash
# Run integration tests with mocked dependencies
pytest tests/test_integration.py -v

# Run integration tests with coverage
pytest tests/test_integration.py --cov=app
```

### Live Server Testing

The `scripts/test_live_integration.py` script provides comprehensive testing against a running server:

**Live Test Features:**

- 🔍 **Server Connectivity**: Tests basic server connection and responsiveness
- 🧪 **Function Generation**: Tests code generation with real AI providers
- 🔧 **Code Refactoring**: Tests code improvement and refactoring capabilities
- 🐛 **Bug Fixing**: Tests bug detection and fixing functionality
- 🤖 **OpenAI Compatibility**: Tests OpenAI-compatible chat completions
- ⏱️ **Performance Testing**: Measures response times and performance metrics
- 📊 **Comprehensive Reporting**: Provides detailed test results and summaries

**Running Live Server Tests:**

```bash
# Make sure the server is running first
python main.py

# In another terminal, run the live integration tests
python scripts/test_live_integration.py
```

**Live Test Output Example:**

```
🚀 Starting Live Server Tests
==================================================
🔍 Testing server connection...
✅ Server is running and responsive

🧪 Testing function generation...
✅ Function generation successful (2.34s)
   Response preview: def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)...

🔧 Testing code refactoring...
✅ Code refactoring successful (1.87s)
   Response preview: def sum_list(lst):
    """Calculate the sum of a list of numbers."""
    return sum(lst)...

🐛 Testing bug fixing...
✅ Bug fixing successful (2.12s)
   Response preview: def divide_numbers(a, b):
    """Divide two numbers with zero division handling."""
    if b == 0:
        raise ValueError("Cannot divide by zero")...

🤖 Testing OpenAI-compatible endpoint...
✅ OpenAI endpoint successful (2.56s)
   Response preview: def fibonacci(n):
    """Calculate Fibonacci number at position n."""
    if n <= 1:
        return n...

==================================================
📊 TEST SUMMARY
==================================================
Tests passed: 4/4
🎉 All live server tests passed!
```

### Manual Integration Testing

For manual testing against a live server, you can also run the manual integration tests:

```bash
# Run manual integration tests
python tests/test_integration.py
```

### Test Configuration

The tests use pytest with the following features:

- **Flask Test Client**: Uses Flask's built-in test client for API testing
- **Mocking**: Mocks external AI providers to avoid dependencies during unit testing
- **Fixtures**: Provides reusable test fixtures for consistent test setup
- **Coverage**: Supports code coverage reporting to ensure comprehensive testing

**Test Dependencies:**

```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov
```

### Continuous Integration

The test suite is designed to work with CI/CD pipelines:

```bash
# Run all tests for CI
pytest tests/ --cov=app --cov-report=xml

# Run tests with verbose output
pytest tests/ -v --tb=short

# Run tests in parallel (if pytest-xdist is installed)
pytest tests/ -n auto
```

## Configuration

The application uses a flexible configuration system that supports:

- **Environment Variables**: Set via `.env` file or system environment
- **Multiple AI Providers**: Easy switching between Ollama, OpenAI, Mistral, and llama.cpp
- **Customizable Parameters**: Temperature, top_p, max_tokens, timeout settings
- **Flask Configuration**: Host, port, debug mode settings

### Configuration Options

| Variable              | Default                  | Description                                  |
| --------------------- | ------------------------ | -------------------------------------------- |
| `AI_PROVIDER`         | `ollama`                 | AI provider to use (ollama, openai, mistral, llamacpp) |
| `OLLAMA_BASE_URL`     | `http://localhost:11434` | Ollama server URL                            |
| `LLAMACPP_BASE_URL`   | `http://localhost:8080`  | llama.cpp server URL                         |
| `DEFAULT_MODEL`       | `deepseek-coder:6.7b`    | Default model to use                         |
| `REQUEST_TIMEOUT`     | `120`                    | Request timeout in seconds                   |
| `MAX_TOKENS`          | `4096`                   | Maximum tokens to generate                   |
| `DEFAULT_TEMPERATURE` | `0.1`                    | Default temperature for generation           |
| `DEFAULT_TOP_P`       | `0.9`                    | Default top_p for generation                 |

#### Using llama.cpp

To route all requests through a local `llama.cpp` server:

```bash
AI_PROVIDER=llamacpp
LLAMACPP_BASE_URL=http://localhost:8080  # adjust if your server runs elsewhere
LLAMACPP_MODEL=gpt-oss-120b              # optional override, defaults to gpt-oss-120b
```

The server must be started with the OpenAI-compatible HTTP interface enabled (e.g., `./server -m <model> --host 0.0.0.0 --port 8080 --api`). Streaming responses are supported automatically.

## Project Structure

```
ai-coder/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration management
│   ├── processors/
│   │   ├── __init__.py          # Processors package
│   │   └── code_processor.py    # Main code processing logic
│   ├── routes/
│   │   ├── __init__.py          # Routes package
│   │   └── openai_routes.py     # OpenAI-compatible endpoints
│   └── utils/
│       ├── __init__.py          # Utils package
│       ├── ai_provider.py       # AI provider abstractions
│       └── pattern_detector.py  # Pattern detection logic
├── tests/
│   ├── __init__.py              # Tests package
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_code_processor.py   # Unit tests for CodeProcessor
│   └── test_integration.py      # Integration tests for API endpoints
├── scripts/
│   └── test_live_integration.py # Live server integration testing
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Development

### Adding New AI Providers

1. Create a new provider class in `app/utils/ai_provider.py`
2. Implement the `AIProvider` abstract base class
3. Add the provider to the `AIProviderFactory`
4. Update configuration options
5. Add tests for the new provider in `test_code_processor.py`

### Adding New Patterns

1. Add the pattern to `prompt_patterns` in `CodeProcessor`
2. Update validation logic in `_validate_pattern_data`
3. Add convenience endpoint if needed
4. Add unit tests for the new pattern
5. Add integration tests for the new pattern
6. Update documentation

### Testing Guidelines

When contributing to the project, please ensure:

1. **Unit Tests**: Add comprehensive unit tests for new functionality in `test_code_processor.py`
2. **Integration Tests**: Add integration tests for new API endpoints in `test_integration.py`
3. **Live Testing**: Test new features using the live integration test script
4. **Test Coverage**: Maintain high test coverage (aim for >90%)
5. **Test Documentation**: Update test documentation when adding new test cases

**Running Tests Before Committing:**

```bash
# Run all tests to ensure nothing is broken
pytest tests/ -v

# Run tests with coverage to check coverage
pytest tests/ --cov=app --cov-report=html

# Run live integration tests if adding new endpoints
python scripts/test_live_integration.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add comprehensive tests for new functionality
5. Ensure all tests pass (unit, integration, and live tests)
6. Update documentation
7. Submit a pull request

**Pull Request Requirements:**

- All tests must pass
- New functionality must have corresponding tests
- Code coverage should not decrease
- Documentation must be updated
- Live integration tests should pass

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:

- Create an issue in the repository
- Check the configuration and logs
- Ensure your AI provider is properly configured and running


### Test pattern_detector

```bash
$ pytest tests/test_pattern_detector.py::TestPatternDetector::test_extract_code_blocks_with_blank_lines -v -s

$ pytest tests/test_pattern_detector.py::TestPatternDetector::test_real_world_explain_code_scenario -v -s

# Test all pattern detector tests
pytest tests/test_pattern_detector.py -v
```

```
curl -X POST http://localhost:5000/api/query_psalm \
  -H "Content-Type: application/json" \
  -d '{
    "psalm_number": 1,
    "verse_number": 1,
    "question": "How does Augustine interpret the three verbs?",
    "model": "mistral:latest"
  }'
``` 


### build and run docker images

```
docker system prune -af

docker compose up --build -d whitaker-mcp
docker run -it --rm --network ai-coder_default \
  -e CASSANDRA_HOST=cassandra-server \
  --entrypoint bash \
  ai-coder-augustine-mcp
docker rm -f $(docker ps -aq --filter ancestor=whitaker-mcp)
docker rm -f $(docker ps -aq --filter ancestor=augustine-mcp)
```


### mcp commands

```
{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}
{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```