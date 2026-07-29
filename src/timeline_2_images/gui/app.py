# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Application entry point for PySide6 GUI."""

import sys
import time
from pathlib import Path

START_TIME = time.time()
LOG_FILE = Path.home() / ".timeline2images-startup.log"


def log_time(message: str) -> None:
    """Log elapsed time since startup to file and stdout."""
    elapsed = time.time() - START_TIME
    msg = f"[{elapsed:.2f}s] {message}"
    print(msg, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


log_time("Python started - importing PySide6...")
from PySide6.QtWidgets import QApplication

log_time("PySide6 imported")

log_time("Importing TimelineWindow...")
from timeline_2_images.gui.main_window import TimelineWindow

log_time("TimelineWindow imported")


def main() -> None:
    """Launch the GUI application."""
    log_time("main() started")

    log_time("Creating QApplication...")
    app = QApplication(sys.argv)
    log_time("QApplication created")

    app.setApplicationName("Timeline 2 Images")
    app.setApplicationVersion("0.3.0")

    _apply_dark_stylesheet(app)
    log_time("Dark theme applied")
    log_time("App configured")

    log_time("Creating TimelineWindow...")
    window = TimelineWindow()
    log_time("TimelineWindow created and initialized")

    log_time("Showing window...")
    window.show()
    log_time("Window shown - entering event loop")

    sys.exit(app.exec())


def _apply_dark_stylesheet(app: QApplication) -> None:
    """Apply dark theme stylesheet to all widgets."""
    dark_stylesheet = """
    QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QLabel {
        color: #ffffff;
    }
    QPushButton {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        padding: 4px;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
        border: 1px solid #4d4d4d;
    }
    QPushButton:pressed {
        background-color: #1d1d1d;
    }
    QLineEdit, QSpinBox, QDateEdit {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 3px;
        padding: 3px;
    }
    QCalendarWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QCalendarWidget QAbstractItemView {
        background-color: #2d2d2d;
        color: #ffffff;
        alternate-background-color: #3d3d3d;
    }
    QCalendarWidget QAbstractItemView:selected {
        background-color: #0066cc;
        color: #ffffff;
    }
    QCalendarWidget QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QCalendarWidget QToolButton {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
    }
    QCalendarWidget QSpinBox {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
    }
    QRadioButton {
        color: #ffffff;
    }
    QMessageBox {
        background-color: #1e1e1e;
    }
    QMessageBox QLabel {
        color: #ffffff;
    }
    QMessageBox QPushButton {
        min-width: 60px;
    }
    QFileDialog {
        background-color: #1e1e1e;
    }
    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #4d4d4d;
        border-radius: 6px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #5d5d5d;
    }
    QScrollBar:horizontal {
        background-color: #1e1e1e;
        height: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:horizontal {
        background-color: #4d4d4d;
        border-radius: 6px;
        min-width: 20px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #5d5d5d;
    }
    """
    app.setStyleSheet(dark_stylesheet)


if __name__ == "__main__":
    main()
