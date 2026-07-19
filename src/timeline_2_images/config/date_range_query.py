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

        available_dates_sorted = sorted(available_dates)

        if self.start_date and self.end_date:
            return self._filter_between_dates(
                available_dates_sorted, self.start_date, self.end_date
            )
        if self.start_date:
            return self._filter_from_start_date(available_dates_sorted, self.start_date, self.days)
        if self.end_date:
            return self._filter_before_end_date(available_dates_sorted, self.end_date, self.days)

        return available_dates_sorted[-self.days :]

    def _filter_between_dates(self, available_dates: list[str], start: str, end: str) -> list[str]:
        """Filter dates between start and end (inclusive)."""
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        return [
            d for d in available_dates if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    def _filter_from_start_date(
        self, available_dates: list[str], start: str, num_days: int
    ) -> list[str]:
        """Filter dates from start_date for num_days."""
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=num_days - 1)
        return [
            d for d in available_dates if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    def _filter_before_end_date(
        self, available_dates: list[str], end: str, num_days: int
    ) -> list[str]:
        """Filter dates N days before end_date (inclusive)."""
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=num_days - 1)
        return [
            d for d in available_dates if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ]

    def _parse_date(self, date_str: str, field_name: str) -> datetime:
        """Parse and validate a date string."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{field_name} must be in YYYY-MM-DD format") from exc

    def validate(self) -> bool:
        """Validate date parameters."""
        start_dt = self._parse_date(self.start_date, "start_date") if self.start_date else None
        end_dt = self._parse_date(self.end_date, "end_date") if self.end_date else None

        if start_dt and end_dt and start_dt > end_dt:
            raise ValueError("start_date must be before end_date")

        # days only needs to be positive if it will be used
        # (i.e., when not using both start_date and end_date)
        if not (self.start_date and self.end_date) and self.days <= 0:
            raise ValueError("days must be positive")

        return True
