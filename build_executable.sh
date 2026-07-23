#!/bin/bash
# Build standalone executables using Nuitka for CLI or GUI

set -e

# Parse command line arguments
BUILD_TYPE="${1:-cli}"

print_usage() {
    echo "Build standalone executable with Nuitka"
    echo ""
    echo "Usage: $0 [cli|gui]"
    echo ""
    echo "Arguments:"
    echo "  cli   - Build CLI version (default)"
    echo "  gui   - Build GUI version (requires PySide6)"
    echo ""
    echo "Examples:"
    echo "  $0          # Build CLI version"
    echo "  $0 cli      # Build CLI version explicitly"
    echo "  $0 gui      # Build GUI version"
    echo ""
    echo "Output:"
    echo "  CLI: ./dist/timeline2images"
    echo "  GUI: ./dist/timeline2images-gui"
}

if [ "$BUILD_TYPE" = "--help" ] || [ "$BUILD_TYPE" = "-h" ]; then
    print_usage
    exit 0
fi

case "$BUILD_TYPE" in
    cli)
        echo "Building CLI executable with Nuitka..."
        ENTRY_POINT="src/timeline_2_images/main.py"
        OUTPUT_NAME="timeline2images"
        QT_FLAGS="--enable-plugin=no-qt"
        CONSOLE_FLAGS=""
        ;;
    gui)
        echo "Building GUI executable with Nuitka..."
        ENTRY_POINT="src/timeline_2_images/gui/app.py"
        OUTPUT_NAME="timeline2images-gui"
        QT_FLAGS="--enable-plugin=pyside6"
        CONSOLE_FLAGS="--windows-disable-console"
        ;;
    *)
        echo "✗ Unknown build type: $BUILD_TYPE"
        print_usage
        exit 1
        ;;
esac

uv run nuitka \
  --onefile \
  --output-dir=./dist \
  --follow-imports \
  --include-package=timeline_2_images \
  $QT_FLAGS \
  $CONSOLE_FLAGS \
  --assume-yes-for-downloads \
  --remove-output \
  "$ENTRY_POINT"

echo "Checking for binary in dist directory..."
ls -lh ./dist/ 2>/dev/null | grep -E "\.bin|\.exe|timeline"

# Check for main.bin (Linux/macOS)
if [ -f "./dist/main.bin" ]; then
    mv "./dist/main.bin" "./dist/$OUTPUT_NAME"
    chmod +x "./dist/$OUTPUT_NAME"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/$OUTPUT_NAME"
# Check for main.exe (Windows)
elif [ -f "./dist/main.exe" ]; then
    mv "./dist/main.exe" "./dist/${OUTPUT_NAME}.exe"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/${OUTPUT_NAME}.exe"
# Check for app.bin (Linux/macOS)
elif [ -f "./dist/app.bin" ]; then
    mv "./dist/app.bin" "./dist/$OUTPUT_NAME"
    chmod +x "./dist/$OUTPUT_NAME"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/$OUTPUT_NAME"
# Check for app.exe (Windows)
elif [ -f "./dist/app.exe" ]; then
    mv "./dist/app.exe" "./dist/${OUTPUT_NAME}.exe"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/${OUTPUT_NAME}.exe"
else
    echo "✗ Build failed or executable not found"
    exit 1
fi

echo ""
if [ "$BUILD_TYPE" = "cli" ]; then
    echo "Usage examples:"
    echo "  ./dist/timeline2images Timeline.json --start-date 2026-01-01 --days 7"
    echo "  ./dist/timeline2images Timeline.json --image-size 800"
else
    echo "Usage:"
    echo "  ./dist/timeline2images-gui"
fi
