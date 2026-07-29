# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Clean up old Nuitka cache versions on macOS to prevent disk bloat."""

import shutil
from pathlib import Path


def cleanup_old_cache_versions(current_version: str) -> None:
    """Remove cache directories for older versions of the CLI.

    Nuitka caches extracted binaries in ~/.cache/timeline2images/{VERSION} on macOS.
    This function cleans up versions other than the current one to prevent
    accumulation across multiple releases.

    Args:
        current_version: Current application version (e.g., "0.7.1")
    """
    # Check both possible cache locations for backwards compatibility
    cache_locations = [
        Path.home() / ".cache" / "timeline2images",  # Current: explicit {HOME}/.cache path
        Path.home() / "Library" / "Caches" / "timeline2images",  # Previous: {CACHE_DIR}
    ]

    for cache_base in cache_locations:
        if not cache_base.exists():
            continue

        try:
            for version_dir in cache_base.iterdir():
                if version_dir.is_dir() and version_dir.name != current_version:
                    # Remove old version cache
                    shutil.rmtree(version_dir, ignore_errors=True)
        except (OSError, PermissionError):
            # Silently ignore cleanup errors (cache might be in use, user lacks permissions, etc.)
            pass
