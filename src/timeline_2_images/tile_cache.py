"""Tile caching for OpenStreetMap tiles to avoid redundant downloads.

Implements both in-memory and disk-based caching strategies for map tiles.
Tiles downloaded from OSM are cached and reused across multiple days,
significantly reducing network I/O for adjacent geographic areas.
"""

import hashlib
from pathlib import Path

import requests


class MemoryTileCache:
    """In-memory tile cache for current session."""

    def __init__(self):
        self.cache: dict[str, bytes] = {}
        self.hits = 0
        self.misses = 0

    def get(self, url: str) -> bytes | None:
        """Get tile from memory cache."""
        return self.cache.get(url)

    def set(self, url: str, data: bytes) -> None:
        """Store tile in memory cache."""
        self.cache[url] = data

    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0


class DiskTileCache:
    """Persistent disk-based tile cache."""

    def __init__(self, cache_dir: str = ".tile_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path from URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.tile"

    def get(self, url: str) -> bytes | None:
        """Get tile from disk cache."""
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                return cache_path.read_bytes()
            except OSError:
                return None
        return None

    def set(self, url: str, data: bytes) -> None:
        """Store tile to disk cache."""
        cache_path = self._get_cache_path(url)
        try:
            cache_path.write_bytes(data)
        except OSError:
            pass

    def clear(self) -> None:
        """Clear all cached tiles."""
        for tile_file in self.cache_dir.glob("*.tile"):
            try:
                tile_file.unlink()
            except OSError:
                pass

    def get_stats(self) -> dict:
        """Get cache statistics."""
        tile_files = list(self.cache_dir.glob("*.tile"))
        total_size = sum(f.stat().st_size for f in tile_files if f.exists())
        return {
            "tile_count": len(tile_files),
            "total_size_mb": total_size / 1024 / 1024,
        }


class CachedTileProvider:
    """Wrapper for tile provider with caching."""

    def __init__(
        self,
        url: str,
        memory_cache: MemoryTileCache | None = None,
        disk_cache: DiskTileCache | None = None,
        session: requests.Session | None = None,
    ):
        self.url = url
        self.memory_cache = memory_cache or MemoryTileCache()
        self.disk_cache = disk_cache or DiskTileCache()
        self.session = session or requests.Session()
        self.memory_hits = 0
        self.disk_hits = 0
        self.network_requests = 0

    def get_tile(self, x: int, y: int, z: int) -> bytes:
        """Get tile with caching (memory → disk → network)."""
        tile_url = self.url.format(x=x, y=y, z=z)

        cached = self.memory_cache.get(tile_url)
        if cached is not None:
            self.memory_hits += 1
            return cached

        cached = self.disk_cache.get(tile_url)
        if cached is not None:
            self.disk_hits += 1
            self.memory_cache.set(tile_url, cached)
            return cached

        self.network_requests += 1
        response = self.session.get(tile_url, timeout=10)
        response.raise_for_status()
        data: bytes = response.content
        self.memory_cache.set(tile_url, data)
        self.disk_cache.set(tile_url, data)
        return data

    def get_stats(self) -> dict:
        """Get cache performance statistics."""
        total_requests = self.memory_hits + self.disk_hits + self.network_requests
        return {
            "total_tile_requests": total_requests,
            "memory_cache_hits": self.memory_hits,
            "disk_cache_hits": self.disk_hits,
            "network_requests": self.network_requests,
            "cache_hit_rate": (
                (self.memory_hits + self.disk_hits) / total_requests * 100
                if total_requests > 0
                else 0
            ),
        }


_memory_cache = MemoryTileCache()
_disk_cache = DiskTileCache()
TILE_PROVIDER: CachedTileProvider | None = None


def get_cachedTILE_PROVIDER(
    url: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
) -> CachedTileProvider:
    """Get or create cached tile provider."""
    global TILE_PROVIDER
    if TILE_PROVIDER is None:
        TILE_PROVIDER = CachedTileProvider(url, _memory_cache, _disk_cache)
    return TILE_PROVIDER


def get_osm_tile_url(x: int, y: int, z: int) -> bytes:
    """Get OSM tile with caching."""
    provider = get_cachedTILE_PROVIDER()
    return provider.get_tile(x, y, z)


def get_cache_stats() -> dict:
    """Get overall cache statistics."""
    if TILE_PROVIDER is None:
        return {}
    return {
        "tile_provider_stats": TILE_PROVIDER.get_stats(),
        "disk_cache_stats": _disk_cache.get_stats(),
    }


def clear_caches() -> None:
    """Clear all caches."""
    global TILE_PROVIDER
    _memory_cache.clear()
    _disk_cache.clear()
    TILE_PROVIDER = None
