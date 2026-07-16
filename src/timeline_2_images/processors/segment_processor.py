"""Process timeline segments."""

from timeline_2_images.models import Segment, ProcessedSegment, Bounds
from timeline_2_images.map_renderer import simplify_waypoints


class SegmentProcessor:
    """Processes segments: simplification, bounds, filtering."""

    def __init__(
        self,
        simplification_tolerance_meters: float = 15,
        min_waypoint_count: int = 2,
    ):
        """Initialize segment processor.

        Args:
            simplification_tolerance_meters: RDP simplification tolerance
            min_waypoint_count: Minimum waypoints to process segment
        """
        self.simplification_tolerance_meters = simplification_tolerance_meters
        self.min_waypoint_count = min_waypoint_count

    def process_segment(self, segment: Segment) -> ProcessedSegment | None:
        """Process a segment: simplify, calculate bounds.

        Args:
            segment: Segment object to process

        Returns:
            ProcessedSegment or None if segment is too small
        """
        if len(segment.waypoints) < self.min_waypoint_count:
            return None

        simplified = self.simplify_waypoints(segment.waypoints)

        if not simplified:
            return None

        return ProcessedSegment.from_segment(segment, simplified)

    def process_segments(self, segments: list[Segment]) -> list[ProcessedSegment]:
        """Process multiple segments.

        Args:
            segments: List of Segment objects

        Returns:
            List of successfully processed ProcessedSegment objects
        """
        processed = []
        for segment in segments:
            result = self.process_segment(segment)
            if result:
                processed.append(result)
        return processed

    def simplify_waypoints(self, waypoints: list[tuple[float, float]]) -> list[tuple[float, float]]:
        """Simplify waypoints using RDP algorithm.

        Args:
            waypoints: List of (lat, lon) tuples

        Returns:
            Simplified list of (lat, lon) tuples
        """
        return simplify_waypoints(waypoints, self.simplification_tolerance_meters)

    def extract_waypoints(self, raw_path: list) -> list[tuple[float, float]]:
        """Extract waypoints from raw timeline path.

        Args:
            raw_path: Raw path list from timeline segment

        Returns:
            List of (lat, lon) tuples
        """
        waypoints = []
        for item in raw_path:
            point_str = item.get("point") if isinstance(item, dict) else None
            if not point_str or not isinstance(point_str, str):
                continue

            if "," not in point_str:
                continue

            try:
                lat_str, lon_str = point_str.split(",")
                lat_str = lat_str.replace("°", "").strip()
                lon_str = lon_str.replace("°", "").strip()
                waypoints.append((float(lat_str), float(lon_str)))
            except (ValueError, AttributeError):
                continue

        return waypoints

    def calculate_bounds(self, waypoints: list[tuple[float, float]]) -> Bounds | None:
        """Calculate bounds from waypoints.

        Args:
            waypoints: List of (lat, lon) tuples

        Returns:
            Bounds object or None if no waypoints
        """
        if not waypoints:
            return None

        latitudes = [lat for lat, _ in waypoints]
        longitudes = [lon for _, lon in waypoints]

        return Bounds(
            min_latitude=min(latitudes),
            max_latitude=max(latitudes),
            min_longitude=min(longitudes),
            max_longitude=max(longitudes),
        )

    def filter_by_waypoint_count(
        self, segments: list[Segment], min_count: int = 2
    ) -> list[Segment]:
        """Filter segments by minimum waypoint count.

        Args:
            segments: List of Segment objects
            min_count: Minimum waypoint count

        Returns:
            Filtered list of segments
        """
        return [s for s in segments if len(s.waypoints) >= min_count]

    def merge_segment_waypoints(
        self, segments: list[ProcessedSegment]
    ) -> list[tuple[float, float]]:
        """Merge waypoints from multiple segments into single list.

        Args:
            segments: List of ProcessedSegment objects

        Returns:
            Combined list of (lat, lon) tuples
        """
        all_waypoints = []
        for segment in segments:
            all_waypoints.extend(segment.simplified_waypoints)
        return all_waypoints
