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
        MODE_FLAGS="--onefile"
        WINDOWS_FLAGS=""
        ;;
    gui)
        echo "Building GUI executable with Nuitka..."
        ENTRY_POINT="src/timeline_2_images/gui/app.py"
        OUTPUT_NAME="timeline2images-gui"
        QT_FLAGS="--enable-plugin=pyside6"
        MODE_FLAGS="--mode=app"
        WINDOWS_FLAGS="--windows-console-mode=disable"
        ;;
    *)
        echo "✗ Unknown build type: $BUILD_TYPE"
        print_usage
        exit 1
        ;;
esac

# Required plugins for dependencies
REQUIRED_PLUGINS="--enable-plugin=numpy --enable-plugin=implicit-imports"

# Add macOS-specific optimization flags to improve startup time on Intel/ARM Macs
MACOS_OPTIMIZATION_FLAGS=""
MACOS_CACHE_FLAGS=""
if [ "$(uname)" = "Darwin" ]; then
    MACOS_OPTIMIZATION_FLAGS="--clang --lto=yes"
    echo "Applying macOS optimizations ($BUILD_TYPE): $MACOS_OPTIMIZATION_FLAGS"

    # For CLI on macOS: use persistent cache in ~/Library/Caches to avoid 40s extraction on every run
    if [ "$BUILD_TYPE" = "cli" ]; then
        APP_VERSION=$(uv run python -c "import sys; sys.path.insert(0, 'src'); from timeline_2_images import __version__; print(__version__)")
        # Use explicit path for macOS: {HOME}/Library/Caches/timeline2images/{VERSION}
        MACOS_CACHE_FLAGS="--onefile-tempdir-spec={HOME}/Library/Caches/timeline2images/{VERSION} --onefile-cache-mode=cached --company-name=timeline2images --product-name=timeline2images --product-version=$APP_VERSION"
        echo "Applying macOS cache optimization for CLI: persistent cache in ~/Library/Caches"
    fi
fi

uv run nuitka \
  $MODE_FLAGS \
  --output-dir=./dist \
  --follow-imports \
  --include-package=timeline_2_images \
  $QT_FLAGS \
  $REQUIRED_PLUGINS \
  $WINDOWS_FLAGS \
  --deployment \
  $MACOS_OPTIMIZATION_FLAGS \
  $MACOS_CACHE_FLAGS \
  --assume-yes-for-downloads \
  --remove-output \
  "$ENTRY_POINT"

echo "Checking for build output in dist directory..."
ls -lh ./dist/ 2>/dev/null | head -20

# macOS GUI apps with --mode=app create .app bundles (must keep intact)
if [ -d "./dist/app.app" ] && [ "$BUILD_TYPE" = "gui" ]; then
    APP_VERSION=$(uv run python -c "import sys; sys.path.insert(0, 'src'); from timeline_2_images import __version__; print(__version__)")
    mv "./dist/app.app" "./dist/$OUTPUT_NAME-$APP_VERSION-macos-amd64.app"
    echo "✓ $BUILD_TYPE app bundle built successfully at ./dist/$OUTPUT_NAME-$APP_VERSION-macos-amd64.app"
# Modern Nuitka (--mode=standalone/app) creates .dist directories (CLI and non-macOS GUI)
# Check for main.dist/main.bin (CLI, Linux/macOS)
elif [ -f "./dist/main.dist/main.bin" ]; then
    cp "./dist/main.dist/main.bin" "./dist/$OUTPUT_NAME"
    chmod +x "./dist/$OUTPUT_NAME"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/$OUTPUT_NAME"
# Check for main.dist/main.exe (CLI, Windows)
elif [ -f "./dist/main.dist/main.exe" ]; then
    cp "./dist/main.dist/main.exe" "./dist/${OUTPUT_NAME}.exe"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/${OUTPUT_NAME}.exe"
# Check for app.dist/app.bin (GUI, Linux/macOS non-app bundle)
elif [ -f "./dist/app.dist/app.bin" ]; then
    cp "./dist/app.dist/app.bin" "./dist/$OUTPUT_NAME"
    chmod +x "./dist/$OUTPUT_NAME"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/$OUTPUT_NAME"
# Check for app.dist/app.exe (GUI, Windows)
elif [ -f "./dist/app.dist/app.exe" ]; then
    cp "./dist/app.dist/app.exe" "./dist/${OUTPUT_NAME}.exe"
    echo "✓ $BUILD_TYPE executable built successfully at ./dist/${OUTPUT_NAME}.exe"
# Legacy Nuitka (--onefile) creates single files
# Check for main.bin (Linux/macOS)
elif [ -f "./dist/main.bin" ]; then
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
    echo "✗ Build failed or output not found"
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
