# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Worker thread for timeline operations to prevent UI blocking."""

from PySide6.QtCore import QThread, Signal


class TimelineWorker(QThread):
    """Worker thread for async timeline operations."""

    validation_complete = Signal(bool, str)  # success, error_message
    dates_loaded = Signal(list)  # list of date strings

    def __init__(self, processor, file_path: str):
        """Initialize worker.

        Args:
            processor: ITimelineProcessor implementation
            file_path: Path to Timeline.json file
        """
        super().__init__()
        self.processor = processor
        self.file_path = file_path

    def run(self) -> None:
        """Run worker thread - validate file and load dates."""
        try:
            # Validate file
            is_valid = self.processor.validate_file(self.file_path)
            if not is_valid:
                self.validation_complete.emit(False, "Invalid Timeline.json file")
                return

            # Get available dates
            dates = self.processor.get_available_dates(self.file_path)
            self.validation_complete.emit(True, "")
            self.dates_loaded.emit(dates)

        except Exception as e:
            self.validation_complete.emit(False, str(e))
