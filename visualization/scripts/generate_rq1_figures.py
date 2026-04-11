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
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from wordcloud import WordCloud

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
REP_COLOR = COLORS["neutral_dark"]
RW_COLOR = COLORS["good_dark"]


def _set_dynamic_ylim_positive(
    ax: plt.Axes,
    tops: list[float],
    pad_ratio: float = 0.20,
    min_top: float = 1.0,
) -> None:
    """Adaptive positive y-limits for bar charts."""
    ymax = max([float(v) for v in tops] + [min_top])
    ax.set_ylim(0, ymax * (1.0 + pad_ratio))


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
    show_significance: bool = True,
    show_legend: bool = False,
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
    if show_significance:
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
    if show_legend:
        ax.legend(frameon=False, fontsize=8, loc="upper left")


def fig1_profit_and_deceptions(
    r_dir: str, rw_dir: str, output_dir: Path, show_significance: bool = True
) -> None:
    """Four-panel KDE distribution figure for RQ2 welfare core metrics."""

    df_r  = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[Fig1] Missing data, skipping.")
        return

    profit_r  = per_run_values(df_r,  sum_seller_profit)
    profit_rw = per_run_values(df_rw, sum_seller_profit)
    def _hq_products_count(run_df: pd.DataFrame) -> float:
        hq_auth, _lq_auth, hq_fake = product_quality_counts(run_df)
        return float(hq_auth + hq_fake)

    def _transaction_count(run_df: pd.DataFrame) -> float:
        return float(len(run_df))

    hq_r      = per_run_values(df_r,  _hq_products_count)
    hq_rw     = per_run_values(df_rw, _hq_products_count)
    tx_r      = per_run_values(df_r,  _transaction_count)
    tx_rw     = per_run_values(df_rw, _transaction_count)
    util_r    = per_run_values(df_r,  sum_buyer_utility)
    util_rw   = per_run_values(df_rw, sum_buyer_utility)

    p_profit  = mannwhitney_p(profit_r, profit_rw)
    p_hq      = mannwhitney_p(hq_r,     hq_rw)
    p_tx      = mannwhitney_p(tx_r,     tx_rw)
    p_utility = mannwhitney_p(util_r,   util_rw)

    mean_p_r  = float(np.mean(profit_r))
    mean_p_rw = float(np.mean(profit_rw))
    lift_pct  = (mean_p_rw - mean_p_r) / mean_p_r * 100 if mean_p_r > 0 else 0
    mean_hq_r = float(np.mean(hq_r))
    mean_hq_rw = float(np.mean(hq_rw))
    hq_lift = (mean_hq_rw - mean_hq_r) / mean_hq_r * 100 if mean_hq_r > 0 else 0.0

    mean_u_r  = float(np.mean(util_r))
    mean_u_rw = float(np.mean(util_rw))
    util_lift = (mean_u_rw - mean_u_r) / abs(mean_u_r) * 100 if mean_u_r != 0 else 0

    mean_tx_r = float(np.mean(tx_r))
    mean_tx_rw = float(np.mean(tx_rw))
    tx_lift = (mean_tx_rw - mean_tx_r) / mean_tx_r * 100 if mean_tx_r > 0 else 0.0

    fig, (ax_p, ax_hq, ax_u, ax_t) = plt.subplots(
        1, 4, figsize=(14.0, 3.9), gridspec_kw={"wspace": 0.38}
    )
    _kde_panel(
        ax_p,
        profit_r, profit_rw,
        LABEL_R, LABEL_RW,
        REP_COLOR, RW_COLOR,
        xlabel="Total Seller Profit (per run)",
        title="(a) Seller Profit",
        p_val=p_profit,
        annotation=f"+{lift_pct:.0f}% mean profit",
        show_significance=show_significance,
        show_legend=False,
    )

    _kde_panel(
        ax_hq,
        hq_r, hq_rw,
        LABEL_R, LABEL_RW,
        REP_COLOR, RW_COLOR,
        xlabel="HQ Products Counts (per run)",
        title="(b) HQ Products",
        p_val=p_hq,
        annotation=f"+{hq_lift:.0f}% HQ products",
        show_significance=show_significance,
        show_legend=False,
    )

    util_sign = "+" if util_lift >= 0 else ""
    _kde_panel(
        ax_u,
        util_r, util_rw,
        LABEL_R, LABEL_RW,
        REP_COLOR, RW_COLOR,
        xlabel="Total Buyer Utility (per run)",
        title="(c) Buyer Utility",
        p_val=p_utility,
        annotation=f"{util_sign}{util_lift:.0f}% mean utility",
        show_significance=show_significance,
        show_legend=False,
    )
    _kde_panel(
        ax_t,
        tx_r, tx_rw,
        LABEL_R, LABEL_RW,
        REP_COLOR, RW_COLOR,
        xlabel="Transaction Count (per run)",
        title="(d) Transactions",
        p_val=p_tx,
        annotation=f"+{tx_lift:.0f}% transactions",
        show_significance=show_significance,
        show_legend=False,
    )

    shared_handles = [
        Line2D([0], [0], color=REP_COLOR, lw=1.8, label=LABEL_R),
        Line2D([0], [0], color=RW_COLOR, lw=1.8, label=LABEL_RW),
    ]
    fig.legend(
        handles=shared_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.18)

    save_figure(fig, output_dir / "rq1_warrant_vs_rep_deception_and_profit.png")
    if show_significance:
        print(
            f"  [Fig1] p_profit={p_profit:.4f}, p_hq={p_hq:.4f}, "
            f"p_utility={p_utility:.4f}, p_tx={p_tx:.4f}"
        )
    else:
        print("  [Fig1] Welfare core distribution figure (profit/HQ/utility/tx) saved.")


def fig_rq2_product_quality_over_rounds(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """RQ2: round-wise trend for true-quality counts (HQ vs LQ; Rep vs Rep+Warrant)."""
    df_r = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[RQ2-RoundQuality] Missing data, skipping.")
        return

    def _round_stats(df: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
        dfx = df.copy()
        sold_col = "sold" if "sold" in dfx.columns else "is_sold"
        round_col = "round_num" if "round_num" in dfx.columns else "round"
        quality_col = (
            "quality" if "quality" in dfx.columns
            else ("true_quality" if "true_quality" in dfx.columns else "actual_quality")
        )
        dfx = dfx[dfx[sold_col] == True]  # noqa: E712
        dfx["quality"] = dfx[quality_col].astype(str).str.upper().str.strip()

        cats = {
            "HQ True Quality": (dfx["quality"] == "HQ"),
            "LQ True Quality": (dfx["quality"] == "LQ"),
        }
        rounds = sorted(int(r) for r in dfx[round_col].dropna().unique())
        out = {}
        for cat_name, mask in cats.items():
            cdf = dfx[mask]
            run_round = (
                cdf.groupby(["run_id", round_col]).size().rename("count").reset_index()
            )
            means, sems = [], []
            for r in rounds:
                vals = run_round.loc[run_round[round_col] == r, "count"].astype(float).tolist()
                if not vals:
                    means.append(0.0)
                    sems.append(0.0)
                else:
                    means.append(float(np.mean(vals)))
                    sems.append(float(np.std(vals, ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0)
            out[cat_name] = (np.array(rounds), np.array(means), np.array(sems))
        return out

    stats_r = _round_stats(df_r)
    stats_rw = _round_stats(df_rw)

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), gridspec_kw={"wspace": 0.28}, sharex=True)
    for ax, cat_name in zip(
        axes,
        ["HQ True Quality", "LQ True Quality"],
    ):
        xr, mr, sr = stats_r[cat_name]
        xw, mw, sw = stats_rw[cat_name]
        ax.plot(xr, mr, color=REP_COLOR, lw=1.8, label="Rep")
        ax.fill_between(xr, mr - sr, mr + sr, color=COLORS["neutral"], alpha=0.22)
        ax.plot(xw, mw, color=RW_COLOR, lw=1.8, label="Rep+Warrant")
        ax.fill_between(xw, mw - sw, mw + sw, color=RW_COLOR, alpha=0.18)
        ax.set_title(cat_name, fontsize=10)
        ax.set_xlabel("Round", fontsize=9)
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Mean Sold Count per Round", fontsize=10)
    shared_handles = [
        Line2D([0], [0], color=REP_COLOR, lw=1.8, label="Rep"),
        Line2D([0], [0], color=RW_COLOR, lw=1.8, label="Rep+Warrant"),
    ]
    fig.legend(
        handles=shared_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.18)
    save_figure(fig, output_dir / "rq2_product_quality_over_rounds.png")
    print("  [RQ2-RoundQuality] Product-quality round trend figure saved.")


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
    show_significance: bool = True,
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
        if show_significance:
            add_significance_bracket(ax, x[i] - w / 2, x[i] + w / 2,
                                     y_top, p, h_frac=0.07, fontsize=9)

    global_top = max(bracket_tops) if bracket_tops else max(means_r + means_rw)
    _set_dynamic_ylim_positive(ax, [global_top], pad_ratio=0.30, min_top=1.0)

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
    _set_dynamic_ylim_positive(ax, y_tops, pad_ratio=0.22, min_top=1.0)

    save_figure(fig, output_dir / "rq1_2_rep_only_manipulation_detection.png")
    print("  [Fig1-2] Rep-only manipulation-detection figure saved.")


def fig1_1_manipulation_detection(
    r_dir: str, rw_dir: str, output_dir: Path, show_significance: bool = True
) -> None:
    probe_r = load_probes_df(r_dir)
    probe_rw = load_probes_df(rw_dir)
    if probe_r.empty or probe_rw.empty:
        print("[Fig1-1] No probe data found, skipping.")
        return

    means_r, stds_r, means_rw, stds_rw, p_vals = _compute_probe_panel_stats(probe_r, probe_rw)
    fig, ax = plt.subplots(1, 1, figsize=(7.2, 4.2))
    _draw_probe_panel(ax, means_r, stds_r, means_rw, stds_rw, p_vals,
                      show_ylabel=True, show_legend=True,
                      show_significance=show_significance)
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
    mix_top = max(bottoms) if bottoms else 1.0
    _set_dynamic_ylim_positive(ax_mix, [mix_top], pad_ratio=0.10, min_top=1.0)

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


def fig_rq2_listed_vs_sold_quality(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """RQ2 quality figure with 3 panels by category.

    Panels: HQ Authentic / LQ Authentic / HQ Counterfeit.
    Within each panel: Listed vs Sold on x-axis, with Rep vs Rep+Warrant bars.
    """
    df_r = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[RQ2-Quality] Missing data, skipping.")
        return

    def _share_runs(df: pd.DataFrame, count_fn):
        runs = per_run_values(df, count_fn)
        out = []
        for hq_auth, lq_auth, hq_fake in runs:
            total = float(hq_auth + lq_auth + hq_fake)
            if total <= 0:
                out.append((0.0, 0.0, 0.0))
            else:
                out.append(
                    (
                        100.0 * float(hq_auth) / total,
                        100.0 * float(lq_auth) / total,
                        100.0 * float(hq_fake) / total,
                    )
                )
        return out

    def _mean_sem(run_shares, idx: int):
        vals = np.array([row[idx] for row in run_shares], dtype=float)
        if len(vals) == 0:
            return 0.0, 0.0
        mean = float(vals.mean())
        sem = float(vals.std(ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0
        return mean, sem

    listed_r = _share_runs(df_r, product_quality_counts_all)
    listed_rw = _share_runs(df_rw, product_quality_counts_all)
    sold_r = _share_runs(df_r, product_quality_counts)
    sold_rw = _share_runs(df_rw, product_quality_counts)

    categories = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit"]
    x = np.arange(2)  # Listed / Sold
    w = 0.34

    fig, axes = plt.subplots(
        1, 3, figsize=(12.2, 4.2), gridspec_kw={"wspace": 0.28}, sharey=False
    )

    for idx, (ax, cat_name) in enumerate(zip(axes, categories)):
        listed_mean_r, listed_sem_r = _mean_sem(listed_r, idx)
        listed_mean_rw, listed_sem_rw = _mean_sem(listed_rw, idx)
        sold_mean_r, sold_sem_r = _mean_sem(sold_r, idx)
        sold_mean_rw, sold_sem_rw = _mean_sem(sold_rw, idx)

        vals_r = [listed_mean_r, sold_mean_r]
        errs_r = [listed_sem_r, sold_sem_r]
        vals_rw = [listed_mean_rw, sold_mean_rw]
        errs_rw = [listed_sem_rw, sold_sem_rw]

        ax.bar(
            x - w / 2,
            vals_r,
            width=w,
            color=REP_COLOR,
            edgecolor="white",
            linewidth=0.5,
            yerr=errs_r,
            capsize=3,
            error_kw={"elinewidth": 1.0, "ecolor": "#555"},
            zorder=3,
        )
        ax.bar(
            x + w / 2,
            vals_rw,
            width=w,
            color=RW_COLOR,
            edgecolor="white",
            linewidth=0.5,
            yerr=errs_rw,
            capsize=3,
            error_kw={"elinewidth": 1.0, "ecolor": "#555"},
            zorder=3,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(["Listed", "Sold"], fontsize=9)
        ax.set_title(cat_name, fontsize=10)
        if idx == 0:
            ax.set_ylabel("Share (%)", fontsize=10)
        panel_tops = [vals_r[i] + errs_r[i] for i in range(2)] + [vals_rw[i] + errs_rw[i] for i in range(2)]
        _set_dynamic_ylim_positive(ax, panel_tops, pad_ratio=0.18, min_top=1.0)
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_axisbelow(True)

    handles = [
        mpatches.Patch(facecolor=REP_COLOR, edgecolor="white", label="Rep"),
        mpatches.Patch(facecolor=RW_COLOR, edgecolor="white", label="Rep+Warrant"),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    fig.subplots_adjust(bottom=0.18)

    save_figure(fig, output_dir / "rq2_listed_vs_sold_quality.png")
    print("  [RQ2-Quality] Listed-vs-sold quality figure saved.")


def fig_rq2_welfare_overview(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """RQ2 welfare overview in one grouped-bar figure (Rep vs Rep+Warrant)."""
    df_r = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[RQ2-Welfare] Missing data, skipping.")
        return

    def _sem(vals: list[float]) -> float:
        n = len(vals)
        if n <= 1:
            return 0.0
        return float(np.std(vals, ddof=1) / np.sqrt(n))

    def _tx_count(run_df: pd.DataFrame) -> float:
        return float(len(run_df))

    def _hq_auth_share_listed(run_df: pd.DataFrame) -> float:
        hq_auth, lq_auth, hq_fake = product_quality_counts_all(run_df)
        total = float(hq_auth + lq_auth + hq_fake)
        if total <= 0:
            return 0.0
        return 100.0 * float(hq_auth) / total

    metrics = [
        ("Seller Profit", sum_seller_profit),
        ("Buyer Utility", sum_buyer_utility),
        ("Transactions", _tx_count),
        ("HQ Auth Share (%)", _hq_auth_share_listed),
    ]

    means_r, sems_r, means_rw, sems_rw = [], [], [], []
    for _, fn in metrics:
        vals_r = per_run_values(df_r, fn)
        vals_rw = per_run_values(df_rw, fn)
        means_r.append(float(np.mean(vals_r)) if vals_r else 0.0)
        sems_r.append(_sem(vals_r))
        means_rw.append(float(np.mean(vals_rw)) if vals_rw else 0.0)
        sems_rw.append(_sem(vals_rw))

    x = np.arange(len(metrics))
    w = 0.36
    fig, ax = plt.subplots(1, 1, figsize=(8.0, 4.2))
    ax.bar(
        x - w / 2, means_r, width=w, color=COLORS["neutral_dark"], alpha=0.60,
        edgecolor="white", linewidth=0.5, yerr=sems_r, capsize=3,
        error_kw={"elinewidth": 1.0, "ecolor": "#666"}, label="Rep", zorder=3
    )
    ax.bar(
        x + w / 2, means_rw, width=w, color=COLORS["good_dark"], alpha=0.80,
        edgecolor="white", linewidth=0.5, yerr=sems_rw, capsize=3,
        error_kw={"elinewidth": 1.0, "ecolor": "#666"}, label="Rep+Warrant", zorder=3
    )
    ax.set_xticks(x)
    ax.set_xticklabels([m[0] for m in metrics], fontsize=9)
    ax.set_ylabel("Run-Level Mean (mixed units)", fontsize=10)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    save_figure(fig, output_dir / "rq2_warrant_vs_rep_welfare_overview.png")
    print("  [RQ2-Welfare] Welfare overview figure saved.")


def fig_rq2_micro_reasoning_impact(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """RQ2 micro-level analysis: fraudulent-seller reasoning shift with warrant.

    Output includes:
    1. Word-cloud-style panel for Rep (fraud-involved sellers)
    2. Word-cloud-style panel for Rep+Warrant (same seller IDs as Rep fraud set)
    3. TF-IDF embedding + KMeans clustering scatter
    """
    r_path = Path(r_dir)
    rw_path = Path(rw_dir)
    if not r_path.exists() or not rw_path.exists():
        print("[RQ2-Micro] Missing directories, skipping.")
        return

    df_r = load_results_df(r_dir)
    if df_r.empty or "seller_id" not in df_r.columns or "is_honest" not in df_r.columns:
        print("[RQ2-Micro] Missing required transaction fields, skipping.")
        return

    fraud_rows = df_r[df_r["is_honest"] == False]  # noqa: E712
    if fraud_rows.empty:
        print("[RQ2-Micro] No fraudulent transactions in Rep, skipping.")
        return

    fraud_seller_by_run: dict[int, set[int]] = defaultdict(set)
    for _, row in fraud_rows[["run_id", "seller_id"]].dropna().iterrows():
        try:
            rid = int(row["run_id"])
            sid = int(row["seller_id"])
            fraud_seller_by_run[rid].add(sid)
        except Exception:
            continue

    def _clean_reasoning(text: str) -> str:
        if not text:
            return ""
        txt = str(text)
        txt = txt.split("<ACTION>")[0]
        txt = txt.replace("<THOUGHT>", " ").replace("</THOUGHT>", " ")
        txt = re.sub(r"[^A-Za-z\s]", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def _load_reasonings_for_sellers(base_dir: Path, seller_by_run: dict[int, set[int]]) -> list[str]:
        texts: list[str] = []
        for f in sorted(base_dir.glob("run_*_actions.json")):
            try:
                rid = int(f.stem.split("_")[1])
            except Exception:
                continue
            target_sellers = seller_by_run.get(rid, set())
            if not target_sellers:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for rec in data:
                if rec.get("phase") != "seller_listing":
                    continue
                for ai in rec.get("agent_infos", []):
                    aid = ai.get("agent_id")
                    try:
                        sid = int(aid) if aid is not None else None
                    except Exception:
                        sid = None
                    if sid is None and str(ai.get("agent_name", "")).startswith("seller_"):
                        try:
                            sid = int(str(ai["agent_name"]).split("_")[1]) + 1
                        except Exception:
                            sid = None
                    if sid not in target_sellers:
                        continue
                    info = ai.get("agent_action_info", {})
                    txt = _clean_reasoning(info.get("action_reasoning", ""))
                    if txt:
                        texts.append(txt)
        return texts

    rep_texts = _load_reasonings_for_sellers(r_path, fraud_seller_by_run)
    rw_texts = _load_reasonings_for_sellers(rw_path, fraud_seller_by_run)
    if not rep_texts or not rw_texts:
        print("[RQ2-Micro] Insufficient reasoning text for comparison, skipping.")
        return

    stop = {
        "the", "and", "to", "of", "in", "for", "with", "that", "this", "is", "are", "be", "as", "on", "it",
        "my", "i", "we", "our", "can", "will", "should", "need", "must", "have", "has", "from", "by",
        "round", "current", "market", "seller", "buyers", "buyer", "product", "products", "quality", "hq", "lq",
        "action", "function", "arguments", "list", "listing", "based", "decision", "decide", "strategy",
        "profit", "reputation", "budget", "first", "next", "also", "there", "their", "them", "these",
    }

    def _freq(texts: list[str], top_n: int = 36) -> list[tuple[str, int]]:
        cnt = Counter()
        for txt in texts:
            toks = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", txt)]
            toks = [t for t in toks if t not in stop]
            cnt.update(toks)
        return cnt.most_common(top_n)

    def _draw_word_cloud_style(ax: plt.Axes, text_pairs: list[tuple[str, int]], title: str, color: str) -> None:
        ax.set_title(title, fontsize=10)
        ax.axis("off")
        ax.set_box_aspect(1.0)
        if not text_pairs:
            ax.text(0.5, 0.5, "No text", ha="center", va="center", fontsize=10, color="#666")
            return
        freqs = {w: float(c) for w, c in text_pairs}
        wc = WordCloud(
            width=900,
            height=900,
            background_color="white",
            max_words=min(120, len(freqs)),
            collocations=False,
            prefer_horizontal=0.98,
            random_state=42,
            relative_scaling=0.45,
            min_font_size=10,
            max_font_size=110,
            margin=2,
            color_func=lambda *args, **kwargs: color,
        ).generate_from_frequencies(freqs)
        ax.imshow(wc, interpolation="bilinear")

    rep_freq = _freq(rep_texts)
    rw_freq = _freq(rw_texts)

    corpus = rep_texts + rw_texts
    cond_labels = np.array(["Rep"] * len(rep_texts) + ["Rep+Warrant"] * len(rw_texts))
    n_docs = len(corpus)
    if n_docs < 6:
        print("[RQ2-Micro] Too few reasoning samples, skipping.")
        return

    try:
        vec = TfidfVectorizer(max_features=1200, ngram_range=(1, 2), min_df=2, stop_words="english")
        X = vec.fit_transform(corpus)
        if X.shape[1] < 2:
            raise ValueError("Too few TF-IDF features")
        svd = TruncatedSVD(n_components=2, random_state=42)
        emb = svd.fit_transform(X)
        k = 2
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(emb)
    except Exception as e:
        print(f"[RQ2-Micro] Embedding failed ({e}), skipping.")
        return

    fig, axes = plt.subplots(
        1, 3, figsize=(15.0, 5.4), gridspec_kw={"wspace": 0.18, "width_ratios": [1.0, 1.0, 1.0]}
    )
    _draw_word_cloud_style(axes[0], rep_freq, "Rep: Fraud-Involved Seller Reasoning", REP_COLOR)
    _draw_word_cloud_style(axes[1], rw_freq, "Rep+Warrant: Same Seller IDs Reasoning", RW_COLOR)

    ax = axes[2]
    ax.set_box_aspect(1.0)
    cond_color = {"Rep": REP_COLOR, "Rep+Warrant": RW_COLOR}
    cond_marker = {"Rep": "o", "Rep+Warrant": "^"}
    for cond in ["Rep", "Rep+Warrant"]:
        idx = np.where(cond_labels == cond)[0]
        if len(idx) == 0:
            continue
        ax.scatter(
            emb[idx, 0],
            emb[idx, 1],
            c=cond_color[cond],
            s=28,
            alpha=0.82,
            marker=cond_marker[cond],
            edgecolors="white",
            linewidths=0.35,
        )
    ax.set_title("Reasoning Semantic Map under Rep vs Rep+Warrant", fontsize=10)
    ax.set_xlabel("Embedding Dimension 1", fontsize=9)
    ax.set_ylabel("Embedding Dimension 2", fontsize=9)
    ax.grid(alpha=0.22, zorder=0)
    ax.set_axisbelow(True)
    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=REP_COLOR,
               markeredgecolor="white", markersize=7, label="Rep"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor=RW_COLOR,
               markeredgecolor="white", markersize=7, label="Rep+Warrant"),
    ]
    ax.legend(handles=legend_handles, frameon=False, fontsize=8.2, loc="best")
    ax.text(
        0.02, 0.98, f"Clusters identified: {len(np.unique(clusters))}",
        transform=ax.transAxes, ha="left", va="top", fontsize=7.8, color=COLORS["neutral_dark"]
    )

    # Cluster semantic anchors: top-frequency token in each cluster, mapped at centroid.
    cluster_top_words: dict[int, str] = {}
    anchor_red = "#D32F2F"
    for cid in sorted(np.unique(clusters)):
        cluster_docs = [corpus[i] for i in np.where(clusters == cid)[0]]
        top_words = _freq(cluster_docs, top_n=1)
        cluster_top_words[int(cid)] = top_words[0][0] if top_words else f"C{int(cid)+1}"
        cx = float(np.mean(emb[clusters == cid, 0]))
        cy = float(np.mean(emb[clusters == cid, 1]))
        ax.scatter(
            [cx], [cy],
            marker="*", s=200, c=anchor_red,
            edgecolors="white", linewidths=0.9, zorder=5
        )
        ax.text(
            cx, cy,
            f" {cluster_top_words[int(cid)]}",
            fontsize=9.3, color=anchor_red,
            ha="left", va="center", fontweight="bold"
        )

    save_figure(fig, output_dir / "rq2_warrant_micro_reasoning_impact.png")
    print(
        f"  [RQ2-Micro] Saved micro reasoning figure. "
        f"Rep texts={len(rep_texts)}, Rep+Warrant texts={len(rw_texts)}, clusters={len(np.unique(clusters))}"
    )


def fig_rq3_micro_reasoning_impact(
    rq3_base_dir: str, output_dir: Path
) -> None:
    """RQ3 micro-level analysis across seller-communication constraints."""
    base_path = Path(rq3_base_dir)
    constraints = [
        "policy_making",
        "pressure_quickprofits",
        "psychological-based-attack",
    ]

    def _clean_reasoning(text: str) -> str:
        if not text:
            return ""
        txt = str(text)
        txt = txt.split("<ACTION>")[0]
        txt = txt.replace("<THOUGHT>", " ").replace("</THOUGHT>", " ")
        txt = re.sub(r"[^A-Za-z\s]", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def _load_reasonings_for_sellers(base_dir: Path, seller_by_run: dict[int, set[int]]) -> list[str]:
        texts: list[str] = []
        for f in sorted(base_dir.glob("run_*_actions.json")):
            try:
                rid = int(f.stem.split("_")[1])
            except Exception:
                continue
            target_sellers = seller_by_run.get(rid, set())
            if not target_sellers:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for rec in data:
                if rec.get("phase") != "seller_listing":
                    continue
                for ai in rec.get("agent_infos", []):
                    aid = ai.get("agent_id")
                    try:
                        sid = int(aid) if aid is not None else None
                    except Exception:
                        sid = None
                    if sid is None and str(ai.get("agent_name", "")).startswith("seller_"):
                        try:
                            sid = int(str(ai["agent_name"]).split("_")[1]) + 1
                        except Exception:
                            sid = None
                    if sid not in target_sellers:
                        continue
                    info = ai.get("agent_action_info", {})
                    txt = _clean_reasoning(info.get("action_reasoning", ""))
                    if txt:
                        texts.append(txt)
        return texts

    def _fraud_sellers_by_run(df: pd.DataFrame) -> dict[int, set[int]]:
        out: dict[int, set[int]] = defaultdict(set)
        if df.empty or "seller_id" not in df.columns or "is_honest" not in df.columns:
            return out
        fraud_rows = df[df["is_honest"] == False]  # noqa: E712
        for _, row in fraud_rows[["run_id", "seller_id"]].dropna().iterrows():
            try:
                rid = int(row["run_id"])
                sid = int(row["seller_id"])
                out[rid].add(sid)
            except Exception:
                continue
        return out

    rep_texts: list[str] = []
    rw_texts: list[str] = []
    for ck in constraints:
        rep_dir = base_path / f"r_wsc_R_{ck}"
        rw_dir = base_path / f"rw_wsc_R_{ck}"
        if not rep_dir.exists():
            continue
        rep_df = load_results_df(str(rep_dir))
        fraud_map = _fraud_sellers_by_run(rep_df)
        if fraud_map:
            rep_texts.extend(_load_reasonings_for_sellers(rep_dir, fraud_map))
            if rw_dir.exists():
                rw_texts.extend(_load_reasonings_for_sellers(rw_dir, fraud_map))

    if not rep_texts or not rw_texts:
        print("[RQ3-Micro] Insufficient reasoning text for comparison, skipping.")
        return

    stop = {
        "the", "and", "to", "of", "in", "for", "with", "that", "this", "is", "are", "be", "as", "on", "it",
        "my", "i", "we", "our", "can", "will", "should", "need", "must", "have", "has", "from", "by",
        "round", "current", "market", "seller", "buyers", "buyer", "product", "products", "quality", "hq", "lq",
        "action", "function", "arguments", "list", "listing", "based", "decision", "decide", "strategy",
        "profit", "reputation", "budget", "first", "next", "also", "there", "their", "them", "these",
    }

    def _freq(texts: list[str], top_n: int = 36) -> list[tuple[str, int]]:
        cnt = Counter()
        for txt in texts:
            toks = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", txt)]
            toks = [t for t in toks if t not in stop]
            cnt.update(toks)
        return cnt.most_common(top_n)

    def _draw_word_cloud_style(ax: plt.Axes, text_pairs: list[tuple[str, int]], title: str, color: str) -> None:
        ax.set_title(title, fontsize=10)
        ax.axis("off")
        ax.set_box_aspect(1.0)
        if not text_pairs:
            ax.text(0.5, 0.5, "No text", ha="center", va="center", fontsize=10, color="#666")
            return
        freqs = {w: float(c) for w, c in text_pairs}
        wc = WordCloud(
            width=900,
            height=900,
            background_color="white",
            max_words=min(120, len(freqs)),
            collocations=False,
            prefer_horizontal=0.98,
            random_state=42,
            relative_scaling=0.45,
            min_font_size=10,
            max_font_size=110,
            margin=2,
            color_func=lambda *args, **kwargs: color,
        ).generate_from_frequencies(freqs)
        ax.imshow(wc, interpolation="bilinear")

    rep_freq = _freq(rep_texts)
    rw_freq = _freq(rw_texts)

    corpus = rep_texts + rw_texts
    cond_labels = np.array(["Rep"] * len(rep_texts) + ["Rep+Warrant"] * len(rw_texts))
    n_docs = len(corpus)
    if n_docs < 6:
        print("[RQ3-Micro] Too few reasoning samples, skipping.")
        return

    try:
        vec = TfidfVectorizer(max_features=1200, ngram_range=(1, 2), min_df=2, stop_words="english")
        X = vec.fit_transform(corpus)
        if X.shape[1] < 2:
            raise ValueError("Too few TF-IDF features")
        svd = TruncatedSVD(n_components=2, random_state=42)
        emb = svd.fit_transform(X)
        k = 2
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(emb)
    except Exception as e:
        print(f"[RQ3-Micro] Embedding failed ({e}), skipping.")
        return

    fig, axes = plt.subplots(
        1, 3, figsize=(15.0, 5.4), gridspec_kw={"wspace": 0.18, "width_ratios": [1.0, 1.0, 1.0]}
    )
    _draw_word_cloud_style(axes[0], rep_freq, "RQ3 Rep: Fraud-Involved Reasoning", REP_COLOR)
    _draw_word_cloud_style(axes[1], rw_freq, "RQ3 Rep+Warrant: Fraud-Involved Reasoning", RW_COLOR)

    ax = axes[2]
    ax.set_box_aspect(1.0)
    cond_color = {"Rep": REP_COLOR, "Rep+Warrant": RW_COLOR}
    cond_marker = {"Rep": "o", "Rep+Warrant": "^"}
    for cond in ["Rep", "Rep+Warrant"]:
        idx = np.where(cond_labels == cond)[0]
        if len(idx) == 0:
            continue
        ax.scatter(
            emb[idx, 0],
            emb[idx, 1],
            c=cond_color[cond],
            s=28,
            alpha=0.82,
            marker=cond_marker[cond],
            edgecolors="white",
            linewidths=0.35,
        )
    ax.set_title("RQ3 Reasoning Semantic Map", fontsize=10)
    ax.set_xlabel("Embedding Dimension 1", fontsize=9)
    ax.set_ylabel("Embedding Dimension 2", fontsize=9)
    ax.grid(alpha=0.22, zorder=0)
    ax.set_axisbelow(True)
    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=REP_COLOR,
               markeredgecolor="white", markersize=7, label="Rep"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor=RW_COLOR,
               markeredgecolor="white", markersize=7, label="Rep+Warrant"),
    ]
    ax.legend(handles=legend_handles, frameon=False, fontsize=8.2, loc="best")
    ax.text(
        0.02, 0.98, f"Clusters identified: {len(np.unique(clusters))}",
        transform=ax.transAxes, ha="left", va="top", fontsize=7.8, color=COLORS["neutral_dark"]
    )

    # Cluster semantic anchors: top-frequency token in each cluster, mapped at centroid.
    anchor_red = "#D32F2F"
    for cid in sorted(np.unique(clusters)):
        cluster_docs = [corpus[i] for i in np.where(clusters == cid)[0]]
        top_words = _freq(cluster_docs, top_n=1)
        label = top_words[0][0] if top_words else f"C{int(cid)+1}"
        cx = float(np.mean(emb[clusters == cid, 0]))
        cy = float(np.mean(emb[clusters == cid, 1]))
        ax.scatter(
            [cx], [cy],
            marker="*", s=200, c=anchor_red,
            edgecolors="white", linewidths=0.9, zorder=5
        )
        ax.text(
            cx, cy,
            f" {label}",
            fontsize=9.3, color=anchor_red,
            ha="left", va="center", fontweight="bold"
        )

    save_figure(fig, output_dir / "rq3_warrant_micro_reasoning_impact.png")
    print(
        f"  [RQ3-Micro] Saved micro reasoning figure. "
        f"Rep texts={len(rep_texts)}, Rep+Warrant texts={len(rw_texts)}, clusters={len(np.unique(clusters))}"
    )


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
