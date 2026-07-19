"""Manages cache directory and file paths for timeline segments."""

import hashlib
from pathlib import Path


class CachePathManager:
    """Manages cache directory and file paths."""

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

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
