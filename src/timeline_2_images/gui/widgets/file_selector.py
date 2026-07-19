# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""File selector widget for choosing Timeline.json."""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog


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

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText("/path/to/Timeline.json")
        self._path_input.setReadOnly(True)
        layout.addWidget(self._path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(browse_btn)

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
            self._presenter.handle_file_selected(file_path)

    def get_selected_path(self) -> Optional[str]:
        """Get the selected file path."""
        return self._selected_path
