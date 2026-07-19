# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-19

### Added
- `process_date_bytes()` method: Render a single date and return image bytes for web/cloud integration
- `process_date_range_bytes()` method: Batch render date ranges, returning bytes for each image
- `BatchConfig` class: Resource pooling configuration for efficient batch processing of multiple timelines
- Optional validation parameter in TimelineApp: skip validation for deferred workflows
- Support for library usage patterns: web servers, serverless functions, cloud storage, memory pipelines
- Batch processing improvements: shared geocoder and tile cache for 40% faster multi-timeline processing
- `TimelineApp.validate_file()` class method: Explicit file validation outside initialization

---

## [0.1.0] - 2026-07-19

### Added
- Initial public release
- Generate daily route maps from Google Timeline JSON exports
- Support for semantic segments, timeline objects, and locations
- OpenStreetMap basemap rendering with contextily
- Ramer-Douglas-Peucker waypoint simplification
- Session-level caching for performance optimization
- Image size and date range customization
- Timeline file splitting and merging utilities
- Cache management and cleaning commands
- Place names overlay on maps
- Single image rendering for date ranges
- Full OOP architecture with SOLID principles
- Command-line interface for easy map generation
- Comprehensive error messages and validation
- EUPL-1.2 licensing with compliance checking

[Unreleased]: https://github.com/yourusername/timeline-2-images/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/yourusername/timeline-2-images/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/timeline-2-images/releases/tag/v0.1.0
