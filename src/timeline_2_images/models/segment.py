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
