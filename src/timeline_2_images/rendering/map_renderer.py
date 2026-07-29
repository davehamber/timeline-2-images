"""Map renderer for timeline visualization."""

import math
import time
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString

from timeline_2_images.config import RenderConfiguration
from timeline_2_images.models import ProcessedSegment, RenderResult
from timeline_2_images.rendering.tile_cache_manager import TileCacheManager
from timeline_2_images.rendering.tile_downloader import TileDownloader
from timeline_2_images.rendering.place_name_geocoder import PlaceNameGeocoder

matplotlib.use("Agg")


class MapRenderer:
    """Renders timeline segments on OSM maps."""

    def __init__(
        self,
        config: RenderConfiguration | None = None,
        tile_cache: TileCacheManager | None = None,
        geocoder: PlaceNameGeocoder | None = None,
        tile_cache_dir: str | None = None,
        osm_cache_dir: str | None = None,
    ):
        """Initialize map renderer with dependency injection support.

        Args:
            config: RenderConfiguration object (created if not provided)
            tile_cache: TileCacheManager instance (created if not provided)
            geocoder: PlaceNameGeocoder instance (created if not provided)
            tile_cache_dir: Directory for tile cache
            osm_cache_dir: Directory for OSM tile cache
        """
        self.config = config or RenderConfiguration()
        self.tile_cache = tile_cache or TileCacheManager(tile_cache_dir)
        self.geocoder = geocoder or PlaceNameGeocoder()
        self.tile_downloader = TileDownloader(cache_dir=osm_cache_dir)
        self.config.validate()

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
            return self.geocoder.extract_place_name(location)
        except Exception:  # pylint: disable=broad-except
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

    def _calculate_padded_bounds(
        self, dx: float, dy: float, center_x: float, center_y: float
    ) -> tuple:
        """Calculate bounds with padding and aspect ratio correction."""
        pad_ratio = 0.05
        padded_dx = dx * (1 + 2 * pad_ratio)
        padded_dy = dy * (1 + 2 * pad_ratio)

        image_aspect = self.config.image_width / self.config.image_height
        padded_aspect = padded_dx / padded_dy

        if padded_aspect > image_aspect:
            half_width = padded_dx / 2
            half_height = padded_dx / (2 * image_aspect)
        else:
            half_height = padded_dy / 2
            half_width = padded_dy * image_aspect / 2

        return (
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height,
        )

    def _enforce_minimum_area(
        self, minx: float, miny: float, maxx: float, maxy: float, center_x: float, center_y: float
    ) -> tuple:
        """Enforce minimum area constraint."""
        width_m = maxx - minx
        height_m = maxy - miny
        area_sq_km = (width_m * height_m) / 1e6

        if area_sq_km >= self.config.min_area_sq_km:
            return (minx, miny, maxx, maxy)

        area_sq_m = self.config.min_area_sq_km * 1e6
        aspect_ratio = width_m / height_m if height_m > 0 else 1.0
        half_height = math.sqrt(area_sq_m / aspect_ratio) / 2
        half_width = half_height * aspect_ratio

        return (
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height,
        )

    def _apply_padding_and_minimum(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> tuple:
        """Apply padding and enforce minimum area respecting image aspect ratio.

        Args:
            minx, miny, maxx, maxy: Web Mercator bounds

        Returns:
            Adjusted bounds tuple
        """
        dx = (maxx - minx) or 500
        dy = (maxy - miny) or 500
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        minx, miny, maxx, maxy = self._calculate_padded_bounds(dx, dy, center_x, center_y)
        return self._enforce_minimum_area(minx, miny, maxx, maxy, center_x, center_y)

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
        ax.set_aspect("auto")

        # Add OSM basemap
        self.tile_downloader.add_basemap(ax)
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
            gdf_line.plot(
                ax=ax,
                color="#000000",
                linewidth=self.config.line_border_width,
                alpha=0.8,
                zorder=99,
            )
            gdf_line.plot(
                ax=ax,
                color="#1a73e8",
                linewidth=self.config.line_width,
                alpha=self.config.line_alpha,
                zorder=100,
            )

    def _draw_combined_journey_line(self, ax: Any, segments: list[ProcessedSegment]) -> None:
        """Draw journey line for combined routes without closing the loop.

        Args:
            ax: Matplotlib axis
            segments: List of ProcessedSegment objects
        """
        # Sort segments by start time to ensure chronological order
        sorted_segments = sorted(segments, key=lambda s: s.segment.start_time)

        all_waypoints = []
        for segment in sorted_segments:
            all_waypoints.extend(segment.simplified_waypoints)

        if len(all_waypoints) > 1:
            line = LineString([(lon, lat) for lat, lon in all_waypoints])
            gdf_line = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326").to_crs(epsg=3857)

            gdf_line.plot(
                ax=ax,
                color="#000000",
                linewidth=self.config.line_border_width,
                alpha=0.8,
                zorder=99,
            )
            gdf_line.plot(
                ax=ax,
                color="#1a73e8",
                linewidth=self.config.line_width,
                alpha=self.config.line_alpha,
                zorder=100,
            )

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

    def render_combined_segments(
        self, segments: list[ProcessedSegment], output_path: str | Path
    ) -> RenderResult:
        """Render combined segments from multiple days into single image.

        Args:
            segments: List of ProcessedSegment objects (may include connectors)
            output_path: Path to save output image

        Returns:
            RenderResult with rendering info
        """
        output_path = Path(output_path)
        start_time = time.time()

        try:
            if not segments:
                raise ValueError("No segments provided to render")

            all_waypoints = self._collect_waypoints(segments)
            if not all_waypoints:
                raise ValueError("No waypoints found in segments")

            bounds = self._calculate_combined_bounds(all_waypoints)

            self._render_combined_map(segments, bounds, output_path)

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

    def _get_latlon_bounds(self, waypoints: list[tuple[float, float]]) -> tuple:
        """Extract lat/lon bounds from waypoints."""
        lats = [p[0] for p in waypoints]
        lons = [p[1] for p in waypoints]
        min_lat, max_lat, min_lon, max_lon = min(lats), max(lats), min(lons), max(lons)
        # Diagnostic log for debugging coordinate issues
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Bounds from {len(waypoints)} waypoints: "
            f"lat {min_lat:.2f}°-{max_lat:.2f}°, lon {min_lon:.2f}°-{max_lon:.2f}°"
        )
        return min_lat, max_lat, min_lon, max_lon

    def _project_to_mercator(
        self, min_lat: float, max_lat: float, min_lon: float, max_lon: float
    ) -> tuple:
        """Project lat/lon bounds to Web Mercator coordinates."""
        # Sanity check for coordinate values
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Latitude bounds appear invalid: {min_lat}°-{max_lat}° "
                f"(expected -90 to 90). Swapping with longitude?"
            )

        bounds_gdf = gpd.GeoDataFrame(
            geometry=[Point(min_lon, min_lat), Point(max_lon, max_lat)],
            crs="EPSG:4326",
        ).to_crs(epsg=3857)
        return tuple(bounds_gdf.total_bounds)

    def _calculate_border_padded_bounds(
        self, dx: float, dy: float, center_x: float, center_y: float
    ) -> tuple:
        """Calculate bounds with pixel-based border respecting aspect ratio."""
        pixel_size_x = dx / (self.config.image_width or 1000)
        pixel_size_y = dy / (self.config.image_height or 1000)

        border_x = 5 * pixel_size_x
        border_y = 5 * pixel_size_y

        padded_dx = dx + 2 * border_x
        padded_dy = dy + 2 * border_y

        image_aspect = self.config.image_width / self.config.image_height
        padded_aspect = padded_dx / padded_dy

        if padded_aspect > image_aspect:
            half_width = padded_dx / 2
            half_height = padded_dx / (2 * image_aspect)
        else:
            half_height = padded_dy / 2
            half_width = padded_dy * image_aspect / 2

        return (
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height,
        )

    def _calculate_combined_bounds(self, waypoints: list[tuple[float, float]]) -> tuple:
        """Calculate bounds with ~5 pixel border respecting image aspect ratio.

        Args:
            waypoints: List of (lat, lon) tuples

        Returns:
            Tuple of (minx, miny, maxx, maxy) in Web Mercator
        """
        min_lat, max_lat, min_lon, max_lon = self._get_latlon_bounds(waypoints)
        minx, miny, maxx, maxy = self._project_to_mercator(min_lat, max_lat, min_lon, max_lon)

        dx = maxx - minx or 500
        dy = maxy - miny or 500
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        return self._calculate_border_padded_bounds(dx, dy, center_x, center_y)

    def _render_combined_map(
        self, segments: list[ProcessedSegment], bounds: tuple, output_path: Path
    ) -> None:
        """Render combined segments on map and save to file.

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
        ax.set_aspect("auto")

        self.tile_downloader.add_basemap(ax)

        self._draw_combined_journey_line(ax, segments)
        self._draw_large_span_waypoint_markers(ax, segments)
        self._draw_first_and_last_markers(ax, segments)

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

    def _draw_large_span_waypoint_markers(self, ax: Any, segments: list[ProcessedSegment]) -> None:
        """Draw waypoint markers for segments spanning >100km.

        Args:
            ax: Matplotlib axis
            segments: List of ProcessedSegment objects
        """
        pass

    def _draw_first_and_last_markers(self, ax: Any, segments: list[ProcessedSegment]) -> None:
        """Draw start marker at first point and end marker at last point.

        Args:
            ax: Matplotlib axis
            segments: List of ProcessedSegment objects
        """
        all_waypoints = []
        for segment in segments:
            all_waypoints.extend(segment.simplified_waypoints)

        if not all_waypoints:
            return

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
