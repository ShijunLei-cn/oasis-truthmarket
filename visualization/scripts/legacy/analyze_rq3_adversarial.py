#!/usr/bin/env python3
"""
Compute RQ3 adversarial stats:
  Baseline: RQ2 seller-only Real + PQP conditions
    - Rep:   experiments/gpt-4o-mini/paper/rq2/r_wsc_R_pressure_quickprofits
    - RW:    experiments/gpt-4o-mini/paper/rq2/rw_wsc_R_pressure_quickprofits
  Treatment: new RQ3 both-comm Real + PQP conditions
    - Rep:   experiments/gpt-4o-mini/paper/rq3/r_both_R_pqp
    - RW:    experiments/gpt-4o-mini/paper/rq3/rw_both_R_pqp
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    load_results_df, per_run_values,
    count_deceptions, sum_seller_profit, sum_buyer_utility,
    mannwhitney_p,
)

BASE = Path("experiments/gpt-4o-mini/paper")

DIRS = {
    "Rep_base":      BASE / "rq2/r_wsc_R_pressure_quickprofits",
    "RW_base":       BASE / "rq2/rw_wsc_R_pressure_quickprofits",
    "Rep_treatment": BASE / "rq3/r_both_R_pqp",
    "RW_treatment":  BASE / "rq3/rw_both_R_pqp",
}

def _transactions(run_df):
    return float(run_df["transactions"].sum())

def stats(vals):
    a = np.array(vals, dtype=float)
    return a.mean(), a.std(ddof=1) if len(a) > 1 else 0.0

def cohens_d(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    pooled = np.sqrt(((na-1)*np.std(a,ddof=1)**2 + (nb-1)*np.std(b,ddof=1)**2)/(na+nb-2))
    if pooled == 0:
        return float("nan")
    return (np.mean(a) - np.mean(b)) / pooled

def sig(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

data = {}
for label, d in DIRS.items():
    df = load_results_df(str(d))
    if df.empty:
        print(f"WARNING: {label} is empty from {d}")
        data[label] = {}
        continue
    data[label] = {
        "profit":       per_run_values(df, sum_seller_profit),
        "utility":      per_run_values(df, sum_buyer_utility),
        "transactions": per_run_values(df, _transactions),
        "deceptions":   per_run_values(df, count_deceptions),
    }
    print(f"Loaded {label}: {len(data[label]['profit'])} runs")

print()
print("="*70)
print("RQ3 ADVERSARIAL STATS")
print("="*70)
print()

for mech, base_key, trt_key in [("Rep", "Rep_base", "Rep_treatment"),
                                  ("RW",  "RW_base",  "RW_treatment")]:
    print(f"--- {mech} Mechanism ---")
    for metric in ["profit", "utility", "transactions", "deceptions"]:
        if base_key not in data or trt_key not in data:
            continue
        b = data[base_key].get(metric, [])
        t = data[trt_key].get(metric, [])
        if not b or not t:
            continue
        bm, bs = stats(b)
        tm, ts = stats(t)
        p = mannwhitney_p(b, t)
        d = cohens_d(t, b)
        print(f"  {metric:15s}: Base={bm:.1f}±{bs:.1f}  Treatment={tm:.1f}±{ts:.1f}  "
              f"p={p:.4f}{sig(p)}  d={d:.2f}")
    print()

# Summary table for paper
print()
print("="*70)
print("LATEX TABLE VALUES")
print("="*70)
print()
print("Condition     | Transactions | Profit        | Utility       | Deceptions")
print("-"*70)
for label, key in [("Rep, S-Only (baseline)", "Rep_base"),
                    ("Rep, Both (treatment)", "Rep_treatment"),
                    ("RW,  S-Only (baseline)", "RW_base"),
                    ("RW,  Both (treatment)", "RW_treatment")]:
    if key not in data or not data[key]:
        print(f"{label}: NO DATA")
        continue
    d = data[key]
    tm, ts = stats(d.get("transactions", [0]))
    pm, ps = stats(d.get("profit", [0]))
    um, us = stats(d.get("utility", [0]))
    dm, ds = stats(d.get("deceptions", [0]))
    print(f"{label[:30]:30s}: {tm:.1f}±{ts:.1f}  {pm:.1f}±{ps:.1f}  {um:.1f}±{us:.1f}  {dm:.1f}±{ds:.1f}")

# p-values for paper claims
print()
print("Key p-values (treatment vs baseline, same mechanism):")
for mech, base_key, trt_key in [("Rep", "Rep_base", "Rep_treatment"),
                                  ("RW",  "RW_base",  "RW_treatment")]:
    for metric in ["profit", "utility", "deceptions"]:
        b = data.get(base_key, {}).get(metric, [])
        t = data.get(trt_key, {}).get(metric, [])
        if b and t:
            p = mannwhitney_p(b, t)
            d = cohens_d(t, b)
            print(f"  {mech} {metric}: p={p:.4f}{sig(p)}, d={d:.2f}")
