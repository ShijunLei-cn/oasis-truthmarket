#!/usr/bin/env python3
"""
Ablation Study Visualization
Generates comparison graphs and tables for ablation study results
"""

import json
import os
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Academic plotting style
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif"]
plt.rcParams["font.size"] = 11
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["figure.titlesize"] = 14
sns.set_style("whitegrid")


class AblationVisualizer:
    """Visualizer for ablation study results"""

    def __init__(self, ablation_base: str):
        """
        Initialize with ablation experiment base path

        Args:
            ablation_base: Path like 'ablation/temperature_20260123_120000'
        """
        self.ablation_base = ablation_base
        self.exp_dir = Path(f"experiments/{ablation_base}")
        self.output_dir = Path(
            f"visualization/figs/ablation/{Path(ablation_base).name}"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load metadata
        self.metadata = self._load_metadata()

        # Load data for all conditions
        self.data = self._load_all_data()

    def _load_metadata(self) -> Dict:
        """Load ablation study metadata"""
        meta_path = self.exp_dir / "ablation_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                return json.load(f)
        return {}

    def _load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load data from all conditions"""
        data = {}

        for condition in self.metadata.get("conditions", []):
            name = condition["name"]
            exp_id = condition["exp_id"]

            condition_data = self._load_condition_data(exp_id)
            if not condition_data.empty:
                data[name] = condition_data

        return data

    def _load_condition_data(self, exp_id: str) -> pd.DataFrame:
        """Load data from a single condition's database files"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_data = []

        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split("_")[1])

            try:
                conn = sqlite3.connect(db_file)

                # Get transactions summary with deception calculated from product table
                trans_df = pd.read_sql_query(
                    """
                    SELECT 
                        t.round_number,
                        COUNT(*) as transactions,
                        SUM(t.seller_profit) as total_seller_profit,
                        SUM(t.buyer_utility) as total_buyer_utility,
                        SUM(CASE WHEN p.advertised_quality != p.true_quality THEN 1 ELSE 0 END) as deceptions
                    FROM transactions t
                    JOIN product p ON t.product_id = p.product_id
                    GROUP BY t.round_number
                """,
                    conn,
                )

                # Get products summary
                prod_df = pd.read_sql_query(
                    """
                    SELECT 
                        round_number,
                        COUNT(*) as products_listed,
                        SUM(CASE WHEN advertised_quality != true_quality THEN 1 ELSE 0 END) as fraudulent_listings
                    FROM product
                    GROUP BY round_number
                """,
                    conn,
                )

                conn.close()

                # Merge and add run_id
                if not trans_df.empty:
                    merged = trans_df.merge(prod_df, on="round_number", how="outer")
                    merged["run_id"] = run_id
                    all_data.append(merged)

            except Exception as e:
                print(f"Error loading {db_file}: {e}")

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    def compute_metrics(self) -> pd.DataFrame:
        """Compute aggregate metrics for each condition"""
        metrics = []

        for condition, df in self.data.items():
            if df.empty:
                continue

            # Aggregate across runs
            total_trans = df["transactions"].sum()
            total_deceptions = df["deceptions"].sum()

            metrics.append(
                {
                    "condition": condition,
                    "avg_transactions": df.groupby("run_id")["transactions"]
                    .sum()
                    .mean(),
                    "std_transactions": df.groupby("run_id")["transactions"]
                    .sum()
                    .std(),
                    "avg_seller_profit": df.groupby("run_id")["total_seller_profit"]
                    .sum()
                    .mean(),
                    "std_seller_profit": df.groupby("run_id")["total_seller_profit"]
                    .sum()
                    .std(),
                    "avg_buyer_utility": df.groupby("run_id")["total_buyer_utility"]
                    .sum()
                    .mean(),
                    "std_buyer_utility": df.groupby("run_id")["total_buyer_utility"]
                    .sum()
                    .std(),
                    "deception_rate": (
                        total_deceptions / total_trans if total_trans > 0 else 0
                    ),
                    "total_deceptions": total_deceptions,
                    "total_transactions": total_trans,
                }
            )

        return pd.DataFrame(metrics)

    def plot_metric_comparison(
        self, metric: str, title: str, ylabel: str, filename: str
    ):
        """Create bar chart comparing a metric across conditions"""
        metrics_df = self.compute_metrics()

        if metrics_df.empty:
            print(f"No data available for {metric}")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        conditions = metrics_df["condition"].tolist()
        values = metrics_df[f"avg_{metric}"].tolist()
        errors = metrics_df[f"std_{metric}"].tolist()

        x = np.arange(len(conditions))
        colors = sns.color_palette("husl", len(conditions))

        bars = ax.bar(
            x,
            values,
            yerr=errors,
            capsize=5,
            color=colors,
            edgecolor="black",
            linewidth=1,
        )

        ax.set_xlabel("Condition")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(conditions, rotation=45, ha="right")

        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Saved: {self.output_dir / filename}")

    def plot_deception_comparison(self):
        """Create deception rate comparison chart"""
        metrics_df = self.compute_metrics()

        if metrics_df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        conditions = metrics_df["condition"].tolist()
        rates = metrics_df["deception_rate"].tolist()

        x = np.arange(len(conditions))
        colors = ["#d62728" if r > 0.1 else "#2ca02c" for r in rates]

        bars = ax.bar(x, rates, color=colors, edgecolor="black", linewidth=1)

        # Add value labels
        for bar, rate in zip(bars, rates):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{rate:.1%}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        ax.set_xlabel("Condition")
        ax.set_ylabel("Deception Rate")
        ax.set_title(
            f'Deception Rate Comparison - {self.metadata.get("description", "Ablation Study")}'
        )
        ax.set_xticks(x)
        ax.set_xticklabels(conditions, rotation=45, ha="right")
        ax.set_ylim(0, max(rates) * 1.2 if rates else 1)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "deception_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        print(f"Saved: {self.output_dir / 'deception_comparison.png'}")

    def plot_round_evolution(self, metric: str, title: str, ylabel: str, filename: str):
        """Plot metric evolution over rounds for all conditions"""
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = sns.color_palette("husl", len(self.data))

        for idx, (condition, df) in enumerate(self.data.items()):
            if df.empty:
                continue

            # Average across runs for each round
            round_avg = df.groupby("round_number")[metric].mean()
            round_std = df.groupby("round_number")[metric].std()

            rounds = round_avg.index.values
            values = round_avg.values
            errors = round_std.values

            ax.plot(rounds, values, marker="o", label=condition, color=colors[idx])
            ax.fill_between(
                rounds, values - errors, values + errors, alpha=0.2, color=colors[idx]
            )

        ax.set_xlabel("Round")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Saved: {self.output_dir / filename}")

    def generate_summary_table(self) -> pd.DataFrame:
        """Generate summary statistics table"""
        metrics_df = self.compute_metrics()

        if metrics_df.empty:
            return pd.DataFrame()

        # Format for display
        summary = metrics_df.copy()
        summary["Seller Profit"] = summary.apply(
            lambda r: f"{r['avg_seller_profit']:.1f} ± {r['std_seller_profit']:.1f}",
            axis=1,
        )
        summary["Buyer Utility"] = summary.apply(
            lambda r: f"{r['avg_buyer_utility']:.1f} ± {r['std_buyer_utility']:.1f}",
            axis=1,
        )
        summary["Transactions"] = summary.apply(
            lambda r: f"{r['avg_transactions']:.1f} ± {r['std_transactions']:.1f}",
            axis=1,
        )
        summary["Deception Rate"] = summary["deception_rate"].apply(
            lambda x: f"{x:.1%}"
        )

        result = summary[
            [
                "condition",
                "Seller Profit",
                "Buyer Utility",
                "Transactions",
                "Deception Rate",
            ]
        ]
        result.columns = [
            "Condition",
            "Seller Profit",
            "Buyer Utility",
            "Transactions",
            "Deception Rate",
        ]

        # Save as CSV and LaTeX
        result.to_csv(self.output_dir / "summary_table.csv", index=False)

        # LaTeX format
        latex = result.to_latex(index=False, escape=False)
        with open(self.output_dir / "summary_table.tex", "w") as f:
            f.write(latex)

        print(f"Saved: {self.output_dir / 'summary_table.csv'}")
        print(f"Saved: {self.output_dir / 'summary_table.tex'}")

        return result

    def generate_all_visualizations(self):
        """Generate all visualizations"""
        print(f"\n{'='*60}")
        print(f"Generating Ablation Study Visualizations")
        print(f"Study: {self.metadata.get('description', 'Unknown')}")
        print(f"Output: {self.output_dir}")
        print(f"{'='*60}\n")

        # Summary table
        summary = self.generate_summary_table()
        if not summary.empty:
            print("\n" + "=" * 60)
            print("SUMMARY TABLE")
            print("=" * 60)
            print(summary.to_string(index=False))

        # Bar charts
        self.plot_metric_comparison(
            "seller_profit",
            f"Seller Profit - {self.metadata.get('description', '')}",
            "Average Total Seller Profit ($)",
            "seller_profit_comparison.png",
        )

        self.plot_metric_comparison(
            "buyer_utility",
            f"Buyer Utility - {self.metadata.get('description', '')}",
            "Average Total Buyer Utility",
            "buyer_utility_comparison.png",
        )

        self.plot_metric_comparison(
            "transactions",
            f"Transaction Volume - {self.metadata.get('description', '')}",
            "Average Number of Transactions",
            "transactions_comparison.png",
        )

        # Deception comparison
        self.plot_deception_comparison()

        # Round evolution plots
        self.plot_round_evolution(
            "total_seller_profit",
            f"Seller Profit Over Rounds - {self.metadata.get('description', '')}",
            "Seller Profit per Round",
            "seller_profit_evolution.png",
        )

        self.plot_round_evolution(
            "transactions",
            f"Transactions Over Rounds - {self.metadata.get('description', '')}",
            "Transactions per Round",
            "transactions_evolution.png",
        )

        print(f"\n{'='*60}")
        print(f"All visualizations saved to: {self.output_dir}")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Visualize Ablation Study Results")
    parser.add_argument(
        "ablation_base",
        type=str,
        help="Ablation experiment base path (e.g., ablation/temperature_20260123)",
    )

    args = parser.parse_args()

    visualizer = AblationVisualizer(args.ablation_base)
    visualizer.generate_all_visualizations()


if __name__ == "__main__":
    main()
