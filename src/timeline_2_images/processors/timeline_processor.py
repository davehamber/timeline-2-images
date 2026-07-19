"""Timeline data processor."""

from typing import Any

import pandas as pd

from timeline_2_images.models import Segment
from timeline_2_images.config import DateRangeQuery
from timeline_2_images.parsers import TimelineParserFacade


class TimelineProcessor:
    """Processes timeline JSON data and provides access to segments and points."""

    def __init__(self, json_path: str, parser_facade: TimelineParserFacade | None = None):
        """Initialize processor with timeline JSON path and optional parser facade.

        Args:
            json_path: Path to Timeline.json file
            parser_facade: TimelineParserFacade instance (created if not provided)
        """
        self.json_path = json_path
        self._parser = parser_facade or TimelineParserFacade()

    def load_segments_for_day(self, date: str) -> list[Segment]:
        """Load segments for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of Segment objects
        """
        raw_segments_result = self._parser.load_segments_for_day(self.json_path, date)
        if isinstance(raw_segments_result, tuple):
            raw_segments = raw_segments_result[0]
        else:
            raw_segments = raw_segments_result

        if not raw_segments:
            return []

        segments = []
        for raw_segment in raw_segments:
            segment = self._build_segment_from_raw(raw_segment)
            segments.append(segment)

        return segments

    def load_points_for_day(self, date: str) -> pd.DataFrame:
        """Load all points for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            DataFrame with columns: timestamp, lat, lon
        """
        return self._parser.load_points_for_day(self.json_path, date)

    def get_available_dates(self) -> list[str]:
        """Get all dates with data in the timeline.

        Returns:
            List of all YYYY-MM-DD date strings (not filtered by days)
        """
        return self._parser.get_all_available_dates(self.json_path)

    def get_date_range(self, query: DateRangeQuery) -> list[str]:
        """Get dates matching query parameters.

        Args:
            query: DateRangeQuery object with date parameters

        Returns:
            List of YYYY-MM-DD date strings matching query
        """
        query.validate()
        available_dates = self.get_available_dates()
        return query.get_dates(available_dates)

    def _build_segment_from_raw(self, raw_segment: dict[str, Any]) -> Segment:
        """Build Segment object from raw segment dictionary.

        Args:
            raw_segment: Raw segment dict with startTime, endTime, waypoints

        Returns:
            Segment object
        """
        start_str = raw_segment.get("startTime", "")
        end_str = raw_segment.get("endTime", "")
        waypoints = raw_segment.get("waypoints", [])

        start_time = pd.to_datetime(start_str, utc=True)
        end_time = pd.to_datetime(end_str, utc=True)

        return Segment(
            start_time=start_time.to_pydatetime(),
            end_time=end_time.to_pydatetime(),
            waypoints=waypoints,
            segment_type="journey",
        )

    def clear_cache(self) -> None:
        """Clear session cache."""
        self._parser.clear_cache()

    def get_cache_source(self) -> str:
        """Get source of last cache operation."""
        return self._parser.get_cache_source()
