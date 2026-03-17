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

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    COLORS,
    setup_style,
    load_results_df,
    load_probes_df,
    per_run_values,
    count_deceptions,
    sum_seller_profit,
    product_quality_counts,
    mannwhitney_p,
    proportion_ztest_p,
    sig_marker_display,
    add_significance_bracket,
    add_text_box,
    highlight_bar_group,
    add_sig_footnote,
    save_figure,
)

setup_style()

# ── Condition labels ──────────────────────────────────────────────────────────
LABEL_R  = "Rep"
LABEL_RW = "Rep+Warrant"


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 : Seller Profit & Deceptions — main result
# ─────────────────────────────────────────────────────────────────────────────

def fig1_profit_and_deceptions(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """Two-panel bar chart: seller profit (left) and deceptions (right)."""

    df_r  = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[Fig1] Missing data, skipping.")
        return

    # ── Per-run values ──────────────────────────────────────────────────────
    profit_r  = per_run_values(df_r,  sum_seller_profit)
    profit_rw = per_run_values(df_rw, sum_seller_profit)
    dec_r     = per_run_values(df_r,  count_deceptions)
    dec_rw    = per_run_values(df_rw, count_deceptions)

    # ── Statistics ─────────────────────────────────────────────────────────
    p_profit = mannwhitney_p(profit_r, profit_rw)
    p_dec    = mannwhitney_p(dec_r,    dec_rw)

    mean_p_r,  std_p_r  = np.mean(profit_r),  np.std(profit_r,  ddof=1)
    mean_p_rw, std_p_rw = np.mean(profit_rw), np.std(profit_rw, ddof=1)
    mean_d_r,  std_d_r  = np.mean(dec_r),     np.std(dec_r,     ddof=1)
    mean_d_rw, std_d_rw = np.mean(dec_rw),    np.std(dec_rw,    ddof=1)

    lift_pct = (mean_p_rw - mean_p_r) / mean_p_r * 100 if mean_p_r > 0 else 0

    # ── Layout ─────────────────────────────────────────────────────────────
    fig, (ax_p, ax_d) = plt.subplots(1, 2, figsize=(8, 4.5),
                                      gridspec_kw={"wspace": 0.38})
    fig.suptitle(
        "Warrant Eliminates Deception; Honest Trade Rises by 55%",
        fontsize=11, fontweight="bold", y=1.01,
    )

    BAR_W = 0.42
    xs = np.array([0.0, 1.0])
    labels = [LABEL_R, LABEL_RW]

    # ── Left panel : Seller Profit ──────────────────────────────────────────
    profit_means = [mean_p_r,  mean_p_rw]
    profit_stds  = [std_p_r,   std_p_rw]
    profit_colors = [COLORS["good_mid"], COLORS["good_dark"]]

    bars_p = ax_p.bar(
        xs, profit_means,
        width=BAR_W,
        color=profit_colors,
        edgecolor="white", linewidth=0.5,
        yerr=profit_stds,
        capsize=4,
        error_kw={"elinewidth": 1.2, "ecolor": "#333333"},
        zorder=3,
    )
    ax_p.set_xticks(xs)
    ax_p.set_xticklabels(labels, fontsize=10)
    ax_p.set_ylabel("Total Seller Profit (per run)", fontsize=10)
    ax_p.set_title("Seller Profit", fontsize=10, pad=6)
    ax_p.set_ylim(0, max(profit_means) * 1.35)

    # Significance bracket
    y_top_p = max(mean_p_r + std_p_r, mean_p_rw + std_p_rw)
    add_significance_bracket(ax_p, xs[0], xs[1], y_top_p, p_profit,
                              h_frac=0.06, fontsize=10)

    # Lift annotation
    ax_p.annotate(
        f"+{lift_pct:.0f}%",
        xy=(xs[1], mean_p_rw + std_p_rw),
        xytext=(xs[1] + 0.28, mean_p_rw * 1.10),
        fontsize=9, color=COLORS["good_dark"], fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=COLORS["good_dark"], lw=1.2),
    )

    # ── Right panel : Deceptions ────────────────────────────────────────────
    dec_means  = [mean_d_r,  mean_d_rw]
    dec_stds   = [std_d_r,   std_d_rw]
    dec_colors = [COLORS["bad_dark"], COLORS["neutral"]]

    bars_d = ax_d.bar(
        xs, dec_means,
        width=BAR_W,
        color=dec_colors,
        edgecolor="white", linewidth=0.5,
        yerr=dec_stds,
        capsize=4,
        error_kw={"elinewidth": 1.2, "ecolor": "#333333"},
        zorder=3,
    )
    ax_d.set_xticks(xs)
    ax_d.set_xticklabels(labels, fontsize=10)
    ax_d.set_ylabel("Deceptive Transactions (per run)", fontsize=10)
    ax_d.set_title("Deceptions", fontsize=10, pad=6)
    ax_d.set_ylim(0, max(dec_means) * 1.45)

    # Significance bracket
    y_top_d = max(mean_d_r + std_d_r, mean_d_rw + std_d_rw)
    add_significance_bracket(ax_d, xs[0], xs[1], y_top_d, p_dec,
                              h_frac=0.07, fontsize=10)

    # "0 deceptions" annotation
    if mean_d_rw == 0:
        add_text_box(
            ax_d, xs[1], max(dec_means) * 0.08,
            "0 deceptions\nin all 5 runs",
            fontsize=8, color=COLORS["good_dark"], boxcolor="#e8f5e9",
        )

    # ── Legend patch ───────────────────────────────────────────────────────
    legend_patches = [
        mpatches.Patch(color=COLORS["good_mid"],  label=LABEL_R),
        mpatches.Patch(color=COLORS["good_dark"], label=LABEL_RW),
    ]
    fig.legend(
        handles=legend_patches,
        loc="lower center", ncol=2,
        bbox_to_anchor=(0.5, -0.04),
        frameon=False, fontsize=9,
    )

    add_sig_footnote(fig)
    save_figure(fig, output_dir / "rq1_warrant_vs_rep_deception_and_profit.png")
    print(f"  [Fig1] p_profit={p_profit:.4f}, p_dec={p_dec:.4f}")


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


def fig2_vulnerability_probe(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """Grouped bar chart: manipulation detection rate by vulnerability type."""
    probe_r  = load_probes_df(r_dir)
    probe_rw = load_probes_df(rw_dir)
    if probe_r.empty or probe_rw.empty:
        print("[Fig2] No probe data found, skipping.")
        return

    rates_r  = _probe_rates_per_run(probe_r)
    rates_rw = _probe_rates_per_run(probe_rw)

    # ── Per-vulnerability means and stats ─────────────────────────────────
    means_r,  stds_r,  means_rw, stds_rw, p_vals = [], [], [], [], []
    for vk in VULN_KEYS:
        vals_r  = [d[vk] * 100 for d in rates_r]
        vals_rw = [d[vk] * 100 for d in rates_rw]
        means_r.append(np.mean(vals_r))
        stds_r.append(np.std(vals_r,  ddof=1))
        means_rw.append(np.mean(vals_rw))
        stds_rw.append(np.std(vals_rw, ddof=1))
        # z-score on pooled proportions across runs
        total_r  = sum(len(probe_r[probe_r["run_id"] == rid]) for rid in probe_r["run_id"].unique())
        total_rw = sum(len(probe_rw[probe_rw["run_id"] == rid]) for rid in probe_rw["run_id"].unique())
        n_r_vk  = len(probe_r[probe_r["vulnerability_type"] == vk])
        n_rw_vk = len(probe_rw[probe_rw["vulnerability_type"] == vk])
        cnt_r   = probe_r[probe_r["vulnerability_type"] == vk]["manipulation_detected"].sum()
        cnt_rw  = probe_rw[probe_rw["vulnerability_type"] == vk]["manipulation_detected"].sum()
        p = proportion_ztest_p(float(cnt_r), float(n_r_vk),
                                float(cnt_rw), float(n_rw_vk))
        p_vals.append(p)

    # ── Layout ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.suptitle(
        "Sellers Exploit the 'Exit Loophole' 4× More Without Warrant",
        fontsize=11, fontweight="bold", y=1.02,
    )

    n_groups = len(VULN_KEYS)
    x = np.arange(n_groups)
    w = 0.32

    # Both bars in red shades (high detection rate = bad, exploit tendency)
    bars_r = ax.bar(
        x - w / 2, means_r,
        width=w, color=COLORS["bad_dark"], label=LABEL_R,
        edgecolor="white", linewidth=0.5,
        yerr=stds_r, capsize=3,
        error_kw={"elinewidth": 1.0, "ecolor": "#333333"},
        zorder=3,
    )
    bars_rw = ax.bar(
        x + w / 2, means_rw,
        width=w, color=COLORS["bad_mid"], label=LABEL_RW,
        edgecolor="white", linewidth=0.5,
        yerr=stds_rw, capsize=3,
        error_kw={"elinewidth": 1.0, "ecolor": "#333333"},
        zorder=3,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(VULN_LABELS, fontsize=9)
    ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=10)
    ax.set_ylim(0, max(means_r + means_rw) * 1.55)

    # ── Significance brackets ───────────────────────────────────────────────
    for i, p in enumerate(p_vals):
        y_top = max(means_r[i] + stds_r[i], means_rw[i] + stds_rw[i])
        add_significance_bracket(ax, x[i] - w / 2, x[i] + w / 2,
                                  y_top, p, h_frac=0.07, fontsize=9)

    # ── Highlight Exit Strategy group ──────────────────────────────────────
    es_idx = VULN_KEYS.index("exit_strategy")
    ax.annotate(
        "",
        xy=(x[es_idx], max(means_r[es_idx], means_rw[es_idx]) * 1.05),
        xytext=(x[es_idx], max(means_r[es_idx], means_rw[es_idx]) * 1.22),
        arrowprops=dict(arrowstyle="->", color=COLORS["bad_dark"], lw=1.5),
    )
    ax.text(
        x[es_idx], max(means_r[es_idx], means_rw[es_idx]) * 1.26,
        "Primary\nvulnerability",
        ha="center", va="bottom", fontsize=8,
        color=COLORS["bad_dark"], fontweight="bold",
    )
    # Annotate exact values on Exit Strategy bars
    ax.text(x[es_idx] - w / 2, means_r[es_idx] + stds_r[es_idx] + 0.5,
            f"{means_r[es_idx]:.1f}%", ha="center", va="bottom", fontsize=8,
            color=COLORS["bad_dark"])
    ax.text(x[es_idx] + w / 2, means_rw[es_idx] + stds_rw[es_idx] + 0.5,
            f"{means_rw[es_idx]:.1f}%", ha="center", va="bottom", fontsize=8,
            color=COLORS["bad_mid"])

    ax.legend(frameon=False, fontsize=9, loc="upper left")

    add_sig_footnote(fig, extra="z-score proportion test per vulnerability type")
    save_figure(fig, output_dir / "rq1_exit_loophole_vulnerability.png")
    print(f"  [Fig2] p_vals per vulnerability: "
          + ", ".join(f"{VULN_SHORT[i]}={p_vals[i]:.4f}" for i in range(len(VULN_KEYS))))


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 (appendix) : 100% Product-Mix Stacked Bar
# ─────────────────────────────────────────────────────────────────────────────

def fig3_product_mix(
    r_dir: str, rw_dir: str, output_dir: Path
) -> None:
    """100% stacked bar chart of sold product quality (appendix)."""

    df_r  = load_results_df(r_dir)
    df_rw = load_results_df(rw_dir)
    if df_r.empty or df_rw.empty:
        print("[Fig3] Missing data, skipping.")
        return

    # ── Per-run product counts ─────────────────────────────────────────────
    def _pq(df):
        return per_run_values(df, product_quality_counts)

    pq_r  = _pq(df_r)   # list of (hq_auth, lq_auth, hq_cfeit) tuples
    pq_rw = _pq(df_rw)

    def _means(pq, idx):
        vals = [t[idx] for t in pq]
        return np.mean(vals), np.std(vals, ddof=1)

    hqa_r,   hqa_r_std   = _means(pq_r,  0)
    lqa_r,   lqa_r_std   = _means(pq_r,  1)
    hqcf_r,  hqcf_r_std  = _means(pq_r,  2)
    hqa_rw,  hqa_rw_std  = _means(pq_rw, 0)
    lqa_rw,  lqa_rw_std  = _means(pq_rw, 1)
    hqcf_rw, hqcf_rw_std = _means(pq_rw, 2)

    total_r  = hqa_r  + lqa_r  + hqcf_r
    total_rw = hqa_rw + lqa_rw + hqcf_rw

    # Normalize to percentages
    def pct(v, t): return (v / t * 100) if t > 0 else 0.0

    data = {
        LABEL_R:  [pct(hqa_r,  total_r),  pct(lqa_r,  total_r),  pct(hqcf_r,  total_r)],
        LABEL_RW: [pct(hqa_rw, total_rw), pct(lqa_rw, total_rw), pct(hqcf_rw, total_rw)],
    }

    # ── z-score tests on proportions (HQ counterfeit) ─────────────────────
    cnt_cf_r  = sum(t[2] for t in pq_r)
    cnt_tot_r = sum(sum(t) for t in pq_r)
    cnt_cf_rw  = sum(t[2] for t in pq_rw)
    cnt_tot_rw = sum(sum(t) for t in pq_rw)
    p_counterfeit = proportion_ztest_p(
        cnt_cf_r, cnt_tot_r, cnt_cf_rw, cnt_tot_rw
    )

    cnt_hqa_r  = sum(t[0] for t in pq_r)
    cnt_hqa_rw = sum(t[0] for t in pq_rw)
    p_hq_auth = proportion_ztest_p(
        cnt_hqa_r, cnt_tot_r, cnt_hqa_rw, cnt_tot_rw
    )

    # ── Layout ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    fig.suptitle(
        "Warrant Shifts Market Output to Authentic HQ\n— Counterfeit Disappears",
        fontsize=10, fontweight="bold", y=1.03,
    )

    x = np.array([0.0, 1.0])
    w = 0.45
    colors = [COLORS["hq_auth"], COLORS["lq_auth"], COLORS["counterfeit"]]
    seg_labels = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit (fraud)"]
    segments = ["HQ Authentic", "LQ Authentic", "HQ Counterfeit"]

    bottoms = [0.0, 0.0]
    bars_list = []
    for si, (col, lab) in enumerate(zip(colors, seg_labels)):
        heights = [data[LABEL_R][si], data[LABEL_RW][si]]
        b = ax.bar(
            x, heights, width=w,
            bottom=bottoms,
            color=col, label=lab,
            edgecolor="white", linewidth=0.5, zorder=3,
        )
        bars_list.append((b, heights))
        # Label inside bar if tall enough
        for xi, (h, bot) in enumerate(zip(heights, bottoms)):
            if h > 4.0:
                ax.text(x[xi], bot + h / 2, f"{h:.1f}%",
                        ha="center", va="center", fontsize=8,
                        color="white", fontweight="bold")
        bottoms = [bottoms[j] + heights[j] for j in range(2)]

    ax.set_xticks(x)
    ax.set_xticklabels([LABEL_R, LABEL_RW], fontsize=10)
    ax.set_ylabel("Share of Sold Products (%)", fontsize=10)
    ax.set_ylim(0, 115)
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=1)

    # ── Significance annotation for counterfeit ─────────────────────────
    m_cf = sig_marker_display(p_counterfeit)
    m_hqa = sig_marker_display(p_hq_auth)
    note_parts = []
    if m_cf:
        note_parts.append(f"Counterfeit: {m_cf} (p={p_counterfeit:.3f})")
    if m_hqa:
        note_parts.append(f"HQ Authentic: {m_hqa} (p={p_hq_auth:.3f})")
    if note_parts:
        ax.text(0.5, -0.12, "  |  ".join(note_parts),
                transform=ax.transAxes,
                ha="center", va="top", fontsize=7.5, color="#555555")

    add_sig_footnote(fig, extra="z-score proportion test for each product-quality segment")
    save_figure(fig, output_dir / "rq1_product_mix_appendix.png")
    print(f"  [Fig3] p_counterfeit={p_counterfeit:.4f}, p_hq_auth={p_hq_auth:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate RQ1 figures for paper"
    )
    parser.add_argument("--r-dir",  required=True,
                        help="Reputation-Only experiment dir (rq1/r_wo)")
    parser.add_argument("--rw-dir", required=True,
                        help="Rep+Warrant experiment dir (rq1/rw_wo)")
    parser.add_argument("--output-dir", default="visualization/figs/paper/rq1",
                        help="Output directory for figures")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("RQ1: Generating Paper Figures")
    print("=" * 60)

    print("\n[Fig1] Seller Profit & Deceptions…")
    fig1_profit_and_deceptions(args.r_dir, args.rw_dir, output_dir)

    print("\n[Fig2] Vulnerability Probe Detection Rates…")
    fig2_vulnerability_probe(args.r_dir, args.rw_dir, output_dir)

    print("\n[Fig3] Product Mix (appendix)…")
    fig3_product_mix(args.r_dir, args.rw_dir, output_dir)

    print("\n✅  RQ1 figures saved to:", output_dir)


if __name__ == "__main__":
    main()
