#!/bin/bash
set -e

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "Error: NGROK_AUTHTOKEN is not set. Please set this environment variable."
  exit 1
fi

echo "Waiting for backend service to be available..."

# Wait for backend service
until nc -z backend 5678 2>/dev/null; do
    echo "Waiting for backend service to become available..."
    sleep 2
done
echo "✓ Backend service is available"

# Generate ngrok configuration
if ! /app/generate_ngrok_config.sh; then
    echo "Failed to generate ngrok configuration"
    exit 1
fi

# Start ngrok
if [ -f "/etc/ngrok.yml" ]; then
    exec ngrok start --config=/etc/ngrok.yml --all
else
    echo "Error: ngrok configuration file not found"
    exit 1
fi