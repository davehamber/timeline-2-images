"""OpenStreetMap tile downloading and basemap creation."""

import io
import logging
import math
import time
from pathlib import Path
from typing import Any, Optional

import mercantile
import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class TileDownloader:
    """Downloads and merges OpenStreetMap tiles into basemap images."""

    TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    TILE_SIZE = 256
    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 0.2  # Rate limiting: 200ms between requests
    MAX_RETRIES = 2

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize tile downloader.

        Args:
            cache_dir: Directory to cache downloaded tiles (optional)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_request_time = 0.0

    def add_basemap(self, ax: Any) -> None:
        """Add OSM basemap to matplotlib axis.

        Follows contextility's add_basemap() approach: reads bounds from axis,
        downloads appropriate tiles, and displays them on the axis.
        Automatically expands single-point bounds to minimum area.

        Args:
            ax: Matplotlib axis with xlim/ylim set to Web Mercator bounds
        """
        minx_wm, miny_wm, maxx_wm, maxy_wm = self._get_and_validate_bounds(ax)
        if minx_wm is None:
            return

        min_lon, min_lat, max_lon, max_lat = self._convert_to_lat_lon(
            minx_wm,
            miny_wm,
            maxx_wm,
            maxy_wm,  # type: ignore[arg-type]
        )
        zoom = self._calculate_zoom(min_lon, min_lat, max_lon, max_lat)

        tiles = list(mercantile.tiles(min_lon, min_lat, max_lon, max_lat, zoom))
        logger.info(f"Found {len(tiles)} tiles at zoom {zoom}")

        if not tiles:
            logger.warning("No tiles found for bounds")
            return

        tile_arrays = self._download_all_tiles(tiles)
        basemap = self._merge_tiles(tiles, tile_arrays)
        self._display_basemap(ax, tiles, basemap)

    def _get_and_validate_bounds(self, ax: Any) -> tuple[Optional[float], ...]:
        """Get and validate bounds from axis, expanding if needed."""
        minx_wm, maxx_wm = ax.get_xlim()
        miny_wm, maxy_wm = ax.get_ylim()

        bounds_width = maxx_wm - minx_wm
        bounds_height = maxy_wm - miny_wm
        logger.info(f"add_basemap bounds: width={bounds_width}, height={bounds_height}")

        if bounds_width <= 0 or bounds_height <= 0:
            logger.info("Expanding single-point bounds to minimum area (5 sq km)")
            minx_wm, miny_wm, maxx_wm, maxy_wm = self._expand_to_minimum_area(
                minx_wm, miny_wm, maxx_wm, maxy_wm
            )

        return minx_wm, miny_wm, maxx_wm, maxy_wm

    def _convert_to_lat_lon(
        self, minx_wm: float, miny_wm: float, maxx_wm: float, maxy_wm: float
    ) -> tuple[float, float, float, float]:
        """Convert Web Mercator bounds to lat/lon."""
        import geopandas as gpd
        from shapely.geometry import Point

        gdf_wm = gpd.GeoDataFrame(
            geometry=[
                Point(minx_wm, miny_wm),
                Point(maxx_wm, maxy_wm),
            ],
            crs="EPSG:3857",
        ).to_crs(epsg=4326)

        min_lon, min_lat = gdf_wm.geometry[0].x, gdf_wm.geometry[0].y  # type: ignore[attr-defined]
        max_lon, max_lat = gdf_wm.geometry[1].x, gdf_wm.geometry[1].y  # type: ignore[attr-defined]
        logger.info(f"Converted to LL: ({min_lon}, {min_lat}, {max_lon}, {max_lat})")

        return min_lon, min_lat, max_lon, max_lat

    def _download_all_tiles(self, tiles: list) -> list:
        """Download all tiles and return array representations."""
        tile_arrays = []
        for tile in tiles:
            arr = self._get_tile_array(tile)
            tile_arrays.append(arr)
        return tile_arrays

    def _get_tile_array(self, tile: Any) -> np.ndarray:
        """Download a tile and convert to numpy array, or return placeholder."""
        try:
            img = self._download_tile(tile.x, tile.y, tile.z)
            if img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                logger.info(f"Downloaded tile {tile.z}/{tile.x}/{tile.y}")
                return np.array(img)

            logger.warning(f"Failed to download tile {tile.z}/{tile.x}/{tile.y}")
        except Exception as e:
            logger.error(
                f"Exception downloading tile {tile.z}/{tile.x}/{tile.y}: {e}",
                exc_info=True,
            )

        return np.full((self.TILE_SIZE, self.TILE_SIZE, 3), 200, dtype=np.uint8)

    def _display_basemap(self, ax: Any, tiles: list, basemap: np.ndarray) -> None:
        """Calculate extent and display basemap on axis."""
        tile_bounds = self._calculate_tile_extent(tiles)
        extent = (
            tile_bounds["minx"],
            tile_bounds["maxx"],
            tile_bounds["miny"],
            tile_bounds["maxy"],
        )
        logger.info(f"Actual tile extent: {extent}")
        ax.imshow(basemap, extent=extent, aspect="auto", origin="upper", zorder=0)

    def _calculate_zoom(
        self, min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> int:
        """Calculate optimal zoom level based on geographic bounds.

        Uses contextility's algorithm: finds minimum zoom level that covers
        the bounding box. Accounts separately for lon/lat dimensions and
        uses the tighter constraint.

        Args:
            min_lon, min_lat, max_lon, max_lat: Geographic bounds in lon/lat

        Returns:
            Zoom level (0-30)
        """
        lon_length = max_lon - min_lon
        lat_length = max_lat - min_lat

        zoom_lon = math.ceil(math.log2(360 * 2.0 / lon_length)) if lon_length > 0 else 0
        zoom_lat = math.ceil(math.log2(360 * 2.0 / lat_length)) if lat_length > 0 else 0

        return min(zoom_lon, zoom_lat)

    def _download_tile(self, x: int, y: int, z: int) -> Optional[Image.Image]:
        """Download a single tile from OpenStreetMap.

        Args:
            x, y, z: Tile coordinates

        Returns:
            PIL Image if successful, None otherwise
        """
        cached = self._load_cached_tile(x, y, z)
        if cached:
            return cached

        self._apply_rate_limiting()
        url = self.TILE_URL.format(z=z, x=x, y=y)

        for attempt in range(self.MAX_RETRIES):
            result = self._try_download_tile(url, x, y, z, attempt)
            if result is not None:
                return result
            if not self._should_retry(attempt):
                return None

        return None

    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting between tile requests."""
        time.sleep(max(0, self.REQUEST_DELAY - (time.time() - self.last_request_time)))
        self.last_request_time = time.time()

    def _try_download_tile(
        self, url: str, x: int, y: int, z: int, attempt: int
    ) -> Optional[Image.Image]:
        """Attempt to download a single tile with error handling."""
        try:
            response = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                headers={"User-Agent": "timeline-2-images/1.0"},
            )
            return (
                self._process_successful_tile(response, x, y, z)
                if self._handle_tile_response_error(response, x, y, z, attempt)
                else None
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as e:
            self._log_tile_error(e, x, y, z, attempt)
            return None

    def _log_tile_error(self, error: Exception, x: int, y: int, z: int, attempt: int) -> None:
        """Log tile download error if it's the last attempt."""
        if attempt == self.MAX_RETRIES - 1:
            if isinstance(error, requests.exceptions.Timeout):
                logger.warning(f"Timeout downloading tile {z}/{x}/{y}")
            else:
                logger.warning(f"Error downloading tile {z}/{x}/{y}: {error}")

    def _handle_tile_response_error(
        self, response: requests.Response, x: int, y: int, z: int, attempt: int
    ) -> bool:
        """Handle HTTP response errors. Returns True if successful, False if retriable."""
        if response.status_code == 429:
            if attempt < self.MAX_RETRIES - 1:
                retry_after = int(response.headers.get("Retry-After", 1))
                time.sleep(retry_after)
                return False
            return False

        if response.status_code == 403:
            return False

        response.raise_for_status()
        return True

    def _process_successful_tile(
        self, response: requests.Response, x: int, y: int, z: int
    ) -> Optional[Image.Image]:
        """Process successful tile download and cache it."""
        try:
            img = Image.open(io.BytesIO(response.content))
            self._save_cached_tile(img, x, y, z)
            return img
        except Exception as e:
            logger.error(f"Error processing tile {z}/{x}/{y}: {e}")
            return None

    def _should_retry(self, attempt: int) -> bool:
        """Check if we should retry after a failed attempt."""
        return attempt < self.MAX_RETRIES - 1

    def _load_cached_tile(self, x: int, y: int, z: int) -> Optional[Image.Image]:
        """Load tile from cache if available.

        Args:
            x, y, z: Tile coordinates

        Returns:
            PIL Image if cached, None otherwise
        """
        if not self.cache_dir:
            return None

        cache_path = self.cache_dir / f"{z}_{x}_{y}.png"
        if cache_path.exists():
            try:
                return Image.open(cache_path)
            except Exception:
                return None
        return None

    def _save_cached_tile(self, tile: Image.Image, x: int, y: int, z: int) -> None:
        """Save tile to cache.

        Args:
            tile: PIL Image to cache
            x, y, z: Tile coordinates
        """
        if not self.cache_dir:
            return

        cache_path = self.cache_dir / f"{z}_{x}_{y}.png"
        try:
            tile.save(cache_path)
        except Exception:
            pass

    def _merge_tiles(self, tiles: list, arrays: list) -> np.ndarray:
        """Merge multiple tile arrays into a single image.

        Args:
            tiles: List of mercantile.Tile objects
            arrays: List of numpy arrays (one per tile)

        Returns:
            Merged numpy array (height, width, 3)
        """
        # Get tile coordinates
        tile_xys = np.array([(t.x, t.y) for t in tiles])
        logger.info(f"Tile coordinates min: {tile_xys.min(axis=0)}, max: {tile_xys.max(axis=0)}")

        # Normalize to start at 0
        indices = tile_xys - tile_xys.min(axis=0)

        # Calculate merged image dimensions
        n_x = indices[:, 0].max() + 1
        n_y = indices[:, 1].max() + 1
        merged = np.zeros((n_y * self.TILE_SIZE, n_x * self.TILE_SIZE, 3), dtype=np.uint8)
        logger.info(f"Merged image dimensions: {n_y * self.TILE_SIZE}x{n_x * self.TILE_SIZE}")

        # Paste each tile into merged image
        for tile, idx, arr in zip(tiles, indices, arrays):
            x_pos, y_pos = idx
            merged[
                y_pos * self.TILE_SIZE : (y_pos + 1) * self.TILE_SIZE,
                x_pos * self.TILE_SIZE : (x_pos + 1) * self.TILE_SIZE,
                :,
            ] = arr

        return merged

    def _calculate_tile_extent(self, tiles: list) -> dict:
        """Calculate Web Mercator bounds of downloaded tiles.

        Tiles are rectangular blocks. This method calculates the actual geographic
        extent of the merged tile grid, which may differ from requested bounds.

        Args:
            tiles: List of mercantile.Tile objects

        Returns:
            Dict with keys: minx, miny, maxx, maxy (Web Mercator bounds)
        """
        import geopandas as gpd
        from shapely.geometry import Point

        if not tiles:
            return {"minx": 0, "miny": 0, "maxx": 0, "maxy": 0}

        # Get bounds of each tile and find min/max
        min_lon = 180
        max_lon = -180
        min_lat = 90
        max_lat = -90

        for tile in tiles:
            # mercantile.bounds returns (west, south, east, north) in lon/lat
            bounds = mercantile.bounds(tile)
            min_lon = min(min_lon, bounds.west)
            max_lon = max(max_lon, bounds.east)
            min_lat = min(min_lat, bounds.south)
            max_lat = max(max_lat, bounds.north)

        # Convert to Web Mercator using geopandas (consistent with other conversions)
        gdf_wm = gpd.GeoDataFrame(
            geometry=[
                Point(min_lon, min_lat),
                Point(max_lon, max_lat),
            ],
            crs="EPSG:4326",
        ).to_crs(epsg=3857)

        minx_wm, miny_wm, maxx_wm, maxy_wm = gdf_wm.total_bounds

        return {
            "minx": minx_wm,
            "miny": miny_wm,
            "maxx": maxx_wm,
            "maxy": maxy_wm,
        }

    @staticmethod
    def _expand_to_minimum_area(
        minx: float, miny: float, maxx: float, maxy: float, min_area_sq_km: float = 5.0
    ) -> tuple:
        """Expand bounds to show minimum area if currently too small.

        For single-point locations or very small regions, expand to at least
        the specified minimum area, maintaining square aspect ratio.

        Args:
            minx, miny, maxx, maxy: Bounds in Web Mercator
            min_area_sq_km: Minimum area to display (default 5 sq km)

        Returns:
            Expanded bounds tuple (minx, miny, maxx, maxy)
        """
        current_width = maxx - minx
        current_height = maxy - miny

        if current_width <= 0 or current_height <= 0:
            current_width = max(current_width, 1)
            current_height = max(current_height, 1)

        current_area_sq_m = current_width * current_height
        min_area_sq_m = min_area_sq_km * 1e6

        if current_area_sq_m >= min_area_sq_m:
            return (minx, miny, maxx, maxy)

        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        aspect_ratio = current_width / current_height if current_height > 0 else 1.0
        half_height = math.sqrt(min_area_sq_m / aspect_ratio) / 2
        half_width = half_height * aspect_ratio

        return (
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height,
        )
