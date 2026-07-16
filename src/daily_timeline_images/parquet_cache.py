"""Parquet-based caching for Timeline JSON data with file hash validation.

Caches parsed Timeline JSON using pickle (binary format) for fast loading on
consecutive runs. Automatically invalidates cache if the source JSON file has changed.
"""

import hashlib
import pickle
from pathlib import Path


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_cache_path(json_path: str) -> Path:
    """Get cache file path for a given JSON file."""
    json_file = Path(json_path)
    cache_dir = json_file.parent / ".timeline_cache"
    cache_dir.mkdir(exist_ok=True, parents=True)
    cache_file = cache_dir / f"{json_file.stem}.pkl"
    return cache_file


def get_hash_path(json_path: str) -> Path:
    """Get hash metadata file path for a given JSON file."""
    cache_path = get_cache_path(json_path)
    return cache_path.parent / f"{cache_path.stem}.hash"


def load_from_cache(json_path: str) -> dict | None:
    """Load Timeline data from cache if valid (hash matches).

    Returns the parsed data dict if cache is valid, None otherwise.
    """
    cache_path = get_cache_path(json_path)
    hash_path = get_hash_path(json_path)

    if not cache_path.exists() or not hash_path.exists():
        return None

    try:
        current_hash = _compute_file_hash(json_path)
        cached_hash = hash_path.read_text().strip()

        if current_hash != cached_hash:
            return None

        with open(cache_path, "rb") as f:
            data = pickle.load(f)
            if isinstance(data, dict):
                return data
            return None
    except Exception:
        return None


def save_to_cache(json_path: str, data: dict) -> None:
    """Save Timeline data to cache with file hash for validation."""
    cache_path = get_cache_path(json_path)
    hash_path = get_hash_path(json_path)

    try:
        file_hash = _compute_file_hash(json_path)

        with open(cache_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        hash_path.write_text(file_hash)
    except Exception:
        pass


def clear_cache(json_path: str) -> None:
    """Clear cache for a given JSON file."""
    cache_path = get_cache_path(json_path)
    hash_path = get_hash_path(json_path)

    try:
        if cache_path.exists():
            cache_path.unlink()
        if hash_path.exists():
            hash_path.unlink()
    except OSError:
        pass
