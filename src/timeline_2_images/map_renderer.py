"""Internal utility functions for map rendering (kept for backward compatibility).

Note: New OOP code should use timeline_2_images.rendering module instead.
"""

from pathlib import Path

import requests_cache
from shapely.geometry import LineString

# Install requests-cache globally to cache all tile downloads
# This will intercept all requests from contextily automatically
try:
    # Use XDG Base Directory Specification for cache location
    cache_dir = Path.home() / ".cache" / "timeline-2-images"
    cache_dir.mkdir(exist_ok=True, parents=True)
    CACHE_PATH = str(cache_dir / "tiles")

    _CACHE_SESSION = requests_cache.install_cache(  # pylint: disable=assignment-from-no-return  # type: ignore[assignment]
        CACHE_PATH,
        backend="sqlite",
        expire_after=None,  # Never expire - tiles don't change
        match_headers=False,  # Don't vary cache by headers
        stale_if_error=True,  # Use stale cache on error
    )
except (OSError, IOError) as e:
    print(f"Warning: Failed to install requests-cache: {e}")
    _CACHE_SESSION = None


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
