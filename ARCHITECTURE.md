# Architecture & Design

## Overview

**timeline-2-images** is a modern Python application that generates daily route maps from Google Timeline JSON exports. It uses a layered object-oriented architecture with clear separation of concerns, making it suitable for both library and CLI usage.

The application is production-ready with:
- ✅ Full type hints (MyPy validated)
- ✅ Low cyclomatic complexity (all functions A-rated)
- ✅ Installable as a Python library
- ✅ Deployable as a standalone executable
- ✅ Comprehensive error handling and validation

---

## Architecture Layers

```
┌─────────────────────────────────────────┐
│         User Interface Layer            │
│  ┌─────────────────────────────────────┐│
│  │  CLI (main.py: cli())              ││
│  │  Library API (TimelineApp)          ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Application Layer                 │
│  ┌─────────────────────────────────────┐│
│  │  TimelineApp (orchestrator)         ││
│  │  - Coordinates all components      ││
│  │  - Manages workflow                ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Processing & Rendering Layer       │
│  ┌─────────────────────────────────────┐│
│  │  TimelineProcessor    Validation    ││
│  │  SegmentProcessor     MapRenderer   ││
│  │  TileCacheManager                   ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  ┌─────────────────────────────────────┐│
│  │  Models (Segment, ProcessedSegment) ││
│  │  Configuration (RenderConfiguration)││
│  │  Cache (CacheManager, SQLite)       ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Module Organization

```
src/timeline_2_images/
├── __init__.py                  # Public API exports
├── main.py                      # CLI entry points (cli, main)
├── app.py                       # TimelineApp orchestrator
├── banner.py                    # ASCII banner display
├── timeline_validator.py        # JSON structure validation
├── timeline_parser.py           # Legacy functional API (internal)
├── map_renderer.py              # Legacy utilities (internal)
├── sqlite_cache.py              # SQLite cache implementation
│
├── config/                      # Configuration layer
│   ├── __init__.py
│   ├── render_configuration.py  # Image rendering settings
│   └── date_range_query.py      # Date range logic
│
├── models/                      # Data structures
│   ├── __init__.py
│   ├── segment.py               # Segment & ProcessedSegment
│   ├── bounds.py                # Geographic bounding box
│   └── render_result.py         # Rendering operation result
│
├── processors/                  # Data transformation
│   ├── __init__.py
│   ├── timeline_processor.py    # JSON loading & caching
│   └── segment_processor.py     # RDP simplification & processing
│
├── rendering/                   # Map rendering
│   ├── __init__.py
│   ├── map_renderer.py          # MapRenderer class
│   └── tile_cache_manager.py    # OSM tile caching
│
└── cache/                       # Cache abstraction
    ├── __init__.py
    └── manager.py               # CacheManager interface
```

---

## Key Components

### 1. TimelineApp (Orchestrator)

Central coordinator that ties all components together.

```python
from timeline_2_images import TimelineApp, RenderConfiguration

config = RenderConfiguration(image_size=800)
app = TimelineApp("Timeline.json", output_dir="maps", config=config)

# Process date range
results = app.process_date_range(start_date="2026-06-01", days=30)

# Get statistics
dates = app.get_available_dates()
stats = app.get_statistics()
```

**Responsibilities:**
- Manages TimelineProcessor, SegmentProcessor, MapRenderer
- Orchestrates the processing workflow
- Provides unified public API
- Handles cache clearing and statistics

---

### 2. TimelineProcessor (Data Layer)

Loads and parses Timeline.json data with session-level caching.

**Key Methods:**
- `load_segments_for_day(date)` → List[Segment]
- `load_points_for_day(date)` → List[Point]
- `get_available_dates()` → List[str]
- `get_date_range(query)` → List[str]

**Caching Strategy:**
- **Session Cache**: In-memory cache for the JSON file
- **Performance**: ~14x speedup for multi-date queries
- **Implementation**: Lazy date index building on first access

---

### 3. SegmentProcessor (Transformation Layer)

Processes raw segments with line simplification and bounds calculation.

**Key Methods:**
- `process_segments(segments)` → List[ProcessedSegment]
- `simplify_waypoints(waypoints)` → List[waypoints]
- `filter_by_waypoint_count(segments)` → List[Segment]

**Algorithm:** Ramer-Douglas-Peucker (RDP) line simplification
- Tolerance: 20 meters
- Reduces GPS jitter while preserving path shape
- Automatically clusters stationary points

---

### 4. MapRenderer (Presentation Layer)

Renders processed segments to map images with OSM basemaps.

**Key Methods:**
- `render_segments(segments, output_path)` → RenderResult
- `get_cache_info()` → Dict[cache_stats]
- `clear_cache()` → None

**Rendering Pipeline:**
1. Calculate Web Mercator bounds from waypoints
2. Apply padding (5%) and enforce minimum area (5 sq km)
3. Fetch OSM tiles via requests-cache (XDG compliant)
4. Draw base map with contextily
5. Draw journey line with border effect
6. Draw start/end markers
7. Save as JPG image

**Tile Caching:**
- Location: `~/.cache/timeline-2-images/tiles.sqlite`
- Backend: SQLite with requests-cache
- Expiration: Never (tiles are immutable)
- Size: Typically 2-5MB for typical usage

---

### 5. Validation Layer (TimelineValidator)

Validates Timeline.json structure early in the pipeline.

**Validation Checks:**
- File exists and is readable
- Valid JSON format
- Root is an object/dictionary
- Contains at least one data source (semanticSegments, timelineObjects, locations)
- Data source arrays are properly typed

**Error Messages:**
- Descriptive and actionable
- Suggest checking Google Takeout
- Acknowledge format changes

---

### 6. Configuration Layer

**RenderConfiguration:**
- image_size: 500px (default)
- dpi: 100 (default)
- output_format: "jpg"
- start_marker_size: 70 pixels
- end_marker_size: 50 pixels
- min_area_sq_km: 5.0 (minimum viewing area)

**DateRangeQuery:**
Implements flexible date range logic with parameter precedence:
1. `--start-date` + `--end-date` → exact range
2. `--start-date` + `--days` → from start + N days
3. `--end-date` + `--days` → N days before end
4. `--days` only → last N days with data

---

## Data Models

### Segment (Raw Data)

```python
@dataclass
class Segment:
    start_time: str              # ISO 8601 timestamp
    end_time: str
    waypoints: List[tuple]       # (lat, lon) tuples

    methods:
    - get_bounds() → Bounds
    - get_duration() → timedelta
    - get_waypoint_count() → int
```

### ProcessedSegment (After Simplification)

```python
@dataclass
class ProcessedSegment:
    simplified_waypoints: List[tuple]  # After RDP simplification
    bounds: Bounds
    original_waypoint_count: int
    simplified_waypoint_count: int

    methods:
    - from_segment(Segment) → ProcessedSegment
```

### Bounds (Geographic Box)

```python
@dataclass
class Bounds:
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float

    methods:
    - get_center() → (lat, lon)
    - expand(factor) → Bounds
    - get_area_degrees_squared() → float
```

### RenderResult (Operation Result)

```python
@dataclass
class RenderResult:
    date: str
    output_path: Path
    segment_count: int
    point_count: int
    render_time: float
    success: bool
    error_message: str | None

    methods:
    - was_successful() → bool
    - get_summary() → str
```

---

## Data Flow

```
Timeline.json
       ↓
[Validation] → TimelineValidationError on failure
       ↓
TimelineProcessor.load_segments_for_day()
       ↓
List[Segment] (raw data)
       ↓
SegmentProcessor.process_segments()
  ├─ simplify_waypoints() [RDP algorithm]
  ├─ calculate_bounds() [Web Mercator]
  └─ filter by properties
       ↓
List[ProcessedSegment] (simplified)
       ↓
MapRenderer.render_segments()
  ├─ Calculate total bounds
  ├─ Apply padding & minimum area
  ├─ Render map background (OSM)
  ├─ Draw journey lines
  ├─ Draw start/end markers
  └─ Save JPG
       ↓
RenderResult (success/error)
```

---

## Usage Modes

### Mode 1: Command-Line Tool

```bash
# Install as package
pip install timeline-2-images

# Use as CLI
timeline-2-images Timeline.json --start-date 2026-06-01 --days 30
timeline-2-images --clean-cache
```

**Entry Point:** `timeline_2_images.main:cli()` (defined in pyproject.toml)

---

### Mode 2: Library

```python
from timeline_2_images import TimelineApp, RenderConfiguration

config = RenderConfiguration(image_size=800)
app = TimelineApp("Timeline.json", output_dir="maps", config=config)

# Process and iterate results
results = app.process_date_range(days=14)
for result in results:
    if result.was_successful():
        print(f"✓ {result.date}")
    else:
        print(f"✗ {result.date}: {result.error_message}")
```

---

### Mode 3: Standalone Executable

```bash
# Build with Nuitka
./build_executable.sh

# Use as standalone
./dist/timeline2images Timeline.json
```

No Python runtime required. Distributable as a single binary.

---

## Performance Characteristics

### Caching

**Session-Level Cache:**
- JSON file parsed once per session
- All subsequent queries use cached data
- Lazy date index built on first availability check
- Speed-up: ~14x for multi-date processing

**Tile Cache:**
- SQLite backend at `~/.cache/timeline-2-images`
- XDG Base Directory compliant
- Persists across sessions
- Typical size: 2-5MB

### Processing Speed

Typical performance on modern hardware:
- 1 date: ~5-7 seconds (includes tile fetch + render)
- 14 dates: ~40-60 seconds
- 30 dates: ~90-120 seconds

Bottlenecks:
1. OSM tile fetching (network-dependent)
2. Matplotlib rendering (CPU-dependent)
3. GeoDataFrame projections (CPU-dependent)

---

## Code Quality

**Metrics:**
- Type Coverage: 100% (MyPy validated)
- Average Complexity: 2.89/10 (A-rated)
- Pylint Score: 9.69/10
- Functions Analyzed: 137 blocks
- All Functions: A-rated complexity

**Testing:**
- 5 test modules (config, models, processors, rendering, integration)
- Unit and integration tests
- ~74 test cases

---

## Design Principles

1. **Separation of Concerns** - Layers handle specific responsibilities
2. **Type Safety** - Full type hints, MyPy validated
3. **Low Complexity** - All functions maintain A-rated complexity
4. **Testability** - Dependency injection, mockable components
5. **Flexibility** - Works as library, CLI, or executable
6. **Performance** - Session caching for ~14x speedup
7. **User-Friendly** - Clear error messages, helpful guidance

---

## Error Handling

**Validation Layer:**
- Early detection of invalid Timeline.json
- Descriptive error messages
- Actionable solutions

**Processing Layer:**
- Per-date error handling
- Partial success (some dates fail, others succeed)
- Error messages in RenderResult

**Display Layer:**
- Clear success/failure reporting
- Cache statistics on completion

---

## Future Extensibility

The architecture supports:

1. **Custom Caching** - Implement CacheManager interface
2. **Alternative Projections** - Modify MapRenderer._calculate_bounds()
3. **Additional Output Formats** - Extend RenderResult, add new renderers
4. **Different Data Sources** - Subclass TimelineProcessor
5. **Custom Simplification** - Replace SegmentProcessor algorithm
6. **Map Styling** - Extend MapRenderer._render_map()

---

## Backward Compatibility

**Legacy API Preserved:**
- `timeline_parser.py` - Functional API for internal use
- `map_renderer.py` - Utility functions (simplify_waypoints)
- All legacy functions maintained for compatibility

**Migration Path:**
- Old code works with minimal changes
- New code should use TimelineApp
- Both can coexist in the same application
