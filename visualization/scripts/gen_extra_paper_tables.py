#!/usr/bin/env python3
"""
Generate additional tables for the arxiv paper appendix:
1. Profit Decomposition (Honest vs Dishonest) — RQ2 + RQ3
2. Cross-RQ Comprehensive Summary — all conditions

Usage:
    python visualization/scripts/gen_extra_paper_tables.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    load_results_df,
    per_run_values,
    sum_seller_profit,
    sum_buyer_utility,
    count_deceptions,
    honest_profit,
    dishonest_profit,
    honest_buyer_utility,
    dishonest_buyer_utility,
)

import numpy as np

BASE = Path("experiments/gpt-4o/paper_important_results")


def _stats(vals):
    if not vals:
        return float("nan"), float("nan")
    a = np.array(vals, dtype=float)
    return float(a.mean()), float(a.std(ddof=1)) if len(a) > 1 else 0.0


def fmt(m, s):
    if np.isnan(m):
        return "N/A"
    return f"{m:.1f}±{s:.1f}"


def fmt_pct(m, s):
    if np.isnan(m):
        return "N/A"
    return f"{m:.1f}±{s:.1f}\\%"


# ──────────────────────────────────────────────
# TABLE 1: Profit Decomposition
# ──────────────────────────────────────────────

CONDITIONS_RQ2 = [
    ("Rep", "rq2_welfare/r_wo"),
    ("Rep+Warrant", "rq2_welfare/rw_wo"),
]

# NOTE: The paper_important_results tables use the OLD naming convention dirs.
# New naming dirs (platform_fee, price_war, financial_distress) contain different data.
CONDITIONS_RQ3 = [
    ("Rep", "rq3_resilience/r_wsc_R_policy_making"),
    ("Rep+Warrant", "rq3_resilience/rw_wsc_R_policy_making"),
    ("Rep", "rq3_resilience/r_wsc_R_pressure_quickprofits"),
    ("Rep+Warrant", "rq3_resilience/rw_wsc_R_pressure_quickprofits"),
    ("Rep", "rq3_resilience/r_wsc_R_psychological-based-attack"),
    ("Rep+Warrant", "rq3_resilience/rw_wsc_R_psychological-based-attack"),
]

PRESSURE_LABELS = {
    "policy_making": "Platform-Fee",
    "pressure_quickprofits": "Price-War",
    "psychological-based-attack": "Financial-Distress",
}


def gen_profit_decomp_table():
    """Generate Profit Decomposition table (Honest vs Dishonest Profit)."""
    lines = []
    lines.append(r"\begin{table*}[!h]")
    lines.append(r"    \centering")
    lines.append(r"    \small")
    lines.append(r"    \caption{RQ2 \& RQ3: Profit Decomposition — Honest vs Dishonest Seller Profit across Conditions (mean$\pm$std across runs).}")
    lines.append(r"    \label{tab:profit_decomposition}")
    lines.append(r"    \begin{tabular}{llccccc}")
    lines.append(r"    \toprule")
    lines.append(r"    \textbf{RQ} & \textbf{Condition} & \textbf{Total Profit} & \textbf{Honest Profit} & \textbf{Dishonest Profit} & \textbf{Dishonest \%} & \textbf{Deceptions} \\")
    lines.append(r"    \midrule")

    # RQ2
    lines.append(r"    \multicolumn{7}{l}{\textbf{RQ2: Baseline (No Economic Pressure)}} \\")
    for label, path in CONDITIONS_RQ2:
        df = load_results_df(str(BASE / path))
        if df.empty:
            continue
        tot_vals = per_run_values(df, sum_seller_profit)
        hon_vals = per_run_values(df, honest_profit)
        dis_vals = per_run_values(df, dishonest_profit)
        dec_vals = per_run_values(df, count_deceptions)

        m_tot, s_tot = _stats(tot_vals)
        m_hon, s_hon = _stats(hon_vals)
        m_dis, s_dis = _stats(dis_vals)
        m_dec, s_dec = _stats(dec_vals)

        # Dishonest %
        pcts = [100.0 * d / t if t > 0 else 0.0 for d, t in zip(dis_vals, tot_vals)]
        m_pct, s_pct = _stats(pcts)

        lines.append(f"    \\quad {label} & {fmt(m_tot, s_tot)} & {fmt(m_hon, s_hon)} & {fmt(m_dis, s_dis)} & {fmt_pct(m_pct, s_pct)} & {fmt(m_dec, s_dec)} \\\\")

    lines.append(r"    \midrule")
    lines.append(r"    \multicolumn{7}{l}{\textbf{RQ3: Economic Pressure Scenarios}} \\")

    # RQ3 - grouped by pressure
    current_pressure = None
    for label, path in CONDITIONS_RQ3:
        # Extract pressure name from path
        for p_key, p_label in PRESSURE_LABELS.items():
            if p_key in path:
                if p_label != current_pressure:
                    current_pressure = p_label
                    lines.append(f"    \\multicolumn{{7}}{{l}}{{\\textbf{{{p_label}}}}} \\\\")
                break

        df = load_results_df(str(BASE / path))
        if df.empty:
            continue
        tot_vals = per_run_values(df, sum_seller_profit)
        hon_vals = per_run_values(df, honest_profit)
        dis_vals = per_run_values(df, dishonest_profit)
        dec_vals = per_run_values(df, count_deceptions)

        m_tot, s_tot = _stats(tot_vals)
        m_hon, s_hon = _stats(hon_vals)
        m_dis, s_dis = _stats(dis_vals)
        m_dec, s_dec = _stats(dec_vals)

        pcts = [100.0 * d / t if t > 0 else 0.0 for d, t in zip(dis_vals, tot_vals)]
        m_pct, s_pct = _stats(pcts)

        lines.append(f"    \\quad {label} & {fmt(m_tot, s_tot)} & {fmt(m_hon, s_hon)} & {fmt(m_dis, s_dis)} & {fmt_pct(m_pct, s_pct)} & {fmt(m_dec, s_dec)} \\\\")

    lines.append(r"    \bottomrule")
    lines.append(r"    \end{tabular}")
    lines.append(r"\end{table*}")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# TABLE 2: Cross-RQ Comprehensive Summary
# ──────────────────────────────────────────────

def gen_cross_rq_summary():
    """Generate cross-RQ summary table with key metrics for all conditions."""
    lines = []
    lines.append(r"\begin{table*}[!h]")
    lines.append(r"    \centering")
    lines.append(r"    \small")
    lines.append(r"    \caption{Comprehensive Summary: Key Metrics across All Experimental Conditions (mean$\pm$std across 5 runs).}")
    lines.append(r"    \label{tab:cross_rq_summary}")
    lines.append(r"    \begin{tabular}{llccccc}")
    lines.append(r"    \toprule")
    lines.append(r"    \textbf{RQ} & \textbf{Condition} & \textbf{Transactions} & \textbf{Profit (Seller)} & \textbf{Utility (Buyer)} & \textbf{Deceptions} & \textbf{HQ Counterfeit} \\")
    lines.append(r"    \midrule")

    all_conditions = [
        ("RQ2", "Rep", "rq2_welfare/r_wo"),
        ("RQ2", "Rep+Warrant", "rq2_welfare/rw_wo"),
        ("RQ3", "Rep (Platform-Fee)", "rq3_resilience/r_wsc_R_policy_making"),
        ("RQ3", "Rep+Warrant (Platform-Fee)", "rq3_resilience/rw_wsc_R_policy_making"),
        ("RQ3", "Rep (Price-War)", "rq3_resilience/r_wsc_R_pressure_quickprofits"),
        ("RQ3", "Rep+Warrant (Price-War)", "rq3_resilience/rw_wsc_R_pressure_quickprofits"),
        ("RQ3", "Rep (Financial-Distress)", "rq3_resilience/r_wsc_R_psychological-based-attack"),
        ("RQ3", "Rep+Warrant (Financial-Distress)", "rq3_resilience/rw_wsc_R_psychological-based-attack"),
    ]

    current_rq = None
    for rq, label, path in all_conditions:
        if rq != current_rq:
            if current_rq is not None:
                lines.append(r"    \midrule")
            current_rq = rq

        df = load_results_df(str(BASE / path))
        if df.empty:
            lines.append(f"    {rq} & {label} & N/A & N/A & N/A & N/A & N/A \\\\")
            continue

        txn_vals = per_run_values(df, lambda x: float(len(x)))
        prf_vals = per_run_values(df, sum_seller_profit)
        utl_vals = per_run_values(df, sum_buyer_utility)
        dec_vals = per_run_values(df, count_deceptions)
        hq_fake_vals = per_run_values(df, lambda x: float((x["is_honest"] == False).sum()))

        m_txn, s_txn = _stats(txn_vals)
        m_prf, s_prf = _stats(prf_vals)
        m_utl, s_utl = _stats(utl_vals)
        m_dec, s_dec = _stats(dec_vals)
        m_hq, s_hq = _stats(hq_fake_vals)

        lines.append(f"    {rq} & {label} & {fmt(m_txn, s_txn)} & {fmt(m_prf, s_prf)} & {fmt(m_utl, s_utl)} & {fmt(m_dec, s_dec)} & {fmt(m_hq, s_hq)} \\\\")

    lines.append(r"    \bottomrule")
    lines.append(r"    \end{tabular}")
    lines.append(r"\end{table*}")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Generating extra paper tables...")
    print("=" * 60)

    print("\n--- Profit Decomposition Table ---\n")
    t1 = gen_profit_decomp_table()
    print(t1)

    print("\n--- Cross-RQ Summary Table ---\n")
    t2 = gen_cross_rq_summary()
    print(t2)

    # Save
    out_dir = Path("tables/gpt-4o/paper_important_results")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tab_profit_decomposition.tex").write_text(t1)
    (out_dir / "tab_cross_rq_summary.tex").write_text(t2)
    print(f"\nTables saved to: {out_dir.resolve()}")
