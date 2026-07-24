"""Tests for iOS and Android Timeline format compatibility."""

import json
import pytest

from timeline_2_images.parsers.timeline_cache import TimelineCache
from timeline_2_images.parsers.segment_parser import SegmentParser
from timeline_2_images.parsers.point_extractor import PointExtractor


class TestBareArrayDetection:
    """Test detection and wrapping of bare array root structure (iOS format)."""

    def test_ios_bare_array_detection(self, ios_timeline_json):
        """iOS exports bare array root, should be detected and wrapped."""
        with open(ios_timeline_json) as f:
            data = json.load(f)

        assert isinstance(data, list), "iOS fixture should be a bare array"
        assert len(data) == 5, "iOS fixture should have 5 segments"

    def test_android_object_root(self, android_timeline_json):
        """Android exports object root with semanticSegments key."""
        with open(android_timeline_json) as f:
            data = json.load(f)

        assert isinstance(data, dict), "Android fixture should be an object"
        assert "semanticSegments" in data, "Android should have semanticSegments key"
        assert len(data["semanticSegments"]) >= 2, "Android fixture should have at least 2 segments"


class TestGeoUriPrefixStripping:
    """Test stripping of geo: URI prefixes from iOS coordinates."""

    def test_parse_waypoints_with_geo_prefix(self):
        """parse_waypoints should handle geo: prefixed points."""
        path = [
            {"point": "geo:52.499323,13.403603"},
            {"point": "geo:52.502145,13.410234"},
            {"point": "geo:52.506789,13.418912"},
        ]
        waypoints = SegmentParser.parse_waypoints(path)

        assert len(waypoints) == 3, "Should parse all 3 geo: prefixed waypoints"
        assert waypoints[0] == (52.499323, 13.403603)
        assert waypoints[1] == (52.502145, 13.410234)
        assert waypoints[2] == (52.506789, 13.418912)

    def test_parse_waypoints_without_prefix(self):
        """parse_waypoints should still work with unprefixed coordinates (Android)."""
        path = [
            {"point": "52.499323,13.403603"},
            {"point": "52.502145,13.410234"},
        ]
        waypoints = SegmentParser.parse_waypoints(path)

        assert len(waypoints) == 2
        assert waypoints[0] == (52.499323, 13.403603)
        assert waypoints[1] == (52.502145, 13.410234)

    def test_parse_point_string_with_geo_prefix(self):
        """parse_point_string should handle geo: prefixed points."""
        from datetime import datetime, timezone

        dt = datetime.now(timezone.utc)
        result = PointExtractor.parse_point_string(dt, "geo:52.499323,13.403603")

        assert result is not None
        assert result[1] == 52.499323
        assert result[2] == 13.403603

    def test_parse_point_string_without_prefix(self):
        """parse_point_string should still work with unprefixed coordinates (Android)."""
        from datetime import datetime, timezone

        dt = datetime.now(timezone.utc)
        result = PointExtractor.parse_point_string(dt, "52.499323,13.403603")

        assert result is not None
        assert result[1] == 52.499323
        assert result[2] == 13.403603


class TestSegmentParsing:
    """Test segment parsing with both iOS and Android formats."""

    def test_android_segment_parsing(self, android_timeline_json):
        """Android format should parse segments with waypoints correctly."""
        cache = TimelineCache()
        parser = SegmentParser(cache)

        # Load and parse
        segments = parser.load_for_day(android_timeline_json, "2026-01-15")

        assert len(segments) >= 1, "Should find at least 1 segment for 2026-01-15"

        activity_segment = next(
            (s for s in segments if s.get("activityType") == "IN_VEHICLE"), None
        )
        assert activity_segment is not None, "Should have an IN_VEHICLE segment"
        assert len(activity_segment["waypoints"]) == 5, "First activity should have 5 waypoints"
        assert activity_segment["waypoints"][0] == (52.499323, 13.403603)

    def test_ios_segment_parsing(self, ios_timeline_json):
        """iOS format should parse segments with waypoints correctly after wrapping."""
        cache = TimelineCache()
        parser = SegmentParser(cache)

        # Load and parse - should work after bare array wrapping is implemented
        segments = parser.load_for_day(ios_timeline_json, "2026-01-15")

        assert len(segments) >= 1, "Should find segments for 2026-01-15"

        activity_segment = next(
            (s for s in segments if s.get("activityType") == "IN_VEHICLE"), None
        )
        assert activity_segment is not None, "Should have an IN_VEHICLE segment"
        assert len(activity_segment["waypoints"]) > 0, "Activity should have waypoints"
        # Verify coordinates were parsed correctly despite geo: prefix
        assert activity_segment["waypoints"][0] == (52.499323, 13.403603)


class TestDateExtraction:
    """Test date extraction works with both iOS and Android formats."""

    def test_android_date_extraction(self, android_timeline_json):
        """Android format should correctly extract dates."""
        cache = TimelineCache()
        cache.load_file(android_timeline_json)
        cache.build_date_index()

        assert cache.date_index is not None
        date_list = list(cache.date_index.keys())
        assert any("2026-01-15" in d.isoformat() for d in date_list), "Should find 2026-01-15"

    def test_ios_date_extraction(self, ios_timeline_json):
        """iOS format should correctly extract dates after bare array wrapping."""
        cache = TimelineCache()
        cache.load_file(ios_timeline_json)
        cache.build_date_index()

        assert cache.date_index is not None
        date_list = list(cache.date_index.keys())
        assert any("2026-01-15" in d.isoformat() for d in date_list), "Should find 2026-01-15"


class TestPointExtraction:
    """Test point extraction from both format types."""

    def test_android_points_extraction(self, android_timeline_json):
        """Android format should extract points for a date."""
        cache = TimelineCache()
        extractor = PointExtractor(cache)

        df = extractor.load_points_for_day(android_timeline_json, "2026-01-15")

        assert len(df) > 0, "Should extract points for 2026-01-15"
        assert "lat" in df.columns
        assert "lon" in df.columns
        # First point should match start of journey
        assert df.iloc[0]["lat"] == pytest.approx(52.499323, rel=1e-5)
        assert df.iloc[0]["lon"] == pytest.approx(13.403603, rel=1e-5)

    def test_ios_points_extraction(self, ios_timeline_json):
        """iOS format should extract points for a date."""
        cache = TimelineCache()
        extractor = PointExtractor(cache)

        df = extractor.load_points_for_day(ios_timeline_json, "2026-01-15")

        assert len(df) > 0, "Should extract points for 2026-01-15"
        assert "lat" in df.columns
        assert "lon" in df.columns
        # First point should match start of journey
        assert df.iloc[0]["lat"] == pytest.approx(52.499323, rel=1e-5)
        assert df.iloc[0]["lon"] == pytest.approx(13.403603, rel=1e-5)


class TestFormatEquivalence:
    """Verify iOS and Android formats produce equivalent results."""

    def test_same_day_produces_same_waypoints(self, android_timeline_json, ios_timeline_json):
        """Both formats with same data should produce identical waypoints."""
        android_cache = TimelineCache()
        android_parser = SegmentParser(android_cache)
        android_segments = android_parser.load_for_day(android_timeline_json, "2026-01-15")

        ios_cache = TimelineCache()
        ios_parser = SegmentParser(ios_cache)
        ios_segments = ios_parser.load_for_day(ios_timeline_json, "2026-01-15")

        # Filter to just activity segments
        android_activities = [s for s in android_segments if s.get("activityType") == "IN_VEHICLE"]
        ios_activities = [s for s in ios_segments if s.get("activityType") == "IN_VEHICLE"]

        # Both should have vehicle activities
        assert len(android_activities) > 0, "Android should have vehicle activities"
        assert len(ios_activities) > 0, "iOS should have vehicle activities"

        # First activity in each should have same waypoints
        assert len(android_activities[0]["waypoints"]) == len(ios_activities[0]["waypoints"])
        for android_wp, ios_wp in zip(
            android_activities[0]["waypoints"], ios_activities[0]["waypoints"]
        ):
            assert android_wp == pytest.approx(ios_wp, rel=1e-5)
