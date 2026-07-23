# Timeline 2 Images

Generate daily route map images from Google Timeline JSON exports.

## What It Does

This tool processes Google Timeline location history exports and creates a JPG image for each day showing:
- Your route traced as blue lines
- Green circles marking the start of each journey segment
- Red circles marking the end of each journey segment
- OpenStreetMap basemap for geographic context
- Automatically sized to show your entire day's travel area

Use it to review movement patterns, create travel logs, or analyze daily routines.

## Quick Start

## Using Compiled Binaries

Pre-compiled standalone executables are available for Windows, macOS, and Linux. These run without requiring Python installation.

Download the latest binaries from the [Releases](https://github.com/yourusername/timeline-2-images/releases) page for your platform.

### Linux & macOS

```bash
# Make executable
chmod +x timeline2images
chmod +x timeline2images-gui

# Run CLI version
./timeline2images Timeline.json --days 30

# Run GUI version
./timeline2images-gui
```

### Windows

#### GUI Version
```bash
timeline2images-gui.exe
```

Simply double-click to launch the graphical interface.

**If Windows blocks the app:** Windows SmartScreen may display "This App Has Been Blocked for Your Protection" for unsigned executables. To bypass:

1. Right-click the `.exe` file
2. Select **Properties**
3. Check the **"Unblock"** checkbox at the bottom
4. Click **Apply** → **OK**
5. Run the executable normally

This is a one-time step per executable.

#### CLI Version
```bash
timeline2images.exe Timeline.json --days 30
timeline2images.exe Timeline.json --start-date 2026-01-01 --end-date 2026-01-31
```

### Usage (Python)

### Prerequisites
- Python 3.13+
- `uv` package manager (or pip)

### Installation

```bash
# Clone/download this repository, then:
uv sync
```

#### GUI (Graphical Interface)

```bash
uv run python -m timeline_2_images gui
```

Opens an interactive window where you can:
- Select your Timeline.json file
- Choose date ranges for processing
- Configure rendering options
- Monitor generation progress

#### CLI (Command Line)

```bash
uv run python -m timeline_2_images.main path/to/Timeline.json
```

Generates JPG images in the `output/` directory for the last 14 days with location data.

#### CLI Options

```bash
# Generate maps for last 30 days
uv run python -m timeline_2_images.main Timeline.json --days 30

# Save to a custom directory
uv run python -m timeline_2_images.main Timeline.json --output-dir my_maps

# Change image resolution (pixels, max 4000)
uv run python -m timeline_2_images.main Timeline.json --image-size 1500

# Specific date range
uv run python -m timeline_2_images.main Timeline.json --start-date 2026-01-01 --end-date 2026-01-31
```

**Note on image size:** Larger image sizes (1500px+) will significantly increase processing time. Range: 200-4000 pixels.

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
- **Image Size**: Default 500 pixels, range 200-4000 pixels
  - Minimum 200 pixels for adequate visibility of routes and markers
  - Larger sizes increase processing time and memory usage
  - Recommended: 500-2000 pixels for most use cases
- **Map Projection**: Web Mercator (EPSG:3857) for accurate distance calculations

## Getting Your Timeline Data

Google Timeline data can only be extracted directly from your Android device where the location history is stored.

### Export from Android Device

On your Android phone:

1. Open **Settings**
2. Go to **Location** → **Location Services** → **Timeline**
3. Tap **Export Timeline data**
4. Tap **Continue**
5. Verify your identity (authenticate with your device lock method)
6. Choose where to save the file
7. Tap **Save**

The exported `Timeline.json` file will be saved to your device. Transfer it to your computer via email, cloud storage, USB cable, or another method.

**Note:** The exact menu paths may vary slightly depending on your phone manufacturer and Android version. This process has been verified on Samsung Galaxy devices.

See Google's [Location Timeline help page](https://support.google.com/maps/answer/3854828) for more details.

## Development

### Quick Quality Check

Run all code quality checks at once:

```bash
./run_quality_checks.sh
```

This runs:
- **Ruff** - Linting and formatting
- **MyPy** - Type checking
- **PyLint** - Advanced linting
- **Radon** - Cyclomatic complexity analysis
- **PyTest** - Unit tests with coverage

### Individual Tools

```bash
# Linting
uv run ruff check .

# Auto-format code
uv run ruff format .

# Type checking
uv run mypy src/timeline_2_images

# Advanced linting
uv run pylint src/timeline_2_images

# Complexity analysis
uv run radon cc src/timeline_2_images -a

# Maintainability index
uv run radon mi src/timeline_2_images

# Unit tests
uv run pytest

# Tests with coverage
uv run pytest --cov=src/timeline_2_images --cov-report=term-missing

# License compliance
uv run python check_licenses.py
```

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
