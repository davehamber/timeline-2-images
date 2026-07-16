"""Entry point for rendering timeline images."""

import sys
import time
from pathlib import Path

from daily_timeline_images.timeline_parser import (
    load_segments_for_day,
    get_date_range,
)
from daily_timeline_images.map_renderer import (
    render_segments,
    get_tile_cache_stats,
)


def _process_date(
    date_str: str, timeline_path: Path, output_path: Path, image_size: int
) -> tuple[bool, float]:
    """Process a single date and render its map. Returns (success, elapsed_time)."""
    start_time = time.time()
    try:
        print(f"Processing {date_str}...", end=" ", flush=True)
        segments = load_segments_for_day(str(timeline_path), date_str)

        if not segments:
            print("✗ No segments found")
            return False, time.time() - start_time

        output_file = output_path / f"timeline_{date_str}.jpg"
        render_segments(segments, str(output_file), image_size=image_size)

        total_points = sum(len(seg.get("waypoints", [])) for seg in segments)
        elapsed = time.time() - start_time
        output_name = output_file.name
        print(f"✓ ({len(segments)} segments, {total_points} points) {elapsed:.2f}s → {output_name}")
        return True, elapsed
    except ValueError as e:
        print(f"✗ {e}")
    except (OSError, RuntimeError) as e:
        print(f"✗ Error: {e}")
    return False, time.time() - start_time


def main(
    timeline_json: str,
    output_dir: str = "output",
    days: int = 14,
    image_size: int = 500,
    start_date: str | None = None,
    end_date: str | None = None,
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
    """
    timeline_path = Path(timeline_json)
    if not timeline_path.exists():
        print(f"Error: Timeline file not found: {timeline_json}")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    print(f"Loading timeline data from {timeline_json}")
    target_dates = get_date_range(
        str(timeline_path), start_date=start_date, end_date=end_date, days=days
    )

    if not target_dates:
        date_desc = (
            f"from {start_date} to {end_date}"
            if start_date and end_date
            else (
                f"from {start_date}"
                if start_date
                else f"until {end_date}" if end_date else f"in the last {days} days"
            )
        )
        print(f"No timeline data found {date_desc}")
        sys.exit(1)

    print(f"Found {len(target_dates)} days with data")
    print(f"Date range: {target_dates[0]} to {target_dates[-1]}")
    print()

    start_time = time.time()
    results = [
        _process_date(date_str, timeline_path, output_path, image_size) for date_str in target_dates
    ]
    success_count = sum(1 for success, _ in results if success)
    total_time = time.time() - start_time
    day_times = [elapsed for _, elapsed in results]

    print()
    print(f"Generated {success_count}/{len(target_dates)} map images in {output_path}")
    print()
    print("Performance Statistics:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average per day: {total_time / len(target_dates):.2f}s")
    if day_times:
        print(f"  Min/Max per day: {min(day_times):.2f}s / {max(day_times):.2f}s")

    cache_stats = get_tile_cache_stats()
    if cache_stats:
        print()
        print("Tile Cache Statistics:")
        total_tiles = (
            cache_stats["memory_cache_hits"]
            + cache_stats["disk_cache_hits"]
            + cache_stats["network_requests"]
        )
        print(f"  Total tile requests: {total_tiles}")
        print(f"  Memory cache hits: {cache_stats['memory_cache_hits']}")
        print(f"  Disk cache hits: {cache_stats['disk_cache_hits']}")
        print(f"  Network requests: {cache_stats['network_requests']}")
        print(f"  Cache hit rate: {cache_stats['cache_hit_rate']:.1f}%")
        if cache_stats["disk_cache"]["tile_count"] > 0:
            print(
                f"  Disk cache: {cache_stats['disk_cache']['tile_count']} tiles "
                f"({cache_stats['disk_cache']['total_size_mb']:.1f}MB)"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate daily route maps from Google Timeline exports"
    )
    parser.add_argument("timeline_json", help="Path to Timeline.json file")
    parser.add_argument("--output-dir", default="output", help="Output directory for JPG images")
    parser.add_argument(
        "--days", type=int, default=14, help="Number of days to process (default: 14)"
    )
    parser.add_argument(
        "--image-size", type=int, default=500, help="Output image size in pixels (default: 500)"
    )
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format. If set with --end-date, "
        "--days is ignored. If set alone with --days, dates from "
        "start + N days are used.",
    )
    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format. If set with --start-date, "
        "--days is ignored. If set alone with --days, dates N days "
        "before end date are used.",
    )

    args = parser.parse_args()
    main(
        args.timeline_json,
        args.output_dir,
        args.days,
        args.image_size,
        args.start_date,
        args.end_date,
    )
