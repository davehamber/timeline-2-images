"""Parse Google Timeline JSON exports and extract location data."""

import json
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Set

import pandas as pd

from daily_timeline_images.parquet_cache import load_from_cache, save_to_cache


class TimelineCache:
    """Session-level cache for Timeline JSON data to avoid re-parsing large files.

    Caches the full parsed JSON structure in memory for the lifetime of the session,
    avoiding expensive re-parsing when processing multiple dates from the same file.
    Also tries persistent disk cache (parquet) with hash validation.
    """

    def __init__(self):
        self.file_path: str | None = None
        self.data: dict | None = None
        self.date_index: Dict[date, bool] | None = None

    def load_file(self, json_path: str) -> dict:
        """Load and cache Timeline JSON file. Returns cached data if already loaded.

        Priority:
        1. Session memory cache (fastest)
        2. Disk parquet cache if source file hash matches
        3. Parse raw JSON and save to disk cache
        """
        if self.file_path == json_path and self.data is not None:
            return self.data

        self.file_path = json_path

        cached_data = load_from_cache(json_path)
        if cached_data is not None:
            self.data = cached_data
            self.date_index = None
            assert self.data is not None
            return self.data

        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if self.data is not None:
            save_to_cache(json_path, self.data)

        self.date_index = None
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

    def clear(self) -> None:
        """Clear the cache."""
        self.file_path = None
        self.data = None
        self.date_index = None


_cache = TimelineCache()


def _parse_semantic_segments_iter(data: dict):
    """Iterate through semanticSegments with parsed datetimes.

    Yields (segment, datetime) tuples for segments with valid startTime.
    """
    for seg in data.get("semanticSegments", []):
        start_str = seg.get("startTime")
        if not start_str:
            continue
        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt):
            continue
        yield seg, dt.to_pydatetime()


def _parse_waypoints(path: list) -> list:
    """Parse waypoints from timeline path with string coordinates."""
    waypoints = []
    for wp in path:
        pt = wp.get("point")
        if isinstance(pt, str) and "," in pt:
            lat_s, lon_s = pt.split(",")
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
    dt = datetime.fromisoformat(str(dt_timestamp.isoformat()))  # type: ignore[union-attr]
    if dt.astimezone(timezone.utc).date() != target:
        return None
    return start_str


def load_segments_for_day(json_path: str, target_date: str) -> list[dict]:
    """
    Extract semantic segments for a given date with waypoints.

    Each segment represents a distinct journey/stay period.

    Args:
        json_path: Path to Timeline.json file
        target_date: Date in YYYY-MM-DD format

    Returns:
        List of segment dicts with keys: startTime, endTime, waypoints (list of (lat, lon, time))
    """
    data = _cache.load_file(json_path)

    segments = []
    target = datetime.strptime(target_date, "%Y-%m-%d").date()

    for seg in data.get("semanticSegments", []):
        start_str = seg.get("startTime")
        if not start_str:
            continue

        if not _parse_segment_datetime(start_str, target):
            continue

        waypoints = _parse_waypoints(seg.get("timelinePath", []))

        if waypoints:
            segments.append(
                {
                    "startTime": start_str,
                    "endTime": seg.get("endTime"),
                    "waypoints": waypoints,
                }
            )

    return segments


def _parse_timestamp(ts: str | int | float) -> datetime | None:
    """Parse timestamp in various formats (string or milliseconds)."""
    if isinstance(ts, str):
        dt = pd.to_datetime(ts, utc=True, errors="coerce")
        if pd.isna(dt):
            return None
        return datetime.fromisoformat(str(dt.isoformat()))  # type: ignore[union-attr]
    return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)


def _extract_location_point(dt: datetime, loc: dict) -> tuple | None:
    """Extract a single location point if valid coordinates exist."""
    lat: float | None = loc.get("latitudeE7")
    lon: float | None = loc.get("longitudeE7")
    if lat is not None and lon is not None:
        return (dt, float(lat) / 1e7, float(lon) / 1e7)
    return None


def _process_flat_location(loc: dict, target: date) -> tuple | None:
    """Process a single flat location and return point if in target date."""
    ts = loc.get("timestamp") or loc.get("timestampMs")
    if ts is None:
        return None
    dt = _parse_timestamp(ts)
    if dt is None or dt.astimezone(timezone.utc).date() != target:
        return None
    return _extract_location_point(dt, loc)


def _extract_from_flat_locations(data: dict, target: date) -> list:
    """Extract points from flat locations list."""
    rows = []
    for loc in data.get("locations", []):
        point = _process_flat_location(loc, target)
        if point:
            rows.append(point)
    return rows


def _extract_waypoints_from_segment(dt: datetime, seg: dict) -> list:
    """Extract waypoint rows from a timeline segment."""
    rows = []
    waypoints = seg.get("waypointPath", {}).get("waypoints", [])
    for wp in waypoints:
        lat: float | None = wp.get("latE7")
        lon: float | None = wp.get("lngE7")
        if lat is not None and lon is not None:
            rows.append((dt, float(lat) / 1e7, float(lon) / 1e7))
    return rows


def _extract_locations_from_segment(dt: datetime, seg: dict) -> list:
    """Extract start/end location rows from a timeline segment."""
    rows = []
    for key in ("startLocation", "endLocation", "location"):
        loc = seg.get(key)
        if loc and "latitudeE7" in loc and "longitudeE7" in loc:
            rows.append((dt, float(loc["latitudeE7"]) / 1e7, float(loc["longitudeE7"]) / 1e7))
    return rows


def _get_timeline_object_datetime(seg: dict) -> datetime | None:
    """Extract datetime from a timeline object segment."""
    if not seg:
        return None
    duration = seg.get("duration", {})
    start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
    if start_str is None:
        return None
    dt = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    return datetime.fromisoformat(str(dt.isoformat()))


def _matches_target_date(dt: datetime | None, target: date) -> bool:
    """Check if datetime matches target date."""
    if dt is None:
        return False
    return dt.astimezone(timezone.utc).date() == target


def _process_timeline_object(obj: dict, target: date) -> list:
    """Process a single timeline object and return points if in target date."""
    seg = obj.get("activitySegment") or obj.get("placeVisit")
    if not isinstance(seg, dict):
        return []
    dt = _get_timeline_object_datetime(seg)
    if not _matches_target_date(dt, target):
        return []
    if dt is None:
        return []
    rows = []
    rows.extend(_extract_waypoints_from_segment(dt, seg))
    rows.extend(_extract_locations_from_segment(dt, seg))
    return rows


def _extract_from_timeline_objects(data: dict, target: date) -> list:
    """Extract points from timelineObjects (Semantic Location History)."""
    rows = []
    for obj in data.get("timelineObjects", []):
        rows.extend(_process_timeline_object(obj, target))
    return rows


def _parse_point_string(dt, pt: str) -> tuple | None:
    """Parse a single point string coordinate."""
    if not isinstance(pt, str) or "," not in pt:
        return None
    lat_s, lon_s = pt.split(",")
    lat_s = lat_s.replace("°", "").strip()
    lon_s = lon_s.replace("°", "").strip()
    try:
        return (dt, float(lat_s), float(lon_s))
    except ValueError:
        return None


def _get_semantic_segment_datetime(seg: dict) -> datetime | None:
    """Extract datetime from a semantic segment."""
    start_str = seg.get("startTime")
    if not start_str:
        return None
    dt = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    return datetime.fromisoformat(str(dt.isoformat()))


def _extract_points_from_segment_path(dt, seg: dict) -> list:
    """Extract all points from a segment's path."""
    path = seg.get("timelinePath", []) or seg.get("waypointPath", {}).get("waypoints", [])
    rows = []
    for wp in path:
        pt = wp.get("point")
        point = _parse_point_string(dt, pt)
        if point:
            rows.append(point)
    return rows


def _process_semantic_segment(seg: dict, target: date) -> list:
    """Process a single semantic segment and return points if in target date."""
    dt = _get_semantic_segment_datetime(seg)
    if not _matches_target_date(dt, target):
        return []
    if dt is None:
        return []
    return _extract_points_from_segment_path(dt, seg)


def _extract_from_semantic_segments(data: dict, target: date) -> list:
    """Extract points from semanticSegments with string coordinates."""
    rows = []
    for seg in data.get("semanticSegments", []):
        rows.extend(_process_semantic_segment(seg, target))
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
    for loc in data.get("locations", []):
        ts = loc.get("timestamp") or loc.get("timestampMs")
        if ts is None:
            continue
        dt = _parse_timestamp(ts)
        if dt is not None:
            dates.add(dt.astimezone(timezone.utc).date())
    return dates


def _get_segment_start_date(seg: dict) -> date | None:
    """Extract start date from a timeline segment."""
    duration = seg.get("duration", {})
    start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
    if start_str is None:
        return None
    dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt_timestamp):
        return None
    dt = datetime.fromisoformat(str(dt_timestamp.isoformat()))
    return dt.astimezone(timezone.utc).date()


def _extract_dates_from_timeline_objects(data: dict) -> Set[date]:
    """Extract unique dates from timelineObjects."""
    dates = set()
    for obj in data.get("timelineObjects", []):
        seg = obj.get("activitySegment") or obj.get("placeVisit")
        if not seg:
            continue
        segment_date = _get_segment_start_date(seg)
        if segment_date:
            dates.add(segment_date)
    return dates


def _extract_dates_from_segments(data: dict) -> Set[date]:
    """Extract unique dates from semanticSegments."""
    dates = set()
    for _, dt in _parse_semantic_segments_iter(data):
        dates.add(dt.astimezone(timezone.utc).date())
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


def get_date_range(
    json_path: str,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 14,
) -> list[str]:
    """
    Get dates with data based on flexible date range parameters.

    Uses session-level caching to avoid re-parsing large files.

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
    _cache.load_file(json_path)
    _cache.build_date_index()

    if not _cache.date_index:
        return []

    available_sorted = sorted(_cache.date_index.keys())

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    elif start_date and not end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = start + timedelta(days=days - 1)
    elif end_date and not start_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        start = end - timedelta(days=days - 1)
    else:
        return get_last_n_days_with_data(json_path, days)

    result = [d for d in available_sorted if start <= d <= end]
    return [d.strftime("%Y-%m-%d") for d in result]


def clear_cache() -> None:
    """Clear the session cache. Useful for testing or memory management."""
    _cache.clear()
