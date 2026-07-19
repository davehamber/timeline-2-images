# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Worker thread for image generation to prevent UI blocking."""

from PyQt6.QtCore import QThread, pyqtSignal

from timeline_2_images.gui.models.interfaces import (
    ITimelineProcessor,
    ImageGenerationConfig,
    GenerationResult,
    ProgressCallback,
)


class GenerationWorker(QThread):
    """Worker thread for async image generation."""

    generation_complete = pyqtSignal(GenerationResult)

    def __init__(
        self,
        processor: ITimelineProcessor,
        config: ImageGenerationConfig,
        on_progress: ProgressCallback | None = None,
        on_file_loading: callable | None = None,
    ):
        """Initialize worker.

        Args:
            processor: ITimelineProcessor implementation
            config: ImageGenerationConfig with generation parameters
            on_progress: Optional progress callback
            on_file_loading: Optional file loading callback (is_cached)
        """
        super().__init__()
        self.processor = processor
        self.config = config
        self.on_progress = on_progress
        self.on_file_loading = on_file_loading

    def run(self) -> None:
        """Run worker thread - generate images."""
        try:
            result = self.processor.generate_images(
                self.config,
                on_progress=self.on_progress,
                on_file_loading=self.on_file_loading,
            )
            self.generation_complete.emit(result)
        except Exception as e:
            self.generation_complete.emit(
                GenerationResult(
                    success=False,
                    output_dir=self.config.output_dir,
                    image_count=0,
                    error_message=f"Generation failed: {str(e)}",
                )
            )
