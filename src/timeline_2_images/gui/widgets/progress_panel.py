# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Progress tracking panel for image generation."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel


class ProgressPanel(QWidget):
    """Panel showing progress of image generation."""

    def __init__(self):
        """Initialize progress panel."""
        super().__init__()
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(self._status_label)

        # Details label
        self._details_label = QLabel("")
        self._details_label.setStyleSheet("color: #999999; font-size: 8pt;")
        layout.addWidget(self._details_label)

    def start(self) -> None:
        """Start progress tracking."""
        self._progress_bar.setValue(0)
        self._status_label.setText("Processing...")
        self._details_label.setText("")

    def update_progress(self, completed: int, total: int) -> None:
        """Update progress.

        Args:
            completed: Number of items completed
            total: Total number of items to process
        """
        if total > 0:
            percentage = int((completed / total) * 100)
            self._progress_bar.setValue(percentage)
            self._status_label.setText(f"Processing: {completed}/{total} images")
            self._details_label.setText(f"{percentage}% complete")

    def set_complete(self, result) -> None:
        """Mark progress as complete.

        Args:
            result: GenerationResult with completion status
        """
        if result.success:
            self._progress_bar.setValue(100)
            self._status_label.setText(f"✓ Complete: {result.image_count} images generated")
            self._details_label.setText(f"Output: {result.output_dir}")
        else:
            self._progress_bar.setValue(0)
            self._status_label.setText("✗ Failed")
            self._details_label.setText(result.error_message or "Unknown error")
