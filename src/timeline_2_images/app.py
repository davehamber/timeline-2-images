"""Timeline-to-images application orchestrator."""

from pathlib import Path
from typing import Any

from timeline_2_images.processors import TimelineProcessor, SegmentProcessor
from timeline_2_images.rendering import MapRenderer
from timeline_2_images.config import RenderConfiguration, DateRangeQuery
from timeline_2_images.models import RenderResult
from timeline_2_images.cache import CacheManager


class TimelineApp:
    """Main application class orchestrating timeline processing and rendering."""

    def __init__(
        self,
        json_path: str,
        output_dir: str = "output",
        config: RenderConfiguration | None = None,
        cache_manager: CacheManager | None = None,
        cache_dir: str = ".tile_cache",
    ):
        """Initialize timeline app.

        Args:
            json_path: Path to Timeline.json file
            output_dir: Directory for output images
            config: RenderConfiguration (uses defaults if not provided)
            cache_manager: CacheManager for persistent segment caching
            cache_dir: Directory for tile cache
        """
        self.json_path = json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.config = config or RenderConfiguration()
        self.config.validate()

        self.processor = TimelineProcessor(json_path, cache_manager)
        self.segment_processor = SegmentProcessor()
        self.renderer = MapRenderer(config=self.config, tile_cache_dir=cache_dir)

    def process_date_range(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        days: int = 14,
    ) -> list[RenderResult]:
        """Process and render a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            days: Number of days (default 14)

        Returns:
            List of RenderResult objects
        """
        query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
        dates = self.processor.get_date_range(query)

        results = []
        for date in dates:
            result = self.process_date(date)
            results.append(result)

        return results

    def process_date(self, date: str) -> RenderResult:
        """Process and render a single date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            RenderResult with rendering status
        """
        try:
            segments = self.processor.load_segments_for_day(date)

            if not segments:
                return RenderResult(
                    date=date,
                    output_path=self.output_dir / f"{date}.jpg",
                    segment_count=0,
                    point_count=0,
                    render_time=0.0,
                    success=False,
                    error_message="No segments found for date",
                )

            processed_segments = self.segment_processor.process_segments(segments)

            if not processed_segments:
                return RenderResult(
                    date=date,
                    output_path=self.output_dir / f"{date}.jpg",
                    segment_count=0,
                    point_count=0,
                    render_time=0.0,
                    success=False,
                    error_message="No segments after processing",
                )

            output_path = self.output_dir / f"{date}.jpg"
            result = self.renderer.render_segments(processed_segments, str(output_path))
            return result

        except Exception as exception:
            return RenderResult(
                date=date,
                output_path=self.output_dir / f"{date}.jpg",
                segment_count=0,
                point_count=0,
                render_time=0.0,
                success=False,
                error_message=str(exception),
            )

    def get_available_dates(self) -> list[str]:
        """Get all available dates in timeline.

        Returns:
            List of YYYY-MM-DD date strings
        """
        return self.processor.get_available_dates()

    def get_statistics(self) -> dict[str, Any]:
        """Get application statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "json_path": str(self.json_path),
            "output_dir": str(self.output_dir),
            "image_size": self.config.image_size,
            "tile_cache": self.renderer.get_cache_info(),
        }

    def clear_caches(self) -> None:
        """Clear all caches (session and tile)."""
        self.processor.clear_cache()
        self.renderer.clear_cache()
