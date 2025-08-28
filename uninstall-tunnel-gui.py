#!/usr/bin/env python3
"""
AutomataControls™ Tunnel Uninstaller GUI
Removes Portal & Cloudflare Tunnel Configuration
Copyright © 2024 AutomataNexus, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL
Version: 2.0.0
"""

import subprocess
import sys
import os

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

import threading
import time
import queue

# Color scheme - Ultra light mint theme (matching installer)
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

class TunnelUninstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automata Tunnel Uninstaller")
        
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
        
        # Uninstallation state
        self.is_uninstalling = False
        self.process = None
        
        self.create_main_interface()
    
    def create_main_interface(self):
        """Create the main interface"""
        # Main container
        main_container = tk.Frame(self.root, bg=COLORS['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg=COLORS['bg_main'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="AUTOMATA TUNNEL UNINSTALLER",
            font=('Helvetica', 28, 'bold'),
            fg=COLORS['error'],
            bg=COLORS['bg_main']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Complete Removal of Portal & Cloudflare Tunnel",
            font=('Helvetica', 14),
            fg=COLORS['text_mid'],
            bg=COLORS['bg_main']
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Warning Frame
        warning_frame = tk.Frame(main_container, bg='#fef2f2', relief=tk.RAISED, bd=1)
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_title = tk.Label(
            warning_frame,
            text="⚠️ WARNING - COMPLETE REMOVAL",
            font=("Arial", 14, "bold"),
            fg=COLORS['error'],
            bg='#fef2f2'
        )
        warning_title.pack(pady=(10, 5))
        
        warning_text = tk.Label(
            warning_frame,
            text="This uninstaller will permanently remove:\n\n"
                 "• Node.js Portal Server and all files\n"
                 "• Nginx configuration and SSL certificates\n"
                 "• Node-RED installation (if installed by our installer)\n"
                 "• Cloudflare tunnel and all configurations\n"
                 "• All systemd services (portal, nodered, cloudflared)\n\n"
                 "This action CANNOT be undone!",
            font=("Arial", 11),
            fg=COLORS['text_dark'],
            bg='#fef2f2',
            justify=tk.CENTER
        )
        warning_text.pack(pady=(0, 10))
        
        # Commercial License Frame
        license_frame = tk.Frame(main_container, bg=COLORS['bg_secondary'], relief=tk.RAISED, bd=1)
        license_frame.pack(fill=tk.X, pady=(0, 20))
        
        license_text = tk.Label(
            license_frame,
            text="© 2025 AutomataNexus AI & AutomataControls | Author: Andrew Jewell Sr.\n"
                 "Commercial Software - Uninstallation",
            font=("Arial", 9),
            fg=COLORS['text_mid'],
            bg=COLORS['bg_secondary'],
            justify=tk.CENTER
        )
        license_text.pack(pady=5)
        
        # Content area
        content_frame = tk.Frame(main_container, bg=COLORS['bg_secondary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Components to remove checklist
        left_frame = tk.Frame(content_frame, bg=COLORS['bg_secondary'], padx=30, pady=30)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        checklist_label = tk.Label(
            left_frame,
            text="COMPONENTS TO REMOVE",
            font=('Helvetica', 12, 'bold'),
            fg=COLORS['error'],
            bg=COLORS['bg_secondary']
        )
        checklist_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Create checkboxes for what to remove
        self.remove_portal = tk.BooleanVar(value=True)
        self.remove_nginx = tk.BooleanVar(value=True)
        self.remove_nodered = tk.BooleanVar(value=True)
        self.remove_tunnel = tk.BooleanVar(value=True)
        self.remove_nodejs = tk.BooleanVar(value=False)  # Default false, might be used by other apps
        
        components = [
            (self.remove_portal, "Portal Server (terminal-server.js and dependencies)"),
            (self.remove_nginx, "Nginx configuration and SSL certificates"),
            (self.remove_nodered, "Node-RED automation platform"),
            (self.remove_tunnel, "Cloudflare tunnel and configurations"),
            (self.remove_nodejs, "Node.js and npm (WARNING: May affect other applications)")
        ]
        
        for var, text in components:
            check = tk.Checkbutton(
                left_frame,
                text=text,
                variable=var,
                font=('Helvetica', 10),
                fg=COLORS['text_dark'],
                bg=COLORS['bg_secondary'],
                selectcolor=COLORS['bg_accent'],
                activebackground=COLORS['bg_secondary']
            )
            check.pack(anchor=tk.W, pady=2)
            if var == self.remove_nodejs:
                check.config(fg=COLORS['warning'])
        
        # Confirmation checkbox
        confirm_frame = tk.Frame(left_frame, bg='#fef2f2', relief=tk.RAISED, bd=1)
        confirm_frame.pack(fill=tk.X, pady=(30, 20))
        
        self.confirm_var = tk.BooleanVar()
        self.confirm_check = tk.Checkbutton(
            confirm_frame,
            text="I understand this will permanently remove all selected components",
            variable=self.confirm_var,
            font=("Arial", 10, "bold"),
            fg=COLORS['error'],
            bg='#fef2f2',
            selectcolor='#fef2f2',
            activebackground='#fef2f2',
            command=self.check_confirmation
        )
        self.confirm_check.pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(left_frame, bg=COLORS['bg_secondary'])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.uninstall_btn = self.create_button(
            button_frame, "UNINSTALL", 
            self.start_uninstallation, COLORS['error']
        )
        self.uninstall_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.uninstall_btn.config(state='disabled')  # Disabled until confirmed
        
        self.cancel_btn = self.create_button(
            button_frame, "CANCEL", 
            self.root.quit, COLORS['slate']
        )
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Right column - Output
        right_frame = tk.Frame(content_frame, bg=COLORS['bg_accent'], padx=30, pady=30)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Output section header
        output_label = tk.Label(
            right_frame,
            text="UNINSTALLATION LOG",
            font=('Helvetica', 12, 'bold'),
            fg=COLORS['error'],
            bg=COLORS['bg_accent']
        )
        output_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            right_frame,
            mode='indeterminate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Configure progress bar style
        style = ttk.Style()
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=COLORS['error'],
            troughcolor=COLORS['bg_main'],
            bordercolor=COLORS['slate'],
            lightcolor=COLORS['error'],
            darkcolor=COLORS['error']
        )
        
        # Output text area
        text_frame = tk.Frame(right_frame, bg=COLORS['slate'], bd=1)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            text_frame,
            font=('Courier', 10),
            bg=COLORS['bg_main'],
            fg=COLORS['text_dark'],
            wrap=tk.WORD,
            bd=0
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    def create_button(self, parent, text, command, color):
        """Create a styled button"""
        btn = tk.Button(
            parent,
            text=text,
            font=('Helvetica', 10, 'bold'),
            bg=color,
            fg='white',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=command
        )
        return btn
    
    def check_confirmation(self):
        """Enable/disable uninstall button based on confirmation"""
        if self.confirm_var.get():
            self.uninstall_btn.config(state='normal')
        else:
            self.uninstall_btn.config(state='disabled')
        
    def log_output(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
        
    def run_command(self, command, description=""):
        """Run a shell command and capture output"""
        if description:
            self.log_output(f"\n{description}...")
            
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self.log_output(line.strip())
                
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log_output(f"Error: {str(e)}")
            return False
            
    def uninstallation_thread(self):
        """Main uninstallation process"""
        try:
            self.progress.start()
            self.uninstall_btn.config(state='disabled')
            self.cancel_btn.config(state='disabled')
            
            self.log_output("=" * 60)
            self.log_output("Starting uninstallation process...")
            self.log_output("=" * 60)
            
            # Stop services first
            self.log_output("\n▶ Stopping services...")
            services = ["portal", "nodered", "cloudflared", "nginx"]
            for service in services:
                self.run_command(f"sudo systemctl stop {service} 2>/dev/null", f"Stopping {service}")
                self.run_command(f"sudo systemctl disable {service} 2>/dev/null", f"Disabling {service}")
            
            # Remove Cloudflare tunnel if selected
            if self.remove_tunnel.get():
                self.log_output("\n▶ Removing Cloudflare tunnel...")
                
                # List and delete tunnels
                self.run_command(
                    "cloudflared tunnel list 2>/dev/null | grep -v 'ID' | awk '{print $1}' | xargs -I {} cloudflared tunnel delete {} 2>/dev/null",
                    "Deleting Cloudflare tunnels"
                )
                
                # Remove tunnel configurations
                self.run_command("rm -rf /home/Automata/.cloudflared", "Removing tunnel configurations")
                self.run_command("sudo rm -f /etc/systemd/system/cloudflared.service", "Removing tunnel service")
                
                # Uninstall cloudflared
                self.run_command("sudo apt-get remove -y cloudflared", "Uninstalling cloudflared")
            
            # Remove portal if selected
            if self.remove_portal.get():
                self.log_output("\n▶ Removing Portal Server...")
                self.run_command("sudo rm -rf /home/Automata/LegacyIntegration/remote-access-portal", "Removing portal files")
                self.run_command("sudo rm -f /etc/systemd/system/portal.service", "Removing portal service")
            
            # Remove Nginx configuration if selected
            if self.remove_nginx.get():
                self.log_output("\n▶ Removing Nginx configuration...")
                self.run_command("sudo rm -f /etc/nginx/sites-enabled/portal", "Removing site config")
                self.run_command("sudo rm -f /etc/nginx/sites-available/portal", "Removing site available")
                self.run_command("sudo rm -rf /etc/nginx/ssl", "Removing SSL certificates")
                self.run_command("sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/", "Restoring default site")
                self.run_command("sudo systemctl restart nginx", "Restarting nginx")
            
            # Remove Node-RED if selected
            if self.remove_nodered.get():
                self.log_output("\n▶ Removing Node-RED...")
                self.run_command("sudo npm uninstall -g node-red", "Uninstalling Node-RED")
                self.run_command("sudo rm -rf /home/Automata/.node-red", "Removing Node-RED data")
                self.run_command("sudo rm -f /etc/systemd/system/nodered.service", "Removing Node-RED service")
            
            # Remove Node.js if selected (with extra warning)
            if self.remove_nodejs.get():
                response = messagebox.askyesno(
                    "Confirm Node.js Removal",
                    "Are you SURE you want to remove Node.js?\n\n"
                    "This may affect other applications on your system!"
                )
                
                if response:
                    self.log_output("\n▶ Removing Node.js...")
                    self.run_command("sudo apt-get remove -y nodejs npm", "Uninstalling Node.js and npm")
                    self.run_command("sudo apt-get autoremove -y", "Removing dependencies")
                else:
                    self.log_output("\n▶ Skipping Node.js removal (user cancelled)")
            
            # Clean up systemd
            self.log_output("\n▶ Cleaning up system...")
            self.run_command("sudo systemctl daemon-reload", "Reloading systemd")
            
            # Remove installer scripts
            self.log_output("\n▶ Removing installer scripts...")
            self.run_command("rm -f /home/Automata/LegacyIntegration/setup-tunnel.sh", "Removing CLI installer")
            self.run_command("rm -f /home/Automata/LegacyIntegration/setup-tunnel-gui.py", "Removing GUI installer")
            
            self.log_output("\n" + "=" * 60)
            self.log_output("✓ Uninstallation completed successfully!")
            self.log_output("=" * 60)
            self.log_output("\nAll selected components have been removed.")
            self.log_output("You may need to restart your system for all changes to take effect.")
            
            messagebox.showinfo(
                "Uninstallation Complete", 
                "All selected components have been successfully removed.\n\n"
                "Please restart your system if needed."
            )
            
        except Exception as e:
            self.log_output(f"\n✗ Uninstallation failed: {str(e)}")
            messagebox.showerror("Error", f"Uninstallation failed:\n{str(e)}")
        finally:
            self.progress.stop()
            self.cancel_btn.config(state='normal', text="CLOSE")
            
    def start_uninstallation(self):
        """Start uninstallation in a separate thread"""
        response = messagebox.askyesno(
            "Final Confirmation",
            "Are you absolutely sure you want to uninstall?\n\n"
            "This will permanently remove all selected components and cannot be undone!"
        )
        
        if response:
            thread = threading.Thread(target=self.uninstallation_thread)
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = TunnelUninstallerGUI(root)
    root.mainloop()