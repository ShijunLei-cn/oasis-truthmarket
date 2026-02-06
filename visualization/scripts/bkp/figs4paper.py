#!/usr/bin/env python3
"""
Paper Figures Visualization
Academic-style visualizations for paper figures

Generates visualizations comparing different Market Types over rounds:
1. Round Evolution Comparison (4 subplots):
   - Subplot 1: Seller Profit and Buyer Profit
   - Subplot 2: Authentic Products (HQ Authentic, LQ Authentic)
   - Subplot 3: Counterfeit Products (HQ Counterfeit)
   - Subplot 4: Gini Coefficient
"""

import json
import os
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

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


class PaperFigureVisualizer:
    """Paper Figure Visualizer"""
    
    def __init__(self, experiment_configs: Dict[str, str], output_dir: str):
        """
        Initialize visualizer
        
        Args:
            experiment_configs: Dict mapping market type name to experiment ID
                               e.g., {'Reputation-Only': 'gpt-4o-mini/paper/rq2/r_wo',
                                      'Reputation+Warrant': 'gpt-4o-mini/paper/rq2/rw_wo'}
            output_dir: Output directory for figures
        """
        self.experiment_configs = experiment_configs
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme for different market types
        colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']
        self.colors = {name: colors[i % len(colors)] for i, name in enumerate(experiment_configs.keys())}
        
        # Get market parameters for default values
        self.market_params = SimulationConfig.MARKET_PARAMS
    
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
                
                conn.close()
                
                # Get actual round numbers from data
                all_round_numbers = set()
                if not transactions.empty:
                    all_round_numbers.update(transactions['round_number'].unique())
                
                # Aggregate by round
                for round_num in sorted(all_round_numbers):
                    if pd.isna(round_num):
                        continue
                    round_num = int(round_num)
                    round_trans = transactions[transactions['round_number'] == round_num]
                    
                    all_rounds_data.append({
                        'run_id': run_id,
                        'round': round_num,
                        'seller_profit': round_trans['seller_profit'].sum() if not round_trans.empty else 0,
                        'buyer_utility': round_trans['buyer_utility'].sum() if not round_trans.empty else 0,
                    })
            except Exception as e:
                print(f"Warning: Could not load data from {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _load_product_quality_data(self, exp_id: str) -> pd.DataFrame:
        """Load product quality data by round (all listed products in each round)
        Tries both product table and transactions JOIN product to get complete data
        """
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        empty_files = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # First, try to load from product table directly
                products_query = "SELECT round_number, advertised_quality, true_quality FROM product"
                products = pd.read_sql_query(products_query, conn)
                
                # If product table is empty, try to get product info from transactions
                if products.empty:
                    # Check if transactions table exists and has data
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
                    if cursor.fetchone():
                        # Try to get product info from transactions JOIN product
                        tx_products_query = """
                            SELECT DISTINCT t.round_number, p.advertised_quality, p.true_quality
                            FROM transactions t
                            JOIN product p ON t.product_id = p.product_id
                            WHERE p.advertised_quality IS NOT NULL AND p.true_quality IS NOT NULL
                        """
                        tx_products = pd.read_sql_query(tx_products_query, conn)
                        if not tx_products.empty:
                            products = tx_products
                
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
                        
                        # Count by product types
                        # HQ Authentic: advertised HQ, true HQ (honest HQ products)
                        hq_hq = len(round_prod[(round_prod['advertised_quality'] == 'HQ') & (round_prod['true_quality'] == 'HQ')])
                        # HQ Counterfeit: advertised HQ, true LQ (fraudulent HQ products)
                        hq_lq = len(round_prod[(round_prod['advertised_quality'] == 'HQ') & (round_prod['true_quality'] == 'LQ')])
                        # LQ Authentic: advertised LQ, true LQ (honest LQ products)
                        lq_lq = len(round_prod[(round_prod['advertised_quality'] == 'LQ') & (round_prod['true_quality'] == 'LQ')])
                        
                        all_rounds_data.append({
                            'run_id': run_id,
                            'round': round_num,
                            'hq_authentic': hq_hq,
                            'hq_counterfeit': hq_lq,
                            'lq_authentic': lq_lq,
                        })
                else:
                    empty_files.append(db_file.name)
            except Exception as e:
                print(f"Warning: Could not load product quality data from {db_file}: {e}")
        
        # Only print warning if all files are empty or most files are empty
        if empty_files and len(empty_files) > len(list(exp_dir.glob("run_*.db"))) * 0.5:
            print(f"Warning: {len(empty_files)} out of {len(list(exp_dir.glob('run_*.db')))} database files have no products for {exp_id}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _calculate_gini_coefficient(self, values):
        """Calculate Gini coefficient for a list of values"""
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
        indices = np.arange(1, n + 1)
        gini = (2 * np.sum(indices * values)) / (n * np.sum(values)) - (n + 1) / n
        
        # Ensure result is in valid range [0, 1]
        gini = max(0.0, min(1.0, gini))
        
        return gini
    
    def _calculate_gini_by_round(self, exp_id: str, metric_type: str) -> pd.DataFrame:
        """Calculate Gini coefficient by round for each run"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        for db_file in sorted(exp_dir.glob("run_*.db")):
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                if metric_type == 'seller_profit':
                    query = """
                        SELECT round_number, seller_id, SUM(seller_profit) as total_value
                        FROM transactions
                        GROUP BY round_number, seller_id
                    """
                else:  # buyer_utility
                    query = """
                        SELECT round_number, buyer_id, SUM(buyer_utility) as total_value
                        FROM transactions
                        GROUP BY round_number, buyer_id
                    """
                
                result = pd.read_sql_query(query, conn)
                conn.close()
                
                if not result.empty:
                    # Calculate Gini for each round
                    for round_num in sorted(result['round_number'].dropna().unique()):
                        round_num = int(round_num)
                        round_data = result[result['round_number'] == round_num]
                        values = round_data['total_value'].dropna().tolist()
                        
                        if len(values) > 0:
                            gini = self._calculate_gini_coefficient(values)
                            all_rounds_data.append({
                                'run_id': run_id,
                                'round': round_num,
                                'gini': gini
                            })
            except Exception as e:
                print(f"Warning: Could not calculate Gini for {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _aggregate_by_round(self, df: pd.DataFrame, value_col: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Aggregate data by round, returning rounds, means, and stds"""
        if df.empty:
            return np.array([]), np.array([]), np.array([])
        
        grouped = df.groupby('round')[value_col].agg(['mean', 'std']).reset_index()
        rounds = grouped['round'].values
        means = grouped['mean'].values
        stds = grouped['std'].fillna(0).values
        
        return rounds, means, stds
    
    def plot_round_evolution_comparison(self, filename: str = "round_evolution_comparison.png", show_error_bars: bool = True):
        """
        Plot round evolution comparison with 4 subplots:
        1. Seller Profit and Buyer Profit
        2. Product Quality Counts - Authentic Products (HQ Authentic, LQ Authentic)
        3. Product Quality Counts - Counterfeit Products (HQ Counterfeit)
        4. Gini Coefficient
        
        Args:
            filename: Output filename
            show_error_bars: If True, show error bars (fill_between), otherwise only show lines
        """
        fig, axes = plt.subplots(1, 4, figsize=(24, 5))
        
        # Subplot 1: Seller Profit and Buyer Profit
        ax1 = axes[0]
        for market_type, exp_id in self.experiment_configs.items():
            color = self.colors[market_type]
            
            # Load profit data
            profit_data = self._load_round_data_from_db(exp_id)
            
            if not profit_data.empty:
                # Seller Profit
                rounds, means, stds = self._aggregate_by_round(profit_data, 'seller_profit')
                if len(rounds) > 0:
                    ax1.plot(rounds, means, marker='o', linewidth=2, markersize=6, 
                            color=color, label=f'{market_type} (Seller)', linestyle='-')
                    if show_error_bars:
                        ax1.fill_between(rounds, means - stds, means + stds, alpha=0.2, color=color)
                
                # Buyer Profit (Utility)
                rounds, means, stds = self._aggregate_by_round(profit_data, 'buyer_utility')
                if len(rounds) > 0:
                    ax1.plot(rounds, means, marker='s', linewidth=2, markersize=6, 
                            color=color, label=f'{market_type} (Buyer)', linestyle='--', alpha=0.7)
                    if show_error_bars:
                        ax1.fill_between(rounds, means - stds, means + stds, alpha=0.15, color=color)
        
        ax1.set_xlabel('Round', fontsize=12)
        ax1.set_ylabel('Profit/Utility', fontsize=12)
        ax1.set_title('(a) Seller Profit and Buyer Profit', fontsize=13, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # Load product quality data for all market types first (to avoid repeated loading)
        quality_data_cache = {}
        for market_type, exp_id in self.experiment_configs.items():
            quality_data_cache[market_type] = self._load_product_quality_data(exp_id)
            if quality_data_cache[market_type].empty:
                print(f"Warning: No product quality data loaded for {market_type} ({exp_id})")
        
        # Subplot 2: Authentic Products (HQ Authentic and LQ Authentic)
        ax2 = axes[1]
        authentic_types = ['hq_authentic', 'lq_authentic']
        authentic_labels = ['HQ Authentic', 'LQ Authentic']
        markers = ['o', 's']
        
        for quality_type, label, marker in zip(authentic_types, authentic_labels, markers):
            for market_type in self.experiment_configs.keys():
                color = self.colors[market_type]
                quality_data = quality_data_cache[market_type]
                
                if not quality_data.empty:
                    rounds, means, stds = self._aggregate_by_round(quality_data, quality_type)
                    if len(rounds) > 0:
                        ax2.plot(rounds, means, marker=marker, linewidth=2, markersize=6,
                                color=color, label=f'{market_type} - {label}', linestyle='-', alpha=0.8)
                        if show_error_bars:
                            ax2.fill_between(rounds, means - stds, means + stds, alpha=0.15, color=color)
        
        ax2.set_xlabel('Round', fontsize=12)
        ax2.set_ylabel('Product Count', fontsize=12)
        ax2.set_title('(b) Authentic Products', fontsize=13, fontweight='bold')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # Subplot 3: Counterfeit Products (HQ Counterfeit)
        ax3 = axes[2]
        for market_type in self.experiment_configs.keys():
            color = self.colors[market_type]
            quality_data = quality_data_cache[market_type]
            
            if not quality_data.empty:
                rounds, means, stds = self._aggregate_by_round(quality_data, 'hq_counterfeit')
                if len(rounds) > 0:
                    ax3.plot(rounds, means, marker='^', linewidth=2, markersize=6,
                            color=color, label=f'{market_type} - HQ Counterfeit', linestyle='-', alpha=0.8)
                    if show_error_bars:
                        ax3.fill_between(rounds, means - stds, means + stds, alpha=0.15, color=color)
        
        ax3.set_xlabel('Round', fontsize=12)
        ax3.set_ylabel('Product Count', fontsize=12)
        ax3.set_title('(c) Counterfeit Products', fontsize=13, fontweight='bold')
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # Subplot 4: Gini Coefficient
        ax4 = axes[3]
        for market_type, exp_id in self.experiment_configs.items():
            color = self.colors[market_type]
            
            # Calculate Gini for seller profit
            gini_data = self._calculate_gini_by_round(exp_id, 'seller_profit')
            
            if not gini_data.empty:
                rounds, means, stds = self._aggregate_by_round(gini_data, 'gini')
                if len(rounds) > 0:
                    ax4.plot(rounds, means, marker='o', linewidth=2, markersize=6,
                            color=color, label=f'{market_type} (Seller)', linestyle='-')
                    if show_error_bars:
                        ax4.fill_between(rounds, means - stds, means + stds, alpha=0.2, color=color)
            
            # Calculate Gini for buyer utility
            gini_data_buyer = self._calculate_gini_by_round(exp_id, 'buyer_utility')
            
            if not gini_data_buyer.empty:
                rounds, means, stds = self._aggregate_by_round(gini_data_buyer, 'gini')
                if len(rounds) > 0:
                    ax4.plot(rounds, means, marker='s', linewidth=2, markersize=6,
                            color=color, label=f'{market_type} (Buyer)', linestyle='--', alpha=0.7)
                    if show_error_bars:
                        ax4.fill_between(rounds, means - stds, means + stds, alpha=0.15, color=color)
        
        ax4.set_xlabel('Round', fontsize=12)
        ax4.set_ylabel('Gini Coefficient', fontsize=12)
        ax4.set_title('(d) Gini Coefficient', fontsize=13, fontweight='bold')
        ax4.legend(loc='best', fontsize=9)
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim([0, 1])
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def plot_rq3_comparison(self, initial_post_type: str, r_r_exp_id: str, rw_r_exp_id: str, 
                           r_f_exp_id: str, rw_f_exp_id: str, filename: str = None):
        """
        Plot RQ3 comparison with 2x3 subplots layout:
        - Row 1: Rep-Only Market (R)
        - Row 2: Rep+Warrant Market (RW)
        - Column 1: Seller Profit and Buyer Profit
        - Column 2: Authentic Products (HQ Authentic, LQ Authentic)
        - Column 3: Counterfeit Products (HQ Counterfeit)
        Each subplot shows two conditions: Fake Channel (F) and True Channel (R)
        
        Args:
            initial_post_type: Type of initial post (e.g., 'policy_making', 'pressure_quickprofits', 'psychological-based-attack')
            r_r_exp_id: Rep-Only, True Channel experiment ID
            rw_r_exp_id: Rep+Warrant, True Channel experiment ID
            r_f_exp_id: Rep-Only, Fake Channel experiment ID
            rw_f_exp_id: Rep+Warrant, Fake Channel experiment ID
            filename: Output filename (default: rq3_{initial_post_type}_comparison.png)
        """
        if filename is None:
            filename = f"rq3_{initial_post_type}_comparison.png"
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # Color scheme for conditions
        condition_colors = {
            'F': '#d62728',  # Red for Fake Channel
            'R': '#2ca02c',  # Green for True Channel
        }
        
        # Row 1: Rep-Only Market
        # Column 1: Seller Profit and Buyer Profit
        ax1 = axes[0, 0]
        for condition, exp_id, label_suffix in [('F', r_f_exp_id, 'Fake'), ('R', r_r_exp_id, 'True')]:
            if not exp_id:
                continue
            color = condition_colors[condition]
            profit_data = self._load_round_data_from_db(exp_id)
            
            if not profit_data.empty:
                # Seller Profit
                rounds, means, stds = self._aggregate_by_round(profit_data, 'seller_profit')
                if len(rounds) > 0:
                    ax1.plot(rounds, means, marker='o', linewidth=2, markersize=5,
                            color=color, label=f'Rep-Only ({label_suffix}) - Seller', linestyle='-')
                
                # Buyer Profit (Utility)
                rounds, means, stds = self._aggregate_by_round(profit_data, 'buyer_utility')
                if len(rounds) > 0:
                    ax1.plot(rounds, means, marker='s', linewidth=2, markersize=5,
                            color=color, label=f'Rep-Only ({label_suffix}) - Buyer', linestyle='--', alpha=0.7)
        
        ax1.set_xlabel('Round', fontsize=11)
        ax1.set_ylabel('Profit/Utility', fontsize=11)
        ax1.set_title('(a) Seller Profit and Buyer Profit\n(Rep-Only)', fontsize=12, fontweight='bold')
        ax1.legend(loc='best', fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Column 2: Authentic Products
        ax2 = axes[0, 1]
        authentic_types = ['hq_authentic', 'lq_authentic']
        authentic_labels = ['HQ Authentic', 'LQ Authentic']
        markers = ['o', 's']
        
        for condition, exp_id, label_suffix in [('F', r_f_exp_id, 'Fake'), ('R', r_r_exp_id, 'True')]:
            if not exp_id:
                continue
            color = condition_colors[condition]
            quality_data = self._load_product_quality_data(exp_id)
            
            if not quality_data.empty:
                for quality_type, label, marker in zip(authentic_types, authentic_labels, markers):
                    rounds, means, stds = self._aggregate_by_round(quality_data, quality_type)
                    if len(rounds) > 0:
                        ax2.plot(rounds, means, marker=marker, linewidth=2, markersize=5,
                                color=color, label=f'Rep-Only ({label_suffix}) - {label}', linestyle='-', alpha=0.8)
        
        ax2.set_xlabel('Round', fontsize=11)
        ax2.set_ylabel('Product Count', fontsize=11)
        ax2.set_title('(b) Authentic Products\n(Rep-Only)', fontsize=12, fontweight='bold')
        ax2.legend(loc='best', fontsize=7)
        ax2.grid(True, alpha=0.3)
        
        # Column 3: Counterfeit Products
        ax3 = axes[0, 2]
        for condition, exp_id, label_suffix in [('F', r_f_exp_id, 'Fake'), ('R', r_r_exp_id, 'True')]:
            if not exp_id:
                continue
            color = condition_colors[condition]
            quality_data = self._load_product_quality_data(exp_id)
            
            if not quality_data.empty:
                rounds, means, stds = self._aggregate_by_round(quality_data, 'hq_counterfeit')
                if len(rounds) > 0:
                    ax3.plot(rounds, means, marker='^', linewidth=2, markersize=5,
                            color=color, label=f'Rep-Only ({label_suffix}) - HQ Counterfeit', linestyle='-', alpha=0.8)
        
        ax3.set_xlabel('Round', fontsize=11)
        ax3.set_ylabel('Product Count', fontsize=11)
        ax3.set_title('(c) Counterfeit Products\n(Rep-Only)', fontsize=12, fontweight='bold')
        ax3.legend(loc='best', fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        # Row 2: Rep+Warrant Market
        # Column 1: Seller Profit and Buyer Profit
        ax4 = axes[1, 0]
        for condition, exp_id, label_suffix in [('F', rw_f_exp_id, 'Fake'), ('R', rw_r_exp_id, 'True')]:
            if not exp_id:
                continue
            color = condition_colors[condition]
            profit_data = self._load_round_data_from_db(exp_id)
            
            if not profit_data.empty:
                # Seller Profit
                rounds, means, stds = self._aggregate_by_round(profit_data, 'seller_profit')
                if len(rounds) > 0:
                    ax4.plot(rounds, means, marker='o', linewidth=2, markersize=5,
                            color=color, label=f'Rep+Warrant ({label_suffix}) - Seller', linestyle='-')
                
                # Buyer Profit (Utility)
                rounds, means, stds = self._aggregate_by_round(profit_data, 'buyer_utility')
                if len(rounds) > 0:
                    ax4.plot(rounds, means, marker='s', linewidth=2, markersize=5,
                            color=color, label=f'Rep+Warrant ({label_suffix}) - Buyer', linestyle='--', alpha=0.7)
        
        ax4.set_xlabel('Round', fontsize=11)
        ax4.set_ylabel('Profit/Utility', fontsize=11)
        ax4.set_title('(d) Seller Profit and Buyer Profit\n(Rep+Warrant)', fontsize=12, fontweight='bold')
        ax4.legend(loc='best', fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # Column 2: Authentic Products
        ax5 = axes[1, 1]
        for condition, exp_id, label_suffix in [('F', rw_f_exp_id, 'Fake'), ('R', rw_r_exp_id, 'True')]:
            if not exp_id:
                continue
            color = condition_colors[condition]
            quality_data = self._load_product_quality_data(exp_id)
            
            if not quality_data.empty:
                for quality_type, label, marker in zip(authentic_types, authentic_labels, markers):
                    rounds, means, stds = self._aggregate_by_round(quality_data, quality_type)
                    if len(rounds) > 0:
                        ax5.plot(rounds, means, marker=marker, linewidth=2, markersize=5,
                                color=color, label=f'Rep+Warrant ({label_suffix}) - {label}', linestyle='-', alpha=0.8)
        
        ax5.set_xlabel('Round', fontsize=11)
        ax5.set_ylabel('Product Count', fontsize=11)
        ax5.set_title('(e) Authentic Products\n(Rep+Warrant)', fontsize=12, fontweight='bold')
        ax5.legend(loc='best', fontsize=7)
        ax5.grid(True, alpha=0.3)
        
        # Column 3: Counterfeit Products
        ax6 = axes[1, 2]
        for condition, exp_id, label_suffix in [('F', rw_f_exp_id, 'Fake'), ('R', rw_r_exp_id, 'True')]:
            if not exp_id:
                continue
            color = condition_colors[condition]
            quality_data = self._load_product_quality_data(exp_id)
            
            if not quality_data.empty:
                rounds, means, stds = self._aggregate_by_round(quality_data, 'hq_counterfeit')
                if len(rounds) > 0:
                    ax6.plot(rounds, means, marker='^', linewidth=2, markersize=5,
                            color=color, label=f'Rep+Warrant ({label_suffix}) - HQ Counterfeit', linestyle='-', alpha=0.8)
        
        ax6.set_xlabel('Round', fontsize=11)
        ax6.set_ylabel('Product Count', fontsize=11)
        ax6.set_title('(f) Counterfeit Products\n(Rep+Warrant)', fontsize=12, fontweight='bold')
        ax6.legend(loc='best', fontsize=8)
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def generate_all_figures(self):
        """Generate all paper figures (both with and without error bars)"""
        print("Generating paper figures...")
        # Version 1: With error bars
        self.plot_round_evolution_comparison("round_evolution_comparison.png", show_error_bars=True)
        # Version 2: Without error bars
        self.plot_round_evolution_comparison("round_evolution_comparison_no_errorbars.png", show_error_bars=False)
        print("All figures generated!")


def main():
    parser = argparse.ArgumentParser(description='Generate paper figures')
    parser.add_argument('--experiments', nargs='+', default=None,
                       help='Experiment IDs in format "MarketType:ExperimentID" (e.g., "Reputation-Only:gpt-4o-mini/paper/rq2/r_wo")')
    parser.add_argument('--output-dir', type=str, required=True,
                       help='Output directory for figures')
    parser.add_argument('--rq3', action='store_true',
                       help='Generate RQ3 figures (requires --initial-post-type and experiment IDs)')
    parser.add_argument('--initial-post-type', type=str, default=None,
                       help='Initial post type for RQ3 (e.g., policy_making, pressure_quickprofits, psychological-based-attack)')
    parser.add_argument('--r-r', type=str, default=None,
                       help='Rep-Only, True Channel experiment ID for RQ3')
    parser.add_argument('--rw-r', type=str, default=None,
                       help='Rep+Warrant, True Channel experiment ID for RQ3')
    parser.add_argument('--r-f', type=str, default=None,
                       help='Rep-Only, Fake Channel experiment ID for RQ3')
    parser.add_argument('--rw-f', type=str, default=None,
                       help='Rep+Warrant, Fake Channel experiment ID for RQ3')
    
    args = parser.parse_args()
    
    # Create a dummy visualizer for RQ3 (experiment_configs not needed)
    dummy_configs = {}
    visualizer = PaperFigureVisualizer(dummy_configs, args.output_dir)
    
    if args.rq3:
        # Generate RQ3 figures
        if not args.initial_post_type:
            print("Error: --initial-post-type is required for RQ3 figures.")
            return
        
        if not all([args.r_r, args.rw_r, args.r_f, args.rw_f]):
            print("Error: All RQ3 experiment IDs (--r-r, --rw-r, --r-f, --rw-f) are required.")
            return
        
        print(f"Generating RQ3 figure for initial_post_type: {args.initial_post_type}")
        visualizer.plot_rq3_comparison(
            args.initial_post_type,
            args.r_r,
            args.rw_r,
            args.r_f,
            args.rw_f
        )
    else:
        # Generate RQ2 figures
        if not args.experiments:
            print("Error: --experiments is required for RQ2 figures.")
            return
        
        # Parse experiment configurations
        experiment_configs = {}
        for exp_str in args.experiments:
            if ':' not in exp_str:
                print(f"Warning: Invalid format '{exp_str}'. Expected 'MarketType:ExperimentID'. Skipping.")
                continue
            market_type, exp_id = exp_str.split(':', 1)
            experiment_configs[market_type] = exp_id
        
        if not experiment_configs:
            print("Error: No valid experiment configurations provided.")
            return
        
        # Update visualizer with actual configs
        visualizer.experiment_configs = experiment_configs
        visualizer.colors = {name: ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b'][i % 6] 
                            for i, name in enumerate(experiment_configs.keys())}
        
        visualizer.generate_all_figures()


if __name__ == '__main__':
    main()
