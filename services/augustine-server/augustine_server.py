#!/usr/bin/env python3
"""
Augustine MCP Server - RAG processor wrapped as MCP tools.
Usage:
    python augustine_server.py  # stdio transport (for CLINE)
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add project root to Python path for local development
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.core.config import load_config
from app.utils.ai_provider import AIProviderFactory

# Import the processor module directly
import app.processors.psalm_rag_processor as psalm_processor_module

logger = logging.getLogger("augustine-mcp")
app = Server("augustine-mcp")

# ----------------------------------------------------------------------
# Initialize AI provider and processor
# ----------------------------------------------------------------------
try:
    # Load configuration from .env
    config = load_config()
    # Create AI provider using factory based on config
    ai_provider = AIProviderFactory.create_provider(config)
    processor = psalm_processor_module.PsalmRAGProcessor(ai_provider)
except Exception as e:
    logger.error(f"Failed to initialize processor: {e}")
    raise RuntimeError(f"Processor initialization error: {e}")

# ----------------------------------------------------------------------
# Define MCP tools
# ----------------------------------------------------------------------
@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="analyze_psalm",
            description="Process a psalm query using the Augustine RAG processor (legacy interface).",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_data": {"type": "object"},
                    "model": {"type": "string"},
                    "stream": {"type": "boolean"},
                    "original_data": {"type": "object"}
                },
                "required": ["pattern_data", "model"]
            }
        ),
        Tool(
            name="ask_augustine",
            description="Ask Augustine a question about a psalm using simplified parameters: pattern, psalm_number, verse_number, and question. This is the recommended interface.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "enum": ["augustine_psalm_query", "psalm_word_analysis"]},
                    "psalm_number": {"type": "integer"},
                    "verse_number": {"type": "integer", "nullable": true},
                    "question": {"type": "string"},
                    "model": {"type": "string"},
                    "stream": {"type": "boolean"},
                    "original_data": {"type": "object"}
                },
                "required": ["pattern", "psalm_number", "model"]
            }
        ),
        Tool(
            name="get_psalm_health",
            description="Check the health status of the Augustine processor.",
            inputSchema={                     
                "type": "object",
                "properties": {}
            }
        )
    ]

# ----------------------------------------------------------------------
# Implement tool handlers
# ----------------------------------------------------------------------
@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    logger.info(f"=== TOOL CALL START ===")
    logger.info(f"Tool: {name}")
    logger.info(f"Arguments: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
    
    if name == "analyze_psalm":
        try:
            # Extract required parameters with proper fallbacks
            pattern_data = arguments.get("pattern_data", {})
            model = arguments.get("model")
            stream = arguments.get("stream", False)
            original_data = arguments.get("original_data", {})
            
            logger.info(f"Processing analyze_psalm")
            logger.info(f"pattern_data: {json.dumps(pattern_data, indent=2, ensure_ascii=False)}")
            logger.info(f"model: {model}")
            logger.info(f"stream: {stream}")
            
            # Validate required parameters
            if not pattern_data:
                logger.error("pattern_data is required but not provided")
                return [TextContent(type="text", text=json.dumps({"error": "pattern_data is required"}, ensure_ascii=False))]
            if not model:
                logger.error("model is required but not provided")
                return [TextContent(type="text", text=json.dumps({"error": "model is required"}, ensure_ascii=False))]
                
            # Ensure pattern_data has the required 'pattern' field
            if "pattern" not in pattern_data:
                logger.error("pattern_data must contain 'pattern' field")
                return [TextContent(type="text", text=json.dumps({"error": "pattern_data must contain 'pattern' field"}, ensure_ascii=False))]
                
            logger.info(f"Validated parameters - pattern: {pattern_data.get('pattern')}")
            
            # Pass all parameters to processor
            result = processor.process(
                pattern_data,
                model,
                stream,
                original_data
            )
            
            logger.info("Successfully passed parameters to processor")
            
            # Handle streaming response
            if stream and hasattr(result, '__iter__') and not isinstance(result, (str, dict, list)):
                # For streaming responses, collect the entire stream
                full_response = ""
                for chunk in result:
                    if isinstance(chunk, str):
                        full_response += chunk
                logger.info(f"Streaming response collected: {len(full_response)} characters")
                return [TextContent(type="text", text=json.dumps({"content": full_response}, ensure_ascii=False))]
            
            # Handle regular response (dictionary with possible status code)
            if isinstance(result, tuple) and len(result) == 2:
                payload, status_code = result
                logger.info(f"Regular response received with status code: {status_code}")
                return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]
            else:
                logger.info("Regular response received")
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
                
        except Exception as e:
            logger.error(f"Error in analyze_psalm: {str(e)}", exc_info=True)
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    elif name == "ask_augustine":
        try:
            # Extract parameters from the simplified interface
            pattern = arguments.get("pattern")
            psalm_number = arguments.get("psalm_number")
            verse_number = arguments.get("verse_number")
            question = arguments.get("question", "")
            model = arguments.get("model")
            stream = arguments.get("stream", False)
            original_data = arguments.get("original_data", {})
            
            logger.info(f"Processing ask_augustine")
            logger.info(f"pattern: {pattern}")
            logger.info(f"psalm_number: {psalm_number}")
            logger.info(f"verse_number: {verse_number}")
            logger.info(f"question: {question}")
            logger.info(f"model: {model}")
            logger.info(f"stream: {stream}")
            
            # Validate required parameters
            if not pattern:
                logger.error("pattern is required but not provided")
                return [TextContent(type="text", text=json.dumps({"error": "pattern is required"}, ensure_ascii=False))]
            if not psalm_number:
                logger.error("psalm_number is required but not provided")
                return [TextContent(type="text", text=json.dumps({"error": "psalm_number is required"}, ensure_ascii=False))]
            if not model:
                logger.error("model is required but not provided")
                return [TextContent(type="text", text=json.dumps({"error": "model is required"}, ensure_ascii=False))]
                
            logger.info("All required parameters validated successfully")
            
            # Construct pattern_data in the expected format
            pattern_data = {
                "pattern": pattern,
                "psalm_number": psalm_number,
                "verse_number": verse_number,
                "question": question
            }
            
            logger.info(f"Constructed pattern_data: {json.dumps(pattern_data, indent=2, ensure_ascii=False)}")
            
            # Call the existing analyze_psalm logic with the constructed pattern_data
            new_arguments = {
                "pattern_data": pattern_data,
                "model": model,
                "stream": stream,
                "original_data": original_data
            }
            
            logger.info(f"Passing to analyze_psalm with arguments: {json.dumps(new_arguments, indent=2, ensure_ascii=False)}")
            
            # Reuse the existing analyze_psalm handler logic
            result = await call_tool("analyze_psalm", new_arguments)
            
            logger.info("Successfully delegated to analyze_psalm")
            return result
            
        except Exception as e:
            logger.error(f"Error in ask_augustine: {str(e)}", exc_info=True)
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    elif name == "get_psalm_health":
        try:
            logger.info("Processing get_psalm_health")
            health = processor.health_check()
            logger.info(f"Health check result: {json.dumps(health, indent=2, ensure_ascii=False)}")
            return [TextContent(type="text", text=json.dumps(health, ensure_ascii=False))]
        except Exception as e:
            logger.error(f"Error in get_psalm_health: {str(e)}", exc_info=True)
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    logger.error(f"Unknown tool called: {name}")
    raise ValueError(f"Unknown tool: {name}")


def setup_logging():
    """Configure logging to both file and console"""
    # Create logs directory
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("augustine-mcp")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(
        filename=os.path.join(log_dir, "augustine-server.log"),
        mode='a',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Also capture warnings
    logging.captureWarnings(True)
    
    return logger


# ----------------------------------------------------------------------
# Entry point - stdio transport for CLINE
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    import os
    
    logger = setup_logging()
    
    async def main():
        logger.info("Starting Augustine MCP server...")
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP server running with stdio transport")
                await app.run(
                    read_stream, 
                    write_stream, 
                    app.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"MCP server error: {e}")
            sys.exit(1)
    
    asyncio.run(main())
