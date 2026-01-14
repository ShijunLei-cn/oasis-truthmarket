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
    'reputation_warrant': '#1f77b4',  # Blue (darker blue for better contrast)
    'honest': '#2ca02c',  # Green
    'honest_rw': '#9467bd',  # Purple for Reputation+Warrant honest (better contrast)
    'dishonest': '#d62728',  # Red
    'dishonest_rw': '#ff7f0e',  # Orange for Reputation+Warrant dishonest (better contrast)
    'hq': '#4C78A8',  # Blue
    'hq_rw': '#E45756',  # Red/Pink for Reputation+Warrant HQ (better contrast)
    'lq': '#F58518',  # Orange
    'lq_rw': '#54A24B',  # Green for Reputation+Warrant LQ (better contrast)
}


class RQ2Visualizer:
    """RQ2 Market Mechanism Comparison Visualizer"""
    
    def _extract_prefix_from_exp_id(self, exp_id: str) -> str:
        """Extract prefix from experiment ID (e.g., 'gpt-4o-mini/paper/rq2/r_wo' -> 'gpt-4o-mini/paper')"""
        if '/' in exp_id:
            parts = exp_id.split('/')
            # If contains 'paper', extract up to and including 'paper'
            if 'paper' in parts:
                paper_idx = parts.index('paper')
                return '/'.join(parts[:paper_idx + 1])
            # Otherwise, return first part (backward compatibility)
            return parts[0]
        return ""
    
    def __init__(self, r_experiment_id: str, rw_experiment_id: str, output_dir: Optional[str] = None):
        """
        Initialize visualizer
        
        Args:
            r_experiment_id: Reputation-Only experiment ID
            rw_experiment_id: Reputation+Warrant experiment ID
            output_dir: Output directory (default: visualization/figs/{prefix}/rq2_comparison)
        """
        self.r_exp_id = r_experiment_id
        self.rw_exp_id = rw_experiment_id
        
        if output_dir is None:
            # Extract prefix from experiment IDs
            r_prefix = self._extract_prefix_from_exp_id(r_experiment_id)
            rw_prefix = self._extract_prefix_from_exp_id(rw_experiment_id)
            # Use common prefix if both have prefixes, otherwise use the one that has it
            prefix = None
            if r_prefix == rw_prefix:
                prefix = r_prefix
            if prefix:
                output_dir = f"visualization/figs/{prefix}/rq2_comparison"
            else:
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
                # Try to load with public_thumbs_up/public_thumbs_down first, fallback to public_reputation_score
                try:
                    reputation = pd.read_sql_query(
                        "SELECT round, seller_id, public_thumbs_up, public_thumbs_down FROM reputation_history",
                        conn
                    )
                    # Calculate reputation score from thumbs_up and thumbs_down
                    if not reputation.empty:
                        reputation['public_reputation_score'] = reputation['public_thumbs_up'] - reputation['public_thumbs_down']
                except:
                    # Fallback: use public_reputation_score directly if it exists
                    try:
                        reputation = pd.read_sql_query(
                            "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                            conn
                        )
                    except:
                        # If public_reputation_score doesn't exist either, create empty dataframe
                        reputation = pd.DataFrame(columns=['round', 'seller_id', 'public_reputation_score'])
                
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
    
    def _load_round_profit_by_type(self, exp_id: str) -> pd.DataFrame:
        """Load round-by-round data with honest/dishonest profit breakdown"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load transactions with product quality information
                transactions = pd.read_sql_query(
                    "SELECT t.round_number, t.seller_profit, p.advertised_quality, p.true_quality "
                    "FROM transactions t JOIN product p ON t.product_id = p.product_id",
                    conn
                )
                
                conn.close()
                
                if not transactions.empty:
                    # Ensure quality values are strings and strip whitespace
                    transactions['advertised_quality'] = transactions['advertised_quality'].astype(str).str.strip()
                    transactions['true_quality'] = transactions['true_quality'].astype(str).str.strip()
                    
                    # Filter valid quality values
                    valid_quality_mask = (
                        (transactions['advertised_quality'].isin(['HQ', 'LQ'])) &
                        (transactions['true_quality'].isin(['HQ', 'LQ']))
                    )
                    
                    # Identify dishonest transactions: advertised HQ but delivered LQ
                    dishonest_mask = (
                        valid_quality_mask &
                        (transactions['advertised_quality'] == 'HQ') & 
                        (transactions['true_quality'] == 'LQ')
                    )
                    
                    honest_mask = valid_quality_mask & ~dishonest_mask
                    
                    # Aggregate by round
                    all_round_numbers = sorted(transactions['round_number'].dropna().unique())
                    for round_num in all_round_numbers:
                        round_num = int(round_num)
                        round_trans = transactions[transactions['round_number'] == round_num]
                        
                        # Apply masks to the round-specific transactions
                        round_valid_mask = (
                            (round_trans['advertised_quality'].isin(['HQ', 'LQ'])) &
                            (round_trans['true_quality'].isin(['HQ', 'LQ']))
                        )
                        round_dishonest_mask = (
                            round_valid_mask &
                            (round_trans['advertised_quality'] == 'HQ') & 
                            (round_trans['true_quality'] == 'LQ')
                        )
                        round_honest_mask = round_valid_mask & ~round_dishonest_mask
                        
                        round_dishonest = round_trans[round_dishonest_mask]
                        round_honest = round_trans[round_honest_mask]
                        
                        all_rounds_data.append({
                            'run_id': run_id,
                            'round': round_num,
                            'honest_profit': round_honest['seller_profit'].fillna(0).sum(),
                            'dishonest_profit': round_dishonest['seller_profit'].fillna(0).sum(),
                        })
            except Exception as e:
                print(f"Warning: Could not load profit data from {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _load_seller_profit_by_round(self, exp_id: str) -> pd.DataFrame:
        """Load individual seller profit by round"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_seller_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load transactions with seller_id and round_number
                transactions = pd.read_sql_query(
                    "SELECT round_number, seller_id, seller_profit FROM transactions",
                    conn
                )
                
                conn.close()
                
                if not transactions.empty:
                    # Group by seller and round to aggregate profit per seller per round
                    for (round_num, seller_id), group in transactions.groupby(['round_number', 'seller_id']):
                        all_seller_data.append({
                            'run_id': run_id,
                            'round': int(round_num),
                            'seller_id': int(seller_id),
                            'seller_profit': group['seller_profit'].sum()
                        })
            except Exception as e:
                print(f"Warning: Could not load seller profit data from {db_file}: {e}")
        
        return pd.DataFrame(all_seller_data)
    
    def _load_buyer_utility_by_round(self, exp_id: str) -> pd.DataFrame:
        """Load individual buyer utility by round"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_buyer_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load transactions with buyer_id and round_number
                transactions = pd.read_sql_query(
                    "SELECT round_number, buyer_id, buyer_utility FROM transactions",
                    conn
                )
                
                conn.close()
                
                if not transactions.empty:
                    # Group by buyer and round to aggregate utility per buyer per round
                    for (round_num, buyer_id), group in transactions.groupby(['round_number', 'buyer_id']):
                        all_buyer_data.append({
                            'run_id': run_id,
                            'round': int(round_num),
                            'buyer_id': int(buyer_id),
                            'buyer_utility': group['buyer_utility'].sum()
                        })
            except Exception as e:
                print(f"Warning: Could not load buyer utility data from {db_file}: {e}")
        
        return pd.DataFrame(all_buyer_data)
    
    def plot_price_evolution(self):
        """1. Price Evolution Over Rounds"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        
        # Check if data is empty
        if r_rounds.empty or 'round' not in r_rounds.columns:
            print("Warning: No data available for reputation-only experiment")
            r_rounds = pd.DataFrame(columns=['round', 'avg_price_hq', 'avg_price_lq'])
        if rw_rounds.empty or 'round' not in rw_rounds.columns:
            print("Warning: No data available for reputation+warrant experiment")
            rw_rounds = pd.DataFrame(columns=['round', 'avg_price_hq', 'avg_price_lq'])
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Aggregate across runs
        if not r_rounds.empty and 'round' in r_rounds.columns:
            r_agg = r_rounds.groupby('round').agg({
                'avg_price_hq': ['mean', 'std'],
                'avg_price_lq': ['mean', 'std']
            }).reset_index()
        else:
            r_agg = pd.DataFrame(columns=['round', ('avg_price_hq', 'mean'), ('avg_price_hq', 'std'), ('avg_price_lq', 'mean'), ('avg_price_lq', 'std')])
        
        if not rw_rounds.empty and 'round' in rw_rounds.columns:
            rw_agg = rw_rounds.groupby('round').agg({
                'avg_price_hq': ['mean', 'std'],
                'avg_price_lq': ['mean', 'std']
            }).reset_index()
        else:
            rw_agg = pd.DataFrame(columns=['round', ('avg_price_hq', 'mean'), ('avg_price_hq', 'std'), ('avg_price_lq', 'mean'), ('avg_price_lq', 'std')])
        
        # Get rounds from both experiments
        all_rounds = set()
        if not r_agg.empty and 'round' in r_agg.columns:
            all_rounds.update(r_agg['round'].unique())
        if not rw_agg.empty and 'round' in rw_agg.columns:
            all_rounds.update(rw_agg['round'].unique())
        rounds = sorted(all_rounds) if all_rounds else []
        
        if not rounds:
            print("Warning: No rounds data available for price evolution plot")
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_xlabel('Round', fontweight='bold')
            ax.set_ylabel('Average Price ($)', fontweight='bold')
            ax.set_title('Price Evolution Over Rounds', fontweight='bold', pad=15)
            plt.tight_layout()
            plt.savefig(self.output_dir / '1_price_evolution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Generated: 1_price_evolution.png (empty)")
            return
        
        # Fill NaN values with market parameter defaults
        default_hq_price = self.market_params.get('hq_price', 5.0)
        default_lq_price = self.market_params.get('lq_price', 3.0)
        
        # Safely access aggregated data
        if not r_agg.empty and ('avg_price_hq', 'mean') in r_agg.columns:
            r_hq_mean = r_agg[('avg_price_hq', 'mean')].fillna(default_hq_price)
            r_hq_std = r_agg[('avg_price_hq', 'std')].fillna(0)
            r_lq_mean = r_agg[('avg_price_lq', 'mean')].fillna(default_lq_price)
            r_lq_std = r_agg[('avg_price_lq', 'std')].fillna(0)
        else:
            r_hq_mean = pd.Series([default_hq_price] * len(rounds), index=rounds)
            r_hq_std = pd.Series([0] * len(rounds), index=rounds)
            r_lq_mean = pd.Series([default_lq_price] * len(rounds), index=rounds)
            r_lq_std = pd.Series([0] * len(rounds), index=rounds)
        
        if not rw_agg.empty and ('avg_price_hq', 'mean') in rw_agg.columns:
            rw_hq_mean = rw_agg[('avg_price_hq', 'mean')].fillna(default_hq_price)
            rw_hq_std = rw_agg[('avg_price_hq', 'std')].fillna(0)
            rw_lq_mean = rw_agg[('avg_price_lq', 'mean')].fillna(default_lq_price)
            rw_lq_std = rw_agg[('avg_price_lq', 'std')].fillna(0)
        else:
            rw_hq_mean = pd.Series([default_hq_price] * len(rounds), index=rounds)
            rw_hq_std = pd.Series([0] * len(rounds), index=rounds)
            rw_lq_mean = pd.Series([default_lq_price] * len(rounds), index=rounds)
            rw_lq_std = pd.Series([0] * len(rounds), index=rounds)
        
        # Align data with rounds
        r_hq_mean = r_hq_mean.reindex(rounds, fill_value=default_hq_price)
        r_hq_std = r_hq_std.reindex(rounds, fill_value=0)
        r_lq_mean = r_lq_mean.reindex(rounds, fill_value=default_lq_price)
        r_lq_std = r_lq_std.reindex(rounds, fill_value=0)
        rw_hq_mean = rw_hq_mean.reindex(rounds, fill_value=default_hq_price)
        rw_hq_std = rw_hq_std.reindex(rounds, fill_value=0)
        rw_lq_mean = rw_lq_mean.reindex(rounds, fill_value=default_lq_price)
        rw_lq_std = rw_lq_std.reindex(rounds, fill_value=0)
        
        # Plot HQ prices
        ax.errorbar(rounds, r_hq_mean, 
                   yerr=r_hq_std,
                   fmt='o-', label='Reputation-Only (HQ)', 
                   color=COLORS['reputation_only'], linewidth=2, markersize=6, capsize=3, alpha=0.6)
        ax.errorbar(rounds, rw_hq_mean,
                   yerr=rw_hq_std,
                   fmt='s-', label='Reputation+Warrant (HQ)',
                   color=COLORS['hq_rw'], linewidth=2, markersize=6, capsize=3, alpha=0.6)
        
        # Plot LQ prices
        ax.errorbar(rounds, r_lq_mean,
                   yerr=r_lq_std,
                   fmt='o-', label='Reputation-Only (LQ)',
                   color=COLORS['lq'], linewidth=1.5, markersize=5, 
                   capsize=2, alpha=0.6)
        ax.errorbar(rounds, rw_lq_mean,
                   yerr=rw_lq_std,
                   fmt='s-', label='Reputation+Warrant (LQ)',
                   color=COLORS['lq_rw'], linewidth=1.5, markersize=5,
                   capsize=2, alpha=0.6)
        
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
        r_profit_by_type = self._load_round_profit_by_type(self.r_exp_id)
        rw_profit_by_type = self._load_round_profit_by_type(self.rw_exp_id)
        
        # Check if data is available
        if r_rounds.empty or 'round' not in r_rounds.columns:
            print(f"Warning: No valid data for reputation-only experiment {self.r_exp_id}")
            return
        if rw_rounds.empty or 'round' not in rw_rounds.columns:
            print(f"Warning: No valid data for reputation+warrant experiment {self.rw_exp_id}")
            return
        
        fig, axes = plt.subplots(3, 2, figsize=(14, 15))
        
        # Top Left: Total profit line plot
        r_agg = r_rounds.groupby('round')['seller_profit'].agg(['mean', 'std']).reset_index()
        rw_agg = rw_rounds.groupby('round')['seller_profit'].agg(['mean', 'std']).reset_index()
        
        rounds = sorted(r_agg['round'].unique())
        axes[0, 0].errorbar(rounds, r_agg['mean'], yerr=r_agg['std'],
                       fmt='o-', label='Reputation-Only', color=COLORS['reputation_only'],
                       linewidth=2, markersize=7, capsize=4, alpha=0.6)
        axes[0, 0].errorbar(rounds, rw_agg['mean'], yerr=rw_agg['std'],
                        fmt='s-', label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                        linewidth=2, markersize=7, capsize=4, alpha=0.6)
        axes[0, 0].set_xlabel('Round', fontweight='bold')
        axes[0, 0].set_ylabel('Average Seller Profit ($)', fontweight='bold')
        axes[0, 0].set_title('Total Seller Profit Progression', fontweight='bold')
        axes[0, 0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        axes[0, 0].set_xticks(rounds)
        
        # Top Right: KDE distribution comparison
        r_all_profits = r_rounds['seller_profit'].dropna().values
        rw_all_profits = rw_rounds['seller_profit'].dropna().values
        
        if len(r_all_profits) > 0 and len(rw_all_profits) > 0:
            # Check if data is suitable for KDE (has variance and enough points)
            r_has_variance = len(r_all_profits) > 1 and np.std(r_all_profits) > 1e-10
            rw_has_variance = len(rw_all_profits) > 1 and np.std(rw_all_profits) > 1e-10
            
            if r_has_variance and rw_has_variance:
                # Create KDE plots
                r_kde = stats.gaussian_kde(r_all_profits)
                rw_kde = stats.gaussian_kde(rw_all_profits)
                
                x_min = min(r_all_profits.min(), rw_all_profits.min())
                x_max = max(r_all_profits.max(), rw_all_profits.max())
                x_range = np.linspace(x_min, x_max, 200)
                
                axes[0, 1].plot(x_range, r_kde(x_range), label='Reputation-Only', 
                            color=COLORS['reputation_only'], linewidth=2, alpha=0.6)
                axes[0, 1].fill_between(x_range, r_kde(x_range), alpha=0.3, 
                                   color=COLORS['reputation_only'])
                axes[0, 1].plot(x_range, rw_kde(x_range), label='Reputation+Warrant',
                            color=COLORS['reputation_warrant'], linewidth=2, alpha=0.6)
                axes[0, 1].fill_between(x_range, rw_kde(x_range), alpha=0.3,
                                   color=COLORS['reputation_warrant'])
            else:
                # Use histogram instead when variance is too low
                axes[0, 1].hist(r_all_profits, bins=20, alpha=0.5, 
                            label='Reputation-Only', color=COLORS['reputation_only'], 
                            density=True, edgecolor='black', linewidth=0.5)
                axes[0, 1].hist(rw_all_profits, bins=20, alpha=0.5,
                            label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                            density=True, edgecolor='black', linewidth=0.5)
            
            # Add mean lines
            axes[0, 1].axvline(np.mean(r_all_profits), color=COLORS['reputation_only'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
            axes[0, 1].axvline(np.mean(rw_all_profits), color=COLORS['reputation_warrant'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
        
        axes[0, 1].set_xlabel('Seller Profit ($)', fontweight='bold')
        axes[0, 1].set_ylabel('Density', fontweight='bold')
        axes[0, 1].set_title('Profit Distribution Comparison', fontweight='bold')
        axes[0, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Bottom Left: Honest profit progression
        if not r_profit_by_type.empty and not rw_profit_by_type.empty:
            r_honest_agg = r_profit_by_type.groupby('round')['honest_profit'].agg(['mean', 'std']).reset_index()
            rw_honest_agg = rw_profit_by_type.groupby('round')['honest_profit'].agg(['mean', 'std']).reset_index()
            
            honest_rounds = sorted(set(r_honest_agg['round'].unique()) | set(rw_honest_agg['round'].unique()))
            axes[1, 0].errorbar(honest_rounds, r_honest_agg['mean'], yerr=r_honest_agg['std'],
                           fmt='o-', label='Reputation-Only (Honest)', color=COLORS['honest'],
                           linewidth=2, markersize=6, capsize=3, alpha=0.6)
            axes[1, 0].errorbar(honest_rounds, rw_honest_agg['mean'], yerr=rw_honest_agg['std'],
                            fmt='s-', label='Reputation+Warrant (Honest)', color=COLORS['honest_rw'],
                            linewidth=2, markersize=6, capsize=3, alpha=0.6)
        
        axes[1, 0].set_xlabel('Round', fontweight='bold')
        axes[1, 0].set_ylabel('Average Honest Profit ($)', fontweight='bold')
        axes[1, 0].set_title('Honest Profit Progression', fontweight='bold')
        axes[1, 0].legend(frameon=True, fancybox=True, shadow=True)
        axes[1, 0].grid(True, alpha=0.3, linestyle='--')
        if not r_profit_by_type.empty:
            axes[1, 0].set_xticks(honest_rounds)
        
        # Bottom Right: Dishonest profit progression
        if not r_profit_by_type.empty and not rw_profit_by_type.empty:
            r_dishonest_agg = r_profit_by_type.groupby('round')['dishonest_profit'].agg(['mean', 'std']).reset_index()
            rw_dishonest_agg = rw_profit_by_type.groupby('round')['dishonest_profit'].agg(['mean', 'std']).reset_index()
            
            dishonest_rounds = sorted(set(r_dishonest_agg['round'].unique()) | set(rw_dishonest_agg['round'].unique()))
            axes[1, 1].errorbar(dishonest_rounds, r_dishonest_agg['mean'], yerr=r_dishonest_agg['std'],
                           fmt='o-', label='Reputation-Only (Dishonest)', color=COLORS['dishonest'],
                           linewidth=2, markersize=6, capsize=3, alpha=0.6)
            axes[1, 1].errorbar(dishonest_rounds, rw_dishonest_agg['mean'], yerr=rw_dishonest_agg['std'],
                            fmt='s-', label='Reputation+Warrant (Dishonest)', color=COLORS['dishonest_rw'],
                            linewidth=2, markersize=6, capsize=3, alpha=0.6)
        
        axes[1, 1].set_xlabel('Round', fontweight='bold')
        axes[1, 1].set_ylabel('Average Dishonest Profit ($)', fontweight='bold')
        axes[1, 1].set_title('Dishonest Profit Progression', fontweight='bold')
        axes[1, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[1, 1].grid(True, alpha=0.3, linestyle='--')
        if not r_profit_by_type.empty:
            axes[1, 1].set_xticks(dishonest_rounds)
        
        # Row 2: Individual seller profit by round
        # Left: Reputation-Only
        r_seller_profit = self._load_seller_profit_by_round(self.r_exp_id)
        if not r_seller_profit.empty:
            seller_ids = sorted(r_seller_profit['seller_id'].unique())
            for seller_id in seller_ids:
                seller_data = r_seller_profit[r_seller_profit['seller_id'] == seller_id].sort_values('round')
                if not seller_data.empty:
                    axes[2, 0].plot(seller_data['round'], seller_data['seller_profit'],
                                   marker='o', linewidth=1.5, markersize=4, alpha=0.7,
                                   label=f'Seller {seller_id}')
        axes[2, 0].set_xlabel('Round', fontweight='bold')
        axes[2, 0].set_ylabel('Seller Profit ($)', fontweight='bold')
        axes[2, 0].set_title('Individual Seller Profit (Reputation-Only)', fontweight='bold')
        axes[2, 0].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
        axes[2, 0].grid(True, alpha=0.3, linestyle='--')
        if not r_rounds.empty:
            axes[2, 0].set_xticks(rounds)
        
        # Right: Reputation+Warrant
        rw_seller_profit = self._load_seller_profit_by_round(self.rw_exp_id)
        if not rw_seller_profit.empty:
            seller_ids = sorted(rw_seller_profit['seller_id'].unique())
            for seller_id in seller_ids:
                seller_data = rw_seller_profit[rw_seller_profit['seller_id'] == seller_id].sort_values('round')
                if not seller_data.empty:
                    axes[2, 1].plot(seller_data['round'], seller_data['seller_profit'],
                                   marker='s', linewidth=1.5, markersize=4, alpha=0.7,
                                   label=f'Seller {seller_id}')
        axes[2, 1].set_xlabel('Round', fontweight='bold')
        axes[2, 1].set_ylabel('Seller Profit ($)', fontweight='bold')
        axes[2, 1].set_title('Individual Seller Profit (Reputation+Warrant)', fontweight='bold')
        axes[2, 1].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
        axes[2, 1].grid(True, alpha=0.3, linestyle='--')
        if not rw_rounds.empty:
            axes[2, 1].set_xticks(rounds)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '2_seller_profit.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 2_seller_profit.png")
    
    def plot_buyer_utility(self):
        """3. Buyer Utility Over Rounds"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        
        fig, axes = plt.subplots(3, 2, figsize=(14, 15))
        
        # Row 0, Left: Line plot
        r_agg = r_rounds.groupby('round')['buyer_utility'].agg(['mean', 'std']).reset_index()
        rw_agg = rw_rounds.groupby('round')['buyer_utility'].agg(['mean', 'std']).reset_index()
        
        rounds = sorted(r_agg['round'].unique())
        axes[0, 0].errorbar(rounds, r_agg['mean'], yerr=r_agg['std'],
                        fmt='o-', label='Reputation-Only', color=COLORS['reputation_only'],
                        linewidth=2, markersize=7, capsize=4, alpha=0.6)
        axes[0, 0].errorbar(rounds, rw_agg['mean'], yerr=rw_agg['std'],
                        fmt='s-', label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                        linewidth=2, markersize=7, capsize=4, alpha=0.6)
        axes[0, 0].set_xlabel('Round', fontweight='bold')
        axes[0, 0].set_ylabel('Average Buyer Utility ($)', fontweight='bold')
        axes[0, 0].set_title('Buyer Utility Progression', fontweight='bold')
        axes[0, 0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        axes[0, 0].set_xticks(rounds)
        
        # Row 0, Right: KDE distribution comparison
        r_all_utils = r_rounds['buyer_utility'].dropna().values
        rw_all_utils = rw_rounds['buyer_utility'].dropna().values
        
        if len(r_all_utils) > 0 and len(rw_all_utils) > 0:
            # Check if data is suitable for KDE (has variance and enough points)
            r_has_variance = len(r_all_utils) > 1 and np.std(r_all_utils) > 1e-10
            rw_has_variance = len(rw_all_utils) > 1 and np.std(rw_all_utils) > 1e-10
            
            if r_has_variance and rw_has_variance:
                # Create KDE plots
                r_kde = stats.gaussian_kde(r_all_utils)
                rw_kde = stats.gaussian_kde(rw_all_utils)
                
                x_min = min(r_all_utils.min(), rw_all_utils.min())
                x_max = max(r_all_utils.max(), rw_all_utils.max())
                x_range = np.linspace(x_min, x_max, 200)
                
                axes[0, 1].plot(x_range, r_kde(x_range), label='Reputation-Only',
                            color=COLORS['reputation_only'], linewidth=2, alpha=0.6)
                axes[0, 1].fill_between(x_range, r_kde(x_range), alpha=0.3,
                                   color=COLORS['reputation_only'])
                axes[0, 1].plot(x_range, rw_kde(x_range), label='Reputation+Warrant',
                            color=COLORS['reputation_warrant'], linewidth=2, alpha=0.6)
                axes[0, 1].fill_between(x_range, rw_kde(x_range), alpha=0.3,
                                   color=COLORS['reputation_warrant'])
            else:
                # Use histogram instead when variance is too low
                axes[0, 1].hist(r_all_utils, bins=20, alpha=0.5,
                            label='Reputation-Only', color=COLORS['reputation_only'],
                            density=True, edgecolor='black', linewidth=0.5)
                axes[0, 1].hist(rw_all_utils, bins=20, alpha=0.5,
                            label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                            density=True, edgecolor='black', linewidth=0.5)
            
            # Add mean lines
            axes[0, 1].axvline(np.mean(r_all_utils), color=COLORS['reputation_only'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
            axes[0, 1].axvline(np.mean(rw_all_utils), color=COLORS['reputation_warrant'],
                           linestyle=':', linewidth=1.5, alpha=0.7)
        
        axes[0, 1].set_xlabel('Buyer Utility ($)', fontweight='bold')
        axes[0, 1].set_ylabel('Density', fontweight='bold')
        axes[0, 1].set_title('Utility Distribution Comparison', fontweight='bold')
        axes[0, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Row 1: Empty or can be used for other visualizations
        axes[1, 0].axis('off')
        axes[1, 1].axis('off')
        
        # Row 2: Individual buyer utility by round
        # Left: Reputation-Only
        r_buyer_utility = self._load_buyer_utility_by_round(self.r_exp_id)
        if not r_buyer_utility.empty:
            buyer_ids = sorted(r_buyer_utility['buyer_id'].unique())
            for buyer_id in buyer_ids:
                buyer_data = r_buyer_utility[r_buyer_utility['buyer_id'] == buyer_id].sort_values('round')
                if not buyer_data.empty:
                    axes[2, 0].plot(buyer_data['round'], buyer_data['buyer_utility'],
                                   marker='o', linewidth=1.5, markersize=4, alpha=0.7,
                                   label=f'Buyer {buyer_id}')
        axes[2, 0].set_xlabel('Round', fontweight='bold')
        axes[2, 0].set_ylabel('Buyer Utility ($)', fontweight='bold')
        axes[2, 0].set_title('Individual Buyer Utility (Reputation-Only)', fontweight='bold')
        axes[2, 0].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
        axes[2, 0].grid(True, alpha=0.3, linestyle='--')
        if not r_rounds.empty:
            axes[2, 0].set_xticks(rounds)
        
        # Right: Reputation+Warrant
        rw_buyer_utility = self._load_buyer_utility_by_round(self.rw_exp_id)
        if not rw_buyer_utility.empty:
            buyer_ids = sorted(rw_buyer_utility['buyer_id'].unique())
            for buyer_id in buyer_ids:
                buyer_data = rw_buyer_utility[rw_buyer_utility['buyer_id'] == buyer_id].sort_values('round')
                if not buyer_data.empty:
                    axes[2, 1].plot(buyer_data['round'], buyer_data['buyer_utility'],
                                   marker='s', linewidth=1.5, markersize=4, alpha=0.7,
                                   label=f'Buyer {buyer_id}')
        axes[2, 1].set_xlabel('Round', fontweight='bold')
        axes[2, 1].set_ylabel('Buyer Utility ($)', fontweight='bold')
        axes[2, 1].set_title('Individual Buyer Utility (Reputation+Warrant)', fontweight='bold')
        axes[2, 1].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
        axes[2, 1].grid(True, alpha=0.3, linestyle='--')
        if not rw_rounds.empty:
            axes[2, 1].set_xticks(rounds)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '3_buyer_utility.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 3_buyer_utility.png")
    
    def plot_reputation(self):
        """4. Seller Reputation Over Rounds"""
        r_exp_dir = Path(f"experiments/{self.r_exp_id}")
        rw_exp_dir = Path(f"experiments/{self.rw_exp_id}")
        
        # Create 3x2 layout: Row 0 = Average reputation, Row 1 = Individual sellers, Row 2 = Rating by quality
        fig, axes = plt.subplots(3, 2, figsize=(14, 15))
        
        # Load reputation data
        r_reps = []
        rw_reps = []
        
        for db_file in sorted(r_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Try to load with public_thumbs_up/public_thumbs_down first, fallback to public_reputation_score
                try:
                    rep = pd.read_sql_query(
                        "SELECT round, seller_id, public_thumbs_up, public_thumbs_down FROM reputation_history",
                        conn
                    )
                    # Calculate reputation score from thumbs_up and thumbs_down
                    if not rep.empty:
                        rep['public_reputation_score'] = rep['public_thumbs_up'] - rep['public_thumbs_down']
                except:
                    # Fallback: use public_reputation_score directly
                    try:
                        rep = pd.read_sql_query(
                            "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                            conn
                        )
                    except:
                        rep = pd.DataFrame(columns=['round', 'seller_id', 'public_reputation_score'])
                r_reps.append(rep)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not load reputation data from {db_file}: {e}")
                pass
        
        for db_file in sorted(rw_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Try to load with public_thumbs_up/public_thumbs_down first, fallback to public_reputation_score
                try:
                    rep = pd.read_sql_query(
                        "SELECT round, seller_id, public_thumbs_up, public_thumbs_down FROM reputation_history",
                        conn
                    )
                    # Calculate reputation score from thumbs_up and thumbs_down
                    if not rep.empty:
                        rep['public_reputation_score'] = rep['public_thumbs_up'] - rep['public_thumbs_down']
                except:
                    # Fallback: use public_reputation_score directly
                    try:
                        rep = pd.read_sql_query(
                            "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                            conn
                        )
                    except:
                        rep = pd.DataFrame(columns=['round', 'seller_id', 'public_reputation_score'])
                rw_reps.append(rep)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not load reputation data from {db_file}: {e}")
                pass
        
        if r_reps and rw_reps:
            r_all = pd.concat(r_reps)
            rw_all = pd.concat(rw_reps)
            
            # Row 0: Average reputation progression (Left: Comparison line plot, Right: Distribution comparison)
            r_agg = r_all.groupby('round')['public_reputation_score'].agg(['mean', 'std']).reset_index()
            rw_agg = rw_all.groupby('round')['public_reputation_score'].agg(['mean', 'std']).reset_index()
            
            rounds = sorted(set(r_agg['round'].unique()) | set(rw_agg['round'].unique()))
            
            # Align data with rounds (handle missing rounds)
            r_mean_dict = dict(zip(r_agg['round'], r_agg['mean']))
            r_std_dict = dict(zip(r_agg['round'], r_agg['std']))
            rw_mean_dict = dict(zip(rw_agg['round'], rw_agg['mean']))
            rw_std_dict = dict(zip(rw_agg['round'], rw_agg['std']))
            
            r_mean_aligned = [r_mean_dict.get(r, np.nan) for r in rounds]
            r_std_aligned = [r_std_dict.get(r, 0) for r in rounds]
            rw_mean_aligned = [rw_mean_dict.get(r, np.nan) for r in rounds]
            rw_std_aligned = [rw_std_dict.get(r, 0) for r in rounds]
            
            # Left: Comparison line plot (both market types)
            axes[0, 0].errorbar(rounds, r_mean_aligned, yerr=r_std_aligned,
                           fmt='o-', label='Reputation-Only', color=COLORS['reputation_only'],
                           linewidth=2, markersize=7, capsize=4, alpha=0.6)
            axes[0, 0].errorbar(rounds, rw_mean_aligned, yerr=rw_std_aligned,
                            fmt='s-', label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                            linewidth=2, markersize=7, capsize=4, alpha=0.6)
            axes[0, 0].set_xlabel('Round', fontweight='bold')
            axes[0, 0].set_ylabel('Average Reputation Score', fontweight='bold')
            axes[0, 0].set_title('Average Reputation Progression', fontweight='bold')
            axes[0, 0].legend(frameon=True, fancybox=True, shadow=True)
            axes[0, 0].grid(True, alpha=0.3, linestyle='--')
            axes[0, 0].set_xticks(rounds)
            
            # Right: KDE distribution comparison
            r_all_scores = r_all['public_reputation_score'].dropna().values
            rw_all_scores = rw_all['public_reputation_score'].dropna().values
            
            if len(r_all_scores) > 0 and len(rw_all_scores) > 0:
                # Check if data is suitable for KDE (has variance and enough points)
                r_has_variance = len(r_all_scores) > 1 and np.std(r_all_scores) > 1e-10
                rw_has_variance = len(rw_all_scores) > 1 and np.std(rw_all_scores) > 1e-10
                
                if r_has_variance and rw_has_variance:
                    # Create KDE plots
                    r_kde = stats.gaussian_kde(r_all_scores)
                    rw_kde = stats.gaussian_kde(rw_all_scores)
                    
                    x_min = min(r_all_scores.min(), rw_all_scores.min())
                    x_max = max(r_all_scores.max(), rw_all_scores.max())
                    x_range = np.linspace(x_min, x_max, 200)
                    
                    axes[0, 1].plot(x_range, r_kde(x_range), label='Reputation-Only', 
                                color=COLORS['reputation_only'], linewidth=2, alpha=0.6)
                    axes[0, 1].fill_between(x_range, r_kde(x_range), alpha=0.3, 
                                       color=COLORS['reputation_only'])
                    axes[0, 1].plot(x_range, rw_kde(x_range), label='Reputation+Warrant',
                                color=COLORS['reputation_warrant'], linewidth=2, alpha=0.6)
                    axes[0, 1].fill_between(x_range, rw_kde(x_range), alpha=0.3,
                                       color=COLORS['reputation_warrant'])
                else:
                    # Use histogram instead when variance is too low
                    axes[0, 1].hist(r_all_scores, bins=20, alpha=0.5, 
                                label='Reputation-Only', color=COLORS['reputation_only'], 
                                density=True, edgecolor='black', linewidth=0.5)
                    axes[0, 1].hist(rw_all_scores, bins=20, alpha=0.5,
                                label='Reputation+Warrant', color=COLORS['reputation_warrant'],
                                density=True, edgecolor='black', linewidth=0.5)
                
                # Add mean lines
                axes[0, 1].axvline(np.mean(r_all_scores), color=COLORS['reputation_only'],
                               linestyle=':', linewidth=1.5, alpha=0.7)
                axes[0, 1].axvline(np.mean(rw_all_scores), color=COLORS['reputation_warrant'],
                               linestyle=':', linewidth=1.5, alpha=0.7)
            
            axes[0, 1].set_xlabel('Reputation Score', fontweight='bold')
            axes[0, 1].set_ylabel('Density', fontweight='bold')
            axes[0, 1].set_title('Reputation Distribution Comparison', fontweight='bold')
            axes[0, 1].legend(frameon=True, fancybox=True, shadow=True)
            axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
            
            # Row 1: Individual seller reputation evolution (Left: R, Right: RW)
            # Use first run's data for individual seller visualization
            if len(r_reps) > 0:
                r_sample = r_reps[0]
                # Get all seller IDs
                seller_ids = sorted(r_sample['seller_id'].unique())
                # Plot each seller's reputation evolution
                for seller_id in seller_ids:
                    seller_data = r_sample[r_sample['seller_id'] == seller_id].sort_values('round')
                    if not seller_data.empty:
                        axes[1, 0].plot(seller_data['round'], seller_data['public_reputation_score'],
                                       marker='o', linewidth=1.5, markersize=4, alpha=0.7,
                                       label=f'Seller {seller_id}')
                axes[1, 0].set_xlabel('Round', fontweight='bold')
                axes[1, 0].set_ylabel('Reputation Score', fontweight='bold')
                axes[1, 0].set_title('Individual Seller Reputation Evolution (Reputation-Only)', fontweight='bold')
                axes[1, 0].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
                axes[1, 0].grid(True, alpha=0.3, linestyle='--')
                axes[1, 0].set_xticks(rounds)
            
            if len(rw_reps) > 0:
                rw_sample = rw_reps[0]
                seller_ids = sorted(rw_sample['seller_id'].unique())
                for seller_id in seller_ids:
                    seller_data = rw_sample[rw_sample['seller_id'] == seller_id].sort_values('round')
                    if not seller_data.empty:
                        axes[1, 1].plot(seller_data['round'], seller_data['public_reputation_score'],
                                       marker='s', linewidth=1.5, markersize=4, alpha=0.7,
                                       label=f'Seller {seller_id}')
                axes[1, 1].set_xlabel('Round', fontweight='bold')
                axes[1, 1].set_ylabel('Reputation Score', fontweight='bold')
                axes[1, 1].set_title('Individual Seller Reputation Evolution (Reputation+Warrant)', fontweight='bold')
                axes[1, 1].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
                axes[1, 1].grid(True, alpha=0.3, linestyle='--')
                axes[1, 1].set_xticks(rounds)
            
            # Row 2: Rating about product quality (Left: R, Right: RW)
            # Load rating data grouped by product quality
            r_ratings_by_quality = self._load_ratings_by_quality(self.r_exp_id)
            rw_ratings_by_quality = self._load_ratings_by_quality(self.rw_exp_id)
            
            if not r_ratings_by_quality.empty:
                r_hq_ratings = r_ratings_by_quality[r_ratings_by_quality['true_quality'] == 'HQ']
                r_lq_ratings = r_ratings_by_quality[r_ratings_by_quality['true_quality'] == 'LQ']
                
                if not r_hq_ratings.empty:
                    r_hq_agg = r_hq_ratings.groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
                    axes[2, 0].errorbar(r_hq_agg['round_number'], r_hq_agg['mean'], yerr=r_hq_agg['std'],
                                       fmt='o-', label='HQ Products', color=COLORS['hq'],
                                       linewidth=2, markersize=6, capsize=3, alpha=0.6)
                
                if not r_lq_ratings.empty:
                    r_lq_agg = r_lq_ratings.groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
                    axes[2, 0].errorbar(r_lq_agg['round_number'], r_lq_agg['mean'], yerr=r_lq_agg['std'],
                                       fmt='s-', label='LQ Products', color=COLORS['lq'],
                                       linewidth=2, markersize=6, capsize=3, alpha=0.6)
                
                axes[2, 0].set_xlabel('Round', fontweight='bold')
                axes[2, 0].set_ylabel('Average Rating', fontweight='bold')
                axes[2, 0].set_title('Product Quality Rating (Reputation-Only)', fontweight='bold')
                axes[2, 0].legend(frameon=True, fancybox=True, shadow=True)
                axes[2, 0].grid(True, alpha=0.3, linestyle='--')
                axes[2, 0].set_xticks(rounds)
                axes[2, 0].axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
            
            if not rw_ratings_by_quality.empty:
                rw_hq_ratings = rw_ratings_by_quality[rw_ratings_by_quality['true_quality'] == 'HQ']
                rw_lq_ratings = rw_ratings_by_quality[rw_ratings_by_quality['true_quality'] == 'LQ']
                
                if not rw_hq_ratings.empty:
                    rw_hq_agg = rw_hq_ratings.groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
                    axes[2, 1].errorbar(rw_hq_agg['round_number'], rw_hq_agg['mean'], yerr=rw_hq_agg['std'],
                                       fmt='^-', label='HQ Products', color=COLORS['hq_rw'],
                                       linewidth=2, markersize=6, capsize=3, alpha=0.6)
                
                if not rw_lq_ratings.empty:
                    rw_lq_agg = rw_lq_ratings.groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
                    axes[2, 1].errorbar(rw_lq_agg['round_number'], rw_lq_agg['mean'], yerr=rw_lq_agg['std'],
                                       fmt='v-', label='LQ Products', color=COLORS['lq_rw'],
                                       linewidth=2, markersize=6, capsize=3, alpha=0.6)
                
                axes[2, 1].set_xlabel('Round', fontweight='bold')
                axes[2, 1].set_ylabel('Average Rating', fontweight='bold')
                axes[2, 1].set_title('Product Quality Rating (Reputation+Warrant)', fontweight='bold')
                axes[2, 1].legend(frameon=True, fancybox=True, shadow=True)
                axes[2, 1].grid(True, alpha=0.3, linestyle='--')
                axes[2, 1].set_xticks(rounds)
                axes[2, 1].axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '4_reputation.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 4_reputation.png")
    
    def _load_ratings_by_quality(self, exp_id: str) -> pd.DataFrame:
        """Load rating data grouped by product quality"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_ratings = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                
                # Join transactions with products to get quality information
                ratings = pd.read_sql_query(
                    """
                    SELECT t.round_number, t.rating, p.true_quality
                    FROM transactions t
                    JOIN product p ON t.product_id = p.product_id
                    WHERE t.rating IS NOT NULL
                    """,
                    conn
                )
                
                conn.close()
                
                if not ratings.empty:
                    # Ensure quality values are strings and strip whitespace
                    ratings['true_quality'] = ratings['true_quality'].astype(str).str.strip()
                    # Filter valid quality values
                    ratings = ratings[ratings['true_quality'].isin(['HQ', 'LQ'])]
                    all_ratings.append(ratings)
            except Exception as e:
                print(f"Warning: Could not load rating data from {db_file}: {e}")
        
        if all_ratings:
            return pd.concat(all_ratings, ignore_index=True)
        return pd.DataFrame(columns=['round_number', 'rating', 'true_quality'])
    
    def _load_product_quality_data(self, exp_id: str) -> pd.DataFrame:
        """Load product quality data by round"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load all products with quality information
                products = pd.read_sql_query(
                    "SELECT round_number, advertised_quality, true_quality FROM product",
                    conn
                )
                
                conn.close()
                
                if not products.empty:
                    # Ensure quality values are strings and strip whitespace
                    products['advertised_quality'] = products['advertised_quality'].astype(str).str.strip()
                    products['true_quality'] = products['true_quality'].astype(str).str.strip()
                    
                    # Filter valid quality values
                    valid_quality_mask = (
                        (products['advertised_quality'].isin(['HQ', 'LQ'])) &
                        (products['true_quality'].isin(['HQ', 'LQ']))
                    )
                    products = products[valid_quality_mask]
                    
                    # Aggregate by round
                    all_round_numbers = sorted(products['round_number'].dropna().unique())
                    for round_num in all_round_numbers:
                        round_num = int(round_num)
                        round_prod = products[products['round_number'] == round_num]
                        
                        # Count by four product types: (advertised, true)
                        lq_lq = len(round_prod[(round_prod['advertised_quality'] == 'LQ') & (round_prod['true_quality'] == 'LQ')])
                        lq_hq = len(round_prod[(round_prod['advertised_quality'] == 'LQ') & (round_prod['true_quality'] == 'HQ')])
                        hq_hq = len(round_prod[(round_prod['advertised_quality'] == 'HQ') & (round_prod['true_quality'] == 'HQ')])
                        hq_lq = len(round_prod[(round_prod['advertised_quality'] == 'HQ') & (round_prod['true_quality'] == 'LQ')])
                        
                        all_rounds_data.append({
                            'run_id': run_id,
                            'round': round_num,
                            'lq_lq': lq_lq,  # LQ advertised, LQ true
                            'lq_hq': lq_hq,  # LQ advertised, HQ true
                            'hq_hq': hq_hq,  # HQ advertised, HQ true
                            'hq_lq': hq_lq,  # HQ advertised, LQ true (dishonest)
                        })
            except Exception as e:
                print(f"Warning: Could not load product quality data from {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _load_transaction_quality_data(self, exp_id: str) -> pd.DataFrame:
        """Load transaction quality data by round (only successful transactions)"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # First, check if there are any transactions
                tx_count = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions", conn)['count'].iloc[0]
                
                # Load transactions with product quality information
                # Use LEFT JOIN to ensure we capture all transactions, even if product data is missing
                transactions = pd.read_sql_query(
                    "SELECT t.round_number, p.advertised_quality, p.true_quality "
                    "FROM transactions t LEFT JOIN product p ON t.product_id = p.product_id",
                    conn
                )
                
                # Debug: print transaction count info
                if tx_count > 0 and transactions.empty:
                    print(f"Warning: {db_file} has {tx_count} transactions but JOIN returned empty")
                elif tx_count > 0:
                    matched_count = len(transactions[transactions['advertised_quality'].notna()])
                    if matched_count < tx_count:
                        print(f"Warning: {db_file} has {tx_count} transactions but only {matched_count} matched with products")
                
                conn.close()
                
                if not transactions.empty:
                    # Drop rows where product information is missing (NULL from LEFT JOIN)
                    initial_count = len(transactions)
                    transactions = transactions.dropna(subset=['advertised_quality', 'true_quality'])
                    
                    if transactions.empty:
                        print(f"Warning: {db_file} has {initial_count} transaction rows but no valid product quality data after filtering NULLs")
                        continue
                    
                    # Ensure quality values are strings and strip whitespace
                    transactions['advertised_quality'] = transactions['advertised_quality'].astype(str).str.strip()
                    transactions['true_quality'] = transactions['true_quality'].astype(str).str.strip()
                    
                    # Filter out 'nan' strings that might result from conversion
                    transactions = transactions[
                        (transactions['advertised_quality'] != 'nan') & 
                        (transactions['true_quality'] != 'nan')
                    ]
                    
                    # Filter valid quality values
                    valid_quality_mask = (
                        (transactions['advertised_quality'].isin(['HQ', 'LQ'])) &
                        (transactions['true_quality'].isin(['HQ', 'LQ']))
                    )
                    transactions = transactions[valid_quality_mask]
                    
                    if transactions.empty:
                        print(f"Warning: {db_file} has transactions but no valid HQ/LQ quality values after filtering")
                        continue
                    
                    # Aggregate by round
                    all_round_numbers = sorted(transactions['round_number'].dropna().unique())
                    for round_num in all_round_numbers:
                        round_num = int(round_num)
                        round_tx = transactions[transactions['round_number'] == round_num]
                        
                        # Count by four product types: (advertised, true)
                        lq_lq = len(round_tx[(round_tx['advertised_quality'] == 'LQ') & (round_tx['true_quality'] == 'LQ')])
                        lq_hq = len(round_tx[(round_tx['advertised_quality'] == 'LQ') & (round_tx['true_quality'] == 'HQ')])
                        hq_hq = len(round_tx[(round_tx['advertised_quality'] == 'HQ') & (round_tx['true_quality'] == 'HQ')])
                        hq_lq = len(round_tx[(round_tx['advertised_quality'] == 'HQ') & (round_tx['true_quality'] == 'LQ')])
                        
                        all_rounds_data.append({
                            'run_id': run_id,
                            'round': round_num,
                            'lq_lq': lq_lq,  # LQ advertised, LQ true
                            'lq_hq': lq_hq,  # LQ advertised, HQ true
                            'hq_hq': hq_hq,  # HQ advertised, HQ true
                            'hq_lq': hq_lq,  # HQ advertised, LQ true (dishonest)
                        })
            except Exception as e:
                print(f"Warning: Could not load transaction quality data from {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _get_errorbar_for_rounds(self, rounds, std_dict_or_array, last_round=10):
        """Create error bar array that only shows error for the last round
        Args:
            rounds: List of round numbers (sorted)
            std_dict_or_array: dict mapping round to std value, or array aligned with rounds
        """
        # If it's a dict, extract values in rounds order
        if isinstance(std_dict_or_array, dict):
            std_values = np.array([std_dict_or_array.get(r, 0) for r in rounds])
        else:
            # It's already an array, assume it's aligned with rounds
            std_values = np.array(std_dict_or_array)
        
        yerr = np.zeros(len(rounds))
        if last_round in rounds:
            last_idx = list(rounds).index(last_round)
            if last_idx < len(std_values):
                yerr[last_idx] = std_values[last_idx]
        return yerr
    
    def plot_product_quality_evolution(self):
        """5. Product Quality Evolution Over Rounds
        2x2 layout:
        - Row 0: Number of Products (Col 0: Reputation-Only, Col 1: Reputation+Warrant)
        - Row 1: Number of Transaction Products (Col 0: Reputation-Only, Col 1: Reputation+Warrant)
        Each subplot shows 4 product types: LQ-LQ, LQ-HQ, HQ-HQ, HQ-LQ
        """
        r_quality = self._load_product_quality_data(self.r_exp_id)
        rw_quality = self._load_product_quality_data(self.rw_exp_id)
        r_tx_quality = self._load_transaction_quality_data(self.r_exp_id)
        rw_tx_quality = self._load_transaction_quality_data(self.rw_exp_id)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Define colors and markers for 4 product types
        type_colors = {
            'lq_lq': '#9467bd',    # Purple (LQ advertised, LQ true)
            'lq_hq': '#ff7f0e',    # Orange (LQ advertised, HQ true)
            'hq_hq': '#2ca02c',    # Green (HQ advertised, HQ true)
            'hq_lq': '#d62728',    # Red (HQ advertised, LQ true - dishonest)
        }
        type_labels = {
            'lq_lq': 'LQ-LQ',
            'lq_hq': 'LQ-HQ',
            'hq_hq': 'HQ-HQ',
            'hq_lq': 'HQ-LQ',
        }
        type_markers = {
            'lq_lq': 'o',
            'lq_hq': 's',
            'hq_hq': '^',
            'hq_lq': 'v',
        }
        
        # Get all rounds
        all_rounds = set()
        if not r_quality.empty:
            all_rounds.update(r_quality['round'].unique())
        if not rw_quality.empty:
            all_rounds.update(rw_quality['round'].unique())
        if not r_tx_quality.empty:
            all_rounds.update(r_tx_quality['round'].unique())
        if not rw_tx_quality.empty:
            all_rounds.update(rw_tx_quality['round'].unique())
        rounds = sorted(all_rounds) if all_rounds else []
        
        # Row 0, Col 0: Reputation-Only, Number of Products
        if not r_quality.empty:
            for ptype in ['lq_lq', 'lq_hq', 'hq_hq', 'hq_lq']:
                agg = r_quality.groupby('round')[ptype].agg(['mean', 'std']).reset_index()
                mean_dict = dict(zip(agg['round'], agg['mean']))
                std_dict = dict(zip(agg['round'], agg['std']))
                mean_aligned = [mean_dict.get(r, 0) for r in rounds]
                yerr = self._get_errorbar_for_rounds(rounds, std_dict)
                
                axes[0, 0].errorbar(rounds, mean_aligned, yerr=yerr,
                                   fmt=f'{type_markers[ptype]}-', label=type_labels[ptype],
                                   color=type_colors[ptype], linewidth=2, markersize=6,
                                   capsize=3, alpha=0.6)
        
        axes[0, 0].set_xlabel('Round', fontweight='bold')
        axes[0, 0].set_ylabel('Number of Products', fontweight='bold')
        axes[0, 0].set_title('Reputation-Only: Number of Products', fontweight='bold')
        axes[0, 0].legend(frameon=True, fancybox=True, shadow=True, loc='best')
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        if rounds:
            axes[0, 0].set_xticks(rounds)
        
        # Row 0, Col 1: Reputation+Warrant, Number of Products
        if not rw_quality.empty:
            for ptype in ['lq_lq', 'lq_hq', 'hq_hq', 'hq_lq']:
                agg = rw_quality.groupby('round')[ptype].agg(['mean', 'std']).reset_index()
                mean_dict = dict(zip(agg['round'], agg['mean']))
                std_dict = dict(zip(agg['round'], agg['std']))
                mean_aligned = [mean_dict.get(r, 0) for r in rounds]
                yerr = self._get_errorbar_for_rounds(rounds, std_dict)
                
                axes[0, 1].errorbar(rounds, mean_aligned, yerr=yerr,
                                   fmt=f'{type_markers[ptype]}-', label=type_labels[ptype],
                                   color=type_colors[ptype], linewidth=2, markersize=6,
                                   capsize=3, alpha=0.6)
        
        axes[0, 1].set_xlabel('Round', fontweight='bold')
        axes[0, 1].set_ylabel('Number of Products', fontweight='bold')
        axes[0, 1].set_title('Reputation+Warrant: Number of Products', fontweight='bold')
        axes[0, 1].legend(frameon=True, fancybox=True, shadow=True, loc='best')
        axes[0, 1].grid(True, alpha=0.3, linestyle='--')
        if rounds:
            axes[0, 1].set_xticks(rounds)
        
        # Row 1, Col 0: Reputation-Only, Number of Transaction Products
        if not r_tx_quality.empty:
            for ptype in ['lq_lq', 'lq_hq', 'hq_hq', 'hq_lq']:
                agg = r_tx_quality.groupby('round')[ptype].agg(['mean', 'std']).reset_index()
                mean_dict = dict(zip(agg['round'], agg['mean']))
                std_dict = dict(zip(agg['round'], agg['std']))
                mean_aligned = [mean_dict.get(r, 0) for r in rounds]
                yerr = self._get_errorbar_for_rounds(rounds, std_dict)
                
                axes[1, 0].errorbar(rounds, mean_aligned, yerr=yerr,
                                   fmt=f'{type_markers[ptype]}-', label=type_labels[ptype],
                                   color=type_colors[ptype], linewidth=2, markersize=6,
                                   capsize=3, alpha=0.6)
        
        axes[1, 0].set_xlabel('Round', fontweight='bold')
        axes[1, 0].set_ylabel('Number of Transaction Products', fontweight='bold')
        axes[1, 0].set_title('Reputation-Only: Number of Transaction Products', fontweight='bold')
        axes[1, 0].legend(frameon=True, fancybox=True, shadow=True, loc='best')
        axes[1, 0].grid(True, alpha=0.3, linestyle='--')
        if rounds:
            axes[1, 0].set_xticks(rounds)
        
        # Row 1, Col 1: Reputation+Warrant, Number of Transaction Products
        if not rw_tx_quality.empty:
            for ptype in ['lq_lq', 'lq_hq', 'hq_hq', 'hq_lq']:
                agg = rw_tx_quality.groupby('round')[ptype].agg(['mean', 'std']).reset_index()
                mean_dict = dict(zip(agg['round'], agg['mean']))
                std_dict = dict(zip(agg['round'], agg['std']))
                mean_aligned = [mean_dict.get(r, 0) for r in rounds]
                yerr = self._get_errorbar_for_rounds(rounds, std_dict)
                
                axes[1, 1].errorbar(rounds, mean_aligned, yerr=yerr,
                                   fmt=f'{type_markers[ptype]}-', label=type_labels[ptype],
                                   color=type_colors[ptype], linewidth=2, markersize=6,
                                   capsize=3, alpha=0.6)
        
        axes[1, 1].set_xlabel('Round', fontweight='bold')
        axes[1, 1].set_ylabel('Number of Transaction Products', fontweight='bold')
        axes[1, 1].set_title('Reputation+Warrant: Number of Transaction Products', fontweight='bold')
        axes[1, 1].legend(frameon=True, fancybox=True, shadow=True, loc='best')
        axes[1, 1].grid(True, alpha=0.3, linestyle='--')
        if rounds:
            axes[1, 1].set_xticks(rounds)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '5_product_quality_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 5_product_quality_evolution.png")
    
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
                    # Handle potential NULL values by converting to string first, then handling 'None'/'nan'
                    transactions['advertised_quality'] = transactions['advertised_quality'].astype(str).str.strip()
                    transactions['true_quality'] = transactions['true_quality'].astype(str).str.strip()
                    
                    # Filter out any invalid quality values (None, nan, empty strings)
                    # These should not be considered in dishonest/honest classification
                    valid_quality_mask = (
                        (transactions['advertised_quality'].isin(['HQ', 'LQ'])) &
                        (transactions['true_quality'].isin(['HQ', 'LQ']))
                    )
                    
                    # Identify dishonest transactions: advertised HQ but delivered LQ
                    # Only consider transactions with valid quality values
                    dishonest_mask = (
                        valid_quality_mask &
                        (transactions['advertised_quality'] == 'HQ') & 
                        (transactions['true_quality'] == 'LQ')
                    )
                    
                    # Honest transactions: all valid transactions that are not dishonest
                    honest_mask = valid_quality_mask & ~dishonest_mask
                    
                    # Calculate profits (only for valid transactions)
                    dishonest_profit = transactions[dishonest_mask]['seller_profit'].fillna(0).sum()
                    honest_profit = transactions[honest_mask]['seller_profit'].fillna(0).sum()
                    total_profit = honest_profit + dishonest_profit
                    
                    # Calculate utilities (all transactions, including invalid ones)
                    total_utility = transactions['buyer_utility'].fillna(0).sum()
                    
                    # Count transactions
                    dishonest_count = len(transactions[dishonest_mask])
                    honest_count = len(transactions[honest_mask])
                    total_count = len(transactions)
                    
                    # Count deceptions (all products, not just transactions)
                    # Ensure quality values are strings
                    if not products.empty:
                        products['advertised_quality'] = products['advertised_quality'].astype(str).str.strip()
                        products['true_quality'] = products['true_quality'].astype(str).str.strip()
                        # Filter valid quality values
                        valid_product_mask = (
                            (products['advertised_quality'].isin(['HQ', 'LQ'])) &
                            (products['true_quality'].isin(['HQ', 'LQ']))
                        )
                        deception_count = len(products[
                            valid_product_mask &
                            (products['advertised_quality'] == 'HQ') & 
                            (products['true_quality'] == 'LQ')
                        ])
                    else:
                        deception_count = 0
                    
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
        """6. Total Market Metrics & Honest vs Dishonest Analysis (Combined)"""
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
        plt.savefig(self.output_dir / '6_total_market_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 6_total_market_metrics.png")
    
    
    def generate_all(self):
        """Generate all visualizations"""
        print(f"Generating RQ2 visualizations...")
        print(f"Output directory: {self.output_dir}")
        print()
        
        self.plot_price_evolution()
        self.plot_seller_profit()
        self.plot_buyer_utility()
        self.plot_reputation()
        self.plot_product_quality_evolution()
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
    
    def _generate_markdown_table_multi_level(self, headers_row1: List[str], headers_row2: List[str],
                                            rows: List[List[str]], caption: str = "") -> str:
        """Generate markdown table with multi-level headers (two header rows)"""
        lines = []
        
        if caption:
            lines.append(f"**{caption}**\n")
        
        # First header row
        lines.append("| " + " | ".join(headers_row1) + " |")
        # Second header row
        lines.append("| " + " | ".join(headers_row2) + " |")
        # Separator
        lines.append("|" + "|".join(["---" for _ in headers_row1]) + "|")
        
        # Data rows
        for row in rows:
            lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(lines)
    
    def _generate_latex_table_multi_level(self, headers_row1: List[str], headers_row2: List[str],
                                        rows: List[List[str]], caption: str = "", label: str = "") -> str:
        """Generate LaTeX table with multi-level headers (using \multicolumn)"""
        lines = []
        lines.append("```latex")
        lines.append("\\begin{table}[htbp]")
        lines.append("\\centering")
        if caption:
            lines.append(f"\\caption{{{caption}}}")
        if label:
            lines.append(f"\\label{{{label}}}")
        
        # Count columns (excluding first column which is Market Type)
        num_cols = len(headers_row1)
        lines.append("\\begin{tabular}{" + "c" * num_cols + "}")
        lines.append("\\toprule")
        
        # First header row with \multicolumn for quality types
        header1_parts = []
        header1_parts.append(headers_row1[0])  # Market Type
        # Group HQ-HQ columns
        header1_parts.append("\\multicolumn{2}{c}{HQ-HQ}")
        # Group LQ-LQ columns
        header1_parts.append("\\multicolumn{2}{c}{LQ-LQ}")
        # Group HQ-LQ columns
        header1_parts.append("\\multicolumn{2}{c}{HQ-LQ}")
        lines.append(" & ".join(header1_parts) + " \\\\")
        lines.append("\\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(lr){6-7}")
        
        # Second header row
        lines.append(" & ".join(headers_row2) + " \\\\")
        lines.append("\\midrule")
        
        # Data rows
        for row in rows:
            lines.append(" & ".join(row) + " \\\\")
        
        lines.append("\\bottomrule")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")
        lines.append("```")
        
        return "\n".join(lines)
    
    def _generate_latex_table_multi_level_gini(self, headers_row1: List[str], headers_row2: List[str],
                                        rows: List[List[str]], caption: str = "", label: str = "") -> str:
        """Generate LaTeX table with multi-level headers for Gini coefficient table"""
        lines = []
        lines.append("```latex")
        lines.append("\\begin{table}[htbp]")
        lines.append("\\centering")
        if caption:
            lines.append(f"\\caption{{{caption}}}")
        if label:
            lines.append(f"\\label{{{label}}}")
        
        # Count columns
        num_cols = len(headers_row1)
        lines.append("\\begin{tabular}{" + "c" * num_cols + "}")
        lines.append("\\toprule")
        
        # First header row with \multicolumn for grouped columns
        header1_parts = []
        header1_parts.append(headers_row1[0])  # Market Type
        header1_parts.append(headers_row1[1])  # Transaction Count
        # Group Profit columns (Seller, Buyer)
        header1_parts.append("\\multicolumn{2}{c}{Profit}")
        # Group Profit margin columns (Seller, Buyer)
        header1_parts.append("\\multicolumn{2}{c}{Profit margin}")
        # Group Gini Coefficient columns (Seller, Buyer)
        header1_parts.append("\\multicolumn{2}{c}{Gini Coefficient}")
        lines.append(" & ".join(header1_parts) + " \\\\")
        lines.append("\\cmidrule(lr){3-4} \\cmidrule(lr){5-6} \\cmidrule(lr){7-8}")
        
        # Second header row
        lines.append(" & ".join(headers_row2) + " \\\\")
        lines.append("\\midrule")
        
        # Data rows
        for row in rows:
            lines.append(" & ".join(row) + " \\\\")
        
        lines.append("\\bottomrule")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")
        lines.append("```")
        
        return "\n".join(lines)
    
    def _get_model_name(self, exp_id: str) -> str:
        """Extract model name from experiment configuration"""
        config = self._load_experiment_config(exp_id)
        if not config:
            # Try to get from config.json or experiment_config.json
            config_file = f"experiments/{exp_id}/config.json"
            if not os.path.exists(config_file):
                config_file = f"experiments/{exp_id}/experiment_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
        
        # Try to get model name from config
        model_name = None
        if 'MODEL_TYPE' in config:
            model_name = config['MODEL_TYPE']
        elif 'model_type' in config:
            model_name = config['model_type']
        elif 'MODEL_PLATFORM' in config and 'MODEL_TYPE' in config:
            model_name = f"{config.get('MODEL_PLATFORM', 'unknown')}/{config.get('MODEL_TYPE', 'unknown')}"
        elif 'model_platform' in config and 'model_type' in config:
            model_name = f"{config.get('model_platform', 'unknown')}/{config.get('model_type', 'unknown')}"
        
        # Fallback to default if not found
        if not model_name:
            model_name = SimulationConfig.MODEL_TYPE if hasattr(SimulationConfig, 'MODEL_TYPE') else "Unknown"
        
        return model_name
    
    def generate_summary_statistics_table(self):
        """Generate Summary Statistics Table"""
        r_exp_dir = Path(f"experiments/{self.r_exp_id}")
        rw_exp_dir = Path(f"experiments/{self.rw_exp_id}")
        
        r_data = self._prepare_cross_run_data(self.r_exp_id, r_exp_dir)
        rw_data = self._prepare_cross_run_data(self.rw_exp_id, rw_exp_dir)
        
        if not r_data['run_ids'] or not rw_data['run_ids']:
            return
        
        # Get model name (use the same for both experiments, or get from first available)
        model_name = self._get_model_name(self.r_exp_id)
        if not model_name or model_name == "Unknown":
            model_name = self._get_model_name(self.rw_exp_id)
        
        # Calculate statistics for each market type
        # Reputation-Only metrics
        r_utils = r_data['buyer_utilities']
        r_profits = r_data['seller_profits']
        r_tx = r_data['transaction_counts']
        r_deceptions = r_data['deceptions']
        r_efficiency = [u + p for u, p in zip(r_utils, r_profits)]
        
        # Reputation+Warrant metrics
        rw_utils = rw_data['buyer_utilities']
        rw_profits = rw_data['seller_profits']
        rw_tx = rw_data['transaction_counts']
        rw_deceptions = rw_data['deceptions']
        rw_efficiency = [u + p for u, p in zip(rw_utils, rw_profits)]
        
        # Prepare table data: Each row is a market type
        headers = ['Model Name', 'Market Type', 'Buyer Utility (Mean ± Std)', 
                  'Seller Profit (Mean ± Std)', 'Transactions (Mean ± Std)',
                  'Deception Rate (Mean ± Std)', 'Market Efficiency (Mean ± Std)']
        
        rows = []
        
        # Row 1: Reputation-Only
        rows.append([
            model_name,
            'Reputation-Only',
            f"{self._format_number(np.mean(r_utils), 1)} ± {self._format_number(np.std(r_utils), 1)}",
            f"{self._format_number(np.mean(r_profits), 1)} ± {self._format_number(np.std(r_profits), 1)}",
            f"{self._format_number(np.mean(r_tx), 1)} ± {self._format_number(np.std(r_tx), 1)}",
            f"{self._format_number(np.mean(r_deceptions), 1)} ± {self._format_number(np.std(r_deceptions), 1)}",
            f"{self._format_number(np.mean(r_efficiency), 1)} ± {self._format_number(np.std(r_efficiency), 1)}"
        ])
        
        # Row 2: Reputation+Warrant
        rows.append([
            model_name,
            'Reputation+Warrant',
            f"{self._format_number(np.mean(rw_utils), 1)} ± {self._format_number(np.std(rw_utils), 1)}",
            f"{self._format_number(np.mean(rw_profits), 1)} ± {self._format_number(np.std(rw_profits), 1)}",
            f"{self._format_number(np.mean(rw_tx), 1)} ± {self._format_number(np.std(rw_tx), 1)}",
            f"{self._format_number(np.mean(rw_deceptions), 1)} ± {self._format_number(np.std(rw_deceptions), 1)}",
            f"{self._format_number(np.mean(rw_efficiency), 1)} ± {self._format_number(np.std(rw_efficiency), 1)}"
        ])
        
        # Generate markdown and LaTeX tables
        md_table = self._generate_markdown_table(headers, rows, 
                                                 "Summary Statistics Comparison")
        latex_table = self._generate_latex_table(headers, rows,
                                                "Summary Statistics Comparison",
                                                "tab:rq2_summary_stats")
        
        # Save to file
        table_file = self.table_dir / "rq2_summary_statistics.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print("✓ Generated: rq2_summary_statistics.md")
        
        # Table 2: Summary Statistics with Gini Coefficient (restructured)
        # Calculate Gini coefficients by run, then take mean (more statistically sound)
        r_seller_gini_mean, r_seller_gini_std = self._calculate_gini_by_run(self.r_exp_id, 'seller_profit')
        r_buyer_gini_mean, r_buyer_gini_std = self._calculate_gini_by_run(self.r_exp_id, 'buyer_utility')
        rw_seller_gini_mean, rw_seller_gini_std = self._calculate_gini_by_run(self.rw_exp_id, 'seller_profit')
        rw_buyer_gini_mean, rw_buyer_gini_std = self._calculate_gini_by_run(self.rw_exp_id, 'buyer_utility')
        
        # Calculate profit margins for sellers and buyers
        # For sellers: profit margin = profit / revenue (estimated from price)
        # For buyers: profit margin = utility / (utility + price) or utility / price
        r_seller_margins = []
        r_buyer_margins = []
        rw_seller_margins = []
        rw_buyer_margins = []
        
        for db_file in sorted(r_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Load transactions with price data
                tx_data = pd.read_sql_query(
                    "SELECT t.seller_profit, t.buyer_utility, p.price "
                    "FROM transactions t JOIN product p ON t.product_id = p.product_id "
                    "WHERE t.seller_profit IS NOT NULL AND p.price IS NOT NULL",
                    conn
                )
                conn.close()
                
                if not tx_data.empty:
                    # Seller profit margin: profit / (profit + estimated_cost)
                    # Since we don't have cost directly, use: margin = profit / price (simplified)
                    # Or: margin = profit / (profit + price) if we assume cost ≈ price - profit
                    seller_profits = tx_data['seller_profit'].values
                    prices = tx_data['price'].values
                    # Use a more accurate calculation: margin = profit / price (assuming price represents revenue)
                    # But this might overestimate margin. Better: margin = profit / (price) where price is revenue
                    # For simplicity, use: margin = profit / price (treating price as revenue per transaction)
                    valid_mask = prices > 0
                    if np.sum(valid_mask) > 0:
                        margins = seller_profits[valid_mask] / prices[valid_mask]
                        r_seller_margins.extend(margins.tolist())
                    
                    # Buyer profit margin: utility / price (treating as efficiency metric)
                    buyer_utils = tx_data['buyer_utility'].values
                    valid_mask = prices > 0
                    if np.sum(valid_mask) > 0:
                        margins = buyer_utils[valid_mask] / prices[valid_mask]
                        r_buyer_margins.extend(margins.tolist())
            except Exception as e:
                print(f"Warning: Could not calculate profit margins from {db_file}: {e}")
        
        for db_file in sorted(rw_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                tx_data = pd.read_sql_query(
                    "SELECT t.seller_profit, t.buyer_utility, p.price "
                    "FROM transactions t JOIN product p ON t.product_id = p.product_id "
                    "WHERE t.seller_profit IS NOT NULL AND p.price IS NOT NULL",
                    conn
                )
                conn.close()
                
                if not tx_data.empty:
                    seller_profits = tx_data['seller_profit'].values
                    prices = tx_data['price'].values
                    valid_mask = prices > 0
                    if np.sum(valid_mask) > 0:
                        margins = seller_profits[valid_mask] / prices[valid_mask]
                        rw_seller_margins.extend(margins.tolist())
                    
                    buyer_utils = tx_data['buyer_utility'].values
                    valid_mask = prices > 0
                    if np.sum(valid_mask) > 0:
                        margins = buyer_utils[valid_mask] / prices[valid_mask]
                        rw_buyer_margins.extend(margins.tolist())
            except Exception as e:
                print(f"Warning: Could not calculate profit margins from {db_file}: {e}")
        
        # New table structure: Market Type | Transaction Count | Profit (Seller) | Profit (Buyer) | 
        #                      Profit margin (Seller) | Profit margin (Buyer) | Gini Coefficient (Seller) | Gini Coefficient (Buyer)
        headers2_row1 = ['Market Type', 'Transaction Count', 'Profit', 'Profit', 
                        'Profit margin', 'Profit margin', 'Gini Coefficient', 'Gini Coefficient']
        headers2_row2 = ['', '', 'Seller', 'Buyer', 'Seller', 'Buyer', 'Seller', 'Buyer']
        rows2 = []
        
        # Helper function to format Mean±Std
        def format_mean_std(values):
            if len(values) == 0:
                return "N/A"
            mean = np.mean(values) if len(values) > 0 else 0.0
            std = np.std(values) if len(values) > 1 else 0.0
            return f"{self._format_number(mean, 1)}±{self._format_number(std, 1)}"
        
        # Row 1: Reputation-Only
        rows2.append([
            'Reputation-Only',
            format_mean_std(r_tx),
            format_mean_std(r_profits),
            format_mean_std(r_utils),
            format_mean_std(r_seller_margins) if len(r_seller_margins) > 0 else "N/A",
            format_mean_std(r_buyer_margins) if len(r_buyer_margins) > 0 else "N/A",
            f"{self._format_number(r_seller_gini_mean, 3)}",
            f"{self._format_number(r_buyer_gini_mean, 3)}"
        ])
        
        # Row 2: Reputation+Warrant
        rows2.append([
            'Reputation+Warrant',
            format_mean_std(rw_tx),
            format_mean_std(rw_profits),
            format_mean_std(rw_utils),
            format_mean_std(rw_seller_margins) if len(rw_seller_margins) > 0 else "N/A",
            format_mean_std(rw_buyer_margins) if len(rw_buyer_margins) > 0 else "N/A",
            f"{self._format_number(rw_seller_gini_mean, 3)}",
            f"{self._format_number(rw_buyer_gini_mean, 3)}"
        ])
        
        # Generate markdown and LaTeX tables with multi-level headers
        md_table2 = self._generate_markdown_table_multi_level(headers2_row1, headers2_row2, rows2,
                                                  "Summary Statistics with Gini Coefficient")
        latex_table2 = self._generate_latex_table_multi_level_gini(headers2_row1, headers2_row2, rows2,
                                                "Summary Statistics with Gini Coefficient",
                                                "tab:rq2_summary_stats")
        
        # Append to the same file
        with open(table_file, 'a', encoding='utf-8') as f:
            f.write("\n\n")
            f.write(md_table2)
            f.write("\n\n")
            f.write(latex_table2)
        
        print("✓ Updated: rq2_summary_statistics.md (added Gini coefficient table)")
    
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
        table_file = self.table_dir / "rq2_round_comparison.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print("✓ Generated: rq2_round_comparison.md")
    
    def generate_profit_utility_by_round_table(self):
        """Generate Profit and Utility Comparison Table by Round"""
        r_rounds = self._load_round_data_from_db(self.r_exp_id)
        rw_rounds = self._load_round_data_from_db(self.rw_exp_id)
        r_profit_by_type = self._load_round_profit_by_type(self.r_exp_id)
        rw_profit_by_type = self._load_round_profit_by_type(self.rw_exp_id)
        
        if r_rounds.empty or rw_rounds.empty:
            return
        
        # Aggregate by round
        r_agg = r_rounds.groupby('round').agg({
            'seller_profit': ['mean', 'std'],
            'buyer_utility': ['mean', 'std']
        }).reset_index()
        
        rw_agg = rw_rounds.groupby('round').agg({
            'seller_profit': ['mean', 'std'],
            'buyer_utility': ['mean', 'std']
        }).reset_index()
        
        # Aggregate profit by type
        r_honest_agg = r_profit_by_type.groupby('round')['honest_profit'].agg(['mean', 'std']).reset_index() if not r_profit_by_type.empty else pd.DataFrame()
        r_dishonest_agg = r_profit_by_type.groupby('round')['dishonest_profit'].agg(['mean', 'std']).reset_index() if not r_profit_by_type.empty else pd.DataFrame()
        rw_honest_agg = rw_profit_by_type.groupby('round')['honest_profit'].agg(['mean', 'std']).reset_index() if not rw_profit_by_type.empty else pd.DataFrame()
        rw_dishonest_agg = rw_profit_by_type.groupby('round')['dishonest_profit'].agg(['mean', 'std']).reset_index() if not rw_profit_by_type.empty else pd.DataFrame()
        
        # Get all rounds
        all_rounds = sorted(set(r_agg['round'].unique()) | set(rw_agg['round'].unique()))
        
        headers = ['Round', 'R-Total Profit', 'R-Honest Profit', 'R-Dishonest Profit', 'R-Buyer Utility',
                  'RW-Total Profit', 'RW-Honest Profit', 'RW-Dishonest Profit', 'RW-Buyer Utility']
        rows = []
        
        for round_num in all_rounds:
            r_row = r_agg[r_agg['round'] == round_num]
            rw_row = rw_agg[rw_agg['round'] == round_num]
            
            r_total = f"{self._format_number(r_row[('seller_profit', 'mean')].values[0])}" if not r_row.empty else "N/A"
            rw_total = f"{self._format_number(rw_row[('seller_profit', 'mean')].values[0])}" if not rw_row.empty else "N/A"
            
            r_honest = "N/A"
            if not r_honest_agg.empty:
                r_honest_row = r_honest_agg[r_honest_agg['round'] == round_num]
                if not r_honest_row.empty:
                    r_honest = f"{self._format_number(r_honest_row['mean'].values[0])}"
            
            r_dishonest = "N/A"
            if not r_dishonest_agg.empty:
                r_dishonest_row = r_dishonest_agg[r_dishonest_agg['round'] == round_num]
                if not r_dishonest_row.empty:
                    r_dishonest = f"{self._format_number(r_dishonest_row['mean'].values[0])}"
            
            rw_honest = "N/A"
            if not rw_honest_agg.empty:
                rw_honest_row = rw_honest_agg[rw_honest_agg['round'] == round_num]
                if not rw_honest_row.empty:
                    rw_honest = f"{self._format_number(rw_honest_row['mean'].values[0])}"
            
            rw_dishonest = "N/A"
            if not rw_dishonest_agg.empty:
                rw_dishonest_row = rw_dishonest_agg[rw_dishonest_agg['round'] == round_num]
                if not rw_dishonest_row.empty:
                    rw_dishonest = f"{self._format_number(rw_dishonest_row['mean'].values[0])}"
            
            r_util = f"{self._format_number(r_row[('buyer_utility', 'mean')].values[0])}" if not r_row.empty else "N/A"
            rw_util = f"{self._format_number(rw_row[('buyer_utility', 'mean')].values[0])}" if not rw_row.empty else "N/A"
            
            rows.append([str(round_num), r_total, r_honest, r_dishonest, r_util,
                        rw_total, rw_honest, rw_dishonest, rw_util])
        
        # Add summary row (average across all rounds)
        r_total_mean = np.mean([float(r[1]) if r[1] != "N/A" else 0 for r in rows])
        r_honest_mean = np.mean([float(r[2]) if r[2] != "N/A" else 0 for r in rows if r[2] != "N/A"])
        r_dishonest_mean = np.mean([float(r[3]) if r[3] != "N/A" else 0 for r in rows if r[3] != "N/A"])
        r_util_mean = np.mean([float(r[4]) if r[4] != "N/A" else 0 for r in rows])
        rw_total_mean = np.mean([float(r[5]) if r[5] != "N/A" else 0 for r in rows])
        rw_honest_mean = np.mean([float(r[6]) if r[6] != "N/A" else 0 for r in rows if r[6] != "N/A"])
        rw_dishonest_mean = np.mean([float(r[7]) if r[7] != "N/A" else 0 for r in rows if r[7] != "N/A"])
        rw_util_mean = np.mean([float(r[8]) if r[8] != "N/A" else 0 for r in rows])
        
        rows.append(['Average', 
                    f"{self._format_number(r_total_mean)}",
                    f"{self._format_number(r_honest_mean)}" if r_honest_mean != 0 else "N/A",
                    f"{self._format_number(r_dishonest_mean)}" if r_dishonest_mean != 0 else "N/A",
                    f"{self._format_number(r_util_mean)}",
                    f"{self._format_number(rw_total_mean)}",
                    f"{self._format_number(rw_honest_mean)}" if rw_honest_mean != 0 else "N/A",
                    f"{self._format_number(rw_dishonest_mean)}" if rw_dishonest_mean != 0 else "N/A",
                    f"{self._format_number(rw_util_mean)}"])
        
        # Add total row (sum across all rounds)
        r_total_sum = sum([float(r[1]) if r[1] != "N/A" else 0 for r in rows[:-1]])
        r_honest_sum = sum([float(r[2]) if r[2] != "N/A" else 0 for r in rows[:-1] if r[2] != "N/A"])
        r_dishonest_sum = sum([float(r[3]) if r[3] != "N/A" else 0 for r in rows[:-1] if r[3] != "N/A"])
        r_util_sum = sum([float(r[4]) if r[4] != "N/A" else 0 for r in rows[:-1]])
        rw_total_sum = sum([float(r[5]) if r[5] != "N/A" else 0 for r in rows[:-1]])
        rw_honest_sum = sum([float(r[6]) if r[6] != "N/A" else 0 for r in rows[:-1] if r[6] != "N/A"])
        rw_dishonest_sum = sum([float(r[7]) if r[7] != "N/A" else 0 for r in rows[:-1] if r[7] != "N/A"])
        rw_util_sum = sum([float(r[8]) if r[8] != "N/A" else 0 for r in rows[:-1]])
        
        rows.append(['Total',
                    f"{self._format_number(r_total_sum)}",
                    f"{self._format_number(r_honest_sum)}" if r_honest_sum != 0 else "N/A",
                    f"{self._format_number(r_dishonest_sum)}" if r_dishonest_sum != 0 else "N/A",
                    f"{self._format_number(r_util_sum)}",
                    f"{self._format_number(rw_total_sum)}",
                    f"{self._format_number(rw_honest_sum)}" if rw_honest_sum != 0 else "N/A",
                    f"{self._format_number(rw_dishonest_sum)}" if rw_dishonest_sum != 0 else "N/A",
                    f"{self._format_number(rw_util_sum)}"])
        
        # Generate markdown and LaTeX tables
        md_table = self._generate_markdown_table(headers, rows,
                                                "Profit and Utility Comparison by Round")
        latex_table = self._generate_latex_table(headers, rows,
                                                "Profit and Utility Comparison by Round",
                                                "tab:profit_utility_by_round")
        
        # Save to file
        table_file = self.table_dir / "rq2_profit_utility_by_round.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print("✓ Generated: rq2_profit_utility_by_round.md")
        
        # Table 2: Overall Profit and Utility Statistics (similar to product_quality format)
        # Calculate statistics across all rounds
        r_total_profit_all = r_rounds['seller_profit'].values
        r_honest_profit_all = r_profit_by_type['honest_profit'].values if not r_profit_by_type.empty else np.array([])
        r_dishonest_profit_all = r_profit_by_type['dishonest_profit'].values if not r_profit_by_type.empty else np.array([])
        r_buyer_utility_all = r_rounds['buyer_utility'].values
        
        rw_total_profit_all = rw_rounds['seller_profit'].values
        rw_honest_profit_all = rw_profit_by_type['honest_profit'].values if not rw_profit_by_type.empty else np.array([])
        rw_dishonest_profit_all = rw_profit_by_type['dishonest_profit'].values if not rw_profit_by_type.empty else np.array([])
        rw_buyer_utility_all = rw_rounds['buyer_utility'].values
        
        # Helper function to format Mean±Std
        def format_mean_std(values):
            if len(values) == 0:
                return "N/A"
            mean = np.mean(values) if len(values) > 0 else 0.0
            std = np.std(values) if len(values) > 1 else 0.0
            return f"{self._format_number(mean, 1)}±{self._format_number(std, 1)}"
        
        # New format: rows = market type, columns = metrics with Mean±Std format
        headers2 = ['Market Type', 'Total Profit', 'Honest Profit', 'Dishonest Profit', 'Buyer Utility']
        rows2 = []
        
        # Reputation-Only row
        rows2.append(['Reputation-Only',
                    format_mean_std(r_total_profit_all),
                    format_mean_std(r_honest_profit_all),
                    format_mean_std(r_dishonest_profit_all),
                    format_mean_std(r_buyer_utility_all)])
        
        # Reputation+Warrant row
        rows2.append(['Reputation+Warrant',
                    format_mean_std(rw_total_profit_all),
                    format_mean_std(rw_honest_profit_all),
                    format_mean_std(rw_dishonest_profit_all),
                    format_mean_std(rw_buyer_utility_all)])
        
        md_table2 = self._generate_markdown_table(headers2, rows2,
                                                  "Overall Profit and Utility Statistics (All 10 Rounds)")
        latex_table2 = self._generate_latex_table(headers2, rows2,
                                                   "Overall Profit and Utility Statistics (All 10 Rounds)",
                                                   "tab:profit_utility_overall")
        
        # Append to the same file
        table_file = self.table_dir / "rq2_profit_utility_by_round.md"
        with open(table_file, 'a', encoding='utf-8') as f:
            f.write("\n\n")
            f.write(md_table2)
            f.write("\n\n")
            f.write(latex_table2)
        
        print("✓ Updated: rq2_profit_utility_by_round.md (added overall statistics)")
    
    def _calculate_gini_coefficient(self, values):
        """Calculate Gini coefficient for a list of values
        Uses the standard formula: G = (2 * sum(i * y_i)) / (n * sum(y_i)) - (n + 1) / n
        where i is the rank (1 to n) and y_i is the sorted value in ascending order
        """
        if len(values) == 0:
            return 0.0
        
        # Convert to numpy array and remove zeros/negative values
        values = np.array([v for v in values if v > 0])
        if len(values) == 0 or np.sum(values) == 0:
            return 0.0
        
        # Sort in ascending order
        values = np.sort(values)
        n = len(values)
        
        if n == 1:
            return 0.0  # Single value means perfect equality
        
        # Gini coefficient formula: G = (2 * sum(i * y_i)) / (n * sum(y_i)) - (n + 1) / n
        # where i is the rank (1 to n) and y_i is the sorted value
        indices = np.arange(1, n + 1)
        gini = (2 * np.sum(indices * values)) / (n * np.sum(values)) - (n + 1) / n
        
        # Ensure result is in valid range [0, 1]
        gini = max(0.0, min(1.0, gini))
        
        return gini
    
    def _load_individual_seller_profits(self, exp_id: str) -> List[float]:
        """Load total profit for each seller across all rounds
        Returns a list where each element is the total profit of one seller in one run
        (each run is treated as an independent experiment)
        """
        exp_dir = Path(f"experiments/{exp_id}")
        seller_profits = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Get total profit per seller for this run
                query = """
                    SELECT seller_id, SUM(seller_profit) as total_profit
                    FROM transactions
                    GROUP BY seller_id
                """
                result = pd.read_sql_query(query, conn)
                conn.close()
                
                if not result.empty:
                    # Add each seller's total profit from this run
                    seller_profits.extend(result['total_profit'].dropna().tolist())
            except Exception as e:
                print(f"Warning: Could not load seller profits from {db_file}: {e}")
        
        return seller_profits
    
    def _calculate_gini_by_run(self, exp_id: str, metric_type: str) -> Tuple[float, float]:
        """Calculate Gini coefficient by run, then return mean and std
        Args:
            exp_id: Experiment ID
            metric_type: 'seller_profit' or 'buyer_utility'
        Returns:
            (mean_gini, std_gini)
        """
        exp_dir = Path(f"experiments/{exp_id}")
        gini_values = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                
                if metric_type == 'seller_profit':
                    query = """
                        SELECT seller_id, SUM(seller_profit) as total_value
                        FROM transactions
                        GROUP BY seller_id
                    """
                else:  # buyer_utility
                    query = """
                        SELECT buyer_id, SUM(buyer_utility) as total_value
                        FROM transactions
                        GROUP BY buyer_id
                    """
                
                result = pd.read_sql_query(query, conn)
                conn.close()
                
                if not result.empty:
                    values = result['total_value'].dropna().tolist()
                    if len(values) > 0:
                        gini = self._calculate_gini_coefficient(values)
                        gini_values.append(gini)
            except Exception as e:
                print(f"Warning: Could not calculate Gini for {db_file}: {e}")
        
        if len(gini_values) == 0:
            return (0.0, 0.0)
        
        return (np.mean(gini_values), np.std(gini_values))
    
    def _load_individual_buyer_utilities(self, exp_id: str) -> List[float]:
        """Load total utility for each buyer across all rounds"""
        exp_dir = Path(f"experiments/{exp_id}")
        buyer_utilities = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Get total utility per buyer
                query = """
                    SELECT buyer_id, SUM(buyer_utility) as total_utility
                    FROM transactions
                    GROUP BY buyer_id
                """
                result = pd.read_sql_query(query, conn)
                conn.close()
                
                if not result.empty:
                    buyer_utilities.extend(result['total_utility'].dropna().tolist())
            except Exception as e:
                print(f"Warning: Could not load buyer utilities from {db_file}: {e}")
        
        return buyer_utilities
    
    def generate_reputation_tables(self):
        """Generate reputation-related tables"""
        r_exp_dir = Path(f"experiments/{self.r_exp_id}")
        rw_exp_dir = Path(f"experiments/{self.rw_exp_id}")
        
        # Load reputation data
        r_reps = []
        rw_reps = []
        
        for db_file in sorted(r_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Try to load with public_thumbs_up/public_thumbs_down first, fallback to public_reputation_score
                try:
                    rep = pd.read_sql_query(
                        "SELECT round, seller_id, public_thumbs_up, public_thumbs_down FROM reputation_history",
                        conn
                    )
                    if not rep.empty:
                        rep['public_reputation_score'] = rep['public_thumbs_up'] - rep['public_thumbs_down']
                except:
                    # Fallback: use public_reputation_score directly
                    try:
                        rep = pd.read_sql_query(
                            "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                            conn
                        )
                    except:
                        rep = pd.DataFrame(columns=['round', 'seller_id', 'public_reputation_score'])
                r_reps.append(rep)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not load reputation data from {db_file}: {e}")
        
        for db_file in sorted(rw_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                # Try to load with public_thumbs_up/public_thumbs_down first, fallback to public_reputation_score
                try:
                    rep = pd.read_sql_query(
                        "SELECT round, seller_id, public_thumbs_up, public_thumbs_down FROM reputation_history",
                        conn
                    )
                    if not rep.empty:
                        rep['public_reputation_score'] = rep['public_thumbs_up'] - rep['public_thumbs_down']
                except:
                    # Fallback: use public_reputation_score directly
                    try:
                        rep = pd.read_sql_query(
                            "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                            conn
                        )
                    except:
                        rep = pd.DataFrame(columns=['round', 'seller_id', 'public_reputation_score'])
                rw_reps.append(rep)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not load reputation data from {db_file}: {e}")
        
        if not r_reps or not rw_reps:
            return
        
        r_all = pd.concat(r_reps)
        rw_all = pd.concat(rw_reps)
        
        # Table 1: Average reputation by round
        r_agg = r_all.groupby('round')['public_reputation_score'].agg(['mean', 'std']).reset_index()
        rw_agg = rw_all.groupby('round')['public_reputation_score'].agg(['mean', 'std']).reset_index()
        
        all_rounds = sorted(set(r_agg['round'].unique()) | set(rw_agg['round'].unique()))
        
        # Calculate delta (incremental) reputation
        r_agg_sorted = r_agg.sort_values('round')
        rw_agg_sorted = rw_agg.sort_values('round')
        
        # Calculate delta: current round - previous round
        r_delta = []
        rw_delta = []
        for i, round_num in enumerate(all_rounds):
            r_row = r_agg_sorted[r_agg_sorted['round'] == round_num]
            rw_row = rw_agg_sorted[rw_agg_sorted['round'] == round_num]
            
            if i == 0:
                # First round: delta is 0 (no previous round)
                r_delta.append(0.0)
                rw_delta.append(0.0)
            else:
                prev_round = all_rounds[i-1]
                r_prev_row = r_agg_sorted[r_agg_sorted['round'] == prev_round]
                rw_prev_row = rw_agg_sorted[rw_agg_sorted['round'] == prev_round]
                
                if not r_row.empty and not r_prev_row.empty:
                    r_delta.append(r_row['mean'].values[0] - r_prev_row['mean'].values[0])
                else:
                    r_delta.append(0.0)
                
                if not rw_row.empty and not rw_prev_row.empty:
                    rw_delta.append(rw_row['mean'].values[0] - rw_prev_row['mean'].values[0])
                else:
                    rw_delta.append(0.0)
        
        # Calculate overall statistics across all rounds
        # For Reputation Mean and Std: aggregate all round values
        r_reputation_means = []
        r_reputation_stds = []
        rw_reputation_means = []
        rw_reputation_stds = []
        
        for i, round_num in enumerate(all_rounds):
            r_row = r_agg[r_agg['round'] == round_num]
            rw_row = rw_agg[rw_agg['round'] == round_num]
            
            if not r_row.empty:
                r_reputation_means.append(r_row['mean'].values[0])
                r_reputation_stds.append(r_row['std'].values[0])
            if not rw_row.empty:
                rw_reputation_means.append(rw_row['mean'].values[0])
                rw_reputation_stds.append(rw_row['std'].values[0])
        
        # Calculate overall statistics for reputation
        r_rep_mean_overall = np.mean(r_reputation_means) if r_reputation_means else 0.0
        r_rep_std_overall = np.mean(r_reputation_stds) if r_reputation_stds else 0.0
        rw_rep_mean_overall = np.mean(rw_reputation_means) if rw_reputation_means else 0.0
        rw_rep_std_overall = np.mean(rw_reputation_stds) if rw_reputation_stds else 0.0
        
        # Calculate overall statistics for delta reputation
        r_delta_mean_overall = np.mean([d for d in r_delta if d != 0.0]) if r_delta else 0.0
        # For delta std, calculate std of delta values (excluding first round's 0)
        r_delta_std_overall = np.std([d for d in r_delta if d != 0.0]) if len([d for d in r_delta if d != 0.0]) > 1 else 0.0
        rw_delta_mean_overall = np.mean([d for d in rw_delta if d != 0.0]) if rw_delta else 0.0
        rw_delta_std_overall = np.std([d for d in rw_delta if d != 0.0]) if len([d for d in rw_delta if d != 0.0]) > 1 else 0.0
        
        # Table 1: Original format - Reputation by Round
        headers1 = ['Round', 'R-Avg Reputation', 'R-Avg Delta Reputation', 'R-Std Reputation', 
                  'RW-Avg Reputation', 'RW-Std Reputation']
        rows1 = []
        
        for i, round_num in enumerate(all_rounds):
            r_row = r_agg[r_agg['round'] == round_num]
            rw_row = rw_agg[rw_agg['round'] == round_num]
            
            r_mean = f"{self._format_number(r_row['mean'].values[0])}" if not r_row.empty else "N/A"
            r_delta_val = f"{self._format_number(r_delta[i])}" if i < len(r_delta) else "N/A"
            r_std = f"{self._format_number(r_row['std'].values[0])}" if not r_row.empty else "N/A"
            rw_mean = f"{self._format_number(rw_row['mean'].values[0])}" if not rw_row.empty else "N/A"
            rw_std = f"{self._format_number(rw_row['std'].values[0])}" if not rw_row.empty else "N/A"
            
            rows1.append([str(round_num), r_mean, r_delta_val, r_std, rw_mean, rw_std])
        
        # Add summary rows
        r_overall_mean = np.mean([float(r[1]) if r[1] != "N/A" else 0 for r in rows1])
        r_overall_delta = np.mean([float(r[2]) if r[2] != "N/A" else 0 for r in rows1])
        r_overall_std = np.mean([float(r[3]) if r[3] != "N/A" else 0 for r in rows1])
        rw_overall_mean = np.mean([float(r[4]) if r[4] != "N/A" else 0 for r in rows1])
        rw_overall_std = np.mean([float(r[5]) if r[5] != "N/A" else 0 for r in rows1])
        
        rows1.append(['Average', 
                    f"{self._format_number(r_overall_mean)}",
                    f"{self._format_number(r_overall_delta)}",
                    f"{self._format_number(r_overall_std)}",
                    f"{self._format_number(rw_overall_mean)}",
                    f"{self._format_number(rw_overall_std)}"])
        
        md_table1 = self._generate_markdown_table(headers1, rows1,
                                                "Average Reputation by Round")
        latex_table1 = self._generate_latex_table(headers1, rows1,
                                                "Average Reputation by Round",
                                                "tab:reputation_by_round")
        
        # Table 2: Advanced reputation statistics
        # Calculate comprehensive reputation metrics
        
        # Load transaction data for rating analysis
        r_transactions = []
        rw_transactions = []
        
        for db_file in sorted(r_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                tx = pd.read_sql_query(
                    "SELECT rating, round_number FROM transactions WHERE rating IS NOT NULL",
                    conn
                )
                r_transactions.append(tx)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not load transactions from {db_file}: {e}")
        
        for db_file in sorted(rw_exp_dir.glob("run_*.db")):
            try:
                conn = sqlite3.connect(db_file)
                tx = pd.read_sql_query(
                    "SELECT rating, round_number FROM transactions WHERE rating IS NOT NULL",
                    conn
                )
                rw_transactions.append(tx)
                conn.close()
            except Exception as e:
                print(f"Warning: Could not load transactions from {db_file}: {e}")
        
        r_tx_all = pd.concat(r_transactions) if r_transactions else pd.DataFrame()
        rw_tx_all = pd.concat(rw_transactions) if rw_transactions else pd.DataFrame()
        
        # Calculate reputation scores and statistics
        r_all_scores = r_all['public_reputation_score'].dropna().values
        rw_all_scores = rw_all['public_reputation_score'].dropna().values
        
        # Calculate thumbs_up and thumbs_down statistics if available
        r_thumbs_up_all = []
        r_thumbs_down_all = []
        rw_thumbs_up_all = []
        rw_thumbs_down_all = []
        
        if 'public_thumbs_up' in r_all.columns and 'public_thumbs_down' in r_all.columns:
            r_thumbs_up_all = r_all['public_thumbs_up'].dropna().values
            r_thumbs_down_all = r_all['public_thumbs_down'].dropna().values
        if 'public_thumbs_up' in rw_all.columns and 'public_thumbs_down' in rw_all.columns:
            rw_thumbs_up_all = rw_all['public_thumbs_up'].dropna().values
            rw_thumbs_down_all = rw_all['public_thumbs_down'].dropna().values
        
        # Helper function to format Mean±Std
        def format_mean_std(values):
            if len(values) == 0:
                return "N/A"
            mean = np.mean(values) if len(values) > 0 else 0.0
            std = np.std(values) if len(values) > 1 else 0.0
            return f"{self._format_number(mean, 1)}±{self._format_number(std, 1)}"
        
        # Advanced metrics calculation
        def calculate_advanced_metrics(scores, thumbs_up, thumbs_down, delta_list, transactions_df):
            """Calculate advanced reputation metrics"""
            metrics = {}
            
            if len(scores) == 0:
                return {k: "N/A" for k in ['rep_mean_std', 'rep_median', 'rep_gini', 'rep_cv', 
                                           'pos_rate', 'avg_rating', 'rating_density', 
                                           'rep_growth', 'rep_concentration']}
            
            # Basic statistics
            metrics['rep_mean_std'] = format_mean_std(scores)
            metrics['rep_median'] = f"{self._format_number(np.median(scores), 1)}"
            metrics['rep_min'] = f"{self._format_number(np.min(scores), 1)}"
            metrics['rep_max'] = f"{self._format_number(np.max(scores), 1)}"
            
            # Gini coefficient (reputation inequality)
            if len(scores) > 0 and np.sum(scores) != 0:
                metrics['rep_gini'] = f"{self._format_number(self._calculate_gini_coefficient(scores), 3)}"
            else:
                metrics['rep_gini'] = "0.000"
            
            # Coefficient of Variation (stability/volatility)
            if np.mean(scores) != 0:
                cv = np.std(scores) / np.abs(np.mean(scores))
                metrics['rep_cv'] = f"{self._format_number(cv, 3)}"
            else:
                metrics['rep_cv'] = "N/A"
            
            # Positive rate (thumbs_up / (thumbs_up + thumbs_down))
            if len(thumbs_up) > 0 and len(thumbs_down) > 0:
                total_feedback = np.sum(thumbs_up) + np.sum(thumbs_down)
                if total_feedback > 0:
                    pos_rate = np.sum(thumbs_up) / total_feedback
                    metrics['pos_rate'] = f"{self._format_number(pos_rate * 100, 1)}%"
                else:
                    metrics['pos_rate'] = "N/A"
            else:
                metrics['pos_rate'] = "N/A"
            
            # Average rating intensity (from transactions)
            if not transactions_df.empty and 'rating' in transactions_df.columns:
                ratings = transactions_df['rating'].dropna().values
                if len(ratings) > 0:
                    avg_rating = np.mean(np.abs(ratings))
                    metrics['avg_rating'] = f"{self._format_number(avg_rating, 2)}"
                else:
                    metrics['avg_rating'] = "N/A"
            else:
                metrics['avg_rating'] = "N/A"
            
            # Rating density (ratings per transaction)
            if not transactions_df.empty:
                total_tx = len(transactions_df)
                rated_tx = len(transactions_df[transactions_df['rating'].notna()])
                if total_tx > 0:
                    density = rated_tx / total_tx
                    metrics['rating_density'] = f"{self._format_number(density * 100, 1)}%"
                else:
                    metrics['rating_density'] = "N/A"
            else:
                metrics['rating_density'] = "N/A"
            
            # Reputation growth (final / initial, or average delta)
            delta_nonzero = [d for d in delta_list if d != 0.0]
            if len(delta_nonzero) > 0:
                metrics['rep_growth'] = format_mean_std(delta_nonzero)
            else:
                metrics['rep_growth'] = "N/A"
            
            # Reputation concentration (percentage of sellers above thresholds)
            if len(scores) > 0:
                total_sellers = len(scores)
                above_zero = np.sum(scores > 0) / total_sellers * 100
                above_ten = np.sum(scores > 10) / total_sellers * 100
                above_twenty = np.sum(scores > 20) / total_sellers * 100
                metrics['rep_concentration'] = f"{self._format_number(above_zero, 1)}%/{self._format_number(above_ten, 1)}%/{self._format_number(above_twenty, 1)}%"
            else:
                metrics['rep_concentration'] = "N/A"
            
            return metrics
        
        # Calculate advanced metrics for both market types
        r_metrics = calculate_advanced_metrics(
            r_all_scores, r_thumbs_up_all, r_thumbs_down_all, r_delta, r_tx_all
        )
        rw_metrics = calculate_advanced_metrics(
            rw_all_scores, rw_thumbs_up_all, rw_thumbs_down_all, rw_delta, rw_tx_all
        )
        
        # Simplified table with selected statistics
        headers2 = ['Market Type', 'Reputation', 'Reputation CV',
                    'Positive Rate', 'Reputation Growth']
        rows2 = []
        
        # Reputation-Only (R) row
        rows2.append(['Reputation-Only',
                    r_metrics['rep_mean_std'],
                    r_metrics['rep_cv'],
                    r_metrics['pos_rate'],
                    r_metrics['rep_growth']])
        
        # Reputation+Warrant (RW) row
        rows2.append(['Reputation+Warrant',
                    rw_metrics['rep_mean_std'],
                    rw_metrics['rep_cv'],
                    rw_metrics['pos_rate'],
                    rw_metrics['rep_growth']])
        
        md_table2 = self._generate_markdown_table(headers2, rows2,
                                                "Average Reputation Statistics (All 10 Rounds)")
        latex_table2 = self._generate_latex_table(headers2, rows2,
                                                "Average Reputation Statistics (All 10 Rounds)",
                                                "tab:reputation_statistics")
        
        # Save both tables to the same file
        table_file = self.table_dir / "rq2_reputation_by_round.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table1)
            f.write("\n\n")
            f.write(latex_table1)
            f.write("\n\n")
            f.write(md_table2)
            f.write("\n\n")
            f.write(latex_table2)
        
        print("✓ Generated: rq2_reputation_by_round.md")
        
        # Table 2: Individual seller reputation (final round)
        # Use first run for individual seller data
        if len(r_reps) > 0 and len(rw_reps) > 0:
            r_sample = r_reps[0]
            rw_sample = rw_reps[0]
            
            # Get final round
            final_round = max(r_sample['round'].max(), rw_sample['round'].max())
            
            r_final = r_sample[r_sample['round'] == final_round].sort_values('seller_id')
            rw_final = rw_sample[rw_sample['round'] == final_round].sort_values('seller_id')
            
            # Check if thumbs_up/thumbs_down columns exist
            has_thumbs = 'public_thumbs_up' in r_sample.columns and 'public_thumbs_down' in r_sample.columns
            
            if has_thumbs:
                headers = ['Seller ID', 'R-Final Reputation', 'R-Thumbs Up', 'R-Thumbs Down',
                          'RW-Final Reputation', 'RW-Thumbs Up', 'RW-Thumbs Down']
            else:
                headers = ['Seller ID', 'R-Final Reputation', 'RW-Final Reputation']
            rows = []
            
            all_seller_ids = sorted(set(r_final['seller_id'].unique()) | set(rw_final['seller_id'].unique()))
            
            for seller_id in all_seller_ids:
                r_seller = r_final[r_final['seller_id'] == seller_id]
                rw_seller = rw_final[rw_final['seller_id'] == seller_id]
                
                r_rep = f"{self._format_number(r_seller['public_reputation_score'].values[0])}" if not r_seller.empty and 'public_reputation_score' in r_seller.columns else "N/A"
                
                if has_thumbs:
                    r_up = f"{int(r_seller['public_thumbs_up'].values[0])}" if not r_seller.empty and 'public_thumbs_up' in r_seller.columns else "N/A"
                    r_down = f"{int(r_seller['public_thumbs_down'].values[0])}" if not r_seller.empty and 'public_thumbs_down' in r_seller.columns else "N/A"
                    rw_rep = f"{self._format_number(rw_seller['public_reputation_score'].values[0])}" if not rw_seller.empty and 'public_reputation_score' in rw_seller.columns else "N/A"
                    rw_up = f"{int(rw_seller['public_thumbs_up'].values[0])}" if not rw_seller.empty and 'public_thumbs_up' in rw_seller.columns else "N/A"
                    rw_down = f"{int(rw_seller['public_thumbs_down'].values[0])}" if not rw_seller.empty and 'public_thumbs_down' in rw_seller.columns else "N/A"
                    rows.append([str(seller_id), r_rep, r_up, r_down, rw_rep, rw_up, rw_down])
                else:
                    rw_rep = f"{self._format_number(rw_seller['public_reputation_score'].values[0])}" if not rw_seller.empty and 'public_reputation_score' in rw_seller.columns else "N/A"
                    rows.append([str(seller_id), r_rep, rw_rep])
            
            md_table = self._generate_markdown_table(headers, rows,
                                                    f"Individual Seller Reputation (Final Round {final_round})")
            latex_table = self._generate_latex_table(headers, rows,
                                                    f"Individual Seller Reputation (Final Round {final_round})",
                                                    "tab:reputation_individual")
            
            table_file = self.table_dir / "rq2_reputation_individual.md"
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(md_table)
                f.write("\n\n")
                f.write(latex_table)
            
            print("✓ Generated: rq2_reputation_individual.md")
        
        # Table 3: Rating by product quality
        r_ratings = self._load_ratings_by_quality(self.r_exp_id)
        rw_ratings = self._load_ratings_by_quality(self.rw_exp_id)
        
        if not r_ratings.empty and not rw_ratings.empty:
            r_hq_agg = r_ratings[r_ratings['true_quality'] == 'HQ'].groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
            r_lq_agg = r_ratings[r_ratings['true_quality'] == 'LQ'].groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
            rw_hq_agg = rw_ratings[rw_ratings['true_quality'] == 'HQ'].groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
            rw_lq_agg = rw_ratings[rw_ratings['true_quality'] == 'LQ'].groupby('round_number')['rating'].agg(['mean', 'std']).reset_index()
            
            all_rounds = sorted(set(r_hq_agg['round_number'].unique()) | 
                              set(r_lq_agg['round_number'].unique()) |
                              set(rw_hq_agg['round_number'].unique()) |
                              set(rw_lq_agg['round_number'].unique()))
            
            headers = ['Round', 'R-HQ Rating', 'R-LQ Rating', 'RW-HQ Rating', 'RW-LQ Rating']
            rows = []
            
            for round_num in all_rounds:
                r_hq_row = r_hq_agg[r_hq_agg['round_number'] == round_num]
                r_lq_row = r_lq_agg[r_lq_agg['round_number'] == round_num]
                rw_hq_row = rw_hq_agg[rw_hq_agg['round_number'] == round_num]
                rw_lq_row = rw_lq_agg[rw_lq_agg['round_number'] == round_num]
                
                r_hq = f"{self._format_number(r_hq_row['mean'].values[0])}" if not r_hq_row.empty else "N/A"
                r_lq = f"{self._format_number(r_lq_row['mean'].values[0])}" if not r_lq_row.empty else "N/A"
                rw_hq = f"{self._format_number(rw_hq_row['mean'].values[0])}" if not rw_hq_row.empty else "N/A"
                rw_lq = f"{self._format_number(rw_lq_row['mean'].values[0])}" if not rw_lq_row.empty else "N/A"
                
                rows.append([str(round_num), r_hq, r_lq, rw_hq, rw_lq])
            
            # Add summary rows
            r_hq_mean = np.mean([float(r[1]) if r[1] != "N/A" else 0 for r in rows])
            r_lq_mean = np.mean([float(r[2]) if r[2] != "N/A" else 0 for r in rows])
            rw_hq_mean = np.mean([float(r[3]) if r[3] != "N/A" else 0 for r in rows])
            rw_lq_mean = np.mean([float(r[4]) if r[4] != "N/A" else 0 for r in rows])
            
            rows.append(['Average',
                        f"{self._format_number(r_hq_mean)}",
                        f"{self._format_number(r_lq_mean)}",
                        f"{self._format_number(rw_hq_mean)}",
                        f"{self._format_number(rw_lq_mean)}"])
            
            md_table = self._generate_markdown_table(headers, rows,
                                                    "Product Quality Rating by Round")
            latex_table = self._generate_latex_table(headers, rows,
                                                    "Product Quality Rating by Round",
                                                    "tab:rating_by_quality")
            
            table_file = self.table_dir / "rq2_rating_by_quality.md"
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(md_table)
                f.write("\n\n")
                f.write(latex_table)
            
            print("✓ Generated: rq2_rating_by_quality.md")
    
    def generate_product_quality_tables(self):
        """Generate Product Quality tables
        - Table 1: Product Quality by Round (3 quality combinations: HQ-HQ, LQ-LQ, Dishonest)
        - Table 2: Overall Product Quality Statistics (aggregated across all 10 rounds)
        """
        # Load product quality data
        r_quality = self._load_product_quality_data(self.r_exp_id)
        rw_quality = self._load_product_quality_data(self.rw_exp_id)
        
        if r_quality.empty or rw_quality.empty:
            print("Warning: No product quality data available for table generation")
            return
        
        # Define 3 quality combinations:
        # 1. HQ-HQ: Honest High Quality (HQ advertised, HQ true)
        # 2. LQ-LQ: Honest Low Quality (LQ advertised, LQ true)
        # 3. Dishonest: HQ-LQ (HQ advertised, LQ true - deception)
        # Note: LQ-HQ (LQ advertised, HQ true) is less common, we can include it separately or combine
        
        # Aggregate by round for both experiments
        r_agg = r_quality.groupby('round').agg({
            'hq_hq': ['mean', 'std'],
            'lq_lq': ['mean', 'std'],
            'hq_lq': ['mean', 'std'],  # Dishonest
            'lq_hq': ['mean', 'std']  # Less common case
        }).reset_index()
        r_agg.columns = ['round', 'hq_hq_mean', 'hq_hq_std', 'lq_lq_mean', 'lq_lq_std', 
                        'hq_lq_mean', 'hq_lq_std', 'lq_hq_mean', 'lq_hq_std']
        
        rw_agg = rw_quality.groupby('round').agg({
            'hq_hq': ['mean', 'std'],
            'lq_lq': ['mean', 'std'],
            'hq_lq': ['mean', 'std'],  # Dishonest
            'lq_hq': ['mean', 'std']  # Less common case
        }).reset_index()
        rw_agg.columns = ['round', 'hq_hq_mean', 'hq_hq_std', 'lq_lq_mean', 'lq_lq_std',
                        'hq_lq_mean', 'hq_lq_std', 'lq_hq_mean', 'lq_hq_std']
        
        all_rounds = sorted(set(r_agg['round'].unique()) | set(rw_agg['round'].unique()))
        
        # Table 1: Product Quality by Round
        headers = ['Round', 'R-HQ-HQ', 'R-LQ-LQ', 'R-Dishonest', 
                  'RW-HQ-HQ', 'RW-LQ-LQ', 'RW-Dishonest']
        rows = []
        
        for round_num in all_rounds:
            r_row = r_agg[r_agg['round'] == round_num]
            rw_row = rw_agg[rw_agg['round'] == round_num]
            
            r_hq_hq = f"{self._format_number(r_row['hq_hq_mean'].values[0], 1)}" if not r_row.empty else "N/A"
            r_lq_lq = f"{self._format_number(r_row['lq_lq_mean'].values[0], 1)}" if not r_row.empty else "N/A"
            r_dishonest = f"{self._format_number(r_row['hq_lq_mean'].values[0], 1)}" if not r_row.empty else "N/A"
            
            rw_hq_hq = f"{self._format_number(rw_row['hq_hq_mean'].values[0], 1)}" if not rw_row.empty else "N/A"
            rw_lq_lq = f"{self._format_number(rw_row['lq_lq_mean'].values[0], 1)}" if not rw_row.empty else "N/A"
            rw_dishonest = f"{self._format_number(rw_row['hq_lq_mean'].values[0], 1)}" if not rw_row.empty else "N/A"
            
            rows.append([str(round_num), r_hq_hq, r_lq_lq, r_dishonest,
                        rw_hq_hq, rw_lq_lq, rw_dishonest])
        
        # Calculate overall statistics (average across all rounds)
        r_hq_hq_overall = np.mean([float(r[1]) if r[1] != "N/A" else 0 for r in rows])
        r_lq_lq_overall = np.mean([float(r[2]) if r[2] != "N/A" else 0 for r in rows])
        r_dishonest_overall = np.mean([float(r[3]) if r[3] != "N/A" else 0 for r in rows])
        rw_hq_hq_overall = np.mean([float(r[4]) if r[4] != "N/A" else 0 for r in rows])
        rw_lq_lq_overall = np.mean([float(r[5]) if r[5] != "N/A" else 0 for r in rows])
        rw_dishonest_overall = np.mean([float(r[6]) if r[6] != "N/A" else 0 for r in rows])
        
        rows.append(['Average',
                    f"{self._format_number(r_hq_hq_overall, 1)}",
                    f"{self._format_number(r_lq_lq_overall, 1)}",
                    f"{self._format_number(r_dishonest_overall, 1)}",
                    f"{self._format_number(rw_hq_hq_overall, 1)}",
                    f"{self._format_number(rw_lq_lq_overall, 1)}",
                    f"{self._format_number(rw_dishonest_overall, 1)}"])
        
        # Calculate total sum across all rounds
        r_hq_hq_total = sum([float(r[1]) if r[1] != "N/A" else 0 for r in rows[:-1]])
        r_lq_lq_total = sum([float(r[2]) if r[2] != "N/A" else 0 for r in rows[:-1]])
        r_dishonest_total = sum([float(r[3]) if r[3] != "N/A" else 0 for r in rows[:-1]])
        rw_hq_hq_total = sum([float(r[4]) if r[4] != "N/A" else 0 for r in rows[:-1]])
        rw_lq_lq_total = sum([float(r[5]) if r[5] != "N/A" else 0 for r in rows[:-1]])
        rw_dishonest_total = sum([float(r[6]) if r[6] != "N/A" else 0 for r in rows[:-1]])
        
        rows.append(['Total',
                    f"{self._format_number(r_hq_hq_total, 1)}",
                    f"{self._format_number(r_lq_lq_total, 1)}",
                    f"{self._format_number(r_dishonest_total, 1)}",
                    f"{self._format_number(rw_hq_hq_total, 1)}",
                    f"{self._format_number(rw_lq_lq_total, 1)}",
                    f"{self._format_number(rw_dishonest_total, 1)}"])
        
        md_table1 = self._generate_markdown_table(headers, rows,
                                                  "Product Quality by Round (3 Quality Combinations)")
        latex_table1 = self._generate_latex_table(headers, rows,
                                                 "Product Quality by Round (3 Quality Combinations)",
                                                 "tab:product_quality_by_round")
        
        # Table 2: Overall Product Quality Statistics
        # Load transaction quality data to distinguish "On sale" vs "Sold"
        r_tx_quality = self._load_transaction_quality_data(self.r_exp_id)
        rw_tx_quality = self._load_transaction_quality_data(self.rw_exp_id)
        
        # Calculate statistics across all rounds and runs
        # On sale: all products (from r_quality and rw_quality)
        r_hq_hq_all = r_quality['hq_hq'].values
        r_lq_lq_all = r_quality['lq_lq'].values
        r_hq_lq_all = r_quality['hq_lq'].values
        r_lq_hq_all = r_quality['lq_hq'].values
        
        rw_hq_hq_all = rw_quality['hq_hq'].values
        rw_lq_lq_all = rw_quality['lq_lq'].values
        rw_hq_lq_all = rw_quality['hq_lq'].values
        rw_lq_hq_all = rw_quality['lq_hq'].values
        
        # Sold: only transaction products (from r_tx_quality and rw_tx_quality)
        r_tx_hq_hq_all = r_tx_quality['hq_hq'].values if not r_tx_quality.empty else np.array([])
        r_tx_lq_lq_all = r_tx_quality['lq_lq'].values if not r_tx_quality.empty else np.array([])
        r_tx_hq_lq_all = r_tx_quality['hq_lq'].values if not r_tx_quality.empty else np.array([])
        r_tx_lq_hq_all = r_tx_quality['lq_hq'].values if not r_tx_quality.empty else np.array([])
        
        rw_tx_hq_hq_all = rw_tx_quality['hq_hq'].values if not rw_tx_quality.empty else np.array([])
        rw_tx_lq_lq_all = rw_tx_quality['lq_lq'].values if not rw_tx_quality.empty else np.array([])
        rw_tx_hq_lq_all = rw_tx_quality['hq_lq'].values if not rw_tx_quality.empty else np.array([])
        rw_tx_lq_hq_all = rw_tx_quality['lq_hq'].values if not rw_tx_quality.empty else np.array([])
        
        # New format: multi-level headers with On sale and Sold sub-columns
        # Helper function to format Mean±Std
        def format_mean_std(values):
            if len(values) == 0:
                return "N/A"
            mean = np.mean(values) if len(values) > 0 else 0.0
            std = np.std(values) if len(values) > 1 else 0.0
            return f"{self._format_number(mean, 1)}±{self._format_number(std, 1)}"
        
        # Multi-level headers: first row for quality types, second row for On sale/Sold
        headers2_row1 = ['Market Type', 'HQ-HQ', 'HQ-HQ', 'LQ-LQ', 'LQ-LQ', 'HQ-LQ', 'HQ-LQ']
        headers2_row2 = ['Market Type', 'On sale', 'Sold', 'On sale', 'Sold', 'On sale', 'Sold']
        
        # Data rows: each market type has both On sale and Sold data
        rows2 = []
        
        # Reputation-Only row
        rows2.append(['Reputation-Only',
                    format_mean_std(r_hq_hq_all),      # HQ-HQ On sale
                    format_mean_std(r_tx_hq_hq_all),    # HQ-HQ Sold
                    format_mean_std(r_lq_lq_all),      # LQ-LQ On sale
                    format_mean_std(r_tx_lq_lq_all),   # LQ-LQ Sold
                    format_mean_std(r_hq_lq_all),      # HQ-LQ On sale
                    format_mean_std(r_tx_hq_lq_all)])   # HQ-LQ Sold
        
        # Reputation+Warrant row
        rows2.append(['Reputation+Warrant',
                    format_mean_std(rw_hq_hq_all),     # HQ-HQ On sale
                    format_mean_std(rw_tx_hq_hq_all),   # HQ-HQ Sold
                    format_mean_std(rw_lq_lq_all),     # LQ-LQ On sale
                    format_mean_std(rw_tx_lq_lq_all),  # LQ-LQ Sold
                    format_mean_std(rw_hq_lq_all),     # HQ-LQ On sale
                    format_mean_std(rw_tx_hq_lq_all)]) # HQ-LQ Sold
        
        # Generate markdown table with multi-level headers
        md_table2 = self._generate_markdown_table_multi_level(
            headers2_row1, headers2_row2, rows2,
            "Overall Product Quality Statistics (All 10 Rounds)")
        
        # Generate LaTeX table with multi-level headers
        latex_table2 = self._generate_latex_table_multi_level(
            headers2_row1, headers2_row2, rows2,
            "Overall Product Quality Statistics (All 10 Rounds)",
            "tab:product_quality_overall")
        
        # Save both tables to a single file
        table_file = self.table_dir / "rq2_product_quality.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table1)
            f.write("\n\n")
            f.write(latex_table1)
            f.write("\n\n")
            f.write(md_table2)
            f.write("\n\n")
            f.write(latex_table2)
        
        print("✓ Generated: rq2_product_quality.md")
    
    def generate_tables(self):
        """Generate all tables"""
        self.generate_summary_statistics_table()
        self.generate_round_comparison_table()
        self.generate_profit_utility_by_round_table()
        self.generate_reputation_tables()
        self.generate_product_quality_tables()


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

