FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyMuPDF for PDF support (optional)
RUN pip install --no-cache-dir pymupdf

# Copy MCP server
COPY word_to_md_server.py .

# Create directory for documents
RUN mkdir -p /documents

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command
ENTRYPOINT ["python", "word_to_md_server.py"]