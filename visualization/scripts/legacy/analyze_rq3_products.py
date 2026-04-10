#!/usr/bin/env python3
"""Compute product quality stats for RQ3 adversarial conditions."""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import load_results_df, per_run_values

BASE = Path("experiments/gpt-4o-mini/paper")

DIRS = {
    "Rep, S-Only":  BASE / "rq2/r_wsc_R_pressure_quickprofits",
    "Rep, Both":    BASE / "rq3/r_both_R_pqp",
    "RW, S-Only":   BASE / "rq2/rw_wsc_R_pressure_quickprofits",
    "RW, Both":     BASE / "rq3/rw_both_R_pqp",
}

def product_stats(run_df):
    """Return dict of product quality counts for a single run."""
    aq = "actual_quality" if "actual_quality" in run_df.columns else "quality"
    adq = "advertised_quality"
    sold_col = "sold" if "sold" in run_df.columns else "is_sold"

    if aq not in run_df.columns or adq not in run_df.columns:
        return {}

    df = run_df.copy()
    df[aq] = df[aq].astype(str).str.upper().str.strip()
    df[adq] = df[adq].astype(str).str.upper().str.strip()
    sold = df[sold_col] == True

    hq_auth_on_sale = float(((df[adq]=="HQ") & (df[aq]=="HQ")).sum())
    hq_auth_sold    = float(((df[adq]=="HQ") & (df[aq]=="HQ") & sold).sum())
    lq_auth_on_sale = float(((df[adq]=="LQ") & (df[aq]=="LQ")).sum())
    lq_auth_sold    = float(((df[adq]=="LQ") & (df[aq]=="LQ") & sold).sum())
    hq_cfeit_on_sale = float(((df[adq]=="HQ") & (df[aq]=="LQ")).sum())
    hq_cfeit_sold    = float(((df[adq]=="HQ") & (df[aq]=="LQ") & sold).sum())

    return {
        "hq_auth_on_sale": hq_auth_on_sale,
        "hq_auth_sold": hq_auth_sold,
        "lq_auth_on_sale": lq_auth_on_sale,
        "lq_auth_sold": lq_auth_sold,
        "hq_cfeit_on_sale": hq_cfeit_on_sale,
        "hq_cfeit_sold": hq_cfeit_sold,
    }

def per_run_product_stats(df):
    results = {}
    for rid in sorted(df["run_id"].unique()):
        rdf = df[df["run_id"] == rid]
        s = product_stats(rdf)
        for k, v in s.items():
            results.setdefault(k, []).append(v)
    return results

def fmt(vals):
    a = np.array(vals, dtype=float)
    return f"{a.mean():.1f}±{a.std(ddof=1):.1f}"

print("Product Quality Stats for RQ3 Adversarial Design")
print("="*70)
for label, d in DIRS.items():
    df = load_results_df(str(d))
    if df.empty:
        print(f"{label}: NO DATA")
        continue
    s = per_run_product_stats(df)
    print(f"\n{label}:")
    print(f"  HQ Auth: on_sale={fmt(s['hq_auth_on_sale'])}, sold={fmt(s['hq_auth_sold'])}")
    print(f"  LQ Auth: on_sale={fmt(s['lq_auth_on_sale'])}, sold={fmt(s['lq_auth_sold'])}")
    print(f"  HQ Cfeit: on_sale={fmt(s['hq_cfeit_on_sale'])}, sold={fmt(s['hq_cfeit_sold'])}")

print()
print("="*70)
print("LATEX TABLE (tab:rq3_product_quality):")
print("="*70)
print(r"\begin{tabular}{ccccccc}")
print(r"\toprule")
print(r"\textbf{Condition} & \multicolumn{2}{c}{HQ Authentic} & \multicolumn{2}{c}{LQ Authentic} & \multicolumn{2}{c}{HQ Counterfeit} \\")
print(r" & On sale & Sold & On sale & Sold & On sale & Sold \\")
print(r"\midrule")
for label, d in DIRS.items():
    df = load_results_df(str(d))
    if df.empty:
        continue
    s = per_run_product_stats(df)
    print(f"{label} & {fmt(s['hq_auth_on_sale'])} & {fmt(s['hq_auth_sold'])} & {fmt(s['lq_auth_on_sale'])} & {fmt(s['lq_auth_sold'])} & {fmt(s['hq_cfeit_on_sale'])} & {fmt(s['hq_cfeit_sold'])} \\\\")
print(r"\bottomrule")
print(r"\end{tabular}")
