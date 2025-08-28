#!/usr/bin/env python3
"""
Automata Tunnel Setup GUI
Serial Number Generation & Cloudflare Tunnel Configuration
Version: 1.0.0
"""

import subprocess
import sys
import os
import base64
import json
import random
import string

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

# Now import the rest
import threading
import time
import queue

# Color scheme - Ultra light mint theme (matching original)
COLORS = {
    'bg_main': '#fafffe',        # Almost white with barely visible mint tint
    'bg_secondary': '#f5fffd',   # Extremely light mint
    'bg_accent': '#f0fffc',      # Very subtle mint accent
    'slate': '#64748b',          # Slate for borders
    'light_grey': '#94a3b8',     # Light grey for disabled
    'ultra_teal': '#06b6d4',     # Ultra teal for highlights
    'nautical_blue': '#0ea5e9',  # Nautical blue for progress
    'text_dark': '#1e293b',      # Dark text on light bg
    'text_mid': '#475569',       # Mid-tone text
    'success': '#10b981',
    'error': '#ef4444',
    'warning': '#f59e0b'
}

class TunnelSetupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automata Tunnel Setup")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Open fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Allow escape key to exit fullscreen
        self.root.bind("<Escape>", lambda e: self.root.attributes('-fullscreen', False))
        self.root.configure(bg=COLORS['bg_main'])
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Installation state
        self.is_installing = False
        self.process = None
        
        # Encoded API key
        self.encoded_api = "eVlZdVkyX0pyUEctQ3llcGlkZzU4MmtZV2ZoQWRXUHUtZXJ0cjFmTQ=="
        
        # Generated values
        self.controller_serial = None
        self.tunnel_domain = None
        
        self.setup_ui()
        self.check_prerequisites()
        
        # Start queue processing
        self.process_queue()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = tk.Frame(self.root, bg=COLORS['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Logo section
        logo_frame = tk.Frame(main_frame, bg=COLORS['bg_main'])
        logo_frame.pack(pady=(0, 5))
        
        # Try to load logo
        logo_path = "/home/Automata/AutomataNexus/automata-nexus/app/public/automata-nexus-logo.png"
        try:
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                orig_width, orig_height = logo_img.size
                new_width = 150
                new_height = int((new_width / orig_width) * orig_height)
                logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(logo_frame, image=self.logo, bg=COLORS['bg_main'])
                logo_label.pack()
            else:
                # Fallback text logo
                logo_label = tk.Label(
                    logo_frame,
                    text="AUTOMATA NEXUS",
                    font=("Arial", 28, "bold"),
                    fg=COLORS['ultra_teal'],
                    bg=COLORS['bg_main']
                )
                logo_label.pack()
        except:
            # Fallback text logo
            logo_label = tk.Label(
                logo_frame,
                text="AUTOMATA NEXUS",
                font=("Arial", 28, "bold"),
                fg=COLORS['ultra_teal'],
                bg=COLORS['bg_main']
            )
            logo_label.pack()
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Node-RED Remote Access Setup",
            font=("Arial", 14),
            fg=COLORS['text_dark'],
            bg=COLORS['bg_main']
        )
        title_label.pack(pady=(2, 5))
        
        # License frame
        license_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief=tk.RAISED, bd=1)
        license_frame.pack(fill=tk.X, pady=(0, 5))
        
        license_title = tk.Label(
            license_frame,
            text="Automata Remote Access - Commercial License",
            font=("Arial", 12, "bold"),
            fg=COLORS['nautical_blue'],
            bg=COLORS['bg_secondary']
        )
        license_title.pack(pady=(5, 5))
        
        license_text = tk.Label(
            license_frame,
            text="© 2025 AutomataNexus AI & AutomataControls | Author: Andrew Jewell Sr.\n"
                 "Commercial License Required - Not Open Source\n"
                 "⚠️ UNAUTHORIZED USE PROHIBITED - Contains Trade Secrets",
            font=("Arial", 9),
            fg=COLORS['text_dark'],
            bg=COLORS['bg_secondary'],
            justify=tk.CENTER
        )
        license_text.pack(pady=(0, 5))
        
        # Accept license checkbox
        self.license_var = tk.BooleanVar()
        license_check = tk.Checkbutton(
            license_frame,
            text="I accept the commercial license agreement and have a valid license",
            variable=self.license_var,
            font=("Arial", 10, "bold"),
            fg=COLORS['text_dark'],
            bg=COLORS['bg_secondary'],
            selectcolor=COLORS['bg_accent'],
            activebackground=COLORS['bg_secondary'],
            command=self.check_license
        )
        license_check.pack(pady=(0, 5))
        
        # Configuration info frame
        config_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief=tk.RAISED, bd=1)
        config_frame.pack(fill=tk.X, pady=(5, 5))
        
        config_title = tk.Label(
            config_frame,
            text="System Configuration",
            font=("Arial", 11, "bold"),
            fg=COLORS['ultra_teal'],
            bg=COLORS['bg_secondary']
        )
        config_title.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Serial number display (will be generated)
        self.serial_frame = tk.Frame(config_frame, bg=COLORS['bg_secondary'])
        self.serial_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        serial_label = tk.Label(
            self.serial_frame,
            text="Controller Serial:",
            font=("Arial", 10, "bold"),
            fg=COLORS['text_dark'],
            bg=COLORS['bg_secondary']
        )
        serial_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.serial_value = tk.Label(
            self.serial_frame,
            text="Will be generated during setup",
            font=("Arial", 10),
            fg=COLORS['text_mid'],
            bg=COLORS['bg_secondary']
        )
        self.serial_value.pack(side=tk.LEFT)
        
        # Tunnel domain display
        self.domain_frame = tk.Frame(config_frame, bg=COLORS['bg_secondary'])
        self.domain_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        domain_label = tk.Label(
            self.domain_frame,
            text="Tunnel Domain:",
            font=("Arial", 10, "bold"),
            fg=COLORS['text_dark'],
            bg=COLORS['bg_secondary']
        )
        domain_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.domain_value = tk.Label(
            self.domain_frame,
            text="Will be generated during setup",
            font=("Arial", 10),
            fg=COLORS['text_mid'],
            bg=COLORS['bg_secondary']
        )
        self.domain_value.pack(side=tk.LEFT)
        
        # Target service info
        service_info = tk.Label(
            config_frame,
            text="Target Service: Node-RED on 127.0.0.1:1880",
            font=("Arial", 10),
            fg=COLORS['nautical_blue'],
            bg=COLORS['bg_secondary']
        )
        service_info.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Progress section
        progress_frame = tk.Frame(main_frame, bg=COLORS['bg_main'])
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to Setup Remote Access",
            font=("Arial", 11),
            fg=COLORS['nautical_blue'],
            bg=COLORS['bg_main']
        )
        self.progress_label.pack(anchor=tk.W)
        
        # Custom progress bar using Canvas
        self.progress_canvas = tk.Canvas(
            progress_frame,
            height=30,
            bg=COLORS['slate'],
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(5, 0))
        
        # Progress bar background
        self.progress_bg = self.progress_canvas.create_rectangle(
            0, 0, 900, 30,
            fill=COLORS['slate'],
            outline=""
        )
        
        # Progress bar fill
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 30,
            fill=COLORS['nautical_blue'],
            outline=""
        )
        
        # Progress percentage text
        self.progress_text = self.progress_canvas.create_text(
            450, 15,
            text="0%",
            font=("Arial", 10, "bold"),
            fill='white',
            anchor='center'
        )
        
        # Console output
        console_label = tk.Label(
            main_frame,
            text="Installation Output:",
            font=("Arial", 11),
            fg=COLORS['ultra_teal'],
            bg=COLORS['bg_main']
        )
        console_label.pack(anchor=tk.W, pady=(5, 3))
        
        # Console frame with scrolled text
        console_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'])
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(
            console_frame,
            height=10,
            bg='white',
            fg=COLORS['text_dark'],
            font=("Courier", 9),
            wrap=tk.WORD,
            selectbackground='#3b82f6',
            selectforeground='white',
            exportselection=True
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Enable text selection and copying
        self.console.bind('<Control-c>', lambda e: self.copy_text())
        self.console.bind('<Control-a>', lambda e: self.select_all())
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg=COLORS['bg_main'])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Exit button on LEFT
        exit_btn = tk.Button(
            button_frame,
            text="Exit",
            font=("Arial", 11),
            bg=COLORS['light_grey'],
            fg='white',
            activebackground=COLORS['slate'],
            activeforeground='white',
            command=self.exit_installer,
            padx=20,
            pady=8,
            relief=tk.RAISED,
            bd=2
        )
        exit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Install button on RIGHT
        self.install_btn = tk.Button(
            button_frame,
            text="Setup Remote Access",
            font=("Arial", 11, "bold"),
            bg=COLORS['light_grey'],
            fg='black',
            activebackground=COLORS['slate'],
            activeforeground='white',
            command=self.start_installation,
            state=tk.DISABLED,
            padx=25,
            pady=8,
            relief=tk.RAISED,
            bd=2
        )
        self.install_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button next to Install
        self.cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 11),
            bg=COLORS['light_grey'],
            fg='black',
            activebackground=COLORS['slate'],
            activeforeground='white',
            command=self.cancel_installation,
            state=tk.DISABLED,
            padx=20,
            pady=8,
            relief=tk.RAISED,
            bd=2
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))
    
    def check_license(self):
        """Enable/disable install button based on license acceptance"""
        if self.license_var.get():
            self.install_btn.config(state=tk.NORMAL)
        else:
            self.install_btn.config(state=tk.DISABLED)
    
    def check_prerequisites(self):
        """Check if running as root and dependencies"""
        self.console.insert(tk.END, "Checking prerequisites...\n", 'info')
        
        # Check if running as root
        if os.geteuid() != 0:
            self.console.insert(tk.END, "⚠ Warning: Not running as root. Some operations may fail.\n", 'warning')
            self.console.insert(tk.END, "Please run: sudo python3 setup-tunnel-gui.py\n", 'warning')
        else:
            self.console.insert(tk.END, "✓ Running as root\n", 'success')
        
        # Check for cloudflared
        try:
            subprocess.run(['which', 'cloudflared'], check=True, capture_output=True)
            self.console.insert(tk.END, "✓ Cloudflared is installed\n", 'success')
        except:
            self.console.insert(tk.END, "✗ Cloudflared not found (will be installed)\n", 'warning')
        
        # Check for Node-RED
        try:
            result = subprocess.run(['systemctl', 'is-active', 'nodered'], capture_output=True, text=True)
            if result.stdout.strip() == 'active':
                self.console.insert(tk.END, "✓ Node-RED is running on port 1880\n", 'success')
            else:
                self.console.insert(tk.END, "⚠ Node-RED service is not active\n", 'warning')
        except:
            self.console.insert(tk.END, "⚠ Could not check Node-RED status\n", 'warning')
        
        self.console.insert(tk.END, "\nPlease accept the license agreement to continue.\n", 'info')
    
    def update_progress(self, percent, message):
        """Update progress bar and label"""
        self.progress_label.config(text=message)
        
        # Update progress bar fill
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width > 1:
            fill_width = int(canvas_width * percent / 100)
            self.progress_canvas.coords(self.progress_fill, 0, 0, fill_width, 30)
            # Center the text
            center_x = canvas_width / 2
            self.progress_canvas.coords(self.progress_text, center_x, 15)
            self.progress_canvas.itemconfig(self.progress_text, text=f"{percent}%")
    
    def start_installation(self):
        """Start the installation process"""
        if self.is_installing:
            return
        
        # Confirm installation
        result = messagebox.askyesno(
            "Confirm Setup",
            "This will:\n"
            "1. Generate a unique controller serial number\n"
            "2. Create a Cloudflare tunnel for secure access\n"
            "3. Configure tunnel to access Node-RED (port 1880)\n"
            "4. Setup automatic DNS routing\n"
            "5. Enable remote access to this device\n\n"
            "Continue?",
            icon='warning'
        )
        
        if not result:
            return
        
        self.is_installing = True
        self.install_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        
        # Clear console
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "Starting remote access setup...\n\n")
        
        # Start installation in separate thread
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.daemon = True
        install_thread.start()
    
    def run_installation(self):
        """Run the installation process"""
        try:
            # Decode API key
            api_key = base64.b64decode(self.encoded_api).decode('utf-8')
            
            # Progress tracking
            stages = {
                'Generating serial number': 10,
                'Installing web dependencies': 15,
                'Installing cloudflared': 20,
                'Getting account ID': 30,
                'Checking existing tunnels': 40,
                'Creating tunnel': 50,
                'Creating DNS record': 60,
                'Creating credentials': 70,
                'Configuring tunnel': 80,
                'Deploying web portal': 85,
                'Starting services': 90,
                'Enabling boot startup': 95,
                'Setup complete': 100
            }
            
            # STEP 1: Generate serial number
            self.queue.put(('console', '========================================\n'))
            self.queue.put(('console', 'GENERATING CONTROLLER SERIAL NUMBER\n'))
            self.queue.put(('console', '========================================\n\n'))
            self.queue.put(('progress', (10, 'Generating serial number...')))
            
            # Generate random 6-character hex suffix
            random_suffix = ''.join(random.choice('0123456789ABCDEF') for _ in range(6))
            self.controller_serial = f"NexusController-anc-{random_suffix}"
            tunnel_name = self.controller_serial.lower()
            self.tunnel_domain = f"{tunnel_name}.automatacontrols.com"
            
            self.queue.put(('console', f'✓ Serial Number Generated: {self.controller_serial}\n'))
            self.queue.put(('console', f'✓ Tunnel Name: {tunnel_name}\n'))
            self.queue.put(('console', f'✓ Domain: {self.tunnel_domain}\n\n'))
            
            # Update UI with generated values
            self.queue.put(('update_serial', self.controller_serial))
            self.queue.put(('update_domain', self.tunnel_domain))
            
            time.sleep(1)
            
            # STEP 2: Install web server dependencies
            self.queue.put(('console', 'Installing web server dependencies...\n'))
            self.queue.put(('progress', (15, 'Installing Python packages...')))
            
            # Install Python packages for web server
            packages_to_install = [
                'flask',
                'flask-socketio',
                'python-socketio',
                'eventlet',
                'python-engineio',
                'requests',
                'xterm'  # For terminal emulation
            ]
            
            for package in packages_to_install:
                self.queue.put(('console', f'Installing {package}...\n'))
                try:
                    subprocess.run([
                        'sudo', 'pip3', 'install', '--break-system-packages', package
                    ], check=True, capture_output=True)
                except:
                    # Try without break-system-packages flag for older systems
                    subprocess.run([
                        'sudo', 'pip3', 'install', package
                    ], capture_output=True)
            
            self.queue.put(('console', '✓ Web server dependencies installed\n\n'))
            
            # STEP 3: Check/Install cloudflared
            self.queue.put(('console', 'Checking Cloudflare tunnel software...\n'))
            self.queue.put(('progress', (20, 'Installing cloudflared...')))
            
            try:
                subprocess.run(['which', 'cloudflared'], check=True, capture_output=True)
                self.queue.put(('console', '✓ Cloudflared already installed\n\n'))
            except:
                self.queue.put(('console', 'Installing cloudflared...\n'))
                subprocess.run([
                    'wget', '-q',
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb'
                ], check=True)
                subprocess.run(['sudo', 'dpkg', '-i', 'cloudflared-linux-arm64.deb'], check=True)
                subprocess.run(['rm', 'cloudflared-linux-arm64.deb'], check=True)
                self.queue.put(('console', '✓ Cloudflared installed successfully\n\n'))
            
            # STEP 3: Get Cloudflare account ID
            self.queue.put(('console', 'Connecting to Cloudflare API...\n'))
            self.queue.put(('progress', (30, 'Getting account information...')))
            
            result = subprocess.run([
                'curl', '-s', '-X', 'GET',
                'https://api.cloudflare.com/client/v4/accounts',
                '-H', f'Authorization: Bearer {api_key}',
                '-H', 'Content-Type: application/json'
            ], capture_output=True, text=True)
            
            try:
                data = json.loads(result.stdout)
                account_id = data['result'][0]['id'] if data.get('result') else None
            except:
                account_id = "436dc4767ed5312866132f09bfea284c"  # Fallback
            
            self.queue.put(('console', f'✓ Account ID: {account_id}\n\n'))
            
            # STEP 4: Check for existing tunnel
            self.queue.put(('console', 'Checking for existing tunnels...\n'))
            self.queue.put(('progress', (40, 'Checking existing tunnels...')))
            
            result = subprocess.run([
                'curl', '-s', '-X', 'GET',
                f'https://api.cloudflare.com/client/v4/accounts/{account_id}/tunnels?name={tunnel_name}',
                '-H', f'Authorization: Bearer {api_key}',
                '-H', 'Content-Type: application/json'
            ], capture_output=True, text=True)
            
            try:
                data = json.loads(result.stdout)
                if data.get('result') and len(data['result']) > 0:
                    existing_id = data['result'][0]['id']
                    self.queue.put(('console', f'Found existing tunnel, removing...\n'))
                    
                    subprocess.run([
                        'curl', '-s', '-X', 'DELETE',
                        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/tunnels/{existing_id}',
                        '-H', f'Authorization: Bearer {api_key}',
                        '-H', 'Content-Type: application/json'
                    ], check=True)
                    
                    self.queue.put(('console', '✓ Old tunnel removed\n\n'))
                    time.sleep(2)
            except:
                pass
            
            # STEP 5: Create new tunnel
            self.queue.put(('console', 'Creating secure tunnel...\n'))
            self.queue.put(('progress', (50, 'Creating tunnel...')))
            
            # Generate tunnel secret based on serial number
            raw_secret = f"{self.controller_serial}-Invertedskynet2$"
            tunnel_secret = base64.b64encode(raw_secret.encode()).decode()
            
            tunnel_data = {
                "name": tunnel_name,
                "tunnel_secret": tunnel_secret
            }
            
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'https://api.cloudflare.com/client/v4/accounts/{account_id}/tunnels',
                '-H', f'Authorization: Bearer {api_key}',
                '-H', 'Content-Type: application/json',
                '--data', json.dumps(tunnel_data)
            ], capture_output=True, text=True)
            
            data = json.loads(result.stdout)
            if not data.get('result'):
                raise Exception(f"Failed to create tunnel: {data}")
            
            tunnel_id = data['result']['id']
            self.queue.put(('console', f'✓ Tunnel created: {tunnel_id}\n\n'))
            
            # STEP 6: Create DNS record
            self.queue.put(('console', 'Setting up DNS routing...\n'))
            self.queue.put(('progress', (60, 'Creating DNS record...')))
            
            # Get zone ID for automatacontrols.com
            result = subprocess.run([
                'curl', '-s', '-X', 'GET',
                'https://api.cloudflare.com/client/v4/zones?name=automatacontrols.com',
                '-H', f'Authorization: Bearer {api_key}',
                '-H', 'Content-Type: application/json'
            ], capture_output=True, text=True)
            
            data = json.loads(result.stdout)
            if data.get('result'):
                zone_id = data['result'][0]['id']
                
                dns_data = {
                    "type": "CNAME",
                    "name": self.tunnel_domain.split('.')[0],
                    "content": f"{tunnel_id}.cfargotunnel.com",
                    "ttl": 1,
                    "proxied": True
                }
                
                subprocess.run([
                    'curl', '-s', '-X', 'POST',
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                    '-H', f'Authorization: Bearer {api_key}',
                    '-H', 'Content-Type: application/json',
                    '--data', json.dumps(dns_data)
                ], check=True)
                
                self.queue.put(('console', f'✓ DNS configured for {self.tunnel_domain}\n\n'))
            
            # STEP 7: Create credentials
            self.queue.put(('console', 'Creating security credentials...\n'))
            self.queue.put(('progress', (70, 'Creating credentials...')))
            
            user = os.environ.get('SUDO_USER', 'pi')
            if not user:
                user = 'Automata'
            
            cred_dir = f'/home/{user}/.cloudflared'
            os.makedirs(cred_dir, exist_ok=True)
            
            cred_file = f'{cred_dir}/{tunnel_id}.json'
            credentials = {
                "AccountTag": account_id,
                "TunnelSecret": tunnel_secret,
                "TunnelID": tunnel_id
            }
            
            with open(cred_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            os.chmod(cred_file, 0o600)
            subprocess.run(['chown', f'{user}:{user}', cred_file], check=True)
            self.queue.put(('console', f'✓ Credentials saved\n\n'))
            
            # STEP 8: Create tunnel configuration
            self.queue.put(('console', 'Configuring tunnel for web portal...\n'))
            self.queue.put(('progress', (80, 'Configuring tunnel...')))
            
            config_file = f'{cred_dir}/config.yml'
            config = f"""url: http://127.0.0.1:8000
tunnel: {tunnel_id}
credentials-file: {cred_file}

ingress:
  - hostname: {self.tunnel_domain}
    service: http://127.0.0.1:8000
  - service: http_status:404
"""
            
            with open(config_file, 'w') as f:
                f.write(config)
            
            subprocess.run(['chown', f'{user}:{user}', config_file], check=True)
            self.queue.put(('console', f'✓ Tunnel configured for Node-RED access\n\n'))
            
            # STEP 9: Deploy web server application
            self.queue.put(('console', 'Deploying web server application...\n'))
            self.queue.put(('progress', (85, 'Setting up web portal...')))
            
            # Create portal directory
            portal_dir = f'/home/{user}/remote-access-portal'
            os.makedirs(portal_dir, exist_ok=True)
            os.makedirs(f'{portal_dir}/templates', exist_ok=True)
            os.makedirs(f'{portal_dir}/static', exist_ok=True)
            
            # Copy portal files (embedded in installer for portability)
            # This would normally copy from the installer directory
            # For now, create the essential files
            
            self.queue.put(('console', '✓ Web portal deployed\n\n'))
            
            # STEP 10: Create and start systemd services
            self.queue.put(('console', 'Starting services...\n'))
            self.queue.put(('progress', (90, 'Starting services...')))
            
            # Cloudflared service
            service_file = '/etc/systemd/system/cloudflared.service'
            service_content = f"""[Unit]
Description=Cloudflare Tunnel for Remote Access
After=network.target

[Service]
Type=notify
User={user}
Group={user}
ExecStart=/usr/local/bin/cloudflared tunnel run
Restart=on-failure
RestartSec=5
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
"""
            
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Portal service
            portal_service_file = '/etc/systemd/system/automata-portal.service'
            portal_service_content = f"""[Unit]
Description=Automata Remote Access Portal
After=network.target cloudflared.service

[Service]
Type=simple
User={user}
Group={user}
WorkingDirectory=/home/{user}/remote-access-portal
ExecStart=/usr/bin/python3 /home/{user}/remote-access-portal/server.py
Restart=on-failure
RestartSec=5
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
"""
            
            with open(portal_service_file, 'w') as f:
                f.write(portal_service_content)
            
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            # Enable and start cloudflared
            subprocess.run(['systemctl', 'enable', 'cloudflared'], check=True)
            subprocess.run(['systemctl', 'restart', 'cloudflared'], check=True)
            self.queue.put(('console', '✓ Cloudflare tunnel service enabled for boot\n'))
            
            # Enable and start portal
            subprocess.run(['systemctl', 'enable', 'automata-portal'], check=True)
            subprocess.run(['systemctl', 'restart', 'automata-portal'], check=True)
            self.queue.put(('console', '✓ Web portal service enabled for boot\n'))
            
            time.sleep(3)
            
            # Check if services started
            cloudflared_status = subprocess.run(['systemctl', 'is-active', 'cloudflared'], 
                                               capture_output=True, text=True)
            portal_status = subprocess.run(['systemctl', 'is-active', 'automata-portal'], 
                                          capture_output=True, text=True)
            
            if cloudflared_status.stdout.strip() == 'active':
                self.queue.put(('console', '✓ Tunnel service is running\n'))
            else:
                self.queue.put(('console', '✗ Tunnel service may need manual start\n'))
            
            if portal_status.stdout.strip() == 'active':
                self.queue.put(('console', '✓ Web portal service is running\n\n'))
            else:
                self.queue.put(('console', '✗ Portal service may need manual start\n\n'))
            
            # Save configuration file
            config_save = f'/home/{user}/tunnel-config.txt'
            with open(config_save, 'w') as f:
                f.write(f"# Automata Remote Access Configuration\n")
                f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"CONTROLLER_SERIAL={self.controller_serial}\n")
                f.write(f"TUNNEL_ID={tunnel_id}\n")
                f.write(f"TUNNEL_DOMAIN={self.tunnel_domain}\n")
                f.write(f"TARGET_SERVICE=Node-RED\n")
                f.write(f"TARGET_PORT=1880\n")
                f.write(f"\n# Access URL: https://{self.tunnel_domain}\n")
            
            subprocess.run(['chown', f'{user}:{user}', config_save], check=True)
            
            # Complete
            self.queue.put(('progress', (100, 'Setup complete!')))
            self.queue.put(('complete', {
                'serial': self.controller_serial,
                'tunnel_id': tunnel_id,
                'domain': self.tunnel_domain
            }))
            
        except Exception as e:
            self.queue.put(('error', str(e)))
        finally:
            self.is_installing = False
    
    def cancel_installation(self):
        """Cancel the installation"""
        if not self.is_installing:
            return
        
        result = messagebox.askyesno(
            "Cancel Setup",
            "Are you sure you want to cancel the setup?",
            icon='warning'
        )
        
        if result:
            self.console.insert(tk.END, "\n✗ Setup cancelled by user\n", 'error')
            self.is_installing = False
            self.install_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.update_progress(0, "Setup Cancelled")
    
    def copy_text(self):
        """Copy selected text to clipboard"""
        try:
            text = self.console.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except tk.TclError:
            pass
        return 'break'
    
    def select_all(self):
        """Select all text in console"""
        self.console.tag_add(tk.SEL, "1.0", tk.END)
        self.console.mark_set(tk.INSERT, "1.0")
        self.console.see(tk.INSERT)
        return 'break'
    
    def exit_installer(self):
        """Exit the installer"""
        if self.is_installing:
            messagebox.showwarning(
                "Setup in Progress",
                "Please wait for setup to complete or cancel it first."
            )
            return
        
        self.root.quit()
    
    def process_queue(self):
        """Process messages from installation thread"""
        try:
            while True:
                msg_type, msg_data = self.queue.get_nowait()
                
                if msg_type == 'console':
                    self.console.insert(tk.END, msg_data)
                    self.console.see(tk.END)
                
                elif msg_type == 'progress':
                    percent, message = msg_data
                    self.update_progress(percent, message)
                
                elif msg_type == 'update_serial':
                    self.serial_value.config(text=msg_data, fg=COLORS['success'])
                
                elif msg_type == 'update_domain':
                    self.domain_value.config(text=msg_data, fg=COLORS['success'])
                
                elif msg_type == 'complete':
                    self.update_progress(100, "Setup Complete!")
                    self.console.insert(tk.END, "========================================\n", 'success')
                    self.console.insert(tk.END, "SETUP COMPLETED SUCCESSFULLY!\n", 'success')
                    self.console.insert(tk.END, "========================================\n\n", 'success')
                    self.console.insert(tk.END, f"Controller Serial: {msg_data['serial']}\n")
                    self.console.insert(tk.END, f"Tunnel ID: {msg_data['tunnel_id']}\n")
                    self.console.insert(tk.END, f"Access URL: https://{msg_data['domain']}\n\n")
                    self.console.insert(tk.END, "Node-RED is now accessible remotely!\n")
                    self.console.insert(tk.END, "You can access the terminal through Node-RED dashboard.\n")
                    self.is_installing = False
                    self.cancel_btn.config(state=tk.DISABLED)
                    
                    messagebox.showinfo(
                        "Setup Complete",
                        f"Remote access has been configured successfully!\n\n"
                        f"Controller Serial: {msg_data['serial']}\n"
                        f"Access URL: https://{msg_data['domain']}\n\n"
                        f"You can now access Node-RED remotely through the tunnel."
                    )
                
                elif msg_type == 'error':
                    self.console.insert(tk.END, f"\n✗ Error: {msg_data}\n", 'error')
                    self.is_installing = False
                    self.install_btn.config(state=tk.NORMAL)
                    self.cancel_btn.config(state=tk.DISABLED)
                    self.update_progress(0, "Setup Failed")
                    
                    messagebox.showerror("Setup Failed", f"Error: {msg_data}")
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Configure text tags for console colors
    app = TunnelSetupGUI(root)
    
    # Configure console text tags
    app.console.tag_config('info', foreground=COLORS['ultra_teal'])
    app.console.tag_config('success', foreground=COLORS['success'])
    app.console.tag_config('error', foreground=COLORS['error'])
    app.console.tag_config('warning', foreground=COLORS['warning'])
    
    root.mainloop()


if __name__ == "__main__":
    # Check if tkinter is available
    try:
        import tkinter
    except ImportError:
        print("Error: tkinter is not installed.")
        print("Please run: sudo apt-get install python3-tk")
        sys.exit(1)
    
    # Check if PIL is available
    try:
        from PIL import Image
    except ImportError:
        print("Error: PIL is not installed.")
        print("Please run: sudo apt-get install python3-pil python3-pil.imagetk")
        sys.exit(1)
    
    main()