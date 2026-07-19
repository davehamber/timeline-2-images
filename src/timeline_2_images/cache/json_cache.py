# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""SQLite-based persistent cache for parsed JSON timeline data."""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


class JsonCache:
    """Persistent SQLite cache for parsed JSON timeline data."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize JSON cache.

        Args:
            cache_dir: Cache directory (uses ~/.cache/timeline-2-images by default)
        """
        if cache_dir is None:
            cache_dir = str(Path.home() / ".cache" / "timeline-2-images")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "json_cache.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS json_cache (
                    json_path TEXT PRIMARY KEY,
                    file_mtime REAL NOT NULL,
                    file_size INTEGER NOT NULL,
                    cached_data TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, json_path: str) -> Optional[Any]:
        """Get cached parsed JSON data if valid.

        Args:
            json_path: Path to Timeline.json file

        Returns:
            Cached data if valid and exists, None otherwise
        """
        try:
            json_file = Path(json_path).resolve()  # Normalize to absolute path
            if not json_file.exists():
                return None

            current_mtime = json_file.stat().st_mtime
            current_size = json_file.stat().st_size

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT file_mtime, file_size, cached_data FROM json_cache WHERE json_path = ?",
                    (str(json_file),),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                cached_mtime, cached_size, cached_data = row

                # Validate cache freshness
                if cached_mtime != current_mtime or cached_size != current_size:
                    # File has changed, invalidate cache
                    self.delete(json_path)
                    return None

                return json.loads(cached_data)
        except Exception as e:
            import sys
            print(f"Cache error for {json_path}: {e}", file=sys.stderr)
            return None

    def set(self, json_path: str, data: Any) -> None:
        """Cache parsed JSON data.

        Args:
            json_path: Path to Timeline.json file
            data: Parsed data to cache
        """
        try:
            json_file = Path(json_path).resolve()  # Normalize to absolute path
            if not json_file.exists():
                return

            mtime = json_file.stat().st_mtime
            size = json_file.stat().st_size
            cached_json = json.dumps(data)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO json_cache
                    (json_path, file_mtime, file_size, cached_data)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(json_file), mtime, size, cached_json),
                )
                conn.commit()
        except Exception:
            pass

    def delete(self, json_path: str) -> None:
        """Delete cached entry.

        Args:
            json_path: Path to Timeline.json file
        """
        try:
            json_file = Path(json_path).resolve()  # Normalize to absolute path
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM json_cache WHERE json_path = ?", (str(json_file),))
                conn.commit()
        except Exception:
            pass

    def clear(self) -> None:
        """Clear entire cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM json_cache")
                conn.commit()
        except Exception:
            pass
