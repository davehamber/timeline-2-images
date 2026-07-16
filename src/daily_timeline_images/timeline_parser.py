"""Parse Google Timeline JSON exports and extract location data."""

import json
from datetime import datetime, timezone

import pandas as pd


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

    def in_target_day(dt: datetime) -> bool:
        return dt.astimezone(timezone.utc).date() == target

    for seg in data.get("semanticSegments", []):
        start_str = seg.get("startTime")
        if not start_str:
            continue

        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt):
            continue
        dt = dt.to_pydatetime()

        if not in_target_day(dt):
            continue

        waypoints = []
        path = seg.get("timelinePath", [])
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

        if waypoints:
            segments.append({
                "startTime": start_str,
                "endTime": seg.get("endTime"),
                "waypoints": waypoints,
            })

    return segments


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

    rows = []
    target = datetime.strptime(target_date, "%Y-%m-%d").date()

    def in_target_day(dt: datetime) -> bool:
        return dt.astimezone(timezone.utc).date() == target

    # Shape 1: flat "locations" list
    if "locations" in data:
        for loc in data["locations"]:
            ts = loc.get("timestamp") or loc.get("timestampMs")
            if ts is None:
                continue
            if isinstance(ts, str):
                dt = pd.to_datetime(ts, utc=True, errors="coerce")
                if pd.isna(dt):
                    continue
                dt = dt.to_pydatetime()
            else:
                dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)

            if not in_target_day(dt):
                continue

            lat = loc.get("latitudeE7")
            lon = loc.get("longitudeE7")
            if lat is not None and lon is not None:
                rows.append((dt, lat / 1e7, lon / 1e7))

    # Shape 2: "timelineObjects" (Semantic Location History)
    for obj in data.get("timelineObjects", []):
        seg = obj.get("activitySegment") or obj.get("placeVisit")
        if not seg:
            continue
        duration = seg.get("duration", {})
        start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
        if start_str is None:
            continue
        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt):
            continue
        dt = dt.to_pydatetime()
        if not in_target_day(dt):
            continue

        # Waypoints along an activity segment
        waypoints = seg.get("waypointPath", {}).get("waypoints", [])
        for wp in waypoints:
            lat = wp.get("latE7")
            lon = wp.get("lngE7")
            if lat is not None and lon is not None:
                rows.append((dt, lat / 1e7, lon / 1e7))

        # Start/end locations
        for key in ("startLocation", "endLocation", "location"):
            loc = seg.get(key)
            if loc and "latitudeE7" in loc and "longitudeE7" in loc:
                rows.append((dt, loc["latitudeE7"] / 1e7, loc["longitudeE7"] / 1e7))

    # Shape 3: newer "semanticSegments" with "point": "lat,lng" strings (may have ° symbols)
    for seg in data.get("semanticSegments", []):
        start_str = seg.get("startTime")
        if not start_str:
            continue
        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt):
            continue
        dt = dt.to_pydatetime()
        if not in_target_day(dt):
            continue

        path = seg.get("timelinePath", []) or seg.get("waypointPath", {}).get("waypoints", [])
        for wp in path:
            pt = wp.get("point")
            if isinstance(pt, str) and "," in pt:
                lat_s, lon_s = pt.split(",")
                # Remove degree symbols and whitespace
                lat_s = lat_s.replace("°", "").strip()
                lon_s = lon_s.replace("°", "").strip()
                try:
                    rows.append((dt, float(lat_s), float(lon_s)))
                except ValueError:
                    continue

    if not rows:
        raise ValueError(
            f"No points found for {target_date}. Check the Timeline JSON structure."
        )

    df = pd.DataFrame(rows, columns=["timestamp", "lat", "lon"]).sort_values("timestamp")
    return df


def get_last_n_days_with_data(json_path: str, days: int = 14) -> list[str]:
    """
    Find the last N days that have timeline data.

    Returns dates in YYYY-MM-DD format, sorted chronologically.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_dates = set()

    # Extract dates from locations
    for loc in data.get("locations", []):
        ts = loc.get("timestamp") or loc.get("timestampMs")
        if ts is None:
            continue
        if isinstance(ts, str):
            dt = pd.to_datetime(ts, utc=True, errors="coerce")
            if pd.isna(dt):
                continue
            dt = dt.to_pydatetime()
        else:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        all_dates.add(dt.astimezone(timezone.utc).date())

    # Extract dates from timelineObjects
    for obj in data.get("timelineObjects", []):
        seg = obj.get("activitySegment") or obj.get("placeVisit")
        if not seg:
            continue
        duration = seg.get("duration", {})
        start_str = duration.get("startTimestamp") or duration.get("startTimestampMs")
        if start_str is None:
            continue
        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt):
            continue
        dt = dt.to_pydatetime()
        all_dates.add(dt.astimezone(timezone.utc).date())

    # Extract dates from semanticSegments
    for seg in data.get("semanticSegments", []):
        start_str = seg.get("startTime")
        if not start_str:
            continue
        dt = pd.to_datetime(start_str, utc=True, errors="coerce")
        if pd.isna(dt):
            continue
        dt = dt.to_pydatetime()
        all_dates.add(dt.astimezone(timezone.utc).date())

    sorted_dates = sorted(all_dates, reverse=True)
    last_n = sorted_dates[:days]
    return sorted([d.strftime("%Y-%m-%d") for d in last_n])
