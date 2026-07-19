# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Adapter: Converts TimelineApp to GUI's ITimelineProcessor interface.

This adapter encapsulates the core library so the GUI layer never
directly depends on TimelineApp or other core implementation details.
"""

from pathlib import Path
from typing import Optional

from timeline_2_images.app import TimelineApp
from timeline_2_images.exceptions import TimelineException, ValidationError
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
        except (ValidationError, TimelineException) as e:
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
    ) -> GenerationResult:
        """Generate map images for date range."""
        try:
            app = self._get_or_create_app(config.timeline_path)

            # Determine which method to use based on config
            if config.single_image:
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
                else:
                    error = f"Failed to generate combined image: {result.error or 'Unknown error'}"
                    return GenerationResult(
                        success=False,
                        output_dir=Path(config.output_dir),
                        image_count=0,
                        error_message=error,
                    )
            else:
                results = app.process_date_range(
                    start_date=config.start_date,
                    end_date=config.end_date,
                    days=config.days,
                    on_progress=on_progress,
                )
                success = all(r.was_successful() for r in results)
                image_count = sum(1 for r in results if r.was_successful())

                if success:
                    return GenerationResult(
                        success=True,
                        output_dir=Path(config.output_dir),
                        image_count=image_count,
                    )
                else:
                    # Collect error details for failed dates
                    failed_dates = [r.date for r in results if not r.was_successful()]
                    error_details = ", ".join(failed_dates[:5])  # Show first 5 failed dates
                    if len(failed_dates) > 5:
                        error_details += f" (and {len(failed_dates) - 5} more)"

                    error = (
                        f"Generated {image_count} of {len(results)} images. "
                        f"Failed dates: {error_details}"
                    )
                    return GenerationResult(
                        success=False,
                        output_dir=Path(config.output_dir),
                        image_count=image_count,
                        error_message=error,
                    )

        except Exception as e:
            return GenerationResult(
                success=False,
                output_dir=Path(config.output_dir),
                image_count=0,
                error_message=str(e),
            )

    def clear_cache(self) -> None:
        """Clear any cached data."""
        if self._app:
            self._app.clear_caches()

    def _get_or_create_app(self, json_path: str) -> TimelineApp:
        """Get or create TimelineApp instance (caches for session).

        This keeps the app instance alive for the session, reusing it
        across multiple operations for efficiency.
        """
        if self._app is None or self._app.json_path != json_path:
            self._app = TimelineApp(json_path, validate=True)
        return self._app
