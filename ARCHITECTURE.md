# Architecture & Function Flow

## Overview

This document shows the function relationships and data flow through the timeline-2-images application.

## Main Data Processing Flow

```mermaid
graph TD
    A["main.py: main()"] --> B["get_last_n_days_with_data()"]
    B --> C["Extracts dates from Timeline.json"]
    A --> D["_process_date()"]
    D --> E["load_segments_for_day()"]
    E --> F["_parse_waypoints()"]
    D --> G["render_segments()"]
    G --> H["Collects & simplifies waypoints"]
    G --> I["Calculates bounds"]
    G --> J["Draws journey line & markers"]
    G --> K["Saves JPG output"]
```

## Detailed Module Functions

### timeline_parser.py - Date & Segment Extraction

```mermaid
graph TD
    A["get_last_n_days_with_data()"]
    A --> B["_extract_dates_from_locations()"]
    A --> C["_extract_dates_from_timeline_objects()"]
    A --> D["_extract_dates_from_segments()"]

    C --> C1["_get_segment_start_date()"]
    D --> D1["_get_semantic_segment_datetime()"]

    style A fill:#e1f5ff,color:#000000,color:#000000
    style B fill:#f3e5f5,color:#000000,color:#000000
    style C fill:#f3e5f5,color:#000000,color:#000000
    style D fill:#f3e5f5,color:#000000,color:#000000
```

### timeline_parser.py - Point Extraction

```mermaid
graph TD
    A["load_points_for_day()"]
    A --> B["_extract_from_flat_locations()"]
    A --> C["_extract_from_timeline_objects()"]
    A --> D["_extract_from_semantic_segments()"]

    B --> B1["_process_flat_location()"]
    B1 --> B2["_parse_timestamp()"]
    B1 --> B3["_extract_location_point()"]

    C --> C1["_process_timeline_object()"]
    C1 --> C2["_get_timeline_object_datetime()"]
    C1 --> C3["_matches_target_date()"]
    C1 --> C4["_extract_waypoints_from_segment()"]
    C1 --> C5["_extract_locations_from_segment()"]

    D --> D1["_process_semantic_segment()"]
    D1 --> D2["_get_semantic_segment_datetime()"]
    D1 --> D3["_matches_target_date()"]
    D1 --> D4["_extract_points_from_segment_path()"]
    D4 --> D5["_parse_point_string()"]

    style A fill:#e1f5ff,color:#000000
    style B fill:#f3e5f5,color:#000000
    style C fill:#f3e5f5,color:#000000
    style D fill:#f3e5f5,color:#000000
```

### timeline_parser.py - Segment Loading

```mermaid
graph TD
    A["load_segments_for_day()"]
    A --> B["_parse_segment_datetime()"]
    A --> C["_parse_waypoints()"]

    style A fill:#e1f5ff,color:#000000
    style B fill:#c8e6c9,color:#000000
    style C fill:#c8e6c9,color:#000000
```

### map_renderer.py - Map Rendering Pipeline

```mermaid
graph TD
    A["render_segments()"]
    A --> B["_collect_and_simplify_waypoints()"]
    B --> B1["simplify_waypoints()"]

    A --> C["_calculate_bounds()"]
    A --> D["_calculate_padded_bounds()"]
    A --> E["_enforce_minimum_area()"]

    A --> F["_draw_journey_line()"]
    A --> G["_draw_markers()"]

    A --> H["savefig() - Output JPG"]

    style A fill:#e1f5ff,color:#000000
    style B1 fill:#fff9c4,color:#000000
    style F fill:#f8bbd0,color:#000000
    style G fill:#f8bbd0,color:#000000
    style H fill:#90caf9,color:#000000
```

### split_timeline.py - CLI & Timeline Splitting

```mermaid
graph TD
    A["main()"]
    A --> B["_handle_split()"]
    A --> C["_handle_merge()"]

    B --> B1["split_timeline_by_year()"]
    C --> C1["merge_timelines()"]

    style A fill:#e1f5ff,color:#000000
    style B fill:#c8e6c9,color:#000000
    style C fill:#c8e6c9,color:#000000
```

### main.py - CLI & Orchestration

```mermaid
graph TD
    A["main()"]
    A --> B["get_last_n_days_with_data()"]
    A --> C["_process_date()"]

    C --> C1["load_segments_for_day()"]
    C --> C2["render_segments()"]

    style A fill:#e1f5ff,color:#000000
    style B fill:#b3e5fc,color:#000000
    style C fill:#c8e6c9,color:#000000
```

## Data Flow Architecture

```mermaid
graph LR
    A["Timeline.json<br/>Input"] --> B["Date Query<br/>Functions"]
    B --> C["Segment/Point<br/>Extraction"]
    C --> D["Waypoint<br/>Simplification<br/>RDP Algorithm"]
    D --> E["Bounds<br/>Calculation"]
    E --> F["Map<br/>Rendering<br/>Matplotlib + OSM"]
    F --> G["JPG Output<br/>Images"]

    style A fill:#ffebee,color:#000000
    style G fill:#c8e6c9,color:#000000
    style D fill:#fff9c4,color:#000000
    style F fill:#f8bbd0,color:#000000
```

## Function Complexity Hierarchy

**Tier 1 - Entry Points (A complexity)**
- `main()` - CLI orchestrator
- `main()` (split_timeline) - Timeline management CLI

**Tier 2 - Core Business Logic (A complexity)**
- `load_segments_for_day()` - Extract segments with waypoints
- `load_points_for_day()` - Extract individual points
- `get_last_n_days_with_data()` - Find dates with data
- `render_segments()` - Generate map images

**Tier 3 - Schema Handlers (A complexity)**
- `_process_flat_location()` - Handle flat location schema
- `_process_timeline_object()` - Handle timeline objects schema
- `_process_semantic_segment()` - Handle semantic segments schema

**Tier 4 - Utility Functions (A complexity)**
- `simplify_waypoints()` - RDP line simplification
- `_parse_timestamp()` - Timestamp parsing
- `_parse_waypoints()` - Waypoint coordinate parsing
- `_parse_point_string()` - String coordinate parsing
- Bounds calculation helpers

**All 39 functions maintain A complexity (≤ 5 cyclomatic complexity)**

## Key Design Patterns

1. **Data Pipeline**: Functions transform data sequentially without state
2. **Pure Functions**: Most functions have no side effects
3. **Schema Abstraction**: Three schema handlers for different Timeline JSON formats
4. **Single Responsibility**: Each function does one thing well
5. **Composition**: Small functions compose into larger workflows
