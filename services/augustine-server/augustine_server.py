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

# Import the existing processor and AI provider utilities
from app.processors.psalm_rag_processor import PsalmRAGProcessor
from app.utils.ai_provider import AIProviderFactory
from app.config import load_config

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
    processor = PsalmRAGProcessor(ai_provider)
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
            description="Process a psalm query using the Augustine RAG processor.",
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
    if name == "analyze_psalm":
        try:
            result = processor.process(
                arguments["pattern_data"],
                arguments["model"],
                arguments.get("stream", False),
                arguments.get("original_data", {}),
            )
            
            # Handle streaming response
            if arguments.get("stream", False) and hasattr(result, '__iter__') and not isinstance(result, (str, dict, list)):
                # For streaming responses, we need to handle the generator differently
                # Since MCP expects a list of TextContent, we'll collect the entire stream
                # This is a limitation of the current MCP protocol for streaming
                # In production, you might want to handle streaming differently
                full_response = ""
                for chunk in result:
                    if isinstance(chunk, str):
                        full_response += chunk
                # Extract just the JSON content from the stream
                # This is a simplified approach - in practice you'd want to parse the SSE stream
                return [TextContent(type="text", text=json.dumps({"content": full_response}, ensure_ascii=False))]
            
            # Handle regular response (dictionary with possible status code)
            if isinstance(result, tuple) and len(result) == 2:
                payload, status_code = result
                # For MCP, we'll return the payload regardless of status code
                # The client should handle HTTP status codes appropriately
                return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]
            else:
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
                
        except Exception as e:
            logger.error(f"Error in analyze_psalm: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    if name == "get_psalm_health":
        try:
            health = processor.health_check()
            return [TextContent(type="text", text=json.dumps(health, ensure_ascii=False))]
        except Exception as e:
            logger.error(f"Error in get_psalm_health: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    raise ValueError(f"Unknown tool: {name}")

# ----------------------------------------------------------------------
# Entry point - stdio transport for CLINE
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
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
