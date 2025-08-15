# RDP2GUI v1.0.0 Release

## Installation

### Debian/Ubuntu/Linux Mint

Download the `.deb` package and install using one of the following methods:

```bash
# Method 1: Install with automatic dependency resolution
sudo apt install ./rdp2gui_1.0.0_all.deb

# Method 2: Install with dpkg and then fix dependencies
sudo dpkg -i rdp2gui_1.0.0_all.deb
sudo apt-get install -f
```

### Manual Installation

For other Linux distributions:

```bash
# Clone the repository
git clone https://github.com/rjeffmyers/rdp2gui.git
cd rdp2gui

# Make executable
chmod +x rdp2gui.py

# Install dependencies
# See README.md for distribution-specific commands

# Run the application
./rdp2gui.py
```

## What's New

This is the first official release of RDP2GUI, bringing a user-friendly GUI for FreeRDP to Linux users.

### Key Features
- 🖥️ Simple connection management with saved connections
- 🔒 Secure password storage using system keyring
- ⚙️ Advanced options (display, performance, audio, security)
- 🖥️ Multi-monitor support with monitor identification tool
- 🛠️ Built-in installation helpers
- 🐛 Debug mode for troubleshooting

## System Requirements

- Python 3.6 or higher
- GTK+ 3.0
- FreeRDP 2.x (xfreerdp)

## Known Issues

- KDE Wallet integration may require additional configuration
- Some special characters in passwords may need escaping

## Support

For issues or feature requests, please visit:
https://github.com/rjeffmyers/rdp2gui/issues

## License

MIT License - See LICENSE file for details