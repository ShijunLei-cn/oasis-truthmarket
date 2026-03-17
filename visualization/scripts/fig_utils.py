#!/usr/bin/env python3
"""
Shared utilities for paper figure generation.

Design principles (per proposal):
- Green = good outcomes (honest profit, authentic HQ, buyer utility gain)
- Red   = bad outcomes (deceptions, counterfeit, dishonest profit)
- Gray  = neutral baseline / no-comm conditions
- Line style distinguishes condition variants; hue carries semantic meaning
- Every comparison figure must include statistical significance markers
"""

import json
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server/script use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import stats


# ─── Semantic Color Palette ──────────────────────────────────────────────────

COLORS = {
    # Good-outcome greens
    "good_dark":    "#1a7a3a",   # Rep+Warrant – primary positive bar
    "good_mid":     "#4caf72",   # Rep – lighter positive bar
    "good_light":   "#a8d8b8",   # stacked honest segment
    "hq_auth":      "#2e7d32",   # HQ authentic product
    "lq_auth":      "#66bb6a",   # LQ authentic product (lighter green)
    # Bad-outcome reds
    "bad_dark":     "#c0392b",   # Rep – high deception bar
    "bad_mid":      "#e57373",   # Rep+Warrant – lower deception bar
    "bad_light":    "#ffcdd2",   # stacked dishonest segment
    "counterfeit":  "#c62828",   # HQ counterfeit product
    # Neutral grays
    "neutral":      "#9e9e9e",   # baseline / no-comm dot/bar
    "neutral_dark": "#424242",   # dark annotation text
    "neutral_light":"#e0e0e0",   # light background panel
    # Accent for annotations
    "accent":       "#1565c0",   # annotation arrow/box border
}

# Consistent condition colors for line charts (RQ3 round evolution)
CONDITION_COLORS = {
    "Rep":                 "#9e9e9e",   # gray
    "Rep, Comm":           "#43a047",   # green (improvement on Rep)
    "Rep+Warrant":         "#1565c0",   # blue
    "Rep+Warrant, Comm":   "#0d47a1",   # deep blue
}
CONDITION_LS = {
    "Rep":                 "-",
    "Rep, Comm":           "--",
    "Rep+Warrant":         "-",
    "Rep+Warrant, Comm":   "--",
}


# ─── Matplotlib Style Setup ──────────────────────────────────────────────────

def setup_style() -> None:
    """Apply global academic plotting style."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.titlesize": 12,
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "grid.color": "#cccccc",
        }
    )


# ─── Statistical Tests ───────────────────────────────────────────────────────

def mannwhitney_p(a: List[float], b: List[float]) -> float:
    """Two-sided Mann-Whitney U test. Returns p-value (1.0 if insufficient data)."""
    a = [x for x in a if x is not None]
    b = [x for x in b if x is not None]
    if len(a) < 2 or len(b) < 2:
        return 1.0
    try:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        return float(p)
    except Exception:
        return 1.0


def proportion_ztest_p(count1: float, n1: float,
                        count2: float, n2: float) -> float:
    """z-score test for equality of two proportions. Returns p-value."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = count1 / n1, count2 / n2
    p_pool = (count1 + count2) / (n1 + n2)
    if p_pool in (0.0, 1.0):
        return 1.0 if p1 == p2 else 0.0
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return float(2 * (1 - stats.norm.cdf(abs(z))))


def sig_marker(p: float) -> str:
    """Return significance stars string."""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def sig_marker_display(p: float) -> Optional[str]:
    """Return significance stars string, or None if not significant."""
    m = sig_marker(p)
    return None if m == "ns" else m


# ─── Significance Bracket Drawing ────────────────────────────────────────────

def add_significance_bracket(
    ax: plt.Axes,
    x1: float,
    x2: float,
    y_base: float,
    p_val: float,
    h_frac: float = 0.04,
    fontsize: int = 9,
) -> None:
    """Draw a bracket + significance marker between two bars.

    Parameters
    ----------
    x1, x2   : bar centre x positions
    y_base    : top of the taller bar (bracket starts here)
    h_frac    : bracket height as fraction of y_base
    """
    marker = sig_marker_display(p_val)
    if marker is None:
        return
    h = max(y_base * h_frac, 2.0)
    y1 = y_base + h * 0.5
    ax.plot(
        [x1, x1, x2, x2],
        [y1, y1 + h, y1 + h, y1],
        lw=1.0, c="black",
    )
    ax.text(
        (x1 + x2) / 2,
        y1 + h + h * 0.2,
        marker,
        ha="center", va="bottom",
        fontsize=fontsize, color="black",
    )


def add_text_box(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    fontsize: int = 8,
    color: str = "#1a7a3a",
    boxcolor: str = "#e8f5e9",
) -> None:
    """Add a highlighted annotation text box."""
    ax.annotate(
        text,
        xy=(x, y),
        fontsize=fontsize,
        color=color,
        ha="center", va="bottom",
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor=boxcolor,
            edgecolor=color,
            alpha=0.9,
            linewidth=0.8,
        ),
    )


def highlight_bar_group(
    ax: plt.Axes,
    x_center: float,
    width: float,
    y_max: float,
    label: str = "",
    color: str = "#fff9c4",
    border: str = "#f57f17",
) -> None:
    """Draw a shaded rectangle around a bar group to highlight it."""
    rect = mpatches.FancyBboxPatch(
        (x_center - width / 2, 0),
        width,
        y_max * 1.15,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor=border,
        linewidth=1.2,
        alpha=0.35,
        zorder=0,
    )
    ax.add_patch(rect)
    if label:
        ax.text(
            x_center,
            y_max * 1.18,
            label,
            ha="center", va="bottom",
            fontsize=7, color=border,
            fontweight="bold",
        )


# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_results_df(experiment_dir: str) -> pd.DataFrame:
    """Load all run_*_results.json from a directory into one DataFrame."""
    path = Path(experiment_dir)
    if not path.exists():
        print(f"  WARNING: directory not found: {experiment_dir}")
        return pd.DataFrame()
    rows = []
    for f in sorted(path.glob("run_*_results.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            run_id = int(f.stem.split("_")[1])
            for item in data:
                item["run_id"] = run_id
            rows.extend(data)
        except Exception as e:
            print(f"  ERROR loading {f}: {e}")
    if not rows:
        print(f"  WARNING: no results in {experiment_dir}")
        return pd.DataFrame()
    return pd.DataFrame(rows)


def load_probes_df(experiment_dir: str) -> pd.DataFrame:
    """Load all run_*_cognitive_probes.json from a directory."""
    path = Path(experiment_dir)
    if not path.exists():
        return pd.DataFrame()
    rows = []
    for f in sorted(path.glob("run_*_cognitive_probes.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            run_id = int(f.stem.split("_")[1])
            for item in data:
                item["run_id"] = run_id
            rows.extend(data)
        except Exception as e:
            print(f"  ERROR loading {f}: {e}")
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def per_run_values(df: pd.DataFrame, fn) -> List[float]:
    """Apply aggregation fn to each run_id subset; return list of per-run scalars."""
    if df.empty or "run_id" not in df.columns:
        return []
    results = []
    for rid in sorted(df["run_id"].unique()):
        val = fn(df[df["run_id"] == rid])
        results.append(val)
    return results


def count_deceptions(run_df: pd.DataFrame) -> float:
    return float((run_df["is_honest"] == False).sum())  # noqa: E712


def sum_seller_profit(run_df: pd.DataFrame) -> float:
    return float(run_df["seller_profit"].sum())


def sum_buyer_utility(run_df: pd.DataFrame) -> float:
    return float(run_df["buyer_utility"].sum())


def honest_profit(run_df: pd.DataFrame) -> float:
    return float(run_df[run_df["is_honest"] == True]["seller_profit"].sum())  # noqa: E712


def dishonest_profit(run_df: pd.DataFrame) -> float:
    return float(run_df[run_df["is_honest"] == False]["seller_profit"].sum())  # noqa: E712


def count_counterfeit_sold(run_df: pd.DataFrame) -> float:
    q_col = next(
        (c for c in ["quality", "actual_quality", "true_quality"] if c in run_df.columns),
        None,
    )
    a_col = "advertised_quality" if "advertised_quality" in run_df.columns else None
    s_col = next((c for c in ["sold", "is_sold"] if c in run_df.columns), None)
    if not (q_col and a_col and s_col):
        return 0.0
    df = run_df.copy()
    df[q_col] = df[q_col].astype(str).str.upper().str.strip()
    df[a_col] = df[a_col].astype(str).str.upper().str.strip()
    mask = (df[a_col] == "HQ") & (df[q_col] == "LQ") & (df[s_col] == True)  # noqa: E712
    return float(mask.sum())


def product_quality_counts(run_df: pd.DataFrame):
    """Return (hq_auth_sold, lq_auth_sold, hq_counterfeit_sold) for a run."""
    q_col = next(
        (c for c in ["quality", "actual_quality", "true_quality"] if c in run_df.columns),
        None,
    )
    a_col = "advertised_quality" if "advertised_quality" in run_df.columns else None
    s_col = next((c for c in ["sold", "is_sold"] if c in run_df.columns), None)
    if not (q_col and a_col):
        return 0.0, 0.0, 0.0
    df = run_df.copy()
    df[q_col] = df[q_col].astype(str).str.upper().str.strip()
    df[a_col] = df[a_col].astype(str).str.upper().str.strip()
    sold = (df[s_col] == True) if s_col else pd.Series(False, index=df.index)  # noqa: E712
    hq_auth = float(((df[a_col] == "HQ") & (df[q_col] == "HQ") & sold).sum())
    lq_auth = float(((df[a_col] == "LQ") & (df[q_col] == "LQ") & sold).sum())
    hq_cfeit = float(((df[a_col] == "HQ") & (df[q_col] == "LQ") & sold).sum())
    return hq_auth, lq_auth, hq_cfeit


# ─── Footnote Helper ─────────────────────────────────────────────────────────

def add_sig_footnote(fig: plt.Figure, extra: str = "") -> None:
    """Add a standard significance-marker footnote at the bottom of a figure.

    Explains the *, **, *** notation so readers know the p-value thresholds.
    """
    note = (
        "Significance markers: * p<0.05,  ** p<0.01,  *** p<0.001  "
        "(Mann-Whitney U for totals; z-score proportion test for rates)"
    )
    if extra:
        note = note + "   |   " + extra
    fig.text(
        0.5, -0.02,
        note,
        ha="center", va="top",
        fontsize=7, color="#555555",
        style="italic",
        transform=fig.transFigure,
    )


# ─── Save Helper ─────────────────────────────────────────────────────────────

def save_figure(fig: plt.Figure, output_path: Path, dpi: int = 300) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {output_path}")
