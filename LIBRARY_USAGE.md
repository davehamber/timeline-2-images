# Library Usage Guide

The `timeline-2-images` package can be used as both a command-line tool and a Python library. This guide shows how to use it programmatically in your own applications.

## Installation

As a library dependency:
```bash
pip install timeline-2-images
# or with uv:
uv add timeline-2-images
```

## Basic Usage

### Simple Processing

```python
from timeline_2_images import TimelineApp

# Create app with default settings
app = TimelineApp("Timeline.json", output_dir="maps")

# Process last 14 days (default)
results = app.process_date_range()

for result in results:
    if result.was_successful():
        print(f"✓ Generated {result.date}: {result.point_count} points")
    else:
        print(f"✗ Failed {result.date}: {result.error_message}")
```

### Custom Configuration

```python
from timeline_2_images import TimelineApp, RenderConfiguration

# Configure image rendering
config = RenderConfiguration(
    image_size=800,  # pixels
    dpi=150,
    output_format="jpg",
)

app = TimelineApp(
    "Timeline.json",
    output_dir="maps",
    config=config,
)

# Process specific date range
results = app.process_date_range(
    start_date="2026-06-01",
    end_date="2026-06-30",
)

print(f"Generated {sum(1 for r in results if r.was_successful())}/{len(results)} maps")
```

### Processing Single Dates

```python
from timeline_2_images import TimelineApp

app = TimelineApp("Timeline.json")

# Process individual dates
dates_to_process = ["2026-06-15", "2026-06-16", "2026-06-17"]

for date in dates_to_process:
    result = app.process_date(date)
    print(f"{date}: {result}")
```

### Getting Available Dates

```python
from timeline_2_images import TimelineApp

app = TimelineApp("Timeline.json")

# Get all dates with data
available_dates = app.get_available_dates()
print(f"Timeline covers {len(available_dates)} days")
print(f"From {available_dates[0]} to {available_dates[-1]}")
```

## Advanced Usage

### Processing with Statistics

```python
from timeline_2_images import TimelineApp
from timeline_2_images.config import DateRangeQuery

app = TimelineApp("Timeline.json")

# Get statistics
stats = app.get_statistics()
print(f"Cache info: {stats['tile_cache']}")

# Process with custom date range query
query = DateRangeQuery(start_date="2026-06-01", days=30)
dates = app.processor.get_date_range(query)

results = app.process_date_range(start_date="2026-06-01", days=30)
successful = sum(1 for r in results if r.was_successful())
failed = sum(1 for r in results if not r.was_successful())

print(f"Success: {successful}, Failed: {failed}")
```

### Direct Processor Access

```python
from timeline_2_images.processors import TimelineProcessor, SegmentProcessor
from timeline_2_images.config import RenderConfiguration
from timeline_2_images.rendering import MapRenderer

# Manually orchestrate processing steps
timeline = TimelineProcessor("Timeline.json")
segments = timeline.load_segments_for_day("2026-06-15")

processor = SegmentProcessor()
processed = processor.process_segments(segments)

# Render manually
config = RenderConfiguration(image_size=600)
renderer = MapRenderer(config=config)
result = renderer.render_segments(processed, "map_2026_06_15.jpg")

print(f"Rendered: {result.output_path}, {result.point_count} points")
```

## API Reference

### TimelineApp

Main orchestrator for timeline processing.

**Constructor:**
```python
TimelineApp(
    json_path: str,
    output_dir: str = "output",
    config: RenderConfiguration | None = None,
    cache_manager: CacheManager | None = None,
    cache_dir: str | None = None,
)
```

**Methods:**
- `process_date_range(start_date, end_date, days) -> list[RenderResult]` - Process multiple dates
- `process_date(date: str) -> RenderResult` - Process single date
- `get_available_dates() -> list[str]` - Get all dates with data
- `get_statistics() -> dict` - Get app statistics
- `clear_caches()` - Clear session and tile caches

### RenderConfiguration

Image rendering configuration.

**Constructor:**
```python
RenderConfiguration(
    image_size: int = 500,
    dpi: int = 100,
    output_format: str = "jpg",
    start_marker_size: int = 70,
    end_marker_size: int = 50,
    min_area_sq_km: float = 5.0,
)
```

### Models

**Segment** - A timeline segment (journey or stay)

**ProcessedSegment** - Segment after RDP simplification

**RenderResult** - Result of rendering a single date
- `date: str` - Date (YYYY-MM-DD)
- `output_path: Path` - Path to generated image
- `segment_count: int` - Number of segments
- `point_count: int` - Number of waypoints
- `render_time: float` - Rendering time in seconds
- `success: bool` - Whether render succeeded
- `error_message: str | None` - Error if failed
- `was_successful() -> bool` - Check if successful

## Error Handling

```python
from timeline_2_images import TimelineApp
from timeline_2_images.timeline_validator import TimelineValidationError

try:
    app = TimelineApp("Timeline.json")
    results = app.process_date_range(days=30)
except TimelineValidationError as e:
    print(f"Invalid Timeline.json: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Processing failed: {e}")
```

## Command-Line Usage

While using as a library, the command-line tool is still available:

```bash
# Generate maps for last 14 days
timeline-2-images Timeline.json

# Specific date range
timeline-2-images Timeline.json --start-date 2026-06-01 --end-date 2026-06-30

# Custom output directory and size
timeline-2-images Timeline.json --output-dir my_maps --image-size 800

# Clean cache
timeline-2-images --clean-cache
```
