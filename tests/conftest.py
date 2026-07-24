"""Shared fixtures for tests."""

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
                    {
                        "point": {"latitudeE7": 400000000, "longitudeE7": -740000000},
                        "duration": {"seconds": "3600"},
                    }
                ],
            }
        ]
    }
    json_file = tmp_path / "Timeline.json"
    with open(json_file, "w") as f:
        json.dump(timeline_data, f)
    return str(json_file)


@pytest.fixture
def android_timeline_json(tmp_path):
    """Android Timeline.json with string coordinates (no geo: prefix)."""
    timeline_data = {
        "semanticSegments": [
            {
                "startTime": "2026-01-15T08:30:00Z",
                "endTime": "2026-01-15T09:45:00Z",
                "activityType": "IN_VEHICLE",
                "timelinePath": [
                    {"point": "52.499323,13.403603"},
                    {"point": "52.502145,13.410234"},
                    {"point": "52.506789,13.418912"},
                    {"point": "52.510234,13.423456"},
                    {"point": "52.515241,13.428765"},
                ],
            },
            {
                "startTime": "2026-01-15T09:45:00Z",
                "endTime": "2026-01-15T10:30:00Z",
                "activityType": "WALKING",
                "timelinePath": [
                    {"point": "52.515241,13.428765"},
                    {"point": "52.515678,13.429234"},
                    {"point": "52.516123,13.430456"},
                ],
            },
            {
                "startTime": "2026-01-15T10:30:00Z",
                "endTime": "2026-01-15T14:00:00Z",
                "placeVisit": {
                    "location": {
                        "placeId": "place123",
                        "address": "Café Downtown",
                        "latitudeE7": 525161230,
                        "longitudeE7": 134304560,
                    },
                    "duration": {
                        "startTimestampMs": "1737957000000",
                        "endTimestampMs": "1737968400000",
                    },
                },
            },
        ]
    }
    json_file = tmp_path / "Timeline.json"
    with open(json_file, "w") as f:
        json.dump(timeline_data, f)
    return str(json_file)


@pytest.fixture
def ios_timeline_json(tmp_path):
    """iOS location-history.json with bare array root and geo: prefixed coordinates.

    Bare array (no semanticSegments wrapper) with same flat segment structure as Android,
    but coordinates use geo: URI prefix format (RFC 5870).
    """
    timeline_data = [
        {
            "startTime": "2026-01-15T08:30:00Z",
            "endTime": "2026-01-15T09:45:00Z",
            "activityType": "IN_VEHICLE",
            "timelinePath": [
                {"point": "geo:52.499323,13.403603"},
                {"point": "geo:52.502145,13.410234"},
                {"point": "geo:52.506789,13.418912"},
                {"point": "geo:52.510234,13.423456"},
                {"point": "geo:52.515241,13.428765"},
            ],
        },
        {
            "startTime": "2026-01-15T09:45:00Z",
            "endTime": "2026-01-15T10:30:00Z",
            "activityType": "WALKING",
            "timelinePath": [
                {"point": "geo:52.515241,13.428765"},
                {"point": "geo:52.515678,13.429234"},
                {"point": "geo:52.516123,13.430456"},
            ],
        },
        {
            "startTime": "2026-01-15T10:30:00Z",
            "endTime": "2026-01-15T14:00:00Z",
            "placeVisit": {
                "location": {
                    "placeId": "place123",
                    "address": "Café Downtown",
                    "latitudeE7": 525161230,
                    "longitudeE7": 134304560,
                },
                "duration": {
                    "startTimestampMs": "1737957000000",
                    "endTimestampMs": "1737968400000",
                },
            },
        },
        {
            "startTime": "2026-01-15T14:00:00Z",
            "endTime": "2026-01-15T15:30:00Z",
            "activityType": "IN_VEHICLE",
            "timelinePath": [
                {"point": "geo:52.516123,13.430456"},
                {"point": "geo:52.520345,13.435789"},
                {"point": "geo:52.525678,13.440234"},
                {"point": "geo:52.530567,13.445678"},
            ],
        },
        {
            "startTime": "2026-01-15T15:30:00Z",
            "endTime": "2026-01-15T22:00:00Z",
            "placeVisit": {
                "location": {
                    "placeId": "place456",
                    "address": "Home",
                    "latitudeE7": 525305670,
                    "longitudeE7": 134456780,
                },
                "duration": {
                    "startTimestampMs": "1737968400000",
                    "endTimestampMs": "1737990000000",
                },
            },
        },
    ]
    json_file = tmp_path / "location-history.json"
    with open(json_file, "w") as f:
        json.dump(timeline_data, f)
    return str(json_file)
