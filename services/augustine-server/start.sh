#!/bin/bash
set -e

# Run from project root, not from the script's directory
cd /app

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEBUG_LOG="/app/logs/debug_${TIMESTAMP}.log"
SERVER_LOG="/app/logs/server_${TIMESTAMP}.log"

mkdir -p /app/logs

export CASSANDRA_HOST=${CASSANDRA_HOST:-cassandra-server}


echo "=== Startup Debug ===" > "$DEBUG_LOG"
echo "Time: $(date)" >> "$DEBUG_LOG"
echo "Python: $(which python3)" >> "$DEBUG_LOG"
echo "PWD: $(pwd)" >> "$DEBUG_LOG"
echo "Files:" >> "$DEBUG_LOG"
ls -la /app/ >> "$DEBUG_LOG"


echo "Starting Augustine MCP server..."
echo "Debug log: $DEBUG_LOG"
echo "Server log: $SERVER_LOG"

# Pipe stderr to debug log, stdout to server log
exec python3 -u /app/augustine_server.py 2>> "$DEBUG_LOG" 1>> "$SERVER_LOG"



echo "Augustine MCP server stopped." >> "$DEBUG_LOG"
