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

if [ -f ./dist/main ]; then
    echo "✓ Executable built successfully at ./dist/main"
    echo ""
    echo "Usage examples:"
    echo "  ./dist/main Timeline.json --start-date 2026-01-01 --days 7"
    echo "  ./dist/main --clean-cache"
else
    echo "✗ Build failed or executable not found"
    exit 1
fi
