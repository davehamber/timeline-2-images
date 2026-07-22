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
from timeline_2_images.config.render_configuration import MIN_IMAGE_SIZE, MAX_IMAGE_SIZE
from timeline_2_images.validators import TimelineValidationError
from timeline_2_images.console_formatter import ConsoleFormatter


class CLIRunner:
    """Handles CLI argument parsing and timeline processing orchestration."""

    @staticmethod
    def _validate_image_size(value: str) -> int:
        """Validate image size argument.

        Args:
            value: String value from argparse

        Returns:
            Valid integer image size

        Raises:
            argparse.ArgumentTypeError: If value is invalid
        """
        try:
            size = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"image size must be an integer, got '{value}'")

        if size < MIN_IMAGE_SIZE:
            raise argparse.ArgumentTypeError(
                f"image size must be at least {MIN_IMAGE_SIZE} pixels, got {size}"
            )

        if size > MAX_IMAGE_SIZE:
            raise argparse.ArgumentTypeError(
                f"image size must not exceed {MAX_IMAGE_SIZE} pixels, got {size}"
            )

        return size

    @staticmethod
    def _validate_days(value: str) -> int:
        """Validate days argument.

        Args:
            value: String value from argparse

        Returns:
            Valid positive integer number of days

        Raises:
            argparse.ArgumentTypeError: If value is invalid
        """
        try:
            days = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"days must be an integer, got '{value}'")

        if days < 1:
            raise argparse.ArgumentTypeError("days must be positive (minimum 1 day)")

        return days

    def validate_dates(self, start_date: str | None, end_date: str | None, days: int) -> None:
        """Validate date arguments from CLI.

        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            days: Number of days to process

        Raises:
            SystemExit: If dates are invalid
        """
        try:
            query = DateRangeQuery(start_date=start_date, end_date=end_date, days=days)
            query.validate()
        except ValueError as e:
            ConsoleFormatter.print_error(f"Invalid date arguments: {str(e)}")
            sys.exit(1)

    def initialize_app(
        self,
        timeline_json: str,
        output_dir: str,
        image_width: int,
        image_height: int,
        place_names: bool,
    ) -> TimelineApp:
        """Initialize TimelineApp with CLI configuration.

        Args:
            timeline_json: Path to Timeline.json file
            output_dir: Output directory for images
            image_width: Width of output images in pixels
            image_height: Height of output images in pixels
            place_names: Whether to add place names to maps

        Returns:
            Initialized TimelineApp instance

        Raises:
            SystemExit: If Timeline.json validation fails
        """
        try:
            config = RenderConfiguration(
                image_width=image_width, image_height=image_height, add_place_names=place_names
            )
            return TimelineApp(str(timeline_json), output_dir=output_dir, config=config)
        except TimelineValidationError as e:
            ConsoleFormatter.print_error(str(e))
            sys.exit(1)

    def process_images(
        self,
        timeline_json: str,
        output_dir: str,
        days: int,
        image_width: int,
        image_height: int,
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
            image_width: Width of output images in pixels
            image_height: Height of output images in pixels
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            place_names: Whether to add place names to maps
            single_image: Whether to render as single combined image
        """
        self.validate_dates(start_date, end_date, days)
        app = self.initialize_app(timeline_json, output_dir, image_width, image_height, place_names)
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
            "--days",
            type=self._validate_days,
            default=14,
            help="Number of days to process (default: 14)",
        )
        parser.add_argument(
            "--image-size",
            type=self._validate_image_size,
            default=None,
            help=f"Output image size in pixels (sets both width and height, {MIN_IMAGE_SIZE}-{MAX_IMAGE_SIZE})",
        )
        parser.add_argument(
            "--image-width",
            type=self._validate_image_size,
            default=None,
            help=f"Output image width in pixels ({MIN_IMAGE_SIZE}-{MAX_IMAGE_SIZE}, default: 500)",
        )
        parser.add_argument(
            "--image-height",
            type=self._validate_image_size,
            default=None,
            help=f"Output image height in pixels ({MIN_IMAGE_SIZE}-{MAX_IMAGE_SIZE}, default: 500)",
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
            # Handle image size: --image-size sets both, or use separate --image-width/height
            if args.image_size is not None:
                image_width = args.image_size
                image_height = args.image_size
            else:
                image_width = args.image_width if args.image_width is not None else 500
                image_height = args.image_height if args.image_height is not None else 500

            self.process_images(
                args.timeline_json,
                args.output_dir,
                args.days,
                image_width,
                image_height,
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
    image_size: int | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
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
        image_size: Output image size in pixels (sets both width and height, default 500)
        image_width: Output image width in pixels (overrides image_size, default 500)
        image_height: Output image height in pixels (overrides image_size, default 500)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        place_names: If True, add place names to maps (default: True)
        single_image: If True, combine all dates into single image (default: False)
    """
    # Handle backward compatibility: image_size sets both width and height
    width = (
        image_size if image_size is not None else (image_width if image_width is not None else 500)
    )
    height = (
        image_size
        if image_size is not None
        else (image_height if image_height is not None else 500)
    )

    runner = CLIRunner()
    runner.process_images(
        timeline_json,
        output_dir,
        days,
        width,
        height,
        start_date,
        end_date,
        place_names,
        single_image,
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
