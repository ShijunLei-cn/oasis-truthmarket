#!/usr/bin/env python3
"""
RQ2 Market Mechanism Comparison Visualization
Academic-style visualizations for comparing Reputation-Only vs Reputation+Warrant markets

Generates 5 observation perspectives:
1. Price Evolution Over Rounds
2. Seller Profit Over Rounds
3. Buyer Utility Over Rounds
4. Seller Reputation Over Rounds
5. Total Market Metrics & Honest vs Dishonest Analysis (Combined)
"""

import json
import os
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from scipy import stats

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.patches import Rectangle

# Import market parameters
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import SimulationConfig

# Academic plotting style
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid", {'font.family': 'serif'})
sns.set_palette("husl")

# Color scheme: R=red tones, RW=blue tones
COLORS = {
    'reputation_only': '#d62728',  # Red
    'reputation_warrant': '#2ca02c',  # Green (for contrast)
    'honest': '#2ca02c',  # Green
    'dishonest': '#d62728',  # Red
    'hq': '#4C78A8',  # Blue
    'lq': '#F58518',  # Orange
}


class RQ2Visualizer:
    """RQ2 Market Mechanism Comparison Visualizer"""
    
    def __init__(self, r_experiment_id: str, rw_experiment_id: str, output_dir: Optional[str] = None):
        """
        Initialize visualizer
        
        Args:
            r_experiment_id: Reputation-Only experiment ID
            rw_experiment_id: Reputation+Warrant experiment ID
            output_dir: Output directory (default: visualization/figs/rq2_<timestamp>)
        """
        self.r_exp_id = r_experiment_id
        self.rw_exp_id = rw_experiment_id
        
        if output_dir is None:
            output_dir = f"visualization/figs/rq2_comparison"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create table output directory
        self.table_dir = Path("visualization/table")
        self.table_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self.r_data = self._load_experiment_data(r_experiment_id)
        self.rw_data = self._load_experiment_data(rw_experiment_id)
        self.r_config = self._load_experiment_config(r_experiment_id)
        self.rw_config = self._load_experiment_config(rw_experiment_id)
        
        # Get market parameters for default values
        self.market_params = SimulationConfig.MARKET_PARAMS
        
    def _load_experiment_data(self, exp_id: str) -> Dict:
        """Load aggregated statistics"""
        stats_file = f"analysis/{exp_id}/aggregated/aggregated_statistics.json"
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_experiment_config(self, exp_id: str) -> Dict:
        """Load experiment configuration"""
        config_file = f"experiments/{exp_id}/config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_round_data_from_db(self, exp_id: str) -> pd.DataFrame:
        """Load round-by-round data from database files"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load transactions
                transactions = pd.read_sql_query(
                    "SELECT round_number, seller_profit, buyer_utility FROM transactions",
                    conn
                )
                
                # Load products for price data
                products = pd.read_sql_query(
                    "SELECT round_number, advertised_quality, price, true_quality FROM product",
                    conn
                )
                
                # Load reputation history
                reputation = pd.read_sql_query(
                    "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                    conn
                )
                
                conn.close()
                
                # Get actual round numbers from data (dynamic, not hardcoded)
                all_round_numbers = set()
                if not transactions.empty:
                    all_round_numbers.update(transactions['round_number'].unique())
                if not products.empty:
                    all_round_numbers.update(products['round_number'].unique())
                if not reputation.empty:
                    all_round_numbers.update(reputation['round'].unique())
                
                # Aggregate by round
                for round_num in sorted(all_round_numbers):
                    if pd.isna(round_num):
                        continue
                    round_num = int(round_num)
                    round_trans = transactions[transactions['round_number'] == round_num]
                    round_prod = products[products['round_number'] == round_num]
                    round_rep = reputation[reputation['round'] == round_num]
                    
                    all_rounds_data.append({
                        'run_id': run_id,
                        'round': round_num,
                        'seller_profit': round_trans['seller_profit'].sum() if not round_trans.empty else 0,
                        'buyer_utility': round_trans['buyer_utility'].sum() if not round_trans.empty else 0,
                        'transactions': len(round_trans),
                        'avg_price_hq': round_prod[round_prod['advertised_quality'] == 'HQ']['price'].mean() if not round_prod[round_prod['advertised_quality'] == 'HQ'].empty else np.nan,
                        'avg_price_lq': round_prod[round_prod['advertised_quality'] == 'LQ']['price'].mean() if not round_prod[round_prod['advertised_quality'] == 'LQ'].empty else np.nan,
                        'avg_reputation': round_rep['public_reputation_score'].mean() if not round_rep.empty else np.nan,
                        'deceptions': len(round_prod[(round_prod['advertised_quality'] == 'HQ') & (round_prod['true_quality'] == 'LQ')]),
                    })
            except Exception as e:
                print(f"Warning: Could not load data from {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def plot_price_evolution(self):
        """1. Price Evolution Over Rounds"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Aggregate across runs
        r_agg = r_rounds.groupby('round').agg({
            'avg_price_hq': ['mean', 'std'],
            'avg_price_lq': ['mean', 'std']
        }).reset_index()
        
        rw_agg = rw_rounds.groupby('round').agg({
            'avg_price_hq': ['mean', 'std'],
            'avg_price_lq': ['mean', 'std']
        }).reset_index()
        
        rounds = sorted(r_agg['round'].unique())
        
        # Fill NaN values with market parameter defaults
        default_hq_price = self.market_params.get('hq_price', 5.0)
        default_lq_price = self.market_params.get('lq_price', 3.0)
        
        r_hq_mean = r_agg[('avg_price_hq', 'mean')].fillna(default_hq_price)
        r_hq_std = r_agg[('avg_price_hq', 'std')].fillna(0)
        r_lq_mean = r_agg[('avg_price_lq', 'mean')].fillna(default_lq_price)
        r_lq_std = r_agg[('avg_price_lq', 'std')].fillna(0)
        
        rw_hq_mean = rw_agg[('avg_price_hq', 'mean')].fillna(default_hq_price)
        rw_hq_std = rw_agg[('avg_price_hq', 'std')].fillna(0)
        rw_lq_mean = rw_agg[('avg_price_lq', 'mean')].fillna(default_lq_price)
        rw_lq_std = rw_agg[('avg_price_lq', 'std')].fillna(0)
        
        # Plot HQ prices
        ax.errorbar(rounds, r_hq_mean, 
                   yerr=r_hq_std,
                   fmt='o-', label='Reputation-Only (HQ)', 
                   color=COLORS['reputation_only'], linewidth=2, markersize=6, capsize=3)
        ax.errorbar(rounds, rw_hq_mean,
                   yerr=rw_hq_std,
                   fmt='s--', label='Reputation+Warrant (HQ)',
                   color=COLORS['reputation_warrant'], linewidth=2, markersize=6, capsize=3)
        
        # Plot LQ prices
        ax.errorbar(rounds, r_lq_mean,
                   yerr=r_lq_std,
                   fmt='o-', label='Reputation-Only (LQ)',
                   color=COLORS['reputation_only'], linewidth=1.5, markersize=5, 
                   capsize=2, alpha=0.6, linestyle=':')
        ax.errorbar(rounds, rw_lq_mean,
                   yerr=rw_lq_std,
                   fmt='s--', label='Reputation+Warrant (LQ)',
                   color=COLORS['reputation_warrant'], linewidth=1.5, markersize=5,
                   capsize=2, alpha=0.6, linestyle=':')
        
        ax.set_xlabel('Round', fontweight='bold')
        ax.set_ylabel('Average Price ($)', fontweight='bold')
        ax.set_title('Price Evolution Over Rounds', fontweight='bold', pad=15)
        ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xticks(rounds)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '1_price_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 1_price_evolution.png")
    
    def plot_seller_profit(self):
        """2. Seller Profit Over Rounds"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Left: Line plot
        r_agg = r_rounds.groupby('round')['seller_profit'].agg(['mean', 'std']).reset_index()
        rw_agg = rw_rounds.groupby('round')['seller_profit'].agg(['mean', 'std']).reset_index()
        
        rounds = sorted(r_agg['round'].unique())
        axes[0].errorbar(rounds, r_agg['mean'], yerr=r_agg['std'],
                       fmt='o-', label='Reputation-Only', color=COLORS['reputation_only'],
                       linewidth=2, markersize=7, capsize=4)
        axes[0].errorbar(rounds, rw_agg['mean'], yerr=rw_agg['std'],
                        fmt='s--', label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                        linewidth=2, markersize=7, capsize=4)
        axes[0].set_xlabel('Round', fontweight='bold')
        axes[0].set_ylabel('Average Seller Profit ($)', fontweight='bold')
        axes[0].set_title('Seller Profit Progression', fontweight='bold')
        axes[0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].set_xticks(rounds)
        
        # Right: KDE distribution comparison
        r_all_profits = r_rounds['seller_profit'].dropna().values
        rw_all_profits = rw_rounds['seller_profit'].dropna().values
        
        if len(r_all_profits) > 0 and len(rw_all_profits) > 0:
            # Create KDE plots
            r_kde = stats.gaussian_kde(r_all_profits)
            rw_kde = stats.gaussian_kde(rw_all_profits)
            
            x_min = min(r_all_profits.min(), rw_all_profits.min())
            x_max = max(r_all_profits.max(), rw_all_profits.max())
            x_range = np.linspace(x_min, x_max, 200)
            
            axes[1].plot(x_range, r_kde(x_range), label='Reputation-Only', 
                        color=COLORS['reputation_only'], linewidth=2)
            axes[1].fill_between(x_range, r_kde(x_range), alpha=0.3, 
                               color=COLORS['reputation_only'])
            axes[1].plot(x_range, rw_kde(x_range), label='Reputation+Warrant',
                        color=COLORS['reputation_warrant'], linewidth=2, linestyle='--')
            axes[1].fill_between(x_range, rw_kde(x_range), alpha=0.3,
                               color=COLORS['reputation_warrant'])
            
            # Add mean lines
            axes[1].axvline(np.mean(r_all_profits), color=COLORS['reputation_only'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
            axes[1].axvline(np.mean(rw_all_profits), color=COLORS['reputation_warrant'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
        
        axes[1].set_xlabel('Seller Profit ($)', fontweight='bold')
        axes[1].set_ylabel('Density', fontweight='bold')
        axes[1].set_title('Profit Distribution Comparison', fontweight='bold')
        axes[1].legend(frameon=True, fancybox=True, shadow=True)
        axes[1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '2_seller_profit.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 2_seller_profit.png")
    
    def plot_buyer_utility(self):
        """3. Buyer Utility Over Rounds"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Left: Line plot
        r_agg = r_rounds.groupby('round')['buyer_utility'].agg(['mean', 'std']).reset_index()
        rw_agg = rw_rounds.groupby('round')['buyer_utility'].agg(['mean', 'std']).reset_index()
        
        rounds = sorted(r_agg['round'].unique())
        axes[0].errorbar(rounds, r_agg['mean'], yerr=r_agg['std'],
                        fmt='o-', label='Reputation-Only', color=COLORS['reputation_only'],
                        linewidth=2, markersize=7, capsize=4)
        axes[0].errorbar(rounds, rw_agg['mean'], yerr=rw_agg['std'],
                        fmt='s--', label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                        linewidth=2, markersize=7, capsize=4)
        axes[0].set_xlabel('Round', fontweight='bold')
        axes[0].set_ylabel('Average Buyer Utility ($)', fontweight='bold')
        axes[0].set_title('Buyer Utility Progression', fontweight='bold')
        axes[0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].set_xticks(rounds)
        
        # Right: KDE distribution comparison
        r_all_utils = r_rounds['buyer_utility'].dropna().values
        rw_all_utils = rw_rounds['buyer_utility'].dropna().values
        
        if len(r_all_utils) > 0 and len(rw_all_utils) > 0:
            # Create KDE plots
            r_kde = stats.gaussian_kde(r_all_utils)
            rw_kde = stats.gaussian_kde(rw_all_utils)
            
            x_min = min(r_all_utils.min(), rw_all_utils.min())
            x_max = max(r_all_utils.max(), rw_all_utils.max())
            x_range = np.linspace(x_min, x_max, 200)
            
            axes[1].plot(x_range, r_kde(x_range), label='Reputation-Only',
                        color=COLORS['reputation_only'], linewidth=2)
            axes[1].fill_between(x_range, r_kde(x_range), alpha=0.3,
                               color=COLORS['reputation_only'])
            axes[1].plot(x_range, rw_kde(x_range), label='Reputation+Warrant',
                        color=COLORS['reputation_warrant'], linewidth=2, linestyle='--')
            axes[1].fill_between(x_range, rw_kde(x_range), alpha=0.3,
                               color=COLORS['reputation_warrant'])
            
            # Add mean lines
            axes[1].axvline(np.mean(r_all_utils), color=COLORS['reputation_only'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
            axes[1].axvline(np.mean(rw_all_utils), color=COLORS['reputation_warrant'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
        
        axes[1].set_xlabel('Buyer Utility ($)', fontweight='bold')
        axes[1].set_ylabel('Density', fontweight='bold')
        axes[1].set_title('Utility Distribution Comparison', fontweight='bold')
        axes[1].legend(frameon=True, fancybox=True, shadow=True)
        axes[1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '3_buyer_utility.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 3_buyer_utility.png")
    
    def plot_reputation(self):
        """4. Seller Reputation Over Rounds"""
        r_exp_dir = Path(f"experiments/{self.r_exp_id}")
        rw_exp_dir = Path(f"experiments/{self.rw_exp_id}")
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Load reputation data
        r_reps = []
        rw_reps = []
        
        for db_file in sorted(r_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                rep = pd.read_sql_query(
                    "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                    conn
                )
                r_reps.append(rep)
                conn.close()
            except:
                pass
        
        for db_file in sorted(rw_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                rep = pd.read_sql_query(
                    "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                    conn
                )
                rw_reps.append(rep)
                conn.close()
            except:
                pass
        
        if r_reps and rw_reps:
            r_all = pd.concat(r_reps)
            rw_all = pd.concat(rw_reps)
            
            # Left: Average reputation progression
            r_agg = r_all.groupby('round')['public_reputation_score'].agg(['mean', 'std']).reset_index()
            rw_agg = rw_all.groupby('round')['public_reputation_score'].agg(['mean', 'std']).reset_index()
            
            rounds = sorted(r_agg['round'].unique())
            axes[0].errorbar(rounds, r_agg['mean'], yerr=r_agg['std'],
                           fmt='o-', label='Reputation-Only', color=COLORS['reputation_only'],
                           linewidth=2, markersize=7, capsize=4)
            axes[0].errorbar(rounds, rw_agg['mean'], yerr=rw_agg['std'],
                            fmt='s--', label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                            linewidth=2, markersize=7, capsize=4)
            axes[0].set_xlabel('Round', fontweight='bold')
            axes[0].set_ylabel('Average Reputation Score', fontweight='bold')
            axes[0].set_title('Average Reputation Progression', fontweight='bold')
            axes[0].legend(frameon=True, fancybox=True, shadow=True)
            axes[0].grid(True, alpha=0.3, linestyle='--')
            axes[0].set_xticks(rounds)
            
            # Right: Heatmap (sample one run)
            if len(r_reps) > 0:
                sample_rep = r_reps[0].pivot_table(
                    index='seller_id', columns='round', values='public_reputation_score', aggfunc='mean'
                )
                im = axes[1].imshow(sample_rep.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=5)
                axes[1].set_xlabel('Round', fontweight='bold')
                axes[1].set_ylabel('Seller ID', fontweight='bold')
                axes[1].set_title('Reputation Heatmap (Sample Run)', fontweight='bold')
                axes[1].set_xticks(range(len(sample_rep.columns)))
                axes[1].set_xticklabels(sample_rep.columns)
                axes[1].set_yticks(range(len(sample_rep.index)))
                axes[1].set_yticklabels(sample_rep.index)
                plt.colorbar(im, ax=axes[1], label='Reputation Score')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '4_reputation.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 4_reputation.png")
    
    def _prepare_cross_run_data(self, exp_id: str, exp_dir: Path) -> Dict:
        """Prepare cross-run comparison data for one experiment"""
        run_ids = []
        seller_profits = []
        honest_profits = []
        dishonest_profits = []
        buyer_utilities = []
        transaction_counts = []
        honest_transaction_counts = []
        dishonest_transaction_counts = []
        deceptions = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            try:
                run_id = int(db_file.stem.split('_')[1])
                conn = sqlite3.connect(db_file)
                
                # Load transactions and products
                transactions = pd.read_sql_query(
                    "SELECT t.seller_profit, t.buyer_utility, p.advertised_quality, p.true_quality "
                    "FROM transactions t JOIN product p ON t.product_id = p.product_id",
                    conn
                )
                
                products = pd.read_sql_query(
                    "SELECT advertised_quality, true_quality FROM product",
                    conn
                )
                
                conn.close()
                
                if not transactions.empty:
                    run_ids.append(run_id)
                    
                    # Ensure quality values are strings and strip whitespace
                    transactions['advertised_quality'] = transactions['advertised_quality'].astype(str).str.strip()
                    transactions['true_quality'] = transactions['true_quality'].astype(str).str.strip()
                    
                    # Identify dishonest transactions: advertised HQ but delivered LQ
                    dishonest_mask = (
                        (transactions['advertised_quality'] == 'HQ') & 
                        (transactions['true_quality'] == 'LQ')
                    )
                    
                    # Calculate profits
                    dishonest_profit = transactions[dishonest_mask]['seller_profit'].fillna(0).sum()
                    honest_profit = transactions[~dishonest_mask]['seller_profit'].fillna(0).sum()
                    total_profit = honest_profit + dishonest_profit
                    
                    # Calculate utilities
                    total_utility = transactions['buyer_utility'].fillna(0).sum()
                    
                    # Count transactions
                    dishonest_count = len(transactions[dishonest_mask])
                    honest_count = len(transactions[~dishonest_mask])
                    total_count = len(transactions)
                    
                    # Count deceptions (all products, not just transactions)
                    # Ensure quality values are strings
                    products['advertised_quality'] = products['advertised_quality'].astype(str).str.strip()
                    products['true_quality'] = products['true_quality'].astype(str).str.strip()
                    deception_count = len(products[
                        (products['advertised_quality'] == 'HQ') & 
                        (products['true_quality'] == 'LQ')
                    ])
                    
                    seller_profits.append(total_profit)
                    honest_profits.append(honest_profit)
                    dishonest_profits.append(dishonest_profit)
                    buyer_utilities.append(total_utility)
                    transaction_counts.append(total_count)
                    honest_transaction_counts.append(honest_count)
                    dishonest_transaction_counts.append(dishonest_count)
                    deceptions.append(deception_count)
            except Exception as e:
                print(f"Warning: Could not process {db_file}: {e}")
        
        return {
            'run_ids': run_ids,
            'seller_profits': seller_profits,
            'honest_profits': honest_profits,
            'dishonest_profits': dishonest_profits,
            'buyer_utilities': buyer_utilities,
            'transaction_counts': transaction_counts,
            'honest_transaction_counts': honest_transaction_counts,
            'dishonest_transaction_counts': dishonest_transaction_counts,
            'deceptions': deceptions
        }
    
    def _plot_single_market_cross_run(self, axes_col, data, market_label, market_color, 
                                     ylim_profit, ylim_utility, ylim_tx, xlim_profit, xlim_utility):
        """Plot cross-run comparison for a single market mechanism (column layout)"""
        run_ids = data['run_ids']
        seller_profits = data['seller_profits']
        honest_profits = data['honest_profits']
        dishonest_profits = data['dishonest_profits']
        buyer_utilities = data['buyer_utilities']
        transaction_counts = data['transaction_counts']
        honest_transaction_counts = data['honest_transaction_counts']
        dishonest_transaction_counts = data['dishonest_transaction_counts']
        
        # 1. Seller total profit comparison (stacked)
        axes_col[0].bar(run_ids, honest_profits, alpha=0.7, 
                       color=COLORS['honest'], label='Honest Profit', edgecolor='black')
        axes_col[0].bar(run_ids, dishonest_profits, 
                       bottom=honest_profits, alpha=0.7,
                       color=COLORS['dishonest'], label='Dishonest Profit', edgecolor='black')
        
        # Add mean lines
        honest_mean = np.mean(honest_profits)
        dishonest_mean = np.mean(dishonest_profits)
        total_mean = np.mean(seller_profits)
        
        axes_col[0].axhline(y=honest_mean, color='green', linestyle='--', linewidth=1.5,
                           label=f'Honest Mean: {honest_mean:.2f}')
        axes_col[0].axhline(y=dishonest_mean, color='darkred', linestyle='--', linewidth=1.5,
                           label=f'Dishonest Mean: {dishonest_mean:.2f}')
        axes_col[0].axhline(y=total_mean, color='blue', linestyle='--', linewidth=1.5,
                           label=f'Total Mean: {total_mean:.2f}')
        
        axes_col[0].set_title(f'Total Seller Profits ({market_label})', fontweight='bold')
        axes_col[0].set_xlabel('Run ID', fontweight='bold')
        axes_col[0].set_ylabel('Total Profit ($)', fontweight='bold')
        axes_col[0].set_ylim(ylim_profit)
        axes_col[0].legend(loc='lower right', frameon=True, fancybox=True, shadow=True, fontsize=9)
        axes_col[0].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # 2. Buyer total utility comparison
        # Use green for Reputation-Only, keep market_color for Reputation+Warrant
        bar_color = 'green' if 'Reputation-Only' in market_label else market_color
        axes_col[1].bar(run_ids, buyer_utilities, alpha=0.7, 
                       color=bar_color, edgecolor='black')
        # Use green for Reputation-Only, blue for Reputation+Warrant
        mean_color = 'green' if 'Reputation-Only' in market_label else 'blue'
        axes_col[1].axhline(y=np.mean(buyer_utilities), 
                           color=mean_color, linestyle='--', linewidth=1.5,
                           label=f'Mean: {np.mean(buyer_utilities):.2f}')
        axes_col[1].set_title(f'Total Buyer Utilities ({market_label})', fontweight='bold')
        axes_col[1].set_xlabel('Run ID', fontweight='bold')
        axes_col[1].set_ylabel('Total Utility ($)', fontweight='bold')
        axes_col[1].set_ylim(ylim_utility)
        axes_col[1].legend(loc='lower right', frameon=True, fancybox=True, shadow=True)
        axes_col[1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # 3. Transaction count comparison (stacked)
        axes_col[2].bar(run_ids, honest_transaction_counts, alpha=0.7,
                       color=COLORS['honest'], label='Honest Transactions', edgecolor='black')
        axes_col[2].bar(run_ids, dishonest_transaction_counts,
                       bottom=honest_transaction_counts, alpha=0.7,
                       color=COLORS['dishonest'], label='Dishonest Transactions', edgecolor='black')
        
        honest_tx_mean = np.mean(honest_transaction_counts)
        dishonest_tx_mean = np.mean(dishonest_transaction_counts)
        total_tx_mean = np.mean(transaction_counts)
        
        axes_col[2].axhline(y=honest_tx_mean, color='green', linestyle='--', linewidth=1.5,
                            label=f'Honest Mean: {honest_tx_mean:.1f}')
        axes_col[2].axhline(y=dishonest_tx_mean, color='darkred', linestyle='--', linewidth=1.5,
                            label=f'Dishonest Mean: {dishonest_tx_mean:.1f}')
        axes_col[2].axhline(y=total_tx_mean, color='blue', linestyle='--', linewidth=1.5,
                            label=f'Total Mean: {total_tx_mean:.1f}')
        
        axes_col[2].set_title(f'Transaction Counts ({market_label})', fontweight='bold')
        axes_col[2].set_xlabel('Run ID', fontweight='bold')
        axes_col[2].set_ylabel('Number of Transactions', fontweight='bold')
        axes_col[2].set_ylim(ylim_tx)
        axes_col[2].legend(loc='lower right', frameon=True, fancybox=True, shadow=True, fontsize=9)
        axes_col[2].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # 4. Profit vs Utility scatter plot
        axes_col[3].scatter(seller_profits, buyer_utilities, alpha=0.7, s=60,
                           color=market_color, edgecolors='black', linewidth=0.5)
        axes_col[3].set_title(f'Seller Profits vs Buyer Utilities ({market_label})', fontweight='bold')
        axes_col[3].set_xlabel('Total Seller Profit ($)', fontweight='bold')
        axes_col[3].set_ylabel('Total Buyer Utility ($)', fontweight='bold')
        axes_col[3].set_xlim(xlim_profit)
        axes_col[3].set_ylim(ylim_utility)
        axes_col[3].grid(True, alpha=0.3, linestyle='--')
        
        # Add run ID labels
        for i, run_id in enumerate(run_ids):
            axes_col[3].annotate(f'R{run_id}', (seller_profits[i], buyer_utilities[i]), 
                               xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    def plot_total_market_metrics(self):
        """5. Total Market Metrics & Honest vs Dishonest Analysis (Combined)"""
        r_exp_dir = Path(f"experiments/{self.r_exp_id}")
        rw_exp_dir = Path(f"experiments/{self.rw_exp_id}")
        
        r_data = self._prepare_cross_run_data(self.r_exp_id, r_exp_dir)
        rw_data = self._prepare_cross_run_data(self.rw_exp_id, rw_exp_dir)
        
        if not r_data['run_ids'] or not rw_data['run_ids']:
            print("Warning: Insufficient data for cross-run comparison")
            return
        
        # Calculate unified axis limits for comparison
        all_profits = r_data['seller_profits'] + rw_data['seller_profits']
        all_utilities = r_data['buyer_utilities'] + rw_data['buyer_utilities']
        all_tx_counts = r_data['transaction_counts'] + rw_data['transaction_counts']
        
        ylim_profit = (0, max(all_profits) * 1.1 if all_profits else 200)
        ylim_utility = (0, max(all_utilities) * 1.1 if all_utilities else 220)
        ylim_tx = (0, max(all_tx_counts) * 1.1 if all_tx_counts else 200)
        xlim_profit = (0, max(all_profits) * 1.1 if all_profits else 200)
        xlim_utility = (0, max(all_utilities) * 1.1 if all_utilities else 220)
        
        # Create 4x2 layout: Column 0 = Reputation-Only, Column 1 = Reputation+Warrant
        fig, axes = plt.subplots(4, 2, figsize=(14, 16))
        # fig.suptitle('Cross-Run Comparison Analysis', fontsize=16, fontweight='bold')
        
        # First column: Reputation-Only
        self._plot_single_market_cross_run(
            axes[:, 0], r_data, 'Reputation-Only', COLORS['reputation_only'],
            ylim_profit, ylim_utility, ylim_tx, xlim_profit, xlim_utility
        )
        
        # Second column: Reputation+Warrant
        self._plot_single_market_cross_run(
            axes[:, 1], rw_data, 'Reputation+Warrant', COLORS['reputation_warrant'],
            ylim_profit, ylim_utility, ylim_tx, xlim_profit, xlim_utility
        )
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '5_total_market_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 5_total_market_metrics.png")
    
    
    def generate_all(self):
        """Generate all visualizations"""
        print(f"Generating RQ2 visualizations...")
        print(f"Output directory: {self.output_dir}")
        print()
        
        self.plot_price_evolution()
        self.plot_seller_profit()
        self.plot_buyer_utility()
        self.plot_reputation()
        self.plot_total_market_metrics()
        
        print()
        print(f"✓ All visualizations generated in: {self.output_dir}")
        
        # Generate tables
        print()
        print("Generating tables...")
        self.generate_tables()
        print(f"✓ All tables generated in: {self.table_dir}")
    
    def _format_number(self, value: float, decimals: int = 2) -> str:
        """Format number with specified decimal places"""
        if pd.isna(value) or np.isnan(value):
            return "N/A"
        return f"{value:.{decimals}f}"
    
    def _calculate_p_value(self, group1: List[float], group2: List[float]) -> float:
        """Calculate p-value using t-test"""
        try:
            if len(group1) < 2 or len(group2) < 2:
                return np.nan
            t_stat, p_value = stats.ttest_ind(group1, group2)
            return p_value
        except:
            return np.nan
    
    def _generate_markdown_table(self, headers: List[str], rows: List[List[str]], 
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
    
    def _generate_latex_table(self, headers: List[str], rows: List[List[str]], 
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
        lines.append("\\begin{tabular}{" + "c" * len(headers) + "}")
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
    
    def generate_summary_statistics_table(self):
        """Generate Summary Statistics Table"""
        r_exp_dir = Path(f"experiments/{self.r_exp_id}")
        rw_exp_dir = Path(f"experiments/{self.rw_exp_id}")
        
        r_data = self._prepare_cross_run_data(self.r_exp_id, r_exp_dir)
        rw_data = self._prepare_cross_run_data(self.rw_exp_id, rw_exp_dir)
        
        if not r_data['run_ids'] or not rw_data['run_ids']:
            return
        
        # Calculate statistics
        metrics = []
        
        # Buyer utility
        r_utils = r_data['buyer_utilities']
        rw_utils = rw_data['buyer_utilities']
        r_util_mean = np.mean(r_utils)
        r_util_std = np.std(r_utils)
        rw_util_mean = np.mean(rw_utils)
        rw_util_std = np.std(rw_utils)
        util_change = ((rw_util_mean - r_util_mean) / r_util_mean * 100) if r_util_mean != 0 else 0
        util_p = self._calculate_p_value(r_utils, rw_utils)
        metrics.append({
            'name': 'Buyer Utility',
            'r_mean': r_util_mean,
            'r_std': r_util_std,
            'rw_mean': rw_util_mean,
            'rw_std': rw_util_std,
            'change': util_change,
            'p_value': util_p
        })
        
        # Seller profit
        r_profits = r_data['seller_profits']
        rw_profits = rw_data['seller_profits']
        r_profit_mean = np.mean(r_profits)
        r_profit_std = np.std(r_profits)
        rw_profit_mean = np.mean(rw_profits)
        rw_profit_std = np.std(rw_profits)
        profit_change = ((rw_profit_mean - r_profit_mean) / r_profit_mean * 100) if r_profit_mean != 0 else 0
        profit_p = self._calculate_p_value(r_profits, rw_profits)
        metrics.append({
            'name': 'Seller Profit',
            'r_mean': r_profit_mean,
            'r_std': r_profit_std,
            'rw_mean': rw_profit_mean,
            'rw_std': rw_profit_std,
            'change': profit_change,
            'p_value': profit_p
        })
        
        # Transactions
        r_tx = r_data['transaction_counts']
        rw_tx = rw_data['transaction_counts']
        r_tx_mean = np.mean(r_tx)
        r_tx_std = np.std(r_tx)
        rw_tx_mean = np.mean(rw_tx)
        rw_tx_std = np.std(rw_tx)
        tx_change = ((rw_tx_mean - r_tx_mean) / r_tx_mean * 100) if r_tx_mean != 0 else 0
        tx_p = self._calculate_p_value(r_tx, rw_tx)
        metrics.append({
            'name': 'Transactions',
            'r_mean': r_tx_mean,
            'r_std': r_tx_std,
            'rw_mean': rw_tx_mean,
            'rw_std': rw_tx_std,
            'change': tx_change,
            'p_value': tx_p
        })
        
        # Deception rate
        r_deceptions = r_data['deceptions']
        rw_deceptions = rw_data['deceptions']
        r_dec_mean = np.mean(r_deceptions)
        r_dec_std = np.std(r_deceptions)
        rw_dec_mean = np.mean(rw_deceptions)
        rw_dec_std = np.std(rw_deceptions)
        dec_change = ((rw_dec_mean - r_dec_mean) / r_dec_mean * 100) if r_dec_mean != 0 else 0
        dec_p = self._calculate_p_value(r_deceptions, rw_deceptions)
        metrics.append({
            'name': 'Deception Rate',
            'r_mean': r_dec_mean,
            'r_std': r_dec_std,
            'rw_mean': rw_dec_mean,
            'rw_std': rw_dec_std,
            'change': dec_change,
            'p_value': dec_p
        })
        
        # Market efficiency (total utility + profit)
        r_efficiency = [u + p for u, p in zip(r_utils, r_profits)]
        rw_efficiency = [u + p for u, p in zip(rw_utils, rw_profits)]
        r_eff_mean = np.mean(r_efficiency)
        r_eff_std = np.std(r_efficiency)
        rw_eff_mean = np.mean(rw_efficiency)
        rw_eff_std = np.std(rw_efficiency)
        eff_change = ((rw_eff_mean - r_eff_mean) / r_eff_mean * 100) if r_eff_mean != 0 else 0
        eff_p = self._calculate_p_value(r_efficiency, rw_efficiency)
        metrics.append({
            'name': 'Market Efficiency',
            'r_mean': r_eff_mean,
            'r_std': r_eff_std,
            'rw_mean': rw_eff_mean,
            'rw_std': rw_eff_std,
            'change': eff_change,
            'p_value': eff_p
        })
        
        # Prepare table data
        headers = ['Metric', 'Reputation-Only (Mean ± Std)', 
                  'Reputation+Warrant (Mean ± Std)', 'Change (%)', 'p-value']
        rows = []
        for m in metrics:
            r_str = f"{self._format_number(m['r_mean'])} ± {self._format_number(m['r_std'])}"
            rw_str = f"{self._format_number(m['rw_mean'])} ± {self._format_number(m['rw_std'])}"
            change_str = f"{self._format_number(m['change'], 1)}%"
            p_str = self._format_number(m['p_value'], 4) if not pd.isna(m['p_value']) else "N/A"
            rows.append([m['name'], r_str, rw_str, change_str, p_str])
        
        # Generate markdown and LaTeX tables
        md_table = self._generate_markdown_table(headers, rows, 
                                                 "Summary Statistics Comparison")
        latex_table = self._generate_latex_table(headers, rows,
                                                "Summary Statistics Comparison",
                                                "tab:summary_stats")
        
        # Save to file
        table_file = self.table_dir / "summary_statistics.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print("✓ Generated: summary_statistics.md")
    
    def generate_round_comparison_table(self):
        """Generate Round-by-Round Comparison Table"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        
        if r_rounds.empty or rw_rounds.empty:
            return
        
        # Aggregate by round
        r_agg = r_rounds.groupby('round').agg({
            'buyer_utility': ['mean', 'std'],
            'seller_profit': ['mean', 'std'],
            'transactions': ['mean', 'std']
        }).reset_index()
        
        rw_agg = rw_rounds.groupby('round').agg({
            'buyer_utility': ['mean', 'std'],
            'seller_profit': ['mean', 'std'],
            'transactions': ['mean', 'std']
        }).reset_index()
        
        # Get all rounds
        all_rounds = sorted(set(r_agg['round'].unique()) | set(rw_agg['round'].unique()))
        
        headers = ['Round', 'R-Buyer Utility', 'RW-Buyer Utility', 
                  'R-Seller Profit', 'RW-Seller Profit',
                  'R-Transactions', 'RW-Transactions']
        rows = []
        
        for round_num in all_rounds:
            r_row = r_agg[r_agg['round'] == round_num]
            rw_row = rw_agg[rw_agg['round'] == round_num]
            
            r_util = f"{self._format_number(r_row[('buyer_utility', 'mean')].values[0])}" if not r_row.empty else "N/A"
            rw_util = f"{self._format_number(rw_row[('buyer_utility', 'mean')].values[0])}" if not rw_row.empty else "N/A"
            r_profit = f"{self._format_number(r_row[('seller_profit', 'mean')].values[0])}" if not r_row.empty else "N/A"
            rw_profit = f"{self._format_number(rw_row[('seller_profit', 'mean')].values[0])}" if not rw_row.empty else "N/A"
            r_tx = f"{self._format_number(r_row[('transactions', 'mean')].values[0], 1)}" if not r_row.empty else "N/A"
            rw_tx = f"{self._format_number(rw_row[('transactions', 'mean')].values[0], 1)}" if not rw_row.empty else "N/A"
            
            rows.append([str(round_num), r_util, rw_util, r_profit, rw_profit, r_tx, rw_tx])
        
        # Generate markdown and LaTeX tables
        md_table = self._generate_markdown_table(headers, rows,
                                                "Round-by-Round Comparison")
        latex_table = self._generate_latex_table(headers, rows,
                                                "Round-by-Round Comparison",
                                                "tab:round_comparison")
        
        # Save to file
        table_file = self.table_dir / "round_comparison.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print("✓ Generated: round_comparison.md")
    
    def generate_tables(self):
        """Generate all tables"""
        self.generate_summary_statistics_table()
        self.generate_round_comparison_table()


def main():
    parser = argparse.ArgumentParser(description='Generate RQ2 market mechanism comparison visualizations')
    parser.add_argument('--r-exp', '--reputation-only', dest='r_exp', required=True,
                       help='Reputation-Only experiment ID')
    parser.add_argument('--rw-exp', '--reputation-warrant', dest='rw_exp', required=True,
                       help='Reputation+Warrant experiment ID')
    parser.add_argument('--out', dest='output_dir', default=None,
                       help='Output directory (default: visualization/figs/rq2_comparison)')
    
    args = parser.parse_args()
    
    visualizer = RQ2Visualizer(args.r_exp, args.rw_exp, args.output_dir)
    visualizer.generate_all()


if __name__ == "__main__":
    main()

