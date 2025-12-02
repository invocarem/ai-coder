#!/bin/bash
set -e

# Run from project root, not from the script's directory
cd /app

export CASSANDRA_HOST=${CASSANDRA_HOST:-cassandra-server}
# Add logging to capture any startup errors
echo "Starting Augustine MCP server..."
python3 /app/augustine_server.py 2>&1 | tee /app/augustine_server.log
echo "Augustine MCP server stopped."
