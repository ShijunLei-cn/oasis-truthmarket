"""
Multi-run analysis module
Analyzes aggregated results from multiple simulation runs
"""

import os
import json
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from .data_loader import ExperimentDataLoader
from .statistics import StatisticsCalculator
from .utils import setup_plot_style, plot_save, get_title_suffix
import re


class MultiRunAnalyzer:
    """Analyzer for multi-run experiments"""
    
    def __init__(self, experiment_id: str):
        """
        Initialize multi-run analyzer
        
        Args:
            experiment_id: Experiment ID
        """
        self.data_loader = ExperimentDataLoader(experiment_id)
        self.experiment_id = experiment_id
        self.paths = self.data_loader.paths
        self.run_data = {}
        self.aggregated_data = {}
        self.title_suffix = self.data_loader.get_title_suffix()
    
    def load_data(self) -> None:
        """Load all run data from experiment"""
        self.run_data = self.data_loader.load_experiment_data()
    
    def generate_aggregated_statistics(self) -> Dict[str, Any]:
        """
        Generate aggregated statistics across all runs
        
        Returns:
            Dictionary containing aggregated statistics
        """
        if not self.run_data:
            stats = {
                'experiment_id': self.experiment_id,
                'total_runs': 0,
                'summary_stats': {},
                'round_stats': {},
                'seller_profit_by_run': {},
                'buyer_utility_by_run': {}
            }
            self.aggregated_data = stats
            return stats
        
        # Use StatisticsCalculator for calculation
        calculator = StatisticsCalculator(self.run_data)
        stats = calculator.calculate_cross_run_statistics()
        
        # Add experiment metadata
        stats['experiment_id'] = self.experiment_id
        stats['total_runs'] = len(self.run_data)
        
        self.aggregated_data = stats
        return stats
    
    def save_aggregated_results(self) -> None:
        """Save aggregated results to JSON file"""
        if not self.aggregated_data:
            return
        
        results_file = os.path.join(
            self.paths['aggregated_analysis_dir'], 
            'aggregated_statistics.json'
        )
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.aggregated_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Aggregated statistics saved to: {results_file}")
    
    def _parse_config_from_run_key(self, run_key: str) -> tuple:
        """
        Parse configuration from run_key (filename)
        
        Args:
            run_key: Run key (e.g., 'run_1_reputation_only_both')
            
        Returns:
            Tuple of (market_type, communication_type) or (None, None) if cannot parse
        """
        # Pattern: run_<number>_<market_type>_<communication_type>
        # Examples: run_1_reputation_only_both, run_2_reputation_and_warrant_none
        match = re.match(r'run_\d+_(reputation_only|reputation_and_warrant)_(none|seller|buyer|both)', run_key)
        if match:
            market_type = match.group(1)
            comm_type = match.group(2)
            return (market_type, comm_type)
        return (None, None)
    
    def _format_config_label(self, market_type: str, comm_type: str) -> str:
        """Format configuration label for display"""
        # Format market type
        if market_type == 'reputation_only':
            market_label = 'Rep-Only'
        elif market_type == 'reputation_and_warrant':
            market_label = 'Rep+Warrant'
        else:
            market_label = market_type.replace('_', ' ').title()
        
        # Format communication type
        if comm_type == 'none':
            return market_label
        else:
            return f"{market_label} | {comm_type.title()} Comm."
    
    def _prepare_cross_run_data(self) -> Dict[str, List]:
        """
        Prepare cross-run comparison data
        
        Returns:
            Dictionary containing prepared data for visualization
        """
        calculator = StatisticsCalculator(self.run_data)
        return calculator.prepare_cross_run_comparison_data()
    
    def _prepare_config_grouped_data(self) -> Dict[str, Any]:
        """
        Prepare data grouped by configuration (8 configs)
        
        Returns:
            Dictionary containing grouped data by configuration
        """
        if not self.run_data:
            return {}
        
        # Group runs by configuration
        config_groups = {}
        for run_key, data in self.run_data.items():
            market_type, comm_type = self._parse_config_from_run_key(run_key)
            if market_type is None or comm_type is None:
                continue
            
            config_key = f"{market_type}_{comm_type}"
            if config_key not in config_groups:
                config_groups[config_key] = {
                    'market_type': market_type,
                    'comm_type': comm_type,
                    'run_keys': [],
                    'seller_profits': [],
                    'honest_profits': [],
                    'dishonest_profits': [],
                    'buyer_utilities': [],
                    'transaction_counts': [],
                    'honest_transaction_counts': [],
                    'dishonest_transaction_counts': []
                }
            
            transactions = data.get('transactions', pd.DataFrame())
            products = data.get('product', pd.DataFrame())
            
            if transactions.empty:
                continue
            
            config_groups[config_key]['run_keys'].append(run_key)
            
            # Calculate profits and utilities (same logic as StatisticsCalculator)
            if not products.empty and 'product_id' in transactions.columns:
                merged = transactions.merge(
                    products[['product_id', 'advertised_quality', 'true_quality']],
                    on='product_id',
                    how='left'
                )
                
                dishonest_mask = (
                    (merged['advertised_quality'] == 'HQ') & 
                    (merged['true_quality'] == 'LQ')
                )
                
                if 'seller_profit' in merged.columns:
                    dishonest_profit = merged[dishonest_mask]['seller_profit'].fillna(0).sum()
                    honest_profit = merged[~dishonest_mask]['seller_profit'].fillna(0).sum()
                else:
                    dishonest_profit = 0
                    honest_profit = 0
                
                if 'buyer_utility' in merged.columns:
                    dishonest_buyer_utility = merged[dishonest_mask]['buyer_utility'].fillna(0).sum()
                    honest_buyer_utility = merged[~dishonest_mask]['buyer_utility'].fillna(0).sum()
                else:
                    dishonest_buyer_utility = 0
                    honest_buyer_utility = 0
                
                dishonest_transaction_count = len(merged[dishonest_mask])
                honest_transaction_count = len(merged[~dishonest_mask])
            else:
                if 'seller_profit' in transactions.columns:
                    honest_profit = transactions['seller_profit'].fillna(0).sum()
                    dishonest_profit = 0
                else:
                    honest_profit = 0
                    dishonest_profit = 0
                
                if 'buyer_utility' in transactions.columns:
                    honest_buyer_utility = transactions['buyer_utility'].fillna(0).sum()
                    dishonest_buyer_utility = 0
                else:
                    honest_buyer_utility = 0
                    dishonest_buyer_utility = 0
                
                honest_transaction_count = len(transactions)
                dishonest_transaction_count = 0
                
            config_groups[config_key]['honest_profits'].append(float(honest_profit))
            config_groups[config_key]['dishonest_profits'].append(float(dishonest_profit))
            config_groups[config_key]['seller_profits'].append(float(honest_profit + dishonest_profit))
            config_groups[config_key]['buyer_utilities'].append(float(honest_buyer_utility + dishonest_buyer_utility))
            config_groups[config_key]['honest_transaction_counts'].append(int(honest_transaction_count))
            config_groups[config_key]['dishonest_transaction_counts'].append(int(dishonest_transaction_count))
            config_groups[config_key]['transaction_counts'].append(int(honest_transaction_count + dishonest_transaction_count))
        
        # Calculate statistics for each config
        config_stats = {}
        config_labels = []
        
        # Sort configs for consistent ordering
        sorted_configs = sorted(config_groups.keys(), key=lambda x: (
            x.startswith('reputation_only'),  # reputation_only first
            x.split('_')[-1]  # then by comm_type
        ))
        
        for config_key in sorted_configs:
            group = config_groups[config_key]
            label = self._format_config_label(group['market_type'], group['comm_type'])
            config_labels.append(label)
            
            config_stats[label] = {
                'mean_seller_profit': np.mean(group['seller_profits']) if group['seller_profits'] else 0,
                'std_seller_profit': np.std(group['seller_profits']) if group['seller_profits'] else 0,
                'mean_honest_profit': np.mean(group['honest_profits']) if group['honest_profits'] else 0,
                'std_honest_profit': np.std(group['honest_profits']) if group['honest_profits'] else 0,
                'mean_dishonest_profit': np.mean(group['dishonest_profits']) if group['dishonest_profits'] else 0,
                'std_dishonest_profit': np.std(group['dishonest_profits']) if group['dishonest_profits'] else 0,
                'mean_buyer_utility': np.mean(group['buyer_utilities']) if group['buyer_utilities'] else 0,
                'std_buyer_utility': np.std(group['buyer_utilities']) if group['buyer_utilities'] else 0,
                'mean_transaction_count': np.mean(group['transaction_counts']) if group['transaction_counts'] else 0,
                'std_transaction_count': np.std(group['transaction_counts']) if group['transaction_counts'] else 0,
                'mean_honest_transaction_count': np.mean(group['honest_transaction_counts']) if group['honest_transaction_counts'] else 0,
                'mean_dishonest_transaction_count': np.mean(group['dishonest_transaction_counts']) if group['dishonest_transaction_counts'] else 0,
            }
        
        return {
            'config_labels': config_labels,
            'config_stats': config_stats,
            'config_groups': config_groups
        }
    
    def plot_cross_run_comparison_by_config(self, out_dir: Optional[str] = None) -> None:
        """Plot cross-run comparison charts for each configuration (separate chart per config)"""
        if out_dir is None:
            out_dir = self.paths['aggregated_analysis_dir']
        os.makedirs(out_dir, exist_ok=True)
        
        # Get configuration-grouped data
        grouped_data = self._prepare_config_grouped_data()
        if not grouped_data or not grouped_data.get('config_groups'):
            print("Warning: Could not prepare configuration-grouped data")
            return
        
        setup_plot_style()
        config_groups = grouped_data['config_groups']
        config_labels = grouped_data['config_labels']
        
        # Create a separate chart for each configuration
        for config_key in sorted(config_groups.keys(), key=lambda x: (
            x.startswith('reputation_only'),
            x.split('_')[-1]
        )):
            group = config_groups[config_key]
            config_label = self._format_config_label(group['market_type'], group['comm_type'])
            
            if not group['run_keys']:
                continue
            
            # Prepare data for this configuration
            run_count = len(group['run_keys'])
            x_positions = range(run_count)
            x_labels = [f"Run {i+1}" for i in range(run_count)]
            
            honest_profits = group['honest_profits']
            dishonest_profits = group['dishonest_profits']
            seller_profits = group['seller_profits']
            buyer_utilities = group['buyer_utilities']
            transaction_counts = group['transaction_counts']
            honest_transaction_counts = group['honest_transaction_counts']
            dishonest_transaction_counts = group['dishonest_transaction_counts']
        
            # Create plots for this configuration
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle(f'Cross-Run Comparison Analysis - {config_label}', fontsize=14, fontweight='bold')
            
            # 1. Seller total profit comparison (stacked)
            axes[0, 0].bar(x_positions, honest_profits, alpha=0.7, color='green', label='Honest Profit')
            axes[0, 0].bar(x_positions, dishonest_profits, bottom=honest_profits, alpha=0.7, 
                          color='red', label='Dishonest Profit')
            axes[0, 0].set_xticks(x_positions)
            axes[0, 0].set_xticklabels(x_labels)
            honest_mean = np.mean(honest_profits)
            dishonest_mean = np.mean(dishonest_profits)
            total_mean = np.mean(seller_profits)
            axes[0, 0].axhline(y=honest_mean, color='darkgreen', linestyle='--', linewidth=1.5,
                              label=f'Honest Mean: {honest_mean:.2f}')
            axes[0, 0].axhline(y=dishonest_mean, color='darkred', linestyle='--', linewidth=1.5,
                              label=f'Dishonest Mean: {dishonest_mean:.2f}')
            axes[0, 0].axhline(y=total_mean, color='blue', linestyle='--', linewidth=1.5,
                              label=f'Total Mean: {total_mean:.2f}')
            axes[0, 0].set_title('Total Seller Profits (Honest vs Dishonest)')
            axes[0, 0].set_xlabel('Run')
            axes[0, 0].set_ylabel('Total Profit')
            axes[0, 0].legend(fontsize=8)
            axes[0, 0].grid(True, alpha=0.3)
            
            # 2. Buyer total utility comparison
            axes[0, 1].bar(x_positions, buyer_utilities, alpha=0.7, color='lightgreen')
            axes[0, 1].set_xticks(x_positions)
            axes[0, 1].set_xticklabels(x_labels)
            axes[0, 1].axhline(y=np.mean(buyer_utilities), color='red', linestyle='--',
                              label=f'Mean: {np.mean(buyer_utilities):.2f}')
            axes[0, 1].set_title('Total Buyer Utilities')
            axes[0, 1].set_xlabel('Run')
            axes[0, 1].set_ylabel('Total Utility')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. Transaction count comparison (stacked)
            axes[1, 0].bar(x_positions, honest_transaction_counts, alpha=0.7, color='green', 
                          label='Honest Transactions')
            axes[1, 0].bar(x_positions, dishonest_transaction_counts, bottom=honest_transaction_counts, 
                          alpha=0.7, color='red', label='Dishonest Transactions')
            axes[1, 0].set_xticks(x_positions)
            axes[1, 0].set_xticklabels(x_labels)
            honest_mean_tx = np.mean(honest_transaction_counts)
            dishonest_mean_tx = np.mean(dishonest_transaction_counts)
            total_mean_tx = np.mean(transaction_counts)
            axes[1, 0].axhline(y=honest_mean_tx, color='darkgreen', linestyle='--', linewidth=1.5,
                              label=f'Honest Mean: {honest_mean_tx:.1f}')
            axes[1, 0].axhline(y=dishonest_mean_tx, color='darkred', linestyle='--', linewidth=1.5,
                              label=f'Dishonest Mean: {dishonest_mean_tx:.1f}')
            axes[1, 0].axhline(y=total_mean_tx, color='blue', linestyle='--', linewidth=1.5,
                              label=f'Total Mean: {total_mean_tx:.1f}')
            axes[1, 0].set_title('Transaction Counts (Honest vs Dishonest)')
            axes[1, 0].set_xlabel('Run')
            axes[1, 0].set_ylabel('Number of Transactions')
            axes[1, 0].legend(fontsize=8)
            axes[1, 0].grid(True, alpha=0.3)
            
            # 4. Profit vs Utility scatter plot
            axes[1, 1].scatter(seller_profits, buyer_utilities, alpha=0.7, s=60)
            axes[1, 1].set_title('Seller Profits vs Buyer Utilities')
            axes[1, 1].set_xlabel('Total Seller Profit')
            axes[1, 1].set_ylabel('Total Buyer Utility')
            axes[1, 1].grid(True, alpha=0.3)
            
            for i in range(run_count):
                label = f"R{i+1}"
                axes[1, 1].annotate(label, (seller_profits[i], buyer_utilities[i]), 
                                   xytext=(5, 5), textcoords='offset points', fontsize=8)
            
            # Save with configuration-specific filename
            safe_config_name = config_key.replace('_', '-')
            plot_save(fig, out_dir, f'cross_run_comparison_{safe_config_name}')
    
    def plot_cross_run_comparison(self, out_dir: Optional[str] = None) -> None:
        """Plot cross-run comparison charts grouped by configuration (8 configs) - aggregated view"""
        if out_dir is None:
            out_dir = self.paths['aggregated_analysis_dir']
        os.makedirs(out_dir, exist_ok=True)
        
        # Get configuration-grouped data
        grouped_data = self._prepare_config_grouped_data()
        if not grouped_data or not grouped_data.get('config_labels'):
            print("Warning: Could not prepare configuration-grouped data, falling back to all-runs view")
            # Fallback to old method
            data = self._prepare_cross_run_data()
            if not data:
                return
            # ... (old plotting code as fallback)
            return
        
        setup_plot_style()
        
        config_labels = grouped_data['config_labels']
        config_stats = grouped_data['config_stats']
        x_positions = range(len(config_labels))
        
        # Extract data for plotting
        mean_seller_profits = [config_stats[label]['mean_seller_profit'] for label in config_labels]
        std_seller_profits = [config_stats[label]['std_seller_profit'] for label in config_labels]
        mean_honest_profits = [config_stats[label]['mean_honest_profit'] for label in config_labels]
        mean_dishonest_profits = [config_stats[label]['mean_dishonest_profit'] for label in config_labels]
        mean_buyer_utilities = [config_stats[label]['mean_buyer_utility'] for label in config_labels]
        std_buyer_utilities = [config_stats[label]['std_buyer_utility'] for label in config_labels]
        mean_transaction_counts = [config_stats[label]['mean_transaction_count'] for label in config_labels]
        mean_honest_transaction_counts = [config_stats[label]['mean_honest_transaction_count'] for label in config_labels]
        mean_dishonest_transaction_counts = [config_stats[label]['mean_dishonest_transaction_count'] for label in config_labels]
        
        # Create plots
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        title_suffix = self.title_suffix if self.title_suffix else self.experiment_id
        fig.suptitle(f'Cross-Configuration Comparison Analysis ({title_suffix})', fontsize=14)
        
        # 1. Seller total profit comparison (stacked bar with error bars)
        axes[0, 0].bar(x_positions, mean_honest_profits, alpha=0.7, color='green', label='Honest Profit')
        axes[0, 0].bar(x_positions, mean_dishonest_profits, bottom=mean_honest_profits, alpha=0.7, 
                      color='red', label='Dishonest Profit')
        # Add error bars for total profit
        axes[0, 0].errorbar(x_positions, mean_seller_profits, yerr=std_seller_profits,
                           fmt='none', color='black', capsize=3, linewidth=1.5)
        axes[0, 0].set_xticks(x_positions)
        axes[0, 0].set_xticklabels(config_labels, rotation=45, ha='right', fontsize=9)
        axes[0, 0].set_title('Average Seller Profits by Configuration (Honest vs Dishonest)')
        axes[0, 0].set_xlabel('Configuration')
        axes[0, 0].set_ylabel('Average Profit (mean ± std)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # 2. Buyer total utility comparison
        axes[0, 1].bar(x_positions, mean_buyer_utilities, alpha=0.7, color='lightgreen', 
                      yerr=std_buyer_utilities, capsize=5, error_kw={'linewidth': 1.5})
        axes[0, 1].set_xticks(x_positions)
        axes[0, 1].set_xticklabels(config_labels, rotation=45, ha='right', fontsize=9)
        axes[0, 1].set_title('Average Buyer Utilities by Configuration')
        axes[0, 1].set_xlabel('Configuration')
        axes[0, 1].set_ylabel('Average Utility (mean ± std)')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # 3. Transaction count comparison (stacked)
        axes[1, 0].bar(x_positions, mean_honest_transaction_counts, alpha=0.7, color='green', 
                      label='Honest Transactions')
        axes[1, 0].bar(x_positions, mean_dishonest_transaction_counts, 
                      bottom=mean_honest_transaction_counts, alpha=0.7, color='red', 
                      label='Dishonest Transactions')
        axes[1, 0].set_xticks(x_positions)
        axes[1, 0].set_xticklabels(config_labels, rotation=45, ha='right', fontsize=9)
        axes[1, 0].set_title('Average Transaction Counts by Configuration (Honest vs Dishonest)')
        axes[1, 0].set_xlabel('Configuration')
        axes[1, 0].set_ylabel('Average Number of Transactions')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # 4. Profit vs Utility scatter plot (with error bars)
        axes[1, 1].errorbar(mean_seller_profits, mean_buyer_utilities, 
                           xerr=std_seller_profits, yerr=std_buyer_utilities,
                           fmt='o', alpha=0.7, markersize=8, capsize=3, linewidth=1.5)
        axes[1, 1].set_title('Average Seller Profits vs Buyer Utilities by Configuration')
        axes[1, 1].set_xlabel('Average Seller Profit (mean ± std)')
        axes[1, 1].set_ylabel('Average Buyer Utility (mean ± std)')
        axes[1, 1].grid(True, alpha=0.3)
        
        # Add configuration labels
        for i, label in enumerate(config_labels):
            # Shorten label for annotation
            short_label = label.replace('Rep-Only', 'RO').replace('Rep+Warrant', 'RW').replace(' Comm.', '')
            axes[1, 1].annotate(short_label, 
                               (mean_seller_profits[i], mean_buyer_utilities[i]),
                               xytext=(5, 5), textcoords='offset points', fontsize=7)
        
        plt.tight_layout()
        plot_save(fig, out_dir, 'cross_run_comparison')
    
    def plot_round_progression(self, out_dir: Optional[str] = None) -> None:
        """Plot round progression charts comparing all 8 configurations"""
        if out_dir is None:
            out_dir = self.paths['aggregated_analysis_dir']
        os.makedirs(out_dir, exist_ok=True)
        
        # Get configuration-grouped data
        grouped_data = self._prepare_config_grouped_data()
        if not grouped_data or not grouped_data.get('config_groups'):
            print("Warning: Could not prepare configuration-grouped data for round progression")
            return
        
        setup_plot_style()
        config_groups = grouped_data['config_groups']
        
        # Import SimulationConfig for round count
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, base_dir)
        from config import SimulationConfig
        
        # Collect round-by-round data for each configuration
        config_round_data = {}
        
        for config_key, group in config_groups.items():
            market_type = group['market_type']
            comm_type = group['comm_type']
            config_label = self._format_config_label(market_type, comm_type)
            
            # Collect round-by-round data for all runs in this config
            round_seller_profits = {}  # round_num -> list of profits
            round_buyer_utilities = {}  # round_num -> list of utilities
            round_transaction_counts = {}  # round_num -> list of counts
            
            for run_key in group['run_keys']:
                data = self.run_data[run_key]
                transactions = data.get('transactions', pd.DataFrame())
                
                if transactions.empty or 'round_number' not in transactions.columns:
                    continue
                
                for round_num in range(1, SimulationConfig.SIMULATION_ROUNDS + 1):
                    round_trans = transactions[transactions['round_number'] == round_num]
                    if round_trans.empty:
                        continue
                    
                    if round_num not in round_seller_profits:
                        round_seller_profits[round_num] = []
                        round_buyer_utilities[round_num] = []
                        round_transaction_counts[round_num] = []
                    
                    if 'seller_profit' in round_trans.columns:
                        round_seller_profits[round_num].append(round_trans['seller_profit'].sum())
                    if 'buyer_utility' in round_trans.columns:
                        round_buyer_utilities[round_num].append(round_trans['buyer_utility'].sum())
                    round_transaction_counts[round_num].append(len(round_trans))
            
            # Calculate mean and std for each round
            rounds = sorted(round_seller_profits.keys())
            config_round_data[config_label] = {
                'rounds': rounds,
                'avg_seller_profits': [np.mean(round_seller_profits[r]) for r in rounds],
                'std_seller_profits': [np.std(round_seller_profits[r]) for r in rounds],
                'avg_buyer_utilities': [np.mean(round_buyer_utilities[r]) for r in rounds],
                'std_buyer_utilities': [np.std(round_buyer_utilities[r]) for r in rounds],
                'avg_transaction_counts': [np.mean(round_transaction_counts[r]) for r in rounds],
                'std_transaction_counts': [np.std(round_transaction_counts[r]) for r in rounds]
            }
        
        # Create plots comparing all configurations
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        title_suffix = self.title_suffix if self.title_suffix else self.experiment_id
        fig.suptitle(f'Round Progression Analysis by Configuration ({title_suffix})', fontsize=14, fontweight='bold')
        
        # Color palette for 8 configurations
        colors = sns.color_palette("tab10", n_colors=8)
        linestyles = ['-', '--', '-.', ':', '-', '--', '-.', ':']
        markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'X']
        
        # Sort config labels for consistent ordering
        sorted_config_labels = sorted(config_round_data.keys(), key=lambda x: (
            x.startswith('Rep-Only'),  # Rep-Only first
            x.split('|')[0].strip()  # then by comm type
        ))
        
        # 1. Seller profit progression
        for i, config_label in enumerate(sorted_config_labels):
            data = config_round_data[config_label]
            # Combine marker and linestyle in fmt string (marker + linestyle)
            fmt_str = f'{markers[i]}{linestyles[i]}'
            axes[0].errorbar(data['rounds'], data['avg_seller_profits'], 
                           yerr=data['std_seller_profits'],
                           fmt=fmt_str,
                           color=colors[i], label=config_label,
                           capsize=3, linewidth=2, markersize=6, alpha=0.8)
        axes[0].set_title('Seller Profit Progression by Configuration', fontweight='bold')
        axes[0].set_xlabel('Round')
        axes[0].set_ylabel('Average Profit (mean ± std)')
        axes[0].legend(loc='best', fontsize=8, ncol=2)
        axes[0].grid(True, alpha=0.3)
        
        # 2. Buyer utility progression
        for i, config_label in enumerate(sorted_config_labels):
            data = config_round_data[config_label]
            # Combine marker and linestyle in fmt string
            fmt_str = f'{markers[i]}{linestyles[i]}'
            axes[1].errorbar(data['rounds'], data['avg_buyer_utilities'],
                           yerr=data['std_buyer_utilities'],
                           fmt=fmt_str,
                           color=colors[i], label=config_label,
                           capsize=3, linewidth=2, markersize=6, alpha=0.8)
        axes[1].set_title('Buyer Utility Progression by Configuration', fontweight='bold')
        axes[1].set_xlabel('Round')
        axes[1].set_ylabel('Average Utility (mean ± std)')
        axes[1].legend(loc='best', fontsize=8, ncol=2)
        axes[1].grid(True, alpha=0.3)
        
        # 3. Transaction count progression
        for i, config_label in enumerate(sorted_config_labels):
            data = config_round_data[config_label]
            # Combine marker and linestyle in fmt string
            fmt_str = f'{markers[i]}{linestyles[i]}'
            axes[2].errorbar(data['rounds'], data['avg_transaction_counts'],
                           yerr=data['std_transaction_counts'],
                           fmt=fmt_str,
                           color=colors[i], label=config_label,
                           capsize=3, linewidth=2, markersize=6, alpha=0.8)
        axes[2].set_title('Transaction Count Progression by Configuration', fontweight='bold')
        axes[2].set_xlabel('Round')
        axes[2].set_ylabel('Average Transaction Count (mean ± std)')
        axes[2].legend(loc='best', fontsize=8, ncol=2)
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_save(fig, out_dir, 'round_progression')
    
    def generate_individual_run_analysis(self) -> None:
        """Generate individual analysis for each run"""
        from .single_run_analysis import SingleRunAnalyzer
        
        individual_dir = self.paths['individual_analysis_dir']
        
        for run_key, data in self.run_data.items():
            run_output_dir = os.path.join(individual_dir, run_key)
            os.makedirs(run_output_dir, exist_ok=True)
            
            try:
                # Build db_path directly from run_key (which is already the filename without .db)
                db_path = os.path.join(self.paths['experiment_dir'], f'{run_key}.db')
                
                if not os.path.exists(db_path):
                    print(f"Warning: Database file not found: {db_path}, skipping individual analysis")
                    continue
                
                analyzer = SingleRunAnalyzer(db_path, run_output_dir)
                analyzer.analyze()
                print(f"Run {run_key} analysis complete")
            except Exception as e:
                print(f"Error during analysis of Run {run_key}: {e}")
    
    def analyze(self) -> None:
        """Run complete multi-run analysis"""
        print(f"Start analyzing experiment: {self.experiment_id}")
        
        # Load data
        self.load_data()
        
        if not self.run_data:
            print("No data found for analysis")
            return
        
        # Generate aggregated statistics
        print("Generating aggregated statistics...")
        self.generate_aggregated_statistics()
        
        # Save results
        self.save_aggregated_results()
        
        # Generate aggregated visualizations
        aggregated_dir = self.paths['aggregated_analysis_dir']
        print(f"Generating aggregate visualizations to: {aggregated_dir}")
        
        # Generate cross-run comparison for each configuration (separate charts)
        print("Generating per-configuration cross-run comparison charts...")
        self.plot_cross_run_comparison_by_config(aggregated_dir)
        
        # Generate aggregated view across all configurations
        print("Generating aggregated cross-configuration comparison chart...")
        self.plot_cross_run_comparison(aggregated_dir)
        
        # Generate round progression comparison across all configurations
        print("Generating round progression comparison chart...")
        self.plot_round_progression(aggregated_dir)
        
        # Generate individual run analysis
        print("Generating individual run analysis...")
        self.generate_individual_run_analysis()
        
        print(f"Experiment analysis complete! Results saved in: {self.paths['analysis_dir']}")


# Test cases
if __name__ == "__main__":
    print("Multi-run analysis module")
    print("This module requires actual experiment data to test.")
    print("Usage:")
    print("  from visualization.core.multi_run_analysis import MultiRunAnalyzer")
    print("  analyzer = MultiRunAnalyzer('experiment_id')")
    print("  analyzer.analyze()")
