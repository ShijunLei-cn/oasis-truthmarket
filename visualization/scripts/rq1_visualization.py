import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import numpy as np
import os
from collections import defaultdict
from typing import Dict, List, Any

def load_probe_results(experiment_dir: str):
    """Load all cognitive probe results from the experiment directory."""
    path = Path(experiment_dir)
    all_results = []
    
    if not path.exists():
        print(f"ERROR: Experiment directory does not exist: {experiment_dir}")
        return pd.DataFrame()
    
    # Find all run_*_cognitive_probes.json files
    probe_files = list(path.glob("run_*_cognitive_probes.json"))
    if not probe_files:
        print(f"ERROR: No cognitive probe result files found in {experiment_dir}")
        print(f"  Expected files: run_*_cognitive_probes.json")
        print(f"  Available files in directory:")
        for f in sorted(path.glob("run_*")):
            print(f"    - {f.name}")
        print(f"\n  This usually means:")
        print(f"    1. RQ1 experiment did not run cognitive probes")
        print(f"    2. Cognitive probe results were not saved")
        print(f"    3. Files are in a different location")
        return pd.DataFrame()
    
    print(f"Found {len(probe_files)} cognitive probe files")
    for file in probe_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    print(f"  Warning: {file.name} is empty")
                    continue
                # Add run identifier
                run_id = file.stem.replace("_cognitive_probes", "").replace("run_", "")
                for item in data:
                    item["run_id"] = run_id
                all_results.extend(data)
                print(f"  Loaded {len(data)} probes from {file.name}")
        except Exception as e:
            print(f"  ERROR loading {file.name}: {e}")
            import traceback
            traceback.print_exc()
            
    if not all_results:
        print(f"ERROR: No probe results loaded from {experiment_dir}")
        return pd.DataFrame()
    
    print(f"Total: {len(all_results)} probe results loaded")
    return pd.DataFrame(all_results)

def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate aggregate statistics from probe results."""
    if df.empty:
        return {"error": "No results found"}
    
    stats = {
        "total_probes": len(df),
        "total_manipulation_detected": int(df["manipulation_detected"].sum()),
        "overall_manipulation_rate": float(df["manipulation_detected"].mean()),
        "unique_agents": int(df["agent_id"].nunique()),
        "unique_rounds": int(df["round_num"].nunique()),
        "by_vulnerability_type": {},
        "by_round": {},
        "by_agent": {},
    }
    
    # By vulnerability type
    for vuln_type in df["vulnerability_type"].unique():
        subset = df[df["vulnerability_type"] == vuln_type]
        stats["by_vulnerability_type"][vuln_type] = {
            "total_probes": int(len(subset)),
            "manipulation_detected": int(subset["manipulation_detected"].sum()),
            "manipulation_rate": float(subset["manipulation_detected"].mean()),
            "agents_manipulating": list(
                subset[subset["manipulation_detected"]]["agent_id"].unique()
            ),
        }
        
        # Severity for reputation lag
        if vuln_type == "reputation_lag":
            severities = subset["severity_score"].dropna()
            if len(severities) > 0:
                stats["by_vulnerability_type"][vuln_type]["avg_expected_lag"] = float(
                    severities.mean()
                )
                stats["by_vulnerability_type"][vuln_type]["max_expected_lag"] = float(
                    severities.max()
                )
    
    # By round
    for round_num in sorted(df["round_num"].unique()):
        subset = df[df["round_num"] == round_num]
        stats["by_round"][int(round_num)] = {
            "total_probes": int(len(subset)),
            "manipulation_detected": int(subset["manipulation_detected"].sum()),
            "manipulation_rate": float(subset["manipulation_detected"].mean()),
        }
    
    # By agent
    for agent_id in sorted(df["agent_id"].unique()):
        subset = df[df["agent_id"] == agent_id]
        stats["by_agent"][int(agent_id)] = {
            "total_probes": int(len(subset)),
            "manipulation_detected": int(subset["manipulation_detected"].sum()),
            "manipulation_rate": float(subset["manipulation_detected"].mean()),
        }
    
    return stats

def plot_manipulation_heatmap(df: pd.DataFrame, output_path: Path):
    """Create a heatmap of manipulation detection rates per seller and probe type."""
    if df.empty:
        print("No data to plot.")
        return
    
    # Calculate detection rate: sum(manipulation_detected) / count(*)
    # Group by agent_id and vulnerability_type
    stats = df.groupby(['agent_id', 'vulnerability_type']).agg(
        detected_count=('manipulation_detected', 'sum'),
        total_count=('manipulation_detected', 'count')
    ).reset_index()
    
    stats['detection_rate'] = stats['detected_count'] / stats['total_count']
    
    # Pivot for heatmap: index=agent_id, columns=vulnerability_type, values=detection_rate
    pivot_df = stats.pivot(index='agent_id', columns='vulnerability_type', values='detection_rate')
    
    # Sort index and columns for better presentation
    pivot_df = pivot_df.sort_index()
    
    # Plotting
    plt.figure(figsize=(12, 8))
    
    # Academic style
    sns.set_theme(style="white")
    
    # Map vulnerability type names to more readable labels
    rename_map = {
        'initial_window': 'Initial Window',
        'reputation_lag': 'Reputation Lag',
        'value_imbalance': 'Value Imbalance',
        'reentry': 'Re-entry',
        'exit_strategy': 'Exit Strategy'
    }
    pivot_df.columns = [rename_map.get(col, col) for col in pivot_df.columns]
    
    ax = sns.heatmap(
        pivot_df, 
        annot=True, 
        fmt=".2f", 
        cmap="YlOrRd", 
        linewidths=.5, 
        cbar_kws={'label': 'Detection Rate (Detected / Total Tests)'},
        vmin=0, vmax=1
    )
    
    plt.title('RQ1: Cognitive Manipulation Detection Rate by Seller and Probe Type', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Probe Type (Manipulation Strategy)', fontsize=12, fontweight='bold')
    plt.ylabel('Seller ID', fontsize=12, fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated heatmap: {output_path}")

def plot_manipulation_by_vulnerability(stats: Dict, output_path: Path):
    """Create bar chart of manipulation rates by vulnerability type."""
    if "by_vulnerability_type" not in stats or not stats["by_vulnerability_type"]:
        return
    
    vuln_data = stats["by_vulnerability_type"]
    
    # Prepare data
    vuln_types = list(vuln_data.keys())
    rates = [vuln_data[v]["manipulation_rate"] * 100 for v in vuln_types]
    counts = [vuln_data[v]["manipulation_detected"] for v in vuln_types]
    totals = [vuln_data[v]["total_probes"] for v in vuln_types]
    
    # Clean labels
    labels = [v.replace("_", " ").title() for v in vuln_types]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Colors
    colors = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71", "#9b59b6"]
    
    bars = ax.bar(
        labels, rates, color=colors[: len(labels)], edgecolor="black", linewidth=1.2
    )
    
    # Add value labels on bars
    for bar, count, total in zip(bars, counts, totals):
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f}%\n({count}/{total})",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    
    ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=12)
    ax.set_xlabel("Vulnerability Type", fontsize=12)
    ax.set_title(
        "RQ1: Manipulation Detection Rate by Vulnerability Type",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylim(0, max(rates) * 1.3 if rates else 100)
    
    # Add grid
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ Generated vulnerability comparison: {output_path}")

def plot_manipulation_over_rounds(stats: Dict, output_path: Path):
    """Create line chart of manipulation trends over rounds."""
    if "by_round" not in stats or not stats["by_round"]:
        return
    
    round_data = stats["by_round"]
    
    rounds = sorted(round_data.keys())
    rates = [round_data[r]["manipulation_rate"] * 100 for r in rounds]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(rounds, rates, marker="o", linewidth=2, markersize=8, color="#e74c3c")
    ax.fill_between(rounds, rates, alpha=0.3, color="#e74c3c")
    
    ax.set_xlabel("Round Number", fontsize=12)
    ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=12)
    ax.set_title("RQ1: Manipulation Behavior Over Time", fontsize=14, fontweight="bold")
    
    ax.set_xticks(rounds)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    
    # Highlight early rounds (initial window)
    if len(rounds) >= 2:
        ax.axvspan(0.5, 2.5, alpha=0.2, color="yellow", label="Initial Window")
        ax.legend()
    
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ Generated temporal trend: {output_path}")

def plot_option_distribution(df: pd.DataFrame, output_path: Path):
    """Create stacked bar chart of option selections."""
    if df.empty or "selected_option" not in df.columns:
        return
    
    # Count options by vulnerability type
    option_counts = (
        df.groupby(["vulnerability_type", "selected_option"])
        .size()
        .unstack(fill_value=0)
    )
    
    # Clean labels
    option_counts.index = [v.replace("_", " ").title() for v in option_counts.index]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = {"A": "#e74c3c", "B": "#2ecc71", "C": "#3498db", None: "#95a5a6"}
    
    bottom = np.zeros(len(option_counts))
    for option in ["A", "B", "C"]:
        if option in option_counts.columns:
            values = option_counts[option].values
            ax.bar(
                option_counts.index,
                values,
                bottom=bottom,
                label=f"Option {option}",
                color=colors.get(option, "#95a5a6"),
            )
            bottom += values
    
    ax.set_xlabel("Vulnerability Type", fontsize=12)
    ax.set_ylabel("Number of Responses", fontsize=12)
    ax.set_title(
        "RQ1: Response Distribution by Vulnerability Type",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(title="Selected Option")
    
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ Generated option distribution: {output_path}")

def plot_reputation_lag_severity(df: pd.DataFrame, output_path: Path):
    """Create histogram of expected reputation lag values."""
    if df.empty:
        return
    
    lag_data = df[df["vulnerability_type"] == "reputation_lag"][
        "severity_score"
    ].dropna()
    
    if len(lag_data) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(
        lag_data,
        bins=range(0, int(lag_data.max()) + 2),
        color="#3498db",
        edgecolor="black",
        alpha=0.7,
    )
    
    ax.axvline(
        lag_data.mean(),
        color="#e74c3c",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {lag_data.mean():.1f} rounds",
    )
    
    ax.set_xlabel("Expected Reputation Lag (Rounds)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(
        "RQ1: Distribution of Expected Reputation Lag", fontsize=14, fontweight="bold"
    )
    ax.legend()
    
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ Generated reputation lag severity: {output_path}")

def print_summary_report(stats: Dict):
    """Print formatted summary report."""
    if "error" in stats:
        print(f"Error: {stats['error']}")
        return
    
    print("\n" + "=" * 70)
    print("RQ1 COGNITIVE PROBING ANALYSIS REPORT")
    print("=" * 70)
    
    print(f"\n📊 OVERVIEW")
    print(f"  Total Probes: {stats['total_probes']}")
    print(f"  Manipulation Detected: {stats['total_manipulation_detected']}")
    print(f"  Overall Rate: {stats['overall_manipulation_rate']*100:.1f}%")
    print(f"  Unique Agents: {stats['unique_agents']}")
    print(f"  Unique Rounds: {stats['unique_rounds']}")
    
    if stats.get("by_vulnerability_type"):
        print(f"\n📋 BY VULNERABILITY TYPE")
        for vuln_type, data in stats["by_vulnerability_type"].items():
            label = vuln_type.replace("_", " ").upper()
            print(f"\n  {label}:")
            print(
                f"    Manipulation Rate: {data['manipulation_rate']*100:.1f}% ({data['manipulation_detected']}/{data['total_probes']})"
            )
            if "avg_expected_lag" in data:
                print(f"    Avg Expected Lag: {data['avg_expected_lag']:.1f} rounds")
                print(f"    Max Expected Lag: {data['max_expected_lag']:.0f} rounds")
            if data["agents_manipulating"]:
                print(f"    Agents Detected: {data['agents_manipulating']}")
    
    print(f"\n🎯 KEY FINDINGS")
    
    # Find most exploited vulnerability
    if stats.get("by_vulnerability_type"):
        most_exploited = max(
            stats["by_vulnerability_type"].items(),
            key=lambda x: x[1]["manipulation_rate"],
        )
        print(
            f"  Most Exploited: {most_exploited[0].replace('_', ' ').title()} ({most_exploited[1]['manipulation_rate']*100:.1f}%)"
        )
    
    # Find most manipulative agent
    if stats.get("by_agent"):
        most_manipulative = max(
            stats["by_agent"].items(), key=lambda x: x[1]["manipulation_rate"]
        )
        print(
            f"  Most Manipulative Agent: Agent {most_manipulative[0]} ({most_manipulative[1]['manipulation_rate']*100:.1f}%)"
        )
    
    print("\n" + "=" * 70)

def _format_number(value: float, decimals: int = 2) -> str:
    """Format number with specified decimal places"""
    if pd.isna(value) or np.isnan(value):
        return "N/A"
    return f"{value:.{decimals}f}"

def _generate_markdown_table(headers: List[str], rows: List[List[str]], 
                             caption: str = "") -> str:
    """Generate markdown table with three-line format"""
    lines = []
    
    if caption:
        lines.append(f"**{caption}**\n")
    
    # Header
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---" for _ in headers]) + "|")
    
    # Rows
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    
    return "\n".join(lines)

def _generate_latex_table(headers: List[str], rows: List[List[str]], 
                         caption: str = "", label: str = "") -> str:
    """Generate LaTeX table with three-line format (booktabs style)"""
    lines = []
    lines.append("```latex")
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    if caption:
        lines.append(f"\\caption{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    # Auto-detect column alignment (use 'c' for all columns, can be customized)
    col_spec = "c" * len(headers)
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\toprule")
    lines.append(" & ".join(headers) + " \\\\")
    lines.append("\\midrule")
    
    for row in rows:
        lines.append(" & ".join(row) + " \\\\")
    
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    lines.append("```")
    
    return "\n".join(lines)

def generate_tables(df: pd.DataFrame, stats: Dict, output_dir: Path):
    """Generate all tables for RQ1 analysis"""
    if df.empty:
        print("⚠️  Warning: No data available for table generation")
        return
    
    if "error" in stats:
        print(f"⚠️  Warning: Error in statistics: {stats.get('error')}")
        return
    
    table_dir = Path("visualization/table")
    table_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 Generating RQ1 tables...")
    
    # 1. Manipulation Detection by Vulnerability Type
    if stats.get("by_vulnerability_type"):
        headers = ["Vulnerability Type", "Total Probes", "Manipulation Detected", 
                  "Detection Rate (%)", "Agents Detected"]
        rows = []
        for vuln_type, data in sorted(stats["by_vulnerability_type"].items()):
            label = vuln_type.replace("_", " ").title()
            rate_pct = data['manipulation_rate'] * 100
            agents_str = ", ".join(map(str, data['agents_manipulating'])) if data['agents_manipulating'] else "None"
            rows.append([
                label,
                str(data['total_probes']),
                str(data['manipulation_detected']),
                _format_number(rate_pct, 1),
                agents_str
            ])
        
        md_table = _generate_markdown_table(headers, rows, 
                                           "Manipulation Detection by Vulnerability Type")
        latex_table = _generate_latex_table(headers, rows,
                                          "Manipulation Detection by Vulnerability Type",
                                          "tab:rq1_vulnerability")
        
        table_file = table_dir / "rq1_vulnerability_detection.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        print(f"  ✓ Generated: rq1_vulnerability_detection.md")
    
    # 2. Manipulation Detection by Seller
    if stats.get("by_agent"):
        headers = ["Seller ID", "Total Probes", "Manipulation Detected", "Detection Rate (%)"]
        rows = []
        for agent_id, data in sorted(stats["by_agent"].items()):
            rate_pct = data['manipulation_rate'] * 100
            rows.append([
                str(agent_id),
                str(data['total_probes']),
                str(data['manipulation_detected']),
                _format_number(rate_pct, 1)
            ])
        
        md_table = _generate_markdown_table(headers, rows, 
                                           "Manipulation Detection by Seller")
        latex_table = _generate_latex_table(headers, rows,
                                          "Manipulation Detection by Seller",
                                          "tab:rq1_seller")
        
        table_file = table_dir / "rq1_seller_detection.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        print(f"  ✓ Generated: rq1_seller_detection.md")
    
    # 3. Manipulation Detection by Round
    if stats.get("by_round"):
        headers = ["Round", "Total Probes", "Manipulation Detected", "Detection Rate (%)"]
        rows = []
        for round_num, data in sorted(stats["by_round"].items()):
            rate_pct = data['manipulation_rate'] * 100
            rows.append([
                str(round_num),
                str(data['total_probes']),
                str(data['manipulation_detected']),
                _format_number(rate_pct, 1)
            ])
        
        md_table = _generate_markdown_table(headers, rows, 
                                           "Manipulation Detection by Round")
        latex_table = _generate_latex_table(headers, rows,
                                          "Manipulation Detection by Round",
                                          "tab:rq1_round")
        
        table_file = table_dir / "rq1_round_detection.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        print(f"  ✓ Generated: rq1_round_detection.md")
    
    # 4. Overall Summary Statistics
    headers = ["Metric", "Value"]
    rows = [
        ["Total Probes", str(stats['total_probes'])],
        ["Manipulation Detected", str(stats['total_manipulation_detected'])],
        ["Overall Detection Rate (%)", _format_number(stats['overall_manipulation_rate'] * 100, 1)],
        ["Unique Agents", str(stats['unique_agents'])],
        ["Unique Rounds", str(stats['unique_rounds'])]
    ]
    
    md_table = _generate_markdown_table(headers, rows, 
                                       "RQ1 Overall Summary Statistics")
    latex_table = _generate_latex_table(headers, rows,
                                      "RQ1 Overall Summary Statistics",
                                      "tab:rq1_summary")
    
    table_file = table_dir / "rq1_summary_statistics.md"
    with open(table_file, 'w', encoding='utf-8') as f:
        f.write(md_table)
        f.write("\n\n")
        f.write(latex_table)
    print(f"  ✓ Generated: rq1_summary_statistics.md")
    
    print(f"\n✅ All tables generated in: {table_dir}")

def generate_comparison_tables(df_r: pd.DataFrame, stats_r: Dict, df_rw: pd.DataFrame, stats_rw: Dict):
    """Generate comparison tables for RQ1 analysis (Reputation Only vs Reputation + Warrant)"""
    table_dir = Path("visualization/table")
    table_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 Generating RQ1 comparison tables...")
    
    # 1. Manipulation Detection by Vulnerability Type (Comparison)
    if (stats_r.get("by_vulnerability_type") or stats_rw.get("by_vulnerability_type")):
        # Get all vulnerability types from both
        all_vuln_types = set()
        if stats_r.get("by_vulnerability_type"):
            all_vuln_types.update(stats_r["by_vulnerability_type"].keys())
        if stats_rw.get("by_vulnerability_type"):
            all_vuln_types.update(stats_rw["by_vulnerability_type"].keys())
        
        headers = ["Vulnerability Type", "R: Total Probes", "R: Detected", "R: Rate (%)",
                  "RW: Total Probes", "RW: Detected", "RW: Rate (%)"]
        rows = []
        
        for vuln_type in sorted(all_vuln_types):
            label = vuln_type.replace("_", " ").title()
            
            # Reputation Only data
            r_data = stats_r.get("by_vulnerability_type", {}).get(vuln_type, {})
            r_total = r_data.get('total_probes', 0) if r_data else 0
            r_detected = r_data.get('manipulation_detected', 0) if r_data else 0
            r_rate = r_data.get('manipulation_rate', 0) * 100 if r_data else 0
            
            # Reputation + Warrant data
            rw_data = stats_rw.get("by_vulnerability_type", {}).get(vuln_type, {})
            rw_total = rw_data.get('total_probes', 0) if rw_data else 0
            rw_detected = rw_data.get('manipulation_detected', 0) if rw_data else 0
            rw_rate = rw_data.get('manipulation_rate', 0) * 100 if rw_data else 0
            
            rows.append([
                label,
                str(r_total) if r_total > 0 else "N/A",
                str(r_detected) if r_total > 0 else "N/A",
                _format_number(r_rate, 1) if r_total > 0 else "N/A",
                str(rw_total) if rw_total > 0 else "N/A",
                str(rw_detected) if rw_total > 0 else "N/A",
                _format_number(rw_rate, 1) if rw_total > 0 else "N/A"
            ])
        
        md_table = _generate_markdown_table(headers, rows,
                                           "Manipulation Detection by Vulnerability Type (Comparison)")
        latex_table = _generate_latex_table(headers, rows,
                                          "Manipulation Detection by Vulnerability Type (Comparison)",
                                          "tab:rq1_vulnerability_comparison")
        
        table_file = table_dir / "rq1_vulnerability_detection_comparison.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        print(f"  ✓ Generated: rq1_vulnerability_detection_comparison.md")
    
    # 2. Manipulation Detection by Round (Comparison)
    if (stats_r.get("by_round") or stats_rw.get("by_round")):
        # Get all rounds from both
        all_rounds = set()
        if stats_r.get("by_round"):
            all_rounds.update(stats_r["by_round"].keys())
        if stats_rw.get("by_round"):
            all_rounds.update(stats_rw["by_round"].keys())
        
        headers = ["Round", "R: Total Probes", "R: Detected", "R: Rate (%)",
                  "RW: Total Probes", "RW: Detected", "RW: Rate (%)"]
        rows = []
        
        for round_num in sorted(all_rounds):
            # Reputation Only data
            r_data = stats_r.get("by_round", {}).get(round_num, {})
            r_total = r_data.get('total_probes', 0) if r_data else 0
            r_detected = r_data.get('manipulation_detected', 0) if r_data else 0
            r_rate = r_data.get('manipulation_rate', 0) * 100 if r_data else 0
            
            # Reputation + Warrant data
            rw_data = stats_rw.get("by_round", {}).get(round_num, {})
            rw_total = rw_data.get('total_probes', 0) if rw_data else 0
            rw_detected = rw_data.get('manipulation_detected', 0) if rw_data else 0
            rw_rate = rw_data.get('manipulation_rate', 0) * 100 if rw_data else 0
            
            rows.append([
                str(round_num),
                str(r_total) if r_total > 0 else "N/A",
                str(r_detected) if r_total > 0 else "N/A",
                _format_number(r_rate, 1) if r_total > 0 else "N/A",
                str(rw_total) if rw_total > 0 else "N/A",
                str(rw_detected) if rw_total > 0 else "N/A",
                _format_number(rw_rate, 1) if rw_total > 0 else "N/A"
            ])
        
        md_table = _generate_markdown_table(headers, rows,
                                           "Manipulation Detection by Round (Comparison)")
        latex_table = _generate_latex_table(headers, rows,
                                          "Manipulation Detection by Round (Comparison)",
                                          "tab:rq1_round_comparison")
        
        table_file = table_dir / "rq1_round_detection_comparison.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        print(f"  ✓ Generated: rq1_round_detection_comparison.md")
    
    # 3. Overall Summary Statistics (Comparison) - Vulnerability Detection Rates by Market Type
    # Define the 5 vulnerability types in standard order
    vulnerability_types = [
        ('initial_window', 'Initial Window'),
        ('reputation_lag', 'Reputation Lag'),
        ('value_imbalance', 'Value Imbalance'),
        ('reentry', 'Re-entry'),
        ('exit_strategy', 'Exit Strategy')
    ]
    
    headers = ["Market Type"] + [label for _, label in vulnerability_types]
    rows = []
    
    # Row 1: Reputation Only
    r_row = ["Reputation Only"]
    for vuln_type, _ in vulnerability_types:
        r_data = stats_r.get("by_vulnerability_type", {}).get(vuln_type, {}) if stats_r and 'error' not in stats_r else {}
        r_rate = r_data.get('manipulation_rate', 0) * 100 if r_data else 0
        r_row.append(_format_number(r_rate, 1) if r_data else "N/A")
    rows.append(r_row)
    
    # Row 2: Reputation + Warrant
    rw_row = ["Reputation + Warrant"]
    for vuln_type, _ in vulnerability_types:
        rw_data = stats_rw.get("by_vulnerability_type", {}).get(vuln_type, {}) if stats_rw and 'error' not in stats_rw else {}
        rw_rate = rw_data.get('manipulation_rate', 0) * 100 if rw_data else 0
        rw_row.append(_format_number(rw_rate, 1) if rw_data else "N/A")
    rows.append(rw_row)
    
    md_table = _generate_markdown_table(headers, rows,
                                       "RQ1 Manipulation Detection Rate by Vulnerability Type and Market Type")
    latex_table = _generate_latex_table(headers, rows,
                                      "RQ1 Manipulation Detection Rate by Vulnerability Type and Market Type",
                                      "tab:rq1_summary_comparison")
    
    table_file = table_dir / "rq1_summary_statistics_comparison.md"
    with open(table_file, 'w', encoding='utf-8') as f:
        f.write(md_table)
        f.write("\n\n")
        f.write(latex_table)
    print(f"  ✓ Generated: rq1_summary_statistics_comparison.md")
    
    # 4. Option Distribution by Vulnerability Type (Comparison)
    if (not df_r.empty and "selected_option" in df_r.columns) or \
       (not df_rw.empty and "selected_option" in df_rw.columns):
        # Get all vulnerability types from both dataframes
        all_vuln_types = set()
        if not df_r.empty and "vulnerability_type" in df_r.columns:
            all_vuln_types.update(df_r["vulnerability_type"].unique())
        if not df_rw.empty and "vulnerability_type" in df_rw.columns:
            all_vuln_types.update(df_rw["vulnerability_type"].unique())
        
        headers = ["Vulnerability Type", "R: Option A", "R: Option B", "R: Option C",
                  "RW: Option A", "RW: Option B", "RW: Option C"]
        rows = []
        
        for vuln_type in sorted(all_vuln_types):
            label = vuln_type.replace("_", " ").title()
            
            # Reputation Only option counts
            r_subset = df_r[df_r["vulnerability_type"] == vuln_type] if not df_r.empty else pd.DataFrame()
            r_option_counts = r_subset["selected_option"].value_counts().to_dict() if not r_subset.empty and "selected_option" in r_subset.columns else {}
            r_a = r_option_counts.get("A", 0)
            r_b = r_option_counts.get("B", 0)
            r_c = r_option_counts.get("C", 0)
            
            # Reputation + Warrant option counts
            rw_subset = df_rw[df_rw["vulnerability_type"] == vuln_type] if not df_rw.empty else pd.DataFrame()
            rw_option_counts = rw_subset["selected_option"].value_counts().to_dict() if not rw_subset.empty and "selected_option" in rw_subset.columns else {}
            rw_a = rw_option_counts.get("A", 0)
            rw_b = rw_option_counts.get("B", 0)
            rw_c = rw_option_counts.get("C", 0)
            
            rows.append([
                label,
                str(r_a) if not r_subset.empty else "N/A",
                str(r_b) if not r_subset.empty else "N/A",
                str(r_c) if not r_subset.empty else "N/A",
                str(rw_a) if not rw_subset.empty else "N/A",
                str(rw_b) if not rw_subset.empty else "N/A",
                str(rw_c) if not rw_subset.empty else "N/A"
            ])
        
        md_table = _generate_markdown_table(headers, rows,
                                           "Option Distribution by Vulnerability Type (Comparison)")
        latex_table = _generate_latex_table(headers, rows,
                                          "Option Distribution by Vulnerability Type (Comparison)",
                                          "tab:rq1_option_comparison")
        
        table_file = table_dir / "rq1_option_distribution_comparison.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        print(f"  ✓ Generated: rq1_option_distribution_comparison.md")
    
    print(f"\n✅ All comparison tables generated in: {table_dir}")

def extract_prefix_from_path(path_str: str) -> str:
    """Extract prefix from path (e.g., 'experiments/1230/r_wo' -> '1230', '1230/r_wo' -> '1230')"""
    path = Path(path_str)
    parts = path.parts
    
    # First, try to find pattern like 'experiments/1230/xxx' or '1230/xxx'
    for i, part in enumerate(parts):
        # Check if this part contains a slash (like '1230/r_wo')
        if '/' in part:
            prefix = part.split('/')[0]
            if prefix:
                return prefix
        # Check if this part is a numeric prefix and next part exists (like '1230' followed by 'r_wo')
        if part and part[0].isdigit() and i + 1 < len(parts):
            return part
    
    # Fallback: look for any numeric prefix
    for part in parts:
        if part and part[0].isdigit():
            return part
    
    # Try to extract from paper/rq1/r_wo format
    if 'paper' in parts:
        return 'paper'
    
    return ""

def plot_comparison_manipulation_heatmap(df_r: pd.DataFrame, df_rw: pd.DataFrame, output_path: Path):
    """Create side-by-side heatmap comparison of manipulation detection rates."""
    if df_r.empty and df_rw.empty:
        print("No data to plot for comparison.")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(24, 8))
    
    rename_map = {
        'initial_window': 'Initial Window',
        'reputation_lag': 'Reputation Lag',
        'value_imbalance': 'Value Imbalance',
        'reentry': 'Re-entry',
        'exit_strategy': 'Exit Strategy'
    }
    
    sns.set_theme(style="white")
    
    for idx, (df, label, ax) in enumerate([(df_r, "Reputation Only", axes[0]), (df_rw, "Reputation + Warrant", axes[1])]):
        if df.empty:
            ax.text(0.5, 0.5, f"No data for {label}", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(label, fontsize=14, fontweight='bold', pad=20)
            continue
        
        # Calculate detection rate
        stats = df.groupby(['agent_id', 'vulnerability_type']).agg(
            detected_count=('manipulation_detected', 'sum'),
            total_count=('manipulation_detected', 'count')
        ).reset_index()
        
        stats['detection_rate'] = stats['detected_count'] / stats['total_count']
        
        # Pivot for heatmap
        pivot_df = stats.pivot(index='agent_id', columns='vulnerability_type', values='detection_rate')
        pivot_df = pivot_df.sort_index()
        pivot_df.columns = [rename_map.get(col, col) for col in pivot_df.columns]
        
        sns.heatmap(
            pivot_df,
            annot=True,
            fmt=".2f",
            cmap="YlOrRd",
            linewidths=.5,
            cbar_kws={'label': 'Detection Rate'},
            vmin=0, vmax=1,
            ax=ax
        )
        
        ax.set_title(label, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Probe Type (Manipulation Strategy)', fontsize=12, fontweight='bold')
        if idx == 0:
            ax.set_ylabel('Seller ID', fontsize=12, fontweight='bold')
        else:
            ax.set_ylabel('')
    
    plt.suptitle('RQ1: Cognitive Manipulation Detection Rate Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated comparison heatmap: {output_path}")

def plot_comparison_manipulation_by_vulnerability(stats_r: Dict, stats_rw: Dict, output_path: Path):
    """Create side-by-side bar chart comparison of manipulation rates by vulnerability type."""
    if ("by_vulnerability_type" not in stats_r or not stats_r["by_vulnerability_type"]) and \
       ("by_vulnerability_type" not in stats_rw or not stats_rw["by_vulnerability_type"]):
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(24, 6))
    
    for idx, (stats, label, ax) in enumerate([(stats_r, "Reputation Only", axes[0]), (stats_rw, "Reputation + Warrant", axes[1])]):
        if "by_vulnerability_type" not in stats or not stats["by_vulnerability_type"]:
            ax.text(0.5, 0.5, f"No data for {label}", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(label, fontsize=14, fontweight='bold')
            continue
        
        vuln_data = stats["by_vulnerability_type"]
        vuln_types = list(vuln_data.keys())
        rates = [vuln_data[v]["manipulation_rate"] * 100 for v in vuln_types]
        counts = [vuln_data[v]["manipulation_detected"] for v in vuln_types]
        totals = [vuln_data[v]["total_probes"] for v in vuln_types]
        labels = [v.replace("_", " ").title() for v in vuln_types]
        
        colors = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71", "#9b59b6"]
        bars = ax.bar(labels, rates, color=colors[:len(labels)], edgecolor="black", linewidth=1.2)
        
        for bar, count, total in zip(bars, counts, totals):
            height = bar.get_height()
            ax.annotate(
                f"{height:.1f}%\n({count}/{total})",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )
        
        ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=12)
        ax.set_xlabel("Vulnerability Type", fontsize=12)
        ax.set_title(label, fontsize=14, fontweight="bold")
        ax.set_ylim(0, max(rates) * 1.3 if rates else 100)
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha="right")
    
    plt.suptitle('RQ1: Manipulation Detection Rate by Vulnerability Type Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated comparison vulnerability chart: {output_path}")

def plot_comparison_manipulation_over_rounds(stats_r: Dict, stats_rw: Dict, output_path: Path):
    """Create side-by-side line chart comparison of manipulation trends over rounds."""
    if ("by_round" not in stats_r or not stats_r["by_round"]) and \
       ("by_round" not in stats_rw or not stats_rw["by_round"]):
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(24, 6))
    
    for idx, (stats, label, ax, color) in enumerate([
        (stats_r, "Reputation Only", axes[0], "#d62728"),
        (stats_rw, "Reputation + Warrant", axes[1], "#1f77b4")
    ]):
        if "by_round" not in stats or not stats["by_round"]:
            ax.text(0.5, 0.5, f"No data for {label}", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(label, fontsize=14, fontweight='bold')
            continue
        
        round_data = stats["by_round"]
        rounds = sorted(round_data.keys())
        rates = [round_data[r]["manipulation_rate"] * 100 for r in rounds]
        
        ax.plot(rounds, rates, marker="o", linewidth=2, markersize=8, color=color)
        ax.fill_between(rounds, rates, alpha=0.3, color=color)
        
        ax.set_xlabel("Round Number", fontsize=12)
        ax.set_ylabel("Manipulation Detection Rate (%)", fontsize=12)
        ax.set_title(label, fontsize=14, fontweight="bold")
        ax.set_xticks(rounds)
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)
        
        if len(rounds) >= 2:
            ax.axvspan(0.5, 2.5, alpha=0.2, color="yellow", label="Initial Window")
            ax.legend()
    
    plt.suptitle('RQ1: Manipulation Behavior Over Time Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated comparison temporal trend: {output_path}")

def plot_comparison_option_distribution(df_r: pd.DataFrame, df_rw: pd.DataFrame, output_path: Path):
    """Create side-by-side stacked bar chart comparison of option selections."""
    if df_r.empty and df_rw.empty:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(24, 6))
    
    for idx, (df, label, ax) in enumerate([(df_r, "Reputation Only", axes[0]), (df_rw, "Reputation + Warrant", axes[1])]):
        if df.empty or "selected_option" not in df.columns:
            ax.text(0.5, 0.5, f"No data for {label}", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(label, fontsize=14, fontweight='bold')
            continue
        
        option_counts = df.groupby(["vulnerability_type", "selected_option"]).size().unstack(fill_value=0)
        option_counts.index = [v.replace("_", " ").title() for v in option_counts.index]
        
        colors = {"A": "#e74c3c", "B": "#2ecc71", "C": "#3498db", None: "#95a5a6"}
        bottom = np.zeros(len(option_counts))
        
        for option in ["A", "B", "C"]:
            if option in option_counts.columns:
                values = option_counts[option].values
                ax.bar(option_counts.index, values, bottom=bottom, label=f"Option {option}", color=colors.get(option, "#95a5a6"))
                bottom += values
        
        ax.set_xlabel("Vulnerability Type", fontsize=12)
        ax.set_ylabel("Number of Responses", fontsize=12)
        ax.set_title(label, fontsize=14, fontweight="bold")
        ax.legend(title="Selected Option")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha="right")
    
    plt.suptitle('RQ1: Response Distribution by Vulnerability Type Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated comparison option distribution: {output_path}")

def generate_comparison_analysis(r_input_dir: str, rw_input_dir: str, output_dir: Path):
    """Generate comparison analysis between two market types."""
    print(f"\n📊 Generating comparison analysis...")
    print(f"  Reputation Only: {r_input_dir}")
    print(f"  Reputation + Warrant: {rw_input_dir}")
    
    df_r = load_probe_results(r_input_dir)
    df_rw = load_probe_results(rw_input_dir)
    
    if df_r.empty and df_rw.empty:
        print("  ⚠️  Warning: No data available for comparison")
        return
    
    stats_r = calculate_statistics(df_r) if not df_r.empty else {}
    stats_rw = calculate_statistics(df_rw) if not df_rw.empty else {}
    
    # Generate comparison visualizations
    plot_comparison_manipulation_heatmap(df_r, df_rw, output_dir / "comparison_1_manipulation_heatmap.png")
    plot_comparison_manipulation_by_vulnerability(stats_r, stats_rw, output_dir / "comparison_2_manipulation_by_vulnerability.png")
    plot_comparison_manipulation_over_rounds(stats_r, stats_rw, output_dir / "comparison_3_manipulation_over_rounds.png")
    plot_comparison_option_distribution(df_r, df_rw, output_dir / "comparison_4_option_distribution.png")
    
    # Generate comparison tables
    try:
        generate_comparison_tables(df_r, stats_r, df_rw, stats_rw)
    except Exception as e:
        print(f"  ⚠️  Warning: Comparison table generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"  ✅ Comparison analysis complete!")

def main():
    parser = argparse.ArgumentParser(description="Visualize RQ1 Cognitive Probe Results")
    parser.add_argument("--input-dir", type=str, default=None, help="Directory containing run_*_cognitive_probes.json (for single analysis)")
    parser.add_argument("--r-input-dir", type=str, default=None, help="Reputation Only input directory (for comparison)")
    parser.add_argument("--rw-input-dir", type=str, default=None, help="Reputation + Warrant input directory (for comparison)")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save figures")
    parser.add_argument("--save-stats", action="store_true", help="Save statistics JSON file")
    
    args = parser.parse_args()
    
    # Determine if this is a comparison or single analysis
    is_comparison = args.r_input_dir is not None and args.rw_input_dir is not None
    
    if is_comparison:
        # Comparison mode
        r_input_path = Path(args.r_input_dir)
        rw_input_path = Path(args.rw_input_dir)
        
        # Determine output directory
        if args.output_dir is None:
            prefix = extract_prefix_from_path(args.r_input_dir)
            if prefix:
                output_dir = Path(f"visualization/figs/{prefix}/rq1_comparison")
            else:
                output_dir = Path("visualization/figs/rq1_comparison")
        else:
            output_dir = Path(args.output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate individual analyses
        print("="*70)
        print("RQ1: Individual Market Type Analysis")
        print("="*70)
        
        # Reputation Only analysis
        r_output_dir = output_dir / "r_wo"
        r_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📊 Analyzing Reputation Only market...")
        df_r = load_probe_results(args.r_input_dir)
        if not df_r.empty:
            stats_r = calculate_statistics(df_r)
            if args.save_stats:
                import json
                stats_path = r_output_dir / "rq1_statistics.json"
                with open(stats_path, "w") as f:
                    json.dump(stats_r, f, indent=2, default=str)
            plot_manipulation_heatmap(df_r, r_output_dir / "1_manipulation_heatmap.png")
            plot_manipulation_by_vulnerability(stats_r, r_output_dir / "2_manipulation_by_vulnerability.png")
            plot_manipulation_over_rounds(stats_r, r_output_dir / "3_manipulation_over_rounds.png")
            plot_option_distribution(df_r, r_output_dir / "4_option_distribution.png")
            plot_reputation_lag_severity(df_r, r_output_dir / "5_reputation_lag_severity.png")
            print_summary_report(stats_r)
            print(f"  ✅ Reputation Only analysis saved to: {r_output_dir}")
        else:
            print(f"  ⚠️  Warning: No data found for Reputation Only")
        
        # Reputation + Warrant analysis
        rw_output_dir = output_dir / "rw_wo"
        rw_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📊 Analyzing Reputation + Warrant market...")
        df_rw = load_probe_results(args.rw_input_dir)
        if not df_rw.empty:
            stats_rw = calculate_statistics(df_rw)
            if args.save_stats:
                import json
                stats_path = rw_output_dir / "rq1_statistics.json"
                with open(stats_path, "w") as f:
                    json.dump(stats_rw, f, indent=2, default=str)
            plot_manipulation_heatmap(df_rw, rw_output_dir / "1_manipulation_heatmap.png")
            plot_manipulation_by_vulnerability(stats_rw, rw_output_dir / "2_manipulation_by_vulnerability.png")
            plot_manipulation_over_rounds(stats_rw, rw_output_dir / "3_manipulation_over_rounds.png")
            plot_option_distribution(df_rw, rw_output_dir / "4_option_distribution.png")
            plot_reputation_lag_severity(df_rw, rw_output_dir / "5_reputation_lag_severity.png")
            print_summary_report(stats_rw)
            print(f"  ✅ Reputation + Warrant analysis saved to: {rw_output_dir}")
        else:
            print(f"  ⚠️  Warning: No data found for Reputation + Warrant")
        
        # Generate comparison analysis
        print("\n" + "="*70)
        print("RQ1: Comparison Analysis")
        print("="*70)
        generate_comparison_analysis(args.r_input_dir, args.rw_input_dir, output_dir)
        
        print(f"\n✅ All analyses complete! Results saved to: {output_dir}")
        
    else:
        # Single analysis mode (backward compatibility)
        if args.input_dir is None:
            print("ERROR: Either --input-dir or both --r-input-dir and --rw-input-dir must be provided")
            return
        
        input_path = Path(args.input_dir)
        
        # Determine output directory
        if args.output_dir is None:
            prefix = extract_prefix_from_path(args.input_dir)
            if prefix:
                output_dir = Path(f"visualization/figs/{prefix}/rq1_analysis")
            else:
                output_dir = Path("visualization/figs/rq1_analysis")
        else:
            output_dir = Path(args.output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Analyzing probe results in {input_path}...")
        if not input_path.exists():
            print(f"ERROR: Input directory does not exist: {input_path}")
            print(f"Please check the experiment directory path.")
            return
        
        df = load_probe_results(args.input_dir)
        
        if df.empty:
            print("\n" + "="*70)
            print("ERROR: No data available for visualization")
            print("="*70)
            print(f"Input directory: {input_path}")
            print(f"Output directory: {output_dir}")
            print("\nPossible reasons:")
            print("  1. RQ1 experiment did not generate cognitive probe files")
            print("  2. Cognitive probe files are missing or in wrong location")
            print("  3. Experiment did not complete successfully")
            print("\nTo fix:")
            print("  1. Re-run RQ1 experiment: python example/run_rq1_experiment.py ...")
            print("  2. Check that cognitive probes are enabled and running")
            print("  3. Verify files are saved as: run_*_cognitive_probes.json")
            print("="*70)
            return
        
        print(f"   Loaded {len(df)} probe results")
        
        # Calculate statistics
        print(f"\n📊 Calculating statistics...")
        stats = calculate_statistics(df)
        
        # Save statistics if requested
        if args.save_stats:
            import json
            stats_path = output_dir / "rq1_statistics.json"
            with open(stats_path, "w") as f:
                json.dump(stats, f, indent=2, default=str)
            print(f"   Saved: {stats_path}")
        
        # Generate visualizations
        print(f"\n📈 Generating visualizations...")
        
        # 1. Heatmap (agent x vulnerability type)
        plot_manipulation_heatmap(df, output_dir / "1_manipulation_heatmap.png")
        
        # 2. Manipulation rate by vulnerability type
        plot_manipulation_by_vulnerability(stats, output_dir / "2_manipulation_by_vulnerability.png")
        
        # 3. Manipulation trends over rounds
        plot_manipulation_over_rounds(stats, output_dir / "3_manipulation_over_rounds.png")
        
        # 4. Option distribution
        plot_option_distribution(df, output_dir / "4_option_distribution.png")
        
        # 5. Reputation lag severity
        plot_reputation_lag_severity(df, output_dir / "5_reputation_lag_severity.png")
        
        # Print summary report
        print_summary_report(stats)
        
        # Generate tables
        try:
            generate_tables(df, stats, output_dir)
        except Exception as e:
            print(f"⚠️  Warning: Table generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ Analysis complete! Results saved to: {output_dir}")

if __name__ == "__main__":
    main()
