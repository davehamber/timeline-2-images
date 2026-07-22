"""Integration tests for the complete OOP pipeline."""

import pytest
from pathlib import Path
import json

from timeline_2_images.app import TimelineApp
from timeline_2_images.config import RenderConfiguration
from timeline_2_images.models import RenderResult


@pytest.fixture
def sample_timeline_json(tmp_path):
    """Create a sample Timeline.json for testing."""
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
                ],
            },
        ],
    }
    json_path = tmp_path / "Timeline.json"
    with open(json_path, "w") as f:
        json.dump(timeline_data, f)
    return str(json_path)


class TestTimelineApp:
    """Test TimelineApp orchestrator."""

    def test_initialization(self, sample_timeline_json, tmp_path):
        """Test app initialization."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        assert app.json_path == sample_timeline_json
        assert app.output_dir == Path(output_dir)
        assert app.processor is not None
        assert app.renderer is not None

    def test_initialization_with_config(self, sample_timeline_json, tmp_path):
        """Test app initialization with custom config."""
        output_dir = str(tmp_path / "output")
        config = RenderConfiguration(image_width=800, image_height=800)
        app = TimelineApp(sample_timeline_json, output_dir=output_dir, config=config)
        assert app.config.image_width == 800
        assert app.config.image_height == 800

    def test_get_available_dates(self, sample_timeline_json, tmp_path):
        """Test getting available dates."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        dates = app.get_available_dates()
        assert isinstance(dates, list)

    def test_process_date_no_segments(self, tmp_path):
        """Test processing date with no segments."""
        empty_timeline = {
            "semanticSegments": [],
        }
        json_path = tmp_path / "Timeline.json"
        with open(json_path, "w") as f:
            json.dump(empty_timeline, f)

        output_dir = str(tmp_path / "output")
        app = TimelineApp(str(json_path), output_dir=output_dir)
        result = app.process_date("2024-01-15")

        assert isinstance(result, RenderResult)
        assert result.success is False

    def test_process_date_valid(self, sample_timeline_json, tmp_path):
        """Test processing a valid date."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        result = app.process_date("2024-01-15")

        assert isinstance(result, RenderResult)
        assert result.date == "2024-01-15"
        assert result.render_time >= 0

    def test_process_date_range(self, sample_timeline_json, tmp_path):
        """Test processing a date range."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        results = app.process_date_range(
            start_date="2024-01-15",
            end_date="2024-01-16",
        )

        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, RenderResult)

    def test_process_date_range_with_days(self, sample_timeline_json, tmp_path):
        """Test processing date range with days parameter."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        results = app.process_date_range(days=7)

        assert isinstance(results, list)

    def test_get_statistics(self, sample_timeline_json, tmp_path):
        """Test getting app statistics."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        stats = app.get_statistics()

        assert isinstance(stats, dict)
        assert "json_path" in stats
        assert "output_dir" in stats
        assert "image_width" in stats
        assert "image_height" in stats
        assert "tile_cache" in stats

    def test_clear_caches(self, sample_timeline_json, tmp_path):
        """Test clearing caches."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)
        app.clear_caches()

    def test_output_directory_created(self, sample_timeline_json, tmp_path):
        """Test that output directory is created."""
        output_dir = str(tmp_path / "nonexistent" / "output")
        TimelineApp(sample_timeline_json, output_dir=output_dir)
        assert Path(output_dir).exists()


class TestOOPPipeline:
    """Test the complete OOP pipeline end-to-end."""

    def test_full_pipeline(self, sample_timeline_json, tmp_path):
        """Test the full processing pipeline."""
        output_dir = str(tmp_path / "output")
        config = RenderConfiguration(image_width=500)

        app = TimelineApp(sample_timeline_json, output_dir=output_dir, config=config)

        dates = app.get_available_dates()
        assert len(dates) > 0

        results = app.process_date_range(days=7)
        assert len(results) > 0

        for result in results:
            assert isinstance(result, RenderResult)
            assert result.date in dates

    def test_multiple_dates_processing(self, sample_timeline_json, tmp_path):
        """Test processing multiple dates."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(sample_timeline_json, output_dir=output_dir)

        date1_result = app.process_date("2024-01-15")
        date2_result = app.process_date("2024-01-16")

        assert isinstance(date1_result, RenderResult)
        assert isinstance(date2_result, RenderResult)
        assert date1_result.date != date2_result.date

    def test_error_handling(self, tmp_path):
        """Test error handling with invalid JSON."""
        invalid_json = tmp_path / "invalid.json"
        with open(invalid_json, "w") as f:
            f.write("invalid json")

        output_dir = str(tmp_path / "output")
        app = TimelineApp(str(invalid_json), output_dir=output_dir, validate=False)

        result = app.process_date("2024-01-15")
        assert result.success is False
