"""Tests for rendering classes."""

from datetime import datetime
from pathlib import Path

from timeline_2_images.rendering import MapRenderer, TileCacheManager
from timeline_2_images.config import RenderConfiguration
from timeline_2_images.models import Segment, ProcessedSegment, Bounds


class TestTileCacheManager:
    """Test TileCacheManager."""

    def test_initialization(self, tmp_path):
        """Test cache manager initialization."""
        cache_dir = str(tmp_path / "cache")
        manager = TileCacheManager(cache_dir)
        assert manager.cache_dir == Path(cache_dir)
        assert manager.cache_dir.exists()

    def test_get_cache_stats_no_cache(self, tmp_path):
        """Test cache stats when no cache exists."""
        cache_dir = str(tmp_path / "cache")
        manager = TileCacheManager(cache_dir)
        stats = manager.get_cache_stats()
        assert stats["status"] == "no_cache"

    def test_get_cache_size(self, tmp_path):
        """Test getting cache size."""
        cache_dir = str(tmp_path / "cache")
        manager = TileCacheManager(cache_dir)
        size = manager.get_cache_size()
        assert size == 0

    def test_get_info(self, tmp_path):
        """Test getting complete cache info."""
        cache_dir = str(tmp_path / "cache")
        manager = TileCacheManager(cache_dir)
        info = manager.get_info()
        assert "cache_dir" in info
        assert "cache_size_mb" in info
        assert "status" in info

    def test_clear(self, tmp_path):
        """Test clearing cache."""
        cache_dir = str(tmp_path / "cache")
        manager = TileCacheManager(cache_dir)
        manager.clear()


class TestMapRenderer:
    """Test MapRenderer."""

    def test_initialization(self):
        """Test renderer initialization."""
        renderer = MapRenderer()
        assert renderer.config is not None
        assert renderer.tile_cache is not None

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = RenderConfiguration(image_size=800)
        renderer = MapRenderer(config=config)
        assert renderer.config.image_size == 800

    def test_collect_waypoints(self):
        """Test collecting waypoints from segments."""
        renderer = MapRenderer()
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
        ]
        waypoints = renderer._collect_waypoints(segments)
        assert len(waypoints) == 2

    def test_collect_waypoints_empty(self):
        """Test collecting waypoints from empty segments."""
        renderer = MapRenderer()
        waypoints = renderer._collect_waypoints([])
        assert waypoints == []

    def test_calculate_bounds(self):
        """Test bounds calculation."""
        renderer = MapRenderer()
        waypoints = [
            (40.0, -74.0),
            (41.0, -73.0),
            (40.5, -73.5),
        ]
        bounds = renderer._calculate_bounds(waypoints)
        assert len(bounds) == 4
        minx, miny, maxx, maxy = bounds
        assert minx < maxx
        assert miny < maxy

    def test_apply_padding_and_minimum(self):
        """Test padding and minimum area enforcement."""
        renderer = MapRenderer()
        minx, miny, maxx, maxy = renderer._apply_padding_and_minimum(0, 0, 100, 100)
        assert minx < 0
        assert miny < 0
        assert maxx > 100
        assert maxy > 100

    def test_render_segments_no_segments(self, tmp_path):
        """Test rendering with no segments."""
        renderer = MapRenderer()
        output_path = tmp_path / "test.jpg"
        result = renderer.render_segments([], str(output_path))
        assert not result.was_successful()
        assert result.success is False

    def test_render_segments_valid(self, tmp_path):
        """Test rendering valid segments."""
        renderer = MapRenderer()
        segments = [
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 10, 0),
                    end_time=datetime(2024, 1, 1, 11, 0),
                    waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                ),
                simplified_waypoints=[
                    (40.7128, -74.0060),
                    (40.7138, -74.0070),
                ],
                bounds=Bounds(40.7128, 40.7138, -74.0070, -74.0060),
                center=(40.7133, -74.0065),
            ),
        ]
        output_path = tmp_path / "2024-01-01.jpg"
        result = renderer.render_segments(segments, str(output_path))
        assert result.date == "2024-01-01"
        assert result.segment_count == 1
        assert result.point_count == 2
        assert result.render_time > 0

    def test_clear_cache(self, tmp_path):
        """Test clearing tile cache."""
        cache_dir = str(tmp_path / "cache")
        renderer = MapRenderer(tile_cache_dir=cache_dir)
        renderer.clear_cache()

    def test_get_cache_info(self, tmp_path):
        """Test getting cache information."""
        cache_dir = str(tmp_path / "cache")
        renderer = MapRenderer(tile_cache_dir=cache_dir)
        info = renderer.get_cache_info()
        assert isinstance(info, dict)
        assert "cache_size_mb" in info
