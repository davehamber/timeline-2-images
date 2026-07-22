# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Application entry point for PySide6 GUI."""

import sys

from PySide6.QtWidgets import QApplication

from timeline_2_images.gui.main_window import TimelineWindow


def main() -> None:
    """Launch the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Timeline 2 Images")
    app.setApplicationVersion("0.3.0")

    window = TimelineWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
