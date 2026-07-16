"""Parse Google Timeline JSON exports and extract location data."""

import json
from datetime import datetime, timezone

import pandas as pd


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


def _parse_segment_datetime(start_str: str, target: object) -> str | None:
    """Parse segment start time and return if it matches target date."""
    dt = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    dt = dt.to_pydatetime()
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
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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
            segments.append({
                "startTime": start_str,
                "endTime": seg.get("endTime"),
                "waypoints": waypoints,
            })

    return segments


def _parse_timestamp(ts):
    """Parse timestamp in various formats (string or milliseconds)."""
    if isinstance(ts, str):
        dt = pd.to_datetime(ts, utc=True, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime()
    return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)


def _extract_location_point(dt, loc: dict) -> tuple | None:
    """Extract a single location point if valid coordinates exist."""
    lat = loc.get("latitudeE7")
    lon = loc.get("longitudeE7")
    if lat is not None and lon is not None:
        return (dt, lat / 1e7, lon / 1e7)
    return None


def _process_flat_location(loc: dict, target: object) -> tuple | None:
    """Process a single flat location and return point if in target date."""
    ts = loc.get("timestamp") or loc.get("timestampMs")
    if ts is None:
        return None
    dt = _parse_timestamp(ts)
    if dt is None or dt.astimezone(timezone.utc).date() != target:
        return None
    return _extract_location_point(dt, loc)


def _extract_from_flat_locations(data: dict, target: object) -> list:
    """Extract points from flat locations list."""
    rows = []
    for loc in data.get("locations", []):
        point = _process_flat_location(loc, target)
        if point:
            rows.append(point)
    return rows


def _extract_waypoints_from_segment(dt, seg: dict) -> list:
    """Extract waypoint rows from a timeline segment."""
    rows = []
    waypoints = seg.get("waypointPath", {}).get("waypoints", [])
    for wp in waypoints:
        lat = wp.get("latE7")
        lon = wp.get("lngE7")
        if lat is not None and lon is not None:
            rows.append((dt, lat / 1e7, lon / 1e7))
    return rows


def _extract_locations_from_segment(dt, seg: dict) -> list:
    """Extract start/end location rows from a timeline segment."""
    rows = []
    for key in ("startLocation", "endLocation", "location"):
        loc = seg.get(key)
        if loc and "latitudeE7" in loc and "longitudeE7" in loc:
            rows.append((dt, loc["latitudeE7"] / 1e7, loc["longitudeE7"] / 1e7))
    return rows


def _get_timeline_object_datetime(seg: dict) -> object | None:
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
    return dt.to_pydatetime()


def _matches_target_date(dt: object | None, target: object) -> bool:
    """Check if datetime matches target date."""
    if dt is None:
        return False
    return dt.astimezone(timezone.utc).date() == target


def _process_timeline_object(obj: dict, target: object) -> list:
    """Process a single timeline object and return points if in target date."""
    seg = obj.get("activitySegment") or obj.get("placeVisit")
    dt = _get_timeline_object_datetime(seg)
    if not _matches_target_date(dt, target):
        return []
    rows = []
    rows.extend(_extract_waypoints_from_segment(dt, seg))
    rows.extend(_extract_locations_from_segment(dt, seg))
    return rows


def _extract_from_timeline_objects(data: dict, target: object) -> list:
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


def _get_semantic_segment_datetime(seg: dict) -> object | None:
    """Extract datetime from a semantic segment."""
    start_str = seg.get("startTime")
    if not start_str:
        return None
    dt = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime()


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


def _process_semantic_segment(seg: dict, target: object) -> list:
    """Process a single semantic segment and return points if in target date."""
    dt = _get_semantic_segment_datetime(seg)
    if not _matches_target_date(dt, target):
        return []
    return _extract_points_from_segment_path(dt, seg)


def _extract_from_semantic_segments(data: dict, target: object) -> list:
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

    Args:
        json_path: Path to the Timeline JSON file
        target_date: Date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: timestamp, lat, lon (sorted by timestamp)

    Raises:
        ValueError: If no points found for the target date
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    target = datetime.strptime(target_date, "%Y-%m-%d").date()

    rows = []
    rows.extend(_extract_from_flat_locations(data, target))
    rows.extend(_extract_from_timeline_objects(data, target))
    rows.extend(_extract_from_semantic_segments(data, target))

    if not rows:
        raise ValueError(
            f"No points found for {target_date}. Check the Timeline JSON structure."
        )

    df = pd.DataFrame(rows, columns=["timestamp", "lat", "lon"]).sort_values("timestamp")
    return df


def _extract_dates_from_locations(data: dict) -> set:
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


def _get_segment_start_date(seg: dict) -> object | None:
    """Extract start date from a timeline segment."""
    duration = seg.get("duration", {})
    start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
    if start_str is None:
        return None
    dt = pd.to_datetime(start_str, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime().astimezone(timezone.utc).date()


def _extract_dates_from_timeline_objects(data: dict) -> set:
    """Extract unique dates from timelineObjects."""
    dates = set()
    for obj in data.get("timelineObjects", []):
        seg = obj.get("activitySegment") or obj.get("placeVisit")
        if not seg:
            continue
        date = _get_segment_start_date(seg)
        if date:
            dates.add(date)
    return dates


def _extract_dates_from_segments(data: dict) -> set:
    """Extract unique dates from semanticSegments."""
    dates = set()
    for seg in data.get("semanticSegments", []):
        start_str = seg.get("startTime")
        if not start_str:
            continue
        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if not pd.isna(dt):
            dates.add(dt.to_pydatetime().astimezone(timezone.utc).date())
    return dates


def get_last_n_days_with_data(json_path: str, days: int = 14) -> list[str]:
    """
    Find the last N days that have timeline data.

    Returns dates in YYYY-MM-DD format, sorted chronologically.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_dates = set()
    all_dates.update(_extract_dates_from_locations(data))
    all_dates.update(_extract_dates_from_timeline_objects(data))
    all_dates.update(_extract_dates_from_segments(data))

    sorted_dates = sorted(all_dates, reverse=True)
    last_n = sorted_dates[:days]
    return sorted([d.strftime("%Y-%m-%d") for d in last_n])
