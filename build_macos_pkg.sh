#!/bin/bash
# Build macOS .pkg installer for timeline2images CLI
# Usage: ./build_macos_pkg.sh

set -e

# Check we're on macOS
if [ "$(uname)" != "Darwin" ]; then
    echo "✗ This script only runs on macOS"
    exit 1
fi

# Check the CLI binary exists
if [ ! -f "./dist/timeline2images" ]; then
    echo "✗ CLI binary not found at ./dist/timeline2images"
    echo "  Run './build_executable.sh cli' first"
    exit 1
fi

# Get version and architecture
APP_VERSION=$(uv run python -c "import sys; sys.path.insert(0, 'src'); from timeline_2_images import __version__; print(__version__)")
ARCH=$(uname -m)  # arm64 or x86_64

echo "Building macOS .pkg installer for timeline2images $APP_VERSION ($ARCH)..."

# Create temporary staging directory
STAGING_DIR=$(mktemp -d)
trap "rm -rf $STAGING_DIR" EXIT

PAYLOAD_DIR="$STAGING_DIR/payload"
SCRIPTS_DIR="$STAGING_DIR/scripts"
mkdir -p "$PAYLOAD_DIR/usr/local/bin"
mkdir -p "$SCRIPTS_DIR"

echo "Staging binary to $PAYLOAD_DIR/usr/local/bin/..."
cp "./dist/timeline2images" "$PAYLOAD_DIR/usr/local/bin/timeline2images"
chmod +x "$PAYLOAD_DIR/usr/local/bin/timeline2images"

echo "Creating postinstall script..."
cat > "$SCRIPTS_DIR/postinstall" << 'POSTINSTALL_SCRIPT'
#!/bin/bash
# postinstall script: pre-warm the Nuitka cache by running the binary once
# This forces the ~40s extraction to happen during installation (expected)
# rather than on first user run (unexpected)

BINARY="/usr/local/bin/timeline2images"

# Find the user running the GUI (most reliable on macOS)
# Check for console user - the person currently logged in to the desktop
INSTALL_USER=$(/usr/bin/stat -f '%Su' /dev/console 2>/dev/null)

# If that didn't work, try other methods
if [ -z "$INSTALL_USER" ] || [ "$INSTALL_USER" = "root" ]; then
    # Try getting from SUDO_USER (works if installed via sudo)
    INSTALL_USER="$SUDO_USER"
fi

if [ -z "$INSTALL_USER" ] || [ "$INSTALL_USER" = "root" ]; then
    # Try getting from who/last active user
    INSTALL_USER=$(who | grep '(console)' | awk '{print $1}' | head -1)
fi

# If still no valid user, try to find any non-root user with a home directory
if [ -z "$INSTALL_USER" ] || [ "$INSTALL_USER" = "root" ]; then
    for user_home in /Users/*; do
        if [ -d "$user_home" ]; then
            potential_user=$(basename "$user_home")
            # Skip system accounts
            if [[ ! "$potential_user" =~ ^_ ]] && [ "$potential_user" != "Shared" ] && [ "$potential_user" != "Guest" ]; then
                INSTALL_USER="$potential_user"
                break
            fi
        fi
    done
fi

# If we found a valid non-root user, pre-warm the cache
if [ -n "$INSTALL_USER" ] && [ "$INSTALL_USER" != "root" ] && [ -f "$BINARY" ]; then
    # Run binary as the user using launchctl asuser (macOS 10.7+)
    # This is the most reliable way to run a command as a specific user
    launchctl asuser "$(id -u "$INSTALL_USER")" sudo -u "$INSTALL_USER" "$BINARY" --version >/dev/null 2>&1 || true
fi

exit 0
POSTINSTALL_SCRIPT

chmod +x "$SCRIPTS_DIR/postinstall"

# Build the .pkg file
PKG_OUTPUT="dist/timeline2images-${APP_VERSION}-macos-${ARCH}.pkg"

echo "Building .pkg file to $PKG_OUTPUT..."
pkgbuild \
    --root "$PAYLOAD_DIR" \
    --scripts "$SCRIPTS_DIR" \
    --identifier "com.timeline2images.cli" \
    --version "$APP_VERSION" \
    --install-location "/" \
    "$PKG_OUTPUT"

echo ""
echo "✓ macOS .pkg installer built successfully"
echo "  File: $PKG_OUTPUT"
echo "  Size: $(ls -lh "$PKG_OUTPUT" | awk '{print $5}')"
echo ""
echo "Installation instructions for users:"
echo "  1. Double-click timeline2images-${APP_VERSION}-macos-${ARCH}.pkg"
echo "  2. Follow the installer (this pre-warms the cache)"
echo "  3. Run 'timeline2images --version' from terminal (instant!)"
echo ""
