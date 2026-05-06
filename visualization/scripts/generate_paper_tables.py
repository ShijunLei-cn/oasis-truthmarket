#!/usr/bin/env python3
"""
Generate LaTeX tables for the experiment section from result directories.

Targets the table layouts used in:
overleaf_truthmarket/sections/04_experiments.tex
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from fig_utils import (
    load_results_df,
    load_probes_df,
    per_run_values,
    sum_seller_profit,
    sum_buyer_utility,
    count_deceptions,
    product_quality_counts,
    product_quality_counts_all,
)


def _mean_std(vals: List[float]) -> Tuple[float | None, float | None]:
    if not vals:
        return None, None
    arr = np.array(vals, dtype=float)
    m = float(np.mean(arr))
    s = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    return m, s


def _fmt_ms(m: float | None, s: float | None, precision: int = 1) -> str:
    if m is None or s is None:
        return "--"
    return f"{m:.{precision}f}±{s:.{precision}f}"


def _bold(x: str) -> str:
    return f"\\textbf{{{x}}}"


def _run_stats(exp_dir: Path) -> Dict[str, Tuple[float | None, float | None]]:
    df = load_results_df(str(exp_dir))
    if df.empty:
        return {
            "transactions": (None, None),
            "seller_profit": (None, None),
            "buyer_utility": (None, None),
            "deceptions": (None, None),
        }
    tx_vals = per_run_values(df, lambda d: float(len(d)))
    profit_vals = per_run_values(df, sum_seller_profit)
    utility_vals = per_run_values(df, sum_buyer_utility)
    deception_vals = per_run_values(df, count_deceptions)
    return {
        "transactions": _mean_std(tx_vals),
        "seller_profit": _mean_std(profit_vals),
        "buyer_utility": _mean_std(utility_vals),
        "deceptions": _mean_std(deception_vals),
    }


def _quality_stats(exp_dir: Path) -> Dict[str, Tuple[float | None, float | None]]:
    df = load_results_df(str(exp_dir))
    if df.empty:
        keys = [
            "hq_auth_on_sale",
            "hq_auth_sold",
            "lq_auth_on_sale",
            "lq_auth_sold",
            "hq_fake_on_sale",
            "hq_fake_sold",
        ]
        return {k: (None, None) for k in keys}

    listed = per_run_values(df, product_quality_counts_all)  # tuple hq_auth,lq_auth,hq_fake
    sold = per_run_values(df, product_quality_counts)

    def _idx(vals: List[Tuple[float, float, float]], i: int) -> List[float]:
        return [float(v[i]) for v in vals]

    return {
        "hq_auth_on_sale": _mean_std(_idx(listed, 0)),
        "hq_auth_sold": _mean_std(_idx(sold, 0)),
        "lq_auth_on_sale": _mean_std(_idx(listed, 1)),
        "lq_auth_sold": _mean_std(_idx(sold, 1)),
        "hq_fake_on_sale": _mean_std(_idx(listed, 2)),
        "hq_fake_sold": _mean_std(_idx(sold, 2)),
    }


def _probe_stats(exp_dir: Path) -> Dict[str, Tuple[float | None, float | None]]:
    df = load_probes_df(str(exp_dir))
    if df.empty:
        return {k: (None, None) for k in ["IW", "RL", "VI", "RE", "ES"]}
    vuln_map = {
        "IW": "initial_window",
        "RL": "reputation_lag",
        "VI": "value_imbalance",
        "RE": "reentry",
        "ES": "exit_strategy",
    }
    out: Dict[str, Tuple[float | None, float | None]] = {}
    for short, key in vuln_map.items():
        per_run = []
        for rid in sorted(df["run_id"].unique()):
            sub = df[(df["run_id"] == rid) & (df["vulnerability_type"] == key)]
            # per-run detected sample count
            per_run.append(float((sub["manipulation_detected"] == True).sum()))  # noqa: E712
        out[short] = _mean_std(per_run)
    return out


def _probe_rate_stats(exp_dir: Path) -> Dict[str, Tuple[float | None, float | None]]:
    df = load_probes_df(str(exp_dir))
    if df.empty:
        return {k: (None, None) for k in ["IW", "RL", "VI", "RE", "ES"]}
    vuln_map = {
        "IW": "initial_window",
        "RL": "reputation_lag",
        "VI": "value_imbalance",
        "RE": "reentry",
        "ES": "exit_strategy",
    }
    out: Dict[str, Tuple[float | None, float | None]] = {}
    for short, key in vuln_map.items():
        per_run = []
        for rid in sorted(df["run_id"].unique()):
            sub = df[(df["run_id"] == rid) & (df["vulnerability_type"] == key)]
            if len(sub) == 0:
                per_run.append(0.0)
            else:
                per_run.append(float((sub["manipulation_detected"] == True).mean() * 100.0))  # noqa: E712
        out[short] = _mean_std(per_run)
    return out


def _rq1_action_intent_stats(exp_dir: Path) -> Dict[str, Tuple[float | None, float | None]]:
    path = Path(exp_dir)
    files = sorted(path.glob("run_*_actions.json"))
    if not files:
        return {
            "seller_decisions": (None, None),
            "reentry_actions": (None, None),
            "hq_to_lq_units": (None, None),
            "hq_to_lq_share_pct": (None, None),
        }

    seller_decisions, reentry_actions, hq_to_lq_units, hq_to_lq_share = [], [], [], []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        run_decisions = 0.0
        run_reentry = 0.0
        run_hq_to_lq = 0.0
        run_total_units = 0.0
        for rec in data:
            if rec.get("phase") != "seller_listing":
                continue
            for ai in rec.get("agent_infos", []):
                name = str(ai.get("agent_name", ""))
                if not name.startswith("seller_"):
                    continue
                run_decisions += 1.0
                info = ai.get("agent_action_info", {})
                action = info.get("action_name")
                if action == "reenter_market":
                    run_reentry += 1.0
                    continue
                if action != "list_products":
                    continue
                args = info.get("action_args")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                for p in (args or {}).get("products", []):
                    q = float(p.get("quantity", 1))
                    aq = str(p.get("advertised_quality", "")).upper().strip()
                    tq = str(p.get("product_quality", "")).upper().strip()
                    run_total_units += q
                    if aq == "HQ" and tq == "LQ":
                        run_hq_to_lq += q
        seller_decisions.append(run_decisions)
        reentry_actions.append(run_reentry)
        hq_to_lq_units.append(run_hq_to_lq)
        hq_to_lq_share.append((run_hq_to_lq / run_total_units * 100.0) if run_total_units > 0 else 0.0)

    return {
        "seller_decisions": _mean_std(seller_decisions),
        "reentry_actions": _mean_std(reentry_actions),
        "hq_to_lq_units": _mean_std(hq_to_lq_units),
        "hq_to_lq_share_pct": _mean_std(hq_to_lq_share),
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"  Saved table: {path}")


def _maybe_bold_max(row_map: Dict[str, str], numeric_map: Dict[str, float | None], keys: List[str]) -> Dict[str, str]:
    vals = [numeric_map.get(k) for k in keys if numeric_map.get(k) is not None]
    if not vals:
        return row_map
    max_v = max(vals)
    for k in keys:
        v = numeric_map.get(k)
        if v is not None and np.isclose(v, max_v):
            row_map[k] = _bold(row_map[k])
    return row_map


def generate_rq1_tables(base_dir: Path, out_dir: Path) -> None:
    """New RQ1: vulnerability intent in reputation-only market."""
    rq1_rep = base_dir / "rq1_intent" / "r_wo"
    probes = _probe_stats(rq1_rep)
    rates = _probe_rate_stats(rq1_rep)
    actions = _rq1_action_intent_stats(rq1_rep)

    t1 = rf"""
\begin{{table*}}[t]
    \centering
    \small
    \caption{{RQ1 (Intent, Rep-Only): Vulnerability-Related Signals from Cognitive Probes and Actions (mean$\pm$std across runs).}}
    \label{{tab:rq1_intent_rep_only}}
    \begin{{tabular}}{{lcc}}
    \toprule
    \textbf{{Metric}} & \textbf{{Detected Count / Run}} & \textbf{{Detection Rate (\%) / Run}} \\
    \midrule
    Initial Window (IW) & {_fmt_ms(*probes["IW"])} & {_fmt_ms(*rates["IW"])} \\
    Reputation Lag (RL) & {_fmt_ms(*probes["RL"])} & {_fmt_ms(*rates["RL"])} \\
    Value Imbalance (VI) & {_fmt_ms(*probes["VI"])} & {_fmt_ms(*rates["VI"])} \\
    Re-entry (RE) & {_fmt_ms(*probes["RE"])} & {_fmt_ms(*rates["RE"])} \\
    Exit Strategy (ES) & {_fmt_ms(*probes["ES"])} & {_fmt_ms(*rates["ES"])} \\
    \midrule
    Seller Decisions / Run & {_fmt_ms(*actions["seller_decisions"])} & -- \\
    Re-entry Actions / Run & {_fmt_ms(*actions["reentry_actions"])} & -- \\
    HQ$\rightarrow$LQ Listed Units / Run & {_fmt_ms(*actions["hq_to_lq_units"])} & {_fmt_ms(*actions["hq_to_lq_share_pct"])} \\
    \bottomrule
    \end{{tabular}}
\end{{table*}}
"""
    _write(out_dir / "rq1" / "tab_rq1_intent_rep_only.tex", t1)


def generate_rq2_tables(base_dir: Path, out_dir: Path) -> None:
    """New RQ2: warrant welfare comparison in no-communication market."""
    rq2_base = base_dir / "rq2_welfare"
    rep = _run_stats(rq2_base / "r_wo")
    rw = _run_stats(rq2_base / "rw_wo")
    q_rep = _quality_stats(rq2_base / "r_wo")
    q_rw = _quality_stats(rq2_base / "rw_wo")

    t1 = rf"""
\begin{{table*}}[!h]
    \centering
    \small
    \caption{{RQ2 (Welfare): Rep vs Rep+Warrant under no communication (mean$\pm$std across runs).}}
    \label{{tab:rq2_welfare_summary}}
    \begin{{tabular}}{{lcccc}}
    \toprule
    \textbf{{Condition}} & \textbf{{Transactions}} & \textbf{{Profit (Seller)}} & \textbf{{Utility (Buyer)}} & \textbf{{Deceptions}} \\
    \midrule
    Rep         & {_fmt_ms(*rep["transactions"])} & {_fmt_ms(*rep["seller_profit"])} & {_fmt_ms(*rep["buyer_utility"])} & {_fmt_ms(*rep["deceptions"])} \\
    Rep+Warrant & {_fmt_ms(*rw["transactions"])} & {_fmt_ms(*rw["seller_profit"])} & {_fmt_ms(*rw["buyer_utility"])} & {_fmt_ms(*rw["deceptions"])} \\
    \bottomrule
    \end{{tabular}}
\end{{table*}}
"""
    _write(out_dir / "rq2" / "tab_rq2_welfare_summary.tex", t1)

    t2 = rf"""
\begin{{table*}}[!h]
    \centering
    \small
    \caption{{RQ2 (Welfare): Product Quality Composition in Rep vs Rep+Warrant (mean$\pm$std across runs).}}
    \label{{tab:rq2_welfare_product_quality}}
    \begin{{tabular}}{{lcccccc}}
    \toprule
    \textbf{{Condition}} & \multicolumn{{2}}{{c}}{{\textbf{{HQ Authentic}}}} & \multicolumn{{2}}{{c}}{{\textbf{{LQ Authentic}}}} & \multicolumn{{2}}{{c}}{{\textbf{{HQ Counterfeit}}}} \\
    \cmidrule(lr){{2-3}}\cmidrule(lr){{4-5}}\cmidrule(lr){{6-7}}
     & On sale & Sold & On sale & Sold & On sale & Sold \\
    \midrule
    Rep         & {_fmt_ms(*q_rep["hq_auth_on_sale"])} & {_fmt_ms(*q_rep["hq_auth_sold"])} & {_fmt_ms(*q_rep["lq_auth_on_sale"])} & {_fmt_ms(*q_rep["lq_auth_sold"])} & {_fmt_ms(*q_rep["hq_fake_on_sale"])} & {_fmt_ms(*q_rep["hq_fake_sold"])} \\
    Rep+Warrant & {_fmt_ms(*q_rw["hq_auth_on_sale"])} & {_fmt_ms(*q_rw["hq_auth_sold"])} & {_fmt_ms(*q_rw["lq_auth_on_sale"])} & {_fmt_ms(*q_rw["lq_auth_sold"])} & {_fmt_ms(*q_rw["hq_fake_on_sale"])} & {_fmt_ms(*q_rw["hq_fake_sold"])} \\
    \bottomrule
    \end{{tabular}}
\end{{table*}}
"""
    _write(out_dir / "rq2" / "tab_rq2_welfare_product_quality.tex", t2)


def generate_rq3_tables(base_dir: Path, out_dir: Path) -> None:
    """New RQ3: seller communication interference resilience (constraint-wise)."""
    rq3_base = base_dir / "rq3_resilience"
    constraints = [
        ("platform_fee", "Platform-Fee"),
        ("price_war", "Price-War"),
        ("financial_distress", "Financial-Distress"),
    ]

    # Summary welfare/deception table
    lines = [
        r"\begin{table*}[!h]",
        r"    \centering",
        r"    \small",
        r"    \caption{RQ3 (Resilience): Welfare and Deception under Seller Communication Interference (mean$\pm$std across runs).}",
        r"    \label{tab:rq3_resilience_summary}",
        r"    \begin{tabular}{lcccc}",
        r"    \toprule",
        r"    \textbf{Condition} & \textbf{Transactions} & \textbf{Profit (Seller)} & \textbf{Utility (Buyer)} & \textbf{Deceptions} \\",
        r"    \midrule",
    ]
    for i, (ck, clabel) in enumerate(constraints):
        lines.append(rf"    \multicolumn{{5}}{{l}}{{\textbf{{{clabel}}}}} \\")
        rep = _run_stats(rq3_base / f"r_wsc_R_{ck}")
        rw = _run_stats(rq3_base / f"rw_wsc_R_{ck}")
        lines.append(
            rf"    \quad Rep & {_fmt_ms(*rep['transactions'])} & {_fmt_ms(*rep['seller_profit'])} & {_fmt_ms(*rep['buyer_utility'])} & {_fmt_ms(*rep['deceptions'])} \\"
        )
        lines.append(
            rf"    \quad Rep+Warrant & {_fmt_ms(*rw['transactions'])} & {_fmt_ms(*rw['seller_profit'])} & {_fmt_ms(*rw['buyer_utility'])} & {_fmt_ms(*rw['deceptions'])} \\"
        )
        if i < len(constraints) - 1:
            lines.append(r"    \midrule")
    lines.extend([r"    \bottomrule", r"    \end{tabular}", r"\end{table*}"])
    _write(out_dir / "rq3" / "tab_rq3_resilience_summary.tex", "\n".join(lines))

    # Product quality table
    lines = [
        r"\begin{table*}[!h]",
        r"    \centering",
        r"    \small",
        r"    \caption{RQ3 (Resilience): Product Quality under Seller Communication Interference (mean$\pm$std across runs).}",
        r"    \label{tab:rq3_resilience_product_quality}",
        r"    \resizebox{\textwidth}{!}{%",
        r"    \begin{tabular}{lcccccc}",
        r"    \toprule",
        r"    \textbf{Condition} & \multicolumn{2}{c}{\textbf{HQ Authentic}} & \multicolumn{2}{c}{\textbf{LQ Authentic}} & \multicolumn{2}{c}{\textbf{HQ Counterfeit}} \\",
        r"    \cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
        r"     & On sale & Sold & On sale & Sold & On sale & Sold \\",
        r"    \midrule",
    ]
    for i, (ck, clabel) in enumerate(constraints):
        lines.append(rf"    \multicolumn{{7}}{{l}}{{\textbf{{{clabel}}}}} \\")
        rep = _quality_stats(rq3_base / f"r_wsc_R_{ck}")
        rw = _quality_stats(rq3_base / f"rw_wsc_R_{ck}")
        lines.append(
            rf"    \quad Rep & {_fmt_ms(*rep['hq_auth_on_sale'])} & {_fmt_ms(*rep['hq_auth_sold'])} & {_fmt_ms(*rep['lq_auth_on_sale'])} & {_fmt_ms(*rep['lq_auth_sold'])} & {_fmt_ms(*rep['hq_fake_on_sale'])} & {_fmt_ms(*rep['hq_fake_sold'])} \\"
        )
        lines.append(
            rf"    \quad Rep+Warrant & {_fmt_ms(*rw['hq_auth_on_sale'])} & {_fmt_ms(*rw['hq_auth_sold'])} & {_fmt_ms(*rw['lq_auth_on_sale'])} & {_fmt_ms(*rw['lq_auth_sold'])} & {_fmt_ms(*rw['hq_fake_on_sale'])} & {_fmt_ms(*rw['hq_fake_sold'])} \\"
        )
        if i < len(constraints) - 1:
            lines.append(r"    \midrule")
    lines.extend([r"    \bottomrule", r"    \end{tabular}%", r"    }", r"\end{table*}"])
    _write(out_dir / "rq3" / "tab_rq3_resilience_product_quality.tex", "\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LaTeX experiment tables from result dirs.")
    parser.add_argument("--base-dir", required=True, help="Experiment base dir (contains rq1_intent/rq2_welfare/rq3_resilience).")
    parser.add_argument("--output-dir", required=True, help="Output root dir for generated .tex tables.")
    args = parser.parse_args()

    base = Path(args.base_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating Paper Tables")
    print(f"Base   : {base}")
    print(f"Output : {out}")
    print("=" * 60)

    generate_rq1_tables(base, out)
    generate_rq2_tables(base, out)
    generate_rq3_tables(base, out)

    master = r"""
% Auto-generated table include file
\input{rq1/tab_rq1_intent_rep_only.tex}
\input{rq2/tab_rq2_welfare_summary.tex}
\input{rq2/tab_rq2_welfare_product_quality.tex}
\input{rq3/tab_rq3_resilience_summary.tex}
\input{rq3/tab_rq3_resilience_product_quality.tex}
"""
    _write(out / "all_tables.tex", master)
    print("Done.")


if __name__ == "__main__":
    main()
