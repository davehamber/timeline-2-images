"""Tests for timeline_splitter module."""

import json
import tempfile
from pathlib import Path

import pytest

from daily_timeline_images.timeline_splitter import split_timeline_by_year, merge_timelines


@pytest.fixture
def sample_timeline_multi_year():
    """Create a sample Timeline JSON with data from multiple years."""
    data = {
        "semanticSegments": [
            {
                "startTime": "2023-01-15T10:00:00Z",
                "endTime": "2023-01-15T11:00:00Z",
                "timelinePath": [
                    {"point": "37.0°, -122.0°", "time": "2023-01-15T10:30:00Z"}
                ],
            },
            {
                "startTime": "2024-06-20T14:00:00Z",
                "endTime": "2024-06-20T15:00:00Z",
                "timelinePath": [
                    {"point": "37.1°, -122.1°", "time": "2024-06-20T14:30:00Z"}
                ],
            },
            {
                "startTime": "2024-12-25T08:00:00Z",
                "endTime": "2024-12-25T09:00:00Z",
                "timelinePath": [
                    {"point": "37.2°, -122.2°", "time": "2024-12-25T08:30:00Z"}
                ],
            },
        ],
        "rawSignals": [],
        "userLocationProfile": {},
    }
    return data


def test_split_timeline_creates_yearly_files(sample_timeline_multi_year):
    """Test that split_timeline_by_year creates separate files for each year."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save sample timeline
        timeline_file = Path(tmpdir) / "timeline.json"
        with open(timeline_file, "w") as f:
            json.dump(sample_timeline_multi_year, f)

        # Split into years
        output_dir = Path(tmpdir) / "yearly"
        year_to_path = split_timeline_by_year(str(timeline_file), str(output_dir))

        # Check that files were created
        assert len(year_to_path) == 2  # 2023 and 2024
        assert 2023 in year_to_path
        assert 2024 in year_to_path

        # Verify files exist
        assert Path(year_to_path[2023]).exists()
        assert Path(year_to_path[2024]).exists()


def test_split_timeline_segments_grouped_correctly(sample_timeline_multi_year):
    """Test that segments are grouped correctly by year."""
    with tempfile.TemporaryDirectory() as tmpdir:
        timeline_file = Path(tmpdir) / "timeline.json"
        with open(timeline_file, "w") as f:
            json.dump(sample_timeline_multi_year, f)

        output_dir = Path(tmpdir) / "yearly"
        year_to_path = split_timeline_by_year(str(timeline_file), str(output_dir))

        # Check 2023 file
        with open(year_to_path[2023]) as f:
            data_2023 = json.load(f)
        assert len(data_2023["semanticSegments"]) == 1

        # Check 2024 file
        with open(year_to_path[2024]) as f:
            data_2024 = json.load(f)
        assert len(data_2024["semanticSegments"]) == 2


def test_merge_timelines_combines_files(sample_timeline_multi_year):
    """Test that merge_timelines combines yearly files correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Split first
        timeline_file = Path(tmpdir) / "timeline.json"
        with open(timeline_file, "w") as f:
            json.dump(sample_timeline_multi_year, f)

        split_dir = Path(tmpdir) / "split"
        split_timeline_by_year(str(timeline_file), str(split_dir))

        # Now merge
        merged_file = Path(tmpdir) / "merged.json"
        merge_timelines(str(split_dir), str(merged_file))

        # Check merged file
        with open(merged_file) as f:
            merged_data = json.load(f)

        assert len(merged_data["semanticSegments"]) == 3
        assert merged_file.exists()
        assert merged_file.stat().st_size > 0
