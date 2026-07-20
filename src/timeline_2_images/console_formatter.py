"""Console output formatting for CLI."""

from typing import Any


class ConsoleFormatter:
    """Formats and outputs console messages for CLI operations."""

    @staticmethod
    def print_loading_timeline(timeline_path: str, load_time: float) -> None:
        """Print timeline loading message."""
        print(f"Loading timeline data from {timeline_path}... ✓ ({load_time:.2f}s)")

    @staticmethod
    def print_available_dates(available_dates: list[str]) -> None:
        """Print available dates information."""
        if not available_dates:
            print("No timeline data found")
            return

        print(f"Found {len(available_dates)} days with data")
        print(f"Date range: {available_dates[0]} to {available_dates[-1]}")
        print()

    @staticmethod
    def print_processing_message(dates_to_process: list[str]) -> None:
        """Print message about which dates will be processed."""
        if dates_to_process:
            print(f"Processing dates {dates_to_process[0]} to {dates_to_process[-1]}...")
        else:
            print("Processing dates...")

    @staticmethod
    def print_render_result(result: Any) -> None:
        """Print a single render result."""
        status = "✓" if result.was_successful() else "✗"
        if result.was_successful():
            time_str = f"{result.render_time:.2f}s"
            points_str = f"({result.point_count} points)"
            print(f"{status} {result.date}: {time_str} {points_str}")
        else:
            print(f"{status} {result.date}: {result.error_message}")

    @staticmethod
    def print_single_image_result(result: Any) -> None:
        """Print result for single combined image."""
        status = "✓" if result.was_successful() else "✗"
        print()
        if result.was_successful():
            print(
                f"{status} {result.date}: {result.render_time:.2f}s ({result.point_count} points)"
            )
        else:
            print(f"{status} {result.date}: {result.error_message}")

    @staticmethod
    def print_results_summary(results: list[Any], output_dir: str, total_time: float) -> None:
        """Print summary of render results."""
        success_count = sum(1 for r in results if r.was_successful())

        print()
        print(f"Generated {success_count}/{len(results)} map images in {output_dir}")
        print(f"Total time: {total_time:.2f}s")

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

    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message."""
        print("Error: Invalid Timeline.json structure")
        print(f"  {message}")

    @staticmethod
    def print_no_data_found() -> None:
        """Print message when no timeline data found."""
        print("No timeline data found")
