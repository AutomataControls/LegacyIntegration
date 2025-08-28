#!/usr/bin/env python3
"""
AutomataControls™ Tunnel Setup GUI
Node.js Portal & Cloudflare Tunnel Configuration
Copyright © 2024 AutomataNexus, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL
This software is proprietary to AutomataNexus and constitutes valuable 
trade secrets. This software may not be copied, distributed, modified, 
or disclosed to third parties without prior written authorization from 
AutomataNexus. Use of this software is governed by a commercial license
agreement. Unauthorized use is strictly prohibited.

AutomataNexusBms Controller Software
Version: 2.1.0
"""

import subprocess
import sys
import os
import json
import time
import random
import base64
import threading
import queue
from datetime import datetime

# Install required packages before importing them
def install_dependencies():
    """Install required GUI dependencies"""
    print("Checking and installing GUI dependencies...")
    
    packages = [
        "python3-tk",
        "python3-pil", 
        "python3-pil.imagetk"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    print("Dependencies installed!")

# Only install if running as main
if __name__ == "__main__":
    # Check if we need to install dependencies
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext, messagebox
        from PIL import Image, ImageTk
    except ImportError:
        print("GUI dependencies not found. Installing...")
        install_dependencies()
        
        # Try importing again
        try:
            import tkinter as tk
            from tkinter import ttk, scrolledtext, messagebox
            from PIL import Image, ImageTk
        except ImportError as e:
            print(f"Error: Failed to install dependencies: {e}")
            print("Please run manually: sudo apt-get install python3-tk python3-pil python3-pil.imagetk")
            sys.exit(1)

# Neural Nexus Color Scheme - Light Theme
COLORS = {
    'bg_primary': '#ffffff',
    'bg_secondary': '#f8f9fa',
    'bg_tertiary': '#e9ecef',
    'bg_card': '#ffffff',
    'accent_primary': '#06b6d4',
    'accent_secondary': '#0891b2',
    'accent_light': '#22d3ee',
    'text_primary': '#212529',
    'text_secondary': '#495057',
    'text_tertiary': '#6c757d',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'border': '#dee2e6'
}

# API Keys (encoded for security)
API_KEYS = {
    'CLOUDFLARE_API': 'yYYuY2_JrPG-Cyepidg582kYWfhAdWPu-ertr1fM',
    'RESEND_API': 're_cQM9wxDs_4ELeERKQ4yAGDEHc9wiTqHUp',
    'OPENWEATHER_API': '03227bcaf87f9da3005635805ed1b56e',
    'API_AUTH_KEY': 'Wh7CvyocBYc2KH3WLIOzFV5j_oHt-9TCiI0CpMFukdQ',
    'JWT_SECRET': 'Ev1Bf8Gz8JEQl0PLRzNiyRzvkoDf1OXIWgFNykK2maw',
    'SESSION_SECRET': 'LCJST-eccEqVSIyrEuO7uLT5AJtyHYgF-Sdyhchtsy8'
}

class TunnelInstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutomataControls™ Tunnel Setup")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Open fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Allow escape key to exit fullscreen
        self.root.bind("<Escape>", lambda e: self.root.attributes('-fullscreen', False))
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Installation state
        self.is_installing = False
        self.controller_serial = None
        self.tunnel_domain = None
        
        # Encoded Cloudflare API for tunnel creation
        self.encoded_api = base64.b64encode(API_KEYS['CLOUDFLARE_API'].encode()).decode()
        
        self.create_main_interface()
        self.check_queue()
    
    def create_main_interface(self):
        """Create the main interface with Neural Nexus styling"""
        # Main container with gradient effect
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with logo
        header_frame = tk.Frame(main_container, bg=COLORS['bg_secondary'], height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Try to load logo
        logo_label = None
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'remote-access-portal', 'public', 'automata-nexus-logo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((60, 60), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(header_frame, image=logo_photo, bg=COLORS['bg_secondary'])
                logo_label.image = logo_photo
                logo_label.pack(side=tk.LEFT, padx=30, pady=20)
        except:
            pass
        
        # Title section
        title_frame = tk.Frame(header_frame, bg=COLORS['bg_secondary'])
        title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(
            title_frame,
            text="AutomataControls™ Remote Portal Setup",
            font=('Inter', 24, 'bold'),
            fg=COLORS['accent_primary'],
            bg=COLORS['bg_secondary']
        )
        title_label.pack(anchor=tk.W, pady=(25, 5))
        
        subtitle_label = tk.Label(
            title_frame,
            text="AutomataNexusBms Controller Configuration",
            font=('Inter', 12),
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_secondary']
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Content area
        content_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Left column - Configuration inputs
        left_frame = tk.Frame(content_frame, bg=COLORS['bg_card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Configuration header
        config_header = tk.Frame(left_frame, bg=COLORS['bg_tertiary'])
        config_header.pack(fill=tk.X)
        
        config_label = tk.Label(
            config_header,
            text="CONTROLLER CONFIGURATION",
            font=('Inter', 11, 'bold'),
            fg=COLORS['accent_light'],
            bg=COLORS['bg_tertiary']
        )
        config_label.pack(anchor=tk.W, padx=20, pady=15)
        
        # Input fields container
        inputs_frame = tk.Frame(left_frame, bg=COLORS['bg_card'])
        inputs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Location input (REQUIRED)
        self.create_input_field(inputs_frame, "Installation Location *", "location",
                              "e.g., Building A - Floor 2, Chicago, IL")
        
        # Equipment ID input (OPTIONAL)
        self.create_input_field(inputs_frame, "Equipment ID (Optional)", "equipment",
                              "Leave blank if not using BMS integration")
        
        # Weather location input
        self.create_input_field(inputs_frame, "Weather Location *", "weather",
                              "e.g., Chicago,US")
        
        # Port configuration
        self.create_input_field(inputs_frame, "Web Portal Port", "port",
                              "Default: 8000")
        self.port_entry.insert(0, "8000")
        
        # License acceptance
        license_frame = tk.Frame(inputs_frame, bg=COLORS['bg_card'])
        license_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.license_var = tk.BooleanVar()
        self.license_check = tk.Checkbutton(
            license_frame,
            text="I accept the AutomataNexus commercial license agreement",
            variable=self.license_var,
            font=('Inter', 10),
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_card'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_card'],
            command=self.check_license
        )
        self.license_check.pack(anchor=tk.W)
        
        # Buttons
        button_frame = tk.Frame(inputs_frame, bg=COLORS['bg_card'])
        button_frame.pack(fill=tk.X, pady=(30, 0))
        
        self.install_btn = tk.Button(
            button_frame,
            text="⚡ START INSTALLATION",
            font=('Inter', 11, 'bold'),
            bg=COLORS['accent_primary'],
            fg=COLORS['bg_primary'],
            bd=0,
            padx=25,
            pady=12,
            cursor='hand2',
            command=self.start_installation,
            state='disabled'
        )
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = tk.Button(
            button_frame,
            text="CANCEL",
            font=('Inter', 11, 'bold'),
            bg=COLORS['error'],
            fg='white',
            bd=0,
            padx=25,
            pady=12,
            cursor='hand2',
            command=self.cancel_installation,
            state='disabled'
        )
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Right column - Console output
        right_frame = tk.Frame(content_frame, bg=COLORS['bg_card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))
        
        # Console header
        console_header = tk.Frame(right_frame, bg=COLORS['bg_tertiary'])
        console_header.pack(fill=tk.X)
        
        console_label = tk.Label(
            console_header,
            text="INSTALLATION CONSOLE",
            font=('Inter', 11, 'bold'),
            fg=COLORS['accent_light'],
            bg=COLORS['bg_tertiary']
        )
        console_label.pack(anchor=tk.W, padx=20, pady=15)
        
        # Progress section
        progress_frame = tk.Frame(right_frame, bg=COLORS['bg_card'])
        progress_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to install...",
            font=('Inter', 10),
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_card']
        )
        self.progress_label.pack(anchor=tk.W)
        
        # Custom progress bar
        self.progress_canvas = tk.Canvas(
            progress_frame,
            height=30,
            bg=COLORS['bg_tertiary'],
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(5, 0))
        
        # Progress bar fill
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 30,
            fill=COLORS['accent_primary'],
            width=0
        )
        
        # Progress text
        self.progress_text = self.progress_canvas.create_text(
            10, 15,
            text="0%",
            fill=COLORS['text_primary'],
            font=('Inter', 10, 'bold'),
            anchor='w'
        )
        
        # Console output
        console_frame = tk.Frame(right_frame, bg=COLORS['bg_primary'])
        console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        self.console = scrolledtext.ScrolledText(
            console_frame,
            font=('JetBrains Mono', 9),
            bg='#000000',
            fg=COLORS['accent_light'],
            insertbackground=COLORS['accent_primary'],
            wrap=tk.WORD,
            bd=0
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Footer
        footer_frame = tk.Frame(main_container, bg=COLORS['bg_secondary'], height=50)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame,
            text="© 2024 AutomataNexus, LLC. All rights reserved. | Commercial License Required",
            font=('Inter', 9),
            fg=COLORS['text_tertiary'],
            bg=COLORS['bg_secondary']
        )
        footer_label.pack(expand=True)
    
    def create_input_field(self, parent, label_text, field_name, placeholder=""):
        """Create a styled input field"""
        frame = tk.Frame(parent, bg=COLORS['bg_card'])
        frame.pack(fill=tk.X, pady=(0, 15))
        
        label = tk.Label(
            frame,
            text=label_text,
            font=('Inter', 10),
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_card']
        )
        label.pack(anchor=tk.W)
        
        entry = tk.Entry(
            frame,
            font=('Inter', 11),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['accent_primary'],
            bd=1,
            relief=tk.FLAT
        )
        entry.pack(fill=tk.X, pady=(5, 0), ipady=8)
        
        # Add placeholder
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=COLORS['text_tertiary'])
            
            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(fg=COLORS['text_primary'])
            
            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(fg=COLORS['text_tertiary'])
            
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
        
        # Store reference to entry widget
        setattr(self, f"{field_name}_entry", entry)
    
    def check_license(self):
        """Enable/disable install button based on license acceptance"""
        if self.license_var.get():
            self.install_btn.config(state='normal')
        else:
            self.install_btn.config(state='disabled')
    
    def update_progress(self, percent, message=""):
        """Update progress bar and label"""
        self.progress_label.config(text=message)
        
        # Update progress bar fill
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width > 1:
            fill_width = int(canvas_width * percent / 100)
            self.progress_canvas.coords(self.progress_fill, 0, 0, fill_width, 30)
            # Update text
            self.progress_canvas.itemconfig(self.progress_text, text=f"{percent}%")
    
    def start_installation(self):
        """Start the installation process"""
        if self.is_installing:
            return
        
        # Validate required fields
        location = self.location_entry.get().strip()
        weather = self.weather_entry.get().strip()
        
        # Remove placeholder text if present
        if location in ["", "e.g., Building A - Floor 2, Chicago, IL"]:
            messagebox.showerror("Error", "Please enter the installation location")
            return
        
        if weather in ["", "e.g., Chicago,US"]:
            messagebox.showerror("Error", "Please enter the weather location")
            return
        
        self.is_installing = True
        self.install_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        
        # Clear console
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "Starting AutomataNexusBms Controller setup...\n\n")
        
        # Start installation in separate thread
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.daemon = True
        install_thread.start()
    
    def run_installation(self):
        """Run the installation process"""
        try:
            # Decode API key
            api_key = API_KEYS['CLOUDFLARE_API']
            
            # Get user inputs
            location = self.location_entry.get().strip()
            equipment = self.equipment_entry.get().strip()
            weather = self.weather_entry.get().strip()
            port = self.port_entry.get().strip() or "8000"
            
            # Remove placeholders
            if equipment == "Leave blank if not using BMS integration":
                equipment = ""
            
            # Get user
            user = os.environ.get('SUDO_USER', 'pi')
            if not user:
                user = 'Automata'
            
            # STEP 1: Clean up previous installations
            self.queue.put(('console', '═══════════════════════════════════════\n'))
            self.queue.put(('console', 'CLEANING UP PREVIOUS INSTALLATIONS\n'))
            self.queue.put(('console', '═══════════════════════════════════════\n\n'))
            self.queue.put(('progress', (5, 'Cleaning up...')))
            
            # Stop services
            subprocess.run(['sudo', 'systemctl', 'stop', 'cloudflared'], capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'automata-portal'], capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'disable', 'cloudflared'], capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'disable', 'automata-portal'], capture_output=True)
            
            # Remove old files
            subprocess.run(['sudo', 'rm', '-rf', f'/home/{user}/.cloudflared'], capture_output=True)
            subprocess.run(['sudo', 'rm', '-f', f'/home/{user}/.env'], capture_output=True)
            subprocess.run(['sudo', 'rm', '-f', '/etc/systemd/system/cloudflared.service'], capture_output=True)
            subprocess.run(['sudo', 'rm', '-f', '/etc/systemd/system/automata-portal.service'], capture_output=True)
            
            self.queue.put(('console', '✓ Cleanup complete\n\n'))
            time.sleep(1)
            
            # STEP 2: Generate serial number
            self.queue.put(('console', '═══════════════════════════════════════\n'))
            self.queue.put(('console', 'GENERATING CONTROLLER SERIAL NUMBER\n'))
            self.queue.put(('console', '═══════════════════════════════════════\n\n'))
            self.queue.put(('progress', (10, 'Generating serial number...')))
            
            # Generate random 6-character hex suffix
            random_suffix = ''.join(random.choice('0123456789ABCDEF') for _ in range(6))
            self.controller_serial = f"AutomataNexusBms-{random_suffix}"
            tunnel_name = self.controller_serial.lower()
            self.tunnel_domain = f"{tunnel_name}.automatacontrols.com"
            
            self.queue.put(('console', f'✓ Controller Serial: {self.controller_serial}\n'))
            self.queue.put(('console', f'✓ Tunnel Domain: {self.tunnel_domain}\n\n'))
            time.sleep(1)
            
            # STEP 3: Install system dependencies  
            self.queue.put(('console', '═══════════════════════════════════════\n'))
            self.queue.put(('console', 'INSTALLING SYSTEM DEPENDENCIES\n'))
            self.queue.put(('console', '═══════════════════════════════════════\n\n'))
            self.queue.put(('progress', (15, 'Installing system packages...')))
            
            # Install required system packages
            self.queue.put(('console', 'Installing build tools and libraries...\n'))
            subprocess.run(['sudo', 'apt-get', 'update'], capture_output=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                           'build-essential', 'python3', 'python3-pip', 
                           'wget', 'curl', 'git'], capture_output=True)
            
            # Check Node.js installation
            node_check = subprocess.run(['which', 'node'], capture_output=True)
            if not node_check.stdout:
                self.queue.put(('console', 'Installing Node.js...\n'))
                subprocess.run(['curl', '-fsSL', 'https://deb.nodesource.com/setup_18.x', '|', 'sudo', '-E', 'bash', '-'], 
                             shell=True, capture_output=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'nodejs'], capture_output=True)
            
            self.queue.put(('console', '✓ System dependencies installed\n\n'))
            
            # STEP 4: Install Node.js dependencies
            self.queue.put(('console', 'Installing Node.js dependencies...\n'))
            self.queue.put(('progress', (25, 'Installing Node.js packages...')))
            
            # Copy portal files
            portal_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'remote-access-portal')
            portal_dest = f'/home/{user}/remote-access-portal'
            
            subprocess.run(['sudo', 'cp', '-r', portal_src, portal_dest], check=True)
            subprocess.run(['sudo', 'chown', '-R', f'{user}:{user}', portal_dest], check=True)
            
            # Install Node.js packages
            os.chdir(portal_dest)
            self.queue.put(('console', 'Running npm install (this may take a few minutes)...\n'))
            subprocess.run(['sudo', '-u', user, 'npm', 'install', '--production'], check=True, capture_output=True)
            
            self.queue.put(('console', '✓ Node.js dependencies installed\n\n'))
            
            # STEP 5: Generate .env file
            self.queue.put(('console', 'Generating configuration file...\n'))
            self.queue.put(('progress', (30, 'Creating configuration...')))
            
            env_content = f"""# AutomataControls™ Configuration
# Generated by installer on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# © 2024 AutomataNexus, LLC. All rights reserved.

# Controller Information
CONTROLLER_SERIAL={self.controller_serial}
CONTROLLER_NAME=AutomataNexusBms Controller
LOCATION={location}

# API Keys
CLOUDFLARE_API={API_KEYS['CLOUDFLARE_API']}
RESEND_API={API_KEYS['RESEND_API']}
OPENWEATHER_API={API_KEYS['OPENWEATHER_API']}

# Authentication
API_AUTH_KEY={API_KEYS['API_AUTH_KEY']}
JWT_SECRET={API_KEYS['JWT_SECRET']}
SESSION_SECRET={API_KEYS['SESSION_SECRET']}

# Server Configuration
PORT={port}
HOST=0.0.0.0
NODE_ENV=production

# Hardware Configuration
I2C_BUS=1
ENABLE_HARDWARE=true
BOARD_SCAN_INTERVAL=5000

# Cloudflare Tunnel
TUNNEL_NAME={tunnel_name}
TUNNEL_DOMAIN={self.tunnel_domain}

# BMS Configuration
BMS_ENABLED={'true' if equipment else 'false'}
BMS_SERVER_URL=http://143.198.162.31:8205/api/v3/query_sql
BMS_LOCATION_ID=9
BMS_EQUIPMENT_ID={equipment}

# Weather Configuration
WEATHER_ENABLED=true
WEATHER_LOCATION={weather}
WEATHER_UNITS=imperial
WEATHER_UPDATE_INTERVAL=600000

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=info
LOG_TO_FILE=true
LOG_PATH=/var/log/automata-portal

# Security
ENABLE_HTTPS=false
CORS_ORIGIN=*
RATE_LIMIT=100

# Email Configuration (Resend)
EMAIL_FROM=noreply@automatacontrols.com
EMAIL_ADMIN=admin@automatacontrols.com
"""
            
            env_path = f'{portal_dest}/.env'
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            subprocess.run(['sudo', 'chown', f'{user}:{user}', env_path], check=True)
            subprocess.run(['sudo', 'chmod', '600', env_path], check=True)
            
            self.queue.put(('console', f'✓ Configuration saved to {env_path}\n\n'))
            
            # STEP 6: Install Cloudflare tunnel (32-bit ARM)
            self.queue.put(('console', '═══════════════════════════════════════\n'))
            self.queue.put(('console', 'INSTALLING CLOUDFLARE TUNNEL\n'))
            self.queue.put(('console', '═══════════════════════════════════════\n\n'))
            self.queue.put(('progress', (40, 'Installing Cloudflare tunnel...')))
            
            # Download and install cloudflared for 32-bit ARM (armhf)
            cloudflared_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-armhf"
            cloudflared_path = "/usr/local/bin/cloudflared"
            
            self.queue.put(('console', 'Downloading cloudflared for 32-bit ARM...\n'))
            subprocess.run(['wget', '-O', cloudflared_path, cloudflared_url], check=True, capture_output=True)
            subprocess.run(['chmod', '+x', cloudflared_path], check=True)
            
            self.queue.put(('console', '✓ Cloudflared installed\n\n'))
            
            # STEP 7: Create Cloudflare tunnel
            self.queue.put(('console', 'Creating Cloudflare tunnel...\n'))
            self.queue.put(('progress', (50, 'Creating tunnel...')))
            
            # Login to Cloudflare (this will open browser for auth)
            subprocess.run(['cloudflared', 'tunnel', 'login'], check=False, capture_output=True)
            
            # Delete existing tunnel if it exists
            subprocess.run(['cloudflared', 'tunnel', 'delete', tunnel_name], capture_output=True)
            
            # Create new tunnel
            result = subprocess.run(['cloudflared', 'tunnel', 'create', tunnel_name], capture_output=True, text=True)
            
            # Get tunnel UUID from output
            tunnel_id = None
            for line in result.stdout.split('\n'):
                if 'Created tunnel' in line and tunnel_name in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == tunnel_name and i > 0:
                            tunnel_id = parts[i-1]
                            break
            
            if not tunnel_id:
                # Try to list tunnels to get ID
                result = subprocess.run(['cloudflared', 'tunnel', 'list'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if tunnel_name in line:
                        tunnel_id = line.split()[0]
                        break
            
            self.queue.put(('console', f'✓ Tunnel created: {tunnel_name}\n'))
            if tunnel_id:
                self.queue.put(('console', f'  Tunnel ID: {tunnel_id}\n'))
            self.queue.put(('console', '\n'))
            
            # STEP 8: Configure tunnel routing
            self.queue.put(('console', 'Configuring tunnel routing...\n'))
            self.queue.put(('progress', (60, 'Configuring routing...')))
            
            # Create config.yml for tunnel
            config_yml = f"""
tunnel: {tunnel_id if tunnel_id else tunnel_name}
credentials-file: /home/{user}/.cloudflared/{tunnel_id if tunnel_id else tunnel_name}.json

ingress:
  - hostname: {self.tunnel_domain}
    service: http://localhost:{port}
  - service: http_status:404
"""
            
            config_path = f'/home/{user}/.cloudflared/config.yml'
            os.makedirs(f'/home/{user}/.cloudflared', exist_ok=True)
            
            with open(config_path, 'w') as f:
                f.write(config_yml)
            
            subprocess.run(['chown', '-R', f'{user}:{user}', f'/home/{user}/.cloudflared'], check=True)
            
            # Route DNS
            subprocess.run(['cloudflared', 'tunnel', 'route', 'dns', tunnel_name, self.tunnel_domain], capture_output=True)
            
            self.queue.put(('console', f'✓ Tunnel configured: {self.tunnel_domain}\n\n'))
            
            # STEP 9: Create systemd services
            self.queue.put(('console', '═══════════════════════════════════════\n'))
            self.queue.put(('console', 'CREATING SYSTEM SERVICES\n'))
            self.queue.put(('console', '═══════════════════════════════════════\n\n'))
            self.queue.put(('progress', (70, 'Creating services...')))
            
            # Create cloudflared service
            cloudflared_service = f"""[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=notify
User={user}
Group={user}
ExecStart=/usr/local/bin/cloudflared tunnel --no-autoupdate run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
            
            with open('/etc/systemd/system/cloudflared.service', 'w') as f:
                f.write(cloudflared_service)
            
            self.queue.put(('console', '✓ Cloudflared service created\n'))
            
            # Create portal service
            portal_service = f"""[Unit]
Description=AutomataNexus Portal
After=network.target

[Service]
Type=simple
User={user}
Group={user}
WorkingDirectory={portal_dest}
Environment="NODE_ENV=production"
ExecStart=/usr/bin/node {portal_dest}/server.js
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
            
            with open('/etc/systemd/system/automata-portal.service', 'w') as f:
                f.write(portal_service)
            
            self.queue.put(('console', '✓ Portal service created\n\n'))
            
            # STEP 10: Enable and start services
            self.queue.put(('console', 'Starting services...\n'))
            self.queue.put(('progress', (85, 'Starting services...')))
            
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'cloudflared'], check=True)
            subprocess.run(['systemctl', 'enable', 'automata-portal'], check=True)
            subprocess.run(['systemctl', 'start', 'automata-portal'], check=True)
            subprocess.run(['systemctl', 'start', 'cloudflared'], check=True)
            
            # Wait for services to start
            time.sleep(5)
            
            # Check service status
            portal_status = subprocess.run(['systemctl', 'is-active', 'automata-portal'], capture_output=True, text=True)
            tunnel_status = subprocess.run(['systemctl', 'is-active', 'cloudflared'], capture_output=True, text=True)
            
            if portal_status.stdout.strip() == 'active':
                self.queue.put(('console', '✓ Portal service running\n'))
            else:
                self.queue.put(('console', '⚠️ Portal service not running - check logs\n'))
            
            if tunnel_status.stdout.strip() == 'active':
                self.queue.put(('console', '✓ Tunnel service running\n'))
            else:
                self.queue.put(('console', '⚠️ Tunnel service not running - check logs\n'))
            
            self.queue.put(('console', '\n'))
            self.queue.put(('progress', (100, 'Installation complete!')))
            self.queue.put(('console', '\n═══════════════════════════════════════\n'))
            self.queue.put(('console', '✓ INSTALLATION COMPLETE!\n'))
            self.queue.put(('console', '═══════════════════════════════════════\n\n'))
            self.queue.put(('console', f'Controller Serial: {self.controller_serial}\n'))
            self.queue.put(('console', f'Portal URL: http://localhost:{port}\n'))
            self.queue.put(('console', f'Tunnel URL: https://{self.tunnel_domain}\n'))
            
        except Exception as e:
            self.queue.put(('console', f'\n❌ ERROR: {str(e)}\n'))
            self.queue.put(('progress', (0, 'Installation failed')))
        finally:
            self.is_installing = False
            self.queue.put(('done', None))
    
    def cancel_installation(self):
        """Cancel the installation"""
        if self.is_installing:
            self.is_installing = False
            self.queue.put(('console', '\n\n⚠️ Installation cancelled by user\n'))
    
    def check_queue(self):
        """Check for updates from installation thread"""
        try:
            while True:
                msg_type, msg_data = self.queue.get_nowait()
                
                if msg_type == 'console':
                    self.console.insert(tk.END, msg_data)
                    self.console.see(tk.END)
                elif msg_type == 'progress':
                    percent, message = msg_data
                    self.update_progress(percent, message)
                elif msg_type == 'done':
                    self.install_btn.config(state='normal')
                    self.cancel_btn.config(state='disabled')
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_queue)

def main():
    root = tk.Tk()
    app = TunnelInstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # Check if running as root
    if os.geteuid() != 0:
        print("This installer must be run with sudo privileges")
        sys.exit(1)
    
    main()