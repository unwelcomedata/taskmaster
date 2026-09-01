"""Social media chart export helpers.

Produces publication-ready PNG images sized for common social platforms.
All charts are generated with matplotlib and exported via Pillow so you
have full pixel-level control with no browser dependency.

Supported presets:
  - instagram_square   : 1080×1080
  - instagram_portrait : 1080×1350
  - twitter_landscape  : 1600×900
  - twitter_square     : 1080×1080

Usage:
    from src.viz import bar_chart, line_chart, save_chart
    fig = bar_chart(df, x="state", y="rate", title="DUI Rate by State")
    save_chart(fig, cfg, "dui_rate_by_state", preset="instagram_square")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from PIL import Image

# ---------------------------------------------------------------------------
# Platform presets (width px, height px, DPI)
# Matplotlib figsize is in inches; we derive it from px / dpi.
# ---------------------------------------------------------------------------

PRESETS: dict[str, tuple[int, int, int]] = {
    "instagram_square":   (1080, 1080, 150),
    "instagram_portrait": (1080, 1350, 150),
    "twitter_landscape":  (1600,  900, 150),
    "twitter_square":     (1080, 1080, 150),
}

# Default style — clean, minimal, no chartjunk
_STYLE = {
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.25,
    "axes.axisbelow":     True,
    "font.family":        "sans-serif",
}


def _fig_for_preset(preset: str) -> tuple[plt.Figure, plt.Axes]:
    """Create a (fig, ax) pair sized for the given platform preset."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from: {list(PRESETS)}")
    w_px, h_px, dpi = PRESETS[preset]
    fig_w = w_px / dpi
    fig_h = h_px / dpi
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    return fig, ax


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    subtitle: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = "#2563EB",
    preset: str = "instagram_square",
    sort: bool = True,
) -> plt.Figure:
    """Horizontal bar chart, sorted descending by default.

    Args:
        df:       DataFrame with at least the x and y columns.
        x:        Category column (will appear on the y-axis of a hbar).
        y:        Numeric column.
        title:    Bold headline text.
        subtitle: Smaller text below the title.
        color:    Bar fill color (hex or named).
        preset:   Platform preset key.
        sort:     Sort bars by value descending.
    """
    data = df[[x, y]].dropna().copy()
    if sort:
        data = data.sort_values(y, ascending=True)  # ascending for hbar

    fig, ax = _fig_for_preset(preset)
    with plt.rc_context(_STYLE):
        bars = ax.barh(data[x].astype(str), data[y], color=color)
        ax.bar_label(bars, fmt="{:,.0f}", padding=4, fontsize=9)
        ax.set_xlabel(ylabel or y)
        ax.set_ylabel(xlabel or x)
        _add_title_block(fig, ax, title, subtitle)
    return fig


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    title: str = "",
    subtitle: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: list[str] | None = None,
    preset: str = "twitter_landscape",
    markers: bool = True,
) -> plt.Figure:
    """Line chart supporting one or multiple y series.

    Args:
        y: Single column name, or list of column names for multi-line.
    """
    y_cols = [y] if isinstance(y, str) else y
    default_colors = ["#2563EB", "#DC2626", "#16A34A", "#D97706", "#7C3AED"]
    colors = colors or default_colors[: len(y_cols)]

    fig, ax = _fig_for_preset(preset)
    with plt.rc_context(_STYLE):
        for col, clr in zip(y_cols, colors):
            ax.plot(
                df[x],
                df[col],
                color=clr,
                linewidth=2.5,
                marker="o" if markers else None,
                markersize=5,
                label=col,
            )
        if len(y_cols) > 1:
            ax.legend(framealpha=0.8)
        ax.set_xlabel(xlabel or x)
        ax.set_ylabel(ylabel or (y_cols[0] if len(y_cols) == 1 else ""))
        _add_title_block(fig, ax, title, subtitle)
    return fig


def ranked_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    subtitle: str = "",
    top_n: int = 10,
    color: str = "#2563EB",
    highlight_color: str = "#DC2626",
    highlight_values: list[str] | None = None,
    preset: str = "instagram_portrait",
) -> plt.Figure:
    """Top-N horizontal bar chart with optional highlighted bars.

    Great for 'Top 10 states by X' social posts.

    Args:
        top_n:             Keep only the top N rows by y value.
        highlight_values:  x values to color differently (e.g., ["California"]).
    """
    data = df[[x, y]].dropna().nlargest(top_n, y).sort_values(y, ascending=True)
    bar_colors = [
        highlight_color if str(v) in (highlight_values or []) else color
        for v in data[x]
    ]

    fig, ax = _fig_for_preset(preset)
    with plt.rc_context(_STYLE):
        bars = ax.barh(data[x].astype(str), data[y], color=bar_colors)
        ax.bar_label(bars, fmt="{:,.0f}", padding=4, fontsize=9)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        _add_title_block(fig, ax, title, subtitle)
    return fig


# ---------------------------------------------------------------------------
# Taskmaster-specific chart builders
# ---------------------------------------------------------------------------

# Five brand colors — used to shade the five contestant segments per series.
_SEGMENT_COLORS = ["#003049", "#005F73", "#0A9396", "#EE9B00", "#AE2012"]


def _seg_text_color(hex_color: str) -> str:
    """Pick black/white label text for contrast against a segment fill."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#003049" if luminance > 0.6 else "#FFFFFF"


def stacked_share_bar(
    df: pd.DataFrame,
    series_col: str = "series",
    contestant_col: str = "contestant",
    share_col: str = "pct_of_series_points",
    rank_col: str = "series_rank",
    title: str = "How each Taskmaster series split its points",
    subtitle: str = "Each bar is one series; segments are contestants' share of that series' total points",
    source: str = "Source: Taskmaster UK series 1\u201321, contestant point totals",
    figsize: tuple[float, float] = (12, 13),
    dpi: int = 150,
) -> plt.Figure:
    """Horizontal stacked bar: one bar per series, segments = contestant point share.

    Bars run 0\u2013100% so series are directly comparable regardless of episode count.
    Within each bar, contestants are ordered best\u2192worst (left\u2192right) and each
    segment is labelled with the contestant's name and share.

    Args:
        df:             Prepared metrics frame (from add_series_metrics).
        share_col:      Column holding each contestant's share of series points.
        rank_col:       Within-series rank (1 = best); controls left\u2192right order.
        figsize/dpi:    Figure sizing (tall, since there are 21 series).
    """
    series_ids = sorted(df[series_col].unique())

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        for row_i, s in enumerate(series_ids):
            block = df[df[series_col] == s].sort_values(rank_col)
            left = 0.0
            for seg_i, (_, r) in enumerate(block.iterrows()):
                share = r[share_col]
                color = _SEGMENT_COLORS[seg_i % len(_SEGMENT_COLORS)]
                ax.barh(row_i, share, left=left, color=color, edgecolor="white", linewidth=1.2)
                # Label segments wide enough to fit text.
                if share >= 0.07:
                    ax.text(
                        left + share / 2, row_i,
                        f"{r[contestant_col]}\n{share*100:.0f}%",
                        ha="center", va="center", fontsize=7.5,
                        color=_seg_text_color(color), linespacing=0.95,
                    )
                left += share

        ax.set_yticks(range(len(series_ids)))
        ax.set_yticklabels([f"Series {s}" for s in series_ids], fontsize=9)
        ax.invert_yaxis()  # Series 1 at the top
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
        ax.set_xlabel("Share of series points")
        ax.grid(False)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

        _title_and_source(fig, ax, title, subtitle, source)
    return fig


def all_contestants_ranked(
    df: pd.DataFrame,
    contestant_col: str = "contestant",
    series_col: str = "series",
    value_col: str = "share_vs_equal",
    title: str = "Every Taskmaster contestant, ranked",
    subtitle: str = "Share of series points vs an even split (1.0 = an average contestant that series)",
    source: str = "Source: Taskmaster UK series 1\u201321, contestant point totals",
    highlight_winners: bool = True,
    figsize: tuple[float, float] = (11, 24),
    dpi: int = 150,
) -> plt.Figure:
    """Horizontal bar ranking ALL contestants on a normalized metric, best on top.

    Uses ``share_vs_equal`` by default so contestants from different-length series
    are compared fairly (1.0 = exactly the average contestant in that series).
    A reference line at 1.0 marks the "average contestant" mark.

    Args:
        value_col:         Normalized metric to rank on.
        highlight_winners: Colour series winners distinctly.
        figsize/dpi:       Figure sizing (very tall \u2014 105 bars).
    """
    data = df.sort_values(value_col, ascending=True).copy()  # ascending -> best on top after barh
    labels = [f"{r[contestant_col]}  (S{r[series_col]})" for _, r in data.iterrows()]

    is_winner = data.get("is_winner")
    if highlight_winners and is_winner is not None:
        colors = ["#EE9B00" if w else "#005F73" for w in is_winner]
    else:
        colors = ["#005F73"] * len(data)

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.barh(range(len(data)), data[value_col], color=colors)
        ax.set_yticks(range(len(data)))
        ax.set_yticklabels(labels, fontsize=6.5)
        ax.set_ylim(-1, len(data))
        ax.axvline(1.0, color="#9B2226", linewidth=1.2, linestyle="--", alpha=0.8)
        ax.text(1.0, len(data) - 0.5, "  average contestant (1.0)",
                color="#9B2226", fontsize=8, va="top", ha="left")
        ax.set_xlabel("Share of series points vs even split")
        ax.grid(axis="x", alpha=0.25)
        ax.grid(axis="y", visible=False)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        if highlight_winners and is_winner is not None:
            from matplotlib.patches import Patch
            ax.legend(handles=[
                Patch(color="#EE9B00", label="Series winner"),
                Patch(color="#005F73", label="Other contestant"),
            ], loc="lower right", framealpha=0.9, fontsize=8)
        _title_and_source(fig, ax, title, subtitle, source)
    return fig


def winners_ranked(
    df: pd.DataFrame,
    contestant_col: str = "contestant",
    series_col: str = "series",
    value_col: str = "pct_of_series_points",
    title: str = "Most dominant Taskmaster champions",
    subtitle: str = "Series winners ranked by their share of the series' total points",
    source: str = "Source: Taskmaster UK series 1\u201321, contestant point totals",
    figsize: tuple[float, float] = (11, 9),
    dpi: int = 150,
) -> plt.Figure:
    """Rank the 21 series winners by how dominant their win was (share of points)."""
    winners = df[df["series_rank"] == 1].sort_values(value_col, ascending=True)
    labels = [f"{r[contestant_col]}  (S{r[series_col]})" for _, r in winners.iterrows()]

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        bars = ax.barh(range(len(winners)), winners[value_col] * 100, color="#EE9B00")
        ax.bar_label(bars, fmt="%.0f%%", padding=3, fontsize=8)
        ax.set_yticks(range(len(winners)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Winner's share of series points (%)")
        ax.grid(axis="x", alpha=0.25)
        ax.grid(axis="y", visible=False)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        _title_and_source(fig, ax, title, subtitle, source)
    return fig


def _title_and_source(
    fig: plt.Figure,
    ax: plt.Axes,
    title: str,
    subtitle: str,
    source: str,
) -> None:
    """Left-aligned bold title, grey subtitle, and a small source line at the bottom."""
    if title:
        ax.set_title(title, fontsize=15, fontweight="bold", pad=26, loc="left")
    if subtitle:
        ax.annotate(
            subtitle, xy=(0, 1), xycoords="axes fraction",
            xytext=(0, 12), textcoords="offset points",
            fontsize=9.5, color="#6B7280", ha="left", va="bottom",
        )
    if source:
        fig.text(0.01, 0.005, source, fontsize=7.5, color="#9CA3AF", ha="left", va="bottom")
    fig.tight_layout(rect=[0, 0.02, 1, 1])


# ---------------------------------------------------------------------------
# Title block helper
# ---------------------------------------------------------------------------

def _add_title_block(
    fig: plt.Figure,
    ax: plt.Axes,
    title: str,
    subtitle: str,
) -> None:
    """Add a title and optional subtitle with consistent styling."""
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=12, loc="left")
    if subtitle:
        fig.text(
            0.125, 0.96, subtitle,
            fontsize=9, color="#6B7280",
            ha="left", va="top",
            transform=fig.transFigure,
        )
    fig.tight_layout(rect=[0, 0, 1, 0.94] if subtitle else [0, 0, 1, 1])


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_chart(
    fig: plt.Figure,
    cfg: dict[str, Any],
    filename: str,
    preset: str = "instagram_square",
    add_watermark: str = "",
    show: bool = True,
) -> Path:
    """Save a matplotlib figure to outputs/ as a PNG and display it inline.

    Args:
        fig:           Figure returned by any chart builder above.
        cfg:           Loaded config dict.
        filename:      Output filename without extension.
        preset:        Used to verify final pixel dimensions via Pillow.
        add_watermark: Optional short text drawn in the bottom-right corner.
                       Useful for branding without exposing your identity
                       (e.g. "@unwelcomedata").
        show:          When True (default), render the figure inline in the
                       notebook before closing it.
    """
    out_dir = Path(cfg["paths"]["outputs"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filename}.png"

    if add_watermark:
        _add_watermark(fig, add_watermark)

    w_px, h_px, dpi = PRESETS.get(preset, (1080, 1080, 150))
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")

    if show:
        from IPython.display import display
        display(fig)
    plt.close(fig)

    # Verify and optionally resize to exact pixel dimensions
    img = Image.open(out_path)
    if img.size != (w_px, h_px):
        img = img.resize((w_px, h_px), Image.LANCZOS)
        img.save(out_path, format="PNG", optimize=True)

    print(f"Saved chart → {out_path}  ({w_px}×{h_px} px, preset={preset})")
    return out_path


def _add_watermark(fig: plt.Figure, text: str) -> None:
    """Draw a faint watermark in the lower-right corner of the figure."""
    fig.text(
        0.98, 0.02, text,
        fontsize=8, color="#9CA3AF", alpha=0.7,
        ha="right", va="bottom",
        transform=fig.transFigure,
    )


def save_fig(
    fig: plt.Figure,
    cfg: dict[str, Any],
    filename: str,
    add_watermark: str = "@unwelcomedata",
    dpi: int = 150,
    show: bool = True,
) -> Path:
    """Save a figure at its natural size (no preset resize) and display it inline.

    Use for custom-sized exploratory charts (e.g. the tall 105-bar ranking or
    the 21-row stacked share bar) where forcing a social preset would distort
    the aspect ratio. Social-ready exports still use save_chart() with a preset.

    Args:
        show: When True (default), render the figure inline in the notebook
              before closing it. Keep this on so every chart is visible in the
              notebook, not just written to disk.
    """
    out_dir = Path(cfg["paths"]["outputs"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filename}.png"
    if add_watermark:
        _add_watermark(fig, add_watermark)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"Saved chart → {out_path}")
    if show:
        # Display inline in the notebook, then close to free memory.
        from IPython.display import display
        display(fig)
    plt.close(fig)
    return out_path
