#!/bin/bash
# Install compiled executable with desktop integration on Linux

set -e

INSTALL_TYPE="${1:-gui}"
VERSION="0.3.0"

print_usage() {
    echo "Install compiled executable with desktop integration"
    echo ""
    echo "Usage: $0 [cli|gui]"
    echo ""
    echo "Arguments:"
    echo "  cli   - Install CLI version (no desktop integration)"
    echo "  gui   - Install GUI version with desktop shortcut and icon (default)"
    echo ""
    echo "Install locations:"
    echo "  Binary: ~/.local/bin/timeline2images or ~/.local/bin/timeline2images-gui"
    echo "  Icon:   ~/.local/share/icons/hicolor/scalable/apps/"
    echo "  Desktop: ~/.local/share/applications/"
    echo ""
    echo "Examples:"
    echo "  $0 cli      # Install CLI version"
    echo "  $0 gui      # Install GUI version with desktop integration"
}

if [ "$INSTALL_TYPE" = "--help" ] || [ "$INSTALL_TYPE" = "-h" ]; then
    print_usage
    exit 0
fi

# Create directories if they don't exist
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
mkdir -p ~/.local/share/applications

case "$INSTALL_TYPE" in
    cli)
        echo "Installing CLI executable..."
        if [ ! -f "./dist/timeline2images" ]; then
            echo "✗ CLI executable not found. Build it first with: ./build_executable.sh cli"
            exit 1
        fi
        cp ./dist/timeline2images ~/.local/bin/
        chmod +x ~/.local/bin/timeline2images
        echo "✓ CLI installed to ~/.local/bin/timeline2images"
        echo ""
        echo "Add to PATH if needed:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
    gui)
        echo "Installing GUI executable with desktop integration..."
        if [ ! -f "./dist/timeline2images-gui" ]; then
            echo "✗ GUI executable not found. Build it first with: ./build_executable.sh gui"
            exit 1
        fi

        # Copy executable
        cp ./dist/timeline2images-gui ~/.local/bin/
        chmod +x ~/.local/bin/timeline2images-gui

        # Create and install icon (simple SVG icon)
        install_icon

        # Create and install desktop file
        install_desktop_file

        echo "✓ GUI installed successfully!"
        echo ""
        echo "Installed files:"
        echo "  Binary:  ~/.local/bin/timeline2images-gui"
        echo "  Icon:    ~/.local/share/icons/hicolor/scalable/apps/timeline2images.svg"
        echo "  Desktop: ~/.local/share/applications/timeline2images.desktop"
        echo ""
        echo "The app should appear in your application launcher."
        echo "If not visible, run: update-desktop-database ~/.local/share/applications"
        ;;
    *)
        echo "✗ Unknown install type: $INSTALL_TYPE"
        print_usage
        exit 1
        ;;
esac

install_icon() {
    # Create a simple SVG icon
    cat > ~/.local/share/icons/hicolor/scalable/apps/timeline2images.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <!-- Background circle -->
  <circle cx="128" cy="128" r="120" fill="#4A90E2" opacity="0.9"/>

  <!-- Map layers -->
  <g transform="translate(128, 128)">
    <!-- Path lines (routes) -->
    <path d="M -60 -40 Q -30 -50 0 -40 T 60 -40" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M -60 0 Q -30 10 0 0 T 60 0" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M -60 40 Q -30 50 0 40 T 60 40" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>

    <!-- Start point (green) -->
    <circle cx="-60" cy="-40" r="6" fill="#4CAF50"/>

    <!-- End point (red) -->
    <circle cx="60" cy="40" r="6" fill="#F44336"/>

    <!-- Map grid lines -->
    <line x1="-70" y1="-70" x2="70" y2="-70" stroke="#FFFFFF" stroke-width="1" opacity="0.3"/>
    <line x1="-70" y1="70" x2="70" y2="70" stroke="#FFFFFF" stroke-width="1" opacity="0.3"/>
    <line x1="-70" y1="-70" x2="-70" y2="70" stroke="#FFFFFF" stroke-width="1" opacity="0.3"/>
    <line x1="70" y1="-70" x2="70" y2="70" stroke="#FFFFFF" stroke-width="1" opacity="0.3"/>
  </g>

  <!-- Outer ring -->
  <circle cx="128" cy="128" r="120" fill="none" stroke="#2E5C8A" stroke-width="2"/>
</svg>
EOF
}

install_desktop_file() {
    # Create desktop file for application launcher
    cat > ~/.local/share/applications/timeline2images.desktop << EOF
[Desktop Entry]
Type=Application
Name=Timeline 2 Images
Comment=Generate daily route maps from Google Timeline
Exec=\$HOME/.local/bin/timeline2images-gui
Icon=timeline2images
Categories=Graphics;Utility;
Terminal=false
Version=1.0
EOF
}
