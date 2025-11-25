#!/usr/bin/env python3
"""
Whitaker’s Words as an MCP server.
Usage:
    python whitaker_server.py           # stdio transport (default for CLINE)
    python whitaker_server.py --sse     # SSE transport (for web demos)
"""

import json
import logging
import os
import re
import subprocess
import argparse
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

# ------------------------------------------------------------------
# 1.  Existing Whitaker helpers (unchanged)
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("whitaker-mcp")

WHITAKER_BIN = "/opt/whitakers-words/bin/words"
WHITAKER_DIR = "/opt/whitakers-words"

def call_whitaker(word: str) -> str:
    """Call the native Words binary.  Same code you already had."""
    if not os.path.isfile(WHITAKER_BIN):
        return f"Error: Whitaker not found at {WHITAKER_BIN}"
    try:
        logger.debug("Calling Whitaker for %r", word)
        proc = subprocess.run(
            [WHITAKER_BIN, word],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WHITAKER_DIR,
        )
        return proc.stdout if proc.returncode == 0 else f"Error: {proc.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Analysis timed out"
    except Exception as exc:
        return f"Error: {exc}"

def parse_wh_output(output: str) -> Dict[str, Any]:
    """Very small heuristic parser.  Expand as you like."""
    if output.startswith("Error:"):
        return {"error": output}
    lines = [L.strip() for L in output.splitlines() if L.strip()]
    return {
        "raw_output": output,
        "lines": lines,
        "word_forms": [L for L in lines if re.match(r"^\w+,\s+\w+", L)],
        "definitions": [L for L in lines if L.startswith("(") or ";" in L],
    }

# ------------------------------------------------------------------
# 2.  MCP server setup
# ------------------------------------------------------------------
app = Server("whitaker-latin")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="analyze_latin",
            description="Morphologically analyse a single Latin word.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "Latin word to analyse"},
                },
                "required": ["word"],
            },
        ),
        Tool(
            name="analyze_latin_batch",
            description="Morphologically analyse many Latin words at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "words": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Latin words",
                    }
                },
                "required": ["words"],
            },
        ),
        Tool(
            name="analyze_latin_text",
            description="Tokenise a passage and analyse each unique word.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Latin text passage"},
                },
                "required": ["text"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Route MCP tool calls to Whitaker."""
    if name == "analyze_latin":
        word = arguments["word"].strip().lower()
        out = call_whitaker(word)
        parsed = parse_wh_output(out)
        return [TextContent(type="text", text=json.dumps(parsed, ensure_ascii=False, indent=2))]

    if name == "analyze_latin_batch":
        words = [w.strip().lower() for w in arguments["words"] if w.strip()]
        results = {w: parse_wh_output(call_whitaker(w)) for w in words}
        return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

    if name == "analyze_latin_text":
        text = arguments["text"]
        tokens = re.findall(r"\b[a-zA-Z]+\b", text)
        tokens = [t.lower() for t in tokens if len(t) > 1]
        unique = list(set(tokens))
        results = {w: parse_wh_output(call_whitaker(w)) for w in unique}
        summary = {
            "text": text,
            "total_tokens": len(tokens),
            "unique_tokens": len(unique),
            "analyses": results,
        }
        return [TextContent(type="text", text=json.dumps(summary, ensure_ascii=False, indent=2))]

    raise ValueError(f"Unknown tool: {name}")

# ------------------------------------------------------------------
# 3.  Entry-point – choose stdio (CLINE) or SSE
# ------------------------------------------------------------------
async def main_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

async def main_sse(host: str = "0.0.0.0", port: int = 9090):
    from mcp.server.sse import SseServerTransport
    from anyio import run as anyio_run
    sse = SseServerTransport(host, port)
    await sse.serve(app)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Whitaker MCP server")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport instead of stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9090)
    args = parser.parse_args()

    if args.sse:
        import asyncio
        asyncio.run(main_sse(args.host, args.port))
    else:
        import asyncio
        asyncio.run(main_stdio())