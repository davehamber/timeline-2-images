# Timeline 2 Images

Generate daily route map images from Google Timeline JSON exports. Visualize where you've been each day with beautiful map visualizations.

## What It Does

This tool processes Google Timeline location history exports and creates a JPG image for each day showing:
- Your route traced as a blue line
- Individual location points marked in red
- Map background from OpenStreetMap
- Automatically sized to fit the day's travel area

Perfect for reviewing your movement patterns, creating visual logs, or analyzing daily routines.

## Quick Start

### Prerequisites
- Python 3.13+
- `uv` package manager (or pip)

### Installation

```bash
# Clone/download this repository, then:
uv sync
```

### Usage

Export your Google Timeline data from your phone as JSON, then:

```bash
uv run python -m timeline_2_images.main path/to/Timeline.json
```

This generates JPG images in the `output/` directory for the last 14 days with location data.

### Options

```bash
# Generate maps for last 30 days
uv run python -m timeline_2_images.main Timeline.json --days 30

# Save to a custom directory
uv run python -m timeline_2_images.main Timeline.json --output-dir my_maps

# Change image resolution (pixels)
uv run python -m timeline_2_images.main Timeline.json --image-size 1500
```

### Working with Large Timelines

If your Timeline.json is very large (60MB+), split it by year for easier processing:

```bash
# Split into yearly files
uv run python -m timeline_2_images.split_timeline split Timeline.json --output-dir timelines

# Generate maps from a specific year
uv run python -m timeline_2_images.main timelines/timeline_2025.json --days 365

# Merge yearly files back into one
uv run python -m timeline_2_images.split_timeline merge timelines --output Timeline_merged.json
```

## How It Works

1. **Parse Timeline JSON** - Reads your exported timeline data, extracting semantic journey segments
2. **Simplify Routes** - Applies line simplification (Ramer-Douglas-Peucker algorithm) to reduce GPS noise and jitter
3. **Render Maps** - Uses OpenStreetMap tiles as basemap, draws each journey segment separately, saves as JPG

### Intelligent Journey Rendering

The tool automatically cleans up chaotic GPS data:

- **Segment Separation**: Each distinct journey or stay is rendered independently rather than connecting all points into one tangled line
- **Line Simplification**: GPS jitter and stationary point clustering are automatically reduced while preserving your actual path shape
- **Visual Markers**:
  - **Blue lines**: Your journey routes
  - **Green circles**: Start of each journey segment
  - **Red circles**: End of each journey segment

### Map Specifications

- **Minimum Viewing Area**: Every image shows at least 5 square kilometers
  - Ensures context even on days with minimal movement
  - Prevents excessive zoom on tightly clustered points
- **Image Dimensions**: 1000×1000 pixels (fixed)
- **Map Projection**: Web Mercator (EPSG:3857) for accurate distance calculations

## Getting Your Timeline Data

1. On your Android phone: Settings → Location → Location Settings → Timeline
2. Tap "Export Timeline data"
3. Authenticate with your device lock method
4. Save as JSON file
5. Transfer to your computer

More details on Google's [Location Timeline help page](https://support.google.com/maps/answer/3854828).

## Testing

```bash
# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov
```

## Development

See [CLAUDE.md](CLAUDE.md) for architecture details and module documentation.

## License

This project is licensed under the **European Union Public Licence (EUPL) v1.2**.

See the [LICENSE](LICENSE) file for the full text.

**SPDX-License-Identifier:** `EUPL-1.2`

### What this means:

- ✓ You can use, modify, and distribute this software freely
- ✓ Derivative works must also be licensed under EUPL-1.2 (or a compatible license)
- ✓ You must include a copy of the license with any distribution
- ✓ You must state what changes were made to the original work

The EUPL is compatible with many other open source licenses including MIT, Apache 2.0, GPL, and others. See the LICENSE file for the full compatibility list.
