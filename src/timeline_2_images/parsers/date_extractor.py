"""Extracts and filters dates from timeline JSON data."""

import time
from datetime import date, datetime, timedelta, timezone
from typing import Set

import pandas as pd


class DateExtractor:
    """Extracts and filters dates from timeline JSON data."""

    def __init__(self, data: dict):
        self.data = data

    def extract_from_flat_locations(self) -> Set[date]:
        """Extract unique dates from flat locations list."""
        from timeline_2_images.parsers.point_extractor import PointExtractor

        start = time.time()
        dates = set()
        for location in self.data.get("locations", []):
            timestamp_value = location.get("timestamp") or location.get("timestampMs")
            if timestamp_value is None:
                continue
            parsed_datetime = PointExtractor.parse_timestamp(timestamp_value)
            if parsed_datetime is not None:
                dates.add(parsed_datetime.astimezone(timezone.utc).date())
        elapsed = time.time() - start
        location_count = len(self.data.get("locations", []))
        print(
            f"[TIMING]   extract_from_flat_locations: {elapsed:.2f}s "
            f"({len(dates)} dates from {location_count} locations)"
        )
        return dates

    @staticmethod
    def get_segment_start_date(segment: dict) -> date | None:
        """Extract start date from a timeline segment."""
        start_str = segment.get("startTime")
        if not start_str:
            duration = segment.get("duration", {})
            start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
        if start_str is None:
            return None
        # Try fast path first: fromisoformat
        try:
            if isinstance(start_str, str):
                if start_str.endswith("Z"):
                    parsed_datetime = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    parsed_datetime = datetime.fromisoformat(start_str)
            else:
                # Handle numeric timestamps (milliseconds)
                parsed_datetime = datetime.fromtimestamp(start_str / 1000, tz=timezone.utc)
            return parsed_datetime.astimezone(timezone.utc).date()
        except (ValueError, TypeError):
            # Fallback to pandas for non-standard formats
            try:
                dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
                if pd.isna(dt_timestamp):
                    return None
                return dt_timestamp.to_pydatetime().astimezone(timezone.utc).date()
            except Exception:
                return None

    def extract_from_timeline_objects(self) -> Set[date]:
        """Extract unique dates from timelineObjects."""
        start = time.time()
        dates = set()
        for obj in self.data.get("timelineObjects", []):
            segment = obj.get("activitySegment") or obj.get("placeVisit")
            if not segment:
                continue
            segment_date = self.get_segment_start_date(segment)
            if segment_date:
                dates.add(segment_date)
        elapsed = time.time() - start
        object_count = len(self.data.get("timelineObjects", []))
        print(
            f"[TIMING]   extract_from_timeline_objects: {elapsed:.2f}s "
            f"({len(dates)} dates from {object_count} objects)"
        )
        return dates

    def extract_from_segments(self) -> Set[date]:
        """Extract unique dates from semanticSegments."""
        start = time.time()
        dates = set()
        for segment in self.data.get("semanticSegments", []):
            start_str = segment.get("startTime")
            if not start_str:
                continue
            # Try fast path first: fromisoformat (10x faster than pd.to_datetime)
            try:
                # Handle ISO 8601 format with Z or ±HH:MM timezone
                if start_str.endswith("Z"):
                    parsed_datetime = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    parsed_datetime = datetime.fromisoformat(start_str)
                dates.add(parsed_datetime.astimezone(timezone.utc).date())
            except (ValueError, TypeError):
                # Fallback to pandas for non-standard formats
                try:
                    parsed_datetime = pd.to_datetime(start_str, utc=True, errors="coerce")
                    if not pd.isna(parsed_datetime):
                        dates.add(parsed_datetime.to_pydatetime().astimezone(timezone.utc).date())
                except Exception:
                    pass  # Skip unparseable timestamps
        elapsed = time.time() - start
        segment_count = len(self.data.get("semanticSegments", []))
        print(
            f"[TIMING]   extract_from_segments: {elapsed:.2f}s "
            f"({len(dates)} dates from {segment_count} segments)"
        )
        return dates

    @staticmethod
    def parse_date_string(date_str: str) -> date:
        """Parse YYYY-MM-DD string to date."""
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    @staticmethod
    def calculate_date_bounds(
        start_date: str | None, end_date: str | None, days: int
    ) -> tuple[date, date] | None:
        """Calculate start and end dates from parameters."""
        if start_date and end_date:
            return DateExtractor.parse_date_string(start_date), DateExtractor.parse_date_string(
                end_date
            )
        if start_date:
            start = DateExtractor.parse_date_string(start_date)
            end = start + timedelta(days=days - 1)
            return start, end
        if end_date:
            end = DateExtractor.parse_date_string(end_date)
            start = end - timedelta(days=days - 1)
            return start, end
        return None

    @staticmethod
    def filter_dates_in_range(available_dates: list[date], start: date, end: date) -> list[str]:
        """Filter dates within range and format as strings."""
        result = [d for d in available_dates if start <= d <= end]
        return [d.strftime("%Y-%m-%d") for d in result]
