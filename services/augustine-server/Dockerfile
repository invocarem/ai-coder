FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user for the MCP server
RUN useradd -ms /bin/bash apiuser

# Create logs directory and assign ownership to apiuser
RUN mkdir -p /app/logs && chown apiuser:apiuser /app/logs

# Copy the entire project into the image
COPY . /app

# Install Python dependencies specifically for Augustine server
RUN pip3 install --no-cache-dir -r services/augustine-server/requirements.txt

# Ensure the start script has proper line endings and is executable
RUN sed -i 's/\r$//' /app/services/augustine-server/start.sh && \
    chmod +x /app/services/augustine-server/start.sh

# Launch the MCP server via stdio
# Use bash explicitly to handle line endings and ensure proper execution
ENTRYPOINT ["/bin/bash", "/app/services/augustine-server/start.sh"]
