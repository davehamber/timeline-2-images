# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""GUI settings persistence to cache directory."""

import json
from pathlib import Path
from typing import Any, Optional


class SettingsManager:
    """Manages GUI settings persistence."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize settings manager.

        Args:
            cache_dir: Cache directory for settings (uses ~/.cache/timeline-2-images by default)
        """
        if cache_dir is None:
            cache_dir = str(Path.home() / ".cache" / "timeline-2-images")

        self.cache_dir = Path(cache_dir)
        self.settings_file = self.cache_dir / "settings.json"
        self._settings = self._load_settings()

    def _load_settings(self) -> dict[str, Any]:
        """Load settings from cache directory."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_settings(self, settings: dict[str, Any]) -> None:
        """Save settings to cache directory.

        Args:
            settings: Dictionary of settings to save
        """
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value

    def all_settings(self) -> dict[str, Any]:
        """Get all settings.

        Returns:
            Dictionary of all settings
        """
        return dict(self._settings)
