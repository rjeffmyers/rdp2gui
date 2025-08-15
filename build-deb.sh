#!/bin/bash

# Build script for creating RDP2GUI Debian package

set -e

VERSION="1.0.0"
PACKAGE_NAME="rdp2gui_${VERSION}_all"

echo "Building RDP2GUI Debian package v${VERSION}..."

# Clean any previous builds
rm -f *.deb
rm -rf debian/usr/bin/rdp2gui debian/usr/share/doc/rdp2gui/README.md

# Copy files to package structure
echo "Copying files..."
cp rdp2gui.py debian/usr/bin/rdp2gui
cp README.md debian/usr/share/doc/rdp2gui/

# Set proper permissions
chmod 755 debian/usr/bin/rdp2gui
chmod 755 debian/DEBIAN/postinst

# Calculate installed size
INSTALLED_SIZE=$(du -sk debian/usr | cut -f1)
sed -i "/^Installed-Size:/d" debian/DEBIAN/control
echo "Installed-Size: $INSTALLED_SIZE" >> debian/DEBIAN/control

# Build the package
echo "Building package..."
dpkg-deb --build debian "${PACKAGE_NAME}.deb"

# Clean up
echo "Cleaning up..."
rm -rf debian/usr/bin/rdp2gui debian/usr/share/doc/rdp2gui/README.md

echo "Package built successfully: ${PACKAGE_NAME}.deb"
echo ""
echo "To install: sudo dpkg -i ${PACKAGE_NAME}.deb"
echo "To install with dependencies: sudo apt install ./${PACKAGE_NAME}.deb"