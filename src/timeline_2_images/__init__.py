# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Daily Timeline Images - Generate daily route maps from Google Timeline exports.

This package provides both:
- A library API for integrating timeline processing into other applications
- A command-line tool for generating route maps

Library Usage:
    from timeline_2_images.app import TimelineApp
    from timeline_2_images.config import RenderConfiguration

    config = RenderConfiguration(image_size=800)
    app = TimelineApp("Timeline.json", output_dir="maps", config=config)
    results = app.process_date_range(start_date="2026-06-01", days=30)

Command-Line Usage:
    timeline-2-images Timeline.json --start-date 2026-06-01 --days 30
"""

from timeline_2_images.app import TimelineApp
from timeline_2_images.config import RenderConfiguration, DateRangeQuery
from timeline_2_images.models import Segment, ProcessedSegment, RenderResult
from timeline_2_images.main import main

__version__ = "0.2.0"

__all__ = [
    "TimelineApp",
    "RenderConfiguration",
    "DateRangeQuery",
    "Segment",
    "ProcessedSegment",
    "RenderResult",
    "main",
]
