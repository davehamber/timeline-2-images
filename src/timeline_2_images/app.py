# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Timeline-to-images application orchestrator."""

from pathlib import Path
from typing import Any

from timeline_2_images.processors import TimelineProcessor, SegmentProcessor
from timeline_2_images.rendering import MapRenderer
from timeline_2_images.rendering.tile_cache_manager import TileCacheManager
from timeline_2_images.config import RenderConfiguration, DateRangeQuery
from timeline_2_images.models import RenderResult
from timeline_2_images.validators import TimelineValidator, TimelineValidationError
from timeline_2_images.day_connector_builder import DayConnectorBuilder
from geopy.geocoders import Nominatim


class TimelineApp:
    """Main application class orchestrating timeline processing and rendering."""

    def __init__(
        self,
        json_path: str,
        output_dir: str = "output",
        config: RenderConfiguration | None = None,
        cache_dir: str | None = None,
        processor: TimelineProcessor | None = None,
        segment_processor: SegmentProcessor | None = None,
        renderer: MapRenderer | None = None,
        validate: bool = True,
    ):
        """Initialize timeline app with dependency injection.

        Args:
            json_path: Path to Timeline.json file
            output_dir: Directory for output images
            config: RenderConfiguration (uses defaults if not provided)
            cache_dir: Directory for tile cache (uses ~/.cache/timeline-2-images if not provided)
            processor: TimelineProcessor instance (created if not provided)
            segment_processor: SegmentProcessor instance (created if not provided)
            renderer: MapRenderer instance (created if not provided)
            validate: Whether to validate Timeline.json structure on init (default: True)

        Raises:
            TimelineValidationError: If validate=True and Timeline.json structure is invalid
        """
        # Validate input file if requested
        if validate:
            TimelineValidator().validate_timeline_structure(json_path)

        self.json_path = json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Use provided config or create default
        if config is None:
            config = RenderConfiguration()
        self.config = config
        self.config.validate()

        # Use provided dependencies or create them with defaults
        if processor is None:
            processor = TimelineProcessor(json_path)
        self.processor = processor

        if segment_processor is None:
            segment_processor = SegmentProcessor()
        self.segment_processor = segment_processor

        if renderer is None:
            tile_cache = TileCacheManager(cache_dir)
            geocoder = Nominatim(user_agent="timeline-2-images")
            renderer = MapRenderer(config=self.config, tile_cache=tile_cache, geocoder=geocoder)
        self.renderer = renderer

        # Initialize connector builder for multi-day rendering
        self.connector_builder = DayConnectorBuilder(self.processor, self.segment_processor)

    @classmethod
    def validate_file(cls, json_path: str) -> None:
        """Validate Timeline.json structure without initializing the app.

        Args:
            json_path: Path to Timeline.json file

        Raises:
            TimelineValidationError: If Timeline.json structure is invalid

        Example:
            >>> TimelineApp.validate_file("Timeline.json")
            >>> app = TimelineApp("Timeline.json", validate=False)
        """
        TimelineValidator().validate_timeline_structure(json_path)

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

    def process_date_range_bytes(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        days: int = 14,
    ) -> list[tuple[bytes | None, RenderResult]]:
        """Process and render a date range, returning image bytes for each date.

        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            days: Number of days (default 14)

        Returns:
            List of tuples (image_bytes, RenderResult) for each date
        """
        query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
        dates = self.processor.get_date_range(query)

        results = []
        for date in dates:
            image_bytes, result = self.process_date_bytes(date)
            results.append((image_bytes, result))

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

        except (ValueError, OSError, IOError, RuntimeError) as exception:
            return RenderResult(
                date=date,
                output_path=self.output_dir / f"{date}.jpg",
                segment_count=0,
                point_count=0,
                render_time=0.0,
                success=False,
                error_message=str(exception),
            )

    def process_date_bytes(self, date: str) -> tuple[bytes | None, RenderResult]:
        """Process and render a single date, returning image bytes.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Tuple of (image_bytes, RenderResult) where image_bytes is None if rendering failed
        """
        try:
            segments = self.processor.load_segments_for_day(date)

            if not segments:
                return None, RenderResult(
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
                return None, RenderResult(
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

            if result.was_successful():
                try:
                    with open(result.output_path, "rb") as f:
                        image_bytes = f.read()
                    return image_bytes, result
                except (IOError, OSError) as e:
                    return None, RenderResult(
                        date=date,
                        output_path=result.output_path,
                        segment_count=result.segment_count,
                        point_count=result.point_count,
                        render_time=result.render_time,
                        success=False,
                        error_message=f"Failed to read rendered image: {str(e)}",
                    )

            return None, result

        except (ValueError, OSError, IOError, RuntimeError) as exception:
            return None, RenderResult(
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

    def get_date_range(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        days: int = 14,
    ) -> list[str]:
        """Get dates with data based on flexible date range parameters.

        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            days: Number of days (default 14)

        Returns:
            List of YYYY-MM-DD date strings within the range
        """
        query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
        return self.processor.get_date_range(query)

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

    def process_date_range_single_image(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        days: int = 14,
    ) -> RenderResult:
        """Process date range and render single combined image.

        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            days: Number of days (default 14)

        Returns:
            RenderResult with single combined image
        """
        dates = self.get_date_range(start_date=start_date, end_date=end_date, days=days)

        if not dates:
            return RenderResult(
                date=f"{start_date or 'unknown'}_to_{end_date or 'unknown'}",
                output_path=self.output_dir / "combined.jpg",
                segment_count=0,
                point_count=0,
                render_time=0.0,
                success=False,
                error_message="No dates found in range",
            )

        combined_segments = self.connector_builder.build_segments_with_connectors(dates)

        if not combined_segments:
            return RenderResult(
                date=f"{dates[0]}_to_{dates[-1]}",
                output_path=self.output_dir / f"{dates[0]}_to_{dates[-1]}.jpg",
                segment_count=0,
                point_count=0,
                render_time=0.0,
                success=False,
                error_message="No segments found in date range",
            )

        output_path = self.output_dir / f"{dates[0]}_to_{dates[-1]}.jpg"
        result = self.renderer.render_combined_segments(combined_segments, str(output_path))
        return result

