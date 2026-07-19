# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Presenter/Controller: Mediates between GUI and business logic.

This layer converts user actions into business operations and
updates to display state, keeping GUI and business logic separate.
"""

from typing import Callable, Optional

from timeline_2_images.gui.models.interfaces import (
    ITimelineProcessor,
    ImageGenerationConfig,
    GenerationResult,
    ProgressCallback,
)


class TimelineGeneratorPresenter:
    """Presenter: Orchestrates between GUI views and timeline processor.

    This presenter:
    - Accepts user actions from GUI
    - Validates user input
    - Calls business logic via ITimelineProcessor interface
    - Notifies GUI of results via callbacks

    Never directly uses TimelineApp or any core library internals.
    """

    def __init__(self, processor: ITimelineProcessor):
        """Initialize with processor (dependency injection).

        Args:
            processor: ITimelineProcessor implementation (e.g., adapter)
        """
        self._processor = processor

        # Callbacks for GUI to register (loose coupling)
        self._on_validation_result: Optional[Callable[[bool, Optional[str]], None]] = None
        self._on_available_dates: Optional[Callable[[list[str]], None]] = None
        self._on_generation_complete: Optional[Callable[[GenerationResult], None]] = None

    # ===== Event Registration (GUI calls these to subscribe) =====

    def on_validation_result(self, callback: Callable[[bool, Optional[str]], None]) -> None:
        """Register callback for file validation results.

        Args:
            callback: Called with (is_valid, error_message)
        """
        self._on_validation_result = callback

    def on_available_dates(self, callback: Callable[[list[str]], None]) -> None:
        """Register callback for available dates.

        Args:
            callback: Called with list of YYYY-MM-DD date strings
        """
        self._on_available_dates = callback

    def on_generation_complete(self, callback: Callable[[GenerationResult], None]) -> None:
        """Register callback for generation results.

        Args:
            callback: Called with GenerationResult
        """
        self._on_generation_complete = callback

    # ===== User Actions (GUI calls these on user interaction) =====

    def handle_file_selected(self, path: str) -> None:
        """User selected a Timeline.json file.

        Args:
            path: Path to selected file
        """
        is_valid, error = self._processor.validate_file(path)

        if self._on_validation_result:
            self._on_validation_result(is_valid, error)

        if is_valid:
            # Load available dates after successful validation
            self.handle_timeline_loaded(path)

    def handle_timeline_loaded(self, path: str) -> None:
        """Timeline file has been loaded/validated.

        Args:
            path: Path to timeline file
        """
        dates = self._processor.get_available_dates(path)

        if self._on_available_dates:
            self._on_available_dates(dates)

    def handle_generate_clicked(
        self,
        timeline_path: str,
        output_dir: str,
        image_size: int = 500,
        add_place_names: bool = True,
        single_image: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 14,
        on_progress: Optional[ProgressCallback] = None,
    ) -> None:
        """User clicked 'Generate Maps' button.

        Args:
            timeline_path: Path to Timeline.json
            output_dir: Output directory for images
            image_size: Size of output images
            add_place_names: Whether to add place names
            single_image: Whether to render single combined image
            start_date: Start date (YYYY-MM-DD) or None
            end_date: End date (YYYY-MM-DD) or None
            days: Number of days to process
            on_progress: Progress callback (completed, total)
        """
        config = ImageGenerationConfig(
            timeline_path=timeline_path,
            output_dir=output_dir,
            image_size=image_size,
            add_place_names=add_place_names,
            single_image=single_image,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

        result = self._processor.generate_images(config, on_progress=on_progress)

        if self._on_generation_complete:
            self._on_generation_complete(result)

    def handle_clear_cache_clicked(self) -> None:
        """User clicked 'Clear Cache' button."""
        self._processor.clear_cache()
