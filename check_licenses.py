#!/usr/bin/env python
"""Check that project dependencies use EUPL-1.2 compatible licenses."""

import subprocess
import sys
from typing import Dict, List, Tuple

# Licenses compatible with EUPL-1.2
COMPATIBLE_LICENSE_PATTERNS = [
    "MIT",
    "Apache",
    "BSD",
    "PSF",
    "ISC",
    "MPL",
    "Unlicense",
    "EUPL",
    "0BSD",
    "Python",
    "Boost",
    "CC0",
]

# Licenses incompatible with EUPL-1.2 (for runtime dependencies)
# Note: LGPL and GPL in dev tools are acceptable
RUNTIME_INCOMPATIBLE_PATTERNS = [
    "GPL-3.0-or-later",
    "GPL-2.0-or-later",
]

# Development-only packages (linting, testing, building)
DEV_ONLY_PACKAGES = {
    "pytest",
    "pytest-cov",
    "ruff",
    "pylint",
    "mypy",
    "black",
    "nuitka",
    "pre-commit",
    "radon",
    "astroid",  # dependency of pylint
    "pip-licenses",
}


def get_dependencies() -> List[Tuple[str, str, str]]:
    """Get list of dependencies and their licenses using pip-licenses."""
    try:
        result = subprocess.run(
            ["pip-licenses", "--format=csv", "--with-urls"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print("Error: pip-licenses not found. Install with: uv add --dev pip-licenses")
        sys.exit(1)

    lines = result.stdout.strip().split("\n")
    if len(lines) < 2:
        print("Error: No dependencies found")
        return []

    # Parse CSV (skip header)
    dependencies = []
    for line in lines[1:]:
        parts = [p.strip().strip('"') for p in line.split(",", 2)]
        if len(parts) >= 3:
            name, version, license_str = parts[0], parts[1], parts[2]
            dependencies.append((name, version, license_str))

    return dependencies


def is_compatible(name: str, license_str: str) -> bool:
    """Check if license is compatible with EUPL-1.2.

    Args:
        name: Package name
        license_str: License string

    Returns:
        True if compatible or if it's a dev-only package
    """
    # Dev-only packages are allowed to use any license
    if name.lower() in DEV_ONLY_PACKAGES:
        return True

    # For runtime packages, check for incompatible licenses
    for pattern in RUNTIME_INCOMPATIBLE_PATTERNS:
        if pattern.lower() in license_str.lower():
            return False
    return True


def main() -> int:
    """Check all dependencies for license compatibility."""
    print("Checking dependency licenses for EUPL-1.2 compatibility...\n")

    dependencies = get_dependencies()
    if not dependencies:
        print("No dependencies found")
        return 0

    incompatible = []
    compatible = []
    dev_only = []

    for name, version, license_str in dependencies:
        if is_compatible(name, license_str):
            if name.lower() in DEV_ONLY_PACKAGES:
                dev_only.append((name, version, license_str))
            else:
                compatible.append((name, version, license_str))
        else:
            incompatible.append((name, version, license_str))

    # Report results
    if incompatible:
        print("❌ INCOMPATIBLE RUNTIME LICENSES FOUND:\n")
        for name, version, license_str in incompatible:
            print(f"  {name} ({version}): {license_str}")
            print("    → Incompatible with EUPL-1.2\n")
        return 1

    print("✓ All dependencies are EUPL-1.2 compatible\n")
    print(f"Total packages checked: {len(dependencies)}")
    print(f"  Runtime (must be compatible): {len(compatible)}")
    print(f"  Development-only: {len(dev_only)}")
    print()

    # Show license summary
    licenses_by_type: Dict[str, int] = {}
    for _, _, license_str in compatible:
        licenses_by_type[license_str] = licenses_by_type.get(license_str, 0) + 1

    print("License breakdown:")
    for license_str, count in sorted(licenses_by_type.items(), key=lambda x: -x[1]):
        print(f"  {license_str}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
