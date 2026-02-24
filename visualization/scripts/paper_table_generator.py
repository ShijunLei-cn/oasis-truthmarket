#!/usr/bin/env python3
"""
Paper Table Generator

This module provides functions to generate LaTeX tables that match the exact format
required for the ICML 2025 paper on OASIS x Truth Market.

Tables generated follow the ICML style guide with:
- booktabs formatting (toprule, midrule, bottomrule)
- Centered alignment for all columns
- Proper spacing and formatting
- Bold formatting for significant results
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json


def format_number(value: float, std: float, precision: int = 1) -> str:
    """Format a number with its standard deviation."""
    if pd.isna(value) or pd.isna(std):
        return "N/A"
    return f"{value:.{precision}f}±{std:.{precision}f}"


def _bold_if_max(cell: str, is_max: bool, enable: bool = True) -> str:
    """Bold the cell when it is the max and bolding is enabled."""
    if not enable or not is_max:
        return cell
    return f"\\textbf{{{cell}}}"


def generate_latex_table(
    caption: str,
    label: str,
    headers: List[str],
    rows: List[List[str]],
    table_type: str = "table*",
    position: str = "t",
    bold_columns: Optional[List[int]] = None,
    bold_rows: Optional[List[int]] = None,
    multicolumn_headers: Optional[Dict[int, Tuple[int, str]]] = None,
    alignment: str = "c"
) -> str:
    """
    Generate a LaTeX table in the format required for the ICML paper.

    Args:
        caption: Table caption
        label: Table label (without tab: prefix)
        headers: List of column headers
        rows: List of data rows
        table_type: "table" or "table*"
        position: Table position specifier (e.g., "t", "htbp")
        bold_columns: List of column indices to bold (0-indexed)
        bold_rows: List of row indices to bold (0-indexed)
        multicolumn_headers: Dict mapping column index to (span, text) for multicolumn headers
        alignment: Column alignment (default: "c" for center)
    """
    lines = []

    # Start table
    lines.append(f"\\begin{{{table_type}}}[{position}]")
    lines.append("    \\centering")
    lines.append(f"    \\caption{{{caption}}}")
    lines.append(f"    \\label{{tab:{label}}}")

    # Determine column specification
    num_cols = len(headers)
    col_spec = alignment * num_cols
    lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")

    # Add top rule
    lines.append("    \\toprule")

    # Add headers
    if multicolumn_headers:
        # Handle multicolumn headers
        header_line = []
        col_idx = 0
        for i, header in enumerate(headers):
            if i in multicolumn_headers:
                span, text = multicolumn_headers[i]
                header_line.append(f"\\multicolumn{{{span}}}{{{alignment}}}{{{text}}}")
                col_idx += span
            else:
                # Regular header
                if col_idx < num_cols:
                    header_line.append(f"\\textbf{{{header}}}")
                    col_idx += 1
        lines.append("    " + " & ".join(header_line) + " \\\\")
    else:
        # Regular headers
        formatted_headers = [f"\\textbf{{{h}}}" for h in headers]
        lines.append("    " + " & ".join(formatted_headers) + " \\\\")

    # Add midrule after headers
    lines.append("    \\midrule")

    # Add data rows
    for row_idx, row in enumerate(rows):
        formatted_row = []
        for col_idx, cell in enumerate(row):
            # Apply bold formatting if specified
            if (bold_rows and row_idx in bold_rows) or (bold_columns and col_idx in bold_columns):
                formatted_cell = f"\\textbf{{{cell}}}"
            else:
                formatted_cell = cell
            formatted_row.append(formatted_cell)
        lines.append("    " + " & ".join(formatted_row) + " \\\\")

    # Add bottom rule
    lines.append("    \\bottomrule")
    lines.append("    \\end{tabular}")
    lines.append(f"\\end{{{table_type}}}")

    return "\n".join(lines)


def save_latex_table(
    table_code: str,
    output_path: Path,
    file_mode: str = "w"
) -> None:
    """Save LaTeX table code to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, file_mode, encoding='utf-8') as f:
        f.write(table_code)
    print(f"✅ Table saved to: {output_path}")


def create_summary_stats_table(
    rep_stats: Dict[str, Any],
    rep_warrant_stats: Dict[str, Any],
    output_path: Path
) -> None:
    """Create the Summary Statistics with Reputation table (tab:rq1_summary_stats)."""

    keys = ["transactions", "seller_profit", "buyer_utility", "reputation"]
    max_vals = {}
    min_vals = {}
    for key in keys:
        vals = [
            rep_stats.get(key, float("-inf")),
            rep_warrant_stats.get(key, float("-inf"))
        ]
        max_vals[key] = max(vals)
        min_vals[key] = min(vals)

    # Prepare data
    rows = [
        [
            "Rep",
            format_number(rep_stats.get('transactions', 0), rep_stats.get('transactions_std', 0)),
            format_number(rep_stats.get('seller_profit', 0), rep_stats.get('seller_profit_std', 0)),
            format_number(rep_stats.get('buyer_utility', 0), rep_stats.get('buyer_utility_std', 0)),
            format_number(rep_stats.get('reputation', 0), rep_stats.get('reputation_std', 0))
        ],
        [
            "Rep+Warrant",
            format_number(rep_warrant_stats.get('transactions', 0), rep_warrant_stats.get('transactions_std', 0)),
            format_number(rep_warrant_stats.get('seller_profit', 0), rep_warrant_stats.get('seller_profit_std', 0)),
            format_number(rep_warrant_stats.get('buyer_utility', 0), rep_warrant_stats.get('buyer_utility_std', 0)),
            format_number(rep_warrant_stats.get('reputation', 0), rep_warrant_stats.get('reputation_std', 0))
        ]
    ]

    # Apply bold per column max
    for row in rows:
        for idx, key in enumerate(keys, start=1):
            val = rep_stats[key] if row[0] == "Rep" else rep_warrant_stats[key]
            row[idx] = _bold_if_max(row[idx], val == max_vals[key], enable=max_vals[key] != min_vals[key])

    table_code = generate_latex_table(
        caption="Summary Statistics with Reputation",
        label="rq1_summary_stats",
        headers=["Condition", "Transactions", "Profit (Seller)", "Utility (Buyer)", "Reputation"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path)


def create_manipulation_detection_table(
    rep_detection: Dict[str, float],
    rep_warrant_detection: Dict[str, float],
    output_path: Path
) -> None:
    """Create the Manipulation Detection Rate table (tab:rq1_summary_comparison)."""

    vuln_keys = ["IW", "RL", "VI", "RE", "ES"]
    max_vals = {}
    min_vals = {}
    for key in vuln_keys:
        vals = [
            rep_detection.get(key, float("-inf")),
            rep_warrant_detection.get(key, float("-inf"))
        ]
        max_vals[key] = max(vals)
        min_vals[key] = min(vals)

    rows = [
        [
            "Rep",
            f"{rep_detection.get('IW', 0):.1f}",
            f"{rep_detection.get('RL', 0):.1f}",
            f"{rep_detection.get('VI', 0):.1f}",
            f"{rep_detection.get('RE', 0):.1f}",
            f"\\textbf{{{rep_detection.get('ES', 0):.1f}}}"
        ],
        [
            "Rep+Warrant",
            f"{rep_warrant_detection.get('IW', 0):.1f}",
            f"{rep_warrant_detection.get('RL', 0):.1f}",
            f"{rep_warrant_detection.get('VI', 0):.1f}",
            f"{rep_warrant_detection.get('RE', 0):.1f}",
            f"{rep_warrant_detection.get('ES', 0):.1f}"
        ]
    ]

    # Bold per column max
    for row in rows:
        for idx, key in enumerate(vuln_keys, start=1):
            val = float(row[idx].replace("\\textbf{", "").replace("}", ""))
            row[idx] = _bold_if_max(row[idx], val == max_vals[key], enable=max_vals[key] != min_vals[key])

    table_code = generate_latex_table(
        caption="Manipulation Detection Rate by Vulnerability Type",
        label="rq1_summary_comparison",
        headers=["Market Type", "IW", "RL", "VI", "RE", "ES"],
        rows=rows,
        table_type="table",
        position="htbp"
    )

    save_latex_table(table_code, output_path)


def create_product_quality_table(
    rep_quality: Dict[str, Any],
    rep_warrant_quality: Dict[str, Any],
    output_path: Path
) -> None:
    """Create the Product Quality Statistics table (tab:rq1_product_quality)."""

    keys = [
        "hq_authentic_on_sale",
        "hq_authentic_sold",
        "lq_authentic_on_sale",
        "lq_authentic_sold",
        "hq_counterfeit_on_sale",
        "hq_counterfeit_sold",
    ]
    max_vals = {}
    min_vals = {}
    for key in keys:
        vals = [
            rep_quality.get(key, float("-inf")),
            rep_warrant_quality.get(key, float("-inf"))
        ]
        max_vals[key] = max(vals)
        min_vals[key] = min(vals)

    def fmt(stats: Dict[str, Any], key: str) -> str:
        return format_number(stats.get(key, 0), stats.get(f"{key}_std", 0))

    rows = [
        [
            "Rep",
            fmt(rep_quality, "hq_authentic_on_sale"),
            fmt(rep_quality, "hq_authentic_sold"),
            fmt(rep_quality, "lq_authentic_on_sale"),
            fmt(rep_quality, "lq_authentic_sold"),
            fmt(rep_quality, "hq_counterfeit_on_sale"),
            fmt(rep_quality, "hq_counterfeit_sold"),
        ],
        [
            "Rep+Warrant",
            fmt(rep_warrant_quality, "hq_authentic_on_sale"),
            fmt(rep_warrant_quality, "hq_authentic_sold"),
            fmt(rep_warrant_quality, "lq_authentic_on_sale"),
            fmt(rep_warrant_quality, "lq_authentic_sold"),
            fmt(rep_warrant_quality, "hq_counterfeit_on_sale"),
            fmt(rep_warrant_quality, "hq_counterfeit_sold"),
        ]
    ]

    # Bold per column max
    for row in rows:
        for idx, key in enumerate(keys, start=1):
            val = rep_quality[key] if row[0] == "Rep" else rep_warrant_quality[key]
            row[idx] = _bold_if_max(row[idx], val == max_vals[key], enable=max_vals[key] != min_vals[key])

    table_code = generate_latex_table(
        caption="Product Quality Statistics",
        label="rq1_product_quality",
        headers=["Condition", "On sale", "Sold", "On sale", "Sold", "On sale", "Sold"],
        rows=rows,
        table_type="table*",
        position="t",
        multicolumn_headers={
            1: (2, "HQ Authentic"),
            3: (2, "LQ Authentic"),
            5: (2, "HQ Counterfeit")
        }
    )

    save_latex_table(table_code, output_path)


def create_market_outcomes_table(
    constraint_results: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """Create the Market Outcomes and Reputation Statistics by Constraints table (tab:rq2_initial_posts)."""

    rows = []
    condition_order = ["Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm"]

    # Process each constraint type
    for constraint_name, conditions in constraint_results.items():
        rows.append([f"\\textbf{{{constraint_name.replace('_', '-')}}}", "", "", "", "", ""])

        # Compute per-column maxima/minima within this constraint
        metrics = ["transactions", "seller_profit", "buyer_utility", "reputation"]
        max_vals = {key: float("-inf") for key in metrics}
        min_vals = {key: float("inf") for key in metrics}
        for cond in condition_order:
            if cond not in conditions:
                continue
            stats = conditions[cond]
            for key in metrics:
                max_vals[key] = max(max_vals[key], stats.get(key, float("-inf")))
                min_vals[key] = min(min_vals[key], stats.get(key, float("inf")))

        for condition_name in condition_order:
            if condition_name not in conditions:
                continue
            stats = conditions[condition_name]
            row = [
                "",
                condition_name,
                format_number(stats.get('transactions', 0), stats.get('transactions_std', 0)),
                format_number(stats.get('seller_profit', 0), stats.get('seller_profit_std', 0)),
                format_number(stats.get('buyer_utility', 0), stats.get('buyer_utility_std', 0)),
                format_number(stats.get('reputation', 0), stats.get('reputation_std', 0))
            ]
            for idx, key in enumerate(metrics, start=2):
                row[idx] = _bold_if_max(
                    row[idx],
                    stats.get(key, float("-inf")) == max_vals[key],
                    enable=max_vals[key] != min_vals[key]
                )
            rows.append(row)

        # Add separator line
        if constraint_name != list(constraint_results.keys())[-1]:
            rows.append(["", "", "", "", "", ""])

    table_code = generate_latex_table(
        caption="Market Outcomes and Reputation Statistics by Constraints",
        label="rq2_initial_posts",
        headers=["Constraints", "Condition", "Transactions", "Profit (Seller)", "Utility (Buyer)", "Reputation"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path)


def create_profit_decomposition_table(
    constraint_results: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """Create the Profit Decomposition by Constraints table (tab:rq2_profit_decomposition)."""

    rows = []
    condition_order = ["Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm"]

    for constraint_name, conditions in constraint_results.items():
        rows.append([f"\\textbf{{{constraint_name.replace('_', '-')}}}", "", "", "", "", ""])

        metrics = ["total_profit", "honest_profit", "dishonest_profit"]
        max_vals = {key: float("-inf") for key in metrics}
        min_vals = {key: float("inf") for key in metrics}
        for cond in condition_order:
            if cond not in conditions:
                continue
            stats = conditions[cond]
            # total_profit is recomputed; still use for max
            total_profit = stats.get('honest_profit', 0) + stats.get('dishonest_profit', 0)
            max_vals["total_profit"] = max(max_vals["total_profit"], total_profit)
            max_vals["honest_profit"] = max(max_vals["honest_profit"], stats.get('honest_profit', float("-inf")))
            max_vals["dishonest_profit"] = max(max_vals["dishonest_profit"], stats.get('dishonest_profit', float("-inf")))
            min_vals["total_profit"] = min(min_vals["total_profit"], total_profit)
            min_vals["honest_profit"] = min(min_vals["honest_profit"], stats.get('honest_profit', float("inf")))
            min_vals["dishonest_profit"] = min(min_vals["dishonest_profit"], stats.get('dishonest_profit', float("inf")))

        for condition_name in condition_order:
            if condition_name not in conditions:
                continue
            stats = conditions[condition_name]
            honest_profit = stats.get('honest_profit', 0)
            dishonest_profit = stats.get('dishonest_profit', 0)
            total_profit = honest_profit + dishonest_profit
            dishonest_pct = (dishonest_profit / total_profit * 100) if total_profit > 0 else 0

            row = [
                "",
                condition_name,
                format_number(total_profit, stats.get('total_profit_std', 0)),
                format_number(honest_profit, stats.get('honest_profit_std', 0)),
                format_number(dishonest_profit, stats.get('dishonest_profit_std', 0)),
                f"{dishonest_pct:.1f}"
            ]
            # Apply bold to profit columns
            row[2] = _bold_if_max(row[2], total_profit == max_vals["total_profit"], enable=max_vals["total_profit"] != min_vals["total_profit"])
            row[3] = _bold_if_max(row[3], honest_profit == max_vals["honest_profit"], enable=max_vals["honest_profit"] != min_vals["honest_profit"])
            row[4] = _bold_if_max(row[4], dishonest_profit == max_vals["dishonest_profit"], enable=max_vals["dishonest_profit"] != min_vals["dishonest_profit"])
            rows.append(row)

        if constraint_name != list(constraint_results.keys())[-1]:
            rows.append(["", "", "", "", "", ""])

    table_code = generate_latex_table(
        caption="Profit Decomposition by Constraints",
        label="rq2_profit_decomposition",
        headers=["Constraints", "Condition", "Total Profit", "Honest Profit", "Dishonest Profit", "Dishonest %"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path)


def create_buyer_comm_table(
    stats_map: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """Create the Summary Statistics with Deceptions and Reputation table (tab:rq3_summary_stats)."""

    order = ["Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm"]
    metrics = ["transactions", "seller_profit", "buyer_utility", "deceptions", "reputation"]

    max_vals = {key: float("-inf") for key in metrics}
    min_vals = {key: float("inf") for key in metrics}
    for stats in stats_map.values():
        for key in metrics:
            max_vals[key] = max(max_vals[key], stats.get(key, float("-inf")))
            min_vals[key] = min(min_vals[key], stats.get(key, float("inf")))

    rows = []
    for label in order:
        if label not in stats_map:
            continue
        stats = stats_map[label]
        row = [
            label,
            format_number(stats.get('transactions', 0), stats.get('transactions_std', 0)),
            format_number(stats.get('seller_profit', 0), stats.get('seller_profit_std', 0)),
            format_number(stats.get('buyer_utility', 0), stats.get('buyer_utility_std', 0)),
            format_number(stats.get('deceptions', 0), stats.get('deceptions_std', 0)),
            format_number(stats.get('reputation', 0), stats.get('reputation_std', 0))
        ]
        for idx, key in enumerate(metrics, start=1):
            row[idx] = _bold_if_max(
                row[idx],
                stats.get(key, float("-inf")) == max_vals[key],
                enable=max_vals[key] != min_vals[key]
            )
        rows.append(row)

    table_code = generate_latex_table(
        caption="Summary Statistics with Deceptions and Reputation",
        label="rq3_summary_stats",
        headers=["Condition", "Transactions", "Profit (Seller)", "Utility (Buyer)", "Deceptions", "Reputation"],
        rows=rows,
        table_type="table*",
        position="t"
    )

    save_latex_table(table_code, output_path)


def create_buyer_comm_quality_table(
    quality_map: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """Create the Product Quality Statistics table for buyer communication (tab:rq3_product_quality)."""

    order = ["Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm"]
    keys = [
        "hq_authentic_on_sale",
        "hq_authentic_sold",
        "lq_authentic_on_sale",
        "lq_authentic_sold",
        "hq_counterfeit_on_sale",
        "hq_counterfeit_sold",
    ]

    max_vals = {key: float("-inf") for key in keys}
    min_vals = {key: float("inf") for key in keys}
    for stats in quality_map.values():
        for key in keys:
            max_vals[key] = max(max_vals[key], stats.get(key, float("-inf")))
            min_vals[key] = min(min_vals[key], stats.get(key, float("inf")))

    rows = []
    for label in order:
        if label not in quality_map:
            continue
        stats = quality_map[label]
        row = [
            label,
            format_number(stats.get('hq_authentic_on_sale', 0), stats.get('hq_authentic_on_sale_std', 0)),
            format_number(stats.get('hq_authentic_sold', 0), stats.get('hq_authentic_sold_std', 0)),
            format_number(stats.get('lq_authentic_on_sale', 0), stats.get('lq_authentic_on_sale_std', 0)),
            format_number(stats.get('lq_authentic_sold', 0), stats.get('lq_authentic_sold_std', 0)),
            format_number(stats.get('hq_counterfeit_on_sale', 0), stats.get('hq_counterfeit_on_sale_std', 0)),
            format_number(stats.get('hq_counterfeit_sold', 0), stats.get('hq_counterfeit_sold_std', 0))
        ]
        for idx, key in enumerate(keys, start=1):
            row[idx] = _bold_if_max(
                row[idx],
                stats.get(key, float("-inf")) == max_vals[key],
                enable=max_vals[key] != min_vals[key]
            )
        rows.append(row)

    table_code = generate_latex_table(
        caption="Product Quality Statistics",
        label="rq3_product_quality",
        headers=["Condition", "", "", "", "", "", ""],
        rows=rows,
        table_type="table*",
        position="t",
        multicolumn_headers={
            1: (2, "HQ Authentic"),
            3: (2, "LQ Authentic"),
            5: (2, "HQ Counterfeit")
        }
    )

    save_latex_table(table_code, output_path)


if __name__ == "__main__":
    print("📊 Paper Table Generator")
    print("This module provides functions to generate LaTeX tables for the ICML 2025 paper.")
    print("Import this module and use the table generation functions.")
