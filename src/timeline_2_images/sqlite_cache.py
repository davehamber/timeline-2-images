"""SQLite-based caching for Timeline segments indexed by date.

Stores parsed segments in a database indexed by date for instant lookups.
Automatically manages cache invalidation via SHA-256 hash verification.
"""

import json
import hashlib
import sqlite3
from pathlib import Path


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _get_cache_dir() -> Path:
    """Get cache directory, creating it if needed."""
    cache_dir = Path.home() / ".cache" / "timeline-2-images"
    cache_dir.mkdir(exist_ok=True, parents=True)
    return cache_dir


def get_cache_db_path(_: str) -> Path:
    """Get SQLite database path for a given JSON file."""
    cache_dir = _get_cache_dir()
    return cache_dir / "segments.db"


def get_hash_path(_: str) -> Path:
    """Get hash metadata file path for a given JSON file."""
    cache_dir = _get_cache_dir()
    return cache_dir / "segments.hash"


def _init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize or open the segments database."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            segment_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date ON segments(date)
        """
    )
    conn.commit()
    return conn


def populate_cache(json_path: str, data: dict) -> None:
    """Populate SQLite cache with segments from parsed Timeline data.

    Args:
        json_path: Path to Timeline.json file
        data: Parsed Timeline data dict
    """
    db_path = get_cache_db_path(json_path)
    hash_path = get_hash_path(json_path)

    try:
        conn = _init_db(db_path)

        conn.execute("DELETE FROM segments")

        for segment in data.get("semanticSegments", []):
            start_str = segment.get("startTime")
            if not start_str:
                continue

            import pandas as pd  # pylint: disable=import-outside-toplevel

            dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
            if pd.isna(dt_timestamp):
                continue

            from datetime import datetime, timezone  # pylint: disable=import-outside-toplevel

            parsed_datetime = datetime.fromisoformat(str(dt_timestamp.isoformat()))
            seg_date = parsed_datetime.astimezone(timezone.utc).date().isoformat()

            segment_json = json.dumps(
                {
                    "startTime": start_str,
                    "endTime": segment.get("endTime"),
                    "timelinePath": segment.get("timelinePath", []),
                },
                default=str,
            )

            conn.execute(
                "INSERT INTO segments (date, segment_json) VALUES (?, ?)",
                (seg_date, segment_json),
            )

        conn.commit()
        conn.close()

        file_hash = _compute_file_hash(json_path)
        hash_path.write_text(file_hash)
    except (OSError, ValueError, sqlite3.Error) as e:
        print(f"Warning: Failed to populate segment cache: {e}")


def _validate_cache(db_path: Path, hash_path: Path, json_path: str) -> bool:
    """Check if cache exists and is valid. Returns False and cleans up if invalid."""
    if not db_path.exists() or not hash_path.exists():
        return False

    try:
        current_hash = _compute_file_hash(json_path)
        cached_hash = hash_path.read_text().strip()
        if current_hash != cached_hash:
            db_path.unlink()
            hash_path.unlink()
            return False
        return True
    except (OSError, sqlite3.Error):
        return False


def _load_segment_rows_from_db(db_path: Path, target_date: str) -> list[str] | None:
    """Load segment JSON rows from database. Returns None on error."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT segment_json FROM segments WHERE date = ?", (target_date,))
        rows = [row[0] for row in cursor.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error:
        return None


def load_segments_for_date(json_path: str, target_date: str) -> list[dict] | None:
    """Load segments for a specific date from SQLite cache.

    Returns list of segments if cache is valid, None if cache doesn't exist or is invalid.
    """
    db_path = get_cache_db_path(json_path)
    hash_path = get_hash_path(json_path)

    if not _validate_cache(db_path, hash_path, json_path):
        return None

    rows = _load_segment_rows_from_db(db_path, target_date)
    if rows is None:
        return None

    if not rows:
        return []

    return [json.loads(segment_json) for segment_json in rows]


def get_cache_stats(json_path: str) -> dict:
    """Get SQLite cache statistics."""
    db_path = get_cache_db_path(json_path)

    if not db_path.exists():
        return {"status": "no_cache", "segment_count": 0}

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM segments")
        count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT date) FROM segments")
        date_count = cursor.fetchone()[0]

        db_size_mb = db_path.stat().st_size / 1024 / 1024

        conn.close()

        return {
            "status": "cached",
            "segment_count": count,
            "date_count": date_count,
            "size_mb": db_size_mb,
        }
    except sqlite3.Error:
        return {"status": "error"}


def _load_dates_from_db(db_path: Path) -> list[str] | None:
    """Load all dates from database. Returns None on error."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date FROM segments ORDER BY date")
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates if dates else None
    except sqlite3.Error:
        return None


def get_cached_dates(json_path: str) -> list[str] | None:
    """Get all dates available in SQLite cache, or None if cache is invalid/missing."""
    db_path = get_cache_db_path(json_path)
    hash_path = get_hash_path(json_path)

    if not _validate_cache(db_path, hash_path, json_path):
        return None

    return _load_dates_from_db(db_path)


def clear_cache(json_path: str) -> None:
    """Clear SQLite cache for a given JSON file."""
    db_path = get_cache_db_path(json_path)
    hash_path = get_hash_path(json_path)

    try:
        if db_path.exists():
            db_path.unlink()
        if hash_path.exists():
            hash_path.unlink()
    except OSError:
        pass


def clean_all_cache() -> None:
    """Remove the entire cache directory."""
    try:
        cache_dir = _get_cache_dir()
        if cache_dir.exists():
            import shutil  # pylint: disable=import-outside-toplevel

            shutil.rmtree(cache_dir)
    except OSError as e:
        raise RuntimeError(f"Failed to clean cache: {e}") from e
