#!/usr/bin/env bash
#
# RDP2GUI per-user uninstaller. Removes the executable and menu entry installed
# by install.sh. Your configuration and saved credentials in ~/.config/rdp2gui/
# are left untouched.
#
set -euo pipefail

APP_NAME="rdp2gui"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
TARGET_BIN="$BIN_DIR/$APP_NAME"
TARGET_DESKTOP="$DESKTOP_DIR/$APP_NAME.desktop"

info() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }

removed=0
if [[ -e "$TARGET_BIN" ]]; then
    rm -f "$TARGET_BIN"
    info "Removed $TARGET_BIN"
    removed=1
fi
if [[ -e "$TARGET_DESKTOP" ]]; then
    rm -f "$TARGET_DESKTOP"
    info "Removed $TARGET_DESKTOP"
    removed=1
fi

if (( removed == 0 )); then
    info "Nothing to remove (RDP2GUI does not appear to be installed for this user)."
fi

# Refresh desktop / menu caches (best-effort)
update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 >/dev/null 2>&1 || true
fi

echo
info "Uninstall complete."
printf '    Your settings were preserved at: %s\n' "$HOME/.config/rdp2gui/"
printf '    Delete that folder manually if you want to remove them too.\n'
