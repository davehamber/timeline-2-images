# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Session-level cache for parsed timeline segments with MD5-based invalidation."""

import hashlib
from pathlib import Path
from typing import Optional

from timeline_2_images.models import Segment


class SegmentCache:
    """Session-level cache for parsed segments indexed by date.

    Segments are cached in memory for the lifetime of the session.
    Cache is automatically invalidated if the source file's MD5 changes.
    """

    def __init__(self):
        self.file_md5: Optional[str] = None
        self.segments_by_date: dict[str, list[Segment]] = {}

    def _compute_md5(self, json_path: str) -> str:
        """Compute MD5 hash of the JSON file."""
        md5_hash = hashlib.md5()
        with open(json_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def _validate_file(self, json_path: str) -> bool:
        """Check if file MD5 matches cached MD5. Invalidate if different."""
        current_md5 = self._compute_md5(json_path)

        if self.file_md5 is None:
            # First time - store the MD5
            self.file_md5 = current_md5
            return True

        if current_md5 != self.file_md5:
            # File changed - invalidate cache
            self.file_md5 = current_md5
            self.segments_by_date.clear()
            return False

        return True

    def get(self, json_path: str, date_str: str) -> Optional[list[Segment]]:
        """Get cached segments for a date if file hasn't changed.

        Args:
            json_path: Path to Timeline.json file
            date_str: Date in YYYY-MM-DD format

        Returns:
            Cached segments if available and file unchanged, None otherwise
        """
        if not self._validate_file(json_path):
            return None
        return self.segments_by_date.get(date_str)

    def set(self, json_path: str, date_str: str, segments: list[Segment]) -> None:
        """Cache segments for a date.

        Args:
            json_path: Path to Timeline.json file
            date_str: Date in YYYY-MM-DD format
            segments: List of Segment objects to cache
        """
        # Validate file before caching
        if not self._validate_file(json_path):
            return
        self.segments_by_date[date_str] = segments

    def clear(self) -> None:
        """Clear the cache."""
        self.file_md5 = None
        self.segments_by_date.clear()
