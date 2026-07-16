"""Internal utility functions for map rendering (kept for backward compatibility).

Note: New OOP code should use timeline_2_images.rendering module instead.
"""

import requests_cache
from shapely.geometry import LineString

# Install requests-cache globally to cache all tile downloads
# This will intercept all requests from contextily automatically
try:
    _cache_session = requests_cache.install_cache(
        ".tile_cache/osm-tiles",
        backend="sqlite",
        expire_after=None,  # Never expire - tiles don't change
        match_headers=False,  # Don't vary cache by headers
        stale_if_error=True,  # Use stale cache on error
    )
except Exception as e:
    print(f"Warning: Failed to install requests-cache: {e}")
    _cache_session = None


def simplify_waypoints(waypoints: list[tuple], tolerance_meters: float = 20) -> list[tuple]:
    """
    Simplify waypoints using Ramer-Douglas-Peucker algorithm.

    Reduces the number of points while preserving the overall path shape.
    Filters out stationary clusters (repeated or very close points).

    Args:
        waypoints: List of (lat, lon) tuples
        tolerance_meters: Simplification tolerance in meters (higher = more simplification)

    Returns:
        Simplified list of (lat, lon) tuples
    """
    if len(waypoints) < 3:
        return waypoints

    line = LineString(waypoints)
    tolerance_degrees = tolerance_meters / 111000
    simplified_line = line.simplify(tolerance_degrees)

    if isinstance(simplified_line, LineString):
        return list(simplified_line.coords)
    return waypoints
