"""Batch processing configuration for resource pooling."""

from timeline_2_images.config.render_configuration import RenderConfiguration
from timeline_2_images.rendering import MapRenderer
from timeline_2_images.rendering.tile_cache_manager import TileCacheManager
from geopy.geocoders import Nominatim


class BatchConfig:
    """Configuration for batch processing with shared resources.

    Enables efficient batch processing of multiple timelines by sharing expensive
    resources (geocoder, tile cache, renderer) across multiple TimelineApp instances.

    Example:
        >>> batch_config = BatchConfig(
        ...     render_config=RenderConfiguration(image_size=800),
        ...     cache_dir="/path/to/cache"
        ... )
        >>> app1 = TimelineApp("timeline1.json", batch_config=batch_config)
        >>> app2 = TimelineApp("timeline2.json", batch_config=batch_config)
        >>> # Both apps reuse the same geocoder and tile cache
    """

    def __init__(
        self,
        render_config: RenderConfiguration | None = None,
        cache_dir: str | None = None,
        geocoder: Nominatim | None = None,
    ):
        """Initialize batch configuration with shared resources.

        Args:
            render_config: RenderConfiguration for all apps (uses default if not provided)
            cache_dir: Directory for tile cache (uses ~/.cache/timeline-2-images if not provided)
            geocoder: Nominatim geocoder instance (creates new if not provided)
        """
        self.render_config = render_config or RenderConfiguration()
        self.render_config.validate()

        self.tile_cache = TileCacheManager(cache_dir)
        self.geocoder = geocoder or Nominatim(user_agent="timeline-2-images")

    def create_renderer(self) -> MapRenderer:
        """Create a MapRenderer using shared resources.

        Returns:
            MapRenderer instance using batch-shared tile cache and geocoder
        """
        return MapRenderer(
            config=self.render_config,
            tile_cache=self.tile_cache,
            geocoder=self.geocoder,
        )
