"""Map renderer for timeline visualization."""

import math
import time
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString
import contextily as cx  # type: ignore
from geopy.geocoders import Nominatim  # type: ignore
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable  # type: ignore

from timeline_2_images.config import RenderConfiguration
from timeline_2_images.models import ProcessedSegment, RenderResult
from timeline_2_images.rendering.tile_cache_manager import TileCacheManager

matplotlib.use("Agg")


class MapRenderer:
    """Renders timeline segments on OSM maps."""

    def __init__(
        self,
        config: RenderConfiguration | None = None,
        tile_cache_dir: str | None = None,
    ):
        """Initialize map renderer.

        Args:
            config: RenderConfiguration object
            tile_cache_dir: Directory for tile caching
                (uses ~/.cache/timeline-2-images if not provided)
        """
        self.config = config or RenderConfiguration()
        self.tile_cache = TileCacheManager(tile_cache_dir)
        self.config.validate()
        self.geocoder = Nominatim(user_agent="timeline-2-images")

    def render_segments(
        self, segments: list[ProcessedSegment], output_path: str | Path
    ) -> RenderResult:
        """Render processed segments to image file.

        Args:
            segments: List of ProcessedSegment objects
            output_path: Path to save output image

        Returns:
            RenderResult with rendering info
        """
        output_path = Path(output_path)
        start_time = time.time()

        try:
            if not segments:
                raise ValueError("No segments provided to render")

            # Collect waypoints and calculate bounds
            all_waypoints = self._collect_waypoints(segments)
            if not all_waypoints:
                raise ValueError("No waypoints found in segments")

            # Calculate bounds
            bounds = self._calculate_bounds(all_waypoints)

            # Create figure and render
            self._render_map(segments, bounds, output_path)

            render_time = time.time() - start_time

            point_count = sum(len(s.simplified_waypoints) for s in segments)
            return RenderResult(
                date=output_path.stem,
                output_path=output_path,
                segment_count=len(segments),
                point_count=point_count,
                render_time=render_time,
                success=True,
            )
        except (ValueError, OSError, IOError, RuntimeError) as exception:
            render_time = time.time() - start_time
            return RenderResult(
                date=output_path.stem,
                output_path=output_path,
                segment_count=0,
                point_count=0,
                render_time=render_time,
                success=False,
                error_message=str(exception),
            )

    def _extract_from_structured_address(self, address: dict) -> str:
        """Extract place name from structured address dict.

        Args:
            address: Address dict from Nominatim

        Returns:
            Place name or empty string
        """
        priority_keys = ["city", "town", "village", "borough", "district", "suburb"]
        for key in priority_keys:
            if key in address:
                return str(address[key])
        return ""

    def _extract_from_address_string(self, address_str: str) -> str:
        """Extract place name from comma-separated address string.

        Args:
            address_str: Address string from Nominatim

        Returns:
            Place name or empty string
        """
        parts = [p.strip() for p in address_str.split(",")]
        for part in parts[1:-1]:
            if part and not part.isdigit() and len(part) > 2:
                return str(part)
        return str(parts[0].strip()) if parts else ""

    def _get_place_name(self, lat: float, lon: float) -> str:
        """Fetch place name from coordinates using Nominatim.

        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate

        Returns:
            Place name string (city/town/village/district), or empty string if unavailable
        """
        try:
            location = self.geocoder.reverse(f"{lat}, {lon}", language="en", timeout=5)
            if location and hasattr(location, "raw") and location.raw:
                address = location.raw.get("address", {})
                place = self._extract_from_structured_address(address)
                if place:
                    return place

            address_str = location.address if location else ""
            if address_str:
                return self._extract_from_address_string(address_str)
        except (GeocoderTimedOut, GeocoderUnavailable):
            pass
        except Exception:  # pylint: disable=broad-except
            pass
        return ""

    def _format_location_label(self, start_place: str, end_place: str) -> str:
        """Format start and end place names into a label."""
        if not start_place and not end_place:
            return ""
        if start_place == end_place or not end_place:
            return start_place
        return f"{start_place} - {end_place}"

    def _get_location_label(self, segments: list[ProcessedSegment]) -> str:
        """Get location label with start and end place names.

        Args:
            segments: List of ProcessedSegment objects

        Returns:
            Location label string (e.g., "New York - Boston" or just "Boston")
        """
        all_waypoints = []
        for segment in segments:
            all_waypoints.extend(segment.simplified_waypoints)

        if not all_waypoints:
            return ""

        start_lat, start_lon = all_waypoints[0]
        start_place = self._get_place_name(start_lat, start_lon)

        end_place = ""
        if len(all_waypoints) > 1:
            end_lat, end_lon = all_waypoints[-1]
            end_place = self._get_place_name(end_lat, end_lon)

        return self._format_location_label(start_place, end_place)

    def _collect_waypoints(self, segments: list[ProcessedSegment]) -> list[tuple[float, float]]:
        """Collect all waypoints from segments.

        Args:
            segments: List of ProcessedSegment objects

        Returns:
            List of (lat, lon) tuples
        """
        all_waypoints = []
        for segment in segments:
            all_waypoints.extend(segment.simplified_waypoints)
        return all_waypoints

    def _calculate_bounds(self, waypoints: list[tuple[float, float]]) -> tuple:
        """Calculate Web Mercator bounds from lat/lon points.

        Args:
            waypoints: List of (lat, lon) tuples

        Returns:
            Tuple of (minx, miny, maxx, maxy) in Web Mercator
        """
        lats = [p[0] for p in waypoints]
        lons = [p[1] for p in waypoints]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        bounds_gdf = gpd.GeoDataFrame(
            geometry=[
                Point(min_lon, min_lat),
                Point(max_lon, max_lat),
            ],
            crs="EPSG:4326",
        ).to_crs(epsg=3857)

        minx, miny, maxx, maxy = bounds_gdf.total_bounds
        minx, miny, maxx, maxy = self._apply_padding_and_minimum(minx, miny, maxx, maxy)
        return (minx, miny, maxx, maxy)

    def _apply_padding_and_minimum(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> tuple:
        """Apply padding and enforce minimum area.

        Args:
            minx, miny, maxx, maxy: Web Mercator bounds

        Returns:
            Adjusted bounds tuple
        """
        dx = (maxx - minx) or 500
        dy = (maxy - miny) or 500
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2
        max_dim = max(dx, dy)
        pad_ratio = 0.05
        padded_dim = max_dim * (1 + 2 * pad_ratio)
        half_side = padded_dim / 2

        minx = center_x - half_side
        miny = center_y - half_side
        maxx = center_x + half_side
        maxy = center_y + half_side

        # Enforce minimum area
        width_m = maxx - minx
        height_m = maxy - miny
        area_sq_km = (width_m * height_m) / 1e6

        if area_sq_km < self.config.min_area_sq_km:
            area_sq_m = self.config.min_area_sq_km * 1e6
            half_side = math.sqrt(area_sq_m) / 2
            minx = center_x - half_side
            miny = center_y - half_side
            maxx = center_x + half_side
            maxy = center_y + half_side

        return (minx, miny, maxx, maxy)

    def _render_map(
        self, segments: list[ProcessedSegment], bounds: tuple, output_path: Path
    ) -> None:
        """Render segments on map and save to file.

        Args:
            segments: List of ProcessedSegment objects
            bounds: (minx, miny, maxx, maxy) in Web Mercator
            output_path: Output file path
        """
        minx, miny, maxx, maxy = bounds

        fig_size = self.config.get_figure_size()
        fig, ax = plt.subplots(figsize=fig_size, dpi=self.config.dpi)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)
        ax.set_aspect("equal")

        osm_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        cx.add_basemap(ax, source=osm_url, zoom="auto")

        self._draw_segments(ax, segments)
        self._draw_journey_line(ax, segments)
        self._draw_markers(ax, segments)

        if self.config.add_place_names:
            location_label = self._get_location_label(segments)
            if location_label:
                fig.text(
                    0.98,
                    0.98,
                    location_label,
                    ha="right",
                    va="top",
                    fontsize=11,
                    fontweight="bold",
                    bbox={
                        "boxstyle": "round,pad=0.5",
                        "facecolor": "white",
                        "alpha": 0.85,
                        "edgecolor": "gray",
                    },
                    zorder=200,
                )

        ax.set_axis_off()
        plt.tight_layout(pad=0)
        fig.savefig(
            output_path, dpi=self.config.dpi, format=self.config.output_format, facecolor="white"
        )
        plt.close(fig)

    def _draw_segments(self, ax: Any, segments: list[ProcessedSegment]) -> None:
        """Draw individual segments.

        Args:
            ax: Matplotlib axis
            segments: List of ProcessedSegment objects
        """
        for segment in segments:
            if len(segment.simplified_waypoints) > 1:
                line = LineString([(lon, lat) for lat, lon in segment.simplified_waypoints])
                gdf_line = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326").to_crs(epsg=3857)
                gdf_line.plot(ax=ax, color="#1a73e8", linewidth=2, alpha=0.9, zorder=100)

    def _draw_journey_line(self, ax: Any, segments: list[ProcessedSegment]) -> None:
        """Draw journey line with border.

        Args:
            ax: Matplotlib axis
            segments: List of ProcessedSegment objects
        """
        all_waypoints = []
        for segment in segments:
            all_waypoints.extend(segment.simplified_waypoints)

        if len(all_waypoints) > 1:
            line = LineString([(lon, lat) for lat, lon in all_waypoints])
            gdf_line = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326").to_crs(epsg=3857)
            gdf_line.plot(ax=ax, color="#000000", linewidth=4, alpha=0.8, zorder=99)
            gdf_line.plot(ax=ax, color="#1a73e8", linewidth=2, alpha=0.9, zorder=100)

    def _draw_markers(self, ax: Any, segments: list[ProcessedSegment]) -> None:
        """Draw start and end markers.

        Args:
            ax: Matplotlib axis
            segments: List of ProcessedSegment objects
        """
        all_waypoints = []
        for segment in segments:
            all_waypoints.extend(segment.simplified_waypoints)

        if all_waypoints:
            start_point = Point(all_waypoints[0][1], all_waypoints[0][0])
            gdf_start = gpd.GeoDataFrame(geometry=[start_point], crs="EPSG:4326").to_crs(epsg=3857)
            gdf_start.plot(
                ax=ax,
                color="#34a853",
                markersize=self.config.start_marker_size,
                zorder=101,
                alpha=0.95,
            )

            if len(all_waypoints) > 1:
                end_point = Point(all_waypoints[-1][1], all_waypoints[-1][0])
                gdf_end = gpd.GeoDataFrame(geometry=[end_point], crs="EPSG:4326").to_crs(epsg=3857)
                gdf_end.plot(
                    ax=ax,
                    color="#ea4335",
                    markersize=self.config.end_marker_size,
                    zorder=101,
                    alpha=0.95,
                )

    def clear_cache(self) -> None:
        """Clear tile cache."""
        self.tile_cache.clear()

    def get_cache_info(self) -> dict:
        """Get cache information.

        Returns:
            Dictionary with cache stats
        """
        return self.tile_cache.get_info()
