#!/usr/bin/env python3
"""
RQ1 Analysis: Cognitive Probing Results Analyzer

This script analyzes cognitive probing results and generates visualizations
for studying reputation manipulation behavior.

Usage:
    python analysis/analyze_rq1.py <experiment_dir>
    python analysis/analyze_rq1.py experiments/rq1_20251225_120000

Output:
    - Manipulation rate by vulnerability type (bar chart)
    - Manipulation trends across rounds (line chart)
    - Agent-level manipulation profiles (heatmap)
    - Severity distribution for reputation lag (histogram)
    - Summary statistics (JSON)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Any

import pandas as pd
import numpy as np

# Try importing visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Charts will not be generated.")

try:
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


def load_probe_results(experiment_dir: str) -> List[Dict]:
    """Load all probe results from experiment directory"""
    all_results = []

    # Find all probe result files
    for filename in os.listdir(experiment_dir):
        if filename.endswith("_cognitive_probes.json"):
            filepath = os.path.join(experiment_dir, filename)
            with open(filepath, "r") as f:
                results = json.load(f)
                # Add run identifier
                run_id = filename.replace("_cognitive_probes.json", "").replace(
                    "run_", ""
                )
                for r in results:
                    r["run_id"] = run_id
                all_results.extend(results)

    return all_results


def calculate_statistics(results: List[Dict]) -> Dict[str, Any]:
    """Calculate aggregate statistics"""
    if not results:
        return {"error": "No results found"}

    df = pd.DataFrame(results)

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


def plot_manipulation_by_vulnerability(stats: Dict, output_dir: str):
    """Create bar chart of manipulation rates by vulnerability type"""
    if not HAS_MATPLOTLIB:
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

    output_path = os.path.join(output_dir, "rq1_manipulation_by_vulnerability.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


def plot_manipulation_over_rounds(stats: Dict, output_dir: str):
    """Create line chart of manipulation trends over rounds"""
    if not HAS_MATPLOTLIB:
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

    output_path = os.path.join(output_dir, "rq1_manipulation_over_rounds.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


def plot_agent_manipulation_heatmap(results: List[Dict], output_dir: str):
    """Create heatmap of agent manipulation by vulnerability type"""
    if not HAS_MATPLOTLIB or not HAS_SEABORN:
        return

    df = pd.DataFrame(results)

    # Pivot to create agent x vulnerability matrix
    pivot = df.pivot_table(
        index="agent_id",
        columns="vulnerability_type",
        values="manipulation_detected",
        aggfunc="mean",
    ).fillna(0)

    # Clean column names
    pivot.columns = [c.replace("_", " ").title() for c in pivot.columns]

    fig, ax = plt.subplots(figsize=(12, 8))

    sns.heatmap(
        pivot * 100,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn_r",
        cbar_kws={"label": "Manipulation Rate (%)"},
        ax=ax,
        linewidths=0.5,
    )

    ax.set_xlabel("Vulnerability Type", fontsize=12)
    ax.set_ylabel("Agent ID", fontsize=12)
    ax.set_title(
        "RQ1: Agent Manipulation Profiles by Vulnerability Type",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()

    output_path = os.path.join(output_dir, "rq1_agent_heatmap.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


def plot_option_distribution(results: List[Dict], output_dir: str):
    """Create stacked bar chart of option selections"""
    if not HAS_MATPLOTLIB:
        return

    df = pd.DataFrame(results)

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

    output_path = os.path.join(output_dir, "rq1_option_distribution.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


def plot_reputation_lag_severity(results: List[Dict], output_dir: str):
    """Create histogram of expected reputation lag values"""
    if not HAS_MATPLOTLIB:
        return

    df = pd.DataFrame(results)
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

    output_path = os.path.join(output_dir, "rq1_reputation_lag_severity.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


def print_summary_report(stats: Dict):
    """Print formatted summary report"""
    print("\n" + "=" * 70)
    print("RQ1 COGNITIVE PROBING ANALYSIS REPORT")
    print("=" * 70)

    print(f"\n📊 OVERVIEW")
    print(f"  Total Probes: {stats['total_probes']}")
    print(f"  Manipulation Detected: {stats['total_manipulation_detected']}")
    print(f"  Overall Rate: {stats['overall_manipulation_rate']*100:.1f}%")
    print(f"  Unique Agents: {stats['unique_agents']}")
    print(f"  Unique Rounds: {stats['unique_rounds']}")

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
    if stats["by_vulnerability_type"]:
        most_exploited = max(
            stats["by_vulnerability_type"].items(),
            key=lambda x: x[1]["manipulation_rate"],
        )
        print(
            f"  Most Exploited: {most_exploited[0].replace('_', ' ').title()} ({most_exploited[1]['manipulation_rate']*100:.1f}%)"
        )

    # Find most manipulative agent
    if stats["by_agent"]:
        most_manipulative = max(
            stats["by_agent"].items(), key=lambda x: x[1]["manipulation_rate"]
        )
        print(
            f"  Most Manipulative Agent: Agent {most_manipulative[0]} ({most_manipulative[1]['manipulation_rate']*100:.1f}%)"
        )

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze RQ1 Cognitive Probing Results"
    )
    parser.add_argument("experiment_dir", type=str, help="Path to experiment directory")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for charts (default: experiment_dir/analysis)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.experiment_dir):
        print(f"Error: Directory not found: {args.experiment_dir}")
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(args.experiment_dir, "analysis")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n📂 Loading probe results from: {args.experiment_dir}")

    # Load results
    results = load_probe_results(args.experiment_dir)

    if not results:
        print("No probe results found. Make sure the experiment has completed.")
        sys.exit(1)

    print(f"   Loaded {len(results)} probe results")

    # Calculate statistics
    print(f"\n📊 Calculating statistics...")
    stats = calculate_statistics(results)

    # Save statistics
    stats_path = os.path.join(output_dir, "rq1_statistics.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"   Saved: {stats_path}")

    # Generate visualizations
    print(f"\n📈 Generating visualizations...")
    plot_manipulation_by_vulnerability(stats, output_dir)
    plot_manipulation_over_rounds(stats, output_dir)
    plot_agent_manipulation_heatmap(results, output_dir)
    plot_option_distribution(results, output_dir)
    plot_reputation_lag_severity(results, output_dir)

    # Print report
    print_summary_report(stats)

    print(f"\n✅ Analysis complete! Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
