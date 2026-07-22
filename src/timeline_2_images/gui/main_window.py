# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Main application window for timeline-2-images GUI."""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt

from timeline_2_images import __version__
from timeline_2_images.gui.models import TimelineProcessorAdapter
from timeline_2_images.gui.models.interfaces import GenerationResult
from timeline_2_images.gui.presenter import TimelineGeneratorPresenter
from timeline_2_images.gui.settings_manager import SettingsManager
from timeline_2_images.gui.widgets.file_selector import FileSelector
from timeline_2_images.gui.widgets.date_range_panel import DateRangePanel
from timeline_2_images.gui.widgets.settings_panel import SettingsPanel
from timeline_2_images.gui.widgets.progress_panel import ProgressPanel


class PersistentTooltip(QFrame):
    """Custom persistent tooltip that stays visible on click."""

    def __init__(self, text: str, parent=None):
        """Initialize custom tooltip."""
        super().__init__(parent)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.ToolTip
        )
        self.setStyleSheet(
            "QFrame { background-color: #ffffdc; border: 1px solid #cccccc; "
            "border-radius: 3px; padding: 3px 5px; }"
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setStyleSheet("color: #000000; font-size: 10pt;")
        layout.addWidget(label)
        self.setLayout(layout)

    def show_at(self, pos):
        """Show tooltip at specified position."""
        self.move(pos)
        self.show()


class ClickableHelpLabel(QLabel):
    """QLabel that shows persistent tooltip on click."""

    _tooltip_widget = None  # Class variable for the persistent tooltip

    def __init__(self, text=""):
        """Initialize with text and store tooltip separately."""
        super().__init__(text)
        self._tooltip_text = ""

    def set_click_tooltip(self, text: str):
        """Set tooltip to show on click."""
        self._tooltip_text = text

    def mousePressEvent(self, event):
        """Show persistent tooltip when clicked."""
        if self._tooltip_text:
            # Hide any existing tooltip
            if ClickableHelpLabel._tooltip_widget:
                ClickableHelpLabel._tooltip_widget.hide()
                ClickableHelpLabel._tooltip_widget.deleteLater()

            # Create new tooltip (None parent = top-level window)
            tooltip = PersistentTooltip(self._tooltip_text, None)
            ClickableHelpLabel._tooltip_widget = tooltip
            # Position to the right of cursor with small offset (BEFORE show)
            cursor_pos = event.globalPosition().toPoint()
            cursor_pos.setX(cursor_pos.x() + 10)  # Right offset
            cursor_pos.setY(cursor_pos.y() + 10)  # Down offset
            ClickableHelpLabel._tooltip_widget.move(cursor_pos)
            ClickableHelpLabel._tooltip_widget.show()

    def leaveEvent(self, event):
        """Hide tooltip when mouse leaves widget."""
        if ClickableHelpLabel._tooltip_widget:
            ClickableHelpLabel._tooltip_widget.hide()
        super().leaveEvent(event)


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
        file_label_layout = QHBoxLayout()
        file_label = QLabel("Timeline File:")
        file_label.setStyleSheet("font-weight: bold;")
        file_label_layout.addWidget(file_label)
        file_help = ClickableHelpLabel("?")
        file_help.setStyleSheet("color: #0066cc; font-weight: bold; margin-top: 2px;")
        file_help.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        file_help.set_click_tooltip(
            "Export Timeline.json from your Android phone:\n"
            "1. Open Settings → Location → Location Services → Timeline\n"
            "2. Tap 'Export Timeline data'\n"
            "3. Authenticate with your device lock method\n"
            "4. Choose where to save the file\n"
            "5. Transfer the file to your computer"
        )
        file_label_layout.addWidget(file_help, 0, Qt.AlignmentFlag.AlignVCenter)
        file_label_layout.addStretch()
        file_container = QWidget()
        file_container.setLayout(file_label_layout)
        self._file_selector = FileSelector(self._presenter)
        self._file_selector.on_file_selected(self._on_file_selected_in_selector)
        self._file_selector.setToolTip("Select your exported Timeline.json file (JSON format)")
        main_layout.addWidget(file_container)
        main_layout.addWidget(self._file_selector)

        # ===== Date Range Panel =====
        date_label_layout = QHBoxLayout()
        date_label = QLabel("Date Range")
        date_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        date_label_layout.addWidget(date_label)
        date_help = ClickableHelpLabel("?")
        date_help.setStyleSheet("color: #0066cc; font-weight: bold; margin-top: 10px;")
        date_help.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        date_help.set_click_tooltip(
            "Choose how to select dates:\n"
            "• Last N days: Process the most recent N days with location data\n"
            "• Specific range: Process dates between start and end dates (inclusive)"
        )
        date_label_layout.addWidget(date_help, 0, Qt.AlignmentFlag.AlignVCenter)
        date_label_layout.addStretch()
        date_container = QWidget()
        date_container.setLayout(date_label_layout)
        self._date_range_panel = DateRangePanel()
        main_layout.addWidget(date_container)
        main_layout.addWidget(self._date_range_panel)

        # ===== Settings Panel =====
        settings_label_layout = QHBoxLayout()
        settings_label = QLabel("Image Settings")
        settings_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        settings_label_layout.addWidget(settings_label)
        settings_help = ClickableHelpLabel("?")
        settings_help.setStyleSheet("color: #0066cc; font-weight: bold; margin-top: 10px;")
        settings_help.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_help.set_click_tooltip(
            "Configure map rendering:\n"
            "• Width/Height: Image dimensions in pixels (200-4000 range)\n"
            "  Larger images take longer to render\n"
            "• Add place names: Show location names on maps\n"
            "• Single image: Combine all dates into one map"
        )
        settings_label_layout.addWidget(settings_help, 0, Qt.AlignmentFlag.AlignVCenter)
        settings_label_layout.addStretch()
        settings_container = QWidget()
        settings_container.setLayout(settings_label_layout)
        self._settings_panel = SettingsPanel()
        main_layout.addWidget(settings_container)
        main_layout.addWidget(self._settings_panel)

        # ===== Progress Panel =====
        output_label_layout = QHBoxLayout()
        output_label = QLabel("Output Directory:")
        output_label_layout.addWidget(output_label)
        output_help = ClickableHelpLabel("?")
        output_help.setStyleSheet("color: #0066cc; font-weight: bold; margin-top: 2px;")
        output_help.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        output_help.set_click_tooltip(
            "Destination folder for generated map images\nOrganized by date (e.g., 2024-01-15.jpg)"
        )
        output_label_layout.addWidget(output_help, 0, Qt.AlignmentFlag.AlignVCenter)
        output_label_layout.addStretch()
        output_container = QWidget()
        output_container.setLayout(output_label_layout)
        self._output_dir_label = QLabel("(select a timeline file)")
        main_layout.addWidget(output_container)
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

    def _load_image_size(self) -> None:
        """Load image width and height settings."""
        image_width = self._settings_manager.get("image_width", 500)
        image_height = self._settings_manager.get("image_height", 500)
        self._settings_panel._width_spin.setValue(image_width)
        self._settings_panel._height_spin.setValue(image_height)

    def _load_output_directory(self) -> None:
        """Load output directory setting."""
        output_dir = self._settings_manager.get("output_dir")
        if not output_dir:
            return
        self._settings_panel._output_input.setText(output_dir)
        self._settings_panel._output_dir = output_dir

    def _load_checkbox_settings(self) -> None:
        """Load place names and single image checkbox settings."""
        add_place_names = self._settings_manager.get("add_place_names", True)
        self._settings_panel._place_names_check.setChecked(add_place_names)

        single_image = self._settings_manager.get("single_image", False)
        self._settings_panel._single_image_check.setChecked(single_image)

    def _load_date_range_settings(self) -> None:
        """Load date range mode and dates."""
        date_range_mode = self._settings_manager.get("date_range_mode", "days")

        if date_range_mode == "range":
            self._date_range_panel._range_radio.setChecked(True)
            self._load_date_range_dates()
        else:
            self._date_range_panel._days_radio.setChecked(True)
            days = self._settings_manager.get("date_range_days", 14)
            self._date_range_panel._days_spin.setValue(days)

    def _load_date_range_dates(self) -> None:
        """Load start and end date settings."""
        from PyQt6.QtCore import QDate

        start_date = self._settings_manager.get("date_range_start")
        end_date = self._settings_manager.get("date_range_end")

        if start_date and end_date:
            self._date_range_panel._start_date.setDate(
                QDate.fromString(start_date, "yyyy-MM-dd")
            )
            self._date_range_panel._end_date.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))

    def _load_timeline_file_path(self) -> None:
        """Load and restore timeline file path."""
        timeline_path = self._settings_manager.get("timeline_file_path")
        if not timeline_path or not Path(timeline_path).exists():
            return

        self._file_selector._selected_path = timeline_path
        self._file_selector._path_input.setText(timeline_path)
        self._on_file_selected_in_selector(timeline_path)

    def _load_settings(self) -> None:
        """Load saved settings from previous session."""
        self._load_image_size()
        self._load_output_directory()
        self._load_checkbox_settings()
        self._load_date_range_settings()
        self._load_timeline_file_path()

    def _save_settings(self) -> None:
        """Save current settings for next session."""
        # Get date range settings
        start_date, end_date, days = self._date_range_panel.get_date_range()
        date_range_mode = "range" if start_date and end_date else "days"

        image_width, image_height = self._settings_panel.get_image_size()
        settings = {
            "image_width": image_width,
            "image_height": image_height,
            "output_dir": self._settings_panel.get_output_dir(),
            "add_place_names": self._settings_panel.get_add_place_names(),
            "single_image": self._settings_panel.get_single_image(),
            "date_range_mode": date_range_mode,
            "date_range_days": days
            if date_range_mode == "days"
            else self._date_range_panel._days_spin.value(),
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
        image_width, image_height = self._settings_panel.get_image_size()
        add_place_names = self._settings_panel.get_add_place_names()
        single_image = self._settings_panel.get_single_image()

        start_date, end_date, days = self._date_range_panel.get_date_range()

        self._progress_panel.start()
        self._generate_btn.setEnabled(False)

        self._presenter.handle_generate_clicked(
            timeline_path=timeline_path,
            output_dir=output_dir,
            image_width=image_width,
            image_height=image_height,
            add_place_names=add_place_names,
            single_image=single_image,
            start_date=start_date,
            end_date=end_date,
            days=days,
            on_progress=self._progress_panel.update_progress,
            on_file_loading=self._progress_panel.set_loading_file,
        )

    def _on_cancel(self) -> None:
        """Handle cancel button click - stop generation if running."""
        if self._presenter.is_generating():
            # If generation is active, cancel it immediately
            self._presenter.cancel_generation()
            # Show cancellation result immediately
            result = GenerationResult(
                success=False,
                output_dir=Path(self._settings_panel.get_output_dir() or ""),
                image_count=0,
                error_message="Generation cancelled by user",
            )
            self._progress_panel.set_complete(result)
            # Re-enable Generate button
            self._generate_btn.setEnabled(True)
