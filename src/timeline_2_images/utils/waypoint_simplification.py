"""Waypoint simplification utilities using Ramer-Douglas-Peucker algorithm."""

from shapely.geometry import LineString


class WaypointSimplifier:
    """Simplifies waypoints using Ramer-Douglas-Peucker algorithm."""

    def __init__(self, tolerance_meters: float = 20):
        """Initialize simplifier with tolerance.

        Args:
            tolerance_meters: Simplification tolerance in meters (higher = more simplification)
        """
        self.tolerance_meters = tolerance_meters

    def simplify(self, waypoints: list[tuple]) -> list[tuple]:
        """Simplify waypoints using Ramer-Douglas-Peucker algorithm.

        Reduces the number of points while preserving the overall path shape.
        Filters out stationary clusters (repeated or very close points).

        Args:
            waypoints: List of (lat, lon) tuples

        Returns:
            Simplified list of (lat, lon) tuples
        """
        if len(waypoints) < 3:
            return waypoints

        line = LineString(waypoints)
        tolerance_degrees = self.tolerance_meters / 111000
        simplified_line = line.simplify(tolerance_degrees)

        if isinstance(simplified_line, LineString):
            return list(simplified_line.coords)
        return waypoints
