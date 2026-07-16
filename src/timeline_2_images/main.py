"""Entry point for rendering timeline images."""

import sys
import time
from pathlib import Path
from typing import cast

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


def _print_banner():
    """Display ASCII art banner with colorized block characters."""
    # Color codes: Cyan for borders/TIMELINE, Magenta for 2 IMAGES, White for text
    cyan = "\033[36m"
    magenta = "\033[35m"
    white = "\033[37m"
    reset = "\033[0m"

    banner = f"""
{cyan}╔═════════════════════════════════════════════════════════════════╗
║{reset}                                                                 {cyan}║
║{reset}  {cyan}████████╗{reset}{white}██╗{cyan}███╗   ███╗███████╗{reset}{white}██╗     ██╗{cyan}███╗   ██╗███████╗{reset}   {cyan}║
║{reset}  {cyan}╚══██╔══╝{reset}{white}██║{cyan}████╗ ████║██╔════╝{reset}{white}██║     ██║{cyan}████╗  ██║██╔════╝{reset}   {cyan}║
║{reset}     {cyan}██║{reset}   {white}██║{cyan}██╔████╔██║█████╗{reset}  {white}██║     ██║{cyan}██╔██╗ ██║█████╗{reset}     {cyan}║
║{reset}     {cyan}██║{reset}   {white}██║{cyan}██║╚██╔╝██║██╔══╝{reset}  {white}██║     ██║{cyan}██║╚██╗██║██╔══╝{reset}     {cyan}║
║{reset}     {cyan}██║{reset}   {white}██║{cyan}██║ ╚═╝ ██║███████╗{reset}{white}███████╗██║{cyan}██║ ╚████║███████╗{reset}   {cyan}║
║{reset}     {cyan}╚═╝{reset}   {white}╚═╝╚═╝     ╚═╝╚══════╝{reset}{white}╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝{reset}   {cyan}║
║{reset}                                                                 {cyan}║
║{reset}    {magenta}███████╗{reset}  {white}██╗{magenta}███╗   ███╗ █████╗  ██████╗ ███████╗███████║{reset}    {cyan}║
║{reset}    {magenta}╚════██║{reset}  {white}██║{magenta}████╗ ████║██╔══██╗██╔════╝ ██╔════╝██╔════╝{reset}    {cyan}║
║{reset}     {magenta}█████╔╝{reset}  {white}██║{magenta}██╔████╔██║███████║██║  ███╗█████╗  ███████║{reset}    {cyan}║
║{reset}    {magenta}██╔═══╝{reset}   {white}██║{magenta}██║╚██╔╝██║██╔══██║██║   ██║██╔══╝  ╚════██║{reset}    {cyan}║
║{reset}    {magenta}███████╗{reset}  {white}██║{magenta}██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗███████║{reset}    {cyan}║
║{reset}    {magenta}╚══════╝{reset}  {white}╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝{reset}    {cyan}║
║{reset}                                                                 {cyan}║
║{reset}        {white}Generate daily route maps from Google Timeline{reset}           {cyan}║
║{reset}                                                                 {cyan}║
╚═════════════════════════════════════════════════════════════════╝{reset}
"""
    print(banner)


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
        load_timing: dict = {}
        if profile:
            result = load_segments_for_day(str(timeline_path), date_str, profile=True)
            segments, load_timing = cast(tuple[list[dict], dict], result)
        else:
            segments = cast(list[dict], load_segments_for_day(str(timeline_path), date_str))

        if not segments:
            print("✗ No segments found")
            return False, time.time() - start_time, {}

        output_file = output_path / f"timeline_{date_str}.jpg"
        cache_info_before = get_render_cache_info()
        render_timing = render_segments(
            segments, str(output_file), image_size=image_size, profile=profile
        )
        cache_info_after = get_render_cache_info()

        total_points = sum(len(seg.get("waypoints", [])) for seg in segments)
        elapsed = time.time() - start_time
        output_name = output_file.name

        cache_info = {
            "cache_status": cache_info_after.get("status", "unknown"),
            "total_cached": cache_info_after.get("total_cached_tiles", 0),
        }

        cache_indicator = ""
        if cache_info_after.get("total_cached_tiles", 0) > cache_info_before.get(
            "total_cached_tiles", 0
        ):
            cache_indicator = " 💾"

        details = (
            f"({len(segments)} segments, {total_points} points) {elapsed:.2f}s{cache_indicator}"
        )
        print(f"✓ {details} → {output_name}")

        if profile:
            print("      Timing breakdown:")
            if "load_timing" in locals() and load_timing:
                print("        Load Segments:")
                for key, value in sorted(load_timing.items()):
                    if key not in ("total", "cache_source") and isinstance(value, (int, float)):
                        pct = (
                            (value / load_timing["total"] * 100) if load_timing["total"] > 0 else 0
                        )
                        print(f"          {key:.<20} {value:6.2f}s ({pct:5.1f}%)")
                print(f"          {('total'):.<20} {load_timing.get('total', 0):6.2f}s")
            print("        Render Segments:")
            if render_timing:
                for key, value in sorted(render_timing.items()):
                    if key != "total":
                        pct = (
                            (value / render_timing["total"] * 100)
                            if render_timing["total"] > 0
                            else 0
                        )
                        print(f"          {key:.<20} {value:6.2f}s ({pct:5.1f}%)")
                print(f"          {('total'):.<20} {render_timing.get('total', 0):6.2f}s")

        return True, elapsed, cache_info
    except ValueError as e:
        print(f"✗ {e}")
    except (OSError, RuntimeError) as e:
        print(f"✗ Error: {e}")
    return False, time.time() - start_time, {}


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
    _print_banner()
    timeline_path = Path(timeline_json)
    if not timeline_path.exists():
        print(f"Error: Timeline file not found: {timeline_json}")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    print(f"Loading timeline data from {timeline_json}...", end=" ", flush=True)
    load_start = time.time()
    target_dates = get_date_range(
        str(timeline_path), start_date=start_date, end_date=end_date, days=days
    )
    load_time = time.time() - load_start
    cache_source = get_cache_source()
    cache_label = {
        "session": "session cache",
        "disk": "disk cache",
        "parsed": "parsed from JSON",
    }.get(cache_source, "unknown")
    print(f"✓ ({load_time:.2f}s, {cache_label})")

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
        _process_date(date_str, timeline_path, output_path, image_size, profile)
        for date_str in target_dates
    ]
    success_count = sum(1 for success, _, _ in results if success)
    total_time = time.time() - start_time
    day_times = [elapsed for _, elapsed, _ in results]

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
        disk_cache_info = cache_stats.get("disk_cache", {})
        tile_count = disk_cache_info.get("tile_count", 0)
        cache_size = disk_cache_info.get("total_size_mb", 0.0)
        print(f"  Backend: {cache_stats.get('cache_backend', 'requests-cache')}")
        print(f"  Cache location: {cache_stats.get('cache_location', '.tile_cache')}")
        if tile_count > 0:
            print(f"  Cached tiles: {tile_count} tiles ({cache_size:.1f}MB)")
        print("  Note: Tiles are automatically reused for overlapping geographic areas")


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
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Show detailed timing breakdown for each rendering operation",
    )

    args = parser.parse_args()
    main(
        args.timeline_json,
        args.output_dir,
        args.days,
        args.image_size,
        args.start_date,
        args.end_date,
        args.profile,
    )
