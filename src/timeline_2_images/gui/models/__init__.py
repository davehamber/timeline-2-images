# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""GUI model layer - interfaces and adapters.

Provides:
- Interfaces that GUI depends on (ITimelineProcessor, etc.)
- Adapter that wraps core library to implement those interfaces
- Data models for GUI (ImageGenerationConfig, GenerationResult)
"""

from timeline_2_images.gui.models.interfaces import (
    ITimelineProcessor,
    ImageGenerationConfig,
    GenerationResult,
    ProgressCallback,
)
from timeline_2_images.gui.models.timeline_adapter import TimelineProcessorAdapter

__all__ = [
    "ITimelineProcessor",
    "ImageGenerationConfig",
    "GenerationResult",
    "ProgressCallback",
    "TimelineProcessorAdapter",
]
