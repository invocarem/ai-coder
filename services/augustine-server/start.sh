#!/bin/bash
set -e

# Start Cassandra in the background using the cassandra binary
cassandra -f &

# Wait for Cassandra to be ready
echo "Waiting for Cassandra to become available on port 9042..."
until cqlsh -e "DESCRIBE KEYSPACES" >/dev/null 2>&1; do
  sleep 2
done
echo "Cassandra is up and running."

# Switch to non‑root user and start the FastAPI server
exec su - apiuser -c "uvicorn augustine_server:app --host 0.0.0.0 --port 8002"
