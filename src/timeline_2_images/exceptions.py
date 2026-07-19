# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Custom exception types for timeline-2-images."""


class TimelineException(Exception):
    """Base exception for all timeline-2-images errors."""

    pass


class SegmentProcessingError(TimelineException):
    """Raised when segment processing fails.

    This occurs when semantic segments cannot be loaded, parsed, or processed
    from the Timeline.json file.

    Example:
        >>> try:
        ...     app.process_date("2026-07-19")
        ... except SegmentProcessingError as e:
        ...     print(f"Failed to process segments: {e}")
    """

    pass


class RenderingError(TimelineException):
    """Raised when map rendering fails.

    This occurs when the map renderer cannot create an image from processed
    segments (e.g., invalid bounds, tile fetch failures).

    Example:
        >>> try:
        ...     app.process_date("2026-07-19")
        ... except RenderingError as e:
        ...     print(f"Rendering failed: {e}")
    """

    pass


class ValidationError(TimelineException):
    """Raised when Timeline.json validation fails.

    This occurs when the Timeline.json file structure is invalid or missing
    required data.

    Example:
        >>> try:
        ...     TimelineApp.validate_file("invalid.json")
        ... except ValidationError as e:
        ...     print(f"Timeline invalid: {e}")
    """

    pass


class CacheError(TimelineException):
    """Raised when cache operations fail.

    This occurs when the segment cache cannot be read, written, or cleared.

    Example:
        >>> try:
        ...     app.clear_caches()
        ... except CacheError as e:
        ...     print(f"Cache operation failed: {e}")
    """

    pass
