"""Validate Timeline.json structure and provide descriptive error messages."""

import json
from pathlib import Path
from typing import Any


class TimelineValidationError(Exception):
    """Raised when Timeline.json structure is invalid."""


class TimelineValidator:
    """Validates Timeline.json structure with detailed error messages."""

    @staticmethod
    def validate_field_is_list(data: dict, field: str, errors: list) -> bool:
        """Check if a field exists and is a list. Returns True if field is valid."""
        if field not in data:
            return False
        if not isinstance(data[field], list):
            errors.append(f"{field} must be an array, got {type(data[field]).__name__}")
            return False
        return True

    @staticmethod
    def load_json_file(json_path: str) -> Any:
        """Load and parse JSON file."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]
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

    @staticmethod
    def check_data_is_dict(data: dict) -> None:
        """Verify data is a dictionary."""
        if not isinstance(data, dict):
            raise TimelineValidationError(
                f"Timeline.json root must be an object/dictionary, got {type(data).__name__}\n"
                'Expected: {"semanticSegments": [...], "timelineObjects": [...],\n'
                '"locations": [...]}\n'
                "Note: Google may have changed their Timeline export format.\n"
                "Check that you're exporting from Google Takeout (https://takeout.google.com)"
            )

    @staticmethod
    def check_has_data_sources(data: dict) -> None:
        """Verify data has at least one data source."""
        errors: list[str] = []
        fields = ["semanticSegments", "timelineObjects", "locations"]
        has_data = any(
            TimelineValidator.validate_field_is_list(data, field, errors) for field in fields
        )

        if errors:
            error_msg = "Timeline.json structure errors:\n" + "\n".join(f"  • {e}" for e in errors)
            raise TimelineValidationError(error_msg)

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

    def validate_timeline_structure(self, json_path: str) -> dict:
        """Validate Timeline.json structure and return parsed data."""
        path = Path(json_path)
        if not path.exists():
            raise TimelineValidationError(f"Timeline file not found: {json_path}")

        data: Any = self.load_json_file(json_path)
        self.check_data_is_dict(data)
        self.check_has_data_sources(data)
        return data  # type: ignore

    @staticmethod
    def collect_segment_errors(segment: dict, segment_index: int) -> list[str]:
        """Collect validation errors for a segment."""
        errors: list[str] = []
        for required_field in ["startTime", "endTime"]:
            if required_field not in segment:
                errors.append(f"Segment {segment_index}: missing '{required_field}'")

        if "timelinePath" in segment and not isinstance(segment["timelinePath"], list):
            errors.append(
                f"Segment {segment_index}: timelinePath must be array, "
                f"got {type(segment['timelinePath']).__name__}"
            )
        return errors

    def validate_segment_structure(self, segment: dict, segment_index: int = 0) -> None:
        """Validate a semantic segment has required fields."""
        if not isinstance(segment, dict):
            raise TimelineValidationError(
                f"Segment {segment_index} must be an object, got {type(segment).__name__}"
            )

        errors = self.collect_segment_errors(segment, segment_index)
        if errors:
            raise TimelineValidationError("\n".join(errors))


_validator = TimelineValidator()


def validate_timeline_structure(json_path: str) -> dict:
    """Validate Timeline.json structure and return parsed data."""
    return _validator.validate_timeline_structure(json_path)


def validate_segment_structure(segment: dict, segment_index: int = 0) -> None:
    """Validate a semantic segment has required fields."""
    _validator.validate_segment_structure(segment, segment_index)
