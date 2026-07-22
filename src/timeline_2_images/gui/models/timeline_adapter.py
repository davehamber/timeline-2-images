# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Adapter: Converts TimelineApp to GUI's ITimelineProcessor interface.

This adapter encapsulates the core library so the GUI layer never
directly depends on TimelineApp or other core implementation details.
"""

from pathlib import Path
from typing import Callable, Optional

from timeline_2_images.app import TimelineApp
from timeline_2_images.exceptions import TimelineException
from timeline_2_images.gui.models.interfaces import (
    ITimelineProcessor,
    ImageGenerationConfig,
    GenerationResult,
    ProgressCallback,
)


class TimelineProcessorAdapter(ITimelineProcessor):
    """Adapter: Implements ITimelineProcessor using TimelineApp.

    This adapter is the ONLY place where GUI code directly touches the core library.
    All GUI code depends on ITimelineProcessor interface, not TimelineApp.
    """

    def __init__(self):
        """Initialize adapter (creates nothing until first operation)."""
        self._app: Optional[TimelineApp] = None

    def validate_file(self, path: str) -> tuple[bool, Optional[str]]:
        """Validate Timeline.json file."""
        try:
            TimelineApp.validate_file(path)
            return True, None
        except TimelineException as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_available_dates(self, path: str) -> list[str]:
        """Get all available dates in timeline."""
        try:
            app = self._get_or_create_app(path)
            return app.get_available_dates()
        except Exception as e:
            print(f"Error getting available dates: {e}")
            return []

    def generate_images(
        self,
        config: ImageGenerationConfig,
        on_progress: Optional[ProgressCallback] = None,
        on_file_loading: Optional[Callable[[bool], None]] = None,
    ) -> GenerationResult:
        """Generate map images for date range.

        Args:
            config: ImageGenerationConfig with generation parameters
            on_progress: Optional progress callback (completed, total)
            on_file_loading: Optional callback when file loading completes
        """
        try:
            app = self._get_or_create_app(config.timeline_path, config.output_dir)
            self._load_cache_if_needed(app, config, on_file_loading)

            if config.single_image:
                return self._process_single_image_generation(app, config, on_progress)
            else:
                return self._process_batch_generation(app, config, on_progress)

        except Exception as e:
            return GenerationResult(
                success=False,
                output_dir=Path(config.output_dir),
                image_count=0,
                error_message=str(e),
            )

    def _cache_needs_reload(self, app: TimelineApp, config: ImageGenerationConfig) -> bool:
        """Check if cache needs to be reloaded for this timeline."""
        cache = app.processor._parser._timeline_cache
        if cache.file_path is None or cache.data is None:
            return True

        json_path_normalized = str(Path(config.timeline_path).resolve())
        cache_path_normalized = str(Path(cache.file_path).resolve())
        return json_path_normalized != cache_path_normalized

    def _load_cache_if_needed(
        self,
        app: TimelineApp,
        config: ImageGenerationConfig,
        on_file_loading: Optional[Callable[[bool], None]],
    ) -> None:
        """Load cache if not already loaded for this timeline."""
        cache = app.processor._parser._timeline_cache

        if self._cache_needs_reload(app, config):
            try:
                cache.load_file(config.timeline_path)
            except Exception:
                pass

        is_from_cache = self._get_cache_source(cache)
        if on_file_loading:
            on_file_loading(is_from_cache)

    @staticmethod
    def _get_cache_source(cache) -> bool:
        """Check if cache was loaded from session."""
        try:
            return cache.cache_source == "session"
        except Exception:
            return False

    def _process_single_image_generation(
        self,
        app: TimelineApp,
        config: ImageGenerationConfig,
        on_progress: Optional[ProgressCallback],
    ) -> GenerationResult:
        """Process single image generation."""
        self._apply_config_to_app(app, config)
        result = app.process_date_range_single_image(
            start_date=config.start_date,
            end_date=config.end_date,
            days=config.days,
            on_progress=on_progress,
        )
        if result.was_successful():
            return GenerationResult(
                success=True,
                output_dir=Path(config.output_dir),
                image_count=1,
            )
        error_msg = result.error_message or "Unknown error"
        error = f"Failed to generate combined image: {error_msg}"
        return GenerationResult(
            success=False,
            output_dir=Path(config.output_dir),
            image_count=0,
            error_message=error,
        )

    def _build_batch_result(
        self, config: ImageGenerationConfig, results: list, image_count: int
    ) -> GenerationResult:
        """Build GenerationResult from batch processing results."""
        failed_dates = [r.date for r in results if not r.was_successful()]
        if not failed_dates:
            return GenerationResult(
                success=True, output_dir=Path(config.output_dir), image_count=image_count
            )

        error_details = self._format_failed_dates(failed_dates)
        error = f"Generated {image_count} of {len(results)} images. Failed dates: {error_details}"
        return GenerationResult(
            success=False,
            output_dir=Path(config.output_dir),
            image_count=image_count,
            error_message=error,
        )

    def _process_batch_generation(
        self,
        app: TimelineApp,
        config: ImageGenerationConfig,
        on_progress: Optional[ProgressCallback],
    ) -> GenerationResult:
        """Process batch generation."""
        self._apply_config_to_app(app, config)
        results = app.process_date_range(
            start_date=config.start_date,
            end_date=config.end_date,
            days=config.days,
            on_progress=on_progress,
        )
        image_count = sum(1 for r in results if r.was_successful())
        return self._build_batch_result(config, results, image_count)

    @staticmethod
    def _apply_config_to_app(app: TimelineApp, config: ImageGenerationConfig) -> None:
        """Apply GUI config settings to TimelineApp's render config.

        Args:
            app: TimelineApp instance
            config: ImageGenerationConfig with user-selected settings
        """
        app.config.image_width = config.image_width
        app.config.image_height = config.image_height
        app.config.add_place_names = config.add_place_names

    @staticmethod
    def _format_failed_dates(failed_dates: list[str]) -> str:
        """Format failed dates for error message."""
        error_details = ", ".join(failed_dates[:5])
        if len(failed_dates) > 5:
            error_details += f" (and {len(failed_dates) - 5} more)"
        return error_details

    def clear_cache(self) -> None:
        """Clear any cached data."""
        if self._app:
            self._app.clear_caches()

    def _get_or_create_app(self, json_path: str, output_dir: str = "output") -> TimelineApp:
        """Get or create TimelineApp instance (caches for session).

        This keeps the app instance alive for the session, reusing it
        across multiple operations for efficiency. JSON is cached by json_path;
        output_dir can change without invalidating the cache since it only
        affects where images are saved, not JSON parsing.

        Args:
            json_path: Path to Timeline.json file
            output_dir: Output directory for images
        """
        # Only recreate app if json_path changes; output_dir can change without losing cache
        if self._app is None or self._app.json_path != json_path:
            self._app = TimelineApp(json_path, output_dir=output_dir, validate=True)
        else:
            # Update output_dir if it changed (doesn't invalidate JSON cache)
            output_dir_path = Path(output_dir)
            if self._app.output_dir != output_dir_path:
                self._app.output_dir = output_dir_path
                self._app.output_dir.mkdir(exist_ok=True, parents=True)
        return self._app
