"""Bounds model for geographic area representation."""

from dataclasses import dataclass


@dataclass
class Bounds:
    """Represents geographic bounding box with latitude and longitude."""

    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float

    def get_center(self) -> tuple[float, float]:
        """Get center point of bounds."""
        center_lat = (self.min_latitude + self.max_latitude) / 2
        center_lon = (self.min_longitude + self.max_longitude) / 2
        return (center_lat, center_lon)

    def expand(self, padding_degrees: float) -> "Bounds":
        """Expand bounds by given padding in degrees."""
        return Bounds(
            min_latitude=self.min_latitude - padding_degrees,
            max_latitude=self.max_latitude + padding_degrees,
            min_longitude=self.min_longitude - padding_degrees,
            max_longitude=self.max_longitude + padding_degrees,
        )

    def get_area_degrees_squared(self) -> float:
        """Get area in square degrees."""
        lat_span = self.max_latitude - self.min_latitude
        lon_span = self.max_longitude - self.min_longitude
        return lat_span * lon_span
