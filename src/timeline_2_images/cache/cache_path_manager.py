"""Manages cache directory and file paths for timeline segments."""

from pathlib import Path


class CachePathManager:
    """Manages cache directory and file paths."""

    @staticmethod
    def get_cache_dir() -> Path:
        """Get cache directory, creating it if needed."""
        cache_dir = Path.home() / ".cache" / "timeline-2-images"
        cache_dir.mkdir(exist_ok=True, parents=True)
        return cache_dir

    @staticmethod
    def get_cache_db_path(_: str) -> Path:
        """Get SQLite database path for a given JSON file."""
        cache_dir = CachePathManager.get_cache_dir()
        return cache_dir / "segments.db"

    @staticmethod
    def get_hash_path(_: str) -> Path:
        """Get hash metadata file path for a given JSON file."""
        cache_dir = CachePathManager.get_cache_dir()
        return cache_dir / "segments.hash"
