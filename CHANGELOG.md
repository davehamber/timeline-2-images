# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GUI architecture foundation (Phase 1): Proper layering for desktop interface
  - `gui/models/interfaces.py`: ITimelineProcessor interface (GUI depends on this)
  - `gui/models/timeline_adapter.py`: Adapter wrapping TimelineApp (decouples GUI from core)
  - `gui/presenter.py`: Controller layer handling user actions and state
  - `gui/widgets/`: Package for PyQt6 UI components (implementation in Phase 2)
- 11 comprehensive tests for GUI architecture ensuring proper decoupling
- GUI implementation (Phase 2): Complete PyQt6 desktop application
  - `gui/main_window.py`: TimelineWindow main application window with full layout
  - `gui/widgets/file_selector.py`: File picker widget with browse button
  - `gui/widgets/date_range_panel.py`: Date range selection (last N days or specific range)
  - `gui/widgets/settings_panel.py`: Image size, output directory, place names, single image options
  - `gui/widgets/progress_panel.py`: Progress bar and processing status display
  - `gui/app.py`: Application entry point for launching the desktop GUI
- PyQt6 as runtime dependency for cross-platform GUI support (Linux, macOS, Windows)
- Background threading for file loading to prevent UI freezing on large files
  - TimelineWorker: QThread for async file validation and date loading
  - File loading indicator in FileSelector showing "⟳ Loading file..." status
  - Responsive UI even with 60+ MB Timeline.json files
- Background threading for image generation to prevent UI freezing during processing
  - GenerationWorker: QThread for async image generation
  - Progress updates and real-time feedback during generation
  - Improved error reporting showing failed dates and success count
- GUI settings persistence between sessions
  - SettingsManager: Stores settings in ~/.cache/timeline-2-images/settings.json
  - Remembers: Timeline file path, image size, output directory, place names option, single image option
  - Also remembers date range settings: mode (last N days vs specific range), days value, start/end dates
  - Automatically saves settings when window closes
  - Restores all settings on app startup, including file loading and date range selection

### Fixed
- Date range validation now correctly handles specific date ranges without requiring days > 0
- Output directory setting now correctly used when generating images (was defaulting to project's output/ directory)
- Image size default now correctly set to 500 pixels (was showing 100 due to Qt spinbox initialization order)

### Removed
- SQLite segment caching (SegmentCache) - legacy optimization no longer needed
- `--clean-cache` CLI argument (was specific to SQLite cache)
- Unused `profile` CLI argument and parameter
- Broken `test_caches.py` test file

### Changed
- Simplified caching architecture: now uses only TimelineCache (in-memory) for JSON parsing
- Removed redundant segment indexing logic from SQLite cache
- DateRangeQuery validation: only validates days > 0 when days parameter will be used
- GUI default output directory changed from ~/maps to ~/Downloads for better UX
- Date picker format changed to ISO 8601 (yyyy-MM-dd) for consistency across platforms
- GUI defers Timeline.json parsing until Generate is clicked (faster startup and file selection, uses session-level JSON cache for efficiency)

## [0.3.0] - 2026-07-19

### Added
- Progress callback support in batch methods for real-time progress tracking
- `on_progress` parameter in `process_date_range()`, `process_date_range_bytes()`, and `process_date_range_single_image()`
- Progress tracking examples with tqdm integration in library usage documentation
- Specific exception types for programmatic error handling: `SegmentProcessingError`, `RenderingError`, `ValidationError`, `CacheError`
- Base `TimelineException` class for catching all timeline-related errors
- Exception chaining support for error context and debugging
- `CacheConfig` class for controlling in-memory caching behavior
- Cache size limits (1 MB - 8 GB) for predictable memory usage
- Cache configuration options: enable/disable caching, set max size, auto-clear on exit

---

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

[Unreleased]: https://github.com/yourusername/timeline-2-images/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/yourusername/timeline-2-images/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/timeline-2-images/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/timeline-2-images/releases/tag/v0.1.0
