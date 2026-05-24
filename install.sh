#!/usr/bin/env bash
#
# RDP2GUI per-user installer (no sudo required for the app itself).
#
# Installs the application into your home directory and adds a menu entry for
# KDE (or any freedesktop-compliant desktop). Missing system dependencies are
# detected and only installed after showing you the list and asking for approval
# (that step uses sudo via your package manager).
#
set -euo pipefail

APP_NAME="rdp2gui"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SOURCE_PY="$SRC_DIR/rdp2gui.py"
TARGET_BIN="$BIN_DIR/$APP_NAME"
TARGET_DESKTOP="$DESKTOP_DIR/$APP_NAME.desktop"

info()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m!!!\033[0m %s\n' "$1" >&2; }
err()   { printf '\033[1;31mERROR:\033[0m %s\n' "$1" >&2; }

if [[ ! -f "$SOURCE_PY" ]]; then
    err "Cannot find rdp2gui.py next to this script ($SOURCE_PY)."
    exit 1
fi

# --------------------------------------------------------------------------
# 1. Dependency check (functional, then mapped to package names)
# --------------------------------------------------------------------------
missing_required=()   # human-readable feature names that failed
missing_optional=()

if ! python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" >/dev/null 2>&1; then
    missing_required+=("GTK3 Python bindings")
fi
if ! command -v xfreerdp >/dev/null 2>&1 && ! command -v xfreerdp3 >/dev/null 2>&1; then
    missing_required+=("FreeRDP client (xfreerdp)")
fi
if ! python3 -c "import keyring" >/dev/null 2>&1; then
    missing_optional+=("Python keyring (optional: secure password storage)")
fi

# Detect package manager and build the package name list for whatever is missing.
PM=""
PM_INSTALL=""
req_pkgs=()
opt_pkgs=()

if command -v pacman >/dev/null 2>&1; then
    PM="pacman"
    PM_INSTALL="sudo pacman -S --needed"
    (( ${#missing_required[@]} )) && req_pkgs=(python-gobject gtk3 freerdp)
    (( ${#missing_optional[@]} )) && opt_pkgs=(python-keyring)
elif command -v apt >/dev/null 2>&1; then
    PM="apt"
    PM_INSTALL="sudo apt install"
    (( ${#missing_required[@]} )) && req_pkgs=(python3-gi gir1.2-gtk-3.0 freerdp2-x11)
    (( ${#missing_optional[@]} )) && opt_pkgs=(python3-keyring python3-secretstorage gnome-keyring)
elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
    PM_INSTALL="sudo dnf install"
    (( ${#missing_required[@]} )) && req_pkgs=(python3-gobject gtk3 freerdp)
    (( ${#missing_optional[@]} )) && opt_pkgs=(python3-keyring)
fi

if (( ${#missing_required[@]} || ${#missing_optional[@]} )); then
    info "Dependency check found missing components:"
    for m in "${missing_required[@]}"; do printf '    - %s\n' "$m"; done
    for m in "${missing_optional[@]}"; do printf '    - %s\n' "$m"; done

    if [[ -n "$PM" ]]; then
        all_pkgs=("${req_pkgs[@]}" "${opt_pkgs[@]}")
        cmd="$PM_INSTALL ${all_pkgs[*]}"
        echo
        info "The following command can install them ($PM):"
        printf '    %s\n' "$cmd"
        echo
        read -r -p "Install these now? [y/N] " reply
        if [[ "$reply" =~ ^[Yy]$ ]]; then
            # Word-splitting of $cmd is intentional here.
            # shellcheck disable=SC2086
            $cmd
        else
            warn "Skipping dependency install. Run the command above later if needed."
            if (( ${#missing_required[@]} )); then
                warn "Required components are missing; the app may not start until they are installed."
            fi
        fi
    else
        warn "No supported package manager (pacman/apt/dnf) detected."
        warn "Please install the missing components manually before running the app."
    fi
else
    info "All dependencies satisfied."
fi

# --------------------------------------------------------------------------
# 2. Install the executable
# --------------------------------------------------------------------------
info "Installing executable to $TARGET_BIN"
mkdir -p "$BIN_DIR"
install -m755 "$SOURCE_PY" "$TARGET_BIN"

# --------------------------------------------------------------------------
# 3. Write the desktop entry (absolute Exec so menu launch is PATH-independent)
# --------------------------------------------------------------------------
info "Installing menu entry to $TARGET_DESKTOP"
mkdir -p "$DESKTOP_DIR"
cat > "$TARGET_DESKTOP" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=RDP2GUI
Comment=FreeRDP GUI for Linux - Remote Desktop Connection Client
Exec=$TARGET_BIN
Icon=preferences-desktop-remote-desktop
Terminal=false
Categories=Network;RemoteAccess;
Keywords=rdp;remote;desktop;connection;windows;freerdp;
EOF
chmod 644 "$TARGET_DESKTOP"

# --------------------------------------------------------------------------
# 4. Refresh desktop / menu caches (best-effort)
# --------------------------------------------------------------------------
update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 >/dev/null 2>&1 || true
fi

# --------------------------------------------------------------------------
# 5. PATH hint (menu launch already works via absolute Exec)
# --------------------------------------------------------------------------
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) warn "$BIN_DIR is not on your PATH. The menu entry works regardless;"
       warn "to run '$APP_NAME' from a terminal, add this to your shell profile:"
       warn "    export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

echo
info "RDP2GUI installed successfully."
printf '    Executable : %s\n' "$TARGET_BIN"
printf '    Menu entry : %s\n' "$TARGET_DESKTOP"
printf '    Launch it from your application menu (search "RDP2GUI") or run: %s\n' "$TARGET_BIN"
printf '    To remove it later, run: %s\n' "$SRC_DIR/uninstall.sh"
