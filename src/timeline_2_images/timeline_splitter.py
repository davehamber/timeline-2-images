"""Split Timeline JSON by year into separate files."""

import json
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict

from timeline_2_images.timeline_parser import _parse_semantic_segments_iter


def split_timeline_by_year(json_path: str, output_dir: str = "timelines") -> Dict[int, str]:
    """
    Split a Timeline JSON file into separate files by year.

    Args:
        json_path: Path to Timeline.json file
        output_dir: Directory to save yearly timeline files

    Returns:
        Dictionary mapping year -> output file path
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    print(f"Loading Timeline from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Group data by year
    yearly_data: Dict[int, Dict[str, Any]] = defaultdict(
        lambda: {
            "semanticSegments": [],
            "rawSignals": data.get("rawSignals", []),
            "userLocationProfile": data.get("userLocationProfile", {}),
        }
    )

    # Process semanticSegments
    total_segments = 0
    for seg, dt in _parse_semantic_segments_iter(data):
        year = dt.year
        yearly_data[year]["semanticSegments"].append(seg)
        total_segments += 1

    # Save yearly files
    year_to_path = {}
    for year in sorted(yearly_data.keys()):
        output_file = output_path / f"timeline_{year}.json"
        segment_count = len(yearly_data[year]["semanticSegments"])

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(yearly_data[year], f, indent=2)

        file_size = output_file.stat().st_size / 1024 / 1024
        print(f"  {year}: {segment_count:6d} segments → {output_file.name} ({file_size:.1f}MB)")

        year_to_path[year] = str(output_file)

    print(f"\nTotal segments processed: {total_segments}")
    print(f"Split into {len(year_to_path)} yearly files in {output_path}/")

    return year_to_path


def _load_yearly_file(year_file: Path) -> Dict[str, Any]:
    """Load a yearly timeline file."""
    with open(year_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge_year_file_data(merged_data: Dict[str, Any], year_data: Dict[str, Any]):
    """Merge a single year's data into merged_data."""
    segments = merged_data.get("semanticSegments", [])
    if isinstance(segments, list):
        segments.extend(year_data.get("semanticSegments", []))

    if year_data.get("userLocationProfile") and not merged_data.get("userLocationProfile"):
        merged_data["userLocationProfile"] = year_data["userLocationProfile"]


def _sort_segments_by_starttime(merged_data: Dict[str, Any]):
    """Sort segments by startTime in descending order."""
    segments = merged_data.get("semanticSegments", [])
    if isinstance(segments, list):
        segments.sort(
            key=lambda x: x.get("startTime", "") if isinstance(x, dict) else "", reverse=True
        )


def _write_merged_file(output_file: Path, merged_data: Dict[str, Any]):
    """Write merged data to file and print summary."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f)

    file_size = output_file.stat().st_size / 1024 / 1024
    print(f"Merged file: {output_file.name} ({file_size:.1f}MB)")
    print(f"Total segments: {len(merged_data.get('semanticSegments', []))}")


def merge_timelines(timeline_dir: str, output_path: str = "Timeline_merged.json"):
    """
    Merge yearly timeline files back into a single file.

    Args:
        timeline_dir: Directory containing yearly timeline files
        output_path: Output merged timeline file path
    """
    timeline_path = Path(timeline_dir)
    output_file = Path(output_path)

    merged_data: Dict[str, Any] = {
        "semanticSegments": [],
        "rawSignals": [],
        "userLocationProfile": {},
    }

    for year_file in sorted(timeline_path.glob("timeline_*.json")):
        print(f"Reading {year_file.name}...", end=" ", flush=True)
        data = _load_yearly_file(year_file)
        _merge_year_file_data(merged_data, data)
        print(f"✓ ({len(data.get('semanticSegments', []))} segments)")

    _sort_segments_by_starttime(merged_data)

    print(f"\nWriting merged timeline to {output_path}...")
    _write_merged_file(output_file, merged_data)
