# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2026-07-22

### Fixed
- File picker width alignment: Timeline File and Output Directory pickers now have matching widths
- Vertical spacing between sections reduced by half for more compact layout
- Tooltip positioning: question mark help icons now appear next to cursor instead of centered in app
- Question mark icon vertical alignment with neighboring text labels
- Cancel button behavior: now stops image processing instead of closing the app
- UI freezing when Cancel button clicked during processing
- Loading label spacing in file selector preventing proper width matching
- Nested border appearance around section titles and icons in bordered boxes
- Progress status text color now matches percentage complete text color

### Changed
- Reorganized GUI layout: Output Directory section moved between Timeline File and Date Range sections
- Added bordered boxes around all four main sections (Timeline File, Output Directory, Date Range, Image Settings)
- Added bordered box around progress panel and buttons section
- Enhanced visual hierarchy with consistent spacing and borders throughout GUI
- Code quality: Refactored all Grade B complexity methods to Grade A (335+ Grade A methods total)

## [## [Unreleased]] - 2026-07-22

### Added
- Separate image width and height controls (image_width, image_height parameters)
  - CLI: New `--image-width` and `--image-height` flags for granular control
  - GUI: Two separate spinboxes for width and height independently
  - API: RenderConfiguration now has image_width and image_height attributes
- Backward compatibility: `--image-size` flag still works and sets both dimensions

### Changed
- Image dimension validation now applies to width and height separately (200-4000px range)
- GUI settings panel redesigned with dual spinboxes for width/height instead of single size
- All data models updated to use image_width and image_height instead of image_size

### Fixed
- Rectangular images now render without white borders (was forcing square aspect ratio)
- Bounds calculation now respects image width/height ratio instead of forcing square bounds
- Changed aspect ratio handling from 'equal' (square) to 'auto' (rectangular)

## [0.4.1] - 2026-07-22

### Added
- Image size validation: enforced 200-4000 pixel range with clear error messages
- CLI argument validation for `--image-size` and `--days` with helpful feedback

### Fixed
- GUI image size setting now properly applied to rendered images (was always using default 500px)
- Place names now appear in combined image mode (single image rendering)
- GUI spinbox now clamps out-of-range values to valid range instead of reverting to previous value
- Fixed tag v0.4.0 pointing to incorrect commit (now on main branch)

### Changed
- README.md: Updated with correct Google Timeline export process from Android device
- README.md: Improved Development section with complete quality tools reference
- README.md: Documented 200-4000 pixel image size range and performance impact
- Image size spinbox now uses constants (MIN_IMAGE_SIZE, MAX_IMAGE_SIZE) from configuration
- TimelineProcessorAdapter now applies GUI config (image_size, add_place_names) before rendering

## [0.4.0] - 2026-07-20

### Changed
- Reduced GUI window size and removed excessive empty space (more compact layout)
- GUI architecture foundation (Phase 1): Proper layering for desktop interface
  - `gui/models/interfaces.py`: ITimelineProcessor interface (GUI depends on this)
  - `gui/models/timeline_adapter.py`: Adapter wrapping TimelineApp (decouples GUI from core)
  - `gui/presenter.py`: Controller layer handling user actions and state
  - `gui/widgets/`: Package for PyQt6 UI components (implementation in Phase 2)
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
- Simplified caching architecture: now uses only TimelineCache (in-memory) for JSON parsing
- Removed redundant segment indexing logic from SQLite cache
- DateRangeQuery validation: only validates days > 0 when days parameter will be used
- GUI default output directory changed from ~/maps to ~/Downloads for better UX
- Date picker format changed to ISO 8601 (yyyy-MM-dd) for consistency across platforms
- GUI defers Timeline.json parsing until Generate is clicked (faster startup and file selection)
- Cache usage feedback in progress panel
  - Shows "Loading file (parsing JSON)..." for first-time file loads from disk
  - Shows "Loading file (using cache)..." when reusing cached file from current session
  - Session-level in-memory cache for multiple operations in same app session
- Optimized date extraction: Use datetime.fromisoformat instead of pd.to_datetime

### Fixed
- Code quality improvements (Grade A cyclomatic complexity across all methods)
  - Refactored TimelineProcessorAdapter.generate_images from Grade C to Grade A complexity
  - Extracted helper methods: _load_cache_if_needed, _process_single_image_generation, _process_batch_generation
  - Improved method separation of concerns for better maintainability
- Fixed linting violations
  - Wrapped long docstrings and f-strings to comply with 100-character line limit
  - Removed unused variable assignments in test suite
  - Fixed unused import in test_gui_architecture.py
- Performance improvements in date extraction
  - ~50-60x speedup on date index building (29s → <1s for 45k+ segments)
  - Replaced expensive pandas datetime parsing with native Python fromisoformat
  - Falls back to pandas only for non-standard timestamp formats
- Session-level segment caching with MD5-based invalidation
  - Caches parsed segments by date for fast reuse within session
  - Automatically invalidates cache when Timeline.json file changes (via MD5 hash)
  - Provides ~10x speedup on repeated date queries with same file
- Date range validation now correctly handles specific date ranges without requiring days > 0
- Output directory setting now correctly used when generating images (was defaulting to project's output/ directory)
- Image size default now correctly set to 500 pixels (was showing 100 due to Qt spinbox initialization order)
- Generate Maps button now enables when file is selected (was staying disabled due to deferred file loading)

### Removed
- SQLite persistent JSON caching (JsonCache) - date extraction is now fast enough without it
- `--clean-cache` CLI argument (was specific to SQLite cache)
- Unused `profile` CLI argument and parameter
- Broken `test_caches.py` test file

---

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

[Unreleased]: https://github.com/yourusername/timeline-2-images/compare/v## [Unreleased]...HEAD
[## [Unreleased]]: https://github.com/yourusername/timeline-2-images/compare/v0.3.0...v## [Unreleased]
[0.3.0]: https://github.com/yourusername/timeline-2-images/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/timeline-2-images/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/timeline-2-images/releases/tag/v0.1.0
