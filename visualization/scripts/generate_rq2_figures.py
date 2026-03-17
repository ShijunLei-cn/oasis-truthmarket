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
    Headline : "Product Mix Shifts: Warrant Removes Counterfeit Supply"
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
    setup_style,
    load_results_df,
    per_run_values,
    count_deceptions,
    honest_profit,
    dishonest_profit,
    product_quality_counts,
    mannwhitney_p,
    proportion_ztest_p,
    sig_marker_display,
    add_significance_bracket,
    add_sig_footnote,
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

# Blue x-tick labels for warrant conditions (visual cue only)
COND_XCOLORS = {
    "Rep":                "#444444",
    "Rep, Comm":          "#444444",
    "Rep+Warrant":        "#1565c0",
    "Rep+Warrant, Comm":  "#1565c0",
}


def _load_cond(base_dir: str, constraint_key: str, cond: str) -> pd.DataFrame:
    prefix = DIR_PREFIXES[cond]
    return load_results_df(str(Path(base_dir) / f"{prefix}_{constraint_key}"))


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 : Deceptions per condition × constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig4_deception_by_constraint(base_dir: str, output_dir: Path) -> None:
    n_rows = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        n_rows, 1, figsize=(7.5, 3.5 * n_rows),
        gridspec_kw={"hspace": 0.48},
    )
    fig.suptitle(
        "Under Pressure, Seller Chat Amplifies Deception\n"
        "— Warrant Provides Robust Defense",
        fontsize=11, fontweight="bold",
    )
    fig.subplots_adjust(top=0.90)   # tighten gap between suptitle and first panel

    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52

    for row_idx, (c_key, c_label) in enumerate(CONSTRAINTS):
        ax = axes[row_idx]
        ax.set_title(c_label, fontsize=10, loc="left", fontweight="bold", pad=3)

        means, stds, per_runs = [], [], []
        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            vals = per_run_values(df, count_deceptions) if not df.empty else [0.0]
            means.append(np.mean(vals))
            stds.append(np.std(vals, ddof=1) if len(vals) > 1 else 0.0)
            per_runs.append(vals)

        # Red intensity encodes deception magnitude
        global_max = max(means) if max(means) > 0 else 1.0
        bar_colors = []
        for m in means:
            t = 0.28 + 0.65 * (m / global_max)
            bar_colors.append((min(1.0, 0.72 + t * 0.20), 0.08 + (1 - t) * 0.20,
                                0.08 + (1 - t) * 0.18))

        ax.bar(xs, means, width=w, color=bar_colors,
               edgecolor="white", linewidth=0.4,
               yerr=stds, capsize=3,
               error_kw={"elinewidth": 1.0, "ecolor": "#333"},
               zorder=3)

        # y-limit: based on tallest bar-top (mean+std), with room for brackets
        max_bar_top = max(m + s for m, s in zip(means, stds)) if means else 1.0
        ylim = max_bar_top * 1.55 + 2

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=9)
        ax.set_ylabel("Deceptions", fontsize=9)
        ax.set_ylim(0, ylim)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])

        # Compact numeric labels above each bar (mean value)
        for xi, (m, s) in enumerate(zip(means, stds)):
            if m > 0:
                ax.text(xs[xi], m + s + max_bar_top * 0.03,
                        f"{m:.1f}",
                        ha="center", va="bottom", fontsize=7.5,
                        color=COLORS["bad_dark"] if xi < 2 else "#1a7a3a")

        # Significance brackets: Rep vs Rep+Warrant, Rep+Comm vs RW+Comm
        for (ci, cj) in [(0, 2), (1, 3)]:
            p = mannwhitney_p(per_runs[ci], per_runs[cj])
            y_top = max(means[ci] + stds[ci], means[cj] + stds[cj])
            add_significance_bracket(ax, xs[ci], xs[cj], y_top, p,
                                     h_frac=0.08, fontsize=9)

    add_sig_footnote(fig)
    save_figure(fig, output_dir / "rq2_seller_comm_deception_by_constraint.png")
    print("  [Fig4] Deception facet figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 : Profit decomposition (honest / dishonest stacked)
# ─────────────────────────────────────────────────────────────────────────────

def fig5_profit_decomposition(base_dir: str, output_dir: Path) -> None:
    n_rows = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        n_rows, 1, figsize=(7.5, 3.5 * n_rows),
        gridspec_kw={"hspace": 0.48},
    )
    fig.suptitle(
        "Warrant Ensures Profit Comes from Honest Trade, Not Deception",
        fontsize=11, fontweight="bold",
    )
    fig.subplots_adjust(top=0.93)

    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52

    for row_idx, (c_key, c_label) in enumerate(CONSTRAINTS):
        ax = axes[row_idx]
        ax.set_title(c_label, fontsize=10, loc="left", fontweight="bold", pad=3)

        h_means, h_stds = [], []
        d_means, d_stds = [], []

        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            if df.empty:
                h_means.append(0); h_stds.append(0)
                d_means.append(0); d_stds.append(0)
                continue
            h_vals = per_run_values(df, honest_profit)
            d_vals = per_run_values(df, dishonest_profit)
            h_means.append(np.mean(h_vals))
            h_stds.append(np.std(h_vals, ddof=1) if len(h_vals) > 1 else 0.0)
            d_means.append(np.mean(d_vals))
            d_stds.append(np.std(d_vals, ddof=1) if len(d_vals) > 1 else 0.0)

        # Stacked bars
        ax.bar(xs, h_means, width=w, color=COLORS["good_light"],
               edgecolor="white", linewidth=0.4, label="Honest profit", zorder=3)
        ax.bar(xs, d_means, width=w, bottom=h_means, color=COLORS["bad_light"],
               edgecolor="white", linewidth=0.4, label="Dishonest profit", zorder=3)

        # Percentage labels inside bars
        for xi in range(len(CONDITIONS_ORDER)):
            total = h_means[xi] + d_means[xi]
            if total <= 0:
                continue
            # Honest label (inside green segment)
            hp = h_means[xi] / total * 100
            if h_means[xi] > 80:
                ax.text(xs[xi], h_means[xi] / 2,
                        f"{hp:.0f}%\nhonest",
                        ha="center", va="center", fontsize=7.5,
                        color="#1a5e20", fontweight="bold")
            # Dishonest label (inside red segment, only if visible)
            dp = d_means[xi] / total * 100
            if d_means[xi] > 30:
                ax.text(xs[xi], h_means[xi] + d_means[xi] / 2,
                        f"{dp:.0f}%\nfraud",
                        ha="center", va="center", fontsize=7.5,
                        color=COLORS["bad_dark"], fontweight="bold")
            elif d_means[xi] > 0:
                # Too thin to fit inside — show as compact label above bar
                ax.text(xs[xi], total + total * 0.02,
                        f"{dp:.0f}% fraud",
                        ha="center", va="bottom", fontsize=7,
                        color=COLORS["bad_dark"])

        # Significance: Rep honest% vs Rep+Warrant honest% (z-score on honest fraction)
        for (la, lb) in [("Rep", "Rep+Warrant"), ("Rep, Comm", "Rep+Warrant, Comm")]:
            ia = CONDITIONS_ORDER.index(la)
            ib = CONDITIONS_ORDER.index(lb)
            df_a = _load_cond(base_dir, c_key, la)
            df_b = _load_cond(base_dir, c_key, lb)
            if df_a.empty or df_b.empty:
                continue
            ha_tot   = float(df_a["seller_profit"].sum())
            ha_hon   = float(df_a[df_a["is_honest"] == True]["seller_profit"].sum())  # noqa
            hb_tot   = float(df_b["seller_profit"].sum())
            hb_hon   = float(df_b[df_b["is_honest"] == True]["seller_profit"].sum())  # noqa
            if ha_tot == 0 or hb_tot == 0:
                continue
            p = proportion_ztest_p(ha_hon, ha_tot, hb_hon, hb_tot)
            y_top = max(h_means[ia] + d_means[ia], h_means[ib] + d_means[ib])
            add_significance_bracket(ax, xs[ia], xs[ib], y_top, p,
                                     h_frac=0.08, fontsize=9)

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=9)
        ax.set_ylabel("Seller Profit", fontsize=9)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])
        ymax = max(h + d for h, d in zip(h_means, d_means))
        ax.set_ylim(0, ymax * 1.30 + 10)

        if row_idx == 0:
            ax.legend(frameon=False, fontsize=8, loc="upper right")

    add_sig_footnote(fig, extra="z-score proportion test for honest-profit share")
    save_figure(fig, output_dir / "rq2_profit_decomposition_honest_vs_dishonest.png")
    print("  [Fig5] Profit decomposition figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6 (appendix) : Product mix per constraint
# ─────────────────────────────────────────────────────────────────────────────

def fig6_product_mix(base_dir: str, output_dir: Path) -> None:
    n_rows = len(CONSTRAINTS)
    fig, axes = plt.subplots(
        n_rows, 1, figsize=(7.5, 3.5 * n_rows),
        gridspec_kw={"hspace": 0.48},
    )
    fig.suptitle(
        "Product Mix Shifts: Warrant Removes Counterfeit Supply",
        fontsize=11, fontweight="bold",
    )
    fig.subplots_adjust(top=0.93)

    xs = np.arange(len(CONDITIONS_ORDER))
    w = 0.52
    seg_colors = [COLORS["hq_auth"], COLORS["lq_auth"], COLORS["counterfeit"]]
    seg_labels = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit (fraud)"]

    for row_idx, (c_key, c_label) in enumerate(CONSTRAINTS):
        ax = axes[row_idx]
        ax.set_title(c_label, fontsize=10, loc="left", fontweight="bold", pad=3)

        segs: List[List[float]] = [[], [], []]
        for cond in CONDITIONS_ORDER:
            df = _load_cond(base_dir, c_key, cond)
            if df.empty:
                for si in range(3):
                    segs[si].append(0.0)
                continue
            pq_runs = per_run_values(df, product_quality_counts)
            means_t = [np.mean([t[i] for t in pq_runs]) for i in range(3)]
            total = sum(means_t)
            for si in range(3):
                segs[si].append(means_t[si] / total * 100 if total > 0 else 0.0)

        bottoms = [0.0] * len(CONDITIONS_ORDER)
        for si in range(3):
            lbl = seg_labels[si] if row_idx == 0 else "_"
            ax.bar(xs, segs[si], width=w, bottom=bottoms,
                   color=seg_colors[si], label=lbl,
                   edgecolor="white", linewidth=0.4, zorder=3)
            for xi, (h, b) in enumerate(zip(segs[si], bottoms)):
                if h > 5.0:
                    ax.text(xs[xi], b + h / 2, f"{h:.0f}%",
                            ha="center", va="center", fontsize=7.5,
                            color="white", fontweight="bold")
            bottoms = [bottoms[xi] + segs[si][xi] for xi in range(len(xs))]

        ax.set_xticks(xs)
        ax.set_xticklabels(CONDITIONS_ORDER, fontsize=9)
        ax.set_ylabel("% of Sold Products", fontsize=9)
        ax.set_ylim(0, 110)
        for tick, cond in zip(ax.get_xticklabels(), CONDITIONS_ORDER):
            tick.set_color(COND_XCOLORS[cond])

    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    save_figure(fig, output_dir / "rq2_product_mix_appendix.png")
    print("  [Fig6] Product mix appendix figure saved.")


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

    print("\n✅  RQ2 figures saved to:", output_dir)


if __name__ == "__main__":
    main()
