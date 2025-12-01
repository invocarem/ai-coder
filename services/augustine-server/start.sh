#!/bin/bash
set -e

# Run from project root, not from the script's directory
cd /app
exec su -s /bin/bash apiuser -c "cd /app && python3 services/augustine-server/augustine_server.py"
