#!/usr/bin/env python3
"""
Shared utilities for paper figure generation.

Design principles (paper palette refresh):
- Sage / teal = positive outcomes and coordination improvements
- Orange / sand = deceptive or harmful outcomes
- Lavender = neutral baseline and low-emphasis comparison
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
    # Positive outcomes: image-inspired sage / teal palette
    "good_dark":    "#6BBFD0",   # teal — stronger positive / warrant-enhanced
    "good_mid":     "#A9C89E",   # sage — baseline positive
    "good_light":   "#C6C9DC",   # lavender mist — light positive fill
    # Product quality colors
    "hq_auth":      "#6BBFD0",   # teal — HQ authentic
    "lq_auth":      "#A9C89E",   # sage — LQ authentic
    # Negative outcomes: orange / sand palette
    "bad_dark":     "#F39030",   # vivid orange — deception
    "bad_mid":      "#F3D28A",   # warm sand — lighter deception
    "bad_light":    "#F3D28A",   # sand — dishonest segment fill
    "counterfeit":  "#CFBED3",   # soft lilac — counterfeit / third stacked segment
    # Neutral and low-emphasis tones
    "neutral":      "#C6C9DC",   # lavender gray — neutral baseline
    "neutral_dark": "#4F5D73",   # desaturated slate — annotation text
    "neutral_light":"#F4F3F7",   # paper-like background tint
    # Accent for annotations
    "accent":       "#6BBFD0",   # teal accent — annotation arrows/borders
    # Communication / mechanism colors
    "comm_dark":    "#6BBFD0",   # teal — comm-enhanced condition
    "comm_mid":     "#C6C9DC",   # lavender — lighter comm comparison
    "comm_baseline":"#CFBED3",   # lilac — baseline comm reference
    # Mechanism colors
    "rep_dark":     "#6BBFD0",   # teal — Rep with communication or emphasis
    "rep_mid":      "#A9C89E",   # sage — Rep baseline
    "warrant_dark": "#CFBED3",   # lilac — Rep+Warrant emphasized
    "warrant_mid":  "#C6C9DC",   # lavender — Rep+Warrant baseline
}

METRIC_COLORS = {
    "seller_profit_primary": COLORS["good_dark"],
    "seller_profit_secondary": COLORS["good_mid"],
    "buyer_utility_primary": COLORS["accent"],
    "buyer_utility_secondary": COLORS["comm_mid"],
    "deception_primary": COLORS["bad_dark"],
    "deception_secondary": COLORS["bad_mid"],
    "transactions_primary": COLORS["neutral_dark"],
    "transactions_secondary": COLORS["neutral"],
    "honest_component": COLORS["good_light"],
    "dishonest_component": COLORS["bad_light"],
}

# Consistent condition colors for line charts (RQ3 round evolution)
CONDITION_COLORS = {
    "Rep":                 COLORS["neutral"],
    "Rep, Comm":           COLORS["good_mid"],
    "Rep+Warrant":         COLORS["neutral"],
    "Rep+Warrant, Comm":   COLORS["good_dark"],
}
CONDITION_LS = {
    "Rep":                 "-",
    "Rep, Comm":           "--",
    "Rep+Warrant":         "-",
    "Rep+Warrant, Comm":   "--",
}

# Consistent colors for interference constraints (baseline/policy/pressure/psychology)
INTERFERENCE_CONDITION_COLORS = {
    "baseline": COLORS["neutral"],
    "policy_making": COLORS["good_mid"],
    "pressure_quickprofits": COLORS["accent"],
    "psychological-based-attack": COLORS["bad_mid"],
}


# ─── Matplotlib Style Setup ──────────────────────────────────────────────────

def setup_style() -> None:
    """Apply global Nature/Science-inspired academic plotting style."""
    plt.rcParams.update(
        {
            # ── Typography ──────────────────────────────────────────────────
            "font.family":          "sans-serif",
            "font.sans-serif":      ["Helvetica Neue", "Helvetica", "Arial",
                                     "Liberation Sans", "DejaVu Sans"],
            "font.size":            9,
            "axes.labelsize":       9,
            "axes.titlesize":       10,
            "xtick.labelsize":      8,
            "ytick.labelsize":      8,
            "legend.fontsize":      8,
            "figure.titlesize":     11,
            "axes.unicode_minus":   False,
            # ── Spines & frame ──────────────────────────────────────────────
            "axes.spines.top":      False,
            "axes.spines.right":    False,
            "axes.linewidth":       0.7,
            # ── Grid: off by default (Nature style) ─────────────────────────
            "axes.grid":            False,
            "axes.axisbelow":       True,
            # ── Ticks: outward, thin ─────────────────────────────────────────
            "xtick.direction":      "out",
            "ytick.direction":      "out",
            "xtick.major.width":    0.7,
            "ytick.major.width":    0.7,
            "xtick.major.size":     3.5,
            "ytick.major.size":     3.5,
            "xtick.minor.width":    0.4,
            "ytick.minor.width":    0.4,
            # ── Lines & patches ─────────────────────────────────────────────
            "lines.linewidth":      1.2,
            "patch.linewidth":      0.5,
            # ── Backgrounds ─────────────────────────────────────────────────
            "figure.facecolor":     "white",
            "axes.facecolor":       "white",
        }
    )


def label_panel(ax: "plt.Axes", letter: str,
                fontsize: int = 10,
                x: float = -0.12, y: float = 1.04) -> None:
    """Add a bold (a)/(b)/… panel label at the top-left corner of an axes."""
    ax.text(x, y, f"({letter})",
            transform=ax.transAxes,
            fontsize=fontsize, fontweight="bold",
            va="bottom", ha="right")


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
    color: str = COLORS["good_dark"],
    boxcolor: str = COLORS["neutral_light"],
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

def _extract_transactions_from_actions(actions_file: Path, run_id: int) -> list:
    """Extract flat transaction rows from a run_*_actions.json file.

    The actions.json stores per-round agent actions; buyer purchase_products
    results contain the transaction records we need for analysis.
    """
    rows = []
    data = json.loads(actions_file.read_text(encoding="utf-8"))
    for rnd in data:
        round_num = rnd.get("round", None)
        for agent in rnd.get("agent_infos", []):
            info = agent.get("agent_action_info", {})
            if not isinstance(info, dict):
                continue
            if info.get("action_name") != "purchase_products":
                continue
            results = info.get("action_results", {})
            # action_results may be a JSON string or already a dict
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except Exception:
                    continue
            for txn in results.get("transactions", []):
                adv = str(txn.get("advertised_quality", "")).upper().strip()
                true = str(txn.get("true_quality", "")).upper().strip()
                rows.append({
                    "run_id": run_id,
                    "round": round_num,
                    "transaction_id": txn.get("transaction_id"),
                    "product_id": txn.get("product_id"),
                    "seller_id": txn.get("seller_id"),
                    "advertised_quality": adv,
                    "true_quality": true,
                    "has_warrant": txn.get("has_warrant"),
                    "seller_profit": txn.get("seller_profit", 0.0),
                    "buyer_utility": txn.get("buyer_utility", 0.0),
                    "purchase_price": txn.get("purchase_price"),
                    "is_honest": adv == true,
                    "sold": True,
                    "is_sold": True,
                    "quality": true,
                    "actual_quality": true,
                })
    return rows


def load_results_df(experiment_dir: str) -> pd.DataFrame:
    """Load transaction data from a directory into one DataFrame.

    Tries run_*_results.json first; falls back to extracting transactions
    from run_*_actions.json when results files are absent.
    """
    path = Path(experiment_dir)
    if not path.exists():
        print(f"  WARNING: directory not found: {experiment_dir}")
        return pd.DataFrame()
    rows = []
    # Primary: flat results files
    for f in sorted(path.glob("run_*_results.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            run_id = int(f.stem.split("_")[1])
            for item in data:
                item["run_id"] = run_id
            rows.extend(data)
        except Exception as e:
            print(f"  ERROR loading {f}: {e}")
    # Fallback: extract transactions from actions files
    if not rows:
        for f in sorted(path.glob("run_*_actions.json")):
            try:
                run_id = int(f.stem.split("_")[1])
                rows.extend(_extract_transactions_from_actions(f, run_id))
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


def honest_buyer_utility(run_df: pd.DataFrame) -> float:
    return float(run_df[run_df["is_honest"] == True]["buyer_utility"].sum())  # noqa: E712


def dishonest_buyer_utility(run_df: pd.DataFrame) -> float:
    return float(run_df[run_df["is_honest"] == False]["buyer_utility"].sum())  # noqa: E712


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
    return _product_quality_counts_by_status(run_df, only_sold=True)


def product_quality_counts_all(run_df: pd.DataFrame):
    """Return (hq_auth_listed, lq_auth_listed, hq_counterfeit_listed) for ALL listed products (including unsold)."""
    return _product_quality_counts_by_status(run_df, only_sold=False)


def _product_quality_counts_by_status(run_df: pd.DataFrame, only_sold: bool = True):
    """Internal helper: count product quality for sold or listed products."""
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
    if only_sold and s_col:
        sold = (df[s_col] == True)  # noqa: E712
    else:
        sold = pd.Series(True, index=df.index)  # All listed products
    hq_auth = float(((df[a_col] == "HQ") & (df[q_col] == "HQ") & sold).sum())
    lq_auth = float(((df[a_col] == "LQ") & (df[q_col] == "LQ") & sold).sum())
    hq_cfeit = float(((df[a_col] == "HQ") & (df[q_col] == "LQ") & sold).sum())
    return hq_auth, lq_auth, hq_cfeit


# ─── Footnote Helper ─────────────────────────────────────────────────────────

def add_sig_footnote(fig: plt.Figure, extra: str = "", y: float = -0.02) -> None:
    """Add a standard significance-marker footnote at the bottom of a figure.

    Explains the *, **, *** notation so readers know the p-value thresholds.

    Parameters
    ----------
    y : float
        Vertical position in figure coordinates (default -0.02).
        Pass a more negative value (e.g. -0.10) when the figure has an
        external legend below the axes to avoid overlap.
    """
    note = (
        "Significance markers: * p<0.05,  ** p<0.01,  *** p<0.001  "
        "(Mann-Whitney U for totals; z-score proportion test for rates)"
    )
    if extra:
        note = note + "   |   " + extra
    fig.text(
        0.5, y,
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
