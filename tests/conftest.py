"""Pytest configuration and shared fixtures."""

import json
import pytest


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


@pytest.fixture
def ios_timeline_json(tmp_path):
    """Create an iOS format Timeline.json (bare array) for testing."""
    # iOS exports as bare array (not wrapped in object)
    timeline_data = [
        {
            "startTime": "2026-01-15T10:00:00.000Z",
            "endTime": "2026-01-15T11:00:00.000Z",
            "activityType": "IN_VEHICLE",
            "timelinePath": [
                {"point": "geo:52.499323,13.403603"},
                {"point": "geo:52.502145,13.410234"},
                {"point": "geo:52.506789,13.418912"},
                {"point": "geo:52.510234,13.425678"},
                {"point": "geo:52.515678,13.435234"},
            ],
        },
        {
            "startTime": "2026-01-15T12:00:00.000Z",
            "endTime": "2026-01-15T13:00:00.000Z",
            "activityType": "WALKING",
            "timelinePath": [
                {"point": "geo:52.520123,13.445612"},
                {"point": "geo:52.525456,13.455789"},
            ],
        },
        {
            "startTime": "2026-01-16T10:00:00.000Z",
            "endTime": "2026-01-16T11:00:00.000Z",
            "activityType": "IN_VEHICLE",
            "timelinePath": [
                {"point": "geo:40.7128,-74.0060"},
                {"point": "geo:40.7138,-74.0070"},
            ],
        },
        {
            "startTime": "2026-01-17T10:00:00.000Z",
            "endTime": "2026-01-17T11:00:00.000Z",
            "activityType": "WALKING",
            "timelinePath": [
                {"point": "geo:40.7148,-74.0080"},
            ],
        },
        {
            "startTime": "2026-01-18T10:00:00.000Z",
            "endTime": "2026-01-18T11:00:00.000Z",
            "activityType": "IN_VEHICLE",
            "timelinePath": [
                {"point": "geo:40.7158,-74.0090"},
            ],
        },
    ]
    json_path = tmp_path / "ios_Timeline.json"
    with open(json_path, "w") as f:
        json.dump(timeline_data, f)
    return str(json_path)


@pytest.fixture
def android_timeline_json(tmp_path):
    """Create an Android format Timeline.json for testing."""
    # Android exports as object with semanticSegments key
    timeline_data = {
        "semanticSegments": [
            {
                "startTime": "2026-01-15T10:00:00.000Z",
                "endTime": "2026-01-15T11:00:00.000Z",
                "activityType": "IN_VEHICLE",
                "timelinePath": [
                    {"point": "52.499323,13.403603"},
                    {"point": "52.502145,13.410234"},
                    {"point": "52.506789,13.418912"},
                    {"point": "52.510234,13.425678"},
                    {"point": "52.515678,13.435234"},
                ],
            },
            {
                "startTime": "2026-01-15T12:00:00.000Z",
                "endTime": "2026-01-15T13:00:00.000Z",
                "activityType": "WALKING",
                "timelinePath": [
                    {"point": "52.520123,13.445612"},
                    {"point": "52.525456,13.455789"},
                ],
            },
        ],
    }
    json_path = tmp_path / "android_Timeline.json"
    with open(json_path, "w") as f:
        json.dump(timeline_data, f)
    return str(json_path)
