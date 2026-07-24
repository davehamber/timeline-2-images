# iOS Timeline export: three issues found

Ran into a few things getting an iOS-sourced Timeline export working. None of these are hard to fix — flagging in case they're useful, and happy to open as GitHub issues instead if you'd rather track them there.

## 1. Filename

iOS's on-device export (Settings > Location & Privacy > Export Timeline Data) saves as `location-history.json`, not `Timeline.json`. Worth a line in the README next to the existing Android instructions.

## 2. Root is a bare array, not an object

iOS export root:

```json
[
  { "startTime": ..., "endTime": ..., "visit": {...} },
  { "startTime": ..., "endTime": ..., "activity": {...} }
]
```

`TimelineValidator` expects `{"semanticSegments": [...]}` / `{"timelineObjects": [...]}` / `{"locations": [...]}` and rejects the bare list. The array elements match the `semanticSegments` element schema exactly, so this is just a missing wrapper — could auto-detect a list root and wrap it as `semanticSegments` rather than erroring.

**Workaround:** `jq '{semanticSegments: .}' location-history.json > Timeline.json`

## 3. `geo:` URI prefix breaks waypoint parsing — silent, universal failure

This one's the real bug. After fixing #2, every single date returned "No segments found for date" — including dates independently confirmed via [source] to have populated `activity`/`timelinePath` segments. Uniform across a 4-year span, so not a date/timezone issue.

**Root cause**, `segment_parser.py::parse_waypoints`:

```python
point = segment.get("point")
if isinstance(point, str) and "," in point:
    lat_s, lng_s = point.split(",")
    try:
        lat, lng = float(lat_s), float(lng_s)
    except ValueError:
        continue
```

iOS `timelinePath` points are `geo:`-prefixed: `"geo:52.499323,13.403603"`.

`point.split(",")` gives `lat_s = "geo:52.499323"`, `float()` raises, caught by the bare `except ValueError: continue`. Every point in every path fails silently, `parse_waypoints` always returns `[]`, and `build_segments_with_waypoints`'s `if waypoints:` gate drops the segment. Meanwhile [the date-index code] (used for the date index) doesn't touch `timelinePath` at all, so it correctly reports valid dates — the two code paths silently diverge on this file format, with no error surfaced.

The same `geo:` prefix also shows up in `visit.topCandidate.placeLocation` and `activity.start`/`.end` — worth checking those consumers too.

**Fix:** strip the prefix before parsing:

```python
if point.startswith("geo:"):
    point = point[len("geo:"):]
```

**Workaround applied:**
`jq '(.semanticSegments[].timelinePath[]?.point) |= sub("^geo:"; "")' Timeline.json > Timeline_fixed.json`

## Suggested test coverage

A fixture built from a real iOS export (bare-array root + `geo:`-prefixed points) would catch both #2 and #3 as regressions — currently only Android (Samsung) is mentioned as verified in the README, and iOS support is silently broken end-to-end (zero exceptions, no error) rather than failing loudly.