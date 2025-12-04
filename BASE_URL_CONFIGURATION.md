# Base URL Configuration Guide

This document explains how base URLs are used in the Psalm RAG system.

## Architecture Overview

``` 
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Test Script    │────────▶│  Flask Server    │────────▶│  LlamaCpp AI    │
│  (test script)  │         │  (port 5000)     │         │  (port 8080)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  Cassandra DB    │
                            │  (port 9042)     │
                            └──────────────────┘
```

## Additional Component: Augustine-MCP Server

The Augustine-MCP server is an MCP server that can be directly accessed by CLINE for RAG-based psalm analysis. It connects to both Cassandra DB and LlamaCpp AI server internally:

```
┌─────────────────┐         ┌──────────────────┐
│    CLINE        │────────▶│ Augustine-MCP  │
│                 │         │  (port 9090)   │
└─────────────────┘         └──────────────────┘
                                   │        │
                                   ▼        ▼
                          ┌──────────────────┐ ┌─────────────────┐
                          │  Cassandra DB    │ │  LlamaCpp AI    │
                          │  (port 9042)     │ │  (port 8080)    │
                          └──────────────────┘ └─────────────────┘
```

## Two Different Base URLs

### 1. Flask Server URL (for test script)

- **Purpose**: Where the test script connects to make HTTP requests
- **Used in**: `scripts/test_psalm_rag_live.py`
- **Default**: `http://localhost:5000`
- **Configuration**:
  - Command line: `--base-url http://100.109.56.33:5000`
  - Environment variable: `PSALM_RAG_BASE_URL=http://100.109.56.33:5000`

### 2. LlamaCpp AI Server URL (for Flask server)

- **Purpose**: Where the Flask server connects to get AI responses
- **Used in**: `app/processors/psalm_rag_processor.py` → `app/utils/ai_provider.py`
- **Default**: `http://localhost:8080`
- **Configuration**:
  - Environment variable in Flask app: `LLAMACPP_BASE_URL=http://100.109.56.33:8080`
  - Also requires: `AI_PROVIDER=llamacpp`

### 3. Augustine-MCP Server URL (for RAG processing)

- **Purpose**: Where CLINE connects directly to for RAG-based psalm analysis using the Augustine-MCP server. This service internally queries Cassandra DB for context and calls LlamaCpp AI for response generation.
- **Used in**: CLINE (direct access to MCP server)
- **Default**: `http://localhost:9090`
- **Configuration**:
  - Environment variable in CLINE: `AUGUSTINE_MCP_BASE_URL=http://100.109.56.33:9090`
  - Also requires: `USE_AUGUSTINE_MCP=true`

## Configuration Steps

### For Your Setup (100.109.56.33)

1. **Configure Flask Server Environment** (`.env` file or environment variables):

   ```bash
   # Flask server configuration
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000

   # AI Provider configuration
   AI_PROVIDER=llamacpp
   LLAMACPP_BASE_URL=http://100.109.56.33:8080

   # Augustine-MCP configuration for Latin analysis
   USE_AUGUSTINE_MCP=true
   AUGUSTINE_MCP_BASE_URL=http://100.109.56.33:9090

   # Database configuration
   CASSANDRA_HOSTS=100.109.56.33  # or 127.0.0.1 if running locally
   CASSANDRA_PORT=9042
   ```

2. **Run Test Script**:

   ```bash
   # Option 1: Command line argument
   python scripts/test_psalm_rag_live.py --base-url http://100.109.56.33:5000

   # Option 2: Environment variable
   export PSALM_RAG_BASE_URL=http://100.109.56.33:5000
   python scripts/test_psalm_rag_live.py
   ```

## Code Flow

1. **Test Script** (`test_psalm_rag_live.py`):

   - Uses `base_url` to make HTTP requests to Flask endpoints
   - Example: `POST http://100.109.56.33:5000/api/query_psalm`

2. **Flask Server** (`app/routes/psalm_routes.py`):

   - Receives HTTP request
   - Routes to `PsalmRAGProcessor.process()`

3. **Psalm RAG Processor** (`app/processors/psalm_rag_processor.py`):

   - Uses `self.ai_provider` (passed during initialization)
   - Calls `self.ai_provider.generate_openai_compatible()`

4. **AI Provider** (`app/utils/ai_provider.py`):
   - `LlamaCppProvider` uses `self.base_url` (from config)
   - Makes HTTP request to: `POST {LLAMACPP_BASE_URL}/v1/chat/completions`
   - Example: `POST http://100.109.56.33:8080/v1/chat/completions`

5. **RAG Processing** (CLINE access):
   - When `USE_AUGUSTINE_MCP=true`, CLINE connects directly to Augustine-MCP server
   - Makes HTTP request to: `POST {AUGUSTINE_MCP_BASE_URL}/tools/analyze_psalm` or `POST {AUGUSTINE_MCP_BASE_URL}/tools/ask_augustine`
   - Example: `POST http://100.109.56.33:9090/tools/ask_augustine`
   - The Augustine-MCP server internally:
     * Queries Cassandra DB for psalm context
     * Calls LlamaCpp AI server for generation
     * Returns structured RAG responses

## Verification

To verify your configuration is correct:

1. **Check Flask server can reach LlamaCpp**:

   ```bash
   curl http://100.109.56.33:8080/v1/models
   ```

2. **Check test script can reach Flask server**:

   ```bash
   curl http://100.109.56.33:5000/v1/models
   ```

3. **Check CLINE can reach Augustine-MCP**:

   ```bash
   curl -X POST http://100.109.56.33:9090 -d '{"method": "list_tools"}'
   ```

4. **Test Augustine-MCP RAG functionality**:

   ```bash
   curl -X POST http://100.109.56.33:9090 -d '{"method": "ask_augustine", "params": {"pattern": "augustine_psalm_query", "psalm_number": 23, "model": "deepseek-coder:6.7b"}}'
   ```

5. **Run the test script**:
   ```bash
   python scripts/test_psalm_rag_live.py --base-url http://100.109.56.33:5000
   ```

## Key Files

- `scripts/test_psalm_rag_live.py`: Test script (uses Flask server URL)
- `app/processors/psalm_rag_processor.py`: RAG processor (uses AI provider)
- `app/utils/ai_provider.py`: AI provider implementation (uses LLAMACPP_BASE_URL)
- `app/core/config.py`: Configuration loader (reads LLAMACPP_BASE_URL from env)
- `app/processors/processor_router.py`: Initializes AI provider from config

## Summary

- **Test Script → Flask Server**: Configure via `--base-url` or `PSALM_RAG_BASE_URL`
- **Flask Server → LlamaCpp AI**: Configure via `LLAMACPP_BASE_URL` environment variable
- **Flask Server → Cassandra**: Configure via `CASSANDRA_HOSTS` environment variable

All URLs are configurable via environment variables - no hardcoded IPs in the code.
