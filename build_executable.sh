#!/bin/bash
# Build a standalone executable using Nuitka

set -e

echo "Building timeline-2-images executable with Nuitka..."

uv run nuitka \
  --onefile \
  --output-dir=./dist \
  --follow-imports \
  --include-package=timeline_2_images \
  --enable-plugin=no-qt \
  --remove-output \
  src/timeline_2_images/main.py

if [ -f ./dist/main.bin ]; then
    mv ./dist/main.bin ./dist/timeline2images
    chmod +x ./dist/timeline2images
    echo "✓ Executable built successfully at ./dist/timeline2images"
    echo ""
    echo "Usage examples:"
    echo "  ./dist/timeline2images Timeline.json --start-date 2026-01-01 --days 7"
    echo "  ./dist/timeline2images --clean-cache"
else
    echo "✗ Build failed or executable not found"
    exit 1
fi
