"""Segment models for timeline data."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from timeline_2_images.models.bounds import Bounds


@dataclass
class Segment:
    """Represents a semantic segment from timeline data."""

    start_time: datetime
    end_time: datetime
    waypoints: list[tuple[float, float]]
    segment_type: str = "journey"

    def get_duration(self) -> timedelta:
        """Get duration of segment."""
        return self.end_time - self.start_time

    def get_bounds(self) -> Bounds | None:
        """Get bounding box of waypoints."""
        if not self.waypoints:
            return None

        latitudes = [lat for lat, _ in self.waypoints]
        longitudes = [lon for _, lon in self.waypoints]

        return Bounds(
            min_latitude=min(latitudes),
            max_latitude=max(latitudes),
            min_longitude=min(longitudes),
            max_longitude=max(longitudes),
        )

    def get_waypoint_count(self) -> int:
        """Get number of waypoints."""
        return len(self.waypoints)


@dataclass
class ProcessedSegment:
    """Segment after processing (simplification, bounds calculation)."""

    segment: Segment
    simplified_waypoints: list[tuple[float, float]]
    bounds: Bounds
    center: tuple[float, float]

    @classmethod
    def from_segment(
        cls, segment: Segment, simplified_waypoints: list[tuple[float, float]]
    ) -> "ProcessedSegment":
        """Create ProcessedSegment from Segment and simplified waypoints."""
        bounds = segment.get_bounds()
        if bounds is None:
            raise ValueError("Cannot process segment without waypoints")

        center = bounds.get_center()
        return cls(
            segment=segment,
            simplified_waypoints=simplified_waypoints,
            bounds=bounds,
            center=center,
        )
