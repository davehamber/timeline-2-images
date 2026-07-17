#!/bin/bash
# Check that all dependencies use compatible licenses for EUPL-1.2
# Compatible licenses: MIT, BSD, Apache, MPL, ISC, and other permissive licenses
# Incompatible: GPL, AGPL (strong copyleft - requires full GPL license)

set -e

echo "Checking dependency licenses..."
echo

# Allowed licenses for EUPL-1.2 compatibility
ALLOWED_LICENSES=(
    "MIT"
    "Apache"
    "BSD"
    "PSF"
    "ISC"
    "MPL"
    "Unlicense"
    "EUPL"
    "0BSD"
)

# Run pip-licenses and check for problematic licenses
uv run pip-licenses --format=csv --with-urls | tail -n +2 | while IFS=',' read -r name version license url; do
    # Clean up license field (remove quotes)
    license=$(echo "$license" | tr -d '"')
    name=$(echo "$name" | tr -d '"')

    # Check if license contains any disallowed terms
    if echo "$license" | grep -qi "GPL\|AGPL"; then
        echo "❌ INCOMPATIBLE: $name - $license"
        echo "   GPL/AGPL licenses are incompatible with EUPL-1.2 (requires full GPL)"
        exit 1
    fi
done

echo "✓ All dependencies use compatible licenses"
echo
echo "License summary:"
uv run pip-licenses --format=table
