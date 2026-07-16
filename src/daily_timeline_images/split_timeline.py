"""CLI for splitting Timeline JSON by year."""

import sys
from pathlib import Path

from daily_timeline_images.timeline_splitter import split_timeline_by_year, merge_timelines


def main():
    """Command-line interface for timeline splitting."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Split or merge Google Timeline exports by year"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Split command
    split_parser = subparsers.add_parser("split", help="Split Timeline.json by year")
    split_parser.add_argument("timeline_json", help="Path to Timeline.json file")
    split_parser.add_argument(
        "--output-dir", default="timelines", help="Output directory for yearly files"
    )

    # Merge command
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
        timeline_path = Path(args.timeline_json)
        if not timeline_path.exists():
            print(f"Error: Timeline file not found: {args.timeline_json}")
            sys.exit(1)

        split_timeline_by_year(str(timeline_path), args.output_dir)

    elif args.command == "merge":
        timeline_dir = Path(args.timeline_dir)
        if not timeline_dir.exists():
            print(f"Error: Timeline directory not found: {args.timeline_dir}")
            sys.exit(1)

        merge_timelines(str(timeline_dir), args.output)


if __name__ == "__main__":
    main()
