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

    # Bold the Rep+Warrant row
    bold_rows = [1]

    table_code = generate_latex_table(
        caption="Summary Statistics with Reputation",
        label="rq1_summary_stats",
        headers=["Condition", "Transactions", "Profit (Seller)", "Utility (Buyer)", "Reputation"],
        rows=rows,
        table_type="table*",
        position="t",
        bold_rows=bold_rows
    )

    save_latex_table(table_code, output_path)


def create_manipulation_detection_table(
    rep_detection: Dict[str, float],
    rep_warrant_detection: Dict[str, float],
    output_path: Path
) -> None:
    """Create the Manipulation Detection Rate table (tab:rq1_summary_comparison)."""

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

    def get_quality_stats(stats: Dict, quality_type: str) -> Tuple[float, float, float, float]:
        """Extract quality statistics for a given quality type."""
        hq_on_sale = stats.get(f'{quality_type}_on_sale', 0)
        hq_sold = stats.get(f'{quality_type}_sold', 0)
        hq_on_sale_std = stats.get(f'{quality_type}_on_sale_std', 0)
        hq_sold_std = stats.get(f'{quality_type}_sold_std', 0)
        return (
            format_number(hq_on_sale, hq_on_sale_std),
            format_number(hq_sold, hq_sold_std)
        )

    rep_hq_on_sale, rep_hq_sold = get_quality_stats(rep_quality, 'hq_authentic')
    rep_lq_on_sale, rep_lq_sold = get_quality_stats(rep_quality, 'lq_authentic')
    rep_counterfeit_on_sale, rep_counterfeit_sold = get_quality_stats(rep_quality, 'hq_counterfeit')

    rw_hq_on_sale, rw_hq_sold = get_quality_stats(rep_warrant_quality, 'hq_authentic')
    rw_lq_on_sale, rw_lq_sold = get_quality_stats(rep_warrant_quality, 'lq_authentic')
    rw_counterfeit_on_sale, rw_counterfeit_sold = get_quality_stats(rep_warrant_quality, 'hq_counterfeit')

    rows = [
        [
            "Rep",
            rep_hq_on_sale,
            rep_hq_sold,
            rep_lq_on_sale,
            rep_lq_sold,
            rep_counterfeit_on_sale,
            rep_counterfeit_sold
        ],
        [
            "Rep+Warrant",
            f"\\textbf{{{rw_hq_on_sale}}}",
            f"\\textbf{{{rw_hq_sold}}}",
            f"\\textbf{{{rw_lq_on_sale}}}",
            f"\\textbf{{{rw_lq_sold}}}",
            rw_counterfeit_on_sale,
            rw_counterfeit_sold
        ]
    ]

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
    rep_comm_stats: Dict[str, Any],
    rep_warrant_comm_stats: Dict[str, Any],
    output_path: Path
) -> None:
    """Create the Summary Statistics with Deceptions and Reputation table (tab:rq3_summary_stats)."""

    rows = [
        [
            "Rep, Comm",
            format_number(rep_comm_stats.get('transactions', 0), rep_comm_stats.get('transactions_std', 0)),
            format_number(rep_comm_stats.get('seller_profit', 0), rep_comm_stats.get('seller_profit_std', 0)),
            format_number(rep_comm_stats.get('buyer_utility', 0), rep_comm_stats.get('buyer_utility_std', 0)),
            format_number(rep_comm_stats.get('deceptions', 0), rep_comm_stats.get('deceptions_std', 0)),
            format_number(rep_comm_stats.get('reputation', 0), rep_comm_stats.get('reputation_std', 0))
        ],
        [
            "Rep+Warrant, Comm",
            format_number(rep_warrant_comm_stats.get('transactions', 0), rep_warrant_comm_stats.get('transactions_std', 0)),
            f"\\textbf{{{format_number(rep_warrant_comm_stats.get('seller_profit', 0), rep_warrant_comm_stats.get('seller_profit_std', 0))}}}",
            f"\\textbf{{{format_number(rep_warrant_comm_stats.get('buyer_utility', 0), rep_warrant_comm_stats.get('buyer_utility_std', 0))}}}",
            f"\\textbf{{{format_number(rep_warrant_comm_stats.get('deceptions', 0), rep_warrant_comm_stats.get('deceptions_std', 0))}}}",
            format_number(rep_warrant_comm_stats.get('reputation', 0), rep_warrant_comm_stats.get('reputation_std', 0))
        ]
    ]

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
    rep_comm_quality: Dict[str, Any],
    rep_warrant_comm_quality: Dict[str, Any],
    output_path: Path
) -> None:
    """Create the Product Quality Statistics table for buyer communication (tab:rq3_product_quality)."""

    def get_quality_stats(stats: Dict, quality_type: str) -> Tuple[str, str]:
        """Extract quality statistics for a given quality type."""
        hq_on_sale = stats.get(f'{quality_type}_on_sale', 0)
        hq_sold = stats.get(f'{quality_type}_sold', 0)
        hq_on_sale_std = stats.get(f'{quality_type}_on_sale_std', 0)
        hq_sold_std = stats.get(f'{quality_type}_sold_std', 0)
        return (
            format_number(hq_on_sale, hq_on_sale_std),
            format_number(hq_sold, hq_sold_std)
        )

    rep_hq_on_sale, rep_hq_sold = get_quality_stats(rep_comm_quality, 'hq_authentic')
    rep_lq_on_sale, rep_lq_sold = get_quality_stats(rep_comm_quality, 'lq_authentic')
    rep_counterfeit_on_sale, rep_counterfeit_sold = get_quality_stats(rep_comm_quality, 'hq_counterfeit')

    rw_hq_on_sale, rw_hq_sold = get_quality_stats(rep_warrant_comm_quality, 'hq_authentic')
    rw_lq_on_sale, rw_lq_sold = get_quality_stats(rep_warrant_comm_quality, 'lq_authentic')
    rw_counterfeit_on_sale, rw_counterfeit_sold = get_quality_stats(rep_warrant_comm_quality, 'hq_counterfeit')

    rows = [
        [
            "Rep, Comm",
            rep_hq_on_sale,
            rep_hq_sold,
            rep_lq_on_sale,
            rep_lq_sold,
            rep_counterfeit_on_sale,
            rep_counterfeit_sold
        ],
        [
            "Rep+Warrant, Comm",
            f"\\textbf{{{rw_hq_on_sale}}}",
            f"\\textbf{{{rw_hq_sold}}}",
            f"\\textbf{{{rw_lq_on_sale}}}",
            f"\\textbf{{{rw_lq_on_sale}}}",
            f"\\textbf{{{rw_counterfeit_on_sale}}}",
            f"\\textbf{{{rw_counterfeit_sold}}}"
        ]
    ]

    table_code = generate_latex_table(
        caption="Product Quality Statistics",
        label="rq3_product_quality",
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


if __name__ == "__main__":
    print("📊 Paper Table Generator")
    print("This module provides functions to generate LaTeX tables for the ICML 2025 paper.")
    print("Import this module and use the table generation functions.")
