"""Caching configuration for timeline processing."""

from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Configuration for segment caching behavior.

    Controls how Timeline.json data is cached in memory during processing.

    Attributes:
        enable_caching: Enable in-memory caching of parsed Timeline.json (default: True)
        max_cache_size_mb: Maximum cache size in MB (default: 512)
        clear_on_exit: Clear cache when TimelineApp is garbage collected (default: True)

    Example:
        >>> config = CacheConfig(
        ...     enable_caching=True,
        ...     max_cache_size_mb=256,
        ...     clear_on_exit=True
        ... )
        >>> app = TimelineApp("Timeline.json", cache_config=config)
    """

    enable_caching: bool = True
    max_cache_size_mb: int = 512
    clear_on_exit: bool = True

    def validate(self) -> bool:
        """Validate cache configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if self.max_cache_size_mb < 1:
            raise ValueError("max_cache_size_mb must be at least 1 MB")
        if self.max_cache_size_mb > 8192:
            raise ValueError("max_cache_size_mb must not exceed 8192 MB (8 GB)")
        return True

    def get_cache_size_bytes(self) -> int:
        """Get maximum cache size in bytes.

        Returns:
            Cache size in bytes
        """
        return self.max_cache_size_mb * 1024 * 1024

    def __str__(self) -> str:
        """String representation of cache configuration."""
        status = "enabled" if self.enable_caching else "disabled"
        return (
            f"CacheConfig(enabled={status}, "
            f"max_size={self.max_cache_size_mb}MB, "
            f"clear_on_exit={self.clear_on_exit})"
        )
