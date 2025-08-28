# Legacy Integration Package
## Automata Remote Access Portal for Raspberry Pi 4 Systems

![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204-c51a4a)
![Node-RED](https://img.shields.io/badge/Node--RED-v3.0%2B-8F0000)
![Python](https://img.shields.io/badge/Python-3.7%2B-3776AB)
![Cloudflare](https://img.shields.io/badge/Cloudflare-Tunnel-F38020)
![License](https://img.shields.io/badge/License-Commercial-red)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

This package provides remote access capabilities for legacy Raspberry Pi 4 systems with 64GB SD cards, enabling secure Cloudflare tunnel access to Node-RED, terminal, and Neural BMS.

## Package Contents

### 1. GUI Installer (`setup-tunnel-gui.py`)
- Full-featured GUI installer matching the Automata Nexus installer style
- Generates unique controller serial numbers
- Creates Cloudflare tunnels automatically
- Installs all dependencies
- Sets up systemd services for auto-start on boot

### 2. Command-Line Installer (`setup-tunnel.sh`)
- Shell script version for headless installation
- Same functionality as GUI installer
- Suitable for SSH installation

### 3. Web Portal Application (`remote-access-portal/`)
- Multi-page web interface styled to match Neural Nexus
- Dashboard with system monitoring
- Node-RED iframe integration
- Web-based terminal with xterm.js
- Neural BMS iframe integration
- Runs on port 8000

## Installation

### GUI Installation (Recommended)
```bash
cd "/home/Automata/AutomataNexus/Legacy Integration"
sudo python3 setup-tunnel-gui.py
```

### Command-Line Installation
```bash
cd "/home/Automata/AutomataNexus/Legacy Integration"
sudo bash setup-tunnel.sh
```

## Features

### Serial Number Generation
- Unique 6-character hex suffix: `NexusController-anc-XXXXXX`
- Automatically generated during installation
- Used for tunnel identification

### Cloudflare Tunnel
- Automatic tunnel creation using API
- DNS record creation at `*.automatacontrols.com`
- Secure remote access without port forwarding

### Web Portal Services
- **Dashboard**: System status, CPU/Memory/Disk monitoring
- **Node-RED**: Access to Node-RED on port 1880
- **Terminal**: Full bash terminal in browser
- **Neural BMS**: Access to neuralbms.automatacontrols.com

### Automatic Startup
Two systemd services are created:
- `cloudflared.service` - Manages the tunnel connection
- `automata-portal.service` - Runs the web portal

Both services:
- Start automatically on boot
- Restart on failure
- Can be managed with systemctl commands

## System Requirements

- Raspberry Pi 4 with 64GB SD card
- Raspbian OS (Bullseye or newer)
- Python 3.7+
- Node-RED installed and running on port 1880
- Internet connection

## Dependencies Installed

### Python Packages
- Flask
- Flask-SocketIO
- python-socketio
- eventlet
- python-engineio
- requests

### System Packages
- cloudflared (Cloudflare tunnel daemon)
- python3-tk (for GUI)
- python3-pil (for GUI)

## Configuration Files

After installation, configuration is saved to:
- `/home/Automata/tunnel-config.txt` - Contains serial number and tunnel details
- `/home/Automata/.cloudflared/config.yml` - Cloudflare tunnel configuration

## Access Your Device

After successful installation:
1. Your device will be accessible at: `https://[serial-number].automatacontrols.com`
2. The portal provides access to all services through a single URL
3. No port forwarding or firewall configuration required

## Service Management

```bash
# Check status
sudo systemctl status cloudflared
sudo systemctl status automata-portal

# Restart services
sudo systemctl restart cloudflared
sudo systemctl restart automata-portal

# View logs
sudo journalctl -u cloudflared -f
sudo journalctl -u automata-portal -f
```

## Troubleshooting

1. **Tunnel not connecting**: Check cloudflared service logs
2. **Portal not accessible**: Ensure both services are running
3. **Node-RED not showing**: Verify Node-RED is running on port 1880
4. **Terminal not working**: Check Flask-SocketIO installation

## Security Notice

This software is protected by commercial license.
© 2025 AutomataNexus AI & AutomataControls
Unauthorized use is prohibited.

## Support

For support, contact: devops@automatacontrols.com