# taskmaster — Dataset Codebook
Generated: 2026-09-01

## Columns

### `series`
- **Type**: `int32`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Taskmaster UK series number (1-21).

### `contestant`
- **Type**: `object`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Contestant full name (corrected from first-name-only source against the official per-series cast).

### `total_points`
- **Type**: `int32`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Raw total points the contestant earned across all tasks in their series, as adjudicated on-air. NOT comparable across series (see series_total_points).

### `series_total_points`
- **Type**: `int32`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Sum of all points awarded to all five contestants in that series. Differs across series because episode/task counts differ (S1=6 episodes, S2-3=5, S4-5=8, S6-21=10).

### `series_size`
- **Type**: `int64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Number of contestants in the series (5 for the UK main run).

### `series_mean_points`
- **Type**: `float64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Mean raw points per contestant in that series (series_total_points / series_size).

### `pct_of_series_points`
- **Type**: `float64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Contestant's share of their series' total points (total_points / series_total_points). The primary apples-to-apples metric; sums to 1.0 within each series.

### `share_vs_equal`
- **Type**: `float64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: pct_of_series_points relative to an even split (x series_size). 1.0 = exactly the average contestant that series; >1 = above the even-split share; <1 = below. Cleanest single cross-series comparison.

### `points_vs_series_mean`
- **Type**: `float64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: total_points / series_mean_points. Same ranking as share_vs_equal, expressed in raw-point space.

### `series_rank`
- **Type**: `int64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Within-series rank by points, 1 = best (ties take the minimum rank).

### `is_winner`
- **Type**: `bool`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: True if the contestant finished first in points that series (series_rank == 1).

### `pct_gap_to_winner`
- **Type**: `float64`
- **Non-null**: 105 / 105 (100.0%)
- **Description**: Series winner's share minus this contestant's share, in share points (0 for the winner). How far off the series-topping pace, normalized.

## Notes

Source: Hand-collected total points per contestant per Taskmaster UK series (S1-S21),
reconciled to official full names via the per-series cast list. See SOURCES.md.

KEY CAVEAT: Raw total_points are NOT comparable across series because series differ in
episode count (S1=6, S2-3=5, S4-5=8, S6-21=10) and therefore in points available. Use
pct_of_series_points or share_vs_equal for any cross-series comparison. Points are a
subjective, comedic score awarded on-air, not an objective performance measure.

Scope: UK main series only. Excludes Champion of Champions and New Year Treat specials
and Junior Taskmaster.

License: Scores are facts and not copyrightable; compiled dataset released by the author.
