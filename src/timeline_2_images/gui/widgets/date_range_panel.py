# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Date range selection panel."""

from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QDateEdit,
    QLabel,
)
from PyQt6.QtCore import QDate


class DateRangePanel(QWidget):
    """Panel for selecting date range for processing."""

    def __init__(self):
        """Initialize date range panel."""
        super().__init__()
        self._available_dates: list[str] = []
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Last N days option
        days_layout = QHBoxLayout()
        self._days_radio = QRadioButton("Last N days:")
        self._days_radio.setChecked(True)
        self._days_radio.setToolTip("Process the most recent N days that have location data")
        self._days_spin = QSpinBox()
        self._days_spin.setValue(14)
        self._days_spin.setMinimum(1)
        self._days_spin.setMaximum(365)
        self._days_spin.setToolTip(
            "Number of days to process, counting backwards from the most recent data"
        )
        days_layout.addWidget(self._days_radio)
        days_layout.addWidget(self._days_spin)
        days_layout.addWidget(QLabel("days"))
        days_layout.addStretch()
        layout.addLayout(days_layout)

        # Specific date range option
        range_layout = QVBoxLayout()
        self._range_radio = QRadioButton("Specific range:")
        self._range_radio.setToolTip(
            "Process all days between a specific start and end date (inclusive)"
        )
        range_layout.addWidget(self._range_radio)

        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel("From:"))
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        self._start_date.setDisplayFormat("yyyy-MM-dd")
        self._start_date.setEnabled(False)
        self._start_date.setToolTip("Start date (inclusive) - click calendar icon to select")
        dates_layout.addWidget(self._start_date)

        dates_layout.addWidget(QLabel("To:"))
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._end_date.setDisplayFormat("yyyy-MM-dd")
        self._end_date.setEnabled(False)
        self._end_date.setToolTip("End date (inclusive) - click calendar icon to select")
        dates_layout.addWidget(self._end_date)
        dates_layout.addStretch()

        range_layout.addLayout(dates_layout)
        layout.addLayout(range_layout)

        # Connect radio buttons
        group = QButtonGroup()
        group.addButton(self._days_radio)
        group.addButton(self._range_radio)

        self._days_radio.toggled.connect(self._on_days_toggled)
        self._range_radio.toggled.connect(self._on_range_toggled)

        # Connect date changes for auto-adjustment
        self._start_date.dateChanged.connect(self._on_start_date_changed)
        self._end_date.dateChanged.connect(self._on_end_date_changed)

    def _on_days_toggled(self, checked: bool) -> None:
        """Handle days radio button toggle."""
        self._days_spin.setEnabled(checked)

    def _on_range_toggled(self, checked: bool) -> None:
        """Handle range radio button toggle."""
        self._start_date.setEnabled(checked)
        self._end_date.setEnabled(checked)

    def _on_start_date_changed(self) -> None:
        """Handle start date change - adjust end date if needed."""
        if self._start_date.date() > self._end_date.date():
            self._end_date.blockSignals(True)
            self._end_date.setDate(self._start_date.date())
            self._end_date.blockSignals(False)

    def _on_end_date_changed(self) -> None:
        """Handle end date change - adjust start date if needed."""
        if self._end_date.date() < self._start_date.date():
            self._start_date.blockSignals(True)
            self._start_date.setDate(self._end_date.date())
            self._start_date.blockSignals(False)

    def set_available_dates(self, dates: list[str]) -> None:
        """Set available dates from timeline."""
        self._available_dates = dates
        if dates:
            # Set date range spinbox based on available dates
            max_days = len(dates)
            self._days_spin.setMaximum(max_days)

    def get_date_range(self) -> Tuple[Optional[str], Optional[str], int]:
        """Get selected date range.

        Returns:
            Tuple of (start_date, end_date, days)
            - If using last N days: (None, None, days)
            - If using specific range: (start_date, end_date, 0)
        """
        if self._days_radio.isChecked():
            return None, None, self._days_spin.value()
        else:
            start = self._start_date.date().toString("yyyy-MM-dd")
            end = self._end_date.date().toString("yyyy-MM-dd")
            return start, end, 0
