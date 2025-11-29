#!/bin/bash
set -e

# Run from project root, not from the script's directory
cd /app
exec su -s /bin/bash apiuser -c "python3 /app/services/augustine-server/augustine_server.py"
