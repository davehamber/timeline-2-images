"""Tile cache manager for OSM tile caching."""

from pathlib import Path
import sqlite3


class TileCacheManager:
    """Manages tile caching for map rendering."""

    def __init__(self, cache_dir: str | None = None):
        """Initialize tile cache manager.

        Args:
            cache_dir: Directory for tile cache. If None, uses ~/.cache/timeline-2-images
        """
        if cache_dir is None:
            cache_dir = str(Path.home() / ".cache" / "timeline-2-images")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.db_path = self.cache_dir / "tiles.sqlite"

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            if not self.db_path.exists():
                return {"status": "no_cache", "cached_tiles": 0}

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM responses")
            count = cursor.fetchone()[0]
            conn.close()

            return {
                "status": "cached",
                "total_cached_tiles": count,
                "cache_path": str(self.db_path),
            }
        except (OSError, sqlite3.Error):
            return {"status": "error"}

    def get_cache_size(self) -> int:
        """Get cache size in bytes.

        Returns:
            Size in bytes
        """
        try:
            if self.db_path.exists():
                return self.db_path.stat().st_size
            return 0
        except OSError:
            return 0

    def clear(self) -> None:
        """Clear tile cache."""
        try:
            if self.db_path.exists():
                self.db_path.unlink()
        except OSError:
            pass

    def get_info(self) -> dict:
        """Get complete cache information.

        Returns:
            Dictionary with cache info
        """
        stats = self.get_cache_stats()
        size_bytes = self.get_cache_size()
        size_mb = size_bytes / 1024 / 1024

        return {
            **stats,
            "cache_size_bytes": size_bytes,
            "cache_size_mb": round(size_mb, 2),
            "cache_dir": str(self.cache_dir),
        }
