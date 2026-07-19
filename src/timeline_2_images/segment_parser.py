"""Parses timeline segments from JSON data."""

import time
from datetime import datetime, date, timezone

import pandas as pd

from timeline_2_images.timeline_cache import TimelineCache
from timeline_2_images.sqlite_cache import SegmentCache
from timeline_2_images.date_extractor import DateExtractor


class SegmentParser:
    """Parses timeline segments from JSON data."""

    def __init__(self, cache: TimelineCache, segment_cache: SegmentCache | None = None):
        self.cache = cache
        self.segment_cache = segment_cache or SegmentCache()

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
        cached_segments = self.segment_cache.load_segments_for_date(json_path, target_date)
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
        self.segment_cache.populate_cache(json_path, data)
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
