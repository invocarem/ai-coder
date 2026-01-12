# Word-to-MD MCP Server

## Overview

Word-to-MD provides a Model Context Protocol (MCP) server that converts various document formats to Markdown with three main tools:

- `convert_to_markdown` - Convert single document to Markdown
- `get_document_structure` - Extract structure and metadata from documents
- `batch_convert` - Convert multiple documents at once
- `supported_formats` - List supported document formats

## Supported Formats

- **DOCX** (Microsoft Word OpenXML) - Using mammoth
- **DOC** (Legacy Word) - Using pandoc
- **PDF** - Text extraction using PyMuPDF
- **TXT** - Direct copy to Markdown

## Prerequisites

- Python 3.9+
- Docker (optional)

## Running with Docker Compose

```bash
# Build and start all services including word-to-md
docker-compose up --build

# Or just word-to-md service
docker-compose up word-to-md-mcp --build
```
