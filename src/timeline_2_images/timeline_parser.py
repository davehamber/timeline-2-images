"""Internal timeline parser module (used by TimelineProcessor).

Note: New OOP code should use timeline_2_images.processors.TimelineProcessor instead.
This module is kept for backward compatibility and internal utilities.

Classes have been refactored into separate modules:
- TimelineCache → timeline_cache.py
- SegmentParser → segment_parser.py
- PointExtractor → point_extractor.py
- DateExtractor → date_extractor.py
- TimelineParserFacade → timeline_parser_facade.py
"""

# Re-export for backward compatibility
from timeline_2_images.timeline_cache import TimelineCache
from timeline_2_images.segment_parser import SegmentParser
from timeline_2_images.point_extractor import PointExtractor
from timeline_2_images.date_extractor import DateExtractor
from timeline_2_images.timeline_parser_facade import TimelineParserFacade

__all__ = [
    "TimelineCache",
    "SegmentParser",
    "PointExtractor",
    "DateExtractor",
    "TimelineParserFacade",
]
