#!/bin/bash

#############################################
# Automata Serial Number & Cloudflare Tunnel Setup
# Standalone script for RPi4 systems
# Version: 1.0.0
#############################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
USER="Automata"
APP_DIR="/home/${USER}"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Automata Tunnel Setup Script${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Please run as root (use sudo)${NC}"
   exit 1
fi

# Decode API key (base64 encoded for obfuscation)
# Original: yYYuY2_JrPG-Cyepidg582kYWfhAdWPu-ertr1fM
ENCODED_API="eVlZdVkyX0pyUEctQ3llcGlkZzU4MmtZV2ZoQWRXUHUtZXJ0cjFmTQ=="
CLOUDFLARE_API=$(echo "$ENCODED_API" | base64 -d)

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}Installing Cloudflare tunnel...${NC}"
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        # 64-bit ARM
        CLOUDFLARED_PKG="cloudflared-linux-arm64.deb"
    elif [ "$ARCH" = "armv7l" ] || [ "$ARCH" = "armhf" ]; then
        # 32-bit ARM (Raspberry Pi)
        CLOUDFLARED_PKG="cloudflared-linux-armhf.deb"
    else
        # Fallback to 32-bit ARM
        CLOUDFLARED_PKG="cloudflared-linux-armhf.deb"
    fi
    
    echo -e "${YELLOW}Detected architecture: ${ARCH}${NC}"
    echo -e "${YELLOW}Downloading ${CLOUDFLARED_PKG}...${NC}"
    
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/${CLOUDFLARED_PKG}
    dpkg -i ${CLOUDFLARED_PKG}
    rm ${CLOUDFLARED_PKG}
fi

# Generate new controller serial
echo -e "${YELLOW}Generating controller serial number...${NC}"
RANDOM_SUFFIX=$(openssl rand -hex 3 | tr '[:lower:]' '[:upper:]')
CONTROLLER_SERIAL="NexusController-anc-${RANDOM_SUFFIX}"
# Convert serial to lowercase for tunnel name
TUNNEL_NAME="${CONTROLLER_SERIAL,,}"
# Domain should keep the hyphens
TUNNEL_DOMAIN="${TUNNEL_NAME}.automatacontrols.com"

echo -e "${GREEN}Generated controller serial: ${CONTROLLER_SERIAL}${NC}"
echo -e "${GREEN}Tunnel domain will be: ${TUNNEL_DOMAIN}${NC}"

# Save configuration
CONFIG_FILE="${APP_DIR}/controller-config.txt"
echo "# Automata Controller Configuration" > ${CONFIG_FILE}
echo "# Generated on $(date '+%Y-%m-%d %H:%M:%S')" >> ${CONFIG_FILE}
echo "" >> ${CONFIG_FILE}
echo "CONTROLLER_SERIAL=${CONTROLLER_SERIAL}" >> ${CONFIG_FILE}
echo "TUNNEL_NAME=${TUNNEL_NAME}" >> ${CONFIG_FILE}
echo "TUNNEL_DOMAIN=${TUNNEL_DOMAIN}" >> ${CONFIG_FILE}

# Create cloudflared directory
mkdir -p /home/${USER}/.cloudflared

# Get Cloudflare account ID
echo -e "${YELLOW}Getting Cloudflare account ID...${NC}"
ACCOUNT_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts" \
    -H "Authorization: Bearer ${CLOUDFLARE_API}" \
    -H "Content-Type: application/json" | \
    grep -oP '"id":"\K[^"]+' | head -1)

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${YELLOW}Could not get account ID. Using default...${NC}"
    ACCOUNT_ID="436dc4767ed5312866132f09bfea284c"
fi

echo -e "${GREEN}Account ID: ${ACCOUNT_ID}${NC}"

# Check for existing tunnel and delete if exists
echo -e "${YELLOW}Checking for existing tunnel: ${TUNNEL_NAME}${NC}"
EXISTING_TUNNELS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels?name=${TUNNEL_NAME}" \
    -H "Authorization: Bearer ${CLOUDFLARE_API}" \
    -H "Content-Type: application/json")

EXISTING_ID=$(echo "$EXISTING_TUNNELS" | grep -oP '"id":"\K[^"]+' | head -1)

if [ ! -z "$EXISTING_ID" ]; then
    echo -e "${YELLOW}Found existing tunnel with ID: ${EXISTING_ID}${NC}"
    echo -e "${YELLOW}Deleting existing tunnel...${NC}"
    
    curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels/${EXISTING_ID}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API}" \
        -H "Content-Type: application/json"
    
    echo -e "${GREEN}✓ Existing tunnel deleted${NC}"
    sleep 2
fi

# Generate tunnel secret based on controller serial
echo -e "${YELLOW}Creating new tunnel: ${TUNNEL_NAME}${NC}"
RAW_SECRET="${CONTROLLER_SERIAL}-Invertedskynet2$"
TUNNEL_SECRET=$(echo -n "${RAW_SECRET}" | base64 | tr -d '\n')

# Create tunnel via API
TUNNEL_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels" \
    -H "Authorization: Bearer ${CLOUDFLARE_API}" \
    -H "Content-Type: application/json" \
    --data "{\"name\":\"${TUNNEL_NAME}\",\"tunnel_secret\":\"${TUNNEL_SECRET}\"}")

TUNNEL_ID=$(echo "$TUNNEL_RESPONSE" | grep -oP '"id":"\K[^"]+' | head -1)

if [ -z "$TUNNEL_ID" ]; then
    echo -e "${RED}Failed to create tunnel!${NC}"
    echo -e "${RED}Response: ${TUNNEL_RESPONSE}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tunnel created with ID: ${TUNNEL_ID}${NC}"

# Add tunnel ID to config file
echo "TUNNEL_ID=${TUNNEL_ID}" >> ${CONFIG_FILE}
echo "TUNNEL_SECRET=${TUNNEL_SECRET}" >> ${CONFIG_FILE}

# Create DNS record
echo -e "${YELLOW}Creating DNS record for ${TUNNEL_DOMAIN}...${NC}"

# Get zone ID for automatacontrols.com
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=automatacontrols.com" \
    -H "Authorization: Bearer ${CLOUDFLARE_API}" \
    -H "Content-Type: application/json" | \
    grep -oP '"id":"\K[^"]+' | head -1)

if [ ! -z "$ZONE_ID" ]; then
    # Delete any existing DNS record for this subdomain
    EXISTING_DNS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?name=${TUNNEL_DOMAIN}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API}" \
        -H "Content-Type: application/json")
    
    EXISTING_DNS_ID=$(echo "$EXISTING_DNS" | grep -oP '"id":"\K[^"]+' | head -1)
    
    if [ ! -z "$EXISTING_DNS_ID" ]; then
        echo -e "${YELLOW}Removing existing DNS record...${NC}"
        curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${EXISTING_DNS_ID}" \
            -H "Authorization: Bearer ${CLOUDFLARE_API}" \
            -H "Content-Type: application/json"
    fi
    
    # Create CNAME record
    DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
        -H "Authorization: Bearer ${CLOUDFLARE_API}" \
        -H "Content-Type: application/json" \
        --data "{\"type\":\"CNAME\",\"name\":\"${TUNNEL_DOMAIN%%.*}\",\"content\":\"${TUNNEL_ID}.cfargotunnel.com\",\"ttl\":1,\"proxied\":true}")
    
    echo -e "${GREEN}✓ DNS record created${NC}"
else
    echo -e "${YELLOW}Warning: Could not create DNS record (zone ID not found)${NC}"
fi

# Create credentials file
echo -e "${YELLOW}Creating tunnel credentials...${NC}"
cat > /home/${USER}/.cloudflared/${TUNNEL_ID}.json << EOF
{
  "AccountTag": "${ACCOUNT_ID}",
  "TunnelSecret": "${TUNNEL_SECRET}",
  "TunnelID": "${TUNNEL_ID}"
}
EOF

# Create tunnel config - prompt for port
echo ""
echo -e "${YELLOW}What port is your application running on?${NC}"
echo -e "${YELLOW}Common ports:${NC}"
echo -e "${YELLOW}  1420 - Automata Nexus${NC}"
echo -e "${YELLOW}  3000 - Node.js default${NC}"
echo -e "${YELLOW}  3001 - Neural Nexus${NC}"
echo -e "${YELLOW}  8080 - Alternative HTTP${NC}"
read -p "Enter port number [1420]: " APP_PORT
APP_PORT=${APP_PORT:-1420}

cat > /home/${USER}/.cloudflared/config.yml << EOF
url: http://localhost:${APP_PORT}
tunnel: ${TUNNEL_ID}
credentials-file: /home/${USER}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: ${TUNNEL_DOMAIN}
    service: http://localhost:${APP_PORT}
  - service: http_status:404
EOF

# Set permissions
chown -R ${USER}:${USER} /home/${USER}/.cloudflared
chmod 600 /home/${USER}/.cloudflared/*.json
chmod 644 /home/${USER}/.cloudflared/config.yml
chown ${USER}:${USER} ${CONFIG_FILE}

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/cloudflared.service << EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=notify
User=${USER}
Group=${USER}
ExecStart=/usr/local/bin/cloudflared tunnel run
Restart=on-failure
RestartSec=5
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Start tunnel service
systemctl daemon-reload
systemctl enable cloudflared
systemctl restart cloudflared

# Wait for tunnel to start
sleep 3

# Check tunnel status
if systemctl is-active --quiet cloudflared; then
    echo -e "${GREEN}✓ Cloudflare tunnel is running${NC}"
else
    echo -e "${RED}✗ Tunnel failed to start. Check: journalctl -u cloudflared${NC}"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${GREEN}Controller Serial: ${CONTROLLER_SERIAL}${NC}"
echo -e "${GREEN}Tunnel ID: ${TUNNEL_ID}${NC}"
echo -e "${GREEN}Tunnel URL: https://${TUNNEL_DOMAIN}${NC}"
echo ""
echo -e "${YELLOW}Configuration saved to: ${CONFIG_FILE}${NC}"
echo -e "${YELLOW}Tunnel config: /home/${USER}/.cloudflared/config.yml${NC}"
echo ""
echo -e "Useful commands:"
echo -e "  Check status: ${YELLOW}systemctl status cloudflared${NC}"
echo -e "  View logs: ${YELLOW}journalctl -u cloudflared -f${NC}"
echo -e "  Restart tunnel: ${YELLOW}systemctl restart cloudflared${NC}"
echo ""

# Clear sensitive variable
unset CLOUDFLARE_API