#!/usr/bin/env python3
"""
RQ3 Figures — Buyer Communication & Market Quality

Key findings from data:
  - Deceptions are near-zero in ALL RQ3 conditions (safety already achieved).
  - Buyer communication consistently lifts buyer utility ~7 pts/round.
  - Rep+Warrant+Comm achieves the highest combined outcome.

Color convention (consistent with RQ1/RQ2):
  - COLORS["good_mid"]  (#4caf72) = Rep bars (lighter green, same as RQ1)
  - COLORS["good_dark"] (#1a7a3a) = Rep+Warrant bars (darker green, same as RQ1)
  - Hatching (///)                = with buyer communication ("+BComm")
  - No hatch                      = without buyer communication (baseline)
  - COLORS["bad_dark"]            = Rep deception bars (red, same as RQ1)
  - COLORS["neutral"]             = Rep+Warrant deception bars (gray, near-zero)

Figure 7 : rq3_buyer_comm_market_outcomes.png
    Headline: "Buyer Communication Boosts Market Utility in Both Mechanisms"
    2×2 panel: Seller Profit / Buyer Utility / Transactions / Deceptions

Figure 8 (appendix) : rq3_round_adaptation_appendix.png
    Headline: "Buyer Communication Accelerates Convergence to Higher Utility"
    1×2 line chart: Left = Rep conditions; Right = Rep+Warrant conditions
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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
    sum_seller_profit,
    sum_buyer_utility,
    mannwhitney_p,
    sig_marker_display,
    add_significance_bracket,
    add_sig_footnote,
    save_figure,
)

setup_style()

# ── Directory mapping ─────────────────────────────────────────────────────────
DIRS: Dict[str, str] = {
    "Rep":                "r_wbc_F",
    "Rep, Comm":          "r_wbc_R",
    "Rep+Warrant":        "rw_wbc_F",
    "Rep+Warrant, Comm":  "rw_wbc_R",
}

# ── Paired groups: (no-comm label, comm label, mechanism name) ────────────────
PAIRS: List[Tuple[str, str, str]] = [
    ("Rep",         "Rep, Comm",         "Rep Only"),
    ("Rep+Warrant", "Rep+Warrant, Comm", "Rep+Warrant"),
]

# Consistent with RQ1/RQ2 color conventions:
#   Rep mechanism  → good_mid  (lighter green)
#   Rep+Warrant    → good_dark (darker green)
MECH_COLORS = [COLORS["good_mid"], COLORS["good_dark"]]
# Hatch for +BComm bars (same fill color, added pattern)
HATCH_COMM = "///"


def _load(base_dir: str, label: str) -> pd.DataFrame:
    return load_results_df(str(Path(base_dir) / DIRS[label]))


def _per_run(df: pd.DataFrame, fn) -> List[float]:
    return per_run_values(df, fn) if not df.empty else [0.0]


def _transactions(run_df: pd.DataFrame) -> float:
    return float(run_df["transactions"].sum())


# ─────────────────────────────────────────────────────────────────────────────
# Figure 7 : 2×2 multi-metric comparison
# ─────────────────────────────────────────────────────────────────────────────

def fig7_market_outcomes(base_dir: str, output_dir: Path) -> None:
    """2×2 panel: Profit / Utility / Transactions / Deceptions for 4 conditions."""

    # ── Load per-run data ──────────────────────────────────────────────────
    data: Dict[str, Dict[str, List[float]]] = {}
    for label in DIRS:
        df = _load(base_dir, label)
        data[label] = {
            "profit":       _per_run(df, sum_seller_profit),
            "utility":      _per_run(df, sum_buyer_utility),
            "transactions": _per_run(df, _transactions),
            "deceptions":   _per_run(df, count_deceptions),
        }

    # ── Layout ─────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(9, 7.2),
                              gridspec_kw={"hspace": 0.55, "wspace": 0.38})
    fig.suptitle(
        "Buyer Communication Boosts Market Utility in Both Mechanisms",
        fontsize=11, fontweight="bold",
    )
    fig.subplots_adjust(top=0.91, bottom=0.14)

    # Panel specs: (ax, metric, y-label, semantic role)
    panels = [
        (axes[0, 0], "profit",       "Seller Profit (per run)",  "good"),
        (axes[0, 1], "utility",      "Buyer Utility (per run)",  "good"),
        (axes[1, 0], "transactions", "Transactions (per run)",   "neutral"),
        (axes[1, 1], "deceptions",   "Deceptions (per run)",     "bad"),
    ]

    bar_w    = 0.28
    offsets  = [-bar_w * 0.60, bar_w * 0.60]  # no-comm left, comm right
    group_xs = [0.0, 1.0]                      # two groups, spaced by 1.0

    for ax, metric, ylabel, role in panels:
        all_tops: List[float] = []

        for gi, (no_lbl, comm_lbl, mech_name) in enumerate(PAIRS):
            gx    = group_xs[gi]
            mcolor = MECH_COLORS[gi]

            for bi, (bar_lbl, use_hatch) in enumerate(
                [(no_lbl, False), (comm_lbl, True)]
            ):
                vals = data[bar_lbl][metric]
                m = np.mean(vals)
                s = np.std(vals, ddof=1) if len(vals) > 1 else 0.0
                bx = gx + offsets[bi]

                # Semantic color override per panel role
                if role == "bad":
                    # Red shades for Rep, gray for Rep+Warrant (≈0 deceptions)
                    fc = COLORS["bad_dark"] if gi == 0 else COLORS["neutral"]
                elif role == "neutral":
                    # Neutral gray-blue shades, darker for +Comm
                    fc = "#90a4ae" if not use_hatch else "#546e7a"
                else:
                    fc = mcolor

                hatch = HATCH_COMM if use_hatch else None
                ax.bar(bx, m, width=bar_w,
                       color=fc, hatch=hatch,
                       edgecolor="white" if hatch is None else "#555555",
                       linewidth=0.5 if hatch is None else 0.8,
                       yerr=s, capsize=3,
                       error_kw={"elinewidth": 1.0, "ecolor": "#333"},
                       zorder=3)
                all_tops.append(m + s)

                # Numeric label above bar
                ax.text(bx, m + s * 1.05 + 5,
                        f"{m:.0f}",
                        ha="center", va="bottom", fontsize=7,
                        color="#333333")

            # ── Significance bracket within group (no-comm vs comm) ─────
            no_vals   = data[no_lbl][metric]
            comm_vals = data[comm_lbl][metric]
            p  = mannwhitney_p(no_vals, comm_vals)
            yt = max(np.mean(no_vals)   + np.std(no_vals,   ddof=1),
                     np.mean(comm_vals) + np.std(comm_vals, ddof=1))
            add_significance_bracket(ax,
                                     gx + offsets[0], gx + offsets[1],
                                     yt, p, h_frac=0.07, fontsize=9)

        # ── Cross-mechanism significance bracket (Rep base vs RW base) ──
        no_rep = data["Rep"][metric]
        no_rw  = data["Rep+Warrant"][metric]
        p_mech = mannwhitney_p(no_rep, no_rw)
        y_cross = max(all_tops) * 1.10
        add_significance_bracket(ax,
                                 group_xs[0], group_xs[1],
                                 y_cross, p_mech, h_frac=0.05, fontsize=8)

        # ── Axes formatting ──────────────────────────────────────────────
        # Two short tick labels per group to avoid overlap
        ax.set_xticks([gx + off
                       for gx in group_xs for off in offsets])
        ax.set_xticklabels(["Base", "+BComm", "Base", "+BComm"],
                           fontsize=8)

        # Group name below x-axis
        for gi, (_, _, mech_name) in enumerate(PAIRS):
            ax.text(group_xs[gi], -max(all_tops) * 0.14,
                    mech_name,
                    ha="center", va="top", fontsize=8.5,
                    color="#333333", fontweight="bold",
                    transform=ax.transData)

        ax.set_ylabel(ylabel, fontsize=9)
        y_max = max(all_tops) * 1.40 if all_tops else 10.0
        ax.set_ylim(0, y_max)
        ax.set_xlim(-0.55, 1.55)
        ax.set_title(ylabel.split(" (")[0], fontsize=10, pad=4)

        # ── Deception panel note ─────────────────────────────────────────
        if metric == "deceptions":
            ax.text(0.50, 0.90,
                    "Rep+Warrant → strictly 0\n(warrant eliminates deceptions)",
                    transform=ax.transAxes,
                    ha="center", va="top", fontsize=7.5,
                    color="#555555", style="italic")

    # ── Global legend ─────────────────────────────────────────────────────
    legend_handles = [
        mpatches.Patch(facecolor=COLORS["good_mid"],  edgecolor="#555",
                       label="Rep – Base (no buyer comm)"),
        mpatches.Patch(facecolor=COLORS["good_mid"],  edgecolor="#555",
                       hatch=HATCH_COMM,
                       label="Rep – +Buyer Comm"),
        mpatches.Patch(facecolor=COLORS["good_dark"], edgecolor="#555",
                       label="Rep+Warrant – Base"),
        mpatches.Patch(facecolor=COLORS["good_dark"], edgecolor="#555",
                       hatch=HATCH_COMM,
                       label="Rep+Warrant – +Buyer Comm"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, 0.00), frameon=False, fontsize=8.5)

    add_sig_footnote(fig)
    save_figure(fig, output_dir / "rq3_buyer_comm_market_outcomes.png")
    print("  [Fig7] 2×2 market-outcomes figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 8 (appendix): Per-round buyer utility — split by mechanism
# ─────────────────────────────────────────────────────────────────────────────

def _per_round_utility(df: pd.DataFrame) -> Dict[int, List[float]]:
    """Return {round_num: [per-run buyer utility]}."""
    result: Dict[int, List[float]] = {}
    for rid in sorted(df["run_id"].unique()):
        rdf = df[df["run_id"] == rid]
        for r in range(1, 11):
            v = float(rdf[rdf["round_num"] == r]["buyer_utility"].sum())
            result.setdefault(r, []).append(v)
    return result


def _plot_mechanism_lines(
    ax: plt.Axes,
    base_lbl: str,
    comm_lbl: str,
    base_dir: str,
    base_color: str,
    comm_color: str,
) -> Tuple[List[float], List[float]]:
    """Plot two lines (base + comm) on ax, return (base_means, comm_means)."""
    rounds = list(range(1, 11))
    result = {}
    for label, color, ls, marker in [
        (base_lbl, base_color, "-",  "o"),
        (comm_lbl, comm_color, "--", "s"),
    ]:
        df = _load(base_dir, label)
        if df.empty:
            result[label] = ([], [])
            continue
        rd  = _per_round_utility(df)
        ms  = [np.mean(rd[r]) for r in rounds]
        ss  = [np.std(rd[r], ddof=1) for r in rounds]
        x   = np.array(rounds, dtype=float)
        lbl = label.replace(", Comm", " +BComm")
        ax.plot(x, ms, color=color, ls=ls, lw=2.0, marker=marker,
                markersize=5, label=lbl, zorder=3)
        ax.fill_between(x, [m - s for m, s in zip(ms, ss)],
                        [m + s for m, s in zip(ms, ss)],
                        alpha=0.15, color=color)
        result[label] = (ms, ss)
    return result[base_lbl], result[comm_lbl]


def fig8_round_utility(base_dir: str, output_dir: Path) -> None:
    """1×2 subplots: per-round buyer utility, split by mechanism (appendix)."""

    fig, (ax_rep, ax_rw) = plt.subplots(
        1, 2, figsize=(11, 4.8),
        gridspec_kw={"wspace": 0.30},
        sharey=True,
    )
    fig.suptitle(
        "Buyer Communication Accelerates Convergence to Higher Utility",
        fontsize=11, fontweight="bold",
    )
    fig.subplots_adjust(top=0.88)

    rounds = list(range(1, 11))

    # ── Left: Rep mechanism ───────────────────────────────────────────────
    # Baseline Rep = gray (neutral, no strong mechanism)
    # Rep+BComm    = good_mid green (improvement from buyer comm)
    (base_ms, base_ss), (comm_ms, comm_ss) = _plot_mechanism_lines(
        ax_rep,
        base_lbl="Rep", comm_lbl="Rep, Comm",
        base_dir=base_dir,
        base_color=COLORS["neutral"],      # gray = neutral baseline
        comm_color=COLORS["good_mid"],     # green = comm brings improvement
    )

    # Per-round significance markers
    df_rep  = _load(base_dir, "Rep")
    df_repc = _load(base_dir, "Rep, Comm")
    if not df_rep.empty and not df_repc.empty:
        for r in rounds:
            v_r  = [float(df_rep [(df_rep ["run_id"] == rid) &
                                   (df_rep ["round_num"] == r)]["buyer_utility"].sum())
                    for rid in sorted(df_rep["run_id"].unique())]
            v_rc = [float(df_repc[(df_repc["run_id"] == rid) &
                                   (df_repc["round_num"] == r)]["buyer_utility"].sum())
                    for rid in sorted(df_repc["run_id"].unique())]
            sig = sig_marker_display(mannwhitney_p(v_r, v_rc))
            if sig and base_ms and comm_ms:
                y_mark = max(base_ms[r - 1] + base_ss[r - 1],
                             comm_ms[r - 1] + comm_ss[r - 1])
                ax_rep.text(float(r), y_mark + 1.0, sig,
                            ha="center", va="bottom", fontsize=8,
                            color=COLORS["good_mid"])

    # Annotation: gap at round 10
    if base_ms and comm_ms:
        lift = comm_ms[-1] - base_ms[-1]
        ax_rep.annotate(
            f"+{lift:.0f} utility\nfrom buyer comm",
            xy=(10, comm_ms[-1]),
            xytext=(7.8, comm_ms[-1] + 2.5),
            fontsize=8.5, color=COLORS["good_mid"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["good_mid"], lw=1.2),
        )

    ax_rep.set_title("Rep Mechanism: Effect of Buyer Communication",
                     fontsize=10, pad=4)
    ax_rep.set_xlabel("Market Round", fontsize=10)
    ax_rep.set_ylabel("Buyer Utility (per round, mean ± std)", fontsize=10)
    ax_rep.set_xticks(rounds)
    ax_rep.set_xlim(0.5, 10.8)
    ax_rep.legend(frameon=False, fontsize=9, loc="lower right")

    # ── Right: Rep+Warrant mechanism ─────────────────────────────────────
    # Rep+Warrant base = good_dark (strong mechanism, already good)
    # Rep+Warrant+BComm = good_dark dashed (marginal further improvement)
    (rw_ms, rw_ss), (rwc_ms, rwc_ss) = _plot_mechanism_lines(
        ax_rw,
        base_lbl="Rep+Warrant", comm_lbl="Rep+Warrant, Comm",
        base_dir=base_dir,
        base_color=COLORS["good_dark"],          # solid dark green
        comm_color=COLORS["good_dark"],          # same color, dashed
    )
    # Override: re-plot RW+Comm with slightly lighter shade for visibility
    ax_rw.lines[-1].set_color("#43a047")         # slightly lighter than good_dark
    ax_rw.collections[-1].set_facecolor("#43a047")

    # Per-round significance: RW vs RW+Comm
    df_rw  = _load(base_dir, "Rep+Warrant")
    df_rwc = _load(base_dir, "Rep+Warrant, Comm")
    if not df_rw.empty and not df_rwc.empty:
        for r in rounds:
            v_rw  = [float(df_rw [(df_rw ["run_id"] == rid) &
                                   (df_rw ["round_num"] == r)]["buyer_utility"].sum())
                     for rid in sorted(df_rw["run_id"].unique())]
            v_rwc = [float(df_rwc[(df_rwc["run_id"] == rid) &
                                   (df_rwc["round_num"] == r)]["buyer_utility"].sum())
                     for rid in sorted(df_rwc["run_id"].unique())]
            sig = sig_marker_display(mannwhitney_p(v_rw, v_rwc))
            if sig and rw_ms and rwc_ms:
                y_mark = max(rw_ms[r - 1] + rw_ss[r - 1],
                             rwc_ms[r - 1] + rwc_ss[r - 1])
                ax_rw.text(float(r), y_mark + 1.0, sig,
                           ha="center", va="bottom", fontsize=8,
                           color=COLORS["good_dark"])

    # Annotation: gap at round 10
    if rw_ms and rwc_ms:
        lift2 = rwc_ms[-1] - rw_ms[-1]
        if abs(lift2) >= 0.5:
            ax_rw.annotate(
                f"+{lift2:.0f} utility\n(+BComm)",
                xy=(10, rwc_ms[-1]),
                xytext=(7.8, rwc_ms[-1] + 2.5),
                fontsize=8.5, color="#43a047", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#43a047", lw=1.2),
            )

    ax_rw.set_title("Rep+Warrant Mechanism: Effect of Buyer Communication",
                    fontsize=10, pad=4)
    ax_rw.set_xlabel("Market Round", fontsize=10)
    ax_rw.set_xticks(rounds)
    ax_rw.set_xlim(0.5, 10.8)
    ax_rw.legend(frameon=False, fontsize=9, loc="lower right")

    # ── Shared y-axis range ───────────────────────────────────────────────
    all_ms = (base_ms or []) + (comm_ms or []) + (rw_ms or []) + (rwc_ms or [])
    if all_ms:
        ax_rep.set_ylim(min(all_ms) * 0.92, max(all_ms) * 1.14)

    add_sig_footnote(fig, extra="markers above line = Rep vs Rep+BComm significance per round")
    save_figure(fig, output_dir / "rq3_round_adaptation_appendix.png")
    print("  [Fig8] Round utility (split) figure saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate RQ3 figures for paper")
    parser.add_argument("--base-dir",
                        default="experiments/gpt-4o-mini/paper/rq3")
    parser.add_argument("--output-dir",
                        default="visualization/figs/paper/rq3")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("RQ3: Generating Paper Figures")
    print("=" * 60)

    print("\n[Fig7] 2×2 Market Outcomes…")
    fig7_market_outcomes(args.base_dir, output_dir)

    print("\n[Fig8] Round-level Buyer Utility, split by mechanism (appendix)…")
    fig8_round_utility(args.base_dir, output_dir)

    print("\n✅  RQ3 figures saved to:", output_dir)


if __name__ == "__main__":
    main()
