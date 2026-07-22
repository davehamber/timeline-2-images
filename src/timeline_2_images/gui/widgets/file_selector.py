# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""File selector widget for choosing Timeline.json."""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel


class FileSelector(QWidget):
    """Widget for selecting Timeline.json file."""

    def __init__(self, presenter):
        """Initialize file selector.

        Args:
            presenter: TimelineGeneratorPresenter instance
        """
        super().__init__()
        self._presenter = presenter
        self._selected_path: Optional[str] = None
        self._on_file_selected = None

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText("/path/to/Timeline.json")
        self._path_input.setReadOnly(True)
        layout.addWidget(self._path_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(browse_btn, 0)

        self._loading_label = QLabel("")
        self._loading_label.setStyleSheet("color: #0066cc; font-size: 9pt;")
        layout.addWidget(self._loading_label, 0)

    def _on_browse(self) -> None:
        """Handle browse button click."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Timeline.json",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            self._selected_path = file_path
            self._path_input.setText(file_path)
            # Notify that a file has been selected
            if self._on_file_selected:
                self._on_file_selected(file_path)

    def get_selected_path(self) -> Optional[str]:
        """Get the selected file path."""
        return self._selected_path

    def set_loading(self, is_loading: bool) -> None:
        """Set loading state.

        Args:
            is_loading: True to show loading indicator, False to hide
        """
        if is_loading:
            self._loading_label.setText("⟳ Loading file...")
        else:
            self._loading_label.setText("")

    def on_file_selected(self, callback) -> None:
        """Register callback when file is selected.

        Args:
            callback: Function to call with file path when file is selected
        """
        self._on_file_selected = callback

    def is_file_valid(self) -> bool:
        """Check if selected file is valid.

        Returns:
            True if file exists and is readable
        """
        if not self._selected_path:
            return False
        return Path(self._selected_path).is_file()
