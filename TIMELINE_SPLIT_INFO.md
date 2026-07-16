# Timeline Split Information

Your Timeline.json has been split into 11 yearly files for easier processing.

## Yearly Files (in `timelines/` directory)

| Year | Segments | File Size | Coverage |
|------|----------|-----------|----------|
| 2016 | 3,640    | 26.3 MB   | Full year |
| 2017 | 6,285    | 27.7 MB   | Full year |
| 2018 | 5,524    | 27.4 MB   | Full year |
| 2019 | 5,634    | 27.4 MB   | Full year |
| 2020 | 3,884    | 26.3 MB   | Full year |
| 2021 | 2,889    | 25.9 MB   | Full year |
| 2022 | 2,772    | 25.6 MB   | Full year |
| 2023 | 3,315    | 26.2 MB   | Full year |
| 2024 | 3,035    | 26.3 MB   | Full year |
| 2025 | 5,339    | 30.8 MB   | Full year |
| 2026 | 2,769    | 28.7 MB   | Partial (Jul) |
| **Total** | **45,086** | **299 MB** | 2016–2026 |

## Usage Examples

### Generate maps for a specific year
```bash
# 2025 daily maps (all days with data)
uv run python -m daily_timeline_images.main timelines/timeline_2025.json --days 365

# 2024 daily maps  
uv run python -m daily_timeline_images.main timelines/timeline_2024.json --days 365
```

### Analyze specific years
```bash
# Process last 30 days of 2025 data
uv run python -m daily_timeline_images.main timelines/timeline_2025.json --days 30

# Generate high-res images for 2023
uv run python -m daily_timeline_images.main timelines/timeline_2023.json --days 365 --image-size 2000
```

### Merge back to original format
```bash
uv run python -m daily_timeline_images.split_timeline merge timelines --output Timeline_restored.json
```

## Benefits of Splitting

✓ Smaller, manageable files (~26-31 MB each)  
✓ Faster parsing and processing  
✓ Easy year-by-year analysis  
✓ Reduced memory usage  
✓ Can selectively process specific years
