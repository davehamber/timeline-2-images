"""Tests for data models."""

import pytest
from datetime import datetime

from timeline_2_images.models import Segment, ProcessedSegment, Bounds, RenderResult
from pathlib import Path


class TestBounds:
    """Test Bounds model."""

    def test_bounds_creation(self):
        """Test creating bounds."""
        bounds = Bounds(
            min_latitude=40.0,
            max_latitude=41.0,
            min_longitude=-74.0,
            max_longitude=-73.0,
        )
        assert bounds.min_latitude == 40.0
        assert bounds.max_latitude == 41.0

    def test_get_center(self):
        """Test getting center point."""
        bounds = Bounds(
            min_latitude=40.0,
            max_latitude=42.0,
            min_longitude=-74.0,
            max_longitude=-72.0,
        )
        center_lat, center_lon = bounds.get_center()
        assert center_lat == 41.0
        assert center_lon == -73.0

    def test_expand(self):
        """Test expanding bounds."""
        bounds = Bounds(
            min_latitude=40.0,
            max_latitude=41.0,
            min_longitude=-74.0,
            max_longitude=-73.0,
        )
        expanded = bounds.expand(1.0)
        assert expanded.min_latitude == 39.0
        assert expanded.max_latitude == 42.0
        assert expanded.min_longitude == -75.0
        assert expanded.max_longitude == -72.0

    def test_get_area_degrees_squared(self):
        """Test calculating area."""
        bounds = Bounds(
            min_latitude=0.0,
            max_latitude=2.0,
            min_longitude=0.0,
            max_longitude=3.0,
        )
        assert bounds.get_area_degrees_squared() == 6.0


class TestSegment:
    """Test Segment model."""

    def test_segment_creation(self):
        """Test creating segment."""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 11, 0)
        waypoints = [(40.7128, -74.0060), (40.7138, -74.0070)]

        segment = Segment(
            start_time=start,
            end_time=end,
            waypoints=waypoints,
        )

        assert segment.start_time == start
        assert segment.end_time == end
        assert len(segment.waypoints) == 2

    def test_get_duration(self):
        """Test getting segment duration."""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 11, 0)
        segment = Segment(
            start_time=start,
            end_time=end,
            waypoints=[(40.0, -74.0)],
        )
        duration = segment.get_duration()
        assert duration.total_seconds() == 3600

    def test_get_bounds(self):
        """Test getting segment bounds."""
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[
                (40.0, -74.0),
                (41.0, -73.0),
                (40.5, -73.5),
            ],
        )
        bounds = segment.get_bounds()
        assert bounds is not None
        assert bounds.min_latitude == 40.0
        assert bounds.max_latitude == 41.0
        assert bounds.min_longitude == -74.0
        assert bounds.max_longitude == -73.0

    def test_get_bounds_empty_waypoints(self):
        """Test getting bounds with no waypoints."""
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[],
        )
        assert segment.get_bounds() is None

    def test_get_waypoint_count(self):
        """Test getting waypoint count."""
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[(40.0, -74.0), (41.0, -73.0)],
        )
        assert segment.get_waypoint_count() == 2


class TestProcessedSegment:
    """Test ProcessedSegment model."""

    def test_from_segment(self):
        """Test creating ProcessedSegment from Segment."""
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[(40.0, -74.0), (41.0, -73.0)],
        )
        simplified = [(40.5, -73.5)]

        processed = ProcessedSegment.from_segment(segment, simplified)

        assert processed.segment == segment
        assert processed.simplified_waypoints == simplified
        assert processed.center == (40.5, -73.5)

    def test_from_segment_empty_waypoints(self):
        """Test ProcessedSegment with empty waypoints raises error."""
        segment = Segment(
            start_time=datetime(2024, 1, 1, 10, 0),
            end_time=datetime(2024, 1, 1, 11, 0),
            waypoints=[],
        )
        with pytest.raises(ValueError, match="Cannot process segment without waypoints"):
            ProcessedSegment.from_segment(segment, [])


class TestRenderResult:
    """Test RenderResult model."""

    def test_render_result_creation(self):
        """Test creating render result."""
        output_path = Path("/tmp/test.jpg")
        result = RenderResult(
            date="2024-01-01",
            output_path=output_path,
            segment_count=5,
            point_count=100,
            render_time=2.5,
        )
        assert result.date == "2024-01-01"
        assert result.segment_count == 5

    def test_was_successful(self):
        """Test success check."""
        result = RenderResult(
            date="2024-01-01",
            output_path=Path("/tmp/nonexistent.jpg"),
            segment_count=5,
            point_count=100,
            render_time=2.5,
            success=True,
        )
        assert not result.was_successful()

    def test_get_summary(self):
        """Test summary generation."""
        result = RenderResult(
            date="2024-01-01",
            output_path=Path("/tmp/test.jpg"),
            segment_count=5,
            point_count=100,
            render_time=2.5,
            success=False,
            error_message="Test error",
        )
        summary = result.get_summary()
        assert "2024-01-01" in summary
        assert "FAILED" in summary
        assert "Test error" in summary
