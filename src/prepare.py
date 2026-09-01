"""Sellable dataset preparation and export utilities.

Takes a processed DataFrame and packages it for sale/distribution:
  - Drops any PII columns listed in config.yaml
  - Exports to CSV, Excel, and/or Parquet
  - Generates a plain-text codebook (column descriptions)

Usage in a notebook:
    from src.prepare import package_dataset
    package_dataset(df, cfg, name="my_dataset", codebook={"col": "description"})
"""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Taskmaster feature engineering
# ---------------------------------------------------------------------------

def add_series_metrics(
    df: pd.DataFrame,
    series_col: str = "series",
    contestant_col: str = "contestant",
    points_col: str = "total_points",
) -> pd.DataFrame:
    """Add apples-to-apples comparison metrics to contestant points.

    Raw Taskmaster point totals are NOT comparable across series because series
    differ in episode count (and therefore in the number of points available).
    A winner of a 5-episode series simply had fewer points on offer than a
    mid-table finisher in a 10-episode series. Every metric here is designed to
    normalize that away so contestants can be compared on a common scale.

    Columns added:
      series_total_points   Sum of all points awarded in that series (denominator).
      series_size           Number of contestants in the series (5 for UK main run).
      series_mean_points    Mean points per contestant in that series.
      pct_of_series_points  points / series_total_points. The primary normalized
                            metric: a contestant's SHARE of their series' points.
      share_vs_equal        pct_of_series_points / (1 / series_size). The share
                            relative to an even split. 1.0 = exactly the average
                            contestant; >1 = above the even-split share; <1 = below.
                            This is the cleanest single cross-series comparison.
      points_vs_series_mean total_points / series_mean_points (same idea, raw-point
                            space; identical ranking to share_vs_equal).
      series_rank           Within-series rank by points, 1 = best (ties = min rank).
      is_winner             True if series_rank == 1.
      pct_gap_to_winner     Winner's share minus this contestant's share, in
                            percentage points. 0 for the winner.

    Args:
        df:             Clean long-format DataFrame (one row per contestant-series).
        series_col:     Series id column name.
        contestant_col: Contestant name column name.
        points_col:     Raw total-points column name.

    Returns:
        A new DataFrame with the metric columns appended, sorted by
        (series, series_rank).
    """
    out = df.copy()

    grp = out.groupby(series_col)[points_col]
    out["series_total_points"] = grp.transform("sum")
    out["series_size"] = grp.transform("size")
    out["series_mean_points"] = grp.transform("mean")

    out["pct_of_series_points"] = out[points_col] / out["series_total_points"]
    out["share_vs_equal"] = out["pct_of_series_points"] * out["series_size"]
    out["points_vs_series_mean"] = out[points_col] / out["series_mean_points"]

    # Rank 1 = highest points within the series (ties share the best rank).
    out["series_rank"] = (
        grp.rank(method="min", ascending=False).astype(int)
    )
    out["is_winner"] = out["series_rank"] == 1

    winner_share = (
        out.loc[out["series_rank"] == 1]
        .groupby(series_col)["pct_of_series_points"]
        .max()
    )
    out["pct_gap_to_winner"] = (
        out[series_col].map(winner_share) - out["pct_of_series_points"]
    )

    # Round the derived floats for a clean export (keep enough precision to sum).
    for col in ("series_mean_points",):
        out[col] = out[col].round(2)
    for col in ("pct_of_series_points", "share_vs_equal",
                "points_vs_series_mean", "pct_gap_to_winner"):
        out[col] = out[col].round(4)

    return out.sort_values([series_col, "series_rank"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# PII stripping
# ---------------------------------------------------------------------------

def strip_pii(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Drop columns listed under export.strip_pii_columns in config.yaml."""
    cols_to_drop = cfg.get("export", {}).get("strip_pii_columns", [])
    if cols_to_drop:
        existing = [c for c in cols_to_drop if c in df.columns]
        if existing:
            df = df.drop(columns=existing)
            print(f"Stripped PII columns: {existing}")
    return df


# ---------------------------------------------------------------------------
# Codebook
# ---------------------------------------------------------------------------

def build_codebook(
    df: pd.DataFrame,
    descriptions: dict[str, str] | None = None,
    project_name: str = "",
    notes: str = "",
) -> str:
    """Generate a plain-text codebook for the dataset.

    Args:
        df:           The export-ready DataFrame.
        descriptions: Dict mapping column name → human-readable description.
                      Columns not in the dict get a placeholder.
        project_name: Printed in the header.
        notes:        Free-text notes appended at the bottom (source info, license, etc.).

    Returns:
        Codebook as a string (written to a .md file by package_dataset).
    """
    descriptions = descriptions or {}
    today = date.today().isoformat()

    lines = [
        f"# {project_name} — Dataset Codebook",
        f"Generated: {today}",
        "",
        "## Columns",
        "",
    ]

    for col in df.columns:
        dtype = str(df[col].dtype)
        desc = descriptions.get(col, "_No description provided._")
        non_null = df[col].notna().sum()
        total = len(df)
        lines.append(f"### `{col}`")
        lines.append(f"- **Type**: `{dtype}`")
        lines.append(f"- **Non-null**: {non_null:,} / {total:,} ({non_null/total:.1%})")
        lines.append(f"- **Description**: {desc}")
        lines.append("")

    if notes:
        lines += ["## Notes", "", textwrap.dedent(notes).strip(), ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def package_dataset(
    df: pd.DataFrame,
    cfg: dict[str, Any],
    name: str,
    codebook: dict[str, str] | None = None,
    notes: str = "",
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """Strip PII, export to configured formats, and write a codebook.

    Args:
        df:       Processed DataFrame ready for packaging.
        cfg:      Loaded config dict.
        name:     Base filename (no extension).
        codebook: Column description dict passed to build_codebook().
        notes:    Free-text appended to the codebook (source, license, etc.).
        formats:  Override config export.formats. Supported: csv, xlsx, parquet.

    Returns:
        Dict of {format: Path} for every file written.
    """
    df = strip_pii(df, cfg)

    export_dir = Path(cfg["paths"]["export"])
    export_dir.mkdir(parents=True, exist_ok=True)

    export_cfg = cfg.get("export", {})
    active_formats = formats or export_cfg.get("formats", ["csv"])
    include_codebook = export_cfg.get("include_codebook", True)
    project_name = cfg.get("project_name", name)

    written: dict[str, Path] = {}

    if "csv" in active_formats:
        p = export_dir / f"{name}.csv"
        df.to_csv(p, index=False, encoding=cfg["settings"]["encoding"])
        written["csv"] = p
        print(f"Exported CSV     → {p}")

    if "xlsx" in active_formats:
        p = export_dir / f"{name}.xlsx"
        with pd.ExcelWriter(p, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="data")
        written["xlsx"] = p
        print(f"Exported Excel   → {p}")

    if "parquet" in active_formats:
        p = export_dir / f"{name}.parquet"
        df.to_parquet(p, index=False, engine=cfg["settings"]["parquet_engine"])
        written["parquet"] = p
        print(f"Exported Parquet → {p}")

    if include_codebook:
        cb_text = build_codebook(df, descriptions=codebook, project_name=project_name, notes=notes)
        cb_path = export_dir / f"{name}_codebook.md"
        cb_path.write_text(cb_text, encoding="utf-8")
        written["codebook"] = cb_path
        print(f"Wrote codebook   → {cb_path}")

    print(f"\n✓  Package complete: {len(df):,} rows × {len(df.columns)} columns")
    return written


# ---------------------------------------------------------------------------
# Quick summary helpers (useful before packaging)
# ---------------------------------------------------------------------------

def value_counts_all(df: pd.DataFrame, top_n: int = 10) -> None:
    """Print top-N value counts for every column — quick sanity check."""
    for col in df.columns:
        print(f"\n── {col} ──")
        print(df[col].value_counts(dropna=False).head(top_n).to_string())


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return describe() output for numeric columns only, transposed for readability."""
    return df.select_dtypes("number").describe().T.round(2)
