"""Validate Timeline.json structure and provide descriptive error messages."""

import json
from pathlib import Path


class TimelineValidationError(Exception):
    """Raised when Timeline.json structure is invalid."""


def validate_timeline_structure(json_path: str) -> dict:
    """
    Validate Timeline.json structure and return parsed data.

    Args:
        json_path: Path to Timeline.json file

    Returns:
        Parsed JSON data if valid

    Raises:
        TimelineValidationError: If structure is invalid
    """
    path = Path(json_path)

    # Check file exists
    if not path.exists():
        raise TimelineValidationError(f"Timeline file not found: {json_path}")

    # Check file is readable
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise TimelineValidationError(
            f"Invalid JSON format in {json_path}:\n"
            f"  {e}\n\n"
            "This file does not appear to be valid JSON.\n"
            "Expected structure: a JSON object containing timeline data with one or more of:\n"
            "  • semanticSegments - array of semantic location segments\n"
            "  • timelineObjects - array of raw timeline events\n"
            "  • locations - array of historical location records\n\n"
            "Possible causes:\n"
            "  • File is corrupted or incomplete\n"
            "  • File was edited manually and syntax is broken\n"
            "  • Google changed the Timeline export format\n\n"
            "Solution: Re-download your Timeline.json from Google Takeout\n"
            "          (https://takeout.google.com) and select 'Location History'"
        ) from e
    except (IOError, OSError) as e:
        raise TimelineValidationError(f"Cannot read Timeline file: {e}") from e

    # Validate it's a dictionary
    if not isinstance(data, dict):
        raise TimelineValidationError(
            f"Timeline.json root must be an object/dictionary, got {type(data).__name__}\n"
            'Expected: {"semanticSegments": [...], "timelineObjects": [...], "locations": [...]}\n'
            "Note: Google may have changed their Timeline export format.\n"
            "Check that you're exporting from Google Takeout (https://takeout.google.com)"
        )

    # Check for at least one data source
    has_data = False
    errors = []

    # Validate semanticSegments (if present)
    if "semanticSegments" in data:
        if not isinstance(data["semanticSegments"], list):
            errors.append(
                f"semanticSegments must be an array, got {type(data['semanticSegments']).__name__}"
            )
        else:
            has_data = True

    # Validate timelineObjects (if present)
    if "timelineObjects" in data:
        if not isinstance(data["timelineObjects"], list):
            errors.append(
                f"timelineObjects must be an array, got {type(data['timelineObjects']).__name__}"
            )
        else:
            has_data = True

    # Validate locations (if present)
    if "locations" in data:
        if not isinstance(data["locations"], list):
            errors.append(f"locations must be an array, got {type(data['locations']).__name__}")
        else:
            has_data = True

    # Check if we have at least one data source
    if not has_data:
        raise TimelineValidationError(
            "Timeline.json does not contain location data.\n"
            "Expected at least one of these top-level arrays:\n"
            "  • semanticSegments - semantic location visits and journeys\n"
            "  • timelineObjects - raw timeline events\n"
            "  • locations - historical location records\n\n"
            "Note: Google may have changed their Timeline export format.\n"
            "Please verify the file is from Google Takeout (https://takeout.google.com)\n"
            "and includes 'Location History' in the export."
        )

    # Report any validation errors found
    if errors:
        error_msg = "Timeline.json structure errors:\n" + "\n".join(f"  • {e}" for e in errors)
        raise TimelineValidationError(error_msg)

    return data


def validate_segment_structure(segment: dict, segment_index: int = 0) -> None:
    """
    Validate a semantic segment has required fields.

    Args:
        segment: Segment dictionary
        segment_index: Index for error reporting

    Raises:
        TimelineValidationError: If segment structure is invalid
    """
    if not isinstance(segment, dict):
        raise TimelineValidationError(
            f"Segment {segment_index} must be an object, got {type(segment).__name__}"
        )

    errors = []

    if "startTime" not in segment:
        errors.append(f"Segment {segment_index}: missing 'startTime'")

    if "endTime" not in segment:
        errors.append(f"Segment {segment_index}: missing 'endTime'")

    if "timelinePath" in segment and not isinstance(segment["timelinePath"], list):
        errors.append(
            f"Segment {segment_index}: timelinePath must be array, "
            f"got {type(segment['timelinePath']).__name__}"
        )

    if errors:
        raise TimelineValidationError("\n".join(errors))
