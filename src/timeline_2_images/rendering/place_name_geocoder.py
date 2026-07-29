"""Reverse geocoding using OpenStreetMap Nominatim API."""

import json
import logging
import time
from typing import NamedTuple, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)


class Location(NamedTuple):
    """Result from reverse geocoding."""

    address: str
    latitude: float
    longitude: float
    raw: dict


class PlaceNameGeocoder:
    """Reverse geocoding using OpenStreetMap Nominatim API."""

    NOMINATIM_API = "https://nominatim.openstreetmap.org/reverse"
    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 1.0  # Rate limiting: 1 second between requests per Nominatim policy

    def __init__(self, user_agent: str = "timeline-2-images/1.0"):
        """Initialize geocoder.

        Args:
            user_agent: User-Agent header for requests (required by Nominatim)
        """
        self.user_agent = user_agent
        self.last_request_time = 0.0

    def reverse(
        self,
        query: str,
        timeout: int = REQUEST_TIMEOUT,
        language: str = "en",
        addressdetails: bool = True,
    ) -> Optional[Location]:
        """Reverse geocode coordinates to get place name.

        Args:
            query: Coordinates as string "latitude, longitude" or "latitude,longitude"
            timeout: Request timeout in seconds
            language: Preferred language for results (e.g., "en", "de")
            addressdetails: Whether to include detailed address breakdown

        Returns:
            Location object with address, coordinates, and raw data, or None if not found
        """
        lat, lon = self._parse_coordinates(query)
        if lat is None or lon is None:
            return None

        url = self._build_request_url(lat, lon, language, addressdetails)
        return self._request_and_parse(url, lat, lon, timeout)

    def _parse_coordinates(self, query: str) -> tuple[Optional[float], Optional[float]]:
        """Parse coordinate string to lat/lon tuple."""
        try:
            lat_str, lon_str = query.split(",")
            return float(lat_str.strip()), float(lon_str.strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid coordinates: {query}")
            return None, None

    def _build_request_url(
        self, lat: float, lon: float, language: str, addressdetails: bool
    ) -> str:
        """Build Nominatim API request URL."""
        params = {
            "lat": str(lat),
            "lon": str(lon),
            "format": "json",
        }
        if language:
            params["accept-language"] = language
        if addressdetails:
            params["addressdetails"] = "1"
        return f"{self.NOMINATIM_API}?{urlencode(params)}"

    def _request_and_parse(
        self, url: str, lat: float, lon: float, timeout: int
    ) -> Optional[Location]:
        """Make HTTP request and parse response."""
        self._apply_rate_limiting()
        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": self.user_agent})
            return self._handle_request_response(response, lat, lon)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
        ) as e:
            self._handle_request_error(e, lat, lon)
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error parsing Nominatim response: {e}")
            return None

    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting between requests."""
        time.sleep(max(0, self.REQUEST_DELAY - (time.time() - self.last_request_time)))
        self.last_request_time = time.time()

    def _handle_request_response(
        self, response: requests.Response, lat: float, lon: float
    ) -> Optional[Location]:
        """Handle successful HTTP response."""
        if not self._is_response_ok(response):
            return None
        data = response.json()
        return self._extract_location_from_response(data, lat, lon)

    def _handle_request_error(self, error: Exception, lat: float, lon: float) -> None:
        """Log request error."""
        if isinstance(error, requests.exceptions.Timeout):
            logger.warning(f"Timeout connecting to Nominatim for ({lat}, {lon})")
        elif isinstance(error, requests.exceptions.ConnectionError):
            logger.warning(f"Connection error from Nominatim: {error}")
        else:
            logger.warning(f"Error from Nominatim: {error}")

    def _is_response_ok(self, response: requests.Response) -> bool:
        """Check if HTTP response is valid."""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited by Nominatim, retry after {retry_after}s")
            return False
        if response.status_code == 403:
            logger.warning("Access forbidden by Nominatim (invalid user-agent?)")
            return False
        response.raise_for_status()
        return True

    def _extract_location_from_response(
        self, data: dict | list, lat: float, lon: float
    ) -> Optional[Location]:
        """Extract Location from API response data."""
        if self._is_error_response(data):
            return None

        if not data:
            return None

        data = self._normalize_response_data(data)  # type: ignore[assignment]
        if data is None:
            return None

        display_name = data.get("display_name", "")  # type: ignore[union-attr]
        lat_result = float(data.get("lat", lat))  # type: ignore[union-attr]
        lon_result = float(data.get("lon", lon))  # type: ignore[union-attr]

        return Location(address=display_name, latitude=lat_result, longitude=lon_result, raw=data)  # type: ignore[arg-type]

    def _is_error_response(self, data: dict | list) -> bool:
        """Check if response contains an error."""
        if isinstance(data, dict) and "error" in data:
            if data["error"] == "Unable to geocode":
                return True
            logger.warning(f"Nominatim error: {data['error']}")
            return True
        return False

    def _normalize_response_data(self, data: dict | list) -> Optional[dict]:
        """Normalize response data (handle list responses by extracting first element)."""
        if isinstance(data, list):
            return data[0] if data else None
        return data

    def extract_place_name(self, location: Optional[Location]) -> str:
        """Extract a concise place name from a Location object.

        Args:
            location: Location from reverse() method

        Returns:
            Place name string (e.g., "Neeberg", "Berlin") or empty string if not found
        """
        if not location:
            return ""

        place_from_address = self._extract_from_structured_address(location.raw)
        if place_from_address:
            return place_from_address

        return self._extract_from_display_name(location.address) if location.address else ""

    def _extract_from_structured_address(self, raw_data: Optional[dict]) -> str:
        """Extract place name from structured address dictionary."""
        if not raw_data:
            return ""

        address = raw_data.get("address", {})
        if not isinstance(address, dict):
            return ""

        for key in ["village", "town", "city", "borough", "district", "suburb"]:
            if key in address:
                return str(address[key])

        return ""

    @staticmethod
    def _extract_from_display_name(display_name: str) -> str:
        """Extract place name from display_name string.

        Args:
            display_name: Address string like "Neeberg, Pomerania, Germany"

        Returns:
            Extracted place name or original string if parsing fails
        """
        if not display_name:
            return ""

        parts = [p.strip() for p in display_name.split(",")]
        return PlaceNameGeocoder._find_valid_place_name(parts)

    @staticmethod
    def _find_valid_place_name(parts: list[str]) -> str:
        """Find valid place name from comma-separated parts."""
        if not parts:
            return ""

        for part in parts[1:-1]:
            if PlaceNameGeocoder._is_valid_place_name(part):
                return part

        return parts[0] if parts else ""

    @staticmethod
    def _is_valid_place_name(part: str) -> bool:
        """Check if a part string is a valid place name."""
        return bool(part and not part.isdigit() and len(part) > 2)
