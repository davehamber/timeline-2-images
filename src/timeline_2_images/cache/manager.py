"""Abstract cache manager interface."""

from abc import ABC, abstractmethod

from timeline_2_images.models import Segment


class CacheManager(ABC):
    """Abstract interface for segment caching."""

    @abstractmethod
    def get_segments(self, date: str) -> list[Segment] | None:
        """
        Retrieve cached segments for a date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            List of Segment objects or None if not cached
        """

    @abstractmethod
    def store_segments(self, date: str, segments: list[Segment]) -> None:
        """
        Store segments in cache for a date.

        Args:
            date: Date string in YYYY-MM-DD format
            segments: List of Segment objects to cache
        """

    @abstractmethod
    def get_cached_dates(self) -> list[str]:
        """
        Get list of all dates with cached data.

        Returns:
            List of date strings in YYYY-MM-DD format
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached data."""

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if cache is valid."""
