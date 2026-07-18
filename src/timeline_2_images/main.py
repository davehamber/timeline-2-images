# SPDX-License-Identifier: EUPL-1.2
# Copyright (c) 2026 David Hamber

"""Entry point for rendering timeline images using the OOP architecture."""

import sys
import time
import argparse
from pathlib import Path
from typing import Any

from timeline_2_images.banner import print_banner
from timeline_2_images.app import TimelineApp
from timeline_2_images.config import RenderConfiguration, DateRangeQuery
from timeline_2_images.sqlite_cache import clean_all_cache
from timeline_2_images.timeline_validator import (
    validate_timeline_structure,
    TimelineValidationError,
)


class CLIRunner:
    """Handles CLI argument parsing and timeline processing orchestration."""

    def __init__(self):
        self.app: TimelineApp | None = None
        self.timeline_path: Path | None = None

    def load_and_validate_app(
        self, timeline_json: str, output_dir: str, image_size: int, place_names: bool
    ) -> TimelineApp:
        """Validate Timeline.json and initialize TimelineApp."""
        try:
            validate_timeline_structure(timeline_json)
        except TimelineValidationError as e:
            print("Error: Invalid Timeline.json structure")
            print(f"  {e}")
            sys.exit(1)

        config = RenderConfiguration(image_size=image_size, add_place_names=place_names)
        return TimelineApp(str(timeline_json), output_dir=output_dir, config=config)

    @staticmethod
    def load_available_dates(app: TimelineApp, timeline_path: Path) -> list[str]:
        """Load available dates from timeline."""
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
        return available_dates

    @staticmethod
    def print_cache_info(cache_info: dict) -> None:
        """Print cache information."""
        if not cache_info:
            return
        print()
        print("Cache Information:")
        print(f"  Location: {cache_info.get('cache_dir', 'unknown')}")
        print(f"  Status: {cache_info.get('status', 'unknown')}")
        if cache_info.get("status") == "cached":
            print(f"  Cached tiles: {cache_info.get('total_cached_tiles', 0)}")
        print(f"  Size: {cache_info.get('cache_size_mb', 0):.1f}MB")

    def process_images(
        self,
        timeline_json: str,
        output_dir: str,
        days: int,
        image_size: int,
        start_date: str | None,
        end_date: str | None,
        place_names: bool,
        single_image: bool,
    ) -> None:
        """Process and render timeline images."""
        self.timeline_path = Path(timeline_json)
        self.app = self.load_and_validate_app(timeline_json, output_dir, image_size, place_names)
        self.load_available_dates(self.app, self.timeline_path)

        query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
        dates_to_process = self.app.processor.get_date_range(query)

        if dates_to_process:
            print(f"Processing dates {dates_to_process[0]} to {dates_to_process[-1]}...")
        else:
            print("Processing dates...")

        start_time = time.time()
        results: list[Any] = []

        if single_image:
            self._process_single_image(start_date, end_date, days, results)
        else:
            self._process_multiple_dates(dates_to_process, results)

        self._print_results_summary(results, output_dir, start_time)

    def _process_single_image(
        self, start_date: str | None, end_date: str | None, days: int, results: list
    ) -> None:
        """Process date range as single combined image."""
        assert self.app is not None
        result = self.app.process_date_range_single_image(
            start_date=start_date, end_date=end_date, days=days
        )
        results.append(result)

        status = "✓" if result.was_successful() else "✗"
        print()
        if result.was_successful():
            print(
                f"{status} {result.date}: {result.render_time:.2f}s ({result.point_count} points)"
            )
        else:
            print(f"{status} {result.date}: {result.error_message}")

    def _process_multiple_dates(self, dates_to_process: list[str], results: list) -> None:
        """Process each date individually."""
        assert self.app is not None
        for date in dates_to_process:
            result = self.app.process_date(date)
            results.append(result)

            status = "✓" if result.was_successful() else "✗"
            if result.was_successful():
                time_str = f"{result.render_time:.2f}s"
                points_str = f"({result.point_count} points)"
                print(f"{status} {result.date}: {time_str} {points_str}")
            else:
                print(f"{status} {result.date}: {result.error_message}")

    def _print_results_summary(self, results: list, output_dir: str, start_time: float) -> None:
        """Print final results summary and cache info."""
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.was_successful())

        print()
        print(f"Generated {success_count}/{len(results)} map images in {output_dir}")
        print(f"Total time: {total_time:.2f}s")

        assert self.app is not None
        self.print_cache_info(self.app.renderer.get_cache_info())

    def build_argument_parser(self) -> argparse.ArgumentParser:
        """Build and return argument parser."""
        prog_name = Path(sys.argv[0]).name
        parser = argparse.ArgumentParser(
            prog=prog_name, description="Generate daily route maps from Google Timeline exports"
        )
        parser.add_argument("timeline_json", nargs="?", help="Path to Timeline.json file")
        parser.add_argument(
            "--output-dir", default="output", help="Output directory for JPG images"
        )
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
        parser.add_argument(
            "--no-place-names",
            action="store_true",
            help="Disable adding place names to maps",
        )
        parser.add_argument(
            "--single-image",
            action="store_true",
            help="Combine all dates into single image with connected routes",
        )
        return parser

    def run(self, args: argparse.Namespace) -> None:
        """Execute CLI commands based on parsed arguments."""
        if args.clean_cache:
            self._handle_clean_cache()
        elif args.timeline_json:
            self.process_images(
                args.timeline_json,
                args.output_dir,
                args.days,
                args.image_size,
                args.start_date,
                args.end_date,
                not args.no_place_names,
                args.single_image,
            )
        else:
            parser = self.build_argument_parser()
            parser.print_help()
            sys.exit(1)

    @staticmethod
    def _handle_clean_cache() -> None:
        """Handle cache cleaning operation."""
        try:
            clean_all_cache()
            print("Cache cleaned successfully")
        except RuntimeError as exception:
            print(f"Error: {exception}")
            sys.exit(1)


def main(
    timeline_json: str,
    output_dir: str = "output",
    days: int = 14,
    image_size: int = 500,
    start_date: str | None = None,
    end_date: str | None = None,
    profile: bool = False,  # pylint: disable=unused-argument
    place_names: bool = True,
    single_image: bool = False,
) -> None:
    """Generate daily route maps from Timeline JSON export.

    Args:
        timeline_json: Path to Timeline.json file
        output_dir: Directory to save JPG images
        days: Number of recent days to process (default 14)
        image_size: Output image size in pixels (default 500)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        profile: If True, show detailed timing breakdown per operation
        place_names: If True, add place names to maps (default: True)
        single_image: If True, combine all dates into single image (default: False)
    """
    runner = CLIRunner()
    runner.process_images(
        timeline_json, output_dir, days, image_size, start_date, end_date, place_names, single_image
    )


def cli() -> None:
    """CLI entry point called by setuptools console script.

    Parses command-line arguments and calls main().
    This function is configured in pyproject.toml as the entry point.
    """
    print_banner()

    runner = CLIRunner()
    parser = runner.build_argument_parser()
    args = parser.parse_args()
    runner.run(args)


if __name__ == "__main__":
    cli()
