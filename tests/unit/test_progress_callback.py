"""Unit tests for progress callback functionality."""

from timeline_2_images.app import TimelineApp, ProgressCallback


class TestProgressCallback:
    """Tests for progress callback in batch operations."""

    def test_progress_callback_type_alias(self):
        """Test that ProgressCallback type alias is defined."""
        assert ProgressCallback is not None

    def test_process_date_range_with_progress(self, sample_timeline_json, tmp_path):
        """Test process_date_range with progress callback."""
        app = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "output"),
            validate=False,
        )

        progress_calls = []

        def on_progress(completed: int, total: int):
            progress_calls.append((completed, total))

        app.process_date_range(days=7, on_progress=on_progress)

        # Should have called progress callback after each date
        assert len(progress_calls) > 0
        # Last call should show 100% completion
        assert progress_calls[-1][0] == progress_calls[-1][1]

    def test_process_date_range_without_progress(self, sample_timeline_json, tmp_path):
        """Test process_date_range works without progress callback."""
        app = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "output"),
            validate=False,
        )

        results = app.process_date_range(days=7)
        assert results is not None

    def test_process_date_range_bytes_with_progress(self, sample_timeline_json, tmp_path):
        """Test process_date_range_bytes with progress callback."""
        app = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "output"),
            validate=False,
        )

        progress_calls = []

        def on_progress(completed: int, total: int):
            progress_calls.append((completed, total))

        app.process_date_range_bytes(days=7, on_progress=on_progress)

        # Should have called progress callback after each date
        assert len(progress_calls) > 0
        # Last call should show 100% completion
        assert progress_calls[-1][0] == progress_calls[-1][1]

    def test_progress_callback_counts(self, sample_timeline_json, tmp_path):
        """Test that progress callback receives correct counts."""
        app = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "output"),
            validate=False,
        )

        progress_calls = []

        def on_progress(completed: int, total: int):
            progress_calls.append((completed, total))

        app.process_date_range(days=7, on_progress=on_progress)

        # Check progress increments correctly
        if progress_calls:
            total = progress_calls[0][1]
            for i, (completed, reported_total) in enumerate(progress_calls):
                # Total should be consistent
                assert reported_total == total
                # Completed should increment
                assert completed == i + 1

    def test_process_date_range_single_image_with_progress(self, sample_timeline_json, tmp_path):
        """Test process_date_range_single_image with progress callback."""
        app = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "output"),
            validate=False,
        )

        progress_calls = []

        def on_progress(completed: int, total: int):
            progress_calls.append((completed, total))

        app.process_date_range_single_image(days=7, on_progress=on_progress)

        # Should have called progress callback (at least start and end)
        assert len(progress_calls) > 0
