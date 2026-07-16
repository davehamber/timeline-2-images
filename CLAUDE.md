# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**daily-timeline-images** generates daily route map images from Google Timeline JSON exports. It takes location history data and renders each day's route on an OpenStreetMap basemap as a JPG image, useful for visualizing movement patterns day by day.

The project uses Python 3.13+ and `uv` as the package manager.

## Development Setup & Commands

### Dependencies
```bash
# Install/sync dependencies
uv sync

# Add a new runtime dependency
uv add <package_name>

# Add a development dependency
uv add --dev <package_name>
```

### Running the Application

#### Generate Daily Maps
```bash
# Generate maps for last 14 days (default)
uv run python -m daily_timeline_images.main Timeline.json

# Custom number of days and output directory
uv run python -m daily_timeline_images.main Timeline.json --days 30 --output-dir my_maps

# Custom image size (default 1000x1000 pixels)
uv run python -m daily_timeline_images.main Timeline.json --image-size 800
```

#### Split/Merge Timelines by Year
For large Timeline.json files, split into yearly files for easier processing:

```bash
# Split Timeline.json into yearly files
uv run python -m daily_timeline_images.split_timeline split Timeline.json --output-dir timelines

# Merge yearly files back into one
uv run python -m daily_timeline_images.split_timeline merge timelines --output Timeline_merged.json

# Generate maps from a specific year
uv run python -m daily_timeline_images.main timelines/timeline_2025.json --days 365
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov

# Run a specific test file
uv run pytest tests/test_timeline_parser.py

# Run with verbose output
uv run pytest -v
```

### Linting
```bash
uv run ruff check .      # Check for issues
uv run ruff format .     # Auto-format code
```

## Project Structure

```
daily-timeline-images/
├── src/daily_timeline_images/
│   ├── __init__.py           # Package definition
│   ├── main.py               # CLI entry point
│   ├── timeline_parser.py    # JSON parsing and date extraction
│   └── map_renderer.py       # Map rendering with contextily/geopandas
├── tests/
│   ├── test_timeline_parser.py
│   └── test_map_renderer.py
├── output/                   # Generated JPG images (gitignored)
├── pyproject.toml            # Package config and dependencies
├── CLAUDE.md                 # This file
└── .gitignore
```

## Core Modules

### timeline_parser.py
- `load_segments_for_day(json_path, target_date)` - Extract semantic segments with waypoints for a specific date
- `get_last_n_days_with_data(json_path, days)` - Find the most recent N days that contain location data

### map_renderer.py
- `render_segments(segments, out_path, image_size, dpi, min_area_sq_km)` - Render segments with RDP line simplification
- `simplify_waypoints(waypoints, tolerance_meters)` - Simplifies waypoints using Ramer-Douglas-Peucker algorithm

### main.py
- CLI orchestrator that calls parser and renderer in sequence for multiple days

### timeline_splitter.py
- `split_timeline_by_year(json_path, output_dir)` - Splits a large Timeline.json into separate files by year
- `merge_timelines(timeline_dir, output_path)` - Merges yearly timeline files back into a single file

### split_timeline.py
- CLI with `split` and `merge` subcommands for timeline file management

## Key Design Decisions

- **Map Format**: Uses OpenStreetMap via contextily (free, no API key needed)
- **Projection**: Web Mercator (EPSG:3857) for distance calculations; GeoDataFrame conversions handle lat/lon to projected coordinates
- **Minimum Viewing Area**: All images show at least 5 square kilometers (enforced for both single-point and multi-point days)
- **Image Dimensions**: Output is exactly 1000x1000 pixels

## Journey Rendering Strategy

Uses **Ramer-Douglas-Peucker (RDP) line simplification** to create clean, readable journey paths:

1. **Segment-Based Rendering**: Each semantic segment (distinct journey/stay) is drawn as a separate line
2. **RDP Line Simplification**: Reduces GPS jitter while preserving overall path shape
   - Tolerance: 15 meters
   - Removes intermediate points that deviate less than tolerance from simplified line
   - Preserves sharp turns and significant direction changes
3. **Automatic Point Clustering**: Stationary clusters (repeated nearby points) collapse automatically
4. **Visual Representation**:
   - Blue lines: Journey routes (5pt width, 90% opacity)
   - Green circles: Start of each journey segment
   - Red circles: End of each journey segment

## Dependencies

Runtime:
- `pandas`, `geopandas`, `shapely` - Geographic data handling
- `matplotlib` - Plotting/rendering
- `contextily` - OSM basemap tiles

Development:
- `pytest`, `pytest-cov` - Testing
- `ruff` - Linting and formatting

See `pyproject.toml` for full list and versions.
