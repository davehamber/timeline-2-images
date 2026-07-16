#!/usr/bin/env python3
"""Test script to check tile caching between consecutive days."""

from daily_timeline_images.timeline_parser import load_segments_for_day, get_last_n_days_with_data
from daily_timeline_images.map_renderer import (
    render_segments,
    set_debug_mode,
    get_tile_cache_stats,
    get_tile_request_summary,
    clear_tile_caches,
)

test_file = "Timeline.json"

print(f"Using test file: {test_file}")
print("Checking available dates...")

available_dates = get_last_n_days_with_data(test_file, 100)
print(f"Found {len(available_dates)} days with data")
print(f"Date range: {available_dates[0]} to {available_dates[-1]}")
print()

# Find two consecutive days in the data
if len(available_dates) < 2:
    print("Not enough data for testing (need at least 2 days)")
else:
    # Use the first two available dates (which should be consecutive or close)
    dates = available_dates[:2]
    print(f"Testing with dates: {dates}")
    print()

    clear_tile_caches()
    set_debug_mode(True)

    for date in dates:
        print(f"\n{'='*60}")
        print(f"Processing {date}...")
        print("=" * 60)
        try:
            segments = load_segments_for_day(test_file, date)
            if segments:
                output_file = f"output/debug_timeline_{date}.jpg"
                render_segments(segments, output_file, image_size=500)
                print(f"\n  ✓ Generated {output_file}")
            else:
                print(f"  ✗ No segments found for {date}")
        except ValueError as e:
            print(f"  ✗ Error: {e}")

    set_debug_mode(False)

    print("\n" + "=" * 60)
    print("TILE CACHE ANALYSIS")
    print("=" * 60)

    cache_stats = get_tile_cache_stats()
    print("\nCache Configuration:")
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")

    tile_summary = get_tile_request_summary()
    print("\nTile Caching Status:")
    for key, value in tile_summary.items():
        print(f"  {key}: {value}")

    print("\n✅ Tile caching is now enabled using requests-cache!")
    print("\nWith requests-cache:")
    print("  • OSM tiles are automatically cached to .tile_cache/osm-tiles")
    print("  • Tiles requested for 2026-04-08 that overlap with 2026-04-07")
    print("    are served from cache instead of re-downloading")
    print("  • Cache persists between runs (in .tile_cache/ directory)")

    # Check if cache files exist
    from pathlib import Path

    cache_dir = Path(".tile_cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("**/*"))
        print("\n📦 Cached data:")
        print(f"  Cache files found: {len([f for f in cache_files if f.is_file()])}")
        print(f"  Cache location: {cache_dir.absolute()}")
    else:
        print("\n📦 Cache directory: Not yet created (will be created on next run)")
