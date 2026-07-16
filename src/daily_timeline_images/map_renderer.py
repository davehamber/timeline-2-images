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
    else:
        # Handle edge case where simplification results in a point
        return waypoints


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

    # Collect all points for bounding box calculation and create contiguous journey line
    all_points = []
    all_simplified_waypoints = []
    segment_markers = []  # Store start/end points for each segment

    for seg in segments:
        waypoints = seg.get("waypoints", [])
        if waypoints:
            all_points.extend(waypoints)
            # Simplify this segment's waypoints
            simplified = simplify_waypoints(waypoints, tolerance_meters=15)
            all_simplified_waypoints.extend(simplified)
            # Store segment endpoints for markers
            if simplified:
                segment_markers.append((simplified[0], simplified[-1]))

    if not all_points:
        raise ValueError("No waypoints found in segments")

    # Calculate bounding box from all points
    lats = [p[0] for p in all_points]
    lons = [p[1] for p in all_points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Convert bounds to Web Mercator
    bounds_gdf = gpd.GeoDataFrame(
        geometry=[Point(lon, lat) for lat, lon in [(min_lat, min_lon), (max_lat, max_lon)]],
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    minx, miny, maxx, maxy = bounds_gdf.total_bounds
    dx = (maxx - minx) or 500
    dy = (maxy - miny) or 500

    # Expand to square and add padding to fill canvas
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2

    # Use the larger dimension to ensure square coverage
    max_dim = max(dx, dy)
    pad_ratio = 0.05  # Minimal padding (5%) to fill canvas
    padded_dim = max_dim * (1 + 2 * pad_ratio)
    half_side = padded_dim / 2

    minx = center_x - half_side
    maxx = center_x + half_side
    miny = center_y - half_side
    maxy = center_y + half_side

    # Ensure minimum viewing area
    width_m = maxx - minx
    height_m = maxy - miny
    area_sq_m = width_m * height_m
    area_sq_km = area_sq_m / 1e6

    if area_sq_km < min_area_sq_km:
        area_sq_m = min_area_sq_km * 1e6
        half_side = math.sqrt(area_sq_m) / 2
        minx = center_x - half_side
        maxx = center_x + half_side
        miny = center_y - half_side
        maxy = center_y + half_side

    # Create figure with no margins (fill entire canvas)
    fig_size_inches = image_size / dpi
    fig, ax = plt.subplots(figsize=(fig_size_inches, fig_size_inches), dpi=dpi)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)

    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("equal")

    # Add OpenStreetMap basemap FIRST (so lines draw on top)
    cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik, zoom="auto")

    # Draw single contiguous line for entire day's journey with black border
    if len(all_simplified_waypoints) > 1:
        # Note: LineString expects (lon, lat) = (x, y), but waypoints are (lat, lon)
        line = LineString([(lon, lat) for lat, lon in all_simplified_waypoints])
        gdf_line = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326").to_crs(epsg=3857)

        # Draw black border first (wider line, behind)
        gdf_line.plot(ax=ax, color="#000000", linewidth=4, alpha=0.8, zorder=99)

        # Draw blue line on top (thinner line)
        gdf_line.plot(ax=ax, color="#1a73e8", linewidth=2, alpha=0.9, zorder=100)

    # Mark journey start and end (first point of day and last point of day)
    if all_simplified_waypoints:
        # Start marker (first point of the day)
        start_point = Point(all_simplified_waypoints[0][1], all_simplified_waypoints[0][0])
        gdf_start = gpd.GeoDataFrame(geometry=[start_point], crs="EPSG:4326").to_crs(epsg=3857)
        gdf_start.plot(ax=ax, color="#34a853", markersize=35, zorder=101, alpha=0.95)

        # End marker (last point of the day)
        if len(all_simplified_waypoints) > 1:
            end_point = Point(all_simplified_waypoints[-1][1], all_simplified_waypoints[-1][0])
            gdf_end = gpd.GeoDataFrame(geometry=[end_point], crs="EPSG:4326").to_crs(epsg=3857)
            gdf_end.plot(ax=ax, color="#ea4335", markersize=25, zorder=101, alpha=0.95)

    ax.set_axis_off()
    plt.tight_layout(pad=0)

    fig.savefig(
        out_path,
        dpi=dpi,
        format="jpg",
        facecolor="white",
    )
    plt.close(fig)
