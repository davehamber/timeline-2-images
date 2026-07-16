"""Tests for timeline_parser module."""

import json
import tempfile
from pathlib import Path

import pytest
import pandas as pd

from daily_timeline_images.timeline_parser import (
    load_points_for_day,
    get_last_n_days_with_data,
    get_date_range,
)


@pytest.fixture
def sample_timeline_flat():
    """Create a sample Timeline JSON with flat locations structure."""
    data = {
        "locations": [
            {
                "timestampMs": 1625097600000,  # 2021-07-01 00:00:00 UTC (as int)
                "latitudeE7": 370000000,  # 37.0
                "longitudeE7": -1220000000,  # -122.0
            },
            {
                "timestampMs": 1625184000000,  # 2021-07-02 00:00:00 UTC
                "latitudeE7": 370100000,
                "longitudeE7": -1220100000,
            },
            {
                "timestampMs": 1625270400000,  # 2021-07-03 00:00:00 UTC
                "latitudeE7": 370200000,
                "longitudeE7": -1220200000,
            },
        ]
    }
    return data


def test_load_points_for_day_flat_structure(sample_timeline_flat):
    """Test loading points from flat locations structure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        df = load_points_for_day(temp_path, "2021-07-01")
        assert len(df) == 1
        assert df.iloc[0]["lat"] == pytest.approx(37.0, abs=0.0001)
        assert df.iloc[0]["lon"] == pytest.approx(-122.0, abs=0.0001)
    finally:
        Path(temp_path).unlink()


def test_load_points_for_day_no_data():
    """Test that ValueError is raised when no points found for date."""
    data = {"locations": []}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            load_points_for_day(temp_path, "2021-07-01")
    finally:
        Path(temp_path).unlink()


def test_load_points_returns_dataframe(sample_timeline_flat):
    """Test that returned value is a DataFrame with correct columns."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        df = load_points_for_day(temp_path, "2021-07-01")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["timestamp", "lat", "lon"]
        assert len(df) > 0
    finally:
        Path(temp_path).unlink()


def test_get_last_n_days_with_data(sample_timeline_flat):
    """Test finding last N days with data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        dates = get_last_n_days_with_data(temp_path, days=2)
        assert len(dates) == 2
        assert dates == ["2021-07-02", "2021-07-03"]
    finally:
        Path(temp_path).unlink()


def test_load_segments_for_day():
    """Test loading semantic segments for a specific date."""
    data = {
        "semanticSegments": [
            {
                "startTime": "2021-07-01T10:00:00Z",
                "endTime": "2021-07-01T11:00:00Z",
                "timelinePath": [
                    {"point": "37.0°, -122.0°", "time": "2021-07-01T10:15:00Z"},
                    {"point": "37.01°, -122.01°", "time": "2021-07-01T10:30:00Z"},
                ],
            },
            {
                "startTime": "2021-07-02T14:00:00Z",
                "endTime": "2021-07-02T15:00:00Z",
                "timelinePath": [
                    {"point": "37.1°, -122.1°", "time": "2021-07-02T14:30:00Z"},
                ],
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        from daily_timeline_images.timeline_parser import load_segments_for_day

        segments = load_segments_for_day(temp_path, "2021-07-01")
        assert len(segments) == 1
        assert len(segments[0]["waypoints"]) == 2
        assert segments[0]["waypoints"][0] == (37.0, -122.0)
    finally:
        Path(temp_path).unlink()


def test_get_date_range_days_only(sample_timeline_flat):
    """Test get_date_range with days parameter only."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        dates = get_date_range(temp_path, days=2)
        assert len(dates) == 2
        assert dates == ["2021-07-02", "2021-07-03"]
    finally:
        Path(temp_path).unlink()


def test_get_date_range_start_and_end(sample_timeline_flat):
    """Test get_date_range with both start and end dates."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        dates = get_date_range(temp_path, start_date="2021-07-01", end_date="2021-07-02")
        assert len(dates) == 2
        assert dates == ["2021-07-01", "2021-07-02"]
    finally:
        Path(temp_path).unlink()


def test_get_date_range_start_with_days(sample_timeline_flat):
    """Test get_date_range with start date and days."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        dates = get_date_range(temp_path, start_date="2021-07-01", days=2)
        assert len(dates) == 2
        assert dates == ["2021-07-01", "2021-07-02"]
    finally:
        Path(temp_path).unlink()


def test_get_date_range_end_with_days(sample_timeline_flat):
    """Test get_date_range with end date and days."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_timeline_flat, f)
        temp_path = f.name

    try:
        dates = get_date_range(temp_path, end_date="2021-07-03", days=2)
        assert len(dates) == 2
        assert dates == ["2021-07-02", "2021-07-03"]
    finally:
        Path(temp_path).unlink()
