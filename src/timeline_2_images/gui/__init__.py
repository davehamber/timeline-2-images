# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""GUI module for timeline-2-images.

Optional UI layer that provides a PyQt6 desktop interface to the core library.
This module has zero dependencies on the GUI from the core library.

The GUI architecture:
- Interfaces (models/interfaces.py): Define what the GUI needs
- Adapter (models/timeline_adapter.py): Wraps core library to implement interfaces
- Presenter (presenter.py): Controller layer, mediates GUI ↔ business logic
- Widgets (widgets/): PyQt6 UI components
"""
