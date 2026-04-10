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
    setup_style,
    label_panel,
    load_results_df,
    per_run_values,
    count_deceptions,
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
    add_text_box,
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

_UTIL_COLORS = {
    "Rep":                METRIC_COLORS["buyer_utility_secondary"],
    "Rep, Comm":          METRIC_COLORS["buyer_utility_primary"],
    "Rep+Warrant":        METRIC_COLORS["buyer_utility_secondary"],
    "Rep+Warrant, Comm":  METRIC_COLORS["buyer_utility_primary"],
}


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

def fig4_deception_by_constraint(base_dir: str, output_dir: Path) -> None:
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
        bar_colors = [
            METRIC_COLORS["deception_secondary"],
            METRIC_COLORS["deception_primary"],
            METRIC_COLORS["deception_secondary"],
            METRIC_COLORS["deception_primary"],
        ]

        ax.bar(xs, means, width=w, color=bar_colors,
               edgecolor="white", linewidth=0.4,
               yerr=stds, capsize=3,
               error_kw={"elinewidth": 1.0, "ecolor": "#555"},
               zorder=3)

        max_bar_top = max(m + s for m, s in zip(means, stds)) if means else 1.0
        ylim = max_bar_top * 1.55 + 2

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
        if col_idx == 0:
            ax.set_ylabel("Deceptions per Run", fontsize=10)
        ax.set_ylim(0, ylim)
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
    save_figure(fig, output_dir / "rq2_seller_comm_deception_by_constraint.png")
    print("  [Fig4] Deception facet figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 : Profit decomposition (honest / dishonest stacked)
# ─────────────────────────────────────────────────────────────────────────────

def fig5_profit_decomposition(base_dir: str, output_dir: Path) -> None:
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
        ymax = max(h + d for h, d in zip(h_means, d_means)) if h_means else 10
        ax.set_ylim(0, ymax * 1.50 + 10)

        if col_idx == 0:
            ax.legend(frameon=False, fontsize=8, loc="upper left")

    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / "rq2_profit_decomposition_honest_vs_dishonest.png")
    print("  [Fig5] Profit decomposition figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6 (appendix) : Product mix per constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig6_product_mix(base_dir: str, output_dir: Path) -> None:
    n_cols = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        1, n_cols, figsize=(4.5 * n_cols, 3.8),
        gridspec_kw={"wspace": 0.38},
        sharey=True,
    )
    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52
    seg_colors = [COLORS["hq_auth"], COLORS["lq_auth"], COLORS["counterfeit"]]
    seg_labels = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit (fraud)"]
    panel_letters = "abc"

    for col_idx, (c_key, c_label) in enumerate(CONSTRAINTS):
        ax = axes[col_idx]
        label_panel(ax, panel_letters[col_idx])
        segs: List[List[float]] = [[], [], []]
        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            if df.empty:
                for si in range(3):
                    segs[si].append(0.0)
                continue
            pq_runs = per_run_values(df, product_quality_counts_all)
            means_t = [np.mean([t[i] for t in pq_runs]) for i in range(3)]
            total = sum(means_t)
            for si in range(3):
                segs[si].append(means_t[si] / total * 100 if total > 0 else 0.0)

        bottoms = [0.0] * len(CONDITIONS_ORDER)
        for si in range(3):
            lbl = seg_labels[si] if col_idx == 0 else "_"
            ax.bar(xs, segs[si], width=w, bottom=bottoms,
                   color=seg_colors[si], label=lbl,
                   edgecolor="white", linewidth=0.4, zorder=3)
            for xi, (h, b) in enumerate(zip(segs[si], bottoms)):
                if h > 10.0:   # raise threshold to avoid overlap
                    ax.text(xs[xi], b + h / 2, f"{h:.0f}%",
                            ha="center", va="center", fontsize=7,
                            color="white", fontweight="bold")
            bottoms = [bottoms[xi] + segs[si][xi] for xi in range(len(xs))]

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
        if col_idx == 0:
            ax.set_ylabel("Share of Listed Products (%)", fontsize=10)
        ax.set_ylim(0, 112)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])

    # Collect legend handles from first panel, place below entire figure
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center",
               bbox_to_anchor=(0.5, 0.01), ncol=3,
               frameon=False, fontsize=8)
    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / "rq2_product_mix_appendix.png")
    print("  [Fig6] Product mix appendix figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 7 : Buyer Utility decomposition (honest vs fraud) × constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig7_buyer_utility_by_constraint(base_dir: str, output_dir: Path) -> None:
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

        y_lo = min(0.0, min(d_means) * 1.25) if d_means else 0.0
        y_hi = max(h_means) * 1.55 + 10 if h_means else 10
        ax.set_ylim(y_lo, y_hi)

    # Shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center",
               bbox_to_anchor=(0.5, 0.01), ncol=2,
               frameon=False, fontsize=8)
    fig.subplots_adjust(bottom=0.22)
    save_figure(fig, output_dir / "rq2_buyer_utility_by_constraint.png")
    print("  [Fig7] Buyer utility decomposition figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure All : Aggregate all constraints into one 2x2 summary figure
# ─────────────────────────────────────────────────────────────────────────────

def fig_all_constraints_summary(base_dir: str, output_dir: Path) -> None:
    """Aggregate samples across all three constraints and render 4 RQ2 views in one figure."""
    df_by_cond = {cond: _load_cond_all_constraints(base_dir, cond) for cond in CONDITIONS_ORDER}
    xs = np.arange(len(CONDITIONS_ORDER))

    fig, axes = plt.subplots(2, 2, figsize=(12.0, 8.2), gridspec_kw={"wspace": 0.30, "hspace": 0.34})
    ax_dec, ax_profit = axes[0, 0], axes[0, 1]
    ax_mix, ax_util = axes[1, 0], axes[1, 1]
    label_panel(ax_dec, "a")
    label_panel(ax_profit, "b")
    label_panel(ax_mix, "c")
    label_panel(ax_util, "d")

    # (a) Deceptions
    dec_runs = []
    dec_means, dec_stds = [], []
    for cond in CONDITIONS_ORDER:
        df = df_by_cond[cond]
        vals = per_run_values(df, count_deceptions) if not df.empty else [0.0]
        dec_runs.append(vals)
        dec_means.append(np.mean(vals))
        dec_stds.append(np.std(vals, ddof=1) if len(vals) > 1 else 0.0)
    dec_colors = [
        METRIC_COLORS["deception_secondary"],
        METRIC_COLORS["deception_primary"],
        METRIC_COLORS["deception_secondary"],
        METRIC_COLORS["deception_primary"],
    ]
    ax_dec.bar(xs, dec_means, width=0.56, color=dec_colors, edgecolor="white", linewidth=0.4,
               yerr=dec_stds, capsize=3, error_kw={"elinewidth": 1.0, "ecolor": "#555"}, zorder=3)
    ax_dec.set_ylabel("Deceptions per Run", fontsize=10)
    ax_dec.set_xticks(xs)
    ax_dec.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
    for tick in ax_dec.get_xticklabels():
        tick.set_color(COLORS["neutral_dark"])
    dec_top = max(m + s for m, s in zip(dec_means, dec_stds)) if dec_means else 1.0
    ax_dec.set_ylim(0, dec_top * 1.55 + 2)
    for (ci, cj) in [(0, 2), (1, 3)]:
        p = mannwhitney_p(dec_runs[ci], dec_runs[cj])
        y_top = max(dec_means[ci] + dec_stds[ci], dec_means[cj] + dec_stds[cj])
        add_significance_bracket(ax_dec, xs[ci], xs[cj], y_top, p, h_frac=0.08, fontsize=9)

    # (b) Seller profit decomposition
    h_means, h_stds, d_means, d_stds = [], [], [], []
    for cond in CONDITIONS_ORDER:
        df = df_by_cond[cond]
        if df.empty:
            h_means.append(0.0); h_stds.append(0.0); d_means.append(0.0); d_stds.append(0.0)
            continue
        h_vals = per_run_values(df, honest_profit)
        d_vals = per_run_values(df, dishonest_profit)
        h_means.append(np.mean(h_vals)); d_means.append(np.mean(d_vals))
        h_stds.append(np.std(h_vals, ddof=1) if len(h_vals) > 1 else 0.0)
        d_stds.append(np.std(d_vals, ddof=1) if len(d_vals) > 1 else 0.0)
    ax_profit.bar(xs, h_means, width=0.56, color=METRIC_COLORS["honest_component"],
                  edgecolor="#aaaaaa", linewidth=0.5, label="Honest profit", zorder=3)
    ax_profit.bar(xs, d_means, width=0.56, bottom=h_means, color=METRIC_COLORS["dishonest_component"],
                  edgecolor="#aaaaaa", linewidth=0.5, label="Dishonest profit", zorder=3)
    ax_profit.set_ylabel("Seller Profit per Run", fontsize=10)
    ax_profit.set_xticks(xs)
    ax_profit.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
    for tick in ax_profit.get_xticklabels():
        tick.set_color(COLORS["neutral_dark"])
    ymax_p = max(h + d for h, d in zip(h_means, d_means)) if h_means else 10
    ax_profit.set_ylim(0, ymax_p * 1.50 + 10)
    ax_profit.legend(frameon=False, fontsize=8, loc="upper left")

    # (c) Product mix (all listed)
    seg_colors = [COLORS["hq_auth"], COLORS["lq_auth"], COLORS["counterfeit"]]
    seg_labels = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit (fraud)"]
    segs = [[], [], []]
    for cond in CONDITIONS_ORDER:
        df = df_by_cond[cond]
        if df.empty:
            for si in range(3):
                segs[si].append(0.0)
            continue
        pq_runs = per_run_values(df, product_quality_counts_all)
        means_t = [np.mean([t[i] for t in pq_runs]) for i in range(3)]
        total = sum(means_t)
        for si in range(3):
            segs[si].append(means_t[si] / total * 100 if total > 0 else 0.0)
    bottoms = [0.0] * len(CONDITIONS_ORDER)
    for si in range(3):
        ax_mix.bar(xs, segs[si], width=0.56, bottom=bottoms, color=seg_colors[si],
                   label=seg_labels[si], edgecolor="white", linewidth=0.4, zorder=3)
        bottoms = [bottoms[i] + segs[si][i] for i in range(len(xs))]
    ax_mix.set_ylabel("Share of Listed Products (%)", fontsize=10)
    ax_mix.set_xticks(xs)
    ax_mix.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
    for tick in ax_mix.get_xticklabels():
        tick.set_color(COLORS["neutral_dark"])
    ax_mix.set_ylim(0, 112)
    ax_mix.legend(frameon=False, fontsize=8, loc="upper right")

    # (d) Buyer utility decomposition
    uh_means, ud_means = [], []
    total_runs = []
    for cond in CONDITIONS_ORDER:
        df = df_by_cond[cond]
        if df.empty:
            uh_means.append(0.0); ud_means.append(0.0); total_runs.append([0.0])
            continue
        h_vals = per_run_values(df, honest_buyer_utility)
        d_vals = per_run_values(df, dishonest_buyer_utility)
        t_vals = per_run_values(df, sum_buyer_utility)
        uh_means.append(np.mean(h_vals)); ud_means.append(np.mean(d_vals)); total_runs.append(t_vals)
    ax_util.bar(xs, uh_means, width=0.56, color=METRIC_COLORS["honest_component"],
                edgecolor="#aaaaaa", linewidth=0.5, label="Honest utility", zorder=3)
    d_bottoms = [min(dm, 0.0) for dm in ud_means]
    ax_util.bar(xs, [dm if dm >= 0 else -dm for dm in ud_means], width=0.56, bottom=d_bottoms,
                color=METRIC_COLORS["dishonest_component"], edgecolor="#aaaaaa", linewidth=0.5,
                label="Fraud-induced loss", zorder=3)
    ax_util.axhline(0, color="#888888", lw=0.8, zorder=2)
    ax_util.set_ylabel("Buyer Utility per Run", fontsize=10)
    ax_util.set_xticks(xs)
    ax_util.set_xticklabels(CONDITIONS_ORDER, fontsize=8.5, rotation=15, ha="right")
    for tick in ax_util.get_xticklabels():
        tick.set_color(COLORS["neutral_dark"])
    y_lo = min(0.0, min(ud_means) * 1.25) if ud_means else 0.0
    y_hi = max(uh_means) * 1.55 + 10 if uh_means else 10
    ax_util.set_ylim(y_lo, y_hi)
    for (la, lb) in [("Rep", "Rep+Warrant"), ("Rep, Comm", "Rep+Warrant, Comm")]:
        ia = CONDITIONS_ORDER.index(la)
        ib = CONDITIONS_ORDER.index(lb)
        p = mannwhitney_p(total_runs[ia], total_runs[ib])
        y_top = max(uh_means) * (1.08 + 0.14 * (0 if ia == 0 else 1)) if uh_means else 10
        add_significance_bracket(ax_util, xs[ia], xs[ib], y_top, p, h_frac=0.06, fontsize=9)

    fig.subplots_adjust(bottom=0.14)
    save_figure(fig, output_dir / "rq2_All_constraints_combined.png")
    print("  [RQ2-All] Aggregated 2x2 summary figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate RQ2 figures for paper")
    parser.add_argument("--base-dir",
                        default="experiments/gpt-4o-mini/paper/rq2")
    parser.add_argument("--output-dir",
                        default="visualization/figs/paper/rq2")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("RQ2: Generating Paper Figures")
    print("=" * 60)

    print("\n[Fig4] Deception by Constraint…")
    fig4_deception_by_constraint(args.base_dir, output_dir)

    print("\n[Fig5] Profit Decomposition…")
    fig5_profit_decomposition(args.base_dir, output_dir)

    print("\n[Fig6] Product Mix (appendix)…")
    fig6_product_mix(args.base_dir, output_dir)

    print("\n[Fig7] Buyer Utility by Constraint…")
    fig7_buyer_utility_by_constraint(args.base_dir, output_dir)

    print("\n[RQ2-All] Aggregated Summary Across Constraints…")
    fig_all_constraints_summary(args.base_dir, output_dir)

    print("\n✅  RQ2 figures saved to:", output_dir)


if __name__ == "__main__":
    main()
