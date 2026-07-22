"""Render configuration settings."""

from dataclasses import dataclass

MIN_IMAGE_SIZE = 200
MAX_IMAGE_SIZE = 4000


@dataclass
class RenderConfiguration:
    """Configuration for map rendering."""

    image_size: int = 500
    output_format: str = "jpg"
    dpi: int = 100
    min_area_sq_km: float = 5.0
    line_width: int = 2
    line_border_width: int = 4
    line_alpha: float = 0.9
    start_marker_size: int = 35
    end_marker_size: int = 25
    add_place_names: bool = True

    def get_figure_size(self) -> tuple[float, float]:
        """Get figure size in inches."""
        inches_per_pixel = 1 / self.dpi
        size_inches = self.image_size * inches_per_pixel
        return (size_inches, size_inches)

    def get_bounds_padding(self) -> float:
        """Get padding to add to bounds in degrees."""
        return 0.01

    def get_output_filename(self, date_str: str) -> str:
        """Get output filename for a date."""
        return f"{date_str}.{self.output_format}"

    def validate(self) -> bool:
        """Validate configuration."""
        if self.image_size < MIN_IMAGE_SIZE:
            raise ValueError(f"image_size must be at least {MIN_IMAGE_SIZE} pixels")
        if self.image_size > MAX_IMAGE_SIZE:
            raise ValueError(f"image_size must not exceed {MAX_IMAGE_SIZE} pixels")
        if self.dpi <= 0:
            raise ValueError("dpi must be positive")
        if self.min_area_sq_km < 0:
            raise ValueError("min_area_sq_km must be non-negative")
        if not 0 <= self.line_alpha <= 1:
            raise ValueError("line_alpha must be between 0 and 1")
        return True
