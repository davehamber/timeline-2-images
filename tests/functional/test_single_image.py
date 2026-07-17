"""Functional tests for single-image feature."""

import json

import pytest

from timeline_2_images.app import TimelineApp
from timeline_2_images.config import RenderConfiguration


@pytest.fixture
def multi_day_timeline_json(tmp_path):
    """Create a multi-day Timeline.json for single-image testing."""
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
                    {"point": "40.7158,-74.0090"},
                    {"point": "40.7168,-74.0100"},
                    {"point": "40.7178,-74.0110"},
                ],
            },
            {
                "startTime": "2024-01-17T09:00:00.000Z",
                "endTime": "2024-01-17T10:00:00.000Z",
                "timelinePath": [
                    {"point": "51.5074,-0.1278"},
                    {"point": "51.5084,-0.1288"},
                    {"point": "51.5094,-0.1298"},
                ],
            },
        ],
    }
    json_path = tmp_path / "Timeline.json"
    with open(json_path, "w") as f:
        json.dump(timeline_data, f)
    return str(json_path)


class TestSingleImageFunctional:
    """Functional tests for single-image feature."""

    def test_single_image_basic(self, multi_day_timeline_json, tmp_path):
        """Test that single-image feature produces one combined image."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir)

        result = app.process_date_range_single_image(start_date="2024-01-15", end_date="2024-01-17")

        assert result.success
        assert result.point_count > 0
        assert "2024-01-15_to_2024-01-17" in result.date

    def test_single_image_output_filename(self, multi_day_timeline_json, tmp_path):
        """Test that output filename contains date range."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir)

        app.process_date_range_single_image(start_date="2024-01-15", end_date="2024-01-17")

        expected_filename = tmp_path / "output" / "2024-01-15_to_2024-01-17.jpg"
        assert expected_filename.exists()

    def test_single_image_combines_waypoints(self, multi_day_timeline_json, tmp_path):
        """Test that single image combines waypoints from all dates."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir)

        result = app.process_date_range_single_image(start_date="2024-01-15", end_date="2024-01-17")

        assert result.success
        assert result.point_count >= 9

    def test_single_image_with_days_parameter(self, multi_day_timeline_json, tmp_path):
        """Test that single-image works with days parameter."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir)

        result = app.process_date_range_single_image(days=5)

        assert result.success

    def test_single_image_with_no_place_names(self, multi_day_timeline_json, tmp_path):
        """Test that single-image works regardless of place-names setting."""
        output_dir = str(tmp_path / "output")
        config = RenderConfiguration(add_place_names=False)
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir, config=config)

        result = app.process_date_range_single_image(start_date="2024-01-15", end_date="2024-01-17")

        assert result.success

    def test_single_image_empty_date_range(self, multi_day_timeline_json, tmp_path):
        """Test that single-image handles empty date ranges gracefully."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir)

        result = app.process_date_range_single_image(start_date="2024-12-01", end_date="2024-12-31")

        assert not result.success

    def test_single_image_with_gaps(self, tmp_path):
        """Test that single-image handles gaps between days with data."""
        timeline_data = {
            "semanticSegments": [
                {
                    "startTime": "2024-01-15T10:00:00.000Z",
                    "endTime": "2024-01-15T11:00:00.000Z",
                    "timelinePath": [
                        {"point": "40.7128,-74.0060"},
                        {"point": "40.7138,-74.0070"},
                    ],
                },
                {
                    "startTime": "2024-01-17T14:00:00.000Z",
                    "endTime": "2024-01-17T15:00:00.000Z",
                    "timelinePath": [
                        {"point": "40.7158,-74.0090"},
                        {"point": "40.7168,-74.0100"},
                    ],
                },
            ],
        }
        json_path = tmp_path / "Timeline.json"
        with open(json_path, "w") as f:
            json.dump(timeline_data, f)

        output_dir = str(tmp_path / "output")
        app = TimelineApp(str(json_path), output_dir=output_dir)

        result = app.process_date_range_single_image(start_date="2024-01-15", end_date="2024-01-17")

        assert result.success

    def test_single_image_bounds_calculation(self, multi_day_timeline_json, tmp_path):
        """Test that bounds are correctly calculated for all combined waypoints."""
        output_dir = str(tmp_path / "output")
        app = TimelineApp(multi_day_timeline_json, output_dir=output_dir)

        result = app.process_date_range_single_image(start_date="2024-01-15", end_date="2024-01-17")

        assert result.success
        assert result.output_path.exists()
        assert result.output_path.stat().st_size > 0
