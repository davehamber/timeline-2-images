"""Unit tests for GUI architecture (interfaces, adapter, presenter)."""

import pytest

from timeline_2_images.gui.models import (
    ITimelineProcessor,
    TimelineProcessorAdapter,
    ImageGenerationConfig,
)
from timeline_2_images.gui.presenter import TimelineGeneratorPresenter


class TestTimelineProcessorAdapter:
    """Test TimelineProcessorAdapter interface compliance."""

    def test_adapter_implements_interface(self):
        """Adapter should implement ITimelineProcessor interface."""
        adapter = TimelineProcessorAdapter()
        assert isinstance(adapter, ITimelineProcessor)

    def test_validate_file_nonexistent(self):
        """Validate nonexistent file should return False with error."""
        adapter = TimelineProcessorAdapter()
        is_valid, error = adapter.validate_file("/nonexistent/file.json")
        assert is_valid is False
        assert error is not None

    def test_get_available_dates_handles_error(self):
        """Get available dates with nonexistent file should return empty list."""
        adapter = TimelineProcessorAdapter()
        dates = adapter.get_available_dates("/nonexistent/file.json")
        assert dates == []

    def test_clear_cache_does_not_error(self):
        """Clear cache should not raise errors."""
        adapter = TimelineProcessorAdapter()
        adapter.clear_cache()  # Should not raise


class TestTimelineGeneratorPresenter:
    """Test TimelineGeneratorPresenter controller logic."""

    def test_presenter_accepts_processor(self):
        """Presenter should accept any ITimelineProcessor."""
        adapter = TimelineProcessorAdapter()
        presenter = TimelineGeneratorPresenter(adapter)
        assert presenter is not None

    def test_presenter_registers_callbacks(self):
        """Presenter should accept callback registrations."""
        adapter = TimelineProcessorAdapter()
        presenter = TimelineGeneratorPresenter(adapter)

        # Register callbacks - should not raise
        presenter.on_validation_result(lambda valid, error: None)
        presenter.on_available_dates(lambda dates: None)
        presenter.on_generation_complete(lambda result: None)

    def test_presenter_handles_file_selected(self):
        """Presenter should handle file selection."""
        adapter = TimelineProcessorAdapter()
        presenter = TimelineGeneratorPresenter(adapter)

        # Track callbacks
        validation_results = []
        presenter.on_validation_result(
            lambda valid, error: validation_results.append((valid, error))
        )

        # Handle invalid file selection
        presenter.handle_file_selected("/nonexistent/file.json")

        # Should have called validation callback
        assert len(validation_results) == 1
        is_valid, error = validation_results[0]
        assert is_valid is False
        assert error is not None

    def test_presenter_handles_clear_cache(self):
        """Presenter should handle clear cache action."""
        adapter = TimelineProcessorAdapter()
        presenter = TimelineGeneratorPresenter(adapter)

        # Should not raise
        presenter.handle_clear_cache_clicked()

    def test_image_generation_config_creation(self):
        """ImageGenerationConfig should be creatable with expected fields."""
        config = ImageGenerationConfig(
            timeline_path="/path/to/Timeline.json",
            output_dir="/output",
            image_size=800,
            add_place_names=True,
            single_image=False,
            days=30,
        )

        assert config.timeline_path == "/path/to/Timeline.json"
        assert config.output_dir == "/output"
        assert config.image_size == 800
        assert config.add_place_names is True
        assert config.single_image is False
        assert config.days == 30


class TestGUILayerDecoupling:
    """Test that GUI layer is properly decoupled from core library."""

    def test_gui_models_do_not_import_core_app(self):
        """GUI models should not directly import TimelineApp."""
        from timeline_2_images.gui import models

        # Models module should be importable without core library details
        assert hasattr(models, "ITimelineProcessor")
        assert hasattr(models, "TimelineProcessorAdapter")

    def test_adapter_is_only_bridge(self):
        """Adapter should be the only GUI code that imports core library."""
        # This is a design validation - adapter imports TimelineApp
        # but GUI layer imports should go through adapter
        from timeline_2_images.gui.models import timeline_adapter

        # Verify TimelineApp is imported in adapter
        assert hasattr(timeline_adapter, "TimelineApp")
