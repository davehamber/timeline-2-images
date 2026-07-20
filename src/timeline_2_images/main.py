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
from timeline_2_images.config import RenderConfiguration
from timeline_2_images.validators import TimelineValidationError
from timeline_2_images.console_formatter import ConsoleFormatter


class CLIRunner:
    """Handles CLI argument parsing and timeline processing orchestration."""

    def initialize_app(
        self, timeline_json: str, output_dir: str, image_size: int, place_names: bool
    ) -> TimelineApp:
        """Initialize TimelineApp with CLI configuration.

        Args:
            timeline_json: Path to Timeline.json file
            output_dir: Output directory for images
            image_size: Size of output images in pixels
            place_names: Whether to add place names to maps

        Returns:
            Initialized TimelineApp instance

        Raises:
            SystemExit: If Timeline.json validation fails
        """
        try:
            config = RenderConfiguration(image_size=image_size, add_place_names=place_names)
            return TimelineApp(str(timeline_json), output_dir=output_dir, config=config)
        except TimelineValidationError as e:
            ConsoleFormatter.print_error(str(e))
            sys.exit(1)

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
        """Process and render timeline images.

        Args:
            timeline_json: Path to Timeline.json file
            output_dir: Output directory for images
            days: Number of days to process
            image_size: Size of output images in pixels
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            place_names: Whether to add place names to maps
            single_image: Whether to render as single combined image
        """
        app = self.initialize_app(timeline_json, output_dir, image_size, place_names)
        timeline_path = Path(timeline_json)

        # Load and display available dates
        load_start = time.time()
        available_dates = app.get_available_dates()
        load_time = time.time() - load_start
        ConsoleFormatter.print_loading_timeline(str(timeline_path), load_time)

        if not available_dates:
            ConsoleFormatter.print_no_data_found()
            sys.exit(1)

        ConsoleFormatter.print_available_dates(available_dates)

        # Get dates to process
        dates_to_process = app.get_date_range(start_date=start_date, end_date=end_date, days=days)

        ConsoleFormatter.print_processing_message(dates_to_process)

        start_time = time.time()
        results: list[Any] = []

        # Process images
        if single_image:
            result = app.process_date_range_single_image(
                start_date=start_date, end_date=end_date, days=days
            )
            results.append(result)
            ConsoleFormatter.print_single_image_result(result)
        else:
            for date in dates_to_process:
                result = app.process_date(date)
                results.append(result)
                ConsoleFormatter.print_render_result(result)

        # Print summary
        total_time = time.time() - start_time
        ConsoleFormatter.print_results_summary(results, output_dir, total_time)
        ConsoleFormatter.print_cache_info(app.renderer.get_cache_info())

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
        if args.timeline_json:
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


def main(
    timeline_json: str,
    output_dir: str = "output",
    days: int = 14,
    image_size: int = 500,
    start_date: str | None = None,
    end_date: str | None = None,
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
