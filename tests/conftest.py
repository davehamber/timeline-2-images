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
