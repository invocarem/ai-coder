FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for the MCP server
RUN useradd -ms /bin/bash apiuser

WORKDIR /app

# Copy the entire project into the image
COPY . /app

# Install Python dependencies (mcp only)
RUN pip3 install --no-cache-dir -r requirements.txt

# Ensure the start script is executable
RUN chmod +x /app/services/augustine-server/start.sh

# Launch the MCP server via stdio
ENTRYPOINT ["/app/services/augustine-server/start.sh"]
