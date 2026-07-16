"""Entry point for rendering timeline images using the OOP architecture."""

import sys
import time
from pathlib import Path

from timeline_2_images.banner import print_banner
from timeline_2_images.app import TimelineApp
from timeline_2_images.config import RenderConfiguration
from timeline_2_images.sqlite_cache import clean_all_cache


def main(
    timeline_json: str,
    output_dir: str = "output",
    days: int = 14,
    image_size: int = 500,
    start_date: str | None = None,
    end_date: str | None = None,
    profile: bool = False,
):
    """
    Generate daily route maps from Timeline JSON export.

    Args:
        timeline_json: Path to Timeline.json file
        output_dir: Directory to save JPG images
        days: Number of recent days to process (default 14)
        image_size: Output image size in pixels (default 500)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        profile: If True, show detailed timing breakdown per operation
    """
    timeline_path = Path(timeline_json)
    if not timeline_path.exists():
        print(f"Error: Timeline file not found: {timeline_json}")
        sys.exit(1)

    config = RenderConfiguration(image_size=image_size)
    app = TimelineApp(str(timeline_path), output_dir=output_dir, config=config)

    print(f"Loading timeline data from {timeline_path}...", end=" ", flush=True)
    load_start = time.time()
    available_dates = app.get_available_dates()
    load_time = time.time() - load_start
    print(f"✓ ({load_time:.2f}s)")

    if not available_dates:
        print("No timeline data found")
        sys.exit(1)

    print(f"Found {len(available_dates)} days with data")
    print(f"Date range: {available_dates[0]} to {available_dates[-1]}")
    print()

    # Get the dates that will be processed
    from timeline_2_images.config import DateRangeQuery

    query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
    dates_to_process = app.processor.get_date_range(query)

    if dates_to_process:
        print(f"Processing dates {dates_to_process[0]} to {dates_to_process[-1]}...")
    else:
        print("Processing dates...")

    start_time = time.time()
    results = app.process_date_range(start_date=start_date, end_date=end_date, days=days)
    total_time = time.time() - start_time

    success_count = sum(1 for r in results if r.was_successful())
    print()
    print(f"Generated {success_count}/{len(results)} map images in {output_dir}")
    print(f"Total time: {total_time:.2f}s")

    cache_info = app.renderer.get_cache_info()
    if cache_info:
        print()
        print("Cache Information:")
        print(f"  Location: {cache_info.get('cache_dir', 'unknown')}")
        print(f"  Status: {cache_info.get('status', 'unknown')}")
        if cache_info.get("status") == "cached":
            print(f"  Cached tiles: {cache_info.get('total_cached_tiles', 0)}")
        print(f"  Size: {cache_info.get('cache_size_mb', 0):.1f}MB")


if __name__ == "__main__":
    import argparse

    print_banner()

    prog_name = Path(sys.argv[0]).name
    parser = argparse.ArgumentParser(
        prog=prog_name, description="Generate daily route maps from Google Timeline exports"
    )
    parser.add_argument("timeline_json", nargs="?", help="Path to Timeline.json file")
    parser.add_argument("--output-dir", default="output", help="Output directory for JPG images")
    parser.add_argument(
        "--days", type=int, default=14, help="Number of days to process (default: 14)"
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=500,
        help="Output image size in pixels (default: 500)",
    )
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Show detailed timing breakdown (future enhancement)",
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Remove all cached segment data and exit",
    )

    args = parser.parse_args()

    if args.clean_cache:
        try:
            clean_all_cache()
            print("Cache cleaned successfully")
        except RuntimeError as exception:
            print(f"Error: {exception}")
            sys.exit(1)
    elif args.timeline_json:
        main(
            args.timeline_json,
            args.output_dir,
            args.days,
            args.image_size,
            args.start_date,
            args.end_date,
            args.profile,
        )
    else:
        parser.print_help()
        sys.exit(1)
