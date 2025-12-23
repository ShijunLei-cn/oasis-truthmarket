"""
Comparison analysis module
Compares results from different experiments (e.g., different market mechanisms)
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mticker

from .data_loader import ExperimentDataLoader
from .statistics import StatisticsCalculator
from .utils import setup_plot_style, plot_save


class ComparisonAnalyzer:
    """Analyzer for comparing different experiments"""
    
    def __init__(self, experiment_configs: Dict[str, str], output_dir: Optional[str] = None):
        """
        Initialize comparison analyzer
        
        Args:
            experiment_configs: Dictionary mapping experiment names to experiment IDs
                               e.g., {'reputation_only': 'exp_123', 'reputation_warrant': 'exp_456'}
            output_dir: Output directory for comparison charts (default: auto-generated)
        """
        self.experiment_configs = experiment_configs
        self.experiment_data = {}
        self.experiment_configs_dict = {}
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path(f"analysis/comparison_{timestamp}")
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_experiment_data(self):
        """Load data from all experiments"""
        for exp_name, exp_id in self.experiment_configs.items():
            print(f"Loading experiment: {exp_name} ({exp_id})")
            loader = ExperimentDataLoader(exp_id)
            run_data = loader.load_experiment_data()
            config = loader.config
            
            self.experiment_data[exp_name] = {
                'run_data': run_data,
                'config': config,
                'loader': loader
            }
            self.experiment_configs_dict[exp_name] = config
    
    def format_experiment_label(self, config: Dict[str, Any]) -> str:
        """Format experiment label from configuration"""
        parts = []
        market_type = config.get('MARKET_TYPE', 'unknown')
        comm_type = config.get('COMMUNICATION_TYPE', 'none')
        
        if market_type == 'reputation_only':
            parts.append('Rep-Only')
        elif market_type == 'reputation_and_warrant':
            parts.append('Rep+Warrant')
        else:
            parts.append(market_type.replace('_', ' ').title())
        
        if comm_type and comm_type != 'none':
            parts.append(f'{comm_type.title()}Comm')
        
        return ' | '.join(parts) if parts else 'Unknown'
    
    def load_aggregated_statistics(self, exp_name: str) -> Dict[str, Any]:
        """
        Load aggregated statistics for an experiment
        
        Args:
            exp_name: Experiment name
            
        Returns:
            Aggregated statistics dictionary
        """
        if exp_name not in self.experiment_data:
            return {}
        
        loader = self.experiment_data[exp_name]['loader']
        stats_file = os.path.join(loader.paths['aggregated_analysis_dir'], 'aggregated_statistics.json')
        
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Calculate statistics if file doesn't exist
            run_data = self.experiment_data[exp_name]['run_data']
            calculator = StatisticsCalculator(run_data)
            return calculator.calculate_cross_run_statistics()
    
    def plot_summary_comparison(self):
        """Create core metrics comparison chart"""
        if len(self.experiment_configs) < 2:
            print("Need at least 2 experiments to compare")
            return
        
        exp_names = list(self.experiment_configs.keys())
        exp_labels = [self.format_experiment_label(self.experiment_configs_dict[name]) 
                     for name in exp_names]
        
        # Load statistics
        stats_list = [self.load_aggregated_statistics(name) for name in exp_names]
        
        # Extract core metrics
        metrics = {
            'Average Buyer Utility\nper Run': [],
            'Average Seller Profit\nper Run': [],
            'Average Transactions\nper Run': []
        }
        
        stds = {
            'Average Buyer Utility\nper Run': [],
            'Average Seller Profit\nper Run': [],
            'Average Transactions\nper Run': []
        }
        
        for stats in stats_list:
            summary = stats.get('summary_stats', {})
            metrics['Average Buyer Utility\nper Run'].append(
                summary.get('avg_buyer_utility_per_run', 0)
            )
            metrics['Average Seller Profit\nper Run'].append(
                summary.get('avg_seller_profit_per_run', 0)
            )
            metrics['Average Transactions\nper Run'].append(
                summary.get('avg_transactions_per_run', 0)
            )
            
            stds['Average Buyer Utility\nper Run'].append(
                summary.get('std_buyer_utility_per_run', 0)
            )
            stds['Average Seller Profit\nper Run'].append(
                summary.get('std_seller_profit_per_run', 0)
            )
            stds['Average Transactions\nper Run'].append(
                summary.get('std_transactions_per_run', 0)
            )
        
        # Create chart
        fig, axes = plt.subplots(1, 3, figsize=(15, 6))
        fig.suptitle('Market Mechanism Comparison', fontsize=16, fontweight='bold')
        
        colors = sns.color_palette("Set2", len(exp_names))
        
        for i, (metric, values) in enumerate(metrics.items()):
            ax = axes[i]
            bars = ax.bar(exp_labels, values, color=colors, alpha=0.8, 
                         yerr=stds[metric], capsize=10, error_kw={'linewidth': 2})
            
            ax.set_title(metric, fontsize=12, fontweight='bold')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
            
            # Add value labels
            for j, (bar, val, std) in enumerate(zip(bars, values, stds[metric])):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + std + 0.5,
                       f'{val:.2f}±{std:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plot_save(fig, str(self.output_dir), 'market_mechanism_comparison_summary')
    
    def plot_round_progression_comparison(self):
        """Create round-by-round progression comparison chart"""
        if len(self.experiment_configs) < 2:
            return
        
        exp_names = list(self.experiment_configs.keys())
        stats_list = [self.load_aggregated_statistics(name) for name in exp_names]
        
        # Extract round data
        all_rounds = set()
        for stats in stats_list:
            round_stats = stats.get('round_stats', {})
            all_rounds.update(round_stats.keys())
        
        common_rounds = sorted([int(r) for r in all_rounds])
        
        # Prepare data
        buyer_data = {}
        seller_data = {}
        
        for i, stats in enumerate(stats_list):
            round_stats = stats.get('round_stats', {})
            exp_label = self.format_experiment_label(self.experiment_configs_dict[exp_names[i]])
            
            buyer_values = [round_stats.get(str(r), {}).get('avg_buyer_utility', 0) 
                          for r in common_rounds]
            seller_values = [round_stats.get(str(r), {}).get('avg_seller_profit', 0) 
                           for r in common_rounds]
        
            buyer_data[exp_label] = buyer_values
            seller_data[exp_label] = seller_values
        
        # Create plot
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.suptitle('Consumer Utility and Producer Profit by Round for each Market Type', 
                     fontsize=16, fontweight='bold')
        
        ax.set_facecolor('#F0F8FF')
        
        # Plot lines for each experiment
        colors = ['#FF8C42', '#FFD93D', '#8B0000', '#DC143C']
        linestyles = ['-', '--', '-', '--']
        
        for i, (exp_label, buyer_values) in enumerate(buyer_data.items()):
            ax.plot(common_rounds, buyer_values, 'o-', 
                   label=f'Utility ({exp_label})', 
                   linewidth=2.5, markersize=7, color=colors[i % len(colors)],
                   linestyle=linestyles[i % len(linestyles)])
        
        for i, (exp_label, seller_values) in enumerate(seller_data.items()):
            ax.plot(common_rounds, seller_values, 'o-', 
                   label=f'Profit ({exp_label})', 
                   linewidth=2.5, markersize=7, color=colors[(i+2) % len(colors)],
                   linestyle=linestyles[(i+2) % len(linestyles)])
        
        ax.set_xticks(common_rounds)
        ax.set_xticklabels([f'Round {r}' for r in common_rounds])
        ax.set_ylim(0, 60)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10)
        
        plot_save(fig, str(self.output_dir), 'market_mechanism_round_progression')
    
    def plot_deception_comparison(self):
        """Create deception behavior comparison chart"""
        if len(self.experiment_configs) < 2:
            return
        
        exp_names = list(self.experiment_configs.keys())
        exp_labels = [self.format_experiment_label(self.experiment_configs_dict[name]) 
                     for name in exp_names]
        
        # Collect deception data for each experiment
        deception_data = {}
        for exp_name, exp_label in zip(exp_names, exp_labels):
            run_data = self.experiment_data[exp_name]['run_data']
            calculator = StatisticsCalculator(run_data)
            deception_stats = calculator.calculate_deception_statistics()
            
            deceptions_by_run = deception_stats.get('total_deceptions_by_run', {})
            deception_data[exp_label] = list(deceptions_by_run.values())
        
        # Calculate statistics
        means = [np.mean(data) if data else 0 for data in deception_data.values()]
        stds_list = [np.std(data) if data else 0 for data in deception_data.values()]
        
        # Create chart
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Deception Behavior Analysis: TQ=Low & AQ=High Instances', 
                     fontsize=16, fontweight='bold')
        
        colors = ['#ff9999', '#66b3ff']
        
        # Bar chart
        ax = axes[0]
        bars = ax.bar(exp_labels, means, color=colors[:len(exp_labels)], alpha=0.8, 
                     yerr=stds_list, capsize=10, error_kw={'linewidth': 2})
        ax.set_title('Average Deception Instances per Run', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count of TQ=Low & AQ=High Posts')
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar, val, std in zip(bars, means, stds_list):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + std + 0.5,
                   f'{val:.2f}±{std:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Box plot
        ax = axes[1]
        bp = ax.boxplot([deception_data[label] for label in exp_labels], 
                       tick_labels=exp_labels,
                       patch_artist=True,
                       widths=0.6)
        
        for patch, color in zip(bp['boxes'], colors[:len(exp_labels)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title('Distribution of Deception Instances', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count of TQ=Low & AQ=High Posts per Run')
        ax.grid(True, alpha=0.3, axis='y')
        
        plot_save(fig, str(self.output_dir), 'market_mechanism_deception_behavior')
    
    def save_config(self):
        """Save comparison configuration to JSON file"""
        config = {
            'generation_time': datetime.now().isoformat(),
            'experiment_configs': self.experiment_configs,
            'experiment_labels': {
                name: self.format_experiment_label(config_dict)
                for name, config_dict in self.experiment_configs_dict.items()
            },
            'charts_generated': [
                'market_mechanism_comparison_summary.png',
                'market_mechanism_round_progression.png',
                'market_mechanism_deception_behavior.png'
            ]
        }
        
        config_file = self.output_dir / 'config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def generate_all_comparisons(self):
        """Generate all comparison charts"""
        print("Generating comparison charts...")
        setup_plot_style()
        
        self.load_experiment_data()
        self.plot_summary_comparison()
        self.plot_round_progression_comparison()
        self.plot_deception_comparison()
        self.save_config()
        
        print(f"Comparison charts saved to: {self.output_dir}")


def compare_experiments(experiment_configs: Dict[str, str], output_dir: Optional[str] = None):
    """
    Convenience function to compare experiments
        
        Args:
        experiment_configs: Dictionary mapping experiment names to experiment IDs
        output_dir: Output directory (optional)
    """
    analyzer = ComparisonAnalyzer(experiment_configs, output_dir)
    analyzer.generate_all_comparisons()


# Test cases
if __name__ == "__main__":
    print("Comparison analysis module")
    print("This module requires actual experiment data to test.")
    print("Usage:")
    print("  from visualization.core.comparison_analysis import compare_experiments")
    print("  compare_experiments({")
    print("      'reputation_only': 'exp_123',")
    print("      'reputation_warrant': 'exp_456'")
    print("  })")