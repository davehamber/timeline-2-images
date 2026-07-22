"""Parses timeline segments from JSON data."""

import time
from datetime import datetime, date, timezone

import pandas as pd

from timeline_2_images.parsers.timeline_cache import TimelineCache
from timeline_2_images.cache.segment_cache import SegmentCache


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

    def _try_cached_segments(
        self, json_path: str, target_date: str, timing: dict, start: float, profile: bool
    ) -> tuple[list[dict] | tuple[list[dict], dict] | None, bool]:
        """Try to return cached segments if available."""
        cached_segments = self.segment_cache.get(json_path, target_date)
        if cached_segments is None:
            return None, False

        timing["total"] = time.time() - start
        timing["cache_source"] = "segment_cached"
        return (cached_segments, timing) if profile else cached_segments, True

    def _load_and_index_segments(self, json_path: str, timing: dict) -> tuple[list, dict]:
        """Load and build index for segments."""
        step_start = time.time()
        data = self.cache.load_file(json_path)
        timing["json_load"] = time.time() - step_start
        timing["cache_source"] = "json_parsed"

        step_start = time.time()
        segment_date_index = self.cache.build_segment_date_index()
        timing["build_index"] = time.time() - step_start

        return data.get("semanticSegments", []), segment_date_index

    def _match_segments_for_date(
        self, semantic_segs: list, target_date: str, segment_date_index: dict, timing: dict
    ) -> list:
        """Find segments matching the target date."""
        step_start = time.time()
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        matching_indices = segment_date_index.get(target_date_obj, [])
        timing["index_lookup"] = time.time() - step_start

        return [semantic_segs[index] for index in matching_indices if index < len(semantic_segs)]

    def load_for_day(
        self, json_path: str, target_date: str, profile: bool = False
    ) -> list[dict] | tuple[list[dict], dict]:
        """Extract semantic segments for a given date with waypoints."""
        timing: dict = {}
        start = time.time()

        # Try cached segments first
        result, found_cache = self._try_cached_segments(
            json_path, target_date, timing, start, profile
        )
        if found_cache:
            return result

        # Load and index segments
        semantic_segs, segment_date_index = self._load_and_index_segments(json_path, timing)

        # Find matching segments for date
        matching_segments = self._match_segments_for_date(
            semantic_segs, target_date, segment_date_index, timing
        )

        # Build segments with waypoints
        step_start = time.time()
        segments = self.build_segments_with_waypoints(matching_segments, step_start, timing)
        timing["total"] = time.time() - start

        # Cache the segments for this date
        self.segment_cache.set(json_path, target_date, segments)

        return (segments, timing) if profile else segments
