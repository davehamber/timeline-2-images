"""RenderResult model for render operation results."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RenderResult:
    """Represents the result of a rendering operation."""

    date: str
    output_path: Path
    segment_count: int
    point_count: int
    render_time: float
    success: bool = True
    error_message: str | None = None

    def was_successful(self) -> bool:
        """Check if rendering was successful."""
        return self.success and self.output_path.exists()

    def get_summary(self) -> str:
        """Get human-readable summary of render result."""
        if not self.was_successful():
            return f"{self.date}: FAILED - {self.error_message}"
        return (
            f"{self.date}: {self.segment_count} segments, "
            f"{self.point_count} points in {self.render_time:.2f}s"
        )
