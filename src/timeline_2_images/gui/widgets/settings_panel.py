# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Settings panel for image generation options."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
)
from timeline_2_images.config.render_configuration import MIN_IMAGE_SIZE, MAX_IMAGE_SIZE


class SettingsPanel(QWidget):
    """Panel for image generation settings."""

    def __init__(self):
        """Initialize settings panel."""
        super().__init__()
        self._output_dir = str(Path.home() / "Downloads")
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Image size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Image Size:"))
        self._size_spin = QSpinBox()
        self._size_spin.setMinimum(1)
        self._size_spin.setMaximum(MAX_IMAGE_SIZE)
        self._size_spin.setValue(500)
        self._size_spin.valueChanged.connect(self._on_size_changed)
        size_layout.addWidget(self._size_spin)
        size_layout.addWidget(QLabel("pixels"))
        size_layout.addStretch()
        layout.addLayout(size_layout)

        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self._output_input = QLineEdit()
        self._output_input.setText(self._output_dir)
        output_layout.addWidget(self._output_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_output)
        output_layout.addWidget(browse_btn)
        layout.addLayout(output_layout)

        # Checkboxes
        self._place_names_check = QCheckBox("Add place names")
        self._place_names_check.setChecked(True)
        layout.addWidget(self._place_names_check)

        self._single_image_check = QCheckBox("Single combined image")
        self._single_image_check.setChecked(False)
        layout.addWidget(self._single_image_check)

    def _on_size_changed(self, value: int) -> None:
        """Handle image size value changes - clamp to valid range.

        Args:
            value: The new spinbox value
        """
        if value < MIN_IMAGE_SIZE:
            self._size_spin.blockSignals(True)
            self._size_spin.setValue(MIN_IMAGE_SIZE)
            self._size_spin.blockSignals(False)
        elif value > MAX_IMAGE_SIZE:
            self._size_spin.blockSignals(True)
            self._size_spin.setValue(MAX_IMAGE_SIZE)
            self._size_spin.blockSignals(False)

    def _on_browse_output(self) -> None:
        """Handle output directory browse."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self._output_dir = dir_path
            self._output_input.setText(dir_path)

    def get_image_size(self) -> int:
        """Get selected image size."""
        return self._size_spin.value()

    def get_output_dir(self) -> str:
        """Get selected output directory."""
        return self._output_input.text() or self._output_dir

    def get_add_place_names(self) -> bool:
        """Get add place names setting."""
        return self._place_names_check.isChecked()

    def get_single_image(self) -> bool:
        """Get single image setting."""
        return self._single_image_check.isChecked()
