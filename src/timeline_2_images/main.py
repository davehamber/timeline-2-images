"""Entry point for rendering timeline images."""

import sys
import time
from pathlib import Path
from typing import cast

from timeline_2_images.banner import print_banner
from timeline_2_images.timeline_parser import (
    load_segments_for_day,
    get_date_range,
    get_cache_source,
)
from timeline_2_images.map_renderer import (
    render_segments,
    get_tile_cache_stats,
    get_render_cache_info,
)
from timeline_2_images.sqlite_cache import clean_all_cache


def _load_date_segments(timeline_path: Path, date_str: str, profile: bool):
    """Load segments for a date, returning (segments, load_timing)."""
    if profile:
        result = load_segments_for_day(str(timeline_path), date_str, profile=True)
        segments, load_timing = cast(tuple[list[dict], dict], result)
        return segments, load_timing
    segments = cast(list[dict], load_segments_for_day(str(timeline_path), date_str))
    return segments, {}


def _get_cache_indicator(cache_before: dict, cache_after: dict) -> str:
    """Return cache indicator if new tiles were cached."""
    if cache_after.get("total_cached_tiles", 0) > cache_before.get("total_cached_tiles", 0):
        return " 💾"
    return ""


def _print_timing_breakdown(load_timing: dict, render_timing: dict | None):
    """Print detailed timing breakdown for profiling."""
    print("      Timing breakdown:")
    if load_timing:
        print("        Load Segments:")
        _print_timing_section(load_timing)
    if render_timing:
        print("        Render Segments:")
        _print_timing_section(render_timing, exclude_keys=set())


def _should_skip_timing_key(key: str, exclude_keys: set) -> bool:
    """Check if a timing key should be skipped."""
    return key == "total" or key in exclude_keys or not isinstance(key, str)


def _get_timing_percentage(value: float, total: float) -> float:
    """Calculate percentage of value relative to total."""
    return (value / total * 100) if total > 0 else 0


def _print_timing_line(key: str, value: float, total: float):
    """Print a single timing line with percentage."""
    pct = _get_timing_percentage(value, total)
    print(f"          {key:.<20} {value:6.2f}s ({pct:5.1f}%)")


def _print_timing_section(timing: dict, exclude_keys=None):
    """Print a timing section with percentages."""
    if exclude_keys is None:
        exclude_keys = {"cache_source"}

    total = timing.get("total", 0)
    for key, value in sorted(timing.items()):
        if _should_skip_timing_key(key, exclude_keys) or not isinstance(value, (int, float)):
            continue
        _print_timing_line(key, value, total)
    print(f"          {('total'):.<20} {total:6.2f}s")


def _process_date_successful(
    date_str: str,
    output_path: Path,
    segments: list,
    image_size: int,
    profile: bool,
    start_time: float,
    load_timing: dict | None = None,
) -> tuple[bool, float, dict]:
    """Handle successful date processing."""
    if load_timing is None:
        load_timing = {}

    output_file = output_path / f"timeline_{date_str}.jpg"
    cache_before = get_render_cache_info()
    render_timing = render_segments(
        segments, str(output_file), image_size=image_size, profile=profile
    )
    cache_after = get_render_cache_info()

    total_points = sum(len(segment.get("waypoints", [])) for segment in segments)
    elapsed = time.time() - start_time

    cache_info = {
        "cache_status": cache_after.get("status", "unknown"),
        "total_cached": cache_after.get("total_cached_tiles", 0),
    }

    cache_indicator = _get_cache_indicator(cache_before, cache_after)
    details = f"({len(segments)} segments, {total_points} points) {elapsed:.2f}s{cache_indicator}"
    print(f"✓ {details} → {output_file.name}")

    if profile:
        _print_timing_breakdown(load_timing, render_timing)

    return True, elapsed, cache_info


def _handle_date_error(exc: Exception):
    """Handle and print processing error."""
    if isinstance(exc, ValueError):
        print(f"✗ {exc}")
    else:
        print(f"✗ Error: {exc}")


def _process_date(
    date_str: str,
    timeline_path: Path,
    output_path: Path,
    image_size: int,
    profile: bool = False,
) -> tuple[bool, float, dict]:
    """Process a single date and render its map. Returns (success, elapsed_time, cache_info)."""
    start_time = time.time()
    try:
        print(f"Processing {date_str}...", end=" ", flush=True)
        segments, load_timing = _load_date_segments(timeline_path, date_str, profile)

        if not segments:
            print("✗ No segments found")
            return False, time.time() - start_time, {}

        return _process_date_successful(
            date_str, output_path, segments, image_size, profile, start_time, load_timing
        )
    except (ValueError, OSError, RuntimeError) as e:
        _handle_date_error(e)

    return False, time.time() - start_time, {}


def _get_cache_label(cache_source: str) -> str:
    """Get human-readable cache label."""
    labels = {
        "session": "session cache",
        "disk": "disk cache",
        "parsed": "parsed from JSON",
    }
    return labels.get(cache_source, "unknown")


def _build_date_description(start_date: str | None, end_date: str | None, days: int) -> str:
    """Build human-readable description of date range."""
    if start_date and end_date:
        return f"from {start_date} to {end_date}"
    if start_date:
        return f"from {start_date}"
    if end_date:
        return f"until {end_date}"
    return f"in the last {days} days"


def _print_performance_stats(day_times: list[float], target_dates: list[str], total_time: float):
    """Print performance statistics."""
    print("Performance Statistics:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average per day: {total_time / len(target_dates):.2f}s")
    if day_times:
        print(f"  Min/Max per day: {min(day_times):.2f}s / {max(day_times):.2f}s")


def _print_tile_cache_stats():
    """Print tile cache statistics if available."""
    cache_stats = get_tile_cache_stats()
    if not cache_stats:
        return

    print()
    print("Tile Cache Statistics:")
    disk_cache_info = cache_stats.get("disk_cache", {})
    tile_count = disk_cache_info.get("tile_count", 0)
    cache_size = disk_cache_info.get("total_size_mb", 0.0)
    print(f"  Backend: {cache_stats.get('cache_backend', 'requests-cache')}")
    print(f"  Cache location: {cache_stats.get('cache_location', '.tile_cache')}")
    if tile_count > 0:
        print(f"  Cached tiles: {tile_count} tiles ({cache_size:.1f}MB)")
    print("  Note: Tiles are automatically reused for overlapping geographic areas")


def _validate_timeline_file(timeline_json: str) -> Path:
    """Validate timeline file exists."""
    timeline_path = Path(timeline_json)
    if not timeline_path.exists():
        print(f"Error: Timeline file not found: {timeline_json}")
        sys.exit(1)
    return timeline_path


def _load_and_validate_dates(
    timeline_path: Path, start_date: str | None, end_date: str | None, days: int
) -> list[str]:
    """Load dates from timeline and validate we have data."""
    print(f"Loading timeline data from {timeline_path}...", end=" ", flush=True)
    load_start = time.time()
    target_dates = get_date_range(
        str(timeline_path), start_date=start_date, end_date=end_date, days=days
    )
    load_time = time.time() - load_start
    cache_label = _get_cache_label(get_cache_source())
    print(f"✓ ({load_time:.2f}s, {cache_label})")

    if not target_dates:
        date_desc = _build_date_description(start_date, end_date, days)
        print(f"No timeline data found {date_desc}")
        sys.exit(1)

    return target_dates


def _print_date_range_info(target_dates: list[str]):
    """Print date range information."""
    print(f"Found {len(target_dates)} days with data")
    print(f"Date range: {target_dates[0]} to {target_dates[-1]}")
    print()


def _process_all_dates(
    target_dates: list[str],
    timeline_path: Path,
    output_path: Path,
    image_size: int,
    profile: bool,
) -> list[tuple[bool, float, dict]]:
    """Process all target dates and return results."""
    return [
        _process_date(date_str, timeline_path, output_path, image_size, profile)
        for date_str in target_dates
    ]


def _print_final_summary(
    results: list[tuple[bool, float, dict]], target_dates: list[str], output_path: Path
):
    """Print final summary and statistics."""
    success_count = sum(1 for success, _, _ in results if success)
    total_time = sum(elapsed for _, elapsed, _ in results)
    day_times = [elapsed for _, elapsed, _ in results]

    print()
    print(f"Generated {success_count}/{len(target_dates)} map images in {output_path}")
    print()
    _print_performance_stats(day_times, target_dates, total_time)
    _print_tile_cache_stats()


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
    timeline_path = _validate_timeline_file(timeline_json)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    target_dates = _load_and_validate_dates(timeline_path, start_date, end_date, days)
    _print_date_range_info(target_dates)

    results = _process_all_dates(target_dates, timeline_path, output_path, image_size, profile)
    _print_final_summary(results, target_dates, output_path)


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
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Show detailed timing breakdown for each rendering operation",
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
        except RuntimeError as e:
            print(f"Error: {e}")
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
