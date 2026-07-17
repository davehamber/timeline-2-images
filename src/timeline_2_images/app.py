"""Timeline-to-images application orchestrator."""

from pathlib import Path
from typing import Any

from timeline_2_images.processors import TimelineProcessor, SegmentProcessor
from timeline_2_images.rendering import MapRenderer
from timeline_2_images.config import RenderConfiguration, DateRangeQuery
from timeline_2_images.models import RenderResult


class TimelineApp:
    """Main application class orchestrating timeline processing and rendering."""

    def __init__(
        self,
        json_path: str,
        output_dir: str = "output",
        config: RenderConfiguration | None = None,
        cache_dir: str | None = None,
    ):
        """Initialize timeline app.

        Args:
            json_path: Path to Timeline.json file
            output_dir: Directory for output images
            config: RenderConfiguration (uses defaults if not provided)
            cache_dir: Directory for tile cache (uses ~/.cache/timeline-2-images if not provided)
        """
        self.json_path = json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.config = config or RenderConfiguration()
        self.config.validate()

        self.processor = TimelineProcessor(json_path)
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
        query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
        dates = self.processor.get_date_range(query)

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

        combined_segments = self._collect_segments_for_date_range(dates)

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

    def _collect_segments_for_date_range(self, dates: list[str]) -> list[Any]:
        """Collect all segments across date range with day connectors.

        Args:
            dates: List of YYYY-MM-DD date strings

        Returns:
            List of ProcessedSegment objects with connector segments
        """
        all_segments = []

        for date in dates:
            segments = self.processor.load_segments_for_day(date)
            processed = self.segment_processor.process_segments(segments)
            all_segments.extend(processed)

        self._debug_large_span_segments(all_segments)
        return self._add_day_connectors(all_segments, dates) if all_segments else []

    def _debug_large_span_segments(self, segments: list[Any]) -> None:
        """Debug: identify segments that span large geographic distances.

        Args:
            segments: List of ProcessedSegment objects
        """

        for idx, segment in enumerate(segments):
            if not segment.simplified_waypoints or len(segment.simplified_waypoints) < 2:
                continue

            waypoints = segment.simplified_waypoints
            min_lat = min(wp[0] for wp in waypoints)
            max_lat = max(wp[0] for wp in waypoints)
            min_lon = min(wp[1] for wp in waypoints)
            max_lon = max(wp[1] for wp in waypoints)

            lat_span = max_lat - min_lat
            lon_span = max_lon - min_lon
            approx_km = (lat_span + lon_span) * 111

            if approx_km > 50:
                start_wp = waypoints[0]
                end_wp = waypoints[-1]
                seg_type = segment.segment.segment_type
                start_time = segment.segment.start_time
                end_time = segment.segment.end_time

                orig_count = len(segment.segment.waypoints)
                simp_count = len(waypoints)
                print(f"\n[SEGMENT DEBUG] Large span detected ({approx_km:.1f} km)")
                print(f"  Segment type: {seg_type}")
                print(f"  Start: {start_wp[0]:.4f}N, {start_wp[1]:.4f}E")
                print(f"  End: {end_wp[0]:.4f}N, {end_wp[1]:.4f}E")
                print(f"  Time: {start_time} to {end_time}")
                print(f"  Original waypoints: {orig_count}")
                print(f"  Simplified waypoints: {simp_count}")

    def _add_day_connectors(self, segments: list[Any], dates: list[str]) -> list[Any]:
        """Add connector segments between day boundaries.

        Args:
            segments: List of ProcessedSegment objects
            dates: List of dates being processed

        Returns:
            Modified segments with connectors inserted
        """
        if len(dates) <= 1:
            return segments

        result = []
        for segment in segments:
            result.append(segment)

        connectors = self._find_day_connectors(dates)
        result.extend(connectors)

        return result

    def _find_day_connectors(self, dates: list[str]) -> list[Any]:
        """Find and create connector segments between consecutive days.

        Args:
            dates: List of dates being processed

        Returns:
            List of connector segments
        """
        connectors = []

        for i in range(len(dates) - 1):
            current_segments = self.processor.load_segments_for_day(dates[i])
            current_processed = self.segment_processor.process_segments(current_segments)

            if not current_processed:
                continue

            next_date_idx = i + 1
            while next_date_idx < len(dates):
                next_segments = self.processor.load_segments_for_day(dates[next_date_idx])
                next_processed = self.segment_processor.process_segments(next_segments)

                if next_processed:
                    connector = self._create_connector_segment(
                        current_processed[-1], next_processed[0]
                    )
                    if connector:
                        connectors.append(connector)
                    break

                next_date_idx += 1

        return connectors

    def _create_connector_segment(self, end_segment: Any, start_segment: Any) -> Any:
        """Create a connector segment between two segments.

        Args:
            end_segment: Last segment of current day
            start_segment: First segment of next available day

        Returns:
            ProcessedSegment connecting the two, or None if not possible
        """
        from timeline_2_images.models import ProcessedSegment

        if not end_segment.simplified_waypoints or not start_segment.simplified_waypoints:
            return None

        end_point = end_segment.simplified_waypoints[-1]
        start_point = start_segment.simplified_waypoints[0]

        connector_waypoints = [end_point, start_point]

        from timeline_2_images.models import Segment, Bounds

        connector_seg = Segment(
            start_time=end_segment.segment.end_time,
            end_time=start_segment.segment.start_time,
            waypoints=connector_waypoints,
            segment_type="connector",
        )

        bounds = Bounds(
            min_latitude=min(end_point[0], start_point[0]),
            max_latitude=max(end_point[0], start_point[0]),
            min_longitude=min(end_point[1], start_point[1]),
            max_longitude=max(end_point[1], start_point[1]),
        )

        return ProcessedSegment(
            segment=connector_seg,
            simplified_waypoints=connector_waypoints,
            bounds=bounds,
            center=bounds.get_center(),
        )
