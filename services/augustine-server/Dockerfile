FROM cassandra:4.1

# Install Python 3 and pip (Cassandra image is Debian‑based)
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Create a non‑root user for the FastAPI server
RUN useradd -ms /bin/bash apiuser

WORKDIR /app

# Copy the entire project into the image
COPY . /app

# Install Python dependencies (including FastAPI, cassandra-driver, etc.)
RUN pip3 install --no-cache-dir -r services/augustine-server/requirements.txt

# Ensure the start script is executable
RUN chmod +x /app/services/augustine-server/start.sh

# Expose ports: 9042 for Cassandra, 8002 for the API
EXPOSE 9042 8002

# Launch Cassandra and then the FastAPI server
ENTRYPOINT ["/app/services/augustine-server/start.sh"]
