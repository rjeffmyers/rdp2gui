# Changelog

All notable changes to RDP2GUI will be documented in this file.

## [1.0.0] - 2025-08-15

### Initial Release

#### Features
- Simple and intuitive GTK+ graphical interface for xfreerdp
- Connection management with saved connections
- Secure password storage using system keyring
- Advanced connection options:
  - Display settings (fullscreen, custom resolution, multi-monitor)
  - Performance optimizations
  - Audio configuration
  - Local resource sharing
  - Security options (NLA, certificate handling)
- Built-in installation helpers for FreeRDP and keyring support
- Monitor identification tool for multi-monitor setups
- Debug mode for troubleshooting
- Recent connections list for quick access

#### Package
- Debian package (.deb) for easy installation on Ubuntu/Debian-based systems
- Desktop integration with .desktop file
- Proper dependency management

#### Compatibility
- Python 3.6+
- GTK+ 3.0
- FreeRDP 2.x
- Support for GNOME Keyring and Secret Service