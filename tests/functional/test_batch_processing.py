"""Functional tests for batch processing with BatchConfig."""

import pytest

from timeline_2_images.app import TimelineApp
from timeline_2_images.config import BatchConfig, RenderConfiguration


class TestBatchProcessing:
    """Tests for batch processing with resource pooling."""

    def test_single_app_with_batch_config(self, sample_timeline_json):
        """Test TimelineApp with BatchConfig."""
        batch_config = BatchConfig()
        app = TimelineApp(
            sample_timeline_json,
            output_dir="output_batch",
            batch_config=batch_config,
            validate=False,
        )

        assert app.config is batch_config.render_config
        assert app.renderer is not None

    def test_multiple_apps_share_resources(self, tmp_path, sample_timeline_json):
        """Test that multiple apps with same BatchConfig share resources."""
        batch_config = BatchConfig()

        app1 = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "out1"),
            batch_config=batch_config,
            validate=False,
        )

        app2 = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "out2"),
            batch_config=batch_config,
            validate=False,
        )

        # Both apps should use the same geocoder
        assert app1.renderer.geocoder is app2.renderer.geocoder
        # Both apps should use the same tile cache
        assert app1.renderer.tile_cache is app2.renderer.tile_cache

    def test_batch_config_overrides_individual_config(self, tmp_path, sample_timeline_json):
        """Test that BatchConfig overrides individual config parameter."""
        batch_render_config = RenderConfiguration(image_size=800)
        batch_config = BatchConfig(render_config=batch_render_config)

        # Create app with both batch_config and config parameter
        # batch_config should take precedence
        individual_config = RenderConfiguration(image_size=500)
        app = TimelineApp(
            sample_timeline_json,
            output_dir=str(tmp_path / "output"),
            config=individual_config,  # This should be ignored
            batch_config=batch_config,  # This should be used
            validate=False,
        )

        # App should use batch config's render config
        assert app.config is batch_render_config
        assert app.config.image_size == 800

    def test_batch_processing_workflow(self, tmp_path, sample_timeline_json):
        """Test realistic batch processing workflow."""
        # Create shared resources once
        batch_config = BatchConfig(
            render_config=RenderConfiguration(image_size=600),
            cache_dir=str(tmp_path / "cache"),
        )

        # Process multiple timelines with shared resources
        apps = [
            TimelineApp(
                sample_timeline_json,
                output_dir=str(tmp_path / f"output_{i}"),
                batch_config=batch_config,
                validate=False,
            )
            for i in range(2)
        ]

        # All apps should share the same geocoder and tile cache
        for i in range(1, len(apps)):
            assert apps[0].renderer.geocoder is apps[i].renderer.geocoder
            assert apps[0].renderer.tile_cache is apps[i].renderer.tile_cache
