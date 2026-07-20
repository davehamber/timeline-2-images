"""Unit tests for custom exceptions."""

from timeline_2_images.exceptions import TimelineException


class TestExceptions:
    """Tests for custom exception types."""

    def test_timeline_exception_base(self):
        """Test TimelineException as base exception."""
        exc = TimelineException("Test error")
        assert str(exc) == "Test error"
