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


def get_cache_db_path(json_path: str) -> Path:
    """Get SQLite database path for a given JSON file."""
    json_file = Path(json_path)
    cache_dir = json_file.parent / ".timeline_cache"
    cache_dir.mkdir(exist_ok=True, parents=True)
    return cache_dir / "segments.db"


def get_hash_path(json_path: str) -> Path:
    """Get hash metadata file path for a given JSON file."""
    db_path = get_cache_db_path(json_path)
    return db_path.parent / f"{db_path.stem}.hash"


def _init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize or open the segments database."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            segment_json TEXT NOT NULL
        )
        """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_date ON segments(date)
        """)
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

        for seg in data.get("semanticSegments", []):
            start_str = seg.get("startTime")
            if not start_str:
                continue

            import pandas as pd

            dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
            if pd.isna(dt_timestamp):
                continue

            from datetime import datetime, timezone

            dt = datetime.fromisoformat(str(dt_timestamp.isoformat()))
            seg_date = dt.astimezone(timezone.utc).date().isoformat()

            segment_json = json.dumps(
                {
                    "startTime": start_str,
                    "endTime": seg.get("endTime"),
                    "timelinePath": seg.get("timelinePath", []),
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
    except Exception as e:
        print(f"Warning: Failed to populate segment cache: {e}")


def load_segments_for_date(json_path: str, target_date: str) -> list[dict] | None:
    """Load segments for a specific date from SQLite cache.

    Returns list of segments if cache is valid, None if cache doesn't exist or is invalid.
    """
    db_path = get_cache_db_path(json_path)
    hash_path = get_hash_path(json_path)

    if not db_path.exists() or not hash_path.exists():
        return None

    try:
        current_hash = _compute_file_hash(json_path)
        cached_hash = hash_path.read_text().strip()

        if current_hash != cached_hash:
            db_path.unlink()
            hash_path.unlink()
            return None

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT segment_json FROM segments WHERE date = ?", (target_date,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        segments = []
        for (segment_json,) in rows:
            seg = json.loads(segment_json)
            segments.append(seg)

        return segments
    except Exception:
        return None


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
    except Exception:
        return {"status": "error"}


def get_cached_dates(json_path: str) -> list[str] | None:
    """Get all dates available in SQLite cache, or None if cache is invalid/missing."""
    db_path = get_cache_db_path(json_path)
    hash_path = get_hash_path(json_path)

    if not db_path.exists() or not hash_path.exists():
        return None

    try:
        current_hash = _compute_file_hash(json_path)
        cached_hash = hash_path.read_text().strip()

        if current_hash != cached_hash:
            db_path.unlink()
            hash_path.unlink()
            return None

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT date FROM segments ORDER BY date")
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()

        return dates if dates else None
    except Exception:
        return None


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
