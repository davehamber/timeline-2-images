"""Entry point for rendering timeline images."""

import sys
from pathlib import Path

from daily_timeline_images.timeline_parser import load_segments_for_day, get_last_n_days_with_data
from daily_timeline_images.map_renderer import render_segments  # RDP line simplification


def _process_date(date_str: str, timeline_path: Path, output_path: Path, image_size: int) -> bool:
    """Process a single date and render its map."""
    try:
        print(f"Processing {date_str}...", end=" ", flush=True)
        segments = load_segments_for_day(str(timeline_path), date_str)

        if not segments:
            print("✗ No segments found")
            return False

        output_file = output_path / f"timeline_{date_str}.jpg"
        render_segments(segments, str(output_file), image_size=image_size)

        total_points = sum(len(seg.get("waypoints", [])) for seg in segments)
        print(f"✓ ({len(segments)} segments, {total_points} points) → {output_file.name}")
        return True
    except ValueError as e:
        print(f"✗ {e}")
    except (OSError, RuntimeError) as e:
        print(f"✗ Error: {e}")
    return False


def main(
    timeline_json: str,
    output_dir: str = "output",
    days: int = 14,
    image_size: int = 500,
):
    """
    Generate daily route maps from Timeline JSON export.

    Args:
        timeline_json: Path to Timeline.json file
        output_dir: Directory to save JPG images
        days: Number of recent days to process
        image_size: Output image size in pixels (1000x1000)
    """
    timeline_path = Path(timeline_json)
    if not timeline_path.exists():
        print(f"Error: Timeline file not found: {timeline_json}")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    print(f"Loading timeline data from {timeline_json}")
    target_dates = get_last_n_days_with_data(str(timeline_path), days=days)

    if not target_dates:
        print(f"No timeline data found in the last {days} days")
        sys.exit(1)

    print(f"Found {len(target_dates)} days with data in the last {days} days")
    print(f"Date range: {target_dates[0]} to {target_dates[-1]}")
    print()

    success_count = sum(
        _process_date(date_str, timeline_path, output_path, image_size)
        for date_str in target_dates
    )

    print()
    print(f"Generated {success_count}/{len(target_dates)} map images in {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate daily route maps from Google Timeline exports"
    )
    parser.add_argument("timeline_json", help="Path to Timeline.json file")
    parser.add_argument(
        "--output-dir", default="output", help="Output directory for JPG images"
    )
    parser.add_argument(
        "--days", type=int, default=14, help="Number of recent days to process"
    )
    parser.add_argument(
        "--image-size", type=int, default=500, help="Output image size in pixels (default: 500)"
    )

    args = parser.parse_args()
    main(args.timeline_json, args.output_dir, args.days, args.image_size)
