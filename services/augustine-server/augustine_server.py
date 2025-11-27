import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

# Import the existing processor and AI provider utilities
from app.processors.psalm_rag_processor import PsalmRAGProcessor
from app.utils.ai_provider import AIProvider  # Adjust import if the class name differs

logger = logging.getLogger("augustine_server")
app = FastAPI(title="Augustine MCP Server")

# ----------------------------------------------------------------------
# Initialize AI provider and processor (mirroring whitaker_server.py logic)
# ----------------------------------------------------------------------
try:
    ai_provider = AIProvider()  # The constructor may accept config; adjust if needed
    processor = PsalmRAGProcessor(ai_provider)
except Exception as e:
    logger.error(f"Failed to initialize processor: {e}")
    raise RuntimeError(f"Processor initialization error: {e}")

# ----------------------------------------------------------------------
# Pydantic request / response models
# ----------------------------------------------------------------------
class ProcessRequest(BaseModel):
    pattern_data: Dict[str, Any]
    model: str
    stream: bool = False
    original_data: Dict[str, Any] = {}

class ProcessResponse(BaseModel):
    result: Any

# ----------------------------------------------------------------------
# Health‑check endpoint
# ----------------------------------------------------------------------
@app.get("/health")
def health_check():
    try:
        return processor.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------
# Main processing endpoint
# ----------------------------------------------------------------------
@app.post("/process", response_model=ProcessResponse)
def process(request: ProcessRequest):
    try:
        # The original processor returns a Flask Response object; we extract its JSON payload
        flask_response = processor.process(
            request.pattern_data,
            request.model,
            request.stream,
            request.original_data,
        )
        # If the response is a Flask Response, attempt to get its JSON data
        if hasattr(flask_response, "json"):
            payload = flask_response.json
        else:
            # Fallback: assume the processor already returned a dict‑like object
            payload = flask_response
        return ProcessResponse(result=payload)
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
