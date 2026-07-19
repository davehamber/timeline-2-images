"""Unit tests for BatchConfig."""

import pytest

from timeline_2_images.config import BatchConfig, RenderConfiguration


class TestBatchConfig:
    """Tests for BatchConfig resource pooling configuration."""

    def test_default_batch_config(self):
        """Test BatchConfig with default settings."""
        batch_config = BatchConfig()

        assert batch_config.render_config is not None
        assert batch_config.tile_cache is not None
        assert batch_config.geocoder is not None

    def test_batch_config_with_custom_render_config(self):
        """Test BatchConfig with custom RenderConfiguration."""
        render_config = RenderConfiguration(image_size=800)
        batch_config = BatchConfig(render_config=render_config)

        assert batch_config.render_config is render_config
        assert batch_config.render_config.image_size == 800

    def test_batch_config_with_cache_dir(self):
        """Test BatchConfig with custom cache directory."""
        batch_config = BatchConfig(cache_dir="/tmp/cache")

        assert batch_config.tile_cache is not None

    def test_batch_config_create_renderer(self):
        """Test creating renderer from BatchConfig."""
        batch_config = BatchConfig()
        renderer = batch_config.create_renderer()

        assert renderer is not None

    def test_batch_config_resource_sharing(self):
        """Test that two renderers from same BatchConfig share resources."""
        batch_config = BatchConfig()

        renderer1 = batch_config.create_renderer()
        renderer2 = batch_config.create_renderer()

        # Both renderers should use the same geocoder instance
        assert renderer1.geocoder is renderer2.geocoder
        # Both renderers should use the same tile cache instance
        assert renderer1.tile_cache is renderer2.tile_cache

    def test_batch_config_validate_config(self):
        """Test that BatchConfig validates render configuration."""
        render_config = RenderConfiguration(image_size=-1)
        with pytest.raises(ValueError):
            BatchConfig(render_config=render_config)
