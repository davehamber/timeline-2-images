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
        self.segment_date_index: Dict[date, list[int]] | None = None  # date → segment indices
        self.cache_source: str = "none"  # Track which cache was used

    def load_file(self, json_path: str) -> dict:
        """Load and cache Timeline JSON file. Returns cached data if already loaded.

        Priority:
        1. Session memory cache (fastest)
        2. Parse raw JSON if not in memory

        Sets cache_source to one of: "session", "parsed"
        """
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

        all_dates = set()
        all_dates.update(_extract_dates_from_locations(self.data))
        all_dates.update(_extract_dates_from_timeline_objects(self.data))
        all_dates.update(_extract_dates_from_segments(self.data))

        for d in all_dates:
            self.date_index[d] = True

        return self.date_index

    def build_segment_date_index(self) -> Dict[date, list[int]]:
        """Build an index mapping dates to segment indices for fast lookups.

        Parses all segment dates once and caches the result.
        Returns dict: {date: [segment_indices]}
        """
        if self.segment_date_index is not None:
            return self.segment_date_index

        self.segment_date_index = {}
        if not self.data:
            return self.segment_date_index

        semantic_segs = self.data.get("semanticSegments", [])
        for index, segment in enumerate(semantic_segs):
            seg_date = _get_segment_start_date(segment)
            if seg_date:
                self.segment_date_index.setdefault(seg_date, []).append(index)

        return self.segment_date_index

    def clear(self) -> None:
        """Clear the cache."""
        self.file_path = None
        self.data = None
        self.date_index = None
        self.segment_date_index = None


_cache = TimelineCache()


def _parse_semantic_segments_iter(data: dict):
    """Iterate through semanticSegments with parsed datetimes.

    Yields (segment, datetime) tuples for segments with valid startTime.
    """
    for segment in data.get("semanticSegments", []):
        start_str = segment.get("startTime")
        if not start_str:
            continue
        parsed_datetime = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(parsed_datetime):
            continue
        yield segment, parsed_datetime.to_pydatetime()


def _parse_waypoints(path: list) -> list:
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


def _parse_segment_datetime(start_str: str, target: date) -> str | None:
    """Parse segment start time and return if it matches target date."""
    dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt_timestamp):
        return None
    parsed_datetime = datetime.fromisoformat(str(dt_timestamp.isoformat()))  # type: ignore[union-attr]
    if parsed_datetime.astimezone(timezone.utc).date() != target:
        return None
    return start_str


def _build_segments_with_waypoints(
    segment_list: list[dict], step_start: float, timing: dict
) -> list[dict]:
    """Build segment dicts with parsed waypoints from a segment list."""
    segments = []
    for segment in segment_list:
        waypoints = _parse_waypoints(segment.get("timelinePath", []))
        if waypoints:
            segments.append(
                {
                    "startTime": segment.get("startTime"),
                    "endTime": segment.get("endTime"),
                    "waypoints": waypoints,
                }
            )
    timing["waypoint_extraction"] = time.time() - step_start
    return segments


def _load_segments_from_sqlite(
    json_path: str, target_date: str, timing: dict, start: float
) -> list[dict] | None:
    """Try to load segments from SQLite cache."""
    step_start = time.time()
    cached_segments = load_segments_for_date(json_path, target_date)
    timing["sqlite_lookup"] = time.time() - step_start

    if cached_segments is None:
        return None

    timing["cache_source"] = "sqlite"
    step_start = time.time()
    segments = _build_segments_with_waypoints(cached_segments, step_start, timing)
    timing["total"] = time.time() - start
    return segments


def _load_segments_from_json(
    json_path: str, target_date: str, timing: dict, start: float
) -> list[dict]:
    """Load segments from JSON and populate cache."""
    step_start = time.time()
    data = _cache.load_file(json_path)
    timing["json_load"] = time.time() - step_start
    timing["cache_source"] = "json_parsed"

    step_start = time.time()
    populate_cache(json_path, data)
    timing["cache_populate"] = time.time() - step_start

    step_start = time.time()
    segment_date_index = _cache.build_segment_date_index()
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
    segments = _build_segments_with_waypoints(matching_segments, step_start, timing)
    timing["total"] = time.time() - start
    return segments


def load_segments_for_day(
    json_path: str, target_date: str, profile: bool = False
) -> list[dict] | tuple[list[dict], dict]:
    """
    Extract semantic segments for a given date with waypoints.

    Each segment represents a distinct journey/stay period.
    Uses SQLite cache indexed by date for fast lookups.

    Args:
        json_path: Path to Timeline.json file
        target_date: Date in YYYY-MM-DD format
        profile: If True, return (segments, timing_dict) instead of just segments

    Returns:
        List of segment dicts, or (segments, timing) tuple if profile=True
    """
    timing: dict = {}
    start = time.time()

    segments = _load_segments_from_sqlite(json_path, target_date, timing, start)
    if segments is not None:
        return (segments, timing) if profile else segments

    segments = _load_segments_from_json(json_path, target_date, timing, start)
    return (segments, timing) if profile else segments


def _parse_timestamp(timestamp_value: str | int | float) -> datetime | None:
    """Parse timestamp in various formats (string or milliseconds)."""
    if isinstance(timestamp_value, str):
        parsed_datetime = pd.to_datetime(timestamp_value, utc=True, errors="coerce")
        if pd.isna(parsed_datetime):
            return None
        return datetime.fromisoformat(str(parsed_datetime.isoformat()))  # type: ignore[union-attr]
    return datetime.fromtimestamp(int(timestamp_value) / 1000, tz=timezone.utc)


def _extract_location_point(parsed_datetime: datetime, location: dict) -> tuple | None:
    """Extract a single location point if valid coordinates exist."""
    lat: float | None = location.get("latitudeE7")
    lon: float | None = location.get("longitudeE7")
    if lat is not None and lon is not None:
        return (parsed_datetime, float(lat) / 1e7, float(lon) / 1e7)
    return None


def _process_flat_location(location: dict, target: date) -> tuple | None:
    """Process a single flat location and return point if in target date."""
    timestamp_value = location.get("timestamp") or location.get("timestampMs")
    if timestamp_value is None:
        return None
    parsed_datetime = _parse_timestamp(timestamp_value)
    if parsed_datetime is None or parsed_datetime.astimezone(timezone.utc).date() != target:
        return None
    return _extract_location_point(parsed_datetime, location)


def _extract_from_flat_locations(data: dict, target: date) -> list:
    """Extract points from flat locations list."""
    rows = []
    for location in data.get("locations", []):
        point = _process_flat_location(location, target)
        if point:
            rows.append(point)
    return rows


def _extract_waypoints_from_segment(parsed_datetime: datetime, segment: dict) -> list:
    """Extract waypoint rows from a timeline segment."""
    rows = []
    waypoints = segment.get("waypointPath", {}).get("waypoints", [])
    for wp in waypoints:
        lat: float | None = wp.get("latE7")
        lon: float | None = wp.get("lngE7")
        if lat is not None and lon is not None:
            rows.append((parsed_datetime, float(lat) / 1e7, float(lon) / 1e7))
    return rows


def _extract_locations_from_segment(parsed_datetime: datetime, segment: dict) -> list:
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


def _get_timeline_object_datetime(segment: dict) -> datetime | None:
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


def _matches_target_date(parsed_datetime: datetime | None, target: date) -> bool:
    """Check if datetime matches target date."""
    if parsed_datetime is None:
        return False
    return parsed_datetime.astimezone(timezone.utc).date() == target


def _process_timeline_object(obj: dict, target: date) -> list:
    """Process a single timeline object and return points if in target date."""
    segment = obj.get("activitySegment") or obj.get("placeVisit")
    if not isinstance(segment, dict):
        return []
    parsed_datetime = _get_timeline_object_datetime(segment)
    if not _matches_target_date(parsed_datetime, target):
        return []
    if parsed_datetime is None:
        return []
    rows = []
    rows.extend(_extract_waypoints_from_segment(parsed_datetime, segment))
    rows.extend(_extract_locations_from_segment(parsed_datetime, segment))
    return rows


def _extract_from_timeline_objects(data: dict, target: date) -> list:
    """Extract points from timelineObjects (Semantic Location History)."""
    rows = []
    for obj in data.get("timelineObjects", []):
        rows.extend(_process_timeline_object(obj, target))
    return rows


def _parse_point_string(parsed_datetime, point: str) -> tuple | None:
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


def _get_semantic_segment_datetime(segment: dict) -> datetime | None:
    """Extract datetime from a semantic segment."""
    start_str = segment.get("startTime")
    if not start_str:
        return None
    parsed_datetime = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(parsed_datetime):
        return None
    return datetime.fromisoformat(str(parsed_datetime.isoformat()))


def _extract_points_from_segment_path(parsed_datetime, segment: dict) -> list:
    """Extract all points from a segment's path."""
    path = segment.get("timelinePath", []) or segment.get("waypointPath", {}).get("waypoints", [])
    rows = []
    for wp in path:
        point = wp.get("point")
        point = _parse_point_string(parsed_datetime, point)
        if point:
            rows.append(point)
    return rows


def _process_semantic_segment(segment: dict, target: date) -> list:
    """Process a single semantic segment and return points if in target date."""
    parsed_datetime = _get_semantic_segment_datetime(segment)
    if not _matches_target_date(parsed_datetime, target):
        return []
    if parsed_datetime is None:
        return []
    return _extract_points_from_segment_path(parsed_datetime, segment)


def _extract_from_semantic_segments(data: dict, target: date) -> list:
    """Extract points from semanticSegments with string coordinates."""
    rows = []
    for segment in data.get("semanticSegments", []):
        rows.extend(_process_semantic_segment(segment, target))
    return rows


def load_points_for_day(json_path: str, target_date: str) -> pd.DataFrame:
    """
    Extract (timestamp, lat, lon) rows for the given YYYY-MM-DD date.

    Handles three known Google Timeline export shapes:
      1. Old "Records.json" style with flat locations list
      2. Semantic Location History with timelineObjects
      3. Newer on-device export with semanticSegments

    Uses session-level caching to avoid re-parsing large files.

    Args:
        json_path: Path to the Timeline JSON file
        target_date: Date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: timestamp, lat, lon (sorted by timestamp)

    Raises:
        ValueError: If no points found for the target date
    """
    data = _cache.load_file(json_path)

    target = datetime.strptime(target_date, "%Y-%m-%d").date()

    rows = []
    rows.extend(_extract_from_flat_locations(data, target))
    rows.extend(_extract_from_timeline_objects(data, target))
    rows.extend(_extract_from_semantic_segments(data, target))

    if not rows:
        raise ValueError(f"No points found for {target_date}. Check the Timeline JSON structure.")

    df = pd.DataFrame(rows, columns=["timestamp", "lat", "lon"]).sort_values("timestamp")
    return df


def _extract_dates_from_locations(data: dict) -> Set[date]:
    """Extract unique dates from flat locations list."""
    dates = set()
    for location in data.get("locations", []):
        timestamp_value = location.get("timestamp") or location.get("timestampMs")
        if timestamp_value is None:
            continue
        parsed_datetime = _parse_timestamp(timestamp_value)
        if parsed_datetime is not None:
            dates.add(parsed_datetime.astimezone(timezone.utc).date())
    return dates


def _get_segment_start_date(segment: dict) -> date | None:
    """Extract start date from a timeline segment."""
    duration = segment.get("duration", {})
    start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
    if start_str is None:
        return None
    dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt_timestamp):
        return None
    parsed_datetime = datetime.fromisoformat(str(dt_timestamp.isoformat()))
    return parsed_datetime.astimezone(timezone.utc).date()


def _extract_dates_from_timeline_objects(data: dict) -> Set[date]:
    """Extract unique dates from timelineObjects."""
    dates = set()
    for obj in data.get("timelineObjects", []):
        segment = obj.get("activitySegment") or obj.get("placeVisit")
        if not segment:
            continue
        segment_date = _get_segment_start_date(segment)
        if segment_date:
            dates.add(segment_date)
    return dates


def _extract_dates_from_segments(data: dict) -> Set[date]:
    """Extract unique dates from semanticSegments."""
    dates = set()
    for _, parsed_datetime in _parse_semantic_segments_iter(data):
        dates.add(parsed_datetime.astimezone(timezone.utc).date())
    return dates


def get_last_n_days_with_data(json_path: str, days: int = 14) -> list[str]:
    """
    Find the last N days that have timeline data.

    Uses session-level caching to avoid re-parsing.

    Returns dates in YYYY-MM-DD format, sorted chronologically.
    """
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


def _parse_date_string(date_str: str) -> date:
    """Parse YYYY-MM-DD string to date."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _calculate_date_bounds(
    start_date: str | None, end_date: str | None, days: int
) -> tuple[date, date] | None:
    """Calculate start and end dates from parameters. Returns None for day-based fallback."""
    if start_date and end_date:
        return _parse_date_string(start_date), _parse_date_string(end_date)
    if start_date:
        start = _parse_date_string(start_date)
        end = start + timedelta(days=days - 1)
        return start, end
    if end_date:
        end = _parse_date_string(end_date)
        start = end - timedelta(days=days - 1)
        return start, end
    return None


def _filter_dates_in_range(available_dates: list[date], start: date, end: date) -> list[str]:
    """Filter dates within range and format as strings."""
    result = [d for d in available_dates if start <= d <= end]
    return [d.strftime("%Y-%m-%d") for d in result]


def get_all_available_dates(json_path: str) -> list[str]:
    """
    Get ALL dates with data in timeline (no filtering).

    Returns:
        List of all YYYY-MM-DD dates with data, sorted chronologically
    """
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
    """
    Get dates with data based on flexible date range parameters.

    Uses SQLite cache when available to avoid re-parsing large files.
    Falls back to session-level caching if SQLite cache is unavailable.

    Priority:
    1. If both start_date and end_date: use that range, ignore days
    2. If start_date and days: use start_date + days
    3. If end_date and days: use end_date - days + 1 (inclusive)
    4. If only days: use last N days with data (default behavior)

    Only returns dates that have data in the timeline.

    Args:
        json_path: Path to Timeline.json file
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        days: Number of days (default 14)

    Returns:
        List of YYYY-MM-DD dates with data, sorted chronologically
    """
    available_dates = _get_available_dates(json_path)
    if not available_dates:
        return []

    bounds = _calculate_date_bounds(start_date, end_date, days)
    if bounds is None:
        return get_last_n_days_with_data(json_path, days)

    start, end = bounds
    return _filter_dates_in_range(available_dates, start, end)


def get_cache_source() -> str:
    """Return the source of the most recent cache load: 'session', 'disk', or 'parsed'."""
    return _cache.cache_source


def get_sqlite_cache_stats(json_path: str) -> dict:
    """Return SQLite segment cache statistics."""
    return get_cache_stats(json_path)


def clear_cache() -> None:
    """Clear the session cache. Useful for testing or memory management."""
    _cache.clear()
