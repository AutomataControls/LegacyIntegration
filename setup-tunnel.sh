#!/bin/bash

#############################################
# Automata Legacy Integration Portal Setup
# Complete installer with Node.js portal, Nginx, and Cloudflare tunnel
# Version: 2.0.0
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
PORTAL_DIR="${APP_DIR}/remote-access-portal"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Automata Legacy Portal Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Please run as root (use sudo)${NC}"
   exit 1
fi

# Clean up any failed installations
echo -e "${YELLOW}Cleaning up any previous installations...${NC}"

# Stop and disable services if they exist
systemctl stop cloudflared 2>/dev/null || true
systemctl stop automata-portal 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true
systemctl disable cloudflared 2>/dev/null || true
systemctl disable automata-portal 2>/dev/null || true

# Remove old service files
rm -f /etc/systemd/system/cloudflared.service
rm -f /etc/systemd/system/automata-portal.service

# Remove old cloudflared configurations
rm -rf /home/${USER}/.cloudflared 2>/dev/null || true

# Remove old config files
rm -f /home/${USER}/controller-config.txt 2>/dev/null || true
rm -f /home/${USER}/tunnel-config.txt 2>/dev/null || true

# Remove partially downloaded packages
rm -f cloudflared*.deb 2>/dev/null || true

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Install system dependencies
echo -e "${BLUE}Installing system dependencies...${NC}"
apt-get update
apt-get install -y curl wget git openssl python3 python3-pip

# Install Node.js if needed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    apt-get install -y nodejs
    echo -e "${GREEN}✓ Node.js installed${NC}"
else
    echo -e "${GREEN}✓ Node.js already installed ($(node -v))${NC}"
fi

# Install Nginx if needed
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Installing Nginx...${NC}"
    apt-get install -y nginx
    echo -e "${GREEN}✓ Nginx installed${NC}"
else
    echo -e "${GREEN}✓ Nginx already installed${NC}"
fi

# Install Node-RED if needed
if ! command -v node-red &> /dev/null; then
    echo -e "${YELLOW}Installing Node-RED...${NC}"
    npm install -g --unsafe-perm node-red
    
    # Create Node-RED systemd service
    cat > /etc/systemd/system/nodered.service << EOF
[Unit]
Description=Node-RED
After=syslog.target network.target

[Service]
ExecStart=/usr/bin/node-red --max-old-space-size=256
Restart=on-failure
RestartSec=5s
User=${USER}
WorkingDirectory=/home/${USER}
Environment="NODE_OPTIONS=--max-old-space-size=256"

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable nodered
    systemctl start nodered
    echo -e "${GREEN}✓ Node-RED installed and started${NC}"
else
    echo -e "${GREEN}✓ Node-RED already installed${NC}"
    systemctl restart nodered 2>/dev/null || true
fi

# Create portal directory
echo -e "${YELLOW}Setting up portal directory...${NC}"
mkdir -p ${PORTAL_DIR}
cd ${PORTAL_DIR}

# Create package.json
cat > package.json << 'EOF'
{
  "name": "automata-portal",
  "version": "2.0.0",
  "description": "Automata Remote Access Portal",
  "main": "terminal-server.js",
  "scripts": {
    "start": "node terminal-server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "http-proxy-middleware": "^2.0.6",
    "socket.io": "^4.6.1",
    "xterm": "^5.3.0",
    "xterm-addon-fit": "^0.8.0",
    "node-pty": "^1.0.0"
  }
}
EOF

# Install Node.js packages
echo -e "${YELLOW}Installing Node.js packages...${NC}"
npm install

# Create the terminal server
echo -e "${YELLOW}Creating terminal server...${NC}"
cat > terminal-server.js << 'EOF'
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const app = express();
const server = require('http').createServer(app);
const io = require('socket.io')(server);
const pty = require('node-pty');

// Serve static files
app.use('/xterm', express.static(path.join(__dirname, 'node_modules/xterm')));
app.use('/xterm-addon-fit', express.static(path.join(__dirname, 'node_modules/xterm-addon-fit')));

// Store terminal sessions
const terminals = {};

// System info endpoint
app.get('/api/system-info', async (req, res) => {
  const { exec } = require('child_process');
  const util = require('util');
  const execPromise = util.promisify(exec);
  
  try {
    const hostname = require('os').hostname();
    const cpuTemp = await execPromise('vcgencmd measure_temp').then(r => r.stdout.trim().split('=')[1]).catch(() => 'N/A');
    const memInfo = await execPromise('free -m').then(r => {
      const lines = r.stdout.split('\n');
      const mem = lines[1].split(/\s+/);
      return {
        total: parseInt(mem[1]),
        used: parseInt(mem[2]),
        percent: Math.round((parseInt(mem[2]) / parseInt(mem[1])) * 100)
      };
    });
    
    // Read controller serial from config if exists
    let serial = 'Not Configured';
    const fs = require('fs');
    const configPath = '/home/Automata/tunnel-config.txt';
    if (fs.existsSync(configPath)) {
      const config = fs.readFileSync(configPath, 'utf8');
      const match = config.match(/CONTROLLER_SERIAL=(.+)/);
      if (match) serial = match[1];
    }
    
    res.json({
      hostname,
      cpu_temp: cpuTemp,
      mem_total: memInfo.total,
      mem_used: memInfo.used,
      mem_percent: memInfo.percent,
      serial: serial
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Main page
app.get('/', (req, res) => {
  res.send(\`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Automata Remote Access Portal</title>
      <link rel="stylesheet" href="/xterm/css/xterm.css" />
      <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background: linear-gradient(to right, #374151, #14b8a6); color: white; padding: 20px; }
        .nav { background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 10px; }
        .nav button { margin: 0 5px; padding: 10px 20px; border: none; background: #f3f4f6; cursor: pointer; border-radius: 4px; }
        .nav button.active { background: #14b8a6; color: white; }
        .content { padding: 20px; height: calc(100vh - 200px); }
        iframe { width: 100%; height: 100%; border: none; }
        #terminal-container { width: 100%; height: 100%; background: black; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>Automata Remote Access Portal</h1>
        <p id="controller-serial">Loading...</p>
      </div>
      <div class="nav">
        <button onclick="showDashboard()" id="btn-dashboard" class="active">Dashboard</button>
        <button onclick="showNodeRed()" id="btn-nodered">Node-RED</button>
        <button onclick="showTerminal()" id="btn-terminal">Terminal</button>
        <button onclick="showNeuralBMS()" id="btn-neuralbms">Neural BMS</button>
      </div>
      <div class="content" id="content">
        <h2>System Dashboard</h2>
        <div id="system-info">Loading...</div>
      </div>
      
      <script src="/socket.io/socket.io.js"></script>
      <script src="/xterm/lib/xterm.js"></script>
      <script src="/xterm-addon-fit/lib/xterm-addon-fit.js"></script>
      <script>
        let socket = null;
        let term = null;
        let fitAddon = null;
        
        function clearActive() {
          document.querySelectorAll('.nav button').forEach(btn => btn.classList.remove('active'));
        }
        
        function cleanupTerminal() {
          if (term) {
            term.dispose();
            term = null;
          }
          if (socket) {
            socket.disconnect();
            socket = null;
          }
        }
        
        function showDashboard() {
          clearActive();
          cleanupTerminal();
          document.getElementById('btn-dashboard').classList.add('active');
          document.getElementById('content').innerHTML = '<h2>System Dashboard</h2><div id="system-info">Loading...</div>';
          updateSystemInfo();
        }
        
        function showNodeRed() {
          clearActive();
          cleanupTerminal();
          document.getElementById('btn-nodered').classList.add('active');
          document.getElementById('content').innerHTML = '<iframe src="/node-red/"></iframe>';
        }
        
        function showTerminal() {
          clearActive();
          cleanupTerminal();
          document.getElementById('btn-terminal').classList.add('active');
          document.getElementById('content').innerHTML = '<div id="terminal-container"></div>';
          
          // Initialize xterm.js
          term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
              background: '#000000',
              foreground: '#ffffff'
            }
          });
          
          fitAddon = new FitAddon.FitAddon();
          term.loadAddon(fitAddon);
          term.open(document.getElementById('terminal-container'));
          fitAddon.fit();
          
          // Connect to socket
          socket = io();
          
          socket.on('connect', () => {
            socket.emit('terminal-init', { cols: term.cols, rows: term.rows });
          });
          
          socket.on('terminal-output', (data) => {
            term.write(data);
          });
          
          term.onData((data) => {
            socket.emit('terminal-input', data);
          });
          
          term.onResize((size) => {
            socket.emit('terminal-resize', { cols: size.cols, rows: size.rows });
          });
          
          window.addEventListener('resize', () => {
            if (fitAddon) fitAddon.fit();
          });
        }
        
        function showNeuralBMS() {
          clearActive();
          cleanupTerminal();
          document.getElementById('btn-neuralbms').classList.add('active');
          document.getElementById('content').innerHTML = '<iframe src="https://neuralbms.automatacontrols.com/login"></iframe>';
        }
        
        async function updateSystemInfo() {
          try {
            const response = await fetch('/api/system-info');
            const data = await response.json();
            const infoDiv = document.getElementById('system-info');
            const serialDiv = document.getElementById('controller-serial');
            
            if (serialDiv) {
              serialDiv.textContent = 'Controller: ' + data.serial;
            }
            
            if (infoDiv) {
              infoDiv.innerHTML = \\\`
                <p>Hostname: \\\${data.hostname}</p>
                <p>CPU Temperature: \\\${data.cpu_temp}</p>
                <p>Memory: \\\${data.mem_used}MB / \\\${data.mem_total}MB (\\\${data.mem_percent}%)</p>
              \\\`;
            }
          } catch (error) {
            console.error('Failed to fetch system info:', error);
          }
        }
        
        // Update system info on load and every 5 seconds
        updateSystemInfo();
        setInterval(updateSystemInfo, 5000);
      </script>
    </body>
    </html>
  \`);
});

// Socket.IO terminal handling
io.on('connection', (socket) => {
  console.log('Terminal connection established');
  
  socket.on('terminal-init', (data) => {
    const term = pty.spawn('bash', [], {
      name: 'xterm-color',
      cols: data.cols || 80,
      rows: data.rows || 24,
      cwd: process.env.HOME,
      env: process.env
    });
    
    terminals[socket.id] = term;
    
    term.onData((data) => {
      socket.emit('terminal-output', data);
    });
    
    socket.emit('terminal-output', \`Welcome to Automata Controller Terminal\\r\\n\`);
  });
  
  socket.on('terminal-input', (data) => {
    if (terminals[socket.id]) {
      terminals[socket.id].write(data);
    }
  });
  
  socket.on('terminal-resize', (data) => {
    if (terminals[socket.id]) {
      terminals[socket.id].resize(data.cols, data.rows);
    }
  });
  
  socket.on('disconnect', () => {
    if (terminals[socket.id]) {
      terminals[socket.id].kill();
      delete terminals[socket.id];
    }
  });
});

// Start server
const PORT = 8001;
server.listen(PORT, '0.0.0.0', () => {
  console.log(\`Portal server running on port \${PORT}\`);
});
EOF

# Create SSL certificates
echo -e "${YELLOW}Creating SSL certificates...${NC}"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=US/ST=State/L=City/O=Automata/CN=localhost" 2>/dev/null

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/automata-portal << 'EOF'
upstream portal_backend {
    server 127.0.0.1:8001;
}

upstream nodered_backend {
    server 127.0.0.1:1880;
}

# HTTP server - redirect to HTTPS
server {
    listen 8000;
    listen [::]:8000;
    server_name _;
    return 301 https://$host:8443$request_uri;
}

# HTTPS server
server {
    listen 8443 ssl http2;
    listen [::]:8443 ssl http2;
    server_name _;
    
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Main portal
    location / {
        proxy_pass http://portal_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Node-RED proxy with WebSocket support
    location /node-red/ {
        proxy_pass http://nodered_backend/;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Standard headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Node-RED specific
        proxy_set_header X-Scheme $scheme;
        proxy_buffering off;
        
        # Timeouts for WebSocket
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Node-RED WebSocket comms endpoint
    location /node-red/comms {
        proxy_pass http://nodered_backend/comms;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific settings
        proxy_buffering off;
        proxy_connect_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_read_timeout 3600s;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://portal_backend/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Socket.IO for terminal
    location /socket.io/ {
        proxy_pass http://portal_backend/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/automata-portal /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Create systemd service for portal
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/automata-portal.service << EOF
[Unit]
Description=Automata Portal Server
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${PORTAL_DIR}
ExecStart=/usr/bin/node terminal-server.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Decode API key for Cloudflare
ENCODED_API="eVlZdVkyX0pyUEctQ3llcGlkZzU4MmtZV2ZoQWRXUHUtZXJ0cjFmTQ=="
CLOUDFLARE_API=$(echo "$ENCODED_API" | base64 -d)

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}Installing Cloudflare tunnel...${NC}"
    
    # Force 32-bit ARM package for RPi
    CLOUDFLARED_PKG="cloudflared-linux-armhf.deb"
    
    echo -e "${YELLOW}Downloading ${CLOUDFLARED_PKG}...${NC}"
    
    if ! wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/${CLOUDFLARED_PKG}; then
        echo -e "${RED}Failed to download cloudflared. Check internet connection.${NC}"
        exit 1
    fi
    
    # Install cloudflared
    sudo dpkg -i ${CLOUDFLARED_PKG} 2>/dev/null || {
        echo -e "${YELLOW}Fixing dependencies...${NC}"
        sudo apt-get update
        sudo apt-get install -f -y
        sudo dpkg -i ${CLOUDFLARED_PKG}
    }
    
    rm ${CLOUDFLARED_PKG}
fi

# Generate controller serial
echo -e "${YELLOW}Generating controller serial number...${NC}"
RANDOM_SUFFIX=$(openssl rand -hex 3 | tr '[:lower:]' '[:upper:]')
CONTROLLER_SERIAL="NexusController-anc-${RANDOM_SUFFIX}"
TUNNEL_NAME="${CONTROLLER_SERIAL,,}"
TUNNEL_DOMAIN="${TUNNEL_NAME}.automatacontrols.com"

echo -e "${GREEN}Generated controller serial: ${CONTROLLER_SERIAL}${NC}"
echo -e "${GREEN}Tunnel domain will be: ${TUNNEL_DOMAIN}${NC}"

# Save configuration
CONFIG_FILE="${APP_DIR}/tunnel-config.txt"
echo "# Automata Remote Access Configuration" > ${CONFIG_FILE}
echo "# Generated: $(date '+%Y-%m-%d %H:%M:%S')" >> ${CONFIG_FILE}
echo "" >> ${CONFIG_FILE}
echo "CONTROLLER_SERIAL=${CONTROLLER_SERIAL}" >> ${CONFIG_FILE}
echo "TUNNEL_DOMAIN=${TUNNEL_DOMAIN}" >> ${CONFIG_FILE}
echo "TARGET_SERVICE=Portal" >> ${CONFIG_FILE}
echo "TARGET_PORT=8443" >> ${CONFIG_FILE}

# Create cloudflared directory
mkdir -p /home/${USER}/.cloudflared

# Get Cloudflare account ID
echo -e "${YELLOW}Setting up Cloudflare tunnel...${NC}"
ACCOUNT_ID="436dc4767ed5312866132f09bfea284c"

# Check for existing tunnel and delete if exists
echo -e "${YELLOW}Checking for existing tunnel: ${TUNNEL_NAME}${NC}"
EXISTING_TUNNELS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels?name=${TUNNEL_NAME}" \
    -H "Authorization: Bearer ${CLOUDFLARE_API}" \
    -H "Content-Type: application/json")

EXISTING_ID=$(echo "$EXISTING_TUNNELS" | grep -oP '"id":"\K[^"]+' | head -1)

if [ ! -z "$EXISTING_ID" ]; then
    echo -e "${YELLOW}Deleting existing tunnel...${NC}"
    curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels/${EXISTING_ID}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API}" \
        -H "Content-Type: application/json"
    sleep 2
fi

# Create new tunnel
echo -e "${YELLOW}Creating new tunnel: ${TUNNEL_NAME}${NC}"
RAW_SECRET="${CONTROLLER_SERIAL}-Invertedskynet2$"
TUNNEL_SECRET=$(echo -n "${RAW_SECRET}" | base64 | tr -d '\n')

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
echo "TUNNEL_ID=${TUNNEL_ID}" >> ${CONFIG_FILE}

# Create DNS record
echo -e "${YELLOW}Creating DNS record...${NC}"
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=automatacontrols.com" \
    -H "Authorization: Bearer ${CLOUDFLARE_API}" \
    -H "Content-Type: application/json" | \
    grep -oP '"id":"\K[^"]+' | head -1)

if [ ! -z "$ZONE_ID" ]; then
    # Delete existing DNS record
    EXISTING_DNS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?name=${TUNNEL_DOMAIN}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API}" \
        -H "Content-Type: application/json")
    
    EXISTING_DNS_ID=$(echo "$EXISTING_DNS" | grep -oP '"id":"\K[^"]+' | head -1)
    
    if [ ! -z "$EXISTING_DNS_ID" ]; then
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
fi

# Create credentials file
cat > /home/${USER}/.cloudflared/${TUNNEL_ID}.json << EOF
{
  "AccountTag": "${ACCOUNT_ID}",
  "TunnelSecret": "${TUNNEL_SECRET}",
  "TunnelID": "${TUNNEL_ID}"
}
EOF

# Create tunnel config
cat > /home/${USER}/.cloudflared/config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: /home/${USER}/.cloudflared/${TUNNEL_ID}.json

ingress:
  # Everything goes to Nginx HTTPS
  - hostname: ${TUNNEL_DOMAIN}
    service: https://127.0.0.1:8443
    originRequest:
      noTLSVerify: true
  
  # Catch-all
  - service: http_status:404
EOF

# Set permissions
chown -R ${USER}:${USER} /home/${USER}/.cloudflared
chmod 600 /home/${USER}/.cloudflared/*.json
chmod 644 /home/${USER}/.cloudflared/config.yml
chown -R ${USER}:${USER} ${PORTAL_DIR}
chown ${USER}:${USER} ${CONFIG_FILE}

# Create cloudflared systemd service
echo -e "${YELLOW}Creating Cloudflare tunnel service...${NC}"
cat > /etc/systemd/system/cloudflared.service << EOF
[Unit]
Description=Cloudflare Tunnel for Remote Access
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

# Start all services
echo -e "${YELLOW}Starting services...${NC}"
systemctl daemon-reload
systemctl enable automata-portal
systemctl restart automata-portal
systemctl enable cloudflared
systemctl restart cloudflared

# Wait for services to start
sleep 5

# Check services
echo ""
echo -e "${BLUE}Checking service status...${NC}"

if systemctl is-active --quiet automata-portal; then
    echo -e "${GREEN}✓ Portal service is running${NC}"
else
    echo -e "${RED}✗ Portal service failed to start${NC}"
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx failed to start${NC}"
fi

if systemctl is-active --quiet nodered; then
    echo -e "${GREEN}✓ Node-RED is running${NC}"
else
    echo -e "${YELLOW}! Node-RED is not running${NC}"
fi

if systemctl is-active --quiet cloudflared; then
    echo -e "${GREEN}✓ Cloudflare tunnel is running${NC}"
else
    echo -e "${RED}✗ Cloudflare tunnel failed to start${NC}"
fi

# Clear sensitive variable
unset CLOUDFLARE_API

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${GREEN}Controller Serial: ${CONTROLLER_SERIAL}${NC}"
echo -e "${GREEN}Tunnel ID: ${TUNNEL_ID}${NC}"
echo ""
echo -e "${GREEN}Access your portal at:${NC}"
echo -e "  Local:  ${YELLOW}https://$(hostname -I | cut -d' ' -f1):8443${NC}"
echo -e "  Remote: ${YELLOW}https://${TUNNEL_DOMAIN}${NC}"
echo ""
echo -e "${YELLOW}Configuration saved to: ${CONFIG_FILE}${NC}"
echo ""
echo -e "${YELLOW}Services:${NC}"
echo -e "  Portal:     ${GREEN}systemctl status automata-portal${NC}"
echo -e "  Nginx:      ${GREEN}systemctl status nginx${NC}"
echo -e "  Node-RED:   ${GREEN}systemctl status nodered${NC}"
echo -e "  Tunnel:     ${GREEN}systemctl status cloudflared${NC}"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo -e "  ${GREEN}journalctl -u automata-portal -f${NC}"
echo -e "  ${GREEN}journalctl -u cloudflared -f${NC}"
echo ""