#!/bin/bash
set -e

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "Error: NGROK_AUTHTOKEN is not set. Please set this environment variable."
  exit 1
fi

# Extract domain from WEBHOOK_BASE_URL
STATIC_DOMAIN=$(echo $WEBHOOK_BASE_URL | sed -e 's|^https://||' -e 's|/$||')

# Create base ngrok.yml configuration
cat > /etc/ngrok.yml << EOF
version: 2
authtoken: ${NGROK_AUTHTOKEN}
web_addr: 0.0.0.0:4040
region: ap
log: stdout
log_level: info
tunnels:
  backend:
    addr: backend:5678
    proto: http
    domain: ${STATIC_DOMAIN}
    inspect: false
EOF

echo "Successfully generated ngrok.yml configuration"