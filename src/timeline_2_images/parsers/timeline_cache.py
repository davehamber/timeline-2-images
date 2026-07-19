"""Session-level cache for Timeline JSON data."""

import json
from datetime import date
from typing import Dict


class TimelineCache:
    """Session-level cache for Timeline JSON data.

    Caches the full parsed JSON structure in memory for the lifetime of the session.
    SQLite database provides persistent segment caching across sessions.
    """

    def __init__(self):
        self.file_path: str | None = None
        self.data: dict | None = None
        self.date_index: Dict[date, bool] | None = None
        self.segment_date_index: Dict[date, list[int]] | None = None
        self.cache_source: str = "none"

    def load_file(self, json_path: str) -> dict:
        """Load and cache Timeline JSON file. Returns cached data if already loaded."""
        if self.file_path == json_path and self.data is not None:
            self.cache_source = "session"
            return self.data

        self.file_path = json_path
        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.date_index = None
        self.cache_source = "parsed"
        assert self.data is not None
        return self.data

    def build_date_index(self) -> Dict[date, bool]:
        """Build an index of all dates with data for fast lookup."""
        if self.date_index is not None:
            return self.date_index

        self.date_index = {}
        if not self.data:
            return self.date_index

        from timeline_2_images.parsers.date_extractor import DateExtractor

        extractor = DateExtractor(self.data)
        all_dates = set()
        all_dates.update(extractor.extract_from_flat_locations())
        all_dates.update(extractor.extract_from_timeline_objects())
        all_dates.update(extractor.extract_from_segments())

        for d in all_dates:
            self.date_index[d] = True

        return self.date_index

    def build_segment_date_index(self) -> Dict[date, list[int]]:
        """Build an index mapping dates to segment indices for fast lookups."""
        if self.segment_date_index is not None:
            return self.segment_date_index

        self.segment_date_index = {}
        if not self.data:
            return self.segment_date_index

        from timeline_2_images.parsers.date_extractor import DateExtractor

        semantic_segs = self.data.get("semanticSegments", [])
        for index, segment in enumerate(semantic_segs):
            seg_date = DateExtractor.get_segment_start_date(segment)
            if seg_date:
                self.segment_date_index.setdefault(seg_date, []).append(index)

        return self.segment_date_index

    def clear(self) -> None:
        """Clear the cache."""
        self.file_path = None
        self.data = None
        self.date_index = None
        self.segment_date_index = None
