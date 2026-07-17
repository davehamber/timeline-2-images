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

    def test_get_place_name_with_structured_address(self):
        """Test place name retrieval with structured address from Nominatim."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()

        mock_location = Mock()
        mock_location.raw = {
            "address": {
                "house_number": "123",
                "road": "Main Street",
                "city": "New York",
                "state": "New York",
                "country": "United States",
            }
        }

        with patch.object(renderer.geocoder, "reverse", return_value=mock_location):
            place_name = renderer._get_place_name(40.7128, -74.0060)
            assert place_name == "New York"

    def test_get_place_name_with_town_fallback(self):
        """Test place name fallback when city not available but town is."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()

        mock_location = Mock()
        mock_location.raw = {
            "address": {
                "road": "Main Street",
                "town": "Springfield",
                "state": "Illinois",
                "country": "United States",
            }
        }

        with patch.object(renderer.geocoder, "reverse", return_value=mock_location):
            place_name = renderer._get_place_name(39.7817, -89.6501)
            assert place_name == "Springfield"

    def test_get_place_name_with_village_fallback(self):
        """Test place name fallback when only village is available."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()

        mock_location = Mock()
        mock_location.raw = {
            "address": {
                "road": "Country Road",
                "village": "Smallville",
                "country": "United States",
            }
        }

        with patch.object(renderer.geocoder, "reverse", return_value=mock_location):
            place_name = renderer._get_place_name(38.5, -82.0)
            assert place_name == "Smallville"

    def test_get_place_name_string_fallback(self):
        """Test place name extraction from address string when raw not available."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()

        mock_location = Mock()
        mock_location.raw = None
        mock_location.address = "123 Main Street, Boston, Massachusetts, 02101, United States"

        with patch.object(renderer.geocoder, "reverse", return_value=mock_location):
            place_name = renderer._get_place_name(42.3601, -71.0589)
            assert place_name == "Boston"

    def test_get_place_name_string_fallback_postal_code_skip(self):
        """Test that postal codes are skipped in address string fallback."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()

        mock_location = Mock()
        mock_location.raw = None
        mock_location.address = "456 Oak Avenue, Portland, 97201, Oregon, United States"

        with patch.object(renderer.geocoder, "reverse", return_value=mock_location):
            place_name = renderer._get_place_name(45.5152, -122.6784)
            assert place_name == "Portland"

    def test_get_place_name_geocoder_timeout(self):
        """Test handling of Nominatim timeout."""
        from unittest.mock import patch
        from geopy.exc import GeocoderTimedOut

        renderer = MapRenderer()

        with patch.object(renderer.geocoder, "reverse", side_effect=GeocoderTimedOut()):
            place_name = renderer._get_place_name(40.7128, -74.0060)
            assert place_name == ""

    def test_get_place_name_geocoder_unavailable(self):
        """Test handling of Nominatim service unavailable."""
        from unittest.mock import patch
        from geopy.exc import GeocoderUnavailable

        renderer = MapRenderer()

        with patch.object(renderer.geocoder, "reverse", side_effect=GeocoderUnavailable()):
            place_name = renderer._get_place_name(40.7128, -74.0060)
            assert place_name == ""

    def test_get_place_name_generic_exception(self):
        """Test handling of generic exceptions."""
        from unittest.mock import patch

        renderer = MapRenderer()

        with patch.object(renderer.geocoder, "reverse", side_effect=Exception("Unknown error")):
            place_name = renderer._get_place_name(40.7128, -74.0060)
            assert place_name == ""

    def test_get_place_name_empty_response(self):
        """Test handling of None response from geocoder."""
        from unittest.mock import patch

        renderer = MapRenderer()

        with patch.object(renderer.geocoder, "reverse", return_value=None):
            place_name = renderer._get_place_name(40.7128, -74.0060)
            assert place_name == ""

    def test_get_location_label_same_start_and_end(self):
        """Test location label when start and end are the same place."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()
        segments = [
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 10, 0),
                    end_time=datetime(2024, 1, 1, 11, 0),
                    waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                ),
                simplified_waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                bounds=Bounds(40.7128, 40.7138, -74.0070, -74.0060),
                center=(40.7133, -74.0065),
            ),
        ]

        mock_location = Mock()
        mock_location.raw = {"address": {"city": "New York"}}

        with patch.object(renderer.geocoder, "reverse", return_value=mock_location):
            label = renderer._get_location_label(segments)
            assert label == "New York"

    def test_get_location_label_different_start_and_end(self):
        """Test location label with different start and end places."""
        from unittest.mock import Mock, patch

        renderer = MapRenderer()
        segments = [
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 10, 0),
                    end_time=datetime(2024, 1, 1, 14, 0),
                    waypoints=[(40.7128, -74.0060), (42.3601, -71.0589)],
                ),
                simplified_waypoints=[(40.7128, -74.0060), (42.3601, -71.0589)],
                bounds=Bounds(40.7128, 42.3601, -74.0060, -71.0589),
                center=(41.5365, -72.5325),
            ),
        ]

        def mock_reverse(coord_str, language="en", timeout=5):
            mock = Mock()
            if "40.7128" in coord_str:
                mock.raw = {"address": {"city": "New York"}}
            else:
                mock.raw = {"address": {"city": "Boston"}}
            return mock

        with patch.object(renderer.geocoder, "reverse", side_effect=mock_reverse):
            label = renderer._get_location_label(segments)
            assert label == "New York - Boston"

    def test_get_location_label_no_segments(self):
        """Test location label with no segments."""
        renderer = MapRenderer()
        label = renderer._get_location_label([])
        assert label == ""

    def test_get_location_label_failed_lookups(self):
        """Test location label when place name lookups fail."""
        from unittest.mock import patch
        from geopy.exc import GeocoderUnavailable

        renderer = MapRenderer()
        segments = [
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 10, 0),
                    end_time=datetime(2024, 1, 1, 11, 0),
                    waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                ),
                simplified_waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                bounds=Bounds(40.7128, 40.7138, -74.0070, -74.0060),
                center=(40.7133, -74.0065),
            ),
        ]

        with patch.object(renderer.geocoder, "reverse", side_effect=GeocoderUnavailable()):
            label = renderer._get_location_label(segments)
            assert label == ""

    def test_render_segments_with_place_names_disabled(self, tmp_path):
        """Test rendering with place names disabled via config."""
        config = RenderConfiguration(add_place_names=False)
        renderer = MapRenderer(config=config)
        segments = [
            ProcessedSegment(
                segment=Segment(
                    start_time=datetime(2024, 1, 1, 10, 0),
                    end_time=datetime(2024, 1, 1, 11, 0),
                    waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                ),
                simplified_waypoints=[(40.7128, -74.0060), (40.7138, -74.0070)],
                bounds=Bounds(40.7128, 40.7138, -74.0070, -74.0060),
                center=(40.7133, -74.0065),
            ),
        ]
        output_path = tmp_path / "2024-01-01.jpg"
        result = renderer.render_segments(segments, str(output_path))
        assert result.was_successful()
        # File should be created
        assert output_path.exists()
