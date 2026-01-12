#!/usr/bin/env python3
"""
Word to Markdown MCP Server - Base64 version with pandoc
Better table support than mammoth
"""
import json
import base64
import tempfile
import os
import re
import subprocess
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("word-to-md")

def convert_docx_bytes_to_markdown(docx_bytes: bytes) -> dict:
    """Convert DOCX bytes to markdown using pandoc - BETTER TABLE SUPPORT."""
    import mammoth
    
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name
    
    try:
        # Try pandoc first (better table support)
        try:
            # Use pandoc to convert DOCX to Markdown
            result = subprocess.run(
                ['pandoc', '-f', 'docx', '-t', 'markdown', tmp_path, '--wrap=none'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                markdown = result.stdout
                
                # Clean up markdown
                # 1. Remove images (data URIs)
                markdown = re.sub(r'!\[.*?\]\(data:[^)]+\)', '', markdown)
                markdown = re.sub(r'<img[^>]+src="data:[^"]+"[^>]*>', '', markdown)
                
                # 2. Remove headers/footers
                markdown = re.sub(r'^.*507\\s*-\\s*SPEC.*$', '', markdown, flags=re.MULTILINE)
                markdown = re.sub(r'^.*Revision History.*$', '', markdown, flags=re.MULTILINE)
                markdown = re.sub(r'^Page\s+\d+\s+of\s+\d+$', '', markdown, flags=re.MULTILINE | re.IGNORECASE)
                markdown = re.sub(r'^.*\\[.*\\].*$', '', markdown, flags=re.MULTILINE)
                
                # 3. Clean up whitespace
                markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
                markdown = markdown.strip()
                
                return {
                    "markdown": markdown,
                    "original_size": len(docx_bytes),
                    "final_size": len(markdown),
                    "image_count": len(re.findall(r'data:', markdown)),
                    "messages": ["Converted with pandoc"],
                    "converter": "pandoc"
                }
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            # Fall back to mammoth if pandoc fails or isn't installed
            print(f"Pandoc failed, falling back to mammoth: {e}", file=sys.stderr)
        
        # Fallback: Use mammoth
        with open(tmp_path, "rb") as f:
            result = mammoth.convert_to_markdown(f)
            markdown = result.value
            
            # Apply the same cleaning as before
            markdown = re.sub(r'!\[.*?\]\(data:[^)]+\)', '', markdown)
            markdown = re.sub(r'<img[^>]+src="data:[^"]+"[^>]*>', '', markdown)
            
            markdown = re.sub(r'^.*507\\s*-\\s*SPEC.*$', '', markdown, flags=re.MULTILINE)
            markdown = re.sub(r'^.*Revision History.*$', '', markdown, flags=re.MULTILINE)
            markdown = re.sub(r'^Page\s+\d+\s+of\s+\d+$', '', markdown, flags=re.MULTILINE | re.IGNORECASE)
            markdown = re.sub(r'^.*\\[.*\\].*$', '', markdown, flags=re.MULTILINE)
            
            # Try to handle tables better with mammoth output
            # Mammoth sometimes outputs tables as HTML, sometimes as markdown
            # Let's try to convert any remaining HTML tables
            def html_table_to_md(match):
                table_html = match.group(0)
                # Simple conversion for HTML tables
                rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
                if not rows:
                    return ""
                
                md_rows = []
                for i, row in enumerate(rows):
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if not cells:
                        cells = re.findall(r'<th[^>]*>(.*?)</th>', row, re.DOTALL)
                    
                    clean_cells = []
                    for cell in cells:
                        clean = re.sub(r'<[^>]+>', '', cell)
                        clean = re.sub(r'\s+', ' ', clean).strip()
                        clean_cells.append(clean)
                    
                    if clean_cells:
                        md_rows.append("| " + " | ".join(clean_cells) + " |")
                        if i == 0:
                            md_rows.append("| " + " | ".join(["---"] * len(clean_cells)) + " |")
                
                return "\n" + "\n".join(md_rows) + "\n"
            
            markdown = re.sub(r'<table[^>]*>.*?</table>', html_table_to_md, markdown, flags=re.DOTALL | re.IGNORECASE)
            
            markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
            markdown = markdown.strip()
            
            return {
                "markdown": markdown,
                "original_size": len(docx_bytes),
                "final_size": len(markdown),
                "image_count": len(re.findall(r'data:', result.value)),
                "messages": [str(m) for m in result.messages] + ["Converted with mammoth (fallback)"],
                "converter": "mammoth"
            }
    finally:
        os.unlink(tmp_path)



def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract text from PDF bytes."""
    try:
        import fitz  # PyMuPDF
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        
        try:
            doc = fitz.open(tmp_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_parts.append(page.get_text())
            
            return {
                "text": "\n\n".join(text_parts),
                "pages": len(doc)
            }
        finally:
            os.unlink(tmp_path)
    except ImportError:
        return {
            "error": "PyMuPDF not installed"
        }
    except Exception as e:
        return {
            "error": f"PDF extraction failed: {str(e)}"
        }

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="convert_docx_to_markdown",
            description="Convert DOCX file (base64) to Markdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_base64": {
                        "type": "string",
                        "description": "DOCX file content as base64 string"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename for reference"
                    },
                    "file_size": {
                        "type": "number",
                        "description": "File size in bytes"
                    }
                },
                "required": ["content_base64"]
            },
        ),
        Tool(
            name="extract_pdf_text",
            description="Extract text from PDF file (base64)",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_base64": {
                        "type": "string",
                        "description": "PDF file content as base64 string"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename for reference"
                    }
                },
                "required": ["content_base64"]
            },
        ),
        Tool(
            name="convert_text_to_markdown",
            description="Convert plain text to Markdown format",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_base64": {
                        "type": "string",
                        "description": "Text content as base64 string"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename for reference"
                    }
                },
                "required": ["content_base64"]
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        # Decode base64 (common for all tools)
        content_bytes = base64.b64decode(arguments["content_base64"])
        filename = arguments.get("filename", "document")
        
        if name == "convert_docx_to_markdown":
            result = convert_docx_bytes_to_markdown(content_bytes)
            
            if "error" in result:
                response = {
                    "success": False,
                    "error": result["error"],
                    "filename": filename
                }
            else:
                response = {
                    "success": True,
                    "filename": filename,
                    "markdown": result["markdown"],
                    "markdown_length": len(result["markdown"]),
                    "messages": result.get("messages", [])
                }
                
        elif name == "extract_pdf_text":
            result = extract_pdf_text(content_bytes)
            
            if "error" in result:
                response = {
                    "success": False,
                    "error": result["error"],
                    "filename": filename
                }
            else:
                response = {
                    "success": True,
                    "filename": filename,
                    "text": result["text"],
                    "text_length": len(result["text"]),
                    "pages": result.get("pages", 1)
                }
                
        elif name == "convert_text_to_markdown":
            # Just decode the text
            text = content_bytes.decode('utf-8')
            response = {
                "success": True,
                "filename": filename,
                "markdown": text,
                "markdown_length": len(text)
            }
            
        else:
            response = {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
            
    except Exception as e:
        response = {
            "success": False,
            "error": str(e),
            "filename": arguments.get("filename", "unknown")
        }
    
    return [TextContent(type="text", text=json.dumps(response, indent=2))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())