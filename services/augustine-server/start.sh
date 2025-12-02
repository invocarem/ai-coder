#!/bin/bash
set -e

# Run from project root, not from the script's directory
cd /app
#exec su -s /bin/bash apiuser -c "cd /app && python3 services/augustine-server/augustine_server.py"

export CASSANDRA_HOST=${CASSANDRA_HOST:-cassandra-server}
# Add logging to capture any startup errors
echo "Starting Augustine MCP server..."
python3 services/augustine-server/augustine_server.py 2>&1 | tee /app/augustine_server.log
echo "Augustine MCP server stopped."