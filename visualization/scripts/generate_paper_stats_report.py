#!/usr/bin/env python3
"""
generate_paper_stats_report.py

Produces a complete statistical significance report for all paper tables.
Outputs both a plain-text summary and a LaTeX snippet with p-values that
can be included in the paper's appendix or used to verify table claims.

Usage:
    python visualization/scripts/generate_paper_stats_report.py \
        --base-dir experiments/gpt-4o/paper \
        --output-dir visualization/figs/gpt-4o/paper/stats

Output files:
    stats_report.txt       — human-readable summary with p-values and effect sizes
    stats_report.tex       — LaTeX table for paper appendix
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    load_results_df,
    per_run_values,
    count_deceptions,
    sum_seller_profit,
    sum_buyer_utility,
    honest_profit,
    dishonest_profit,
    mannwhitney_p,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(base_dir: Path, rel: str) -> pd.DataFrame:
    return load_results_df(str(base_dir / rel))


def _vals(df: pd.DataFrame, fn) -> List[float]:
    return per_run_values(df, fn) if not df.empty else []


def _stats(vals: List[float]) -> Tuple[float, float]:
    """Return (mean, std). Returns (nan, nan) if empty."""
    if not vals:
        return float("nan"), float("nan")
    a = np.array(vals, dtype=float)
    return float(a.mean()), float(a.std(ddof=1)) if len(a) > 1 else 0.0


def sig_stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def cohens_d(a: List[float], b: List[float]) -> float:
    """Compute Cohen's d effect size between two samples."""
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    na, nb = len(a), len(b)
    pooled_std = np.sqrt(
        ((na - 1) * np.std(a, ddof=1) ** 2 + (nb - 1) * np.std(b, ddof=1) ** 2)
        / (na + nb - 2)
    )
    if pooled_std == 0:
        return float("nan")
    return (np.mean(a) - np.mean(b)) / pooled_std


def fmt(mean: float, std: float) -> str:
    if np.isnan(mean):
        return "N/A"
    return f"{mean:.1f}±{std:.1f}"


# ── RQ1 Analysis ──────────────────────────────────────────────────────────────

def analyze_rq1(base_dir: Path) -> List[Dict]:
    """Compare Rep vs Rep+Warrant without communication."""
    rq1_dir = base_dir / "rq1"
    df_rep = _load(rq1_dir, "r_wo")
    df_rw  = _load(rq1_dir, "rw_wo")

    rows = []
    for metric_name, fn in [
        ("Seller Profit",  sum_seller_profit),
        ("Buyer Utility",  sum_buyer_utility),
        ("Deceptions",     count_deceptions),
    ]:
        a = _vals(df_rep, fn)
        b = _vals(df_rw,  fn)
        p = mannwhitney_p(a, b)
        ma, sa = _stats(a)
        mb, sb = _stats(b)
        rows.append({
            "RQ": "RQ1",
            "Comparison": "Rep vs Rep+Warrant",
            "Metric": metric_name,
            "Rep (mean±std)": fmt(ma, sa),
            "Rep+Warrant (mean±std)": fmt(mb, sb),
            "p-value": f"{p:.4f}",
            "Sig": sig_stars(p),
            "Cohen's d": f"{cohens_d(a, b):.2f}" if not np.isnan(cohens_d(a, b)) else "N/A",
            "n (Rep)": len(a),
            "n (RW)": len(b),
        })
    return rows


# ── RQ2 Analysis ──────────────────────────────────────────────────────────────

CONSTRAINTS = [
    ("policy_making",              "Policy-Making"),
    ("pressure_quickprofits",      "Pressure-Quick-Profits"),
    ("psychological-based-attack", "Psychological-Attack"),
]

RQ2_COMPARISONS = [
    # (label_a, dir_a, label_b, dir_b, description)
    ("Rep",          "r_wsc_F",  "Rep+Warrant",        "rw_wsc_F", "Rep vs Rep+Warrant (no comm)"),
    ("Rep, Comm",    "r_wsc_R",  "Rep+Warrant, Comm",  "rw_wsc_R", "Rep,Comm vs Rep+Warrant,Comm"),
    ("Rep",          "r_wsc_F",  "Rep, Comm",          "r_wsc_R",  "Rep: no-comm vs comm"),
    ("Rep+Warrant",  "rw_wsc_F", "Rep+Warrant, Comm",  "rw_wsc_R", "Rep+Warrant: no-comm vs comm"),
]


def analyze_rq2(base_dir: Path) -> List[Dict]:
    rq2_dir = base_dir / "rq2"
    rows = []

    for c_key, c_label in CONSTRAINTS:
        for la, da, lb, db, desc in RQ2_COMPARISONS:
            df_a = _load(rq2_dir, f"{da}_{c_key}")
            df_b = _load(rq2_dir, f"{db}_{c_key}")

            for metric_name, fn in [
                ("Seller Profit",    sum_seller_profit),
                ("Buyer Utility",    sum_buyer_utility),
                ("Deceptions",       count_deceptions),
                ("Dishonest Profit", dishonest_profit),
            ]:
                a = _vals(df_a, fn)
                b = _vals(df_b, fn)
                if not a or not b:
                    continue
                p = mannwhitney_p(a, b)
                ma, sa = _stats(a)
                mb, sb = _stats(b)
                rows.append({
                    "RQ": "RQ2",
                    "Constraint": c_label,
                    "Comparison": desc,
                    "Metric": metric_name,
                    f"{la} (mean±std)": fmt(ma, sa),
                    f"{lb} (mean±std)": fmt(mb, sb),
                    "p-value": f"{p:.4f}",
                    "Sig": sig_stars(p),
                    "Cohen's d": f"{cohens_d(a, b):.2f}" if not np.isnan(cohens_d(a, b)) else "N/A",
                    "n_a": len(a),
                    "n_b": len(b),
                })
    return rows


# ── RQ3 Analysis ──────────────────────────────────────────────────────────────

RQ3_DIRS = {
    "Rep":                "r_wbc_F",
    "Rep, Comm":          "r_wbc_R",
    "Rep+Warrant":        "rw_wbc_F",
    "Rep+Warrant, Comm":  "rw_wbc_R",
}

RQ3_COMPARISONS = [
    ("Rep",         "Rep, Comm",         "Rep: no buyer-comm vs buyer-comm"),
    ("Rep+Warrant", "Rep+Warrant, Comm", "Rep+Warrant: no buyer-comm vs buyer-comm"),
    ("Rep",         "Rep+Warrant",       "Mechanism: Rep vs Rep+Warrant (no comm)"),
    ("Rep, Comm",   "Rep+Warrant, Comm", "Mechanism: Rep,Comm vs Rep+Warrant,Comm"),
]


def analyze_rq3(base_dir: Path) -> List[Dict]:
    rq3_dir = base_dir / "rq3"
    rows = []

    for la, lb, desc in RQ3_COMPARISONS:
        df_a = _load(rq3_dir, RQ3_DIRS[la])
        df_b = _load(rq3_dir, RQ3_DIRS[lb])

        for metric_name, fn in [
            ("Seller Profit",  sum_seller_profit),
            ("Buyer Utility",  sum_buyer_utility),
            ("Deceptions",     count_deceptions),
        ]:
            a = _vals(df_a, fn)
            b = _vals(df_b, fn)
            if not a or not b:
                continue
            p = mannwhitney_p(a, b)
            ma, sa = _stats(a)
            mb, sb = _stats(b)
            rows.append({
                "RQ": "RQ3",
                "Comparison": desc,
                "Metric": metric_name,
                f"{la} (mean±std)": fmt(ma, sa),
                f"{lb} (mean±std)": fmt(mb, sb),
                "p-value": f"{p:.4f}",
                "Sig": sig_stars(p),
                "Cohen's d": f"{cohens_d(a, b):.2f}" if not np.isnan(cohens_d(a, b)) else "N/A",
                "n_a": len(a),
                "n_b": len(b),
            })
    return rows


# ── Text Report ───────────────────────────────────────────────────────────────

def write_text_report(all_rows: List[Dict], output_path: Path) -> None:
    lines = [
        "=" * 80,
        "STATISTICAL SIGNIFICANCE REPORT",
        "Test: Mann-Whitney U (two-sided) | Effect size: Cohen's d",
        "Significance: * p<0.05  ** p<0.01  *** p<0.001  ns = not significant",
        "=" * 80,
        "",
    ]

    current_rq = None
    current_constraint = None

    for r in all_rows:
        rq = r.get("RQ", "")
        constraint = r.get("Constraint", "")

        if rq != current_rq:
            lines.append("")
            lines.append(f"{'─' * 70}")
            lines.append(f"  {rq}")
            lines.append(f"{'─' * 70}")
            current_rq = rq
            current_constraint = None

        if constraint and constraint != current_constraint:
            lines.append(f"\n  Constraint: {constraint}")
            current_constraint = constraint

        comp = r.get("Comparison", "")
        metric = r.get("Metric", "")
        p_val = r.get("p-value", "")
        sig = r.get("Sig", "")
        d = r.get("Cohen's d", "")

        # Find the two condition columns dynamically
        cond_cols = [k for k in r if "mean±std" in k]
        cond_str = ""
        if len(cond_cols) >= 2:
            cond_str = f"  {cond_cols[0].split('(')[0].strip()}: {r[cond_cols[0]]}  |  {cond_cols[1].split('(')[0].strip()}: {r[cond_cols[1]]}"

        lines.append(f"  [{metric:20s}]  p={p_val}  {sig:3s}  d={d:6s}  —  {comp}")
        if cond_str:
            lines.append(f"    {cond_str}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("NOTE: n=5 runs per condition. Low n may limit power for small effects.")
    lines.append("=" * 80)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Text report saved: {output_path}")


# ── LaTeX Report ─────────────────────────────────────────────────────────────

def write_latex_report(all_rows: List[Dict], output_path: Path) -> None:
    """
    Write a compact LaTeX table of p-values, grouped by RQ and metric.
    Designed to be included in the paper appendix.
    """
    lines = [
        "% Auto-generated statistical significance table",
        "% Significance: * p<0.05, ** p<0.01, *** p<0.001, ns = not significant",
        r"\begin{table*}[ht]",
        r"\centering",
        r"\small",
        r"\caption{Statistical Significance of Key Comparisons (Mann-Whitney U Test)}",
        r"\label{tab:stats_significance}",
        r"\begin{tabular}{lllrrl}",
        r"\toprule",
        r"\textbf{RQ} & \textbf{Constraint} & \textbf{Comparison} & "
        r"\textbf{Metric} & \textbf{$p$-value} & \textbf{Sig.} \\",
        r"\midrule",
    ]

    current_rq = None
    for r in all_rows:
        rq = r.get("RQ", "")
        constraint = r.get("Constraint", "—")
        comp = r.get("Comparison", "").replace("&", r"\&").replace("%", r"\%")
        metric = r.get("Metric", "")
        p_val = r.get("p-value", "")
        sig = r.get("Sig", "")

        # Format p-value
        try:
            p_float = float(p_val)
            if p_float < 0.001:
                p_fmt = r"$<$0.001"
            else:
                p_fmt = f"{p_float:.3f}"
        except ValueError:
            p_fmt = p_val

        sig_latex = sig if sig == "ns" else f"\\textbf{{{sig}}}"

        if rq != current_rq:
            if current_rq is not None:
                lines.append(r"\midrule")
            current_rq = rq

        row = f"{rq} & {constraint} & {comp} & {metric} & {p_fmt} & {sig_latex} \\\\"
        lines.append(row)

    lines += [
        r"\bottomrule",
        r"\multicolumn{6}{l}{\footnotesize * $p<0.05$, ** $p<0.01$, *** $p<0.001$, ns = not significant} \\",
        r"\multicolumn{6}{l}{\footnotesize $n=5$ independent runs per condition. "
        r"Effect sizes (Cohen's $d$) reported in text report.} \\",
        r"\end{tabular}",
        r"\end{table*}",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  LaTeX report saved: {output_path}")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate statistical significance report for all paper comparisons"
    )
    parser.add_argument(
        "--base-dir",
        default="experiments/gpt-4o/paper",
        help="Root directory containing rq1/, rq2/, rq3/ subdirectories",
    )
    parser.add_argument(
        "--output-dir",
        default="visualization/figs/gpt-4o/paper/stats",
        help="Directory for output files",
    )
    parser.add_argument(
        "--rq",
        choices=["rq1", "rq2", "rq3", "all"],
        default="all",
        help="Which RQ to analyze (default: all)",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Statistical Significance Report Generator")
    print(f"Base dir : {base_dir}")
    print(f"Output   : {output_dir}")
    print("=" * 60)

    all_rows: List[Dict] = []

    if args.rq in ("rq1", "all"):
        print("\n[RQ1] Mechanism Effectiveness...")
        rows = analyze_rq1(base_dir)
        all_rows.extend(rows)
        print(f"  {len(rows)} comparisons computed.")

    if args.rq in ("rq2", "all"):
        print("\n[RQ2] Seller Communication...")
        rows = analyze_rq2(base_dir)
        all_rows.extend(rows)
        print(f"  {len(rows)} comparisons computed.")

    if args.rq in ("rq3", "all"):
        print("\n[RQ3] Buyer Communication...")
        rows = analyze_rq3(base_dir)
        all_rows.extend(rows)
        print(f"  {len(rows)} comparisons computed.")

    if not all_rows:
        print("\nNo data found. Check that experiment directories exist.")
        return

    write_text_report(all_rows, output_dir / "stats_report.txt")
    write_latex_report(all_rows, output_dir / "stats_report.tex")

    # Also dump as CSV for manual inspection
    csv_path = output_dir / "stats_report.csv"
    pd.DataFrame(all_rows).to_csv(csv_path, index=False)
    print(f"  CSV dump saved: {csv_path}")

    print(f"\n✅  Statistical report complete. Files in: {output_dir}")


if __name__ == "__main__":
    main()
