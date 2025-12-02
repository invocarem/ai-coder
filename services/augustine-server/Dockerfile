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

# Copy entire project into /app
COPY . /app

# Move Augustine server files to /app root
RUN mv /app/services/augustine-server/augustine_server.py /app/augustine_server.py && \
    mv /app/services/augustine-server/start.sh /app/start.sh && \
    mv /app/services/augustine-server/requirements.txt /app/requirements.txt

# Remove the services directory to keep image clean
RUN rm -rf /app/services

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Ensure the start script has proper line endings and is executable
RUN sed -i 's/\r$//' /app/start.sh && \
    chmod +x /app/start.sh

# Launch the MCP server via stdio
ENTRYPOINT ["/bin/bash", "/app/start.sh"]
