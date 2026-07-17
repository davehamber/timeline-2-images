"""Tests for processor classes."""

import pytest
from datetime import datetime

from timeline_2_images.processors import TimelineProcessor, SegmentProcessor
from timeline_2_images.models import Segment, ProcessedSegment, Bounds


class TestSegmentProcessor:
    """Test SegmentProcessor."""

    def test_simplify_waypoints(self):
        """Test waypoint simplification."""
        processor = SegmentProcessor()
        waypoints = [
            (40.7128, -74.0060),
            (40.7129, -74.0061),
            (40.7130, -74.0062),
            (40.7140, -74.0070),
        ]
        simplified = processor.simplify_waypoints(waypoints)
        assert len(simplified) <= len(waypoints)

    def test_extract_waypoints_empty(self):
        """Test extracting waypoints from empty path."""
        processor = SegmentProcessor()
        result = processor.extract_waypoints([])
        assert result == []

    def test_extract_waypoints_valid(self):
        """Test extracting valid waypoints."""
        processor = SegmentProcessor()
        path = [
            {"point": "40.7128,-74.0060"},
            {"point": "40.7129,-74.0061"},
        ]
        result = processor.extract_waypoints(path)
        assert len(result) == 2
        assert result[0][0] == pytest.approx(40.7128, rel=0.001)

    def test_extract_waypoints_invalid_format(self):
        """Test extracting waypoints with invalid format."""
        processor = SegmentProcessor()
        path = [
            {"point": "invalid"},
            {"point": "40.7128,-74.0060"},
            {"no_point": "40.7129,-74.0061"},
        ]
        result = processor.extract_waypoints(path)
        assert len(result) == 1

    def test_calculate_bounds(self):
        """Test bounds calculation."""
        processor = SegmentProcessor()
        waypoints = [
            (40.0, -74.0),
            (41.0, -73.0),
            (40.5, -73.5),
        ]
        bounds = processor.calculate_bounds(waypoints)
        assert bounds is not None
        assert bounds.min_latitude == 40.0
        assert bounds.max_latitude == 41.0
        assert bounds.min_longitude == -74.0
        assert bounds.max_longitude == -73.0

    def test_calculate_bounds_empty(self):
        """Test bounds with no waypoints."""
        processor = SegmentProcessor()
        result = processor.calculate_bounds([])
        assert result is None

    def test_process_segment_valid(self):
        """Test processing a valid segment."""
        processor = SegmentProcessor()
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[(40.0, -74.0), (41.0, -73.0), (40.5, -73.5)],
        )
        result = processor.process_segment(segment)
        assert result is not None
        assert isinstance(result, ProcessedSegment)
        assert result.bounds.min_latitude == 40.0

    def test_process_segment_too_few_waypoints(self):
        """Test processing segment with too few waypoints."""
        processor = SegmentProcessor(min_waypoint_count=3)
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[(40.0, -74.0)],
        )
        result = processor.process_segment(segment)
        assert result is None

    def test_process_segments_multiple(self):
        """Test processing multiple segments."""
        processor = SegmentProcessor()
        segments = [
            Segment(
                start_time=datetime(2024, 1, 1, 10, 0),
                end_time=datetime(2024, 1, 1, 11, 0),
                waypoints=[(40.0, -74.0), (41.0, -73.0)],
            ),
            Segment(
                start_time=datetime(2024, 1, 1, 12, 0),
                end_time=datetime(2024, 1, 1, 13, 0),
                waypoints=[(40.5, -73.5), (40.6, -73.4)],
            ),
        ]
        results = processor.process_segments(segments)
        assert len(results) == 2

    def test_filter_by_waypoint_count(self):
        """Test filtering segments by waypoint count."""
        processor = SegmentProcessor()
        segments = [
            Segment(
                start_time=datetime(2024, 1, 1, 10, 0),
                end_time=datetime(2024, 1, 1, 11, 0),
                waypoints=[(40.0, -74.0)],
            ),
            Segment(
                start_time=datetime(2024, 1, 1, 12, 0),
                end_time=datetime(2024, 1, 1, 13, 0),
                waypoints=[(40.5, -73.5), (40.6, -73.4)],
            ),
        ]
        filtered = processor.filter_by_waypoint_count(segments, min_count=2)
        assert len(filtered) == 1

    def test_merge_segment_waypoints(self):
        """Test merging waypoints from processed segments."""
        processor = SegmentProcessor()
        segments = [
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 10, 0),
                    end_time=datetime(2024, 1, 1, 11, 0),
                    waypoints=[(40.0, -74.0), (41.0, -73.0)],
                ),
                simplified_waypoints=[(40.0, -74.0), (41.0, -73.0)],
                bounds=Bounds(40.0, 41.0, -74.0, -73.0),
                center=(40.5, -73.5),
            ),
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 12, 0),
                    end_time=datetime(2024, 1, 1, 13, 0),
                    waypoints=[(40.5, -73.5), (40.6, -73.4)],
                ),
                simplified_waypoints=[(40.5, -73.5), (40.6, -73.4)],
                bounds=Bounds(40.5, 40.6, -73.5, -73.4),
                center=(40.55, -73.45),
            ),
        ]
        merged = processor.merge_segment_waypoints(segments)
        assert len(merged) == 4


class TestTimelineProcessor:
    """Test TimelineProcessor."""

    def test_initialization(self, tmp_path):
        """Test processor initialization."""
        json_path = str(tmp_path / "test.json")
        processor = TimelineProcessor(json_path)
        assert processor.json_path == json_path

    def test_clear_cache(self, tmp_path):
        """Test clearing cache."""
        json_path = str(tmp_path / "test.json")
        processor = TimelineProcessor(json_path)
        processor.clear_cache()

    def test_get_cache_source(self, tmp_path):
        """Test getting cache source."""
        json_path = str(tmp_path / "test.json")
        processor = TimelineProcessor(json_path)
        source = processor.get_cache_source()
        assert isinstance(source, str)
