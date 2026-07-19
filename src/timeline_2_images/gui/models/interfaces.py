# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Interfaces that GUI layer depends on (not core library)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


ProgressCallback = Callable[[int, int], None]


@dataclass
class ImageGenerationConfig:
    """Configuration for image generation.

    This is GUI-facing, not dependent on TimelineApp internals.
    """
    timeline_path: str
    output_dir: str
    image_size: int = 500
    add_place_names: bool = True
    single_image: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days: int = 14


@dataclass
class GenerationResult:
    """Result of image generation operation."""
    success: bool
    output_dir: Path
    image_count: int
    error_message: Optional[str] = None


class ITimelineProcessor(ABC):
    """Interface: Timeline processing (GUI depends on this, not concrete TimelineApp)."""

    @abstractmethod
    def validate_file(self, path: str) -> tuple[bool, Optional[str]]:
        """Validate Timeline.json file.

        Args:
            path: Path to Timeline.json

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_available_dates(self, path: str) -> list[str]:
        """Get all available dates in timeline.

        Args:
            path: Path to Timeline.json

        Returns:
            List of YYYY-MM-DD date strings
        """
        pass

    @abstractmethod
    def generate_images(
        self,
        config: ImageGenerationConfig,
        on_progress: Optional[ProgressCallback] = None,
    ) -> GenerationResult:
        """Generate map images for date range.

        Args:
            config: Generation configuration
            on_progress: Optional callback for progress updates (completed, total)

        Returns:
            GenerationResult with success status and details
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any cached data."""
        pass
