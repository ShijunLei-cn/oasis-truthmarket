#!/usr/bin/env python3
"""
RQ2 Figures — Seller Communication under Different Constraints

Figure 4 : rq2_seller_comm_deception_by_constraint.png
    Headline : "Under Pressure, Seller Chat Amplifies Deception —
                Warrant Provides Robust Defense"
    3-row faceted bar chart: deceptions per condition, one row per constraint.

Figure 5 : rq2_profit_decomposition_honest_vs_dishonest.png
    Headline : "Warrant Ensures Profit Comes from Honest Trade, Not Deception"
    3-row faceted stacked bar: honest (green) + dishonest (red) profit.

Figure 6 (appendix) : rq2_product_mix_appendix.png
    Headline : "Product Mix Shifts: Warrant Removes Counterfeit Supply (All Listed Products)"
    3-row faceted 100% stacked bar: HQ auth / LQ auth / HQ counterfeit.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    COLORS,
    METRIC_COLORS,
    CONDITION_COLORS,
    INTERFERENCE_CONDITION_COLORS,
    setup_style,
    label_panel,
    load_results_df,
    per_run_values,
    count_deceptions,
    sum_seller_profit,
    sum_buyer_utility,
    honest_buyer_utility,
    dishonest_buyer_utility,
    honest_profit,
    dishonest_profit,
    product_quality_counts,
    product_quality_counts_all,
    mannwhitney_p,
    proportion_ztest_p,
    sig_marker_display,
    add_significance_bracket,
    save_figure,
)

setup_style()

# ── Experiment naming convention ──────────────────────────────────────────────
#   r_wsc_F_<constraint>   → Rep              (Fake channel = no effective seller comm)
#   r_wsc_R_<constraint>   → Rep, Comm        (Real channel = seller comm active)
#   rw_wsc_F_<constraint>  → Rep+Warrant
#   rw_wsc_R_<constraint>  → Rep+Warrant, Comm

# NOTE: no \n in labels — the reviewer asked to remove line breaks from titles
CONSTRAINTS = [
    ("policy_making",              "Policy-Making"),
    ("pressure_quickprofits",      "Pressure / Quick-Profits"),
    ("psychological-based-attack", "Psychological Attack"),
]

CONDITIONS_ORDER = ["Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm"]

DIR_PREFIXES: Dict[str, str] = {
    "Rep":                "r_wsc_F",
    "Rep, Comm":          "r_wsc_R",
    "Rep+Warrant":        "rw_wsc_F",
    "Rep+Warrant, Comm":  "rw_wsc_R",
}

# X-axis label colors follow the refreshed paper palette
COND_XCOLORS = {
    "Rep":                COLORS["neutral_dark"],
    "Rep, Comm":          COLORS["neutral_dark"],
    "Rep+Warrant":        COLORS["neutral_dark"],
    "Rep+Warrant, Comm":  COLORS["neutral_dark"],
}

def _set_dynamic_ylim_positive(
    ax: plt.Axes,
    tops: List[float],
    pad_ratio: float = 0.20,
    min_top: float = 1.0,
) -> None:
    """Adaptive positive y-limits for bar charts."""
    ymax = max([float(v) for v in tops] + [min_top])
    ax.set_ylim(0, ymax * (1.0 + pad_ratio))


def _set_dynamic_ylim_diverging(
    ax: plt.Axes,
    lows: List[float],
    highs: List[float],
    pad_ratio: float = 0.20,
) -> None:
    """Adaptive diverging y-limits for charts with positive and negative bars."""
    y_lo = min([float(v) for v in lows] + [0.0])
    y_hi = max([float(v) for v in highs] + [0.0, 1.0])
    span = max(y_hi - y_lo, 1.0)
    ax.set_ylim(y_lo - span * pad_ratio * 0.45, y_hi + span * pad_ratio)


def _set_dynamic_ylim_focus_positive(
    ax: plt.Axes,
    values: List[float],
    errs: List[float] | None = None,
    pad_top: float = 0.10,
    pad_bottom: float = 0.08,
) -> None:
    """Tighter positive-axis limits for readability in grouped bar charts.

    If all bars are strictly positive, axis lower bound is set near the minimum
    observed value (instead of forcing 0) to make inter-bar differences clearer.
    If any bar touches/below 0, falls back to 0-based lower bound.
    """
    vals = [float(v) for v in values]
    if not vals:
        ax.set_ylim(0, 1)
        return
    es = [0.0] * len(vals) if errs is None else [float(e) for e in errs]
    tops = [v + e for v, e in zip(vals, es)]
    bots = [v - e for v, e in zip(vals, es)]
    y_hi = max(max(tops), 1.0)
    y_lo = min(bots)
    span = max(y_hi - y_lo, 1.0)
    upper = y_hi + span * pad_top
    has_zero_bar = any(abs(v) <= 1e-12 for v in vals)
    if has_zero_bar:
        lower = 0.0
    elif y_lo > 0:
        lower = max(0.0, y_lo - span * pad_bottom)
    else:
        lower = min(0.0, y_lo - span * pad_bottom * 0.6)
    if upper <= lower:
        upper = lower + 1.0
    ax.set_ylim(lower, upper)


def _load_cond(base_dir: str, constraint_key: str, cond: str) -> pd.DataFrame:
    prefix = DIR_PREFIXES[cond]
    return load_results_df(str(Path(base_dir) / f"{prefix}_{constraint_key}"))


def _load_cond_all_constraints(base_dir: str, cond: str) -> pd.DataFrame:
    """Load and merge one condition across all constraints.

    run_id values are namespaced by constraint key so per_run_values treats
    each (constraint, run_id) as an independent sample.
    """
    frames = []
    for c_key, _ in CONSTRAINTS:
        df = _load_cond(base_dir, c_key, cond)
        if df.empty:
            continue
        dfx = df.copy()
        dfx["run_id"] = dfx["run_id"].astype(str).map(lambda rid: f"{c_key}:{rid}")
        frames.append(dfx)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 : Deceptions per condition × constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig4_deception_by_constraint(base_dir: str, output_dir: Path, file_prefix: str = "rq2") -> None:
    n_cols = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        1, n_cols, figsize=(4.5 * n_cols, 3.8),
        gridspec_kw={"wspace": 0.38},
        sharey=False,
    )
    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52
    panel_letters = "abc"

    # Collect all means/stds first for shared y-max reference
    all_data = []
    for c_key, c_label in CONSTRAINTS:
        means, stds, per_runs = [], [], []
        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            vals = per_run_values(df, count_deceptions) if not df.empty else [0.0]
            means.append(np.mean(vals))
            stds.append(np.std(vals, ddof=1) if len(vals) > 1 else 0.0)
            per_runs.append(vals)
        all_data.append((means, stds, per_runs))

    for col_idx, ((c_key, c_label), (means, stds, per_runs)) in enumerate(
        zip(CONSTRAINTS, all_data)
    ):
        ax = axes[col_idx]
        label_panel(ax, panel_letters[col_idx])
        bar_colors = [CONDITION_COLORS[c] for c in CONDITIONS_ORDER]

        ax.bar(xs, means, width=w, color=bar_colors,
               edgecolor="white", linewidth=0.4,
               yerr=stds, capsize=3,
               error_kw={"elinewidth": 1.0, "ecolor": "#555"},
               zorder=3)

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
        if col_idx == 0:
            ax.set_ylabel("Deceptions per Run", fontsize=10)
        max_bar_top = max(m + s for m, s in zip(means, stds)) if means else 1.0
        _set_dynamic_ylim_positive(ax, [max_bar_top], pad_ratio=0.30, min_top=1.0)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])

        # Compact numeric labels above bars
        for xi, (m, s) in enumerate(zip(means, stds)):
            if m > 0:
                ax.text(xs[xi], m + s + max_bar_top * 0.03,
                        f"{m:.1f}",
                        ha="center", va="bottom", fontsize=7,
                        color=METRIC_COLORS["deception_primary"])

        # Significance brackets: Rep vs Rep+Warrant, Rep+Comm vs RW+Comm
        for (ci, cj) in [(0, 2), (1, 3)]:
            p = mannwhitney_p(per_runs[ci], per_runs[cj])
            y_top = max(means[ci] + stds[ci], means[cj] + stds[cj])
            add_significance_bracket(ax, xs[ci], xs[cj], y_top, p,
                                     h_frac=0.08, fontsize=9)

    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / f"{file_prefix}_seller_comm_deception_by_constraint.png")
    print("  [Fig4] Deception facet figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 : Profit decomposition (honest / dishonest stacked)
# ─────────────────────────────────────────────────────────────────────────────

def fig5_profit_decomposition(base_dir: str, output_dir: Path, file_prefix: str = "rq2") -> None:
    n_cols = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        1, n_cols, figsize=(4.5 * n_cols, 3.8),
        gridspec_kw={"wspace": 0.40},
        sharey=False,
    )
    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52
    panel_letters = "abc"

    for col_idx, (c_key, c_label) in enumerate(CONSTRAINTS):
        ax = axes[col_idx]
        label_panel(ax, panel_letters[col_idx])
        h_means, h_stds = [], []
        d_means, d_stds = [], []

        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            if df.empty:
                h_means.append(0.0); h_stds.append(0.0)
                d_means.append(0.0); d_stds.append(0.0)
                continue
            h_vals = per_run_values(df, honest_profit)
            d_vals = per_run_values(df, dishonest_profit)
            h_means.append(np.mean(h_vals))
            h_stds.append(np.std(h_vals, ddof=1) if len(h_vals) > 1 else 0.0)
            d_means.append(np.mean(d_vals))
            d_stds.append(np.std(d_vals, ddof=1) if len(d_vals) > 1 else 0.0)

        # Stacked bars — darker borders for legibility
        ax.bar(xs, h_means, width=w, color=METRIC_COLORS["honest_component"],
               edgecolor="#aaaaaa", linewidth=0.5, label="Honest profit", zorder=3)
        ax.bar(xs, d_means, width=w, bottom=h_means, color=METRIC_COLORS["dishonest_component"],
               edgecolor="#aaaaaa", linewidth=0.5, label="Dishonest profit", zorder=3)

        # Percentage labels inside bars
        for xi in range(len(CONDITIONS_ORDER)):
            total = h_means[xi] + d_means[xi]
            if total <= 0:
                continue
            hp = h_means[xi] / total * 100
            if h_means[xi] > 80:
                ax.text(xs[xi], h_means[xi] / 2,
                        f"{hp:.0f}%\nhonest",
                        ha="center", va="center", fontsize=7,
                        color=METRIC_COLORS["seller_profit_primary"], fontweight="bold")
            dp = d_means[xi] / total * 100
            if d_means[xi] > 30:
                ax.text(xs[xi], h_means[xi] + d_means[xi] / 2,
                        f"{dp:.0f}%\nfraud",
                        ha="center", va="center", fontsize=7,
                        color=METRIC_COLORS["deception_primary"], fontweight="bold")
            elif d_means[xi] > 0:
                ax.text(xs[xi], total + total * 0.02,
                        f"{dp:.0f}% fraud",
                        ha="center", va="bottom", fontsize=7,
                        color=METRIC_COLORS["deception_primary"])

        # Significance brackets — stagger heights to prevent overlap
        bracket_pairs = [("Rep", "Rep+Warrant", 0), ("Rep, Comm", "Rep+Warrant, Comm", 1)]
        ymax_bars = max(h + d for h, d in zip(h_means, d_means)) if h_means else 10
        for (la, lb, tier) in bracket_pairs:
            ia = CONDITIONS_ORDER.index(la)
            ib = CONDITIONS_ORDER.index(lb)
            df_a = _load_cond(base_dir, c_key, la)
            df_b = _load_cond(base_dir, c_key, lb)
            if df_a.empty or df_b.empty:
                continue
            ha_tot = float(df_a["seller_profit"].sum())
            ha_hon = float(df_a[df_a["is_honest"] == True]["seller_profit"].sum())  # noqa
            hb_tot = float(df_b["seller_profit"].sum())
            hb_hon = float(df_b[df_b["is_honest"] == True]["seller_profit"].sum())  # noqa
            if ha_tot == 0 or hb_tot == 0:
                continue
            p = proportion_ztest_p(ha_hon, ha_tot, hb_hon, hb_tot)
            # Stagger: tier 0 draws bracket lower, tier 1 draws it higher
            y_top = ymax_bars * (1.08 + tier * 0.14)
            add_significance_bracket(ax, xs[ia], xs[ib], y_top, p,
                                     h_frac=0.06, fontsize=9)

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
        if col_idx == 0:
            ax.set_ylabel("Seller Profit per Run", fontsize=10)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])
        ymax = max(h + d for h, d in zip(h_means, d_means)) if h_means else 1.0
        _set_dynamic_ylim_positive(ax, [ymax], pad_ratio=0.28, min_top=1.0)

        if col_idx == 0:
            ax.legend(frameon=False, fontsize=8, loc="upper left")

    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / f"{file_prefix}_profit_decomposition_honest_vs_dishonest.png")
    print("  [Fig5] Profit decomposition figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6 (appendix) : Product mix per constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig6_product_mix(base_dir: str, output_dir: Path, file_prefix: str = "rq2") -> None:
    """Grouped bars for product quality shares (RQ3 style)."""
    constraints = _rq3_constraints_with_baseline()
    base_path = Path(base_dir)
    baseline_dir = base_path.parent / "rq2_welfare"
    market_types = _rq3_market_types(baseline_dir)
    bar_colors = INTERFERENCE_CONDITION_COLORS

    def _share_metric(idx: int):
        out: Dict[str, List[float]] = {}
        err: Dict[str, List[float]] = {}
        for mt_key, _mt_label, dir_prefix, baseline_subdir in market_types:
            means, sems = [], []
            for c_key, _ in constraints:
                if c_key == "baseline":
                    df = load_results_df(str(baseline_subdir))
                else:
                    df = load_results_df(str(base_path / f"{dir_prefix}_{c_key}"))
                vals = []
                if not df.empty:
                    for t in per_run_values(df, product_quality_counts_all):
                        total = float(sum(t))
                        vals.append((float(t[idx]) / total * 100.0) if total > 0 else 0.0)
                if not vals:
                    vals = [0.0]
                means.append(float(np.mean(vals)))
                sems.append(_sem(vals))
            out[mt_key] = means
            err[mt_key] = sems
        return out, err

    share_hq, sem_hq = _share_metric(0)
    share_lq, sem_lq = _share_metric(1)
    share_cf, sem_cf = _share_metric(2)

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3), gridspec_kw={"wspace": 0.25})
    group_x = np.arange(len(market_types))
    bw = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bw

    for ax, metric, sems, ylabel in [
        (axes[0], share_hq, sem_hq, "HQ Authentic Share (%)"),
        (axes[1], share_lq, sem_lq, "LQ Authentic Share (%)"),
        (axes[2], share_cf, sem_cf, "HQ Counterfeit Share (%)"),
    ]:
        for idx, (c_key, c_label) in enumerate(constraints):
            x_pos = group_x + offsets[idx]
            vals = [metric[mt_key][idx] for mt_key, *_ in market_types]
            errs = [sems[mt_key][idx] for mt_key, *_ in market_types]
            ax.bar(
                x_pos, vals, width=bw,
                color=bar_colors[c_key], edgecolor="white", linewidth=0.5,
                yerr=errs, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
                label=c_label, zorder=3
            )
        ax.set_xticks(group_x)
        ax.set_xticklabels([mt_label for _, mt_label, _, _ in market_types], fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9.5)
        ytops = []
        yvals = []
        yerrs = []
        for mt_key, *_ in market_types:
            for i in range(len(constraints)):
                ytops.append(metric[mt_key][i] + sems[mt_key][i])
                yvals.append(metric[mt_key][i])
                yerrs.append(sems[mt_key][i])
        _set_dynamic_ylim_focus_positive(ax, yvals, yerrs, pad_top=0.10, pad_bottom=0.08)
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_axisbelow(True)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.02),
               ncol=4, frameon=False, fontsize=9)
    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / f"{file_prefix}_product_mix_appendix.png")
    print("  [Fig6] Grouped product mix appendix figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 7 : Buyer Utility decomposition (honest vs fraud) × constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig7_buyer_utility_by_constraint(base_dir: str, output_dir: Path, file_prefix: str = "rq2") -> None:
    """Stacked bar: honest buyer utility (green, above 0) + fraud-induced loss
    (red, below 0) per condition × constraint.

    Honest utility >= 0 always; dishonest utility is typically negative
    (buyer paid HQ price but received LQ), so it is drawn below the x-axis
    as a diverging segment.
    """
    n_cols = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        1, n_cols, figsize=(4.5 * n_cols, 3.9),
        gridspec_kw={"wspace": 0.40},
        sharey=False,
    )
    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52
    panel_letters = "abc"

    for col_idx, (c_key, c_label) in enumerate(CONSTRAINTS):
        ax = axes[col_idx]
        label_panel(ax, panel_letters[col_idx])
        h_means, h_stds = [], []
        d_means, d_stds = [], []
        per_runs_total = []

        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            if df.empty:
                h_means.append(0.0); h_stds.append(0.0)
                d_means.append(0.0); d_stds.append(0.0)
                per_runs_total.append([0.0])
                continue
            h_vals = per_run_values(df, honest_buyer_utility)
            d_vals = per_run_values(df, dishonest_buyer_utility)
            t_vals = per_run_values(df, sum_buyer_utility)
            h_means.append(np.mean(h_vals))
            h_stds.append(np.std(h_vals, ddof=1) if len(h_vals) > 1 else 0.0)
            d_means.append(np.mean(d_vals))
            d_stds.append(np.std(d_vals, ddof=1) if len(d_vals) > 1 else 0.0)
            per_runs_total.append(t_vals)

        # Honest utility: positive bars above 0
        ax.bar(xs, h_means, width=w,
               color=METRIC_COLORS["honest_component"], edgecolor="#aaaaaa", linewidth=0.5,
               label="Honest utility" if col_idx == 0 else "_", zorder=3)

        # Dishonest utility: typically negative — draw below 0
        # clip to 0 on top so only the negative portion shows below axis
        d_bottoms = [min(dm, 0.0) for dm in d_means]
        d_heights = [abs(dm) if dm < 0 else dm for dm in d_means]
        ax.bar(xs, [dm if dm >= 0 else -dm for dm in d_means],
               width=w, bottom=d_bottoms,
               color=METRIC_COLORS["dishonest_component"], edgecolor="#aaaaaa", linewidth=0.5,
               label="Fraud-induced loss" if col_idx == 0 else "_", zorder=3)

        # Inline percentage labels
        for xi in range(len(CONDITIONS_ORDER)):
            total_abs = abs(h_means[xi]) + abs(d_means[xi])
            if total_abs <= 0:
                continue
            # honest % label inside green bar
            if h_means[xi] > 50:
                hp = h_means[xi] / total_abs * 100
                ax.text(xs[xi], h_means[xi] / 2,
                        f"{hp:.0f}%\nhonest",
                        ha="center", va="center", fontsize=7,
                        color=METRIC_COLORS["buyer_utility_primary"], fontweight="bold")
            # fraud loss label inside or below red bar
            if d_means[xi] < -20:
                dp = abs(d_means[xi]) / total_abs * 100
                ax.text(xs[xi], d_means[xi] / 2,
                        f"{dp:.0f}%\nfraud",
                        ha="center", va="center", fontsize=7,
                        color=METRIC_COLORS["deception_primary"], fontweight="bold")

        # Horizontal zero line
        ax.axhline(0, color="#888888", lw=0.8, zorder=2)

        # Significance brackets on honest utility (above axis)
        bracket_pairs = [("Rep", "Rep+Warrant", 0), ("Rep, Comm", "Rep+Warrant, Comm", 1)]
        ymax_bars = max(h_means) if h_means else 10
        for la, lb, tier in bracket_pairs:
            ia = CONDITIONS_ORDER.index(la)
            ib = CONDITIONS_ORDER.index(lb)
            p = mannwhitney_p(per_runs_total[ia], per_runs_total[ib])
            y_top = ymax_bars * (1.08 + tier * 0.14)
            add_significance_bracket(ax, xs[ia], xs[ib], y_top, p,
                                     h_frac=0.06, fontsize=9)

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
        if col_idx == 0:
            ax.set_ylabel("Buyer Utility per Run", fontsize=10)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])

        d_low = min(d_means) if d_means else 0.0
        h_high = max(h_means) if h_means else 1.0
        _set_dynamic_ylim_diverging(ax, [d_low], [h_high], pad_ratio=0.22)

    # Shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center",
               bbox_to_anchor=(0.5, 0.01), ncol=2,
               frameon=False, fontsize=8)
    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / f"{file_prefix}_buyer_utility_by_constraint.png")
    print("  [Fig7] Buyer utility decomposition figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure All : Aggregate all constraints into one 2x2 summary figure
# ─────────────────────────────────────────────────────────────────────────────

def fig_all_constraints_summary(base_dir: str, output_dir: Path, file_prefix: str = "rq2") -> None:
    """RQ3 grouped 2x2 summary (grouped bars in all subplots)."""
    base_path = Path(base_dir)
    baseline_dir = base_path.parent / "rq2_welfare"
    constraints = _rq3_constraints_with_baseline()
    market_types = _rq3_market_types(baseline_dir)
    bar_colors = INTERFERENCE_CONDITION_COLORS

    def _transaction_count(run_df: pd.DataFrame) -> float:
        return float(len(run_df))

    def _collect(metric_fn):
        means: Dict[str, List[float]] = {}
        sems: Dict[str, List[float]] = {}
        for mt_key, _mt_label, dir_prefix, baseline_subdir in market_types:
            mt_means, mt_sems = [], []
            for c_key, _ in constraints:
                if c_key == "baseline":
                    df = load_results_df(str(baseline_subdir))
                else:
                    df = load_results_df(str(base_path / f"{dir_prefix}_{c_key}"))
                vals = per_run_values(df, metric_fn) if not df.empty else [0.0]
                if not vals:
                    vals = [0.0]
                mt_means.append(float(np.mean(vals)))
                mt_sems.append(_sem(vals))
            means[mt_key] = mt_means
            sems[mt_key] = mt_sems
        return means, sems

    metrics = [
        ("Deceptions per Run", count_deceptions),
        ("Seller Profit per Run", sum_seller_profit),
        ("Buyer Utility per Run", sum_buyer_utility),
        ("Transaction Count per Run", _transaction_count),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.0), gridspec_kw={"wspace": 0.26, "hspace": 0.28})
    axes_flat = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]
    for letter, ax in zip("abcd", axes_flat):
        label_panel(ax, letter)

    group_x = np.arange(len(market_types))
    bw = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bw

    for ax, (ylabel, metric_fn) in zip(axes_flat, metrics):
        means, sems = _collect(metric_fn)
        for idx, (c_key, c_label) in enumerate(constraints):
            x_pos = group_x + offsets[idx]
            vals = [means[mt_key][idx] for mt_key, *_ in market_types]
            errs = [sems[mt_key][idx] for mt_key, *_ in market_types]
            ax.bar(
                x_pos, vals, width=bw,
                color=bar_colors[c_key], edgecolor="white", linewidth=0.5,
                yerr=errs, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
                label=c_label, zorder=3
            )
        ax.set_xticks(group_x)
        ax.set_xticklabels([mt_label for _, mt_label, _, _ in market_types], fontsize=8.5)
        ax.set_ylabel(ylabel, fontsize=9.5)
        flat_vals = [means[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
        flat_errs = [sems[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
        _set_dynamic_ylim_focus_positive(ax, flat_vals, flat_errs, pad_top=0.10, pad_bottom=0.08)
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_axisbelow(True)

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.01),
               ncol=4, frameon=False, fontsize=9)
    fig.subplots_adjust(bottom=0.16)
    save_figure(fig, output_dir / f"{file_prefix}_all_constraints_grouped.png")
    print("  [RQ3] Grouped all-constraints summary figure saved.")


def fig_rq2_all_markettype_dual_metrics(
    base_dir: str, output_dir: Path, file_prefix: str = "rq2", baseline_dir: str | None = None
) -> None:
    """RQ2 ALL figure requested by user:
    - Left: counterfeit HQ count
    - Right: buyer utility per transaction
    X-axis market types: rep / rep comm / rep+warrant / rep+warrant comm
    Within each market type: baseline / policy-making / pressure / psychology
    """
    base_path = Path(base_dir)
    if baseline_dir is None:
        baseline_dir_path = base_path.parent / "rq1"
    else:
        baseline_dir_path = Path(baseline_dir)

    constraints = [
        ("baseline", "Baseline"),
        ("policy_making", "Policy-Making"),
        ("pressure_quickprofits", "Pressure"),
        ("psychological-based-attack", "Psychology"),
    ]
    market_types = [
        ("rep", "Rep", "r_wsc_F", baseline_dir_path / "r_wo"),
        ("rep_comm", "Rep Comm", "r_wsc_R", baseline_dir_path / "r_wo"),
        ("rw", "Rep+Warrant", "rw_wsc_F", baseline_dir_path / "rw_wo"),
        ("rw_comm", "Rep+Warrant Comm", "rw_wsc_R", baseline_dir_path / "rw_wo"),
    ]
    bar_colors = INTERFERENCE_CONDITION_COLORS

    def _sem(vals: List[float]) -> float:
        n = len(vals)
        if n <= 1:
            return 0.0
        return float(np.std(vals, ddof=1) / np.sqrt(n))

    def _buyer_utility_per_transaction(run_df: pd.DataFrame) -> float:
        tx_count = len(run_df)
        if tx_count <= 0:
            return 0.0
        return float(run_df["buyer_utility"].sum() / tx_count)

    # metrics[(metric_name, market_type_key)] = [baseline, policy, pressure, psychology]
    metrics_mean: Dict[str, Dict[str, List[float]]] = {"hq_fake": {}, "buyer_utility": {}}
    metrics_std: Dict[str, Dict[str, List[float]]] = {"hq_fake": {}, "buyer_utility": {}}

    for mt_key, _, dir_prefix, baseline_dir in market_types:
        # Baseline from RQ1 corresponding mechanism
        baseline_df = load_results_df(str(baseline_dir))
        baseline_hq_runs = per_run_values(baseline_df, count_deceptions) if not baseline_df.empty else [0.0]
        baseline_utility_runs = (
            per_run_values(baseline_df, _buyer_utility_per_transaction)
            if not baseline_df.empty else [0.0]
        )
        if not baseline_hq_runs:
            baseline_hq_runs = [0.0]
        if not baseline_utility_runs:
            baseline_utility_runs = [0.0]

        hq_fake_means = []
        hq_fake_stds = []
        utility_means = []
        utility_stds = []
        for c_key, _ in constraints:
            if c_key == "baseline":
                hq_fake_means.append(float(np.mean(baseline_hq_runs)))
                hq_fake_stds.append(_sem(baseline_hq_runs))
                utility_means.append(float(np.mean(baseline_utility_runs)))
                utility_stds.append(_sem(baseline_utility_runs))
                continue

            df = load_results_df(str(base_path / f"{dir_prefix}_{c_key}"))
            if df.empty:
                hq_runs = [0.0]
                utility_runs = [0.0]
            else:
                hq_runs = per_run_values(df, count_deceptions)
                utility_runs = per_run_values(df, _buyer_utility_per_transaction)
                if not hq_runs:
                    hq_runs = [0.0]
                if not utility_runs:
                    utility_runs = [0.0]

            hq_fake_means.append(float(np.mean(hq_runs)))
            hq_fake_stds.append(_sem(hq_runs))
            utility_means.append(float(np.mean(utility_runs)))
            utility_stds.append(_sem(utility_runs))

        metrics_mean["hq_fake"][mt_key] = hq_fake_means
        metrics_std["hq_fake"][mt_key] = hq_fake_stds
        metrics_mean["buyer_utility"][mt_key] = utility_means
        metrics_std["buyer_utility"][mt_key] = utility_stds

    # Plot
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(13.2, 4.8), gridspec_kw={"wspace": 0.24}
    )
    label_panel(ax_left, "a")
    label_panel(ax_right, "b")

    group_x = np.arange(len(market_types))
    bw = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bw

    left_positions = []
    left_values = []
    left_errs = []
    right_positions = []
    right_values = []
    right_errs = []

    for idx, (c_key, c_label) in enumerate(constraints):
        vals_left = [metrics_mean["hq_fake"][mt_key][idx] for mt_key, *_ in market_types]
        errs_left = [metrics_std["hq_fake"][mt_key][idx] for mt_key, *_ in market_types]
        vals_right = [metrics_mean["buyer_utility"][mt_key][idx] for mt_key, *_ in market_types]
        errs_right = [metrics_std["buyer_utility"][mt_key][idx] for mt_key, *_ in market_types]
        x_pos = group_x + offsets[idx]
        color = bar_colors[c_key]

        ax_left.bar(
            x_pos, vals_left, width=bw, color=color, edgecolor="white", linewidth=0.5,
            yerr=errs_left, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
            label=c_label, zorder=3
        )
        ax_right.bar(
            x_pos, vals_right, width=bw, color=color, edgecolor="white", linewidth=0.5,
            yerr=errs_right, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
            label=c_label, zorder=3
        )

        left_positions.extend(x_pos.tolist())
        left_values.extend(vals_left)
        left_errs.extend(errs_left)
        right_positions.extend(x_pos.tolist())
        right_values.extend(vals_right)
        right_errs.extend(errs_right)

    xlabels = [mt_label for _, mt_label, _, _ in market_types]
    ax_left.set_xticks(group_x)
    ax_left.set_xticklabels(xlabels, fontsize=9)
    ax_left.set_ylabel("HQ Counterfeit Count per Run", fontsize=10)

    ax_right.set_xticks(group_x)
    ax_right.set_xticklabels(xlabels, fontsize=9)
    ax_right.set_ylabel("Buyer Utility / Transactions Count", fontsize=10)

    # Unified style
    for ax in (ax_left, ax_right):
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_axisbelow(True)

    _set_dynamic_ylim_focus_positive(ax_left, left_values, left_errs, pad_top=0.10, pad_bottom=0.08)
    _set_dynamic_ylim_focus_positive(ax_right, right_values, right_errs, pad_top=0.10, pad_bottom=0.08)

    # Add explicit zero markers so zero-height bars are visible.
    def _mark_zero_bars(ax, x_positions, values):
        for x, v in zip(x_positions, values):
            if abs(v) < 1e-12:
                ax.scatter([x], [0], s=22, facecolors="none", edgecolors="#555", linewidths=0.9, zorder=5)

    _mark_zero_bars(ax_left, left_positions, left_values)
    _mark_zero_bars(ax_right, right_positions, right_values)

    handles = [
        mpatches.Patch(facecolor=bar_colors[c_key], edgecolor="white", label=c_label)
        for c_key, c_label in constraints
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=4,
        frameon=False,
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / f"{file_prefix}_markettype_hqfake_utility_ratio.png")
    print("  [RQ3] Market-type grouped dual-metric figure saved.")


def _rq3_constraints_with_baseline():
    return [
        ("baseline", "Baseline"),
        ("policy_making", "Policy-Making"),
        ("pressure_quickprofits", "Pressure"),
        ("psychological-based-attack", "Psychology"),
    ]


def _rq3_market_types(baseline_dir: Path):
    return [
        ("rep", "Rep", "r_wsc_F", baseline_dir / "r_wo"),
        ("rep_comm", "Rep Comm", "r_wsc_R", baseline_dir / "r_wo"),
        ("rw", "Rep+Warrant", "rw_wsc_F", baseline_dir / "rw_wo"),
        ("rw_comm", "Rep+Warrant Comm", "rw_wsc_R", baseline_dir / "rw_wo"),
    ]


def _sem(vals: List[float]) -> float:
    n = len(vals)
    if n <= 1:
        return 0.0
    return float(np.std(vals, ddof=1) / np.sqrt(n))


def _rq3_grouped_metric(
    base_dir: str,
    output_dir: Path,
    baseline_dir: str,
    metric_fn,
    ylabel: str,
    out_name: str,
) -> None:
    base_path = Path(base_dir)
    baseline_path = Path(baseline_dir)
    constraints = _rq3_constraints_with_baseline()
    market_types = _rq3_market_types(baseline_path)
    bar_colors = INTERFERENCE_CONDITION_COLORS

    means: Dict[str, List[float]] = {}
    sems: Dict[str, List[float]] = {}
    for mt_key, _, dir_prefix, baseline_subdir in market_types:
        mt_means, mt_sems = [], []
        for c_key, _ in constraints:
            if c_key == "baseline":
                df = load_results_df(str(baseline_subdir))
            else:
                df = load_results_df(str(base_path / f"{dir_prefix}_{c_key}"))
            vals = per_run_values(df, metric_fn) if not df.empty else [0.0]
            if not vals:
                vals = [0.0]
            mt_means.append(float(np.mean(vals)))
            mt_sems.append(_sem(vals))
        means[mt_key] = mt_means
        sems[mt_key] = mt_sems

    fig, ax = plt.subplots(1, 1, figsize=(7.6, 4.4))
    group_x = np.arange(len(market_types))
    bw = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bw

    for idx, (c_key, c_label) in enumerate(constraints):
        x_pos = group_x + offsets[idx]
        vals = [means[mt_key][idx] for mt_key, *_ in market_types]
        errs = [sems[mt_key][idx] for mt_key, *_ in market_types]
        ax.bar(
            x_pos, vals, width=bw,
            color=bar_colors[c_key], edgecolor="white", linewidth=0.5,
            yerr=errs, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
            label=c_label, zorder=3,
        )

    ax.set_xticks(group_x)
    ax.set_xticklabels([mt_label for _, mt_label, _, _ in market_types], fontsize=9)
    ax.set_ylabel(ylabel, fontsize=10)
    flat_vals = [means[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
    flat_errs = [sems[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
    _set_dynamic_ylim_focus_positive(ax, flat_vals, flat_errs, pad_top=0.10, pad_bottom=0.08)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=2, fontsize=8, loc="upper left")
    save_figure(fig, output_dir / out_name)
    print(f"  [RQ3] Saved grouped figure: {out_name}")


def fig_rq3_welfare_overview(base_dir: str, output_dir: Path, baseline_dir: str, file_prefix: str = "rq3") -> None:
    """RQ3 welfare overview with grouped bars by market type and interference constraint."""
    base_path = Path(base_dir)
    baseline_path = Path(baseline_dir)
    constraints = _rq3_constraints_with_baseline()
    market_types = _rq3_market_types(baseline_path)
    bar_colors = INTERFERENCE_CONDITION_COLORS

    def _transaction_count(run_df: pd.DataFrame) -> float:
        return float(len(run_df))

    def _hq_auth_share(run_df: pd.DataFrame) -> float:
        hq_auth, lq_auth, hq_fake = product_quality_counts_all(run_df)
        total = float(hq_auth + lq_auth + hq_fake)
        if total <= 0:
            return 0.0
        return 100.0 * float(hq_auth) / total

    metrics = [
        ("Seller Profit", sum_seller_profit),
        ("Buyer Utility", sum_buyer_utility),
        ("Transactions", _transaction_count),
        ("HQ Auth Share (%)", _hq_auth_share),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.0), gridspec_kw={"wspace": 0.26, "hspace": 0.28})
    axes_flat = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]
    group_x = np.arange(len(market_types))
    bw = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bw

    for ax, (ylabel, metric_fn), letter in zip(axes_flat, metrics, "abcd"):
        label_panel(ax, letter)
        means: Dict[str, List[float]] = {}
        sems: Dict[str, List[float]] = {}
        for mt_key, _mt_label, dir_prefix, baseline_subdir in market_types:
            mt_means, mt_sems = [], []
            for c_key, _ in constraints:
                if c_key == "baseline":
                    df = load_results_df(str(baseline_subdir))
                else:
                    df = load_results_df(str(base_path / f"{dir_prefix}_{c_key}"))
                vals = per_run_values(df, metric_fn) if not df.empty else [0.0]
                if not vals:
                    vals = [0.0]
                mt_means.append(float(np.mean(vals)))
                mt_sems.append(_sem(vals))
            means[mt_key] = mt_means
            sems[mt_key] = mt_sems

        for idx, (c_key, c_label) in enumerate(constraints):
            x_pos = group_x + offsets[idx]
            vals = [means[mt_key][idx] for mt_key, *_ in market_types]
            errs = [sems[mt_key][idx] for mt_key, *_ in market_types]
            ax.bar(
                x_pos, vals, width=bw,
                color=bar_colors[c_key], edgecolor="white", linewidth=0.5,
                yerr=errs, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
                label=c_label, zorder=3
            )
        ax.set_xticks(group_x)
        ax.set_xticklabels([mt_label for _, mt_label, _, _ in market_types], fontsize=8.5)
        ax.set_ylabel(ylabel, fontsize=9.5)
        flat_vals = [means[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
        flat_errs = [sems[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
        _set_dynamic_ylim_focus_positive(ax, flat_vals, flat_errs, pad_top=0.10, pad_bottom=0.08)
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_axisbelow(True)

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.01),
               ncol=4, frameon=False, fontsize=9)
    fig.subplots_adjust(bottom=0.16)
    save_figure(fig, output_dir / f"{file_prefix}_welfare_overview.png")
    print("  [RQ3] Welfare overview figure saved.")


def fig_rq3_profit_decomposition_grouped(
    base_dir: str, output_dir: Path, baseline_dir: str, file_prefix: str = "rq3"
) -> None:
    """Grouped-bar profit decomposition (left: honest, right: dishonest)."""
    base_path = Path(base_dir)
    baseline_path = Path(baseline_dir)
    constraints = _rq3_constraints_with_baseline()
    market_types = _rq3_market_types(baseline_path)
    bar_colors = INTERFERENCE_CONDITION_COLORS

    def _collect(metric_fn):
        means: Dict[str, List[float]] = {}
        sems: Dict[str, List[float]] = {}
        for mt_key, _, dir_prefix, baseline_subdir in market_types:
            mt_means, mt_sems = [], []
            for c_key, _ in constraints:
                if c_key == "baseline":
                    df = load_results_df(str(baseline_subdir))
                else:
                    df = load_results_df(str(base_path / f"{dir_prefix}_{c_key}"))
                vals = per_run_values(df, metric_fn) if not df.empty else [0.0]
                if not vals:
                    vals = [0.0]
                mt_means.append(float(np.mean(vals)))
                mt_sems.append(_sem(vals))
            means[mt_key] = mt_means
            sems[mt_key] = mt_sems
        return means, sems

    h_means, h_sems = _collect(honest_profit)
    d_means, d_sems = _collect(dishonest_profit)

    fig, (ax_h, ax_d) = plt.subplots(1, 2, figsize=(13.0, 4.4), gridspec_kw={"wspace": 0.22})
    group_x = np.arange(len(market_types))
    bw = 0.18
    offsets = np.array([-1.5, -0.5, 0.5, 1.5]) * bw

    for idx, (c_key, c_label) in enumerate(constraints):
        x_pos = group_x + offsets[idx]
        vals_h = [h_means[mt_key][idx] for mt_key, *_ in market_types]
        errs_h = [h_sems[mt_key][idx] for mt_key, *_ in market_types]
        vals_d = [d_means[mt_key][idx] for mt_key, *_ in market_types]
        errs_d = [d_sems[mt_key][idx] for mt_key, *_ in market_types]
        ax_h.bar(
            x_pos, vals_h, width=bw,
            color=bar_colors[c_key], edgecolor="white", linewidth=0.5,
            yerr=errs_h, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
            label=c_label, zorder=3
        )
        ax_d.bar(
            x_pos, vals_d, width=bw,
            color=bar_colors[c_key], edgecolor="white", linewidth=0.5,
            yerr=errs_d, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#666"},
            label=c_label, zorder=3
        )

    for ax, ylab in [
        (ax_h, "Honest Profit per Run"),
        (ax_d, "Dishonest Profit per Run"),
    ]:
        ax.set_xticks(group_x)
        ax.set_xticklabels([mt_label for _, mt_label, _, _ in market_types], fontsize=9)
        ax.set_ylabel(ylab, fontsize=10)
        if ax is ax_h:
            flat_vals = [h_means[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
            flat_errs = [h_sems[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
        else:
            flat_vals = [d_means[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
            flat_errs = [d_sems[mt_key][i] for mt_key, *_ in market_types for i in range(len(constraints))]
        _set_dynamic_ylim_focus_positive(ax, flat_vals, flat_errs, pad_top=0.10, pad_bottom=0.08)
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_axisbelow(True)

    handles, labels = ax_h.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.02),
               ncol=4, frameon=False, fontsize=9)
    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / f"{file_prefix}_profit_decomposition_honest_vs_dishonest.png")
    print("  [RQ3] Grouped profit decomposition figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate RQ2 figures for paper")
    parser.add_argument("--base-dir",
                        default="experiments/gpt-4o-mini/paper/rq2")
    parser.add_argument("--output-dir",
                        default="visualization/figs/paper/rq2")
    parser.add_argument("--file-prefix", default="rq2",
                        help="Prefix for output figure file names.")
    parser.add_argument("--baseline-dir", default=None,
                        help="Optional baseline directory containing r_wo and rw_wo (for ALL markettype figure).")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("RQ2: Generating Paper Figures")
    print("=" * 60)

    print("\n[Fig4] Deception by Constraint…")
    fig4_deception_by_constraint(args.base_dir, output_dir, file_prefix=args.file_prefix)

    print("\n[Fig5] Profit Decomposition…")
    fig5_profit_decomposition(args.base_dir, output_dir, file_prefix=args.file_prefix)

    print("\n[Fig6] Product Mix (appendix)…")
    fig6_product_mix(args.base_dir, output_dir, file_prefix=args.file_prefix)

    print("\n[RQ3] Welfare Overview…")
    fig_rq3_welfare_overview(
        args.base_dir,
        output_dir,
        baseline_dir=(args.baseline_dir if args.baseline_dir else str(Path(args.base_dir).parent / "rq2_welfare")),
        file_prefix=args.file_prefix,
    )

    print("\n[RQ3] Grouped All-Constraints Summary…")
    fig_all_constraints_summary(args.base_dir, output_dir, file_prefix=args.file_prefix)

    print("\n[RQ3] Market-Type Grouped Figure (HQ fake + Utility ratio)…")
    fig_rq2_all_markettype_dual_metrics(
        args.base_dir,
        output_dir,
        file_prefix=args.file_prefix,
        baseline_dir=args.baseline_dir,
    )

    print("\n✅  RQ2 figures saved to:", output_dir)


if __name__ == "__main__":
    main()
