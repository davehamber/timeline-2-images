"""Processed segment model (after simplification and bounds calculation)."""

from dataclasses import dataclass

from timeline_2_images.models.segment import Segment
from timeline_2_images.models.bounds import Bounds


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
