# RDP2GUI - FreeRDP GUI for Linux

A simple and intuitive GTK+ graphical interface for xfreerdp on Linux, designed to provide a Microsoft Remote Desktop-like experience for Linux users.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![GTK](https://img.shields.io/badge/GTK-3.0-green.svg)

## Description

RDP2GUI is a user-friendly GUI wrapper for the xfreerdp command-line tool, making it easy to connect to Windows machines via RDP (Remote Desktop Protocol) from Linux systems. The interface is inspired by Microsoft's Remote Desktop Connection client, providing a familiar experience for users transitioning from Windows.

## Features

### 🖥️ **Simple Connection Management**
- Clean, intuitive interface similar to Microsoft's RDP client
- Hostname dropdown with previously connected computers
- Auto-fill username and domain from saved connections
- Recent connections list for quick access

### 🔒 **Secure Password Storage**
- System keyring integration (GNOME Keyring support)
- Encrypted local storage fallback
- Optional password saving per connection
- Clear all saved passwords option

### ⚙️ **Advanced Connection Options**
Customizable settings saved per host:
- **Display Settings**
  - Fullscreen mode (default)
  - Custom resolution selection
  - Multi-monitor support
  - Specific monitor selection
  - Monitor identification tool
  
- **Performance Optimizations**
  - Disable font smoothing
  - Disable wallpaper
  - Disable themes
  - Disable desktop composition (Aero)
  - Disable window drag
  - Compression settings

- **Audio Configuration**
  - Play on local computer
  - Play on remote computer
  - Disable audio

- **Local Resources**
  - Clipboard sharing
  - Home directory sharing

- **Security Options**
  - Network Level Authentication (NLA)
  - Certificate handling

### 🛠️ **Built-in Tools**
- **Installation Helpers**
  - Auto-detect missing FreeRDP with installation wizard
  - Keyring support installation guide
  - Terminal-based installers with proper commands

- **Monitor Identification**
  - Visual overlay showing monitor numbers
  - Displays monitor resolution and position
  - Helps configure multi-monitor setups

- **Debug Mode**
  - Toggle command output for troubleshooting
  - Password masking in debug output
  - Detailed error messages

## Requirements

- Python 3.6+
- GTK+ 3.0
- xfreerdp (FreeRDP 2.x)
- Python GObject Introspection (python3-gi)

### Optional
- python3-keyring (for secure password storage)
- python3-secretstorage
- gnome-keyring

## Installation

### Install on KDE-based distributions (Arch/CachyOS, KDE neon, Kubuntu, Fedora KDE, openSUSE…)

The bundled `install.sh` adds RDP2GUI to your KDE application menu. It is a
**per-user** install: the app and its menu entry go in your home directory, so no
root is required for the app itself, and it works the same on any KDE/Plasma desktop
regardless of which distribution or package manager you use.

```bash
git clone https://github.com/rjeffmyers/rdp2gui.git
cd rdp2gui
./install.sh
```

What it does:

- Copies the app to `~/.local/bin/rdp2gui`.
- Creates a menu entry at `~/.local/share/applications/rdp2gui.desktop` with an
  absolute path, so launching from the menu (search **RDP2GUI** in the application
  launcher or KRunner) works even if `~/.local/bin` isn't on your `PATH`.
- Refreshes the KDE/Plasma menu cache so the entry appears immediately.
- Checks for missing dependencies and, **only after showing you the exact package
  list and asking for approval**, installs them with your package manager. It
  auto-detects `pacman` (Arch/CachyOS/Manjaro), `apt` (Kubuntu/KDE neon/Debian), or
  `dnf` (Fedora KDE). The dependency install is the only step that uses `sudo`; if you
  decline, the menu entry is still created and the install command is printed so you
  can run it later.

Uninstall at any time (your settings and saved connections in
`~/.config/rdp2gui/` are preserved):

```bash
./uninstall.sh
```

> **System-wide install:** prefer the app available to all users under `/usr`? Use the
> Debian package (`build-deb.sh`) on Debian-based systems, or copy `rdp2gui.py` to
> `/usr/bin/rdp2gui` and `debian/usr/share/applications/rdp2gui.desktop` to
> `/usr/share/applications/` manually.

> **Wayland note:** RDP2GUI runs on both X11 and Wayland Plasma sessions. The
> **Identify Monitors** tool uses GDK's monitor API, so it correctly detects and
> labels each monitor on Wayland as well as X11.

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/rjeffmyers/rdp2gui.git
cd rdp2gui
```

2. Make the script executable:
```bash
chmod +x rdp2gui.py
```

3. Run the application:
```bash
./rdp2gui.py
```

### Install Dependencies

#### Ubuntu/Debian/Linux Mint:
```bash
# Install FreeRDP
sudo apt update
sudo apt install -y freerdp2-x11

# Install Python GTK bindings
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Optional: Install keyring support for secure password storage
sudo apt install -y python3-keyring python3-secretstorage gnome-keyring
```

#### Fedora:
```bash
# Install FreeRDP
sudo dnf install -y freerdp

# Install Python GTK bindings
sudo dnf install -y python3-gobject gtk3

# Optional: Install keyring support
sudo dnf install -y python3-keyring python3-secretstorage gnome-keyring
```

#### Arch Linux:
```bash
# Install FreeRDP
sudo pacman -S freerdp

# Install Python GTK bindings
sudo pacman -S python-gobject gtk3

# Optional: Install keyring support
sudo pacman -S python-keyring python-secretstorage gnome-keyring
```

## Usage

1. **Basic Connection:**
   - Enter hostname or IP address
   - Enter username (domain\username or username@domain format supported)
   - Enter domain (optional)
   - Click Connect
   - Enter password when prompted

2. **Using Saved Connections:**
   - Select a hostname from the dropdown
   - Username and domain are auto-filled
   - Click Connect and enter password

3. **Advanced Options:**
   - Click "Advanced Options" button
   - Configure display, performance, audio, and security settings
   - Settings are saved per hostname

4. **Tools Menu:**
   - Install FreeRDP if missing
   - Install keyring support
   - Clear saved passwords
   - Identify monitors for multi-monitor setup
   - Toggle debug mode for troubleshooting

## Configuration

Configuration files are stored in:
- `~/.config/rdp2gui/config.json` - Connection settings and preferences
- `~/.config/rdp2gui/credentials.json` - Encrypted passwords (when keyring unavailable)

## Security Notes

- Passwords are stored in the system keyring when available (recommended)
- Fallback to encrypted local storage if keyring is unavailable
- Debug mode masks passwords in terminal output
- Use Tools → Clear Saved Passwords to remove all stored credentials

## Troubleshooting

### Connection Issues
1. Enable debug mode: Tools → Debug Mode
2. Check the terminal output for error messages
3. Verify xfreerdp is installed: `which xfreerdp`
4. Test connection manually: `xfreerdp /v:hostname /u:username`

### Password Issues
- Special characters in passwords are properly handled
- If authentication fails, verify username format (may need DOMAIN\username)
- Check if NLA is required (Advanced Options → Security)

### Keyring Issues
- If keyring isn't working, check Tools → Install Keyring Support
- Ensure gnome-keyring service is running
- The app will fall back to local encrypted storage automatically

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by Microsoft's Remote Desktop Connection client
- Built with Python, GTK+, and FreeRDP
- Thanks to the FreeRDP project for the excellent RDP implementation

## Author

RDP2GUI Contributors

## Links

- [GitHub Repository](https://github.com/rjeffmyers/rdp2gui)
- [FreeRDP Project](https://www.freerdp.com/)
- [Report Issues](https://github.com/rjeffmyers/rdp2gui/issues)
