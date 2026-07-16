"""Render Google Timeline routes on map images."""

import math
import geopandas as gpd
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import matplotlib
import contextily as cx

# Use non-interactive backend for headless rendering
matplotlib.use("Agg")


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

    # Convert to LineString (WGS84), simplify, convert back
    line = LineString(waypoints)

    # Simplify using RDP algorithm (tolerance in degrees, ~111km per degree)
    # Convert meters to approximate degrees (at equator: 1 degree ≈ 111 km)
    tolerance_degrees = tolerance_meters / 111000
    simplified_line = line.simplify(tolerance_degrees)

    if isinstance(simplified_line, LineString):
        return list(simplified_line.coords)
    # Handle edge case where simplification results in a point
    return waypoints


def _collect_and_simplify_waypoints(segments: list[dict]) -> tuple[list, list]:
    """Collect all waypoints and simplified waypoints from segments."""
    all_points = []
    all_simplified = []
    for seg in segments:
        waypoints = seg.get("waypoints", [])
        if waypoints:
            all_points.extend(waypoints)
            simplified = simplify_waypoints(waypoints, tolerance_meters=15)
            all_simplified.extend(simplified)
    return all_points, all_simplified


def _calculate_bounds(all_points: list) -> tuple:
    """Calculate bounds in Web Mercator from lat/lon points."""
    lats = [p[0] for p in all_points]
    lons = [p[1] for p in all_points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    bounds_gdf = gpd.GeoDataFrame(
        geometry=[Point(lon, lat) for lat, lon in [(min_lat, min_lon), (max_lat, max_lon)]],
        crs="EPSG:4326",
    ).to_crs(epsg=3857)
    return tuple(bounds_gdf.total_bounds)


def _calculate_padded_bounds(minx: float, miny: float, maxx: float, maxy: float) -> tuple:
    """Calculate square bounds with padding."""
    dx = (maxx - minx) or 500
    dy = (maxy - miny) or 500
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    max_dim = max(dx, dy)
    pad_ratio = 0.05
    padded_dim = max_dim * (1 + 2 * pad_ratio)
    half_side = padded_dim / 2
    return (
        center_x - half_side,
        center_y - half_side,
        center_x + half_side,
        center_y + half_side,
        center_x,
        center_y,
    )


def _enforce_minimum_area(bounds: tuple, min_area_sq_km: float) -> tuple:
    """Enforce minimum viewing area."""
    minx, miny, maxx, maxy = bounds
    width_m = maxx - minx
    height_m = maxy - miny
    area_sq_km = (width_m * height_m) / 1e6
    if area_sq_km >= min_area_sq_km:
        return bounds
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    area_sq_m = min_area_sq_km * 1e6
    half_side = math.sqrt(area_sq_m) / 2
    return (
        center_x - half_side,
        center_y - half_side,
        center_x + half_side,
        center_y + half_side,
    )


def _draw_journey_line(ax, all_simplified_waypoints: list):
    """Draw the contiguous journey line with border."""
    if len(all_simplified_waypoints) > 1:
        line = LineString([(lon, lat) for lat, lon in all_simplified_waypoints])
        gdf_line = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326").to_crs(epsg=3857)
        gdf_line.plot(ax=ax, color="#000000", linewidth=4, alpha=0.8, zorder=99)
        gdf_line.plot(ax=ax, color="#1a73e8", linewidth=2, alpha=0.9, zorder=100)


def _draw_markers(ax, all_simplified_waypoints: list):
    """Draw start and end markers."""
    if all_simplified_waypoints:
        start_point = Point(all_simplified_waypoints[0][1], all_simplified_waypoints[0][0])
        gdf_start = gpd.GeoDataFrame(geometry=[start_point], crs="EPSG:4326").to_crs(epsg=3857)
        gdf_start.plot(ax=ax, color="#34a853", markersize=35, zorder=101, alpha=0.95)
        if len(all_simplified_waypoints) > 1:
            end_point = Point(all_simplified_waypoints[-1][1], all_simplified_waypoints[-1][0])
            gdf_end = gpd.GeoDataFrame(geometry=[end_point], crs="EPSG:4326").to_crs(epsg=3857)
            gdf_end.plot(ax=ax, color="#ea4335", markersize=25, zorder=101, alpha=0.95)


def render_segments(
    segments: list[dict],
    out_path: str,
    image_size: int = 500,
    dpi: int = 150,
    min_area_sq_km: float = 5,
):
    """
    Render timeline segments on an OSM basemap using RDP line simplification.

    Each segment is drawn as a simplified line, avoiding tangled paths from GPS noise.

    Args:
        segments: List of segment dicts with 'waypoints' (list of (lat, lon) tuples)
        out_path: Output JPG path
        image_size: Size of output image (width and height in pixels)
        dpi: DPI for the image
        min_area_sq_km: Minimum area in sq km to display
    """
    if not segments:
        raise ValueError("No segments provided to render")

    all_points, all_simplified_waypoints = _collect_and_simplify_waypoints(segments)

    if not all_points:
        raise ValueError("No waypoints found in segments")

    minx, miny, maxx, maxy = _calculate_bounds(all_points)
    minx, miny, maxx, maxy, _, _ = _calculate_padded_bounds(minx, miny, maxx, maxy)
    minx, miny, maxx, maxy = _enforce_minimum_area((minx, miny, maxx, maxy), min_area_sq_km)

    fig_size_inches = image_size / dpi
    fig, ax = plt.subplots(figsize=(fig_size_inches, fig_size_inches), dpi=dpi)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)

    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("equal")

    # OpenStreetMap basemap tiles
    osm_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    cx.add_basemap(ax, source=osm_url, zoom="auto")

    _draw_journey_line(ax, all_simplified_waypoints)
    _draw_markers(ax, all_simplified_waypoints)

    ax.set_axis_off()
    plt.tight_layout(pad=0)

    fig.savefig(out_path, dpi=dpi, format="jpg", facecolor="white")
    plt.close(fig)
