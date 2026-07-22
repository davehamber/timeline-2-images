# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Settings panel for image generation options."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QCheckBox,
)
from timeline_2_images.config.render_configuration import MIN_IMAGE_SIZE, MAX_IMAGE_SIZE


class SettingsPanel(QWidget):
    """Panel for image generation settings."""

    def __init__(self):
        """Initialize settings panel."""
        super().__init__()
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Image size (width and height)
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Image Size:"))

        size_layout.addWidget(QLabel("W:"))
        self._width_spin = QSpinBox()
        self._width_spin.setMinimum(1)
        self._width_spin.setMaximum(MAX_IMAGE_SIZE)
        self._width_spin.setValue(500)
        self._width_spin.editingFinished.connect(self._on_width_finished)
        self._width_spin.setToolTip(
            f"Image width in pixels ({MIN_IMAGE_SIZE}-{MAX_IMAGE_SIZE})\n"
            "Larger values produce higher quality but take longer to render"
        )
        size_layout.addWidget(self._width_spin)
        size_layout.addWidget(QLabel("px"))

        size_layout.addWidget(QLabel("H:"))
        self._height_spin = QSpinBox()
        self._height_spin.setMinimum(1)
        self._height_spin.setMaximum(MAX_IMAGE_SIZE)
        self._height_spin.setValue(500)
        self._height_spin.editingFinished.connect(self._on_height_finished)
        self._height_spin.setToolTip(
            f"Image height in pixels ({MIN_IMAGE_SIZE}-{MAX_IMAGE_SIZE})\n"
            "Larger values produce higher quality but take longer to render"
        )
        size_layout.addWidget(self._height_spin)
        size_layout.addWidget(QLabel("px"))

        size_layout.addStretch()
        layout.addLayout(size_layout)

        # Checkboxes
        self._place_names_check = QCheckBox("Add place names")
        self._place_names_check.setChecked(True)
        self._place_names_check.setToolTip(
            "When enabled, maps will include the names of start and end locations\n"
            "Uses reverse geocoding to look up place names (requires internet)"
        )
        layout.addWidget(self._place_names_check)

        self._single_image_check = QCheckBox("Single combined image")
        self._single_image_check.setChecked(False)
        self._single_image_check.setToolTip(
            "When enabled, generates one large map with all routes from the date range\n"
            "When disabled, generates individual maps for each day"
        )
        layout.addWidget(self._single_image_check)

    def _on_width_finished(self) -> None:
        """Handle image width editing finished - clamp to valid range on focus loss."""
        value = self._width_spin.value()
        if value < MIN_IMAGE_SIZE:
            self._width_spin.setValue(MIN_IMAGE_SIZE)
        elif value > MAX_IMAGE_SIZE:
            self._width_spin.setValue(MAX_IMAGE_SIZE)

    def _on_height_finished(self) -> None:
        """Handle image height editing finished - clamp to valid range on focus loss."""
        value = self._height_spin.value()
        if value < MIN_IMAGE_SIZE:
            self._height_spin.setValue(MIN_IMAGE_SIZE)
        elif value > MAX_IMAGE_SIZE:
            self._height_spin.setValue(MAX_IMAGE_SIZE)

    def get_image_size(self) -> tuple[int, int]:
        """Get selected image size (width, height)."""
        return (self._width_spin.value(), self._height_spin.value())

    def get_add_place_names(self) -> bool:
        """Get add place names setting."""
        return self._place_names_check.isChecked()

    def get_single_image(self) -> bool:
        """Get single image setting."""
        return self._single_image_check.isChecked()
