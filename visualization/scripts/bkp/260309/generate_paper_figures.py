#!/usr/bin/env python3
"""
Generate Paper Figures

This script generates figures in the exact format required for the ICML 2025 paper.
All figures use academic formatting with proper captions and labels.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import json
import numpy as np

# Set academic style
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid", {'font.family': 'serif'})


def load_experiment_data(experiment_dir: str) -> pd.DataFrame:
    """Load experimental data from directory."""
    path = Path(experiment_dir)
    all_results = []

    if not path.exists():
        print(f"Warning: Directory {experiment_dir} does not exist")
        return pd.DataFrame()

    # Find result files
    result_files = list(path.glob("run_*_results.json"))
    for file in result_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                run_id = file.stem.replace("_results", "").replace("run_", "")
                for item in data:
                    item["run_id"] = run_id
                all_results.extend(data)
        except Exception as e:
            print(f"Error loading {file}: {e}")

    return pd.DataFrame(all_results)


def generate_round_evolution_comparison(
    r_data: pd.DataFrame,
    rw_data: pd.DataFrame,
    output_path: Path
):
    """
    Generate round evolution comparison figure.

    This figure shows the evolution of key market indicators across rounds
    under different mechanism conditions.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Evolution of Key Market Indicators Across Rounds', fontsize=13, fontweight='bold')

    rounds = sorted(r_data['round_num'].unique())

    # Plot 1: Reputation Evolution
    ax = axes[0, 0]
    r_reputation = r_data.groupby('round_num')['reputation'].mean()
    rw_reputation = rw_data.groupby('round_num')['reputation'].mean()

    ax.plot(rounds, r_reputation, 'o-', label='Rep', linewidth=2, markersize=4)
    ax.plot(rounds, rw_reputation, 's-', label='Rep+Warrant', linewidth=2, markersize=4)
    ax.set_xlabel('Round')
    ax.set_ylabel('Reputation')
    ax.set_title('Reputation Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: Transaction Volume
    ax = axes[0, 1]
    r_transactions = r_data.groupby('round_num')['transactions'].mean()
    rw_transactions = rw_data.groupby('round_num')['transactions'].mean()

    ax.plot(rounds, r_transactions, 'o-', label='Rep', linewidth=2, markersize=4)
    ax.plot(rounds, rw_transactions, 's-', label='Rep+Warrant', linewidth=2, markersize=4)
    ax.set_xlabel('Round')
    ax.set_ylabel('Transactions')
    ax.set_title('Transaction Volume')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: Seller Profit
    ax = axes[1, 0]
    r_profit = r_data.groupby('round_num')['seller_profit'].mean()
    rw_profit = rw_data.groupby('round_num')['seller_profit'].mean()

    ax.plot(rounds, r_profit, 'o-', label='Rep', linewidth=2, markersize=4)
    ax.plot(rounds, rw_profit, 's-', label='Rep+Warrant', linewidth=2, markersize=4)
    ax.set_xlabel('Round')
    ax.set_ylabel('Seller Profit')
    ax.set_title('Seller Profit Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Buyer Utility
    ax = axes[1, 1]
    r_utility = r_data.groupby('round_num')['buyer_utility'].mean()
    rw_utility = rw_data.groupby('round_num')['buyer_utility'].mean()

    ax.plot(rounds, r_utility, 'o-', label='Rep', linewidth=2, markersize=4)
    ax.plot(rounds, rw_utility, 's-', label='Rep+Warrant', linewidth=2, markersize=4)
    ax.set_xlabel('Round')
    ax.set_ylabel('Buyer Utility')
    ax.set_title('Buyer Utility Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'round_evolution_comparison_pressure.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Generated: {output_path / 'round_evolution_comparison_pressure.png'}")


def generate_comparison_by_constraints(
    policy_data: Dict[str, pd.DataFrame],
    output_path: Path
):
    """
    Generate comparison across different constraint types.

    Shows how different mechanisms perform under different constraint conditions.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Market Outcomes by Constraint Type', fontsize=13, fontweight='bold')

    constraints = list(policy_data.keys())

    # Prepare data
    constraint_names = [c.replace('_', '-').title() for c in constraints]
    rep_profits = []
    rw_profits = []

    for constraint in constraints:
        data = policy_data[constraint]
        rep_profit = data[data['condition'] == 'Rep']['seller_profit'].mean()
        rw_profit = data[data['condition'] == 'Rep+Warrant']['seller_profit'].mean()
        rep_profits.append(rep_profit)
        rw_profits.append(rw_profit)

    # Plot 1: Seller Profit by Constraint
    ax = axes[0, 0]
    x = np.arange(len(constraint_names))
    width = 0.35

    ax.bar(x - width/2, rep_profits, width, label='Rep', alpha=0.8)
    ax.bar(x + width/2, rw_profits, width, label='Rep+Warrant', alpha=0.8)
    ax.set_xlabel('Constraint Type')
    ax.set_ylabel('Seller Profit')
    ax.set_title('Seller Profit by Constraint')
    ax.set_xticks(x)
    ax.set_xticklabels(constraint_names, rotation=15)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add more plots as needed...

    plt.tight_layout()
    plt.savefig(output_path / 'comparison_by_constraints.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Generated: {output_path / 'comparison_by_constraints.png'}")


def generate_paper_figures(
    r_dir: str,
    rw_dir: str,
    output_dir: str,
    constraint_dirs: List[str] = None
):
    """Generate all paper figures."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Generating Paper Figures")
    print("=" * 70)

    # Load data
    print("\nLoading experimental data...")
    r_data = load_experiment_data(r_dir)
    rw_data = load_experiment_data(rw_dir)

    if r_data.empty or rw_data.empty:
        print("Warning: Missing data, skipping figure generation")
        return

    # Generate round evolution comparison
    print("\nGenerating round evolution comparison...")
    generate_round_evolution_comparison(r_data, rw_data, output_path)

    # Generate constraint comparison if data available
    if constraint_dirs:
        print("\nGenerating constraint comparison...")
        constraint_data = {}
        for constraint_dir in constraint_dirs:
            data = load_experiment_data(constraint_dir)
            if not data.empty:
                constraint_name = Path(constraint_dir).name
                constraint_data[constraint_name] = data

        if constraint_data:
            generate_comparison_by_constraints(constraint_data, output_path)

    print("\n" + "=" * 70)
    print("Paper figures generated successfully!")
    print("=" * 70)
    print(f"Output directory: {output_path}")
    print("\nGenerated figures:")
    for f in output_path.glob("*.png"):
        print(f"  - {f.name}")


def main():
    parser = argparse.ArgumentParser(description="Generate Paper Figures")
    parser.add_argument("--r-dir", type=str, required=True,
                       help="Reputation Only experiment directory")
    parser.add_argument("--rw-dir", type=str, required=True,
                       help="Reputation+Warrant experiment directory")
    parser.add_argument("--constraint-dirs", type=str, nargs='+', default=[],
                       help="Constraint-specific experiment directories")
    parser.add_argument("--output-dir", type=str, default="visualization/figs/paper",
                       help="Output directory for figures")

    args = parser.parse_args()

    generate_paper_figures(
        args.r_dir,
        args.rw_dir,
        args.output_dir,
        args.constraint_dirs
    )


if __name__ == "__main__":
    main()
