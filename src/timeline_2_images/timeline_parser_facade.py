"""Facade providing OOP interface for timeline parsing operations."""

from datetime import date, datetime

import pandas as pd

from timeline_2_images.timeline_cache import TimelineCache
from timeline_2_images.segment_parser import SegmentParser
from timeline_2_images.point_extractor import PointExtractor
from timeline_2_images.date_extractor import DateExtractor
from timeline_2_images.sqlite_cache import SegmentCache


class TimelineParserFacade:
    """Facade providing OOP interface for timeline parsing operations.

    Coordinates TimelineCache, SegmentParser, PointExtractor, and SegmentCache
    to provide a unified API for timeline operations.
    """

    def __init__(
        self,
        timeline_cache: TimelineCache | None = None,
        segment_parser: SegmentParser | None = None,
        point_extractor: PointExtractor | None = None,
        segment_cache: SegmentCache | None = None,
    ):
        """Initialize timeline parser facade with optional dependency injection.

        Args:
            timeline_cache: Session-level cache (created if not provided)
            segment_parser: Segment parser (created if not provided)
            point_extractor: Point extractor (created if not provided)
            segment_cache: SQLite segment cache (created if not provided)
        """
        self._timeline_cache = timeline_cache or TimelineCache()
        self._segment_cache = segment_cache or SegmentCache()
        self._segment_parser = segment_parser or SegmentParser(
            self._timeline_cache, self._segment_cache
        )
        self._point_extractor = point_extractor or PointExtractor(self._timeline_cache)

    def load_segments_for_day(
        self, json_path: str, target_date: str, profile: bool = False
    ) -> list[dict] | tuple[list[dict], dict]:
        """Extract semantic segments for a given date with waypoints."""
        return self._segment_parser.load_for_day(json_path, target_date, profile)

    def load_points_for_day(self, json_path: str, target_date: str) -> pd.DataFrame:
        """Extract (timestamp, lat, lon) rows for the given YYYY-MM-DD date."""
        return self._point_extractor.load_points_for_day(json_path, target_date)

    def get_last_n_days_with_data(self, json_path: str, days: int = 14) -> list[str]:
        """Find the last N days that have timeline data."""
        self._timeline_cache.load_file(json_path)
        self._timeline_cache.build_date_index()

        if not self._timeline_cache.date_index:
            return []

        sorted_dates = sorted(self._timeline_cache.date_index.keys(), reverse=True)
        last_n = sorted_dates[:days]
        return sorted([d.strftime("%Y-%m-%d") for d in last_n])

    def get_available_dates(
        self, json_path: str, segment_cache: SegmentCache | None = None
    ) -> list[date]:
        """Get available dates from cache or JSON file."""
        cache = segment_cache or self._segment_cache
        cached_dates = cache.get_cached_dates(json_path)
        if cached_dates:
            self._timeline_cache.cache_source = "disk"
            return [datetime.strptime(d, "%Y-%m-%d").date() for d in cached_dates]

        self._timeline_cache.load_file(json_path)
        self._timeline_cache.build_date_index()
        if not self._timeline_cache.date_index:
            return []
        return sorted(self._timeline_cache.date_index.keys())

    def get_all_available_dates(self, json_path: str) -> list[str]:
        """Get ALL dates with data in timeline (no filtering)."""
        available_dates = self.get_available_dates(json_path)
        if not available_dates:
            return []
        return [d.strftime("%Y-%m-%d") for d in sorted(available_dates)]

    def get_date_range(
        self,
        json_path: str,
        start_date: str | None = None,
        end_date: str | None = None,
        days: int = 14,
    ) -> list[str]:
        """Get dates with data based on flexible date range parameters."""
        available_dates = self.get_available_dates(json_path)
        if not available_dates:
            return []

        bounds = DateExtractor.calculate_date_bounds(start_date, end_date, days)
        if bounds is None:
            return self.get_last_n_days_with_data(json_path, days)

        start, end = bounds
        return DateExtractor.filter_dates_in_range(available_dates, start, end)

    def get_cache_source(self) -> str:
        """Return the source of the most recent cache load."""
        return self._timeline_cache.cache_source

    def get_sqlite_cache_stats(self, json_path: str) -> dict:
        """Return SQLite segment cache statistics."""
        return self._segment_cache.get_cache_stats(json_path)

    def clear_cache(self) -> None:
        """Clear the session cache. Useful for testing or memory management."""
        self._timeline_cache.clear()
