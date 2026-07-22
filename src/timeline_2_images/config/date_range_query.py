"""Date range query logic."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DateRangeQuery:
    """Encapsulates date range query parameters and logic."""

    start_date: str | None = None
    end_date: str | None = None
    days: int = 14

    def get_dates(self, available_dates: list[str]) -> list[str]:
        """
        Get dates matching query parameters from available dates.

        Precedence:
        1. Both start_date and end_date → use exact range (ignore days)
        2. start_date + days → dates from start_date + N days
        3. end_date + days → dates N days before end_date (inclusive)
        4. days only → last N days with data (default)
        """
        if not available_dates:
            return []

        sorted_dates = sorted(available_dates)

        if self.start_date and self.end_date:
            return self._filter_between_dates(sorted_dates, self.start_date, self.end_date)

        if self.start_date:
            return self._filter_from_start_date(sorted_dates, self.start_date, self.days)

        if self.end_date:
            return self._filter_before_end_date(sorted_dates, self.end_date, self.days)

        return sorted_dates[-self.days :]

    def _filter_between_dates(self, available_dates: list[str], start: str, end: str) -> list[str]:
        """Filter dates between start and end (inclusive)."""
        start_dt = self._parse_date(start, "start_date")
        end_dt = self._parse_date(end, "end_date")
        return [
            d for d in available_dates if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    def _filter_from_start_date(
        self, available_dates: list[str], start: str, num_days: int
    ) -> list[str]:
        """Filter dates from start_date for num_days."""
        start_dt = self._parse_date(start, "start_date")
        end_dt = start_dt + timedelta(days=num_days - 1)
        return [
            d for d in available_dates if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    def _filter_before_end_date(
        self, available_dates: list[str], end: str, num_days: int
    ) -> list[str]:
        """Filter dates N days before end_date (inclusive)."""
        end_dt = self._parse_date(end, "end_date")
        start_dt = end_dt - timedelta(days=num_days - 1)
        return [
            d for d in available_dates if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    def _parse_date(self, date_str: str, field_name: str) -> datetime:
        """Parse and validate a date string."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as exc:
            if "unconverted data remains" in str(exc):
                raise ValueError(
                    f"{field_name}: '{date_str}' is not a valid date. "
                    "Ensure the date is in YYYY-MM-DD format with valid day/month values."
                ) from exc
            raise ValueError(f"{field_name}: '{date_str}' is not a valid date. {str(exc)}") from exc

    def _validate_date_order(self, start_dt: datetime | None, end_dt: datetime | None) -> None:
        """Validate that start_date is before end_date."""
        if start_dt and end_dt and start_dt > end_dt:
            raise ValueError("start_date must be before end_date")

    def _validate_days_parameter(self) -> None:
        """Validate days parameter is positive when used."""
        if not (self.start_date and self.end_date) and self.days <= 0:
            raise ValueError("days must be positive")

    def validate(self) -> bool:
        """Validate date parameters."""
        start_dt = self._parse_date(self.start_date, "start_date") if self.start_date else None
        end_dt = self._parse_date(self.end_date, "end_date") if self.end_date else None

        self._validate_date_order(start_dt, end_dt)
        self._validate_days_parameter()

        return True
