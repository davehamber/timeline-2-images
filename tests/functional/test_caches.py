"""Functional tests for segment and tile caching."""

import json
import tempfile
from pathlib import Path

import pytest

from timeline_2_images.app import TimelineApp
from timeline_2_images.config import RenderConfiguration
from timeline_2_images.sqlite_cache import (
    get_cache_stats,
    clear_cache,
)


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    """Override cache directory for testing."""
    cache_path = tmp_path / "cache"
    cache_path.mkdir()
    # Patch the cache location
    import timeline_2_images.sqlite_cache as sqlite_module

    def mock_get_cache_dir():
        return cache_path

    monkeypatch.setattr(sqlite_module, "_get_cache_dir", mock_get_cache_dir)
    yield cache_path


@pytest.fixture
def sample_timeline_json(tmp_path):
    """Create a sample Timeline.json for caching tests."""
    timeline_data = {
        "semanticSegments": [
            {
                "startTime": "2024-01-15T10:00:00.000Z",
                "endTime": "2024-01-15T11:00:00.000Z",
                "timelinePath": [
                    {"point": "40.7128,-74.0060"},
                    {"point": "40.7138,-74.0070"},
                    {"point": "40.7148,-74.0080"},
                ],
            },
            {
                "startTime": "2024-01-16T14:00:00.000Z",
                "endTime": "2024-01-16T15:00:00.000Z",
                "timelinePath": [
                    {"point": "40.7128,-74.0060"},
                    {"point": "40.7158,-74.0090"},
                    {"point": "40.7168,-74.0100"},
                ],
            },
            {
                "startTime": "2024-01-17T09:00:00.000Z",
                "endTime": "2024-01-17T10:00:00.000Z",
                "timelinePath": [
                    {"point": "51.5074,-0.1278"},
                    {"point": "51.5084,-0.1288"},
                ],
            },
        ],
    }
    json_path = tmp_path / "Timeline.json"
    with open(json_path, "w") as f:
        json.dump(timeline_data, f)
    return str(json_path)


class TestSegmentCacheFunctional:
    """Functional tests for segment caching."""

    def test_segment_cache_creation(self, tmp_path):
        """Test that segment cache is created during processing."""
        with tempfile.TemporaryDirectory() as cache_dir_tmp:
            import timeline_2_images.sqlite_cache as sqlite_module

            original_get_cache_dir = sqlite_module._get_cache_dir
            sqlite_module._get_cache_dir = lambda: Path(cache_dir_tmp)

            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    test_data = {
                        "semanticSegments": [
                            {
                                "startTime": "2024-01-15T10:00:00.000Z",
                                "endTime": "2024-01-15T11:00:00.000Z",
                                "timelinePath": [{"point": "40.7128,-74.0060"}],
                            },
                        ],
                    }
                    json.dump(test_data, f)
                    json_path = f.name

                output_dir = str(tmp_path / "output")
                app = TimelineApp(json_path, output_dir=output_dir)
                app.process_date("2024-01-15")

                cache_db = Path(cache_dir_tmp) / "segments.db"
                cache_hash = Path(cache_dir_tmp) / "segments.hash"

                assert cache_db.exists(), "Segment cache DB should be created"
                assert cache_hash.exists(), "Segment hash file should be created"

                Path(json_path).unlink()
            finally:
                sqlite_module._get_cache_dir = original_get_cache_dir

    def test_segment_cache_provides_stats(self, tmp_path):
        """Test that segment cache statistics are available."""
        with tempfile.TemporaryDirectory() as cache_dir_tmp:
            import timeline_2_images.sqlite_cache as sqlite_module

            original_get_cache_dir = sqlite_module._get_cache_dir
            sqlite_module._get_cache_dir = lambda: Path(cache_dir_tmp)

            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    test_data = {
                        "semanticSegments": [
                            {
                                "startTime": "2024-01-15T10:00:00.000Z",
                                "endTime": "2024-01-15T11:00:00.000Z",
                                "timelinePath": [{"point": "40.7128,-74.0060"}],
                            },
                        ],
                    }
                    json.dump(test_data, f)
                    json_path = f.name

                output_dir = str(tmp_path / "output")
                app = TimelineApp(json_path, output_dir=output_dir)
                app.process_date("2024-01-15")

                stats = get_cache_stats(json_path)
                assert stats["status"] == "cached"
                assert stats["segment_count"] > 0
                assert stats["date_count"] > 0

                Path(json_path).unlink()
            finally:
                sqlite_module._get_cache_dir = original_get_cache_dir

    def test_segment_cache_handles_multiple_dates(self, sample_timeline_json, cache_dir, tmp_path):
        """Test that cache correctly handles multiple dates."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)

        result1 = app.process_date("2024-01-15")
        result2 = app.process_date("2024-01-16")
        result3 = app.process_date("2024-01-17")

        assert result1.success
        assert result2.success
        assert result3.success

        stats = get_cache_stats(sample_timeline_json)
        assert stats["date_count"] >= 3
        assert stats["segment_count"] >= 3

    def test_segment_cache_clear(self, sample_timeline_json, cache_dir, tmp_path):
        """Test that cache can be cleared."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)

        app.process_date("2024-01-15")
        assert (cache_dir / "segments.db").exists()

        clear_cache(sample_timeline_json)
        assert not (cache_dir / "segments.db").exists()

    def test_segment_cache_with_date_range(self, sample_timeline_json, cache_dir, tmp_path):
        """Test that segment cache works with date range processing."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)

        results = app.process_date_range(start_date="2024-01-15", end_date="2024-01-17")

        assert len(results) == 3
        assert all(r.success for r in results)

        stats = get_cache_stats(sample_timeline_json)
        assert stats["segment_count"] == 3


class TestTileCacheFunctional:
    """Functional tests for tile caching."""

    def test_tile_cache_directory_created(self, sample_timeline_json, tmp_path):
        """Test that tile cache directory is created."""
        output_dir = str(tmp_path / "output")
        cache_dir = str(tmp_path / "tiles_cache")

        app = TimelineApp(sample_timeline_json, output_dir=output_dir, cache_dir=cache_dir)
        app.process_date("2024-01-15")

        assert Path(cache_dir).exists()

    def test_tile_cache_manager_tracks_stats(self, sample_timeline_json, tmp_path):
        """Test that tile cache manager provides statistics."""
        output_dir = str(tmp_path / "output")
        cache_dir = str(tmp_path / "tiles_cache")

        app = TimelineApp(sample_timeline_json, output_dir=output_dir, cache_dir=cache_dir)
        app.process_date("2024-01-15")

        cache_info = app.renderer.get_cache_info()
        assert "cache_dir" in cache_info
        assert cache_info["cache_dir"] == cache_dir

    def test_tile_cache_can_be_cleared(self, sample_timeline_json, tmp_path):
        """Test that tile cache can be cleared."""
        output_dir = str(tmp_path / "output")
        cache_dir = str(tmp_path / "tiles_cache")

        app = TimelineApp(sample_timeline_json, output_dir=output_dir, cache_dir=cache_dir)
        app.process_date("2024-01-15")

        app.renderer.clear_cache()
        cache_info = app.renderer.get_cache_info()
        assert cache_info["status"] == "no_cache"


class TestCombinedCacheFunctional:
    """Functional tests for segment and tile caches working together."""

    def test_full_pipeline_with_caching(self, sample_timeline_json, cache_dir, tmp_path):
        """Test complete pipeline with segment caching for multiple dates."""
        output_dir = str(tmp_path / "output")

        app = TimelineApp(sample_timeline_json, output_dir=output_dir)

        results = []
        for date in ["2024-01-15", "2024-01-16", "2024-01-17"]:
            result = app.process_date(date)
            results.append(result)

        assert all(r.success for r in results)
        assert len(results) == 3

    def test_cache_consistency_across_runs(self, sample_timeline_json, cache_dir, tmp_path):
        """Test that cache produces consistent results across runs."""
        output_dir = str(tmp_path / "output")

        app1 = TimelineApp(sample_timeline_json, output_dir=output_dir)
        result1 = app1.process_date("2024-01-15")

        app2 = TimelineApp(sample_timeline_json, output_dir=output_dir)
        result2 = app2.process_date("2024-01-15")

        assert result1.success == result2.success
        assert result1.point_count == result2.point_count
        assert result1.segment_count == result2.segment_count

    def test_cache_with_place_names_feature(self, sample_timeline_json, cache_dir, tmp_path):
        """Test that caching works with place names feature enabled."""
        output_dir = str(tmp_path / "output")
        config = RenderConfiguration(add_place_names=True)

        app = TimelineApp(sample_timeline_json, output_dir=output_dir, config=config)
        result = app.process_date("2024-01-15")

        assert result.success
        assert (cache_dir / "segments.db").exists()
