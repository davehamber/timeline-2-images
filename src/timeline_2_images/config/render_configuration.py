"""Render configuration settings."""

from dataclasses import dataclass

MIN_IMAGE_SIZE = 200
MAX_IMAGE_SIZE = 4000


@dataclass
class RenderConfiguration:
    """Configuration for map rendering."""

    image_width: int = 500
    image_height: int = 500
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
        """Get figure size in inches (width, height)."""
        inches_per_pixel = 1 / self.dpi
        width_inches = self.image_width * inches_per_pixel
        height_inches = self.image_height * inches_per_pixel
        return (width_inches, height_inches)

    def get_bounds_padding(self) -> float:
        """Get padding to add to bounds in degrees."""
        return 0.01

    def get_output_filename(self, date_str: str) -> str:
        """Get output filename for a date."""
        return f"{date_str}.{self.output_format}"

    def _validate_image_dimensions(self) -> None:
        """Validate image width and height are within bounds."""
        if self.image_width < MIN_IMAGE_SIZE:
            raise ValueError(f"image_width must be at least {MIN_IMAGE_SIZE} pixels")
        if self.image_width > MAX_IMAGE_SIZE:
            raise ValueError(f"image_width must not exceed {MAX_IMAGE_SIZE} pixels")
        if self.image_height < MIN_IMAGE_SIZE:
            raise ValueError(f"image_height must be at least {MIN_IMAGE_SIZE} pixels")
        if self.image_height > MAX_IMAGE_SIZE:
            raise ValueError(f"image_height must not exceed {MAX_IMAGE_SIZE} pixels")

    def _validate_numeric_parameters(self) -> None:
        """Validate numeric parameters are in valid ranges."""
        if self.dpi <= 0:
            raise ValueError("dpi must be positive")
        if self.min_area_sq_km < 0:
            raise ValueError("min_area_sq_km must be non-negative")
        if not 0 <= self.line_alpha <= 1:
            raise ValueError("line_alpha must be between 0 and 1")

    def validate(self) -> bool:
        """Validate configuration."""
        self._validate_image_dimensions()
        self._validate_numeric_parameters()
        return True
