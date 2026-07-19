# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Main application window for timeline-2-images GUI."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)

from timeline_2_images import __version__
from timeline_2_images.gui.models import TimelineProcessorAdapter, ImageGenerationConfig
from timeline_2_images.gui.presenter import TimelineGeneratorPresenter
from timeline_2_images.gui.settings_manager import SettingsManager
from timeline_2_images.gui.widgets.file_selector import FileSelector
from timeline_2_images.gui.widgets.date_range_panel import DateRangePanel
from timeline_2_images.gui.widgets.settings_panel import SettingsPanel
from timeline_2_images.gui.widgets.progress_panel import ProgressPanel


class TimelineWindow(QMainWindow):
    """Main GUI window for timeline image generation."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("Timeline 2 Images")
        self.setGeometry(100, 100, 520, 600)

        # Initialize settings manager
        self._settings_manager = SettingsManager()

        # Initialize presenter with adapter
        self._presenter = TimelineGeneratorPresenter(TimelineProcessorAdapter())
        self._register_callbacks()

        # Create UI
        self._create_ui()

        # Load saved settings
        self._load_settings()

    def _create_ui(self) -> None:
        """Create the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # ===== File Selector =====
        file_label = QLabel("Timeline File:")
        file_label.setStyleSheet("font-weight: bold;")
        self._file_selector = FileSelector(self._presenter)
        self._file_selector.on_file_selected(self._on_file_selected_in_selector)
        main_layout.addWidget(file_label)
        main_layout.addWidget(self._file_selector)

        # ===== Date Range Panel =====
        date_label = QLabel("Date Range")
        date_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self._date_range_panel = DateRangePanel()
        main_layout.addWidget(date_label)
        main_layout.addWidget(self._date_range_panel)

        # ===== Settings Panel =====
        settings_label = QLabel("Image Settings")
        settings_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self._settings_panel = SettingsPanel()
        main_layout.addWidget(settings_label)
        main_layout.addWidget(self._settings_panel)

        # ===== Progress Panel =====
        progress_label = QLabel("Output Directory:")
        self._output_dir_label = QLabel("(select a timeline file)")
        main_layout.addWidget(progress_label)
        main_layout.addWidget(self._output_dir_label)

        self._progress_panel = ProgressPanel()
        main_layout.addWidget(self._progress_panel)

        # ===== Buttons =====
        button_layout = QHBoxLayout()
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._generate_btn = QPushButton("Generate Maps")
        self._generate_btn.clicked.connect(self._on_generate)
        self._generate_btn.setEnabled(False)

        button_layout.addStretch()
        button_layout.addWidget(self._cancel_btn)
        button_layout.addWidget(self._generate_btn)
        main_layout.addLayout(button_layout)

        # ===== Footer =====
        footer_layout = QHBoxLayout()
        description = QLabel("Generate daily route maps from Google Timeline")
        description.setStyleSheet("color: #999999; font-size: 9pt;")
        metadata = QLabel(f"EUPL-1.2, Copyright (c) 2026 David Hamber - v{__version__}")
        metadata.setStyleSheet("color: #999999; font-size: 9pt;")
        footer_layout.addWidget(description)
        footer_layout.addStretch()
        footer_layout.addWidget(metadata)
        main_layout.addLayout(footer_layout)

    def _register_callbacks(self) -> None:
        """Register presenter callbacks."""
        self._presenter.on_validation_result(self._on_validation_result)
        self._presenter.on_available_dates(self._on_available_dates)
        self._presenter.on_generation_complete(self._on_generation_complete)
        self._presenter.on_file_loading(self._on_file_loading)

    def _on_validation_result(self, is_valid: bool, error: Optional[str]) -> None:
        """Handle file validation result."""
        if is_valid:
            self._generate_btn.setEnabled(True)
        else:
            self._generate_btn.setEnabled(False)
            if error:
                QMessageBox.warning(self, "Invalid Timeline File", error)

    def _on_file_loading(self, is_loading: bool) -> None:
        """Handle file loading state.

        Args:
            is_loading: True if file is being loaded, False if complete
        """
        self._file_selector.set_loading(is_loading)

    def _on_file_selected_in_selector(self, file_path: str) -> None:
        """Handle file selection in file selector.

        Args:
            file_path: Path to selected file
        """
        # Enable generate button when a valid file is selected
        if Path(file_path).is_file():
            self._generate_btn.setEnabled(True)
        else:
            self._generate_btn.setEnabled(False)

    def _on_available_dates(self, dates: list[str]) -> None:
        """Handle available dates loaded."""
        self._date_range_panel.set_available_dates(dates)

    def _on_generation_complete(self, result) -> None:
        """Handle generation completion."""
        self._progress_panel.set_complete(result)

        # Re-enable Generate button if a file is still selected
        timeline_path = self._file_selector.get_selected_path()
        if timeline_path and self._file_selector.is_file_valid():
            self._generate_btn.setEnabled(True)

        if result.success:
            QMessageBox.information(
                self,
                "Success",
                f"Generated {result.image_count} images in:\n{result.output_dir}",
            )
        else:
            QMessageBox.critical(self, "Generation Failed", result.error_message or "Unknown error")

    def _load_settings(self) -> None:
        """Load saved settings from previous session."""
        # Load image size
        image_size = self._settings_manager.get("image_size", 500)
        self._settings_panel._size_spin.setValue(image_size)

        # Load output directory
        output_dir = self._settings_manager.get("output_dir")
        if output_dir:
            self._settings_panel._output_input.setText(output_dir)
            self._settings_panel._output_dir = output_dir

        # Load place names setting
        add_place_names = self._settings_manager.get("add_place_names", True)
        self._settings_panel._place_names_check.setChecked(add_place_names)

        # Load single image setting
        single_image = self._settings_manager.get("single_image", False)
        self._settings_panel._single_image_check.setChecked(single_image)

        # Load date range settings
        date_range_mode = self._settings_manager.get("date_range_mode", "days")
        if date_range_mode == "range":
            self._date_range_panel._range_radio.setChecked(True)
            start_date = self._settings_manager.get("date_range_start")
            end_date = self._settings_manager.get("date_range_end")
            if start_date and end_date:
                from PyQt6.QtCore import QDate
                self._date_range_panel._start_date.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
                self._date_range_panel._end_date.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))
        else:
            self._date_range_panel._days_radio.setChecked(True)
            days = self._settings_manager.get("date_range_days", 14)
            self._date_range_panel._days_spin.setValue(days)

        # Load Timeline file path (just restore the path, don't load the file)
        timeline_path = self._settings_manager.get("timeline_file_path")
        if timeline_path:
            from pathlib import Path
            if Path(timeline_path).exists():
                self._file_selector._selected_path = timeline_path
                self._file_selector._path_input.setText(timeline_path)
                # Enable Generate button since file path is valid
                self._on_file_selected_in_selector(timeline_path)

    def _save_settings(self) -> None:
        """Save current settings for next session."""
        # Get date range settings
        start_date, end_date, days = self._date_range_panel.get_date_range()
        date_range_mode = "range" if start_date and end_date else "days"

        settings = {
            "image_size": self._settings_panel.get_image_size(),
            "output_dir": self._settings_panel.get_output_dir(),
            "add_place_names": self._settings_panel.get_add_place_names(),
            "single_image": self._settings_panel.get_single_image(),
            "date_range_mode": date_range_mode,
            "date_range_days": days if date_range_mode == "days" else self._date_range_panel._days_spin.value(),
            "date_range_start": start_date,
            "date_range_end": end_date,
            "timeline_file_path": self._file_selector.get_selected_path(),
        }
        self._settings_manager.save_settings(settings)

    def closeEvent(self, event) -> None:
        """Handle window close event - save settings.

        Args:
            event: Close event
        """
        self._save_settings()
        super().closeEvent(event)

    def _on_generate(self) -> None:
        """Handle generate button click."""
        timeline_path = self._file_selector.get_selected_path()
        if not timeline_path:
            QMessageBox.warning(self, "No File", "Please select a Timeline.json file")
            return

        output_dir = self._settings_panel.get_output_dir()
        image_size = self._settings_panel.get_image_size()
        add_place_names = self._settings_panel.get_add_place_names()
        single_image = self._settings_panel.get_single_image()

        start_date, end_date, days = self._date_range_panel.get_date_range()

        self._progress_panel.start()
        self._generate_btn.setEnabled(False)

        self._presenter.handle_generate_clicked(
            timeline_path=timeline_path,
            output_dir=output_dir,
            image_size=image_size,
            add_place_names=add_place_names,
            single_image=single_image,
            start_date=start_date,
            end_date=end_date,
            days=days,
            on_progress=self._progress_panel.update_progress,
            on_file_loading=self._progress_panel.set_loading_file,
        )

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.close()
