"""Unit tests for custom exceptions."""

import pytest

from timeline_2_images.exceptions import (
    TimelineException,
    SegmentProcessingError,
    RenderingError,
    ValidationError,
    CacheError,
)


class TestExceptions:
    """Tests for custom exception types."""

    def test_timeline_exception_base(self):
        """Test TimelineException as base exception."""
        exc = TimelineException("Test error")
        assert str(exc) == "Test error"

    def test_segment_processing_error_inheritance(self):
        """Test SegmentProcessingError inherits from TimelineException."""
        exc = SegmentProcessingError("Failed to process segments")
        assert isinstance(exc, TimelineException)
        assert isinstance(exc, Exception)

    def test_rendering_error_inheritance(self):
        """Test RenderingError inherits from TimelineException."""
        exc = RenderingError("Failed to render map")
        assert isinstance(exc, TimelineException)
        assert isinstance(exc, Exception)

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from TimelineException."""
        exc = ValidationError("Invalid Timeline.json")
        assert isinstance(exc, TimelineException)
        assert isinstance(exc, Exception)

    def test_cache_error_inheritance(self):
        """Test CacheError inherits from TimelineException."""
        exc = CacheError("Failed to clear cache")
        assert isinstance(exc, TimelineException)
        assert isinstance(exc, Exception)

    def test_catch_base_timeline_exception(self):
        """Test catching all timeline exceptions with base class."""
        exceptions = [
            SegmentProcessingError("test"),
            RenderingError("test"),
            ValidationError("test"),
            CacheError("test"),
        ]

        for exc in exceptions:
            with pytest.raises(TimelineException):
                raise exc

    def test_catch_specific_exception(self):
        """Test catching specific exception types."""
        with pytest.raises(SegmentProcessingError):
            raise SegmentProcessingError("test")

        with pytest.raises(RenderingError):
            raise RenderingError("test")

        with pytest.raises(ValidationError):
            raise ValidationError("test")

        with pytest.raises(CacheError):
            raise CacheError("test")

    def test_exception_with_cause(self):
        """Test exception chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise SegmentProcessingError("Failed to process") from e
        except SegmentProcessingError as exc:
            assert isinstance(exc.__cause__, ValueError)
