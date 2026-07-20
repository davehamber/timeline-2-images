"""Builds connector segments between days in multi-day renders."""

from typing import Any

from timeline_2_images.models import Segment, ProcessedSegment, Bounds
from timeline_2_images.processors import TimelineProcessor, SegmentProcessor


class DayConnectorBuilder:
    """Creates connector segments linking dates in combined image rendering."""

    def __init__(self, processor: TimelineProcessor, segment_processor: SegmentProcessor):
        """Initialize connector builder with processors.

        Args:
            processor: TimelineProcessor for loading segments
            segment_processor: SegmentProcessor for processing segments
        """
        self.processor = processor
        self.segment_processor = segment_processor

    def build_segments_with_connectors(self, dates: list[str]) -> list[Any]:
        """Build all segments across date range with day connectors.

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

        return self._add_day_connectors(all_segments, dates) if all_segments else []

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

        connectors = self._find_day_connectors(dates)
        if not connectors:
            return segments

        return self._build_connected_segments(dates, connectors)

    def _build_connected_segments(self, dates: list[str], connectors: list[Any]) -> list[Any]:
        """Build segments with connectors inserted between days."""
        result = []
        connector_idx = 0

        for day_idx, date in enumerate(dates):
            day_segments = self.processor.load_segments_for_day(date)
            day_processed = self.segment_processor.process_segments(day_segments)
            result.extend(day_processed)

            if connector_idx < len(connectors) and day_idx < len(dates) - 1:
                result.append(connectors[connector_idx])
                connector_idx += 1

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
            current_processed = self._get_processed_segments_for_date(dates[i])
            if not current_processed:
                continue

            connector = self._find_connector_for_current_day(dates, i, current_processed)
            if connector:
                connectors.append(connector)

        return connectors

    def _get_processed_segments_for_date(self, date: str) -> list[Any]:
        """Load and process segments for a single date."""
        segments = self.processor.load_segments_for_day(date)
        return self.segment_processor.process_segments(segments)

    def _find_connector_for_current_day(
        self, dates: list[str], current_idx: int, current_processed: list[Any]
    ) -> Any:
        """Find next day with segments and create connector to it."""
        next_date_idx = current_idx + 1
        while next_date_idx < len(dates):
            next_processed = self._get_processed_segments_for_date(dates[next_date_idx])
            if next_processed:
                return self._create_connector_segment(current_processed[-1], next_processed[0])
            next_date_idx += 1
        return None

    @staticmethod
    def _create_connector_segment(end_segment: Any, start_segment: Any) -> Any:
        """Create a connector segment between two segments.

        Args:
            end_segment: Last segment of current day
            start_segment: First segment of next available day

        Returns:
            ProcessedSegment connecting the two, or None if not possible
        """
        if not end_segment.simplified_waypoints or not start_segment.simplified_waypoints:
            return None

        end_point = end_segment.simplified_waypoints[-1]
        start_point = start_segment.simplified_waypoints[0]

        connector_waypoints = [end_point, start_point]

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
