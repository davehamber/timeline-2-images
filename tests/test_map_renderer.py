"""Tests for map_renderer module."""

import tempfile
from pathlib import Path

import pytest

from daily_timeline_images.map_renderer import simplify_waypoints, render_segments


def test_simplify_waypoints():
    """Test waypoint simplification using RDP algorithm."""
    # Create a noisy path: straight line from (37.0, -122.0) to (37.1, -122.1)
    # with GPS jitter added
    waypoints = [
        (37.0, -122.0),
        (37.01, -122.01),
        (37.008, -122.012),  # Jitter
        (37.02, -122.02),
        (37.018, -122.022),  # Jitter
        (37.03, -122.03),
        (37.04, -122.04),
        (37.1, -122.1),
    ]

    simplified = simplify_waypoints(waypoints, tolerance_meters=20)

    # Should have fewer points than original
    assert len(simplified) < len(waypoints)
    # But should still start and end at the same places
    assert simplified[0] == waypoints[0]
    assert simplified[-1] == waypoints[-1]


def test_simplify_waypoints_short_path():
    """Test simplification with very short path (< 3 points)."""
    waypoints = [(37.0, -122.0), (37.01, -122.01)]
    simplified = simplify_waypoints(waypoints, tolerance_meters=20)
    # Should return original if too short
    assert simplified == waypoints


def test_render_segments():
    """Test rendering from semantic segments."""
    segments = [
        {
            "startTime": "2021-07-01T10:00:00Z",
            "waypoints": [
                (37.0, -122.0),
                (37.01, -122.01),
                (37.02, -122.02),
            ],
        },
        {
            "startTime": "2021-07-01T14:00:00Z",
            "waypoints": [
                (37.05, -122.05),
                (37.06, -122.06),
            ],
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "segments.jpg"
        render_segments(segments, str(output_file), image_size=500, dpi=50)
        assert output_file.exists()
        assert output_file.stat().st_size > 0


def test_render_segments_empty():
    """Test that render_segments raises error with no segments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "empty.jpg"
        with pytest.raises(ValueError, match="No segments provided"):
            render_segments([], str(output_file))


def test_render_segments_no_waypoints():
    """Test that render_segments raises error when segments have no waypoints."""
    segments = [{"startTime": "2021-07-01T10:00:00Z", "waypoints": []}]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "no_waypoints.jpg"
        with pytest.raises(ValueError, match="No waypoints found"):
            render_segments(segments, str(output_file))
