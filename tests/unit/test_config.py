"""Tests for configuration classes."""

import pytest

from timeline_2_images.config import RenderConfiguration, DateRangeQuery


class TestRenderConfiguration:
    """Test RenderConfiguration."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = RenderConfiguration()
        assert config.image_width == 500
        assert config.image_height == 500
        assert config.output_format == "jpg"
        assert config.dpi == 100
        assert config.min_area_sq_km == 5.0

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = RenderConfiguration(
            image_width=800,
            image_height=800,
            dpi=200,
            min_area_sq_km=10.0,
        )
        assert config.image_width == 800
        assert config.image_height == 800
        assert config.dpi == 200

    def test_get_figure_size(self):
        """Test getting figure size."""
        config = RenderConfiguration(image_width=500, image_height=500, dpi=100)
        width, height = config.get_figure_size()
        assert width == 5.0
        assert height == 5.0

    def test_get_output_filename(self):
        """Test getting output filename."""
        config = RenderConfiguration()
        filename = config.get_output_filename("2024-01-15")
        assert filename == "2024-01-15.jpg"

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = RenderConfiguration()
        assert config.validate() is True

    def test_validate_invalid_image_size(self):
        """Test validation with invalid image size."""
        config = RenderConfiguration(image_width=-1, image_height=500)
        with pytest.raises(ValueError, match="image_width must be at least"):
            config.validate()

    def test_validate_invalid_dpi(self):
        """Test validation with invalid dpi."""
        config = RenderConfiguration(dpi=0)
        with pytest.raises(ValueError, match="dpi must be positive"):
            config.validate()

    def test_validate_invalid_alpha(self):
        """Test validation with invalid alpha."""
        config = RenderConfiguration(line_alpha=1.5)
        with pytest.raises(ValueError, match="line_alpha must be between 0 and 1"):
            config.validate()


class TestDateRangeQuery:
    """Test DateRangeQuery."""

    def test_default_query(self):
        """Test default query (last 14 days)."""
        query = DateRangeQuery()
        available_dates = [f"2024-01-{i:02d}" for i in range(1, 31)]
        result = query.get_dates(available_dates)
        assert len(result) == 14
        assert result[0] == "2024-01-17"
        assert result[-1] == "2024-01-30"

    def test_query_with_days_only(self):
        """Test query with days parameter only."""
        query = DateRangeQuery(days=7)
        available_dates = [f"2024-01-{i:02d}" for i in range(1, 31)]
        result = query.get_dates(available_dates)
        assert len(result) == 7
        assert result[-1] == "2024-01-30"

    def test_query_with_start_and_end_dates(self):
        """Test query with both start and end dates."""
        query = DateRangeQuery(start_date="2024-01-10", end_date="2024-01-15")
        available_dates = [f"2024-01-{i:02d}" for i in range(1, 31)]
        result = query.get_dates(available_dates)
        assert len(result) == 6
        assert result[0] == "2024-01-10"
        assert result[-1] == "2024-01-15"

    def test_query_with_start_date_and_days(self):
        """Test query with start date and days."""
        query = DateRangeQuery(start_date="2024-01-10", days=5)
        available_dates = [f"2024-01-{i:02d}" for i in range(1, 31)]
        result = query.get_dates(available_dates)
        assert len(result) == 5
        assert result[0] == "2024-01-10"
        assert result[-1] == "2024-01-14"

    def test_query_with_end_date_and_days(self):
        """Test query with end date and days."""
        query = DateRangeQuery(end_date="2024-01-20", days=5)
        available_dates = [f"2024-01-{i:02d}" for i in range(1, 31)]
        result = query.get_dates(available_dates)
        assert len(result) == 5
        assert result[0] == "2024-01-16"
        assert result[-1] == "2024-01-20"

    def test_query_empty_available_dates(self):
        """Test query with no available dates."""
        query = DateRangeQuery()
        result = query.get_dates([])
        assert result == []

    def test_validate_valid_query(self):
        """Test validation of valid query."""
        query = DateRangeQuery(start_date="2024-01-10", end_date="2024-01-20")
        assert query.validate() is True

    def test_validate_invalid_days(self):
        """Test validation with invalid days."""
        query = DateRangeQuery(days=0)
        with pytest.raises(ValueError, match="days must be positive"):
            query.validate()

    def test_validate_invalid_date_format(self):
        """Test validation with invalid date format."""
        query = DateRangeQuery(start_date="01-01-2024")
        with pytest.raises(ValueError, match="is not a valid date"):
            query.validate()

    def test_validate_start_after_end(self):
        """Test validation when start is after end."""
        query = DateRangeQuery(start_date="2024-01-20", end_date="2024-01-10")
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            query.validate()
