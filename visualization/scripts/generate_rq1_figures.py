#!/usr/bin/env python3
"""
RQ1 Figures — Warrant vs. Reputation-Only Mechanism

Figure 1 : rq1_warrant_vs_rep_deception_and_profit.png
    Headline : "Warrant Eliminates Deception; Honest Trade Rises by 55%"
    Two side-by-side bars: seller profit (green) and deceptions (red).

Figure 2 : rq1_exit_loophole_vulnerability.png
    Headline : "Sellers Exploit the 'Exit Loophole' 4x More Without Warrant"
    Grouped bar chart of manipulation detection rate per vulnerability type.

Figure 3 (appendix) : rq1_product_mix_appendix.png
    Headline : "Warrant Shifts Market Output to Authentic HQ — Counterfeit Disappears"
    100% stacked bar showing product-quality composition of sold items.

Usage
-----
    python generate_rq1_figures.py \
        --r-dir  experiments/gpt-4o-mini/paper/rq1/r_wo \
        --rw-dir experiments/gpt-4o-mini/paper/rq1/rw_wo \
        --output-dir visualization/figs/paper/rq1
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    COLORS,
    METRIC_COLORS,
    setup_style,
    label_panel,
    load_results_df,
    load_probes_df,
    per_run_values,
    count_deceptions,
    sum_seller_profit,
    sum_buyer_utility,
    product_quality_counts,
    product_quality_counts_all,
    mannwhitney_p,
    proportion_ztest_p,
    sig_marker_display,
    add_significance_bracket,
    add_text_box,
    highlight_bar_group,
    save_figure,
)

setup_style()

# ── Condition labels ──────────────────────────────────────────────────────────
LABEL_R  = "Rep"
LABEL_RW = "Rep+Warrant"


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 : Seller Profit & Deceptions — main result
# ─────────────────────────────────────────────────────────────────────────────

def _kde_panel(
    ax: plt.Axes,
    vals_a: list, vals_b: list,
    label_a: str, label_b: str,
    color_a: str, color_b: str,
    xlabel: str, title: str,
    p_val: float,
    annotation: str = "",
) -> None:
    """Overlapping KDE distribution panel for two conditions.

    Shows: filled KDE curve, dashed mean line + μ label, rug of individual points.
    Handles degenerate case (std ≈ 0) by adding tiny noise for KDE only.
    """
    rng = np.random.default_rng(42)
    arr_a = np.array(vals_a, dtype=float)
    arr_b = np.array(vals_b, dtype=float)

    all_vals = np.concatenate([arr_a, arr_b])
    span = max(all_vals.max() - all_vals.min(), 1.0)
    x_lo = all_vals.min() - span * 0.35
    x_hi = all_vals.max() + span * 0.35
    xs = np.linspace(x_lo, x_hi, 500)

    y_peaks = []
    for arr, color, label in [
        (arr_a, color_a, label_a),
        (arr_b, color_b, label_b),
    ]:
        kde_arr = arr.copy()
        if len(kde_arr) == 1:
            # single element — duplicate it so KDE has at least 2 points
            kde_arr = np.append(kde_arr, kde_arr[0] + rng.normal(0, max(span * 0.01, 0.1), 1))
        elif np.std(kde_arr) < 0.1:
            # degenerate (all zeros) — add tiny noise so KDE is a narrow spike
            kde_arr = kde_arr + rng.normal(0, max(span * 0.02, 0.3), len(kde_arr))
        kde = gaussian_kde(kde_arr, bw_method=0.7)
        ys = kde(xs)
        y_peaks.append(float(ys.max()))
        ax.fill_between(xs, ys, alpha=0.14, color=color)
        ax.plot(xs, ys, color=color, lw=1.6, label=label, zorder=3)

    y_max = max(y_peaks) if y_peaks else 1.0

    # Mean dashed vertical lines + μ labels
    for arr, color in [(arr_a, color_a), (arr_b, color_b)]:
        m = float(np.mean(arr))
        ax.axvline(m, color=color, lw=1.2, ls="--", alpha=0.85, zorder=4)
        ax.text(m, y_max * 1.07, f"μ={m:.1f}",
                ha="center", va="bottom", fontsize=8,
                color=color, fontweight="bold")

    # Rug: individual per-run values along x-axis
    rug_y = -y_max * 0.055
    for arr, color in [(arr_a, color_a), (arr_b, color_b)]:
        ax.scatter(arr, np.full(len(arr), rug_y),
                   color=color, s=30, marker="|",
                   linewidths=1.5, alpha=0.9, zorder=5, clip_on=False)

    # Significance marker (top-right corner)
    marker = sig_marker_display(p_val)
    if marker:
        ax.text(0.97, 0.96, marker,
                transform=ax.transAxes, ha="right", va="top",
                fontsize=10, color="black", fontweight="bold")

    # Optional annotation box
    if annotation:
        ax.text(0.97, 0.80, annotation,
                transform=ax.transAxes, ha="right", va="top",
                fontsize=7, color=COLORS["good_dark"],
                bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["neutral_light"],
                          edgecolor=COLORS["good_dark"], alpha=0.9, linewidth=0.8))

    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.set_ylim(rug_y * 2.2, y_max * 1.32)
    ax.set_xlim(x_lo, x_hi)
    ax.legend(frameon=False, fontsize=8, loc="upper left")


def fig1_profit_and_deceptions(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """Two-panel KDE distribution figure: seller profit (left) and deceptions (right)."""

    df_r  = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[Fig1] Missing data, skipping.")
        return

    profit_r  = per_run_values(df_r,  sum_seller_profit)
    profit_rw = per_run_values(df_rw, sum_seller_profit)
    dec_r     = per_run_values(df_r,  count_deceptions)
    dec_rw    = per_run_values(df_rw, count_deceptions)
    util_r    = per_run_values(df_r,  sum_buyer_utility)
    util_rw   = per_run_values(df_rw, sum_buyer_utility)

    p_profit  = mannwhitney_p(profit_r, profit_rw)
    p_dec     = mannwhitney_p(dec_r,    dec_rw)
    p_utility = mannwhitney_p(util_r,   util_rw)

    mean_p_r  = float(np.mean(profit_r))
    mean_p_rw = float(np.mean(profit_rw))
    lift_pct  = (mean_p_rw - mean_p_r) / mean_p_r * 100 if mean_p_r > 0 else 0
    mean_d_rw = float(np.mean(dec_rw))

    mean_u_r  = float(np.mean(util_r))
    mean_u_rw = float(np.mean(util_rw))
    util_lift = (mean_u_rw - mean_u_r) / abs(mean_u_r) * 100 if mean_u_r != 0 else 0

    fig, (ax_p, ax_d, ax_u) = plt.subplots(1, 3, figsize=(11.0, 3.8),
                                             gridspec_kw={"wspace": 0.42})
    _kde_panel(
        ax_p,
        profit_r, profit_rw,
        LABEL_R, LABEL_RW,
        METRIC_COLORS["seller_profit_secondary"], METRIC_COLORS["seller_profit_primary"],
        xlabel="Total Seller Profit (per run)",
        title="(a) Seller Profit",
        p_val=p_profit,
        annotation=f"+{lift_pct:.0f}% mean profit",
    )

    dec_annot = "0 deceptions\nin all 5 runs" if mean_d_rw == 0 else ""
    _kde_panel(
        ax_d,
        dec_r, dec_rw,
        LABEL_R, LABEL_RW,
        METRIC_COLORS["deception_primary"], METRIC_COLORS["deception_secondary"],
        xlabel="Deceptive Transactions (per run)",
        title="(b) Deceptions",
        p_val=p_dec,
        annotation=dec_annot,
    )

    util_sign = "+" if util_lift >= 0 else ""
    _kde_panel(
        ax_u,
        util_r, util_rw,
        LABEL_R, LABEL_RW,
        METRIC_COLORS["buyer_utility_secondary"], METRIC_COLORS["buyer_utility_primary"],
        xlabel="Total Buyer Utility (per run)",
        title="(c) Buyer Utility",
        p_val=p_utility,
        annotation=f"{util_sign}{util_lift:.0f}% mean utility",
    )

    save_figure(fig, output_dir / "rq1_warrant_vs_rep_deception_and_profit.png")
    print(f"  [Fig1] p_profit={p_profit:.4f}, p_dec={p_dec:.4f}, p_utility={p_utility:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 : Vulnerability Probe Detection Rates
# ─────────────────────────────────────────────────────────────────────────────

VULN_KEYS = ["initial_window", "reputation_lag", "value_imbalance",
             "reentry", "exit_strategy"]
VULN_LABELS = ["Initial\nWindow", "Reputation\nLag", "Value\nImbalance",
               "Reentry", "Exit\nStrategy"]
VULN_SHORT = ["IW", "RL", "VI", "RE", "ES"]


def _probe_rates_per_run(probe_df: pd.DataFrame):
    """Return list-of-dicts: each dict has vuln_type -> detection_rate (0-1)."""
    rates_by_run = []
    for rid in sorted(probe_df["run_id"].unique()):
        rdf = probe_df[probe_df["run_id"] == rid]
        rd = {}
        for vk in VULN_KEYS:
            sub = rdf[rdf["vulnerability_type"] == vk]
            rd[vk] = sub["manipulation_detected"].mean() if len(sub) > 0 else 0.0
        rates_by_run.append(rd)
    return rates_by_run


def _compute_probe_panel_stats(probe_r: pd.DataFrame, probe_rw: pd.DataFrame):
    rates_r = _probe_rates_per_run(probe_r)
    rates_rw = _probe_rates_per_run(probe_rw)
    means_r, stds_r, means_rw, stds_rw, p_vals = [], [], [], [], []
    for vk in VULN_KEYS:
        vals_r = [d[vk] * 100 for d in rates_r]
        vals_rw = [d[vk] * 100 for d in rates_rw]
        means_r.append(np.mean(vals_r))
        stds_r.append(np.std(vals_r, ddof=1))
        means_rw.append(np.mean(vals_rw))
        stds_rw.append(np.std(vals_rw, ddof=1))
        n_r_vk = len(probe_r[probe_r["vulnerability_type"] == vk])
        n_rw_vk = len(probe_rw[probe_rw["vulnerability_type"] == vk])
        cnt_r = probe_r[probe_r["vulnerability_type"] == vk]["manipulation_detected"].sum()
        cnt_rw = probe_rw[probe_rw["vulnerability_type"] == vk]["manipulation_detected"].sum()
        p_vals.append(
            proportion_ztest_p(float(cnt_r), float(n_r_vk), float(cnt_rw), float(n_rw_vk))
        )
    return means_r, stds_r, means_rw, stds_rw, p_vals


def _compute_probe_single_stats(probe_df: pd.DataFrame):
    """Single-condition probe stats (mean/std over runs, in %)."""
    rates = _probe_rates_per_run(probe_df)
    means, stds = [], []
    for vk in VULN_KEYS:
        vals = [d[vk] * 100 for d in rates]
        means.append(float(np.mean(vals)) if vals else 0.0)
        stds.append(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)
    return means, stds


def _draw_probe_panel(
    ax: plt.Axes,
    means_r: list,
    stds_r: list,
    means_rw: list,
    stds_rw: list,
    p_vals: list,
    show_ylabel: bool = True,
    show_legend: bool = True,
) -> None:
    n_groups = len(VULN_KEYS)
    x = np.arange(n_groups)
    w = 0.32

    ax.bar(x - w / 2, means_r, width=w, color=COLORS["bad_dark"],
           label=LABEL_R, edgecolor="white", linewidth=0.5,
           yerr=stds_r, capsize=3,
           error_kw={"elinewidth": 1.0, "ecolor": "#555555"}, zorder=3)
    ax.bar(x + w / 2, means_rw, width=w, color=COLORS["bad_mid"],
           label=LABEL_RW, edgecolor="white", linewidth=0.5,
           yerr=stds_rw, capsize=3,
           error_kw={"elinewidth": 1.0, "ecolor": "#555555"}, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(VULN_LABELS, fontsize=9)
    if show_ylabel:
        ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=10)

    bracket_tops = []
    for i, p in enumerate(p_vals):
        y_top = max(means_r[i] + stds_r[i], means_rw[i] + stds_rw[i])
        bracket_tops.append(y_top)
        add_significance_bracket(ax, x[i] - w / 2, x[i] + w / 2,
                                 y_top, p, h_frac=0.07, fontsize=9)

    global_top = max(bracket_tops) if bracket_tops else max(means_r + means_rw)
    ax.set_ylim(0, global_top * 1.52)

    es_idx = VULN_KEYS.index("exit_strategy")
    es_y = bracket_tops[es_idx] * 1.24
    add_text_box(ax, x[es_idx], es_y, "Primary\nvulnerability",
                 fontsize=8, color=COLORS["bad_dark"], boxcolor=COLORS["neutral_light"])
    ax.text(x[es_idx] - w / 2, means_r[es_idx] + stds_r[es_idx] + 1.0,
            f"{means_r[es_idx]:.1f}%", ha="center", va="bottom",
            fontsize=7, color=COLORS["bad_dark"])
    ax.text(x[es_idx] + w / 2, means_rw[es_idx] + stds_rw[es_idx] + 1.0,
            f"{means_rw[es_idx]:.1f}%", ha="center", va="bottom",
            fontsize=7, color=COLORS["bad_mid"])
    if show_legend:
        ax.legend(frameon=False, fontsize=8, loc="upper left")


def fig1_2_manipulation_detection_rep_only(r_dir: str, output_dir: Path) -> None:
    """Standalone manipulation detection figure for reputation-only market."""
    probe_r = load_probes_df(r_dir)
    if probe_r.empty:
        print("[Fig1-2] No probe data found for reputation-only, skipping.")
        return

    means_r, stds_r = _compute_probe_single_stats(probe_r)
    x = np.arange(len(VULN_KEYS))
    w = 0.52

    fig, ax = plt.subplots(1, 1, figsize=(7.0, 4.1))
    ax.bar(
        x, means_r, width=w, color=COLORS["bad_dark"],
        edgecolor="white", linewidth=0.5,
        yerr=stds_r, capsize=3,
        error_kw={"elinewidth": 1.0, "ecolor": "#555555"},
        zorder=3
    )

    ax.set_xticks(x)
    ax.set_xticklabels(VULN_LABELS, fontsize=9)
    ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=10)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)

    y_tops = [m + s for m, s in zip(means_r, stds_r)]
    ylim_top = max(y_tops) * 1.35 if y_tops else 100.0
    ax.set_ylim(0, max(100.0, ylim_top))

    for i, (m, s) in enumerate(zip(means_r, stds_r)):
        ax.text(x[i], m + s + 1.0, f"{m:.1f}%", ha="center", va="bottom",
                fontsize=8, color=COLORS["bad_dark"])

    save_figure(fig, output_dir / "rq1_2_rep_only_manipulation_detection.png")
    print("  [Fig1-2] Rep-only manipulation-detection figure saved.")


def fig1_1_manipulation_detection(r_dir: str, rw_dir: str, output_dir: Path) -> None:
    probe_r = load_probes_df(r_dir)
    probe_rw = load_probes_df(rw_dir)
    if probe_r.empty or probe_rw.empty:
        print("[Fig1-1] No probe data found, skipping.")
        return

    means_r, stds_r, means_rw, stds_rw, p_vals = _compute_probe_panel_stats(probe_r, probe_rw)
    fig, ax = plt.subplots(1, 1, figsize=(7.2, 4.2))
    _draw_probe_panel(ax, means_r, stds_r, means_rw, stds_rw, p_vals,
                      show_ylabel=True, show_legend=True)
    fig.subplots_adjust(bottom=0.20)
    save_figure(fig, output_dir / "rq1_1_manipulation_detection.png")
    print("  [Fig1-1] Manipulation-detection standalone figure saved.")


def fig2_probe_and_product_mix(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """1×3 combined figure: probe, listed mix, and sold-out quality-combo counts."""

    # ── Load data ──────────────────────────────────────────────────────────
    probe_r  = load_probes_df(r_dir)
    probe_rw = load_probes_df(rw_dir)
    df_r     = load_results_df(r_dir)
    df_rw    = load_results_df(rw_dir)

    if probe_r.empty or probe_rw.empty:
        print("[Fig2] No probe data found, skipping.")
        return
    if df_r.empty or df_rw.empty:
        print("[Fig2] Missing results data, skipping.")
        return

    # ── Probe stats ────────────────────────────────────────────────────────
    means_r, stds_r, means_rw, stds_rw, p_vals = _compute_probe_panel_stats(probe_r, probe_rw)

    # ── Product-mix stats (ALL listed products, including unsold) ──────────────────
    pq_r  = per_run_values(df_r,  product_quality_counts_all)
    pq_rw = per_run_values(df_rw, product_quality_counts_all)

    def _pmeans(pq, idx):
        vals = [t[idx] for t in pq]
        return np.mean(vals), np.std(vals, ddof=1)

    hqa_r,  _ = _pmeans(pq_r,  0)
    lqa_r,  _ = _pmeans(pq_r,  1)
    hqcf_r, _ = _pmeans(pq_r,  2)
    hqa_rw, _ = _pmeans(pq_rw, 0)
    lqa_rw, _ = _pmeans(pq_rw, 1)
    hqcf_rw,_ = _pmeans(pq_rw, 2)

    def pct(v, t): return (v / t * 100) if t > 0 else 0.0
    total_r  = hqa_r  + lqa_r  + hqcf_r
    total_rw = hqa_rw + lqa_rw + hqcf_rw
    mix = {
        LABEL_R:  [pct(hqa_r,  total_r),  pct(lqa_r,  total_r),  pct(hqcf_r,  total_r)],
        LABEL_RW: [pct(hqa_rw, total_rw), pct(lqa_rw, total_rw), pct(hqcf_rw, total_rw)],
    }
    cnt_cf_r   = sum(t[2] for t in pq_r)
    cnt_tot_r  = sum(sum(t) for t in pq_r)
    cnt_cf_rw  = sum(t[2] for t in pq_rw)
    cnt_tot_rw = sum(sum(t) for t in pq_rw)
    p_counterfeit = proportion_ztest_p(cnt_cf_r, cnt_tot_r, cnt_cf_rw, cnt_tot_rw)
    cnt_hqa_r  = sum(t[0] for t in pq_r)
    cnt_hqa_rw = sum(t[0] for t in pq_rw)
    p_hq_auth  = proportion_ztest_p(cnt_hqa_r, cnt_tot_r, cnt_hqa_rw, cnt_tot_rw)

    # ── Sold-product quality-combo counts (mean per run) ──────────────────
    pq_sold_r = per_run_values(df_r, product_quality_counts)
    pq_sold_rw = per_run_values(df_rw, product_quality_counts)

    def _means3(pq):
        if not pq:
            return [0.0, 0.0, 0.0]
        return [float(np.mean([t[i] for t in pq])) for i in range(3)]

    sold_counts = {
        LABEL_R: _means3(pq_sold_r),
        LABEL_RW: _means3(pq_sold_rw),
    }

    # ── Layout ─────────────────────────────────────────────────────────────
    fig, (ax_probe, ax_mix, ax_sold) = plt.subplots(
        1, 3, figsize=(14.0, 4.1),
        gridspec_kw={"wspace": 0.34, "width_ratios": [2.1, 1.0, 1.0]},
    )
    # ── (a) Vulnerability probe ────────────────────────────────────────────
    _draw_probe_panel(ax_probe, means_r, stds_r, means_rw, stds_rw, p_vals,
                      show_ylabel=True, show_legend=True)

    # ── (b) Product mix stacked bar (ALL listed products) ───────────────────────
    xm = np.array([0.0, 1.0])
    wm = 0.45
    seg_colors = [COLORS["hq_auth"], COLORS["lq_auth"], COLORS["counterfeit"]]
    seg_labels  = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit"]

    bottoms = [0.0, 0.0]
    for si, (col, lab) in enumerate(zip(seg_colors, seg_labels)):
        heights = [mix[LABEL_R][si], mix[LABEL_RW][si]]
        ax_mix.bar(xm, heights, width=wm, bottom=bottoms,
                   color=col, label=lab, edgecolor="white",
                   linewidth=0.5, zorder=3)
        for xi, (h, bot) in enumerate(zip(heights, bottoms)):
            if h > 8.0:   # only label if segment is wide enough
                ax_mix.text(xm[xi], bot + h / 2, f"{h:.1f}%",
                            ha="center", va="center", fontsize=8,
                            color="white", fontweight="bold")
        bottoms = [bottoms[j] + heights[j] for j in range(2)]

    ax_mix.set_xticks(xm)
    ax_mix.set_xticklabels([LABEL_R, LABEL_RW], fontsize=10)
    ax_mix.set_ylabel("Share of Listed Products (%)", fontsize=10)
    ax_mix.set_ylim(0, 112)

    # ── (c) Sold-out product quality combos (absolute counts) ────────────
    bottoms = [0.0, 0.0]
    for si, col in enumerate(seg_colors):
        heights = [sold_counts[LABEL_R][si], sold_counts[LABEL_RW][si]]
        ax_sold.bar(xm, heights, width=wm, bottom=bottoms,
                    color=col, edgecolor="white", linewidth=0.5, zorder=3)
        for xi, (h, bot) in enumerate(zip(heights, bottoms)):
            if h > 0.35:
                ax_sold.text(xm[xi], bot + h / 2, f"{h:.1f}",
                             ha="center", va="center", fontsize=8,
                             color="white", fontweight="bold")
        bottoms = [bottoms[j] + heights[j] for j in range(2)]
    sold_ymax = max(bottoms) if bottoms else 0.0
    ax_sold.set_xticks(xm)
    ax_sold.set_xticklabels([LABEL_R, LABEL_RW], fontsize=10)
    ax_sold.set_ylabel("Mean Sold Products per Run", fontsize=10)
    ax_sold.set_ylim(0, max(1.0, sold_ymax * 1.18))

    # Shared legend for both product-mix subplots
    handles = [mpatches.Patch(facecolor=c, edgecolor="white", label=l)
               for c, l in zip(seg_colors, seg_labels)]
    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(0.5, 0.03), ncol=3,
               frameon=False, fontsize=8)

    fig.subplots_adjust(bottom=0.20)
    save_figure(fig, output_dir / "rq1_exit_loophole_vulnerability.png")
    print(f"  [Fig2] p_vals per vulnerability: "
          + ", ".join(f"{VULN_SHORT[i]}={p_vals[i]:.4f}" for i in range(len(VULN_KEYS))))
    print(f"  [Fig2] p_counterfeit={p_counterfeit:.4f}, p_hq_auth={p_hq_auth:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate RQ1 figures for paper"
    )
    parser.add_argument("--r-dir",  required=True,
                        help="Reputation-Only experiment dir (rq1/r_wo)")
    parser.add_argument("--rw-dir", required=False, default=None,
                        help="Rep+Warrant experiment dir (required unless --rep-only-only)")
    parser.add_argument("--output-dir", default="visualization/figs/paper/rq1",
                        help="Output directory for figures")
    parser.add_argument(
        "--rep-only-only",
        action="store_true",
        help="Generate only the reputation-only manipulation detection figure."
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("RQ1: Generating Paper Figures")
    print("=" * 60)

    if args.rep_only_only:
        print("\n[Fig1-2] Manipulation Detection (Rep-only standalone)…")
        fig1_2_manipulation_detection_rep_only(args.r_dir, output_dir)
        print("\n✅  Rep-only figure saved to:", output_dir)
        return

    if not args.rw_dir:
        raise ValueError("--rw-dir is required unless --rep-only-only is set.")

    print("\n[Fig1] Seller Profit & Deceptions…")
    fig1_profit_and_deceptions(args.r_dir, args.rw_dir, output_dir)

    print("\n[Fig1-1] Manipulation Detection (standalone)…")
    fig1_1_manipulation_detection(args.r_dir, args.rw_dir, output_dir)

    print("\n[Fig1-2] Manipulation Detection (Rep-only standalone)…")
    fig1_2_manipulation_detection_rep_only(args.r_dir, output_dir)

    print("\n[Fig2] Vulnerability Probe + Product Mix (combined)…")
    fig2_probe_and_product_mix(args.r_dir, args.rw_dir, output_dir)

    print("\n✅  RQ1 figures saved to:", output_dir)


if __name__ == "__main__":
    main()
