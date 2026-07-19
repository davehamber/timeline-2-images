"""Unit tests for CacheConfig."""

import pytest

from timeline_2_images.config import CacheConfig


class TestCacheConfig:
    """Tests for cache configuration."""

    def test_default_cache_config(self):
        """Test CacheConfig with default settings."""
        config = CacheConfig()

        assert config.enable_caching is True
        assert config.max_cache_size_mb == 512
        assert config.clear_on_exit is True

    def test_custom_cache_config(self):
        """Test CacheConfig with custom settings."""
        config = CacheConfig(
            enable_caching=False,
            max_cache_size_mb=256,
            clear_on_exit=False,
        )

        assert config.enable_caching is False
        assert config.max_cache_size_mb == 256
        assert config.clear_on_exit is False

    def test_get_cache_size_bytes(self):
        """Test getting cache size in bytes."""
        config = CacheConfig(max_cache_size_mb=512)
        assert config.get_cache_size_bytes() == 512 * 1024 * 1024

    def test_get_cache_size_bytes_small(self):
        """Test getting cache size in bytes for small cache."""
        config = CacheConfig(max_cache_size_mb=1)
        assert config.get_cache_size_bytes() == 1024 * 1024

    def test_validate_valid_config(self):
        """Test validating a valid cache configuration."""
        config = CacheConfig(max_cache_size_mb=256)
        assert config.validate() is True

    def test_validate_invalid_cache_size_zero(self):
        """Test validation fails with zero cache size."""
        config = CacheConfig(max_cache_size_mb=0)
        with pytest.raises(ValueError, match="must be at least 1 MB"):
            config.validate()

    def test_validate_invalid_cache_size_negative(self):
        """Test validation fails with negative cache size."""
        config = CacheConfig(max_cache_size_mb=-1)
        with pytest.raises(ValueError, match="must be at least 1 MB"):
            config.validate()

    def test_validate_invalid_cache_size_too_large(self):
        """Test validation fails with cache size exceeding maximum."""
        config = CacheConfig(max_cache_size_mb=9000)
        with pytest.raises(ValueError, match="must not exceed 8192 MB"):
            config.validate()

    def test_cache_config_string_representation_enabled(self):
        """Test string representation of enabled cache config."""
        config = CacheConfig(enable_caching=True, max_cache_size_mb=256)
        result = str(config)
        assert "enabled=enabled" in result
        assert "256MB" in result

    def test_cache_config_string_representation_disabled(self):
        """Test string representation of disabled cache config."""
        config = CacheConfig(enable_caching=False, max_cache_size_mb=512)
        result = str(config)
        assert "enabled=disabled" in result
        assert "512MB" in result
