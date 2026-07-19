"""Extracts location points from timeline JSON data."""

from datetime import datetime, timezone

import pandas as pd

from timeline_2_images.timeline_cache import TimelineCache


class PointExtractor:
    """Extracts location points from timeline JSON data."""

    def __init__(self, timeline_cache: TimelineCache | None = None):
        """Initialize point extractor with optional timeline cache.

        Args:
            timeline_cache: TimelineCache instance (created if not provided)
        """
        self.timeline_cache = timeline_cache or TimelineCache()

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

    def process_flat_location(self, location: dict, target) -> tuple | None:
        """Process a single flat location and return point if in target date."""
        timestamp_value = location.get("timestamp") or location.get("timestampMs")
        if timestamp_value is None:
            return None
        parsed_datetime = self.parse_timestamp(timestamp_value)
        if parsed_datetime is None or parsed_datetime.astimezone(timezone.utc).date() != target:
            return None
        return self.extract_location_point(parsed_datetime, location)

    def extract_from_flat_locations(self, data: dict, target) -> list:
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
    def matches_target_date(parsed_datetime: datetime | None, target) -> bool:
        """Check if datetime matches target date."""
        if parsed_datetime is None:
            return False
        return parsed_datetime.astimezone(timezone.utc).date() == target

    def process_timeline_object(self, obj: dict, target) -> list:
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

    def extract_from_timeline_objects(self, data: dict, target) -> list:
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

    def process_semantic_segment(self, segment: dict, target) -> list:
        """Process a single semantic segment and return points if in target date."""
        parsed_datetime = self.get_semantic_segment_datetime(segment)
        if not self.matches_target_date(parsed_datetime, target):
            return []
        if parsed_datetime is None:
            return []
        return self.extract_points_from_segment_path(parsed_datetime, segment)

    def extract_from_semantic_segments(self, data: dict, target) -> list:
        """Extract points from semanticSegments, handling both visits and activities."""
        rows = []
        for segment in data.get("semanticSegments", []):
            segment_rows = self.process_semantic_segment(segment, target)
            if segment_rows:
                rows.extend(segment_rows)
        return rows

    def load_points_for_day(self, json_path: str, target_date: str) -> pd.DataFrame:
        """Extract (timestamp, lat, lon) rows for the given YYYY-MM-DD date."""
        data = self.timeline_cache.load_file(json_path)
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
