#!/usr/bin/env python3

"""
FreeRDP GUI - A simple GTK+ interface for xfreerdp on Linux
Copyright (c) 2024

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import subprocess
import threading
import os
import shutil
import json
import tempfile
import signal
import re

# Check if keyring module is available
try:
    import keyring
    # Try to detect and avoid KDE Wallet if it's causing issues
    backend = keyring.get_keyring()
    backend_name = backend.__class__.__name__.lower()
    
    # If KDE Wallet is detected and we're not on KDE, try to use Secret Service
    if 'kde' in backend_name or 'kwallet' in backend_name:
        try:
            # Try to force SecretService backend for GNOME/XFCE
            from keyring.backends import SecretService
            keyring.set_keyring(SecretService.Keyring())
            KEYRING_AVAILABLE = True
        except:
            # If we can't set SecretService, disable keyring to avoid KDE Wallet popups
            KEYRING_AVAILABLE = False
            print("KDE Wallet detected but not available. Using file storage instead.")
    else:
        KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
except Exception:
    # Any other keyring initialization error - disable it
    KEYRING_AVAILABLE = False
    print("Keyring initialization failed. Using file storage instead.")

class RDPManager(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="FreeRDP GUI")
        self.set_border_width(20)
        self.set_default_size(500, 400)
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b><big>FreeRDP Connection Manager</big></b>")
        vbox.pack_start(title_label, False, False, 0)
        
        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 0)
        
        # Connection details frame
        conn_frame = Gtk.Frame(label="Connection Details")
        vbox.pack_start(conn_frame, False, False, 0)
        
        conn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        conn_box.set_border_width(10)
        conn_frame.add(conn_box)
        
        # Hostname field
        hostname_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        conn_box.pack_start(hostname_box, False, False, 0)
        
        hostname_label = Gtk.Label(label="Computer:")
        hostname_label.set_size_request(100, -1)
        hostname_label.set_xalign(0)
        hostname_box.pack_start(hostname_label, False, False, 0)
        
        self.hostname_entry = Gtk.Entry()
        self.hostname_entry.set_placeholder_text("hostname or IP address")
        self.hostname_entry.connect("changed", self.on_hostname_changed)
        hostname_box.pack_start(self.hostname_entry, True, True, 0)
        
        # Username field
        username_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        conn_box.pack_start(username_box, False, False, 0)
        
        username_label = Gtk.Label(label="Username:")
        username_label.set_size_request(100, -1)
        username_label.set_xalign(0)
        username_box.pack_start(username_label, False, False, 0)
        
        self.username_entry = Gtk.Entry()
        self.username_entry.set_placeholder_text("domain\\username or username")
        username_box.pack_start(self.username_entry, True, True, 0)
        
        # Domain field (optional)
        domain_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        conn_box.pack_start(domain_box, False, False, 0)
        
        domain_label = Gtk.Label(label="Domain:")
        domain_label.set_size_request(100, -1)
        domain_label.set_xalign(0)
        domain_box.pack_start(domain_label, False, False, 0)
        
        self.domain_entry = Gtk.Entry()
        self.domain_entry.set_placeholder_text("(optional)")
        domain_box.pack_start(self.domain_entry, True, True, 0)
        
        # Control buttons frame
        control_frame = Gtk.Frame(label="Connection Control")
        vbox.pack_start(control_frame, False, False, 0)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_border_width(10)
        control_frame.add(button_box)
        
        # Connect button
        self.connect_button = Gtk.Button(label="Connect")
        self.connect_button.connect("clicked", self.on_connect_clicked)
        button_box.pack_start(self.connect_button, True, True, 0)
        
        # Advanced options button
        self.advanced_button = Gtk.Button(label="Advanced Options")
        self.advanced_button.connect("clicked", self.show_advanced_options)
        button_box.pack_start(self.advanced_button, True, True, 0)
        
        # Recent connections frame
        recent_frame = Gtk.Frame(label="Recent Connections")
        vbox.pack_start(recent_frame, True, True, 0)
        
        # List box for recent connections
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_border_width(10)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        recent_frame.add(scrolled_window)
        
        self.recent_listbox = Gtk.ListBox()
        self.recent_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.recent_listbox.connect("row-selected", self.on_recent_selected)
        scrolled_window.add(self.recent_listbox)
        
        # Add menu bar
        menubar = Gtk.MenuBar()
        vbox.pack_start(menubar, False, False, 0)
        vbox.reorder_child(menubar, 0)  # Move to top
        
        # Tools menu
        tools_menu = Gtk.Menu()
        tools_item = Gtk.MenuItem(label="Tools")
        tools_item.set_submenu(tools_menu)
        menubar.append(tools_item)
        
        # Install FreeRDP menu item
        install_item = Gtk.MenuItem(label="Install FreeRDP...")
        install_item.connect("activate", self.show_install_dialog)
        tools_menu.append(install_item)
        
        # Install Keyring menu item
        keyring_item = Gtk.MenuItem(label="Install Keyring Support...")
        keyring_item.connect("activate", self.show_keyring_install_dialog)
        tools_menu.append(keyring_item)
        
        # Separator
        tools_menu.append(Gtk.SeparatorMenuItem())
        
        # Clear saved passwords
        clear_pw_item = Gtk.MenuItem(label="Clear Saved Passwords...")
        clear_pw_item.connect("activate", self.clear_saved_passwords)
        tools_menu.append(clear_pw_item)
        
        # Identify monitors
        identify_item = Gtk.MenuItem(label="Identify Monitors...")
        identify_item.connect("activate", self.identify_monitors)
        tools_menu.append(identify_item)
        
        # Toggle keyring support
        self.keyring_toggle_item = Gtk.CheckMenuItem(label="Use System Keyring")
        self.keyring_toggle_item.set_active(KEYRING_AVAILABLE)
        self.keyring_toggle_item.connect("toggled", self.toggle_keyring_support)
        tools_menu.append(self.keyring_toggle_item)
        
        # Initialize
        self.current_process = None
        self.config_file = os.path.expanduser("~/.config/rdp2gui/config.json")
        self.credentials_file = os.path.expanduser("~/.config/rdp2gui/credentials.json")
        self.use_keyring = KEYRING_AVAILABLE
        
        # Load configuration
        self.config = self.load_config()
        self.stored_credentials = self.load_credentials()
        
        # Load recent connections
        self.load_recent_connections()
        
        # Check if xfreerdp is installed
        if not self.check_freerdp_installed():
            GLib.idle_add(self.show_install_prompt)
    
    def check_freerdp_installed(self):
        """Check if xfreerdp is installed"""
        return shutil.which("xfreerdp") is not None or shutil.which("xfreerdp3") is not None
    
    def get_freerdp_command(self):
        """Get the correct freerdp command"""
        if shutil.which("xfreerdp3"):
            return "xfreerdp3"
        elif shutil.which("xfreerdp"):
            return "xfreerdp"
        return None
    
    def on_hostname_changed(self, widget):
        """Handle hostname change to load saved settings"""
        hostname = self.hostname_entry.get_text().strip()
        if hostname in self.config.get("connections", {}):
            conn_data = self.config["connections"][hostname]
            # Load saved username and domain
            if "username" in conn_data:
                self.username_entry.set_text(conn_data["username"])
            if "domain" in conn_data:
                self.domain_entry.set_text(conn_data["domain"])
    
    def on_connect_clicked(self, widget):
        """Handle connect button click"""
        hostname = self.hostname_entry.get_text().strip()
        username = self.username_entry.get_text().strip()
        domain = self.domain_entry.get_text().strip()
        
        if not hostname:
            self.show_error("Please enter a hostname or IP address")
            return
        
        if not username:
            self.show_error("Please enter a username")
            return
        
        # Get stored password if available
        stored_pass = self.get_password_for_connection(hostname, username)
        
        # Show password dialog
        self.show_password_dialog(hostname, username, domain, stored_pass)
    
    def show_password_dialog(self, hostname, username, domain, stored_pass=None):
        """Show password entry dialog"""
        dialog = Gtk.Dialog(
            title="Enter Password",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_CONNECT, Gtk.ResponseType.OK
        )
        
        dialog.set_default_size(400, 200)
        
        content_area = dialog.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        content_area.add(vbox)
        
        # Info label
        info_text = f"<b>Enter password for {username}@{hostname}</b>"
        info_label = Gtk.Label()
        info_label.set_markup(info_text)
        vbox.pack_start(info_label, False, False, 0)
        
        # Password field
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(password_box, False, False, 0)
        
        password_label = Gtk.Label(label="Password:")
        password_label.set_size_request(100, -1)
        password_label.set_xalign(0)
        password_box.pack_start(password_label, False, False, 0)
        
        password_entry = Gtk.Entry()
        password_entry.set_visibility(False)
        password_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        password_box.pack_start(password_entry, True, True, 0)
        
        # Pre-fill stored password if available
        if stored_pass:
            password_entry.set_text(stored_pass)
        
        # Remember checkbox
        remember_check = Gtk.CheckButton(label="Save password (stored securely)")
        remember_check.set_active(bool(stored_pass))
        vbox.pack_start(remember_check, False, False, 0)
        
        # Security note
        if KEYRING_AVAILABLE and self.use_keyring:
            security_text = "Password will be stored in your system keyring"
        else:
            security_text = "Password will be stored locally (encrypted)"
        
        security_label = Gtk.Label()
        security_label.set_markup(f"<small><i>{security_text}</i></small>")
        vbox.pack_start(security_label, False, False, 0)
        
        dialog.show_all()
        password_entry.grab_focus()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            password = password_entry.get_text()
            remember = remember_check.get_active()
            
            dialog.destroy()
            
            if password:
                # Save password if requested
                if remember:
                    self.save_password(hostname, username, password)
                
                # Save connection info
                self.save_connection_info(hostname, username, domain)
                
                # Start RDP connection
                self.start_rdp_connection(hostname, username, domain, password)
            else:
                self.show_error("Password is required")
        else:
            dialog.destroy()
    
    def start_rdp_connection(self, hostname, username, domain, password):
        """Start the RDP connection using xfreerdp"""
        freerdp_cmd = self.get_freerdp_command()
        if not freerdp_cmd:
            self.show_error("FreeRDP is not installed")
            return
        
        # Build command
        cmd = [freerdp_cmd]
        
        # Add hostname
        cmd.extend([f"/v:{hostname}"])
        
        # Add username
        if domain:
            cmd.extend([f"/u:{username}", f"/d:{domain}"])
        else:
            cmd.extend([f"/u:{username}"])
        
        # Add password
        cmd.extend([f"/p:{password}"])
        
        # Get advanced options for this host
        advanced_opts = self.get_advanced_options(hostname)
        
        # Apply advanced options
        if advanced_opts.get("fullscreen", True):
            cmd.append("/f")
        else:
            # Use specified resolution if not fullscreen
            resolution = advanced_opts.get("resolution", "1920x1080")
            cmd.extend([f"/size:{resolution}"])
        
        # Multi-monitor support
        if advanced_opts.get("multimon", False):
            cmd.append("/multimon")
            
            # Specific monitors if selected
            selected_monitors = advanced_opts.get("selected_monitors", [])
            if selected_monitors:
                monitors_str = ",".join(str(m) for m in selected_monitors)
                cmd.extend([f"/monitors:{monitors_str}"])
        
        # Performance flags
        if advanced_opts.get("disable_fonts", True):
            cmd.append("-fonts")
        if advanced_opts.get("disable_wallpaper", True):
            cmd.append("-wallpaper")
        if advanced_opts.get("disable_themes", True):
            cmd.append("-themes")
        if advanced_opts.get("disable_aero", True):
            cmd.append("-aero")
        if advanced_opts.get("disable_drag", True):
            cmd.append("-window-drag")
        
        # Audio
        audio_mode = advanced_opts.get("audio_mode", "local")
        if audio_mode == "local":
            cmd.append("/sound:sys:alsa")
        elif audio_mode == "remote":
            cmd.append("/audio-mode:1")
        elif audio_mode == "disabled":
            cmd.append("/audio-mode:2")
        
        # Clipboard
        if advanced_opts.get("clipboard", True):
            cmd.append("+clipboard")
        
        # Drive redirection
        if advanced_opts.get("redirect_drives", False):
            home_dir = os.path.expanduser("~")
            cmd.extend([f"/drive:home,{home_dir}"])
        
        # Certificate acceptance
        cmd.append("/cert-ignore")
        
        # Network level authentication
        if advanced_opts.get("nla", True):
            cmd.append("/sec:nla")
        else:
            cmd.append("/sec:rdp")
        
        # Compression
        if advanced_opts.get("compression", True):
            cmd.append("+compression")
        
        # Start the RDP session
        try:
            # Run xfreerdp in a new process
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Show connection window
            self.show_connection_window(hostname, username)
            
        except Exception as e:
            self.show_error(f"Failed to start RDP connection: {str(e)}")
    
    def show_connection_window(self, hostname, username):
        """Show a window indicating active connection"""
        dialog = Gtk.Dialog(
            title=f"Connected to {hostname}",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            "Disconnect", Gtk.ResponseType.CLOSE
        )
        
        dialog.set_default_size(400, 150)
        
        content_area = dialog.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(20)
        content_area.add(vbox)
        
        # Status label
        status_label = Gtk.Label()
        status_label.set_markup(f"<b>Connected to {hostname}</b>\nUser: {username}")
        vbox.pack_start(status_label, True, True, 0)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup("<small>Close this window to disconnect</small>")
        vbox.pack_start(info_label, False, False, 0)
        
        dialog.show_all()
        
        # Monitor the process in a background thread
        def monitor_process():
            if self.current_process:
                self.current_process.wait()
                GLib.idle_add(dialog.destroy)
        
        thread = threading.Thread(target=monitor_process)
        thread.daemon = True
        thread.start()
        
        response = dialog.run()
        
        # Kill the process if dialog is closed
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except:
                self.current_process.kill()
            self.current_process = None
        
        dialog.destroy()
    
    def show_advanced_options(self, widget):
        """Show advanced options dialog"""
        hostname = self.hostname_entry.get_text().strip()
        if not hostname:
            self.show_error("Please enter a hostname first")
            return
        
        dialog = Gtk.Dialog(
            title=f"Advanced Options - {hostname}",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        dialog.set_default_size(600, 700)
        
        content_area = dialog.get_content_area()
        
        # Create scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        content_area.pack_start(scrolled, True, True, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        scrolled.add_with_viewport(vbox)
        
        # Get current settings
        advanced_opts = self.get_advanced_options(hostname)
        
        # Display settings frame
        display_frame = Gtk.Frame(label="Display Settings")
        vbox.pack_start(display_frame, False, False, 0)
        
        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        display_box.set_border_width(10)
        display_frame.add(display_box)
        
        # Fullscreen checkbox
        fullscreen_check = Gtk.CheckButton(label="Fullscreen mode")
        fullscreen_check.set_active(advanced_opts.get("fullscreen", True))
        display_box.pack_start(fullscreen_check, False, False, 0)
        
        # Resolution (when not fullscreen)
        resolution_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        display_box.pack_start(resolution_box, False, False, 0)
        
        resolution_label = Gtk.Label(label="Resolution:")
        resolution_label.set_size_request(120, -1)
        resolution_label.set_xalign(0)
        resolution_box.pack_start(resolution_label, False, False, 0)
        
        resolution_combo = Gtk.ComboBoxText()
        resolutions = ["1920x1080", "1680x1050", "1600x900", "1440x900", 
                       "1366x768", "1280x1024", "1280x720", "1024x768"]
        for res in resolutions:
            resolution_combo.append_text(res)
        
        current_res = advanced_opts.get("resolution", "1920x1080")
        if current_res in resolutions:
            resolution_combo.set_active(resolutions.index(current_res))
        else:
            resolution_combo.set_active(0)
        
        resolution_box.pack_start(resolution_combo, True, True, 0)
        
        # Multi-monitor settings
        multimon_check = Gtk.CheckButton(label="Use multiple monitors")
        multimon_check.set_active(advanced_opts.get("multimon", False))
        display_box.pack_start(multimon_check, False, False, 0)
        
        # Monitor selection
        monitor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        display_box.pack_start(monitor_box, False, False, 0)
        
        monitor_label = Gtk.Label(label="Monitors:")
        monitor_label.set_size_request(120, -1)
        monitor_label.set_xalign(0)
        monitor_box.pack_start(monitor_label, False, False, 0)
        
        monitor_entry = Gtk.Entry()
        monitor_entry.set_placeholder_text("e.g., 0,1 (leave empty for all)")
        selected_monitors = advanced_opts.get("selected_monitors", [])
        if selected_monitors:
            monitor_entry.set_text(",".join(str(m) for m in selected_monitors))
        monitor_box.pack_start(monitor_entry, True, True, 0)
        
        identify_btn = Gtk.Button(label="Identify")
        identify_btn.connect("clicked", self.identify_monitors)
        monitor_box.pack_start(identify_btn, False, False, 0)
        
        # Performance frame
        perf_frame = Gtk.Frame(label="Performance Settings")
        vbox.pack_start(perf_frame, False, False, 0)
        
        perf_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        perf_box.set_border_width(10)
        perf_frame.add(perf_box)
        
        # Performance checkboxes
        disable_fonts_check = Gtk.CheckButton(label="Disable font smoothing")
        disable_fonts_check.set_active(advanced_opts.get("disable_fonts", True))
        perf_box.pack_start(disable_fonts_check, False, False, 0)
        
        disable_wallpaper_check = Gtk.CheckButton(label="Disable wallpaper")
        disable_wallpaper_check.set_active(advanced_opts.get("disable_wallpaper", True))
        perf_box.pack_start(disable_wallpaper_check, False, False, 0)
        
        disable_themes_check = Gtk.CheckButton(label="Disable themes")
        disable_themes_check.set_active(advanced_opts.get("disable_themes", True))
        perf_box.pack_start(disable_themes_check, False, False, 0)
        
        disable_aero_check = Gtk.CheckButton(label="Disable desktop composition")
        disable_aero_check.set_active(advanced_opts.get("disable_aero", True))
        perf_box.pack_start(disable_aero_check, False, False, 0)
        
        disable_drag_check = Gtk.CheckButton(label="Disable full window drag")
        disable_drag_check.set_active(advanced_opts.get("disable_drag", True))
        perf_box.pack_start(disable_drag_check, False, False, 0)
        
        compression_check = Gtk.CheckButton(label="Enable compression")
        compression_check.set_active(advanced_opts.get("compression", True))
        perf_box.pack_start(compression_check, False, False, 0)
        
        # Audio frame
        audio_frame = Gtk.Frame(label="Audio Settings")
        vbox.pack_start(audio_frame, False, False, 0)
        
        audio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        audio_box.set_border_width(10)
        audio_frame.add(audio_box)
        
        # Audio mode radio buttons
        audio_local_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Play on this computer")
        audio_local_radio.set_active(advanced_opts.get("audio_mode", "local") == "local")
        audio_box.pack_start(audio_local_radio, False, False, 0)
        
        audio_remote_radio = Gtk.RadioButton.new_with_label_from_widget(audio_local_radio, "Play on remote computer")
        audio_remote_radio.set_active(advanced_opts.get("audio_mode", "local") == "remote")
        audio_box.pack_start(audio_remote_radio, False, False, 0)
        
        audio_disabled_radio = Gtk.RadioButton.new_with_label_from_widget(audio_local_radio, "Do not play")
        audio_disabled_radio.set_active(advanced_opts.get("audio_mode", "local") == "disabled")
        audio_box.pack_start(audio_disabled_radio, False, False, 0)
        
        # Local resources frame
        resources_frame = Gtk.Frame(label="Local Resources")
        vbox.pack_start(resources_frame, False, False, 0)
        
        resources_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        resources_box.set_border_width(10)
        resources_frame.add(resources_box)
        
        clipboard_check = Gtk.CheckButton(label="Clipboard")
        clipboard_check.set_active(advanced_opts.get("clipboard", True))
        resources_box.pack_start(clipboard_check, False, False, 0)
        
        drives_check = Gtk.CheckButton(label="Share home directory")
        drives_check.set_active(advanced_opts.get("redirect_drives", False))
        resources_box.pack_start(drives_check, False, False, 0)
        
        # Security frame
        security_frame = Gtk.Frame(label="Security Settings")
        vbox.pack_start(security_frame, False, False, 0)
        
        security_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        security_box.set_border_width(10)
        security_frame.add(security_box)
        
        nla_check = Gtk.CheckButton(label="Network Level Authentication (NLA)")
        nla_check.set_active(advanced_opts.get("nla", True))
        security_box.pack_start(nla_check, False, False, 0)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Save settings
            new_opts = {
                "fullscreen": fullscreen_check.get_active(),
                "resolution": resolution_combo.get_active_text(),
                "multimon": multimon_check.get_active(),
                "selected_monitors": [],
                "disable_fonts": disable_fonts_check.get_active(),
                "disable_wallpaper": disable_wallpaper_check.get_active(),
                "disable_themes": disable_themes_check.get_active(),
                "disable_aero": disable_aero_check.get_active(),
                "disable_drag": disable_drag_check.get_active(),
                "compression": compression_check.get_active(),
                "audio_mode": "local" if audio_local_radio.get_active() else 
                             "remote" if audio_remote_radio.get_active() else "disabled",
                "clipboard": clipboard_check.get_active(),
                "redirect_drives": drives_check.get_active(),
                "nla": nla_check.get_active()
            }
            
            # Parse monitor selection
            monitor_text = monitor_entry.get_text().strip()
            if monitor_text:
                try:
                    new_opts["selected_monitors"] = [int(m.strip()) for m in monitor_text.split(",")]
                except:
                    pass
            
            self.save_advanced_options(hostname, new_opts)
            self.show_info("Advanced options saved")
        
        dialog.destroy()
    
    def identify_monitors(self, widget=None):
        """Show monitor identification windows"""
        try:
            # Get monitor information using xrandr
            result = subprocess.run(
                ["xrandr", "--query"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                self.show_error("Could not get monitor information")
                return
            
            # Parse xrandr output
            monitors = []
            monitor_index = 0
            
            for line in result.stdout.split('\n'):
                if ' connected' in line and not 'disconnected' in line:
                    # Extract monitor info
                    parts = line.split()
                    name = parts[0]
                    
                    # Find resolution and position
                    for part in parts:
                        match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', part)
                        if match:
                            width = int(match.group(1))
                            height = int(match.group(2))
                            x = int(match.group(3))
                            y = int(match.group(4))
                            monitors.append({
                                'index': monitor_index,
                                'name': name,
                                'width': width,
                                'height': height,
                                'x': x,
                                'y': y
                            })
                            monitor_index += 1
                            break
            
            if not monitors:
                self.show_info("No monitors detected")
                return
            
            # Create identification windows
            id_windows = []
            
            for mon in monitors:
                window = Gtk.Window()
                window.set_title(f"Monitor {mon['index']}")
                window.set_decorated(False)
                window.set_keep_above(True)
                window.set_default_size(400, 300)
                
                # Position window on the monitor
                window.move(mon['x'] + (mon['width'] - 400) // 2,
                           mon['y'] + (mon['height'] - 300) // 2)
                
                # Create content
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                vbox.set_border_width(20)
                window.add(vbox)
                
                # Add background color
                css_provider = Gtk.CssProvider()
                css_provider.load_from_data(b"""
                    window {
                        background-color: #2196F3;
                    }
                    label {
                        color: white;
                        font-size: 48px;
                        font-weight: bold;
                    }
                    label.info {
                        font-size: 18px;
                        font-weight: normal;
                    }
                """)
                
                style_context = window.get_style_context()
                style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                
                # Monitor number
                number_label = Gtk.Label(label=str(mon['index']))
                number_label.get_style_context().add_class("number")
                vbox.pack_start(number_label, True, True, 0)
                
                # Monitor info
                info_label = Gtk.Label(label=f"{mon['name']}\n{mon['width']}x{mon['height']}")
                info_label.get_style_context().add_class("info")
                vbox.pack_start(info_label, False, False, 0)
                
                # Close instruction
                close_label = Gtk.Label(label="Press ESC or click to close")
                close_label.get_style_context().add_class("info")
                vbox.pack_start(close_label, False, False, 0)
                
                # Connect events
                window.connect("button-press-event", lambda w, e: w.destroy())
                window.connect("key-press-event", lambda w, e: w.destroy() if e.keyval == Gdk.KEY_Escape else None)
                
                window.show_all()
                id_windows.append(window)
            
            # Auto-close after 5 seconds
            def close_all():
                for w in id_windows:
                    if w.get_visible():
                        w.destroy()
                return False
            
            GLib.timeout_add_seconds(5, close_all)
            
        except Exception as e:
            self.show_error(f"Error identifying monitors: {str(e)}")
    
    def get_advanced_options(self, hostname):
        """Get advanced options for a specific host"""
        if hostname in self.config.get("connections", {}):
            return self.config["connections"][hostname].get("advanced", {})
        return {}
    
    def save_advanced_options(self, hostname, options):
        """Save advanced options for a specific host"""
        if "connections" not in self.config:
            self.config["connections"] = {}
        
        if hostname not in self.config["connections"]:
            self.config["connections"][hostname] = {}
        
        self.config["connections"][hostname]["advanced"] = options
        self.save_config()
    
    def save_connection_info(self, hostname, username, domain):
        """Save connection information"""
        if "connections" not in self.config:
            self.config["connections"] = {}
        
        if hostname not in self.config["connections"]:
            self.config["connections"][hostname] = {}
        
        self.config["connections"][hostname]["username"] = username
        self.config["connections"][hostname]["domain"] = domain
        self.config["connections"][hostname]["last_used"] = GLib.DateTime.new_now_local().format("%Y-%m-%d %H:%M:%S")
        
        # Add to recent connections
        if "recent" not in self.config:
            self.config["recent"] = []
        
        # Remove if already in recent
        self.config["recent"] = [r for r in self.config["recent"] if r != hostname]
        
        # Add to beginning
        self.config["recent"].insert(0, hostname)
        
        # Keep only last 10
        self.config["recent"] = self.config["recent"][:10]
        
        self.save_config()
        self.load_recent_connections()
    
    def load_recent_connections(self):
        """Load recent connections into the list"""
        # Clear existing
        for child in self.recent_listbox.get_children():
            self.recent_listbox.remove(child)
        
        # Add recent connections
        for hostname in self.config.get("recent", []):
            if hostname in self.config.get("connections", {}):
                conn = self.config["connections"][hostname]
                
                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hbox.set_border_width(5)
                row.add(hbox)
                
                # Connection info
                username = conn.get("username", "")
                domain = conn.get("domain", "")
                last_used = conn.get("last_used", "")
                
                label_text = f"<b>{hostname}</b>\n"
                if domain:
                    label_text += f"User: {domain}\\{username}\n"
                else:
                    label_text += f"User: {username}\n"
                label_text += f"<small>Last used: {last_used}</small>"
                
                label = Gtk.Label()
                label.set_markup(label_text)
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                
                # Store hostname in row for selection
                row.hostname = hostname
                
                self.recent_listbox.add(row)
        
        self.recent_listbox.show_all()
    
    def on_recent_selected(self, listbox, row):
        """Handle recent connection selection"""
        if row and hasattr(row, 'hostname'):
            hostname = row.hostname
            if hostname in self.config.get("connections", {}):
                conn = self.config["connections"][hostname]
                
                # Fill in the fields
                self.hostname_entry.set_text(hostname)
                self.username_entry.set_text(conn.get("username", ""))
                self.domain_entry.set_text(conn.get("domain", ""))
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        # Set restrictive permissions
        os.chmod(self.config_file, 0o600)
    
    def load_credentials(self):
        """Load stored credentials"""
        credentials = {}
        
        # Try keyring first if available and enabled
        if KEYRING_AVAILABLE and self.use_keyring:
            try:
                stored = keyring.get_password("rdp2gui", "credentials")
                if stored:
                    return json.loads(stored)
            except Exception as e:
                # Silently fall back to file storage
                pass
        
        # Fallback to file storage
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                # Set restrictive permissions
                os.chmod(self.credentials_file, 0o600)
            except:
                pass
        
        return credentials
    
    def save_password(self, hostname, username, password):
        """Save password securely"""
        key = f"{hostname}:{username}"
        self.stored_credentials[key] = password
        
        # Try keyring first if available and enabled
        if KEYRING_AVAILABLE and self.use_keyring:
            try:
                keyring.set_password("rdp2gui", "credentials", 
                                   json.dumps(self.stored_credentials))
                return
            except:
                # Fall back to file storage
                pass
        
        # Fallback to file storage
        os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
        with open(self.credentials_file, 'w') as f:
            json.dump(self.stored_credentials, f)
        # Set restrictive permissions
        os.chmod(self.credentials_file, 0o600)
    
    def get_password_for_connection(self, hostname, username):
        """Get stored password for a connection"""
        key = f"{hostname}:{username}"
        return self.stored_credentials.get(key)
    
    def clear_saved_passwords(self, widget):
        """Clear all saved passwords"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear All Saved Passwords?"
        )
        dialog.format_secondary_text(
            "This will remove all saved passwords. You will need to re-enter them for future connections.\n\n"
            "Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.stored_credentials = {}
            
            # Clear from keyring
            if KEYRING_AVAILABLE and self.use_keyring:
                try:
                    keyring.delete_password("rdp2gui", "credentials")
                except:
                    pass
            
            # Clear file
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            
            self.show_info("All saved passwords have been cleared")
    
    def toggle_keyring_support(self, widget):
        """Toggle keyring support on/off"""
        self.use_keyring = widget.get_active()
        
        if not self.use_keyring:
            self.show_info("System keyring disabled. Passwords will be stored locally.")
        elif not KEYRING_AVAILABLE:
            widget.set_active(False)
            self.use_keyring = False
            self.show_info("Keyring module not available. Please install it first:\nTools → Install Keyring Support")
        else:
            self.show_info("System keyring enabled for secure password storage.")
    
    def show_install_prompt(self):
        """Show prompt to install FreeRDP"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="FreeRDP Not Found"
        )
        dialog.format_secondary_text(
            "FreeRDP is not installed on your system. Would you like to install it?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.show_install_dialog()
    
    def show_install_dialog(self, widget=None):
        """Show installation dialog"""
        dialog = Gtk.Dialog(
            title="Install FreeRDP",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Install", Gtk.ResponseType.OK,
            "Copy Commands", Gtk.ResponseType.APPLY
        )
        
        dialog.set_default_size(600, 400)
        
        content_area = dialog.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        content_area.add(vbox)
        
        # Instructions label
        label = Gtk.Label()
        label.set_markup("<b>FreeRDP Installation</b>")
        vbox.pack_start(label, False, False, 0)
        
        # Text view with commands
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)
        
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(text_view)
        
        commands = """# Install FreeRDP on Ubuntu/Debian/Linux Mint:
sudo apt update
sudo apt install -y freerdp2-x11

# The package name may vary by distribution:
# - freerdp2-x11 (Ubuntu 20.04+, Debian 10+, Mint 20+)
# - freerdp-x11 (older versions)
# - freerdp3-x11 (newer versions)

# After installation, the command 'xfreerdp' will be available
"""
        
        buffer = text_view.get_buffer()
        buffer.set_text(commands)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
            self.run_installation()
        elif response == Gtk.ResponseType.APPLY:
            # Copy to clipboard
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text("sudo apt update && sudo apt install -y freerdp2-x11", -1)
            dialog.destroy()
            self.show_info("Commands copied to clipboard!")
        else:
            dialog.destroy()
    
    def run_installation(self):
        """Run FreeRDP installation"""
        commands = """#!/bin/bash
echo "Installing FreeRDP..."
echo ""
sudo apt update
sudo apt install -y freerdp2-x11
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ FreeRDP installed successfully!"
    echo ""
    echo "Please restart the RDP GUI to use it."
else
    echo ""
    echo "✗ Installation failed."
    echo "Please check your internet connection and try again."
fi
echo ""
echo "Press Enter to close..."
read
"""
        
        # Save commands to temp script
        script_path = "/tmp/install_freerdp.sh"
        with open(script_path, 'w') as f:
            f.write(commands)
        os.chmod(script_path, 0o755)
        
        # Get terminal command
        terminal_cmd = self.get_terminal_command(script_path)
        
        if terminal_cmd:
            subprocess.Popen(terminal_cmd, shell=True)
            
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Installation Started"
            )
            dialog.format_secondary_text(
                "The installation has been started in a new terminal.\n"
                "Please enter your sudo password when prompted.\n"
                "After installation completes, restart this application."
            )
            dialog.run()
            dialog.destroy()
        else:
            self.show_error("Could not determine terminal emulator. Please install manually.")
    
    def get_terminal_command(self, script_path):
        """Get the appropriate terminal command for the system"""
        # Try different terminal emulators
        terminals = [
            ("gnome-terminal", f"gnome-terminal -- bash {script_path}"),
            ("xfce4-terminal", f"xfce4-terminal -e 'bash {script_path}'"),
            ("mate-terminal", f"mate-terminal -e 'bash {script_path}'"),
            ("konsole", f"konsole -e bash {script_path}"),
            ("xterm", f"xterm -e bash {script_path}"),
        ]
        
        for term_name, term_cmd in terminals:
            if shutil.which(term_name):
                return term_cmd
        
        return None
    
    def show_keyring_install_dialog(self, widget=None):
        """Show keyring installation dialog"""
        dialog = Gtk.Dialog(
            title="Install Keyring Support",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Install with apt", Gtk.ResponseType.OK,
            "Copy Commands", Gtk.ResponseType.APPLY
        )
        
        dialog.set_default_size(600, 400)
        
        content_area = dialog.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        content_area.add(vbox)
        
        # Instructions label
        label = Gtk.Label()
        label.set_markup("<b>Python Keyring Installation</b>")
        vbox.pack_start(label, False, False, 0)
        
        # Text view with commands
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)
        
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(text_view)
        
        commands = """# Install Python keyring for secure password storage:
sudo apt update
sudo apt install -y python3-keyring python3-secretstorage gnome-keyring

# This will install:
# - python3-keyring: Python keyring library
# - python3-secretstorage: Secret Service API
# - gnome-keyring: GNOME keyring service

# After installation, restart this application to enable secure password storage.
"""
        
        buffer = text_view.get_buffer()
        buffer.set_text(commands)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
            self.run_keyring_installation()
        elif response == Gtk.ResponseType.APPLY:
            # Copy to clipboard
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text("sudo apt install -y python3-keyring python3-secretstorage gnome-keyring", -1)
            dialog.destroy()
            self.show_info("Commands copied to clipboard!")
        else:
            dialog.destroy()
    
    def run_keyring_installation(self):
        """Run keyring installation"""
        commands = """#!/bin/bash
echo "Installing Python keyring module..."
echo ""
sudo apt update
sudo apt install -y python3-keyring python3-secretstorage gnome-keyring
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Keyring support installed successfully!"
    echo ""
    echo "Please restart the RDP GUI to use secure password storage."
else
    echo ""
    echo "✗ Installation failed."
    echo "Please check your internet connection and try again."
fi
echo ""
echo "Press Enter to close..."
read
"""
        
        # Save commands to temp script
        script_path = "/tmp/install_keyring.sh"
        with open(script_path, 'w') as f:
            f.write(commands)
        os.chmod(script_path, 0o755)
        
        # Get terminal command
        terminal_cmd = self.get_terminal_command(script_path)
        
        if terminal_cmd:
            subprocess.Popen(terminal_cmd, shell=True)
            
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Installation Started"
            )
            dialog.format_secondary_text(
                "The keyring installation has been started in a new terminal.\n"
                "After installation completes, restart this application."
            )
            dialog.run()
            dialog.destroy()
        else:
            self.show_error("Could not determine terminal emulator. Please install manually.")
    
    def show_error(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def show_info(self, message):
        """Show info dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    win = RDPManager()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()