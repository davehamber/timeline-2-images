# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Presenter/Controller: Mediates between GUI and business logic.

This layer converts user actions into business operations and
updates to display state, keeping GUI and business logic separate.
"""

from typing import Callable, Optional, TYPE_CHECKING

from timeline_2_images.gui.models.interfaces import (
    ITimelineProcessor,
    ImageGenerationConfig,
    GenerationResult,
    ProgressCallback,
)

if TYPE_CHECKING:
    from timeline_2_images.gui.timeline_worker import TimelineWorker
    from timeline_2_images.gui.generation_worker import GenerationWorker


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
        self._timeline_worker: Optional["TimelineWorker"] = None
        self._generation_worker: Optional["GenerationWorker"] = None

        # Callbacks for GUI to register (loose coupling)
        self._on_validation_result: Optional[Callable[[bool, Optional[str]], None]] = None
        self._on_available_dates: Optional[Callable[[list[str]], None]] = None
        self._on_generation_complete: Optional[Callable[[GenerationResult], None]] = None
        self._on_file_loading: Optional[Callable[[bool], None]] = None

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

    def on_file_loading(self, callback: Callable[[bool], None]) -> None:
        """Register callback for file loading state.

        Args:
            callback: Called with True when loading starts, False when complete
        """
        self._on_file_loading = callback

    # ===== User Actions (GUI calls these on user interaction) =====

    def handle_file_selected(self, path: str) -> None:
        """User selected a Timeline.json file.

        Args:
            path: Path to selected file
        """
        # Lazy import to avoid PySide6 dependency in non-GUI contexts
        from timeline_2_images.gui.timeline_worker import TimelineWorker

        # Signal that loading has started
        if self._on_file_loading:
            self._on_file_loading(True)

        # Create and start worker thread to avoid blocking UI
        self._timeline_worker = TimelineWorker(self._processor, path)
        self._timeline_worker.validation_complete.connect(self._on_validation_complete)
        self._timeline_worker.dates_loaded.connect(self._on_dates_loaded)
        self._timeline_worker.finished.connect(self._on_timeline_worker_finished)
        self._timeline_worker.start()

    def _on_validation_complete(self, is_valid: bool, error_message: str) -> None:
        """Handle worker validation result.

        Args:
            is_valid: Whether file is valid
            error_message: Error message if invalid
        """
        if self._on_validation_result:
            self._on_validation_result(is_valid, error_message if error_message else None)

    def _on_dates_loaded(self, dates: list[str]) -> None:
        """Handle worker dates loaded.

        Args:
            dates: List of available date strings
        """
        if self._on_available_dates:
            self._on_available_dates(dates)

    def _on_timeline_worker_finished(self) -> None:
        """Handle timeline worker thread finished."""
        if self._on_file_loading:
            self._on_file_loading(False)

    def handle_generate_clicked(
        self,
        timeline_path: str,
        output_dir: str,
        image_width: int = 500,
        image_height: int = 500,
        add_place_names: bool = True,
        single_image: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 14,
        on_progress: Optional[ProgressCallback] = None,
        on_file_loading: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """User clicked 'Generate Maps' button.

        Args:
            timeline_path: Path to Timeline.json
            output_dir: Output directory for images
            image_width: Width of output images
            image_height: Height of output images
            add_place_names: Whether to add place names
            single_image: Whether to render single combined image
            start_date: Start date (YYYY-MM-DD) or None
            end_date: End date (YYYY-MM-DD) or None
            days: Number of days to process
            on_progress: Progress callback (completed, total)
            on_file_loading: File loading callback (is_cached)
        """
        from timeline_2_images.gui.generation_worker import GenerationWorker

        config = ImageGenerationConfig(
            timeline_path=timeline_path,
            output_dir=output_dir,
            image_width=image_width,
            image_height=image_height,
            add_place_names=add_place_names,
            single_image=single_image,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

        # Create and start generation worker thread to avoid blocking UI
        self._generation_worker = GenerationWorker(
            self._processor, config, on_progress, on_file_loading
        )
        self._generation_worker.generation_complete.connect(self._on_generation_complete_signal)
        self._generation_worker.start()

    def _on_generation_complete_signal(self, result: GenerationResult) -> None:
        """Handle generation completion signal from worker.

        Args:
            result: GenerationResult from the worker
        """
        if self._on_generation_complete:
            self._on_generation_complete(result)

    def handle_clear_cache_clicked(self) -> None:
        """User clicked 'Clear Cache' button."""
        self._processor.clear_cache()

    def is_generating(self) -> bool:
        """Check if image generation is currently running.

        Returns:
            True if generation worker is active and running
        """
        return self._generation_worker is not None and self._generation_worker.isRunning()

    def cancel_generation(self) -> None:
        """Cancel the current image generation process."""
        if self._generation_worker is not None and self._generation_worker.isRunning():
            self._generation_worker.requestInterruption()
            # Wait briefly for graceful shutdown
            if not self._generation_worker.wait(1000):  # 1 second timeout
                # Force terminate if thread doesn't exit
                self._generation_worker.terminate()
                self._generation_worker.wait()
