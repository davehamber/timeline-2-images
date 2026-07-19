"""SQLite-based caching for Timeline segments indexed by date.

Stores parsed segments in a database indexed by date for instant lookups.
Automatically manages cache invalidation via SHA-256 hash verification.
"""

import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, timezone

from timeline_2_images.cache_path_manager import CachePathManager


class SegmentCache:
    """Manages SQLite-based segment caching with automatic validation."""

    def __init__(self):
        self.path_manager = CachePathManager()

    def _init_db(self, db_path: Path) -> sqlite3.Connection:
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

    def _validate_cache(self, db_path: Path, hash_path: Path, json_path: str) -> bool:
        """Check if cache exists and is valid. Returns False and cleans up if invalid."""
        if not db_path.exists() or not hash_path.exists():
            return False

        try:
            current_hash = self.path_manager.compute_file_hash(json_path)
            cached_hash = hash_path.read_text().strip()
            if current_hash != cached_hash:
                db_path.unlink()
                hash_path.unlink()
                return False
            return True
        except (OSError, sqlite3.Error):
            return False

    def _extract_segment_date(self, segment: dict) -> str | None:
        """Extract and format segment date from segment dict."""
        start_str = segment.get("startTime")
        if not start_str:
            return None

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel

            dt_timestamp = pd.to_datetime(start_str, utc=True, errors="coerce")
            if pd.isna(dt_timestamp):
                return None
            parsed_datetime = datetime.fromisoformat(str(dt_timestamp.isoformat()))  # type: ignore[union-attr]
            return parsed_datetime.astimezone(timezone.utc).date().isoformat()
        except (ValueError, AttributeError):
            return None

    def _extract_activity_type(self, segment: dict) -> str:
        """Extract activity type from segment."""
        if "activity" in segment:
            activity_type = segment["activity"].get("topCandidate", {}).get("type", "UNKNOWN")
            return str(activity_type) if activity_type else "UNKNOWN"
        return "UNKNOWN"

    def _build_segment_record(self, segment: dict) -> tuple[str, str] | None:
        """Build database record for a segment."""
        seg_date = self._extract_segment_date(segment)
        if not seg_date:
            return None

        activity_type = self._extract_activity_type(segment)
        segment_json = json.dumps(
            {
                "startTime": segment.get("startTime"),
                "endTime": segment.get("endTime"),
                "timelinePath": segment.get("timelinePath", []),
                "activity": segment.get("activity", {}),
                "visit": segment.get("visit", {}),
                "activityType": activity_type,
            },
            default=str,
        )

        return (seg_date, segment_json)

    def populate_cache(self, json_path: str, data: dict) -> None:
        """Populate SQLite cache with segments from parsed Timeline data."""
        db_path = self.path_manager.get_cache_db_path(json_path)
        hash_path = self.path_manager.get_hash_path(json_path)

        try:
            conn = self._init_db(db_path)
            conn.execute("DELETE FROM segments")

            for segment in data.get("semanticSegments", []):
                record = self._build_segment_record(segment)
                if record:
                    seg_date, segment_json = record
                    conn.execute(
                        "INSERT INTO segments (date, segment_json) VALUES (?, ?)",
                        (seg_date, segment_json),
                    )

            conn.commit()
            conn.close()

            file_hash = self.path_manager.compute_file_hash(json_path)
            hash_path.write_text(file_hash)
        except (OSError, ValueError, sqlite3.Error) as e:
            print(f"Warning: Failed to populate segment cache: {e}")

    def _load_segment_rows_from_db(self, db_path: Path, target_date: str) -> list[str] | None:
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

    def load_segments_for_date(self, json_path: str, target_date: str) -> list[dict] | None:
        """Load segments for a specific date from SQLite cache."""
        db_path = self.path_manager.get_cache_db_path(json_path)
        hash_path = self.path_manager.get_hash_path(json_path)

        if not self._validate_cache(db_path, hash_path, json_path):
            return None

        rows = self._load_segment_rows_from_db(db_path, target_date)
        if rows is None:
            return None

        if not rows:
            return []

        return [json.loads(segment_json) for segment_json in rows]

    def _load_dates_from_db(self, db_path: Path) -> list[str] | None:
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

    def get_cached_dates(self, json_path: str) -> list[str] | None:
        """Get all dates available in SQLite cache, or None if cache is invalid/missing."""
        db_path = self.path_manager.get_cache_db_path(json_path)
        hash_path = self.path_manager.get_hash_path(json_path)

        if not self._validate_cache(db_path, hash_path, json_path):
            return None

        return self._load_dates_from_db(db_path)

    def get_cache_stats(self, json_path: str) -> dict:
        """Get SQLite cache statistics."""
        db_path = self.path_manager.get_cache_db_path(json_path)

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

    def clear_cache(self, json_path: str) -> None:
        """Clear SQLite cache for a given JSON file."""
        db_path = self.path_manager.get_cache_db_path(json_path)
        hash_path = self.path_manager.get_hash_path(json_path)

        try:
            if db_path.exists():
                db_path.unlink()
            if hash_path.exists():
                hash_path.unlink()
        except OSError:
            pass

    def clean_all_cache(self) -> None:
        """Remove the entire cache directory."""
        try:
            cache_dir = self.path_manager.get_cache_dir()
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
        except OSError as e:
            raise RuntimeError(f"Failed to clean cache: {e}") from e
