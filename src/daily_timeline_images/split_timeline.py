"""CLI for splitting Timeline JSON by year."""

import argparse
import sys
from pathlib import Path

from daily_timeline_images.timeline_splitter import split_timeline_by_year, merge_timelines


def _handle_split(timeline_json: str, output_dir: str):
    """Handle split command."""
    timeline_path = Path(timeline_json)
    if not timeline_path.exists():
        print(f"Error: Timeline file not found: {timeline_json}")
        sys.exit(1)
    split_timeline_by_year(str(timeline_path), output_dir)


def _handle_merge(timeline_dir: str, output: str):
    """Handle merge command."""
    path = Path(timeline_dir)
    if not path.exists():
        print(f"Error: Timeline directory not found: {timeline_dir}")
        sys.exit(1)
    merge_timelines(str(path), output)


def main():
    """Command-line interface for timeline splitting."""
    parser = argparse.ArgumentParser(
        description="Split or merge Google Timeline exports by year"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    split_parser = subparsers.add_parser("split", help="Split Timeline.json by year")
    split_parser.add_argument("timeline_json", help="Path to Timeline.json file")
    split_parser.add_argument(
        "--output-dir", default="timelines", help="Output directory for yearly files"
    )

    merge_parser = subparsers.add_parser("merge", help="Merge yearly timeline files")
    merge_parser.add_argument("timeline_dir", help="Directory containing yearly timeline files")
    merge_parser.add_argument(
        "--output", default="Timeline_merged.json", help="Output merged timeline file"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "split":
        _handle_split(args.timeline_json, args.output_dir)
    elif args.command == "merge":
        _handle_merge(args.timeline_dir, args.output)


if __name__ == "__main__":
    main()
