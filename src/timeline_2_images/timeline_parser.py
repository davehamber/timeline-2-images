"""Internal timeline parser module (used by TimelineProcessor).

Note: New OOP code should use timeline_2_images.processors.TimelineProcessor instead.
This module is kept for internal utilities and backward compatibility.
"""

import json
import time
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Set

import pandas as pd

from timeline_2_images.sqlite_cache import (
    load_segments_for_date,
    populate_cache,
    get_cache_stats,
    get_cached_dates,
)


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


class SegmentParser:
    """Parses timeline segments from JSON data."""

    def __init__(self, cache: TimelineCache):
        self.cache = cache

    @staticmethod
    def parse_waypoints(path: list) -> list:
        """Parse waypoints from timeline path with string coordinates."""
        waypoints = []
        for wp in path:
            point = wp.get("point")
            if isinstance(point, str) and "," in point:
                lat_s, lon_s = point.split(",")
                lat_s = lat_s.replace("°", "").strip()
                lon_s = lon_s.replace("°", "").strip()
                try:
                    waypoints.append((float(lat_s), float(lon_s)))
                except ValueError:
                    continue
        return waypoints

    @staticmethod
    def parse_segment_datetime(start_str: str, target: date) -> str | None:
        """Parse segment start time and return if it matches target date."""
        dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt_timestamp):
            return None
        iso_str = str(dt_timestamp.isoformat())  # type: ignore[union-attr]
        parsed_datetime = datetime.fromisoformat(iso_str)
        if parsed_datetime.astimezone(timezone.utc).date() != target:
            return None
        return start_str

    def build_segments_with_waypoints(
        self, segment_list: list[dict], step_start: float, timing: dict
    ) -> list[dict]:
        """Build segment dicts with parsed waypoints from a segment list."""
        segments = []
        for segment in segment_list:
            start_time = segment.get("startTime")
            end_time = segment.get("endTime")
            waypoints = self.parse_waypoints(segment.get("timelinePath", []))

            if waypoints:
                segments.append(
                    {
                        "startTime": start_time,
                        "endTime": end_time,
                        "waypoints": waypoints,
                        "activityType": segment.get("activityType", "unknown"),
                    }
                )

        timing["waypoint_extraction"] = time.time() - step_start
        return segments

    def load_from_sqlite(
        self, json_path: str, target_date: str, timing: dict, start: float
    ) -> list[dict] | None:
        """Try to load segments from SQLite cache."""
        step_start = time.time()
        cached_segments = load_segments_for_date(json_path, target_date)
        timing["sqlite_lookup"] = time.time() - step_start

        if cached_segments is None:
            return None

        timing["cache_source"] = "sqlite"
        step_start = time.time()
        segments = self.build_segments_with_waypoints(cached_segments, step_start, timing)
        timing["total"] = time.time() - start
        return segments

    def load_from_json(
        self, json_path: str, target_date: str, timing: dict, start: float
    ) -> list[dict]:
        """Load segments from JSON and populate cache."""
        step_start = time.time()
        data = self.cache.load_file(json_path)
        timing["json_load"] = time.time() - step_start
        timing["cache_source"] = "json_parsed"

        step_start = time.time()
        populate_cache(json_path, data)
        timing["cache_populate"] = time.time() - step_start

        step_start = time.time()
        segment_date_index = self.cache.build_segment_date_index()
        timing["build_index"] = time.time() - step_start

        step_start = time.time()
        semantic_segs = data.get("semanticSegments", [])
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        matching_indices = segment_date_index.get(target_date_obj, [])
        timing["index_lookup"] = time.time() - step_start

        step_start = time.time()
        matching_segments = [
            semantic_segs[index] for index in matching_indices if index < len(semantic_segs)
        ]
        segments = self.build_segments_with_waypoints(matching_segments, step_start, timing)
        timing["total"] = time.time() - start
        return segments

    def load_for_day(
        self, json_path: str, target_date: str, profile: bool = False
    ) -> list[dict] | tuple[list[dict], dict]:
        """Extract semantic segments for a given date with waypoints."""
        timing: dict = {}
        start = time.time()

        segments = self.load_from_sqlite(json_path, target_date, timing, start)
        if segments is not None:
            return (segments, timing) if profile else segments

        segments = self.load_from_json(json_path, target_date, timing, start)
        return (segments, timing) if profile else segments


class PointExtractor:
    """Extracts location points from timeline JSON data."""

    @staticmethod
    def parse_timestamp(timestamp_value: str | int | float) -> datetime | None:
        """Parse timestamp in various formats (string or milliseconds)."""
        if isinstance(timestamp_value, str):
            parsed_datetime = pd.to_datetime(timestamp_value, utc=True, errors="coerce")
            if pd.isna(parsed_datetime):
                return None
            return datetime.fromisoformat(str(parsed_datetime.isoformat()))  # type: ignore[union-attr]
        return datetime.fromtimestamp(int(timestamp_value) / 1000, tz=timezone.utc)

    @staticmethod
    def extract_location_point(parsed_datetime: datetime, location: dict) -> tuple | None:
        """Extract a single location point if valid coordinates exist."""
        lat: float | None = location.get("latitudeE7")
        lon: float | None = location.get("longitudeE7")
        if lat is not None and lon is not None:
            return (parsed_datetime, float(lat) / 1e7, float(lon) / 1e7)
        return None

    def process_flat_location(self, location: dict, target: date) -> tuple | None:
        """Process a single flat location and return point if in target date."""
        timestamp_value = location.get("timestamp") or location.get("timestampMs")
        if timestamp_value is None:
            return None
        parsed_datetime = self.parse_timestamp(timestamp_value)
        if parsed_datetime is None or parsed_datetime.astimezone(timezone.utc).date() != target:
            return None
        return self.extract_location_point(parsed_datetime, location)

    def extract_from_flat_locations(self, data: dict, target: date) -> list:
        """Extract points from flat locations list."""
        rows = []
        for location in data.get("locations", []):
            point = self.process_flat_location(location, target)
            if point:
                rows.append(point)
        return rows

    @staticmethod
    def extract_waypoints_from_segment(parsed_datetime: datetime, segment: dict) -> list:
        """Extract waypoint rows from a timeline segment."""
        rows = []
        waypoints = segment.get("waypointPath", {}).get("waypoints", [])
        for wp in waypoints:
            lat: float | None = wp.get("latE7")
            lon: float | None = wp.get("lngE7")
            if lat is not None and lon is not None:
                rows.append((parsed_datetime, float(lat) / 1e7, float(lon) / 1e7))
        return rows

    @staticmethod
    def extract_locations_from_segment(parsed_datetime: datetime, segment: dict) -> list:
        """Extract start/end location rows from a timeline segment."""
        rows = []
        for key in ("startLocation", "endLocation", "location"):
            location = segment.get(key)
            if location and "latitudeE7" in location and "longitudeE7" in location:
                rows.append(
                    (
                        parsed_datetime,
                        float(location["latitudeE7"]) / 1e7,
                        float(location["longitudeE7"]) / 1e7,
                    )
                )
        return rows

    @staticmethod
    def get_timeline_object_datetime(segment: dict) -> datetime | None:
        """Extract datetime from a timeline object segment."""
        if not segment:
            return None
        duration = segment.get("duration", {})
        start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
        if start_str is None:
            return None
        parsed_datetime = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(parsed_datetime):
            return None
        return datetime.fromisoformat(str(parsed_datetime.isoformat()))

    @staticmethod
    def matches_target_date(parsed_datetime: datetime | None, target: date) -> bool:
        """Check if datetime matches target date."""
        if parsed_datetime is None:
            return False
        return parsed_datetime.astimezone(timezone.utc).date() == target

    def process_timeline_object(self, obj: dict, target: date) -> list:
        """Process a single timeline object and return points if in target date."""
        segment = obj.get("activitySegment") or obj.get("placeVisit")
        if not isinstance(segment, dict):
            return []
        parsed_datetime = self.get_timeline_object_datetime(segment)
        if not self.matches_target_date(parsed_datetime, target):
            return []
        if parsed_datetime is None:
            return []
        rows = []
        rows.extend(self.extract_waypoints_from_segment(parsed_datetime, segment))
        rows.extend(self.extract_locations_from_segment(parsed_datetime, segment))
        return rows

    def extract_from_timeline_objects(self, data: dict, target: date) -> list:
        """Extract points from timelineObjects (Semantic Location History)."""
        rows = []
        for obj in data.get("timelineObjects", []):
            rows.extend(self.process_timeline_object(obj, target))
        return rows

    @staticmethod
    def parse_point_string(parsed_datetime, point: str) -> tuple | None:
        """Parse a single point string coordinate."""
        if not isinstance(point, str) or "," not in point:
            return None
        lat_s, lon_s = point.split(",")
        lat_s = lat_s.replace("°", "").strip()
        lon_s = lon_s.replace("°", "").strip()
        try:
            return (parsed_datetime, float(lat_s), float(lon_s))
        except ValueError:
            return None

    @staticmethod
    def get_semantic_segment_datetime(segment: dict) -> datetime | None:
        """Extract datetime from a semantic segment."""
        start_str = segment.get("startTime")
        if not start_str:
            return None
        parsed_datetime = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(parsed_datetime):
            return None
        return datetime.fromisoformat(str(parsed_datetime.isoformat()))

    @staticmethod
    def extract_points_from_segment_path(parsed_datetime, segment: dict) -> list:
        """Extract all points from a segment's path."""
        path = segment.get("timelinePath", []) or segment.get("waypointPath", {}).get(
            "waypoints", []
        )
        rows = []
        for wp in path:
            point = wp.get("point")
            point = PointExtractor.parse_point_string(parsed_datetime, point)
            if point:
                rows.append(point)
        return rows

    def process_semantic_segment(self, segment: dict, target: date) -> list:
        """Process a single semantic segment and return points if in target date."""
        parsed_datetime = self.get_semantic_segment_datetime(segment)
        if not self.matches_target_date(parsed_datetime, target):
            return []
        if parsed_datetime is None:
            return []
        return self.extract_points_from_segment_path(parsed_datetime, segment)

    def extract_from_semantic_segments(self, data: dict, target: date) -> list:
        """Extract points from semanticSegments, handling both visits and activities."""
        rows = []
        for segment in data.get("semanticSegments", []):
            segment_rows = self.process_semantic_segment(segment, target)
            if segment_rows:
                rows.extend(segment_rows)
        return rows

    def load_points_for_day(self, json_path: str, target_date: str) -> pd.DataFrame:
        """Extract (timestamp, lat, lon) rows for the given YYYY-MM-DD date."""
        cache = _cache
        data = cache.load_file(json_path)
        target = datetime.strptime(target_date, "%Y-%m-%d").date()

        rows = []
        rows.extend(self.extract_from_flat_locations(data, target))
        rows.extend(self.extract_from_timeline_objects(data, target))
        rows.extend(self.extract_from_semantic_segments(data, target))

        if not rows:
            raise ValueError(
                f"No points found for {target_date}. Check the Timeline JSON structure."
            )

        df = pd.DataFrame(rows, columns=["timestamp", "lat", "lon"]).sort_values("timestamp")
        return df


class DateExtractor:
    """Extracts and filters dates from timeline JSON data."""

    def __init__(self, data: dict):
        self.data = data

    def extract_from_flat_locations(self) -> Set[date]:
        """Extract unique dates from flat locations list."""
        dates = set()
        for location in self.data.get("locations", []):
            timestamp_value = location.get("timestamp") or location.get("timestampMs")
            if timestamp_value is None:
                continue
            parsed_datetime = PointExtractor.parse_timestamp(timestamp_value)
            if parsed_datetime is not None:
                dates.add(parsed_datetime.astimezone(timezone.utc).date())
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
        dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt_timestamp):
            return None
        parsed_datetime = datetime.fromisoformat(str(dt_timestamp.isoformat()))
        return parsed_datetime.astimezone(timezone.utc).date()

    def extract_from_timeline_objects(self) -> Set[date]:
        """Extract unique dates from timelineObjects."""
        dates = set()
        for obj in self.data.get("timelineObjects", []):
            segment = obj.get("activitySegment") or obj.get("placeVisit")
            if not segment:
                continue
            segment_date = self.get_segment_start_date(segment)
            if segment_date:
                dates.add(segment_date)
        return dates

    def extract_from_segments(self) -> Set[date]:
        """Extract unique dates from semanticSegments."""
        dates = set()
        for segment in self.data.get("semanticSegments", []):
            start_str = segment.get("startTime")
            if not start_str:
                continue
            parsed_datetime = pd.to_datetime(start_str, utc=True, errors="coerce")
            if pd.isna(parsed_datetime):
                continue
            dates.add(parsed_datetime.to_pydatetime().astimezone(timezone.utc).date())
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


_cache = TimelineCache()
_segment_parser = SegmentParser(_cache)
_point_extractor = PointExtractor()


def load_segments_for_day(
    json_path: str, target_date: str, profile: bool = False
) -> list[dict] | tuple[list[dict], dict]:
    """Extract semantic segments for a given date with waypoints."""
    return _segment_parser.load_for_day(json_path, target_date, profile)


def load_points_for_day(json_path: str, target_date: str) -> pd.DataFrame:
    """Extract (timestamp, lat, lon) rows for the given YYYY-MM-DD date."""
    return _point_extractor.load_points_for_day(json_path, target_date)


def get_last_n_days_with_data(json_path: str, days: int = 14) -> list[str]:
    """Find the last N days that have timeline data."""
    _cache.load_file(json_path)
    _cache.build_date_index()

    if not _cache.date_index:
        return []

    sorted_dates = sorted(_cache.date_index.keys(), reverse=True)
    last_n = sorted_dates[:days]
    return sorted([d.strftime("%Y-%m-%d") for d in last_n])


def _get_available_dates(json_path: str) -> list[date]:
    """Get available dates from cache or JSON file."""
    cached_dates = get_cached_dates(json_path)
    if cached_dates:
        _cache.cache_source = "disk"
        return [datetime.strptime(d, "%Y-%m-%d").date() for d in cached_dates]

    _cache.load_file(json_path)
    _cache.build_date_index()
    if not _cache.date_index:
        return []
    return sorted(_cache.date_index.keys())


def get_all_available_dates(json_path: str) -> list[str]:
    """Get ALL dates with data in timeline (no filtering)."""
    available_dates = _get_available_dates(json_path)
    if not available_dates:
        return []
    return [d.strftime("%Y-%m-%d") for d in sorted(available_dates)]


def get_date_range(
    json_path: str,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 14,
) -> list[str]:
    """Get dates with data based on flexible date range parameters."""
    available_dates = _get_available_dates(json_path)
    if not available_dates:
        return []

    bounds = DateExtractor.calculate_date_bounds(start_date, end_date, days)
    if bounds is None:
        return get_last_n_days_with_data(json_path, days)

    start, end = bounds
    return DateExtractor.filter_dates_in_range(available_dates, start, end)


def get_cache_source() -> str:
    """Return the source of the most recent cache load."""
    return _cache.cache_source


def get_sqlite_cache_stats(json_path: str) -> dict:
    """Return SQLite segment cache statistics."""
    return get_cache_stats(json_path)


def clear_cache() -> None:
    """Clear the session cache. Useful for testing or memory management."""
    _cache.clear()
