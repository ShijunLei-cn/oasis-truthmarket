#!/usr/bin/env python3
"""
Temperature Comparison Visualization
Academic-style visualizations for comparing different temperature settings

Generates visualizations comparing the same market mechanism across different temperatures:
1. Price Evolution Over Rounds
2. Seller Profit Over Rounds (with detailed breakdowns)
3. Buyer Utility Over Rounds (with detailed breakdowns)
4. Seller Reputation Over Rounds
5. Total Market Metrics
6. Product Quality Evolution
"""

import json
import os
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy import stats

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

# Color scheme for different temperatures
COLORS = {
    '0.0': '#1f77b4',  # Blue
    '0.5': '#ff7f0e',  # Orange
    '1.0': '#2ca02c',  # Green
    '1.5': '#d62728',  # Red
    '2.0': '#9467bd',  # Purple
}


class TempVisualizer:
    """Temperature Comparison Visualizer"""
    
    def __init__(self, experiment_ids: Dict[str, str], market_type: str, output_dir: Optional[str] = None):
        """
        Initialize visualizer
        
        Args:
            experiment_ids: Dictionary mapping temperature values to experiment IDs
                          e.g., {'0.0': 'temperature/temp_0.0/r_wo', '0.5': 'temperature/temp_0.5/r_wo'}
            market_type: Market type ('r_wo' or 'rw_wo')
            output_dir: Output directory (default: visualization/figs/temperature/{market_type}_comparison)
        """
        self.experiment_ids = experiment_ids
        self.market_type = market_type
        self.temperatures = sorted(experiment_ids.keys(), key=lambda x: float(x))
        
        if output_dir is None:
            output_dir = f"visualization/figs/temperature/{market_type}_comparison"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create table output directory
        self.table_dir = Path("visualization/table/temperature")
        self.table_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data for each temperature
        self.data = {}
        self.configs = {}
        for temp, exp_id in experiment_ids.items():
            self.data[temp] = self._load_experiment_data(exp_id)
            self.configs[temp] = self._load_experiment_config(exp_id)
        
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
        # Try config.json first, then experiment_config.json
        config_file = f"experiments/{exp_id}/config.json"
        if not os.path.exists(config_file):
            config_file = f"experiments/{exp_id}/experiment_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_round_data_from_db(self, exp_id: str) -> pd.DataFrame:
        """Load round-by-round data from database files"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        if not exp_dir.exists():
            print(f"Warning: Experiment directory not found: {exp_dir}")
            return pd.DataFrame()
        
        db_files = list(sorted(exp_dir.glob("run_*.db")))
        if not db_files:
            print(f"Warning: No database files found in {exp_dir}")
            return pd.DataFrame()
        
        for db_file in db_files:
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load transactions
                transactions = pd.read_sql_query(
                    "SELECT round_number, seller_profit, buyer_utility, seller_id, buyer_id FROM transactions",
                    conn
                )
                
                # Load products for price data
                products = pd.read_sql_query(
                    "SELECT round_number, advertised_quality, price, true_quality FROM product",
                    conn
                )
                
                # Load reputation history
                try:
                    reputation = pd.read_sql_query(
                        "SELECT round, seller_id, public_thumbs_up, public_thumbs_down FROM reputation_history",
                        conn
                    )
                    if not reputation.empty:
                        reputation['public_reputation_score'] = reputation['public_thumbs_up'] - reputation['public_thumbs_down']
                except:
                    try:
                        reputation = pd.read_sql_query(
                            "SELECT round, seller_id, public_reputation_score FROM reputation_history",
                            conn
                        )
                    except:
                        reputation = pd.DataFrame(columns=['round', 'seller_id', 'public_reputation_score'])
                
                conn.close()
                
                # Get actual round numbers from data
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
                    
                    # Calculate averages
                    avg_price_hq = round_prod[round_prod['advertised_quality'] == 'HQ']['price'].mean() if not round_prod[round_prod['advertised_quality'] == 'HQ'].empty else np.nan
                    avg_price_lq = round_prod[round_prod['advertised_quality'] == 'LQ']['price'].mean() if not round_prod[round_prod['advertised_quality'] == 'LQ'].empty else np.nan
                    avg_seller_profit = round_trans['seller_profit'].mean() if not round_trans.empty else np.nan
                    avg_buyer_utility = round_trans['buyer_utility'].mean() if not round_trans.empty else np.nan
                    avg_reputation = round_rep['public_reputation_score'].mean() if not round_rep.empty else np.nan
                    transaction_count = len(round_trans)
                    
                    all_rounds_data.append({
                        'run_id': run_id,
                        'round': round_num,
                        'avg_price_hq': avg_price_hq,
                        'avg_price_lq': avg_price_lq,
                        'seller_profit': avg_seller_profit,
                        'buyer_utility': avg_buyer_utility,
                        'avg_reputation': avg_reputation,
                        'transactions': transaction_count
                    })
            except Exception as e:
                print(f"Warning: Could not load data from {db_file}: {e}")
        
        return pd.DataFrame(all_rounds_data)
    
    def _load_round_profit_by_type(self, exp_id: str) -> pd.DataFrame:
        """Load profit by type (honest/dishonest) by round"""
        exp_dir = Path(f"experiments/{exp_id}")
        all_rounds_data = []
        
        db_files = list(sorted(exp_dir.glob("run_*.db")))
        if not db_files:
            return pd.DataFrame()
        
        for db_file in db_files:
            run_id = int(db_file.stem.split('_')[1])
            try:
                conn = sqlite3.connect(db_file)
                
                # Load transactions with quality information
                transactions = pd.read_sql_query(
                    "SELECT t.round_number, t.seller_profit, p.advertised_quality, p.true_quality "
                    "FROM transactions t JOIN product p ON t.product_id = p.product_id",
                    conn
                )
                conn.close()
                
                if not transactions.empty:
                    transactions['advertised_quality'] = transactions['advertised_quality'].astype(str).str.strip()
                    transactions['true_quality'] = transactions['true_quality'].astype(str).str.strip()
                    
                    valid_mask = (
                        (transactions['advertised_quality'].isin(['HQ', 'LQ'])) &
                        (transactions['true_quality'].isin(['HQ', 'LQ']))
                    )
                    dishonest_mask = (
                        valid_mask &
                        (transactions['advertised_quality'] == 'HQ') &
                        (transactions['true_quality'] == 'LQ')
                    )
                    honest_mask = valid_mask & ~dishonest_mask
                    
                    for round_num in sorted(transactions['round_number'].unique()):
                        if pd.isna(round_num):
                            continue
                        round_num = int(round_num)
                        round_trans = transactions[transactions['round_number'] == round_num]
                        round_dishonest = round_trans[dishonest_mask & (transactions['round_number'] == round_num)]
                        round_honest = round_trans[honest_mask & (transactions['round_number'] == round_num)]
                        
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
                transactions = pd.read_sql_query(
                    "SELECT round_number, seller_id, seller_profit FROM transactions",
                    conn
                )
                conn.close()
                
                if not transactions.empty:
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
                transactions = pd.read_sql_query(
                    "SELECT round_number, buyer_id, buyer_utility FROM transactions",
                    conn
                )
                conn.close()
                
                if not transactions.empty:
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
                    
                    transactions['advertised_quality'] = transactions['advertised_quality'].astype(str).str.strip()
                    transactions['true_quality'] = transactions['true_quality'].astype(str).str.strip()
                    
                    valid_quality_mask = (
                        (transactions['advertised_quality'].isin(['HQ', 'LQ'])) &
                        (transactions['true_quality'].isin(['HQ', 'LQ']))
                    )
                    
                    dishonest_mask = (
                        valid_quality_mask &
                        (transactions['advertised_quality'] == 'HQ') & 
                        (transactions['true_quality'] == 'LQ')
                    )
                    
                    honest_mask = valid_quality_mask & ~dishonest_mask
                    
                    dishonest_profit = transactions[dishonest_mask]['seller_profit'].fillna(0).sum()
                    honest_profit = transactions[honest_mask]['seller_profit'].fillna(0).sum()
                    total_profit = honest_profit + dishonest_profit
                    
                    total_utility = transactions['buyer_utility'].fillna(0).sum()
                    
                    dishonest_count = len(transactions[dishonest_mask])
                    honest_count = len(transactions[honest_mask])
                    total_count = len(transactions)
                    
                    if not products.empty:
                        products['advertised_quality'] = products['advertised_quality'].astype(str).str.strip()
                        products['true_quality'] = products['true_quality'].astype(str).str.strip()
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
    
    def _calculate_gini_coefficient(self, values):
        """Calculate Gini coefficient for a list of values"""
        if len(values) == 0:
            return 0.0
        
        values = np.array([v for v in values if v > 0])
        if len(values) == 0 or np.sum(values) == 0:
            return 0.0
        
        values = np.sort(values)
        n = len(values)
        
        if n == 1:
            return 0.0
        
        indices = np.arange(1, n + 1)
        gini = (2 * np.sum(indices * values)) / (n * np.sum(values)) - (n + 1) / n
        gini = max(0.0, min(1.0, gini))
        
        return gini
    
    def _calculate_gini_by_run(self, exp_id: str, metric_type: str) -> Tuple[float, float]:
        """Calculate Gini coefficient by run, then return mean and std"""
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
    
    def _format_number(self, value: float, decimals: int = 2) -> str:
        """Format number with specified decimal places"""
        if pd.isna(value) or np.isnan(value):
            return "N/A"
        return f"{value:.{decimals}f}"
    
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
        
        num_cols = len(headers_row1)
        lines.append("\\begin{tabular}{" + "c" * num_cols + "}")
        lines.append("\\toprule")
        lines.append(" & ".join(headers_row1) + " \\\\")
        lines.append("\\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(lr){6-7} \\cmidrule(lr){8-9}")
        lines.append(" & ".join(headers_row2) + " \\\\")
        lines.append("\\midrule")
        
        for row in rows:
            lines.append(" & ".join(row) + " \\\\")
        
        lines.append("\\bottomrule")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")
        lines.append("```")
        
        return "\n".join(lines)
    
    def plot_price_evolution(self):
        """1. Price Evolution Over Rounds"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        all_rounds = set()
        temp_data = {}
        
        # Load and aggregate data for each temperature
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            rounds_data = self._load_round_data_from_db(exp_id)
            
            if not rounds_data.empty and 'round' in rounds_data.columns:
                all_rounds.update(rounds_data['round'].unique())
                temp_data[temp] = rounds_data
        
        rounds = sorted(all_rounds) if all_rounds else []
        
        if not rounds:
            print("Warning: No rounds data available for price evolution plot")
            return
        
        default_hq_price = self.market_params.get('hq_price', 5.0)
        default_lq_price = self.market_params.get('lq_price', 3.0)
        
        # Plot HQ prices
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_data and not temp_data[temp].empty:
                agg = temp_data[temp].groupby('round').agg({
                    'avg_price_hq': ['mean', 'std'],
                    'avg_price_lq': ['mean', 'std']
                }).reset_index()
                
                hq_mean = agg[('avg_price_hq', 'mean')].fillna(default_hq_price)
                hq_std = agg[('avg_price_hq', 'std')].fillna(0)
                hq_mean = hq_mean.reindex(rounds, fill_value=default_hq_price)
                hq_std = hq_std.reindex(rounds, fill_value=0)
                
                axes[0].errorbar(rounds, hq_mean, yerr=hq_std,
                              fmt='o-', label=f'Temperature {temp}',
                              color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        axes[0].set_xlabel('Round', fontweight='bold')
        axes[0].set_ylabel('Average Price ($)', fontweight='bold')
        axes[0].set_title('Price Evolution Over Rounds (HQ)', fontweight='bold', pad=15)
        axes[0].legend(loc='best', frameon=True, fancybox=True, shadow=True)
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].set_xticks(rounds)
        
        # Plot LQ prices
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_data and not temp_data[temp].empty:
                agg = temp_data[temp].groupby('round').agg({
                    'avg_price_lq': ['mean', 'std']
                }).reset_index()
                
                lq_mean = agg[('avg_price_lq', 'mean')].fillna(default_lq_price)
                lq_std = agg[('avg_price_lq', 'std')].fillna(0)
                lq_mean = lq_mean.reindex(rounds, fill_value=default_lq_price)
                lq_std = lq_std.reindex(rounds, fill_value=0)
                
                axes[1].errorbar(rounds, lq_mean, yerr=lq_std,
                              fmt='s-', label=f'Temperature {temp}',
                              color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        axes[1].set_xlabel('Round', fontweight='bold')
        axes[1].set_ylabel('Average Price ($)', fontweight='bold')
        axes[1].set_title('Price Evolution Over Rounds (LQ)', fontweight='bold', pad=15)
        axes[1].legend(loc='best', frameon=True, fancybox=True, shadow=True)
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].set_xticks(rounds)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '1_price_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 1_price_evolution.png")
    
    def plot_seller_profit(self):
        """2. Seller Profit Over Rounds (with detailed breakdowns)"""
        fig, axes = plt.subplots(3, 2, figsize=(14, 15))
        
        all_rounds = set()
        temp_data = {}
        temp_profit_by_type = {}
        
        # Load data for each temperature
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            rounds_data = self._load_round_data_from_db(exp_id)
            profit_by_type = self._load_round_profit_by_type(exp_id)
            
            if not rounds_data.empty and 'round' in rounds_data.columns:
                all_rounds.update(rounds_data['round'].unique())
                temp_data[temp] = rounds_data
                temp_profit_by_type[temp] = profit_by_type
        
        rounds = sorted(all_rounds) if all_rounds else []
        
        if not rounds:
            print("Warning: No rounds data available for seller profit plot")
            return
        
        # Top Left: Total profit line plot
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_data and not temp_data[temp].empty:
                agg = temp_data[temp].groupby('round')['seller_profit'].agg(['mean', 'std']).reset_index()
                agg = agg.set_index('round').reindex(rounds).reset_index()
                agg['mean'] = agg['mean'].fillna(0)
                agg['std'] = agg['std'].fillna(0)
                
                axes[0, 0].errorbar(rounds, agg['mean'], yerr=agg['std'],
                                  fmt='o-', label=f'Temperature {temp}',
                                  color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        axes[0, 0].set_xlabel('Round', fontweight='bold')
        axes[0, 0].set_ylabel('Average Seller Profit ($)', fontweight='bold')
        axes[0, 0].set_title('Total Seller Profit Progression', fontweight='bold')
        axes[0, 0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        axes[0, 0].set_xticks(rounds)
        
        # Top Right: KDE distribution comparison
        all_profits_by_temp = {}
        for temp in self.temperatures:
            if temp in temp_data and not temp_data[temp].empty:
                all_profits_by_temp[temp] = temp_data[temp]['seller_profit'].dropna().values
        
        if all_profits_by_temp:
            for temp, profits in all_profits_by_temp.items():
                if len(profits) > 1 and np.std(profits) > 1e-10:
                    color = COLORS.get(temp, '#000000')
                    kde = stats.gaussian_kde(profits)
                    x_range = np.linspace(profits.min(), profits.max(), 200)
                    axes[0, 1].plot(x_range, kde(x_range), label=f'Temperature {temp}',
                                  color=color, linewidth=2, alpha=0.7)
                    axes[0, 1].fill_between(x_range, kde(x_range), alpha=0.3, color=color)
                elif len(profits) > 0:
                    color = COLORS.get(temp, '#000000')
                    axes[0, 1].hist(profits, bins=20, alpha=0.5, label=f'Temperature {temp}',
                                  color=color, density=True, edgecolor='black', linewidth=0.5)
        
        axes[0, 1].set_xlabel('Seller Profit ($)', fontweight='bold')
        axes[0, 1].set_ylabel('Density', fontweight='bold')
        axes[0, 1].set_title('Profit Distribution Comparison', fontweight='bold')
        axes[0, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Middle Left: Honest profit progression
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_profit_by_type and not temp_profit_by_type[temp].empty:
                honest_agg = temp_profit_by_type[temp].groupby('round')['honest_profit'].agg(['mean', 'std']).reset_index()
                honest_rounds = sorted(honest_agg['round'].unique())
                axes[1, 0].errorbar(honest_rounds, honest_agg['mean'], yerr=honest_agg['std'],
                                  fmt='o-', label=f'Temperature {temp}',
                                  color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        axes[1, 0].set_xlabel('Round', fontweight='bold')
        axes[1, 0].set_ylabel('Average Honest Profit ($)', fontweight='bold')
        axes[1, 0].set_title('Honest Profit Progression', fontweight='bold')
        axes[1, 0].legend(frameon=True, fancybox=True, shadow=True)
        axes[1, 0].grid(True, alpha=0.3, linestyle='--')
        
        # Middle Right: Dishonest profit progression
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_profit_by_type and not temp_profit_by_type[temp].empty:
                dishonest_agg = temp_profit_by_type[temp].groupby('round')['dishonest_profit'].agg(['mean', 'std']).reset_index()
                dishonest_rounds = sorted(dishonest_agg['round'].unique())
                axes[1, 1].errorbar(dishonest_rounds, dishonest_agg['mean'], yerr=dishonest_agg['std'],
                                  fmt='s-', label=f'Temperature {temp}',
                                  color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        axes[1, 1].set_xlabel('Round', fontweight='bold')
        axes[1, 1].set_ylabel('Average Dishonest Profit ($)', fontweight='bold')
        axes[1, 1].set_title('Dishonest Profit Progression', fontweight='bold')
        axes[1, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[1, 1].grid(True, alpha=0.3, linestyle='--')
        
        # Bottom: Cross-run comparison (stacked bar chart for first temperature)
        if self.temperatures:
            first_temp = self.temperatures[0]
            exp_id = self.experiment_ids[first_temp]
            exp_dir = Path(f"experiments/{exp_id}")
            if exp_dir.exists():
                cross_run_data = self._prepare_cross_run_data(exp_id, exp_dir)
                if cross_run_data['run_ids']:
                    run_ids = cross_run_data['run_ids']
                    honest_profits = cross_run_data['honest_profits']
                    dishonest_profits = cross_run_data['dishonest_profits']
                    color = COLORS.get(first_temp, '#000000')
                    
                    axes[2, 0].bar(run_ids, honest_profits, alpha=0.7, 
                                  color='#2ca02c', label='Honest Profit', edgecolor='black')
                    axes[2, 0].bar(run_ids, dishonest_profits, 
                                  bottom=honest_profits, alpha=0.7,
                                  color='#d62728', label='Dishonest Profit', edgecolor='black')
                    axes[2, 0].set_xlabel('Run ID', fontweight='bold')
                    axes[2, 0].set_ylabel('Total Profit ($)', fontweight='bold')
                    axes[2, 0].set_title(f'Total Seller Profits (Temperature {first_temp})', fontweight='bold')
                    axes[2, 0].legend(frameon=True, fancybox=True, shadow=True)
                    axes[2, 0].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Bottom Right: Profit vs Utility scatter (for all temperatures)
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            exp_dir = Path(f"experiments/{exp_id}")
            if exp_dir.exists():
                cross_run_data = self._prepare_cross_run_data(exp_id, exp_dir)
                if cross_run_data['run_ids']:
                    color = COLORS.get(temp, '#000000')
                    axes[2, 1].scatter(cross_run_data['seller_profits'], cross_run_data['buyer_utilities'],
                                     alpha=0.7, s=60, color=color, edgecolors='black', linewidth=0.5,
                                     label=f'Temperature {temp}')
        
        axes[2, 1].set_xlabel('Total Seller Profit ($)', fontweight='bold')
        axes[2, 1].set_ylabel('Total Buyer Utility ($)', fontweight='bold')
        axes[2, 1].set_title('Seller Profits vs Buyer Utilities', fontweight='bold')
        axes[2, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[2, 1].grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '2_seller_profit.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 2_seller_profit.png")
    
    def plot_buyer_utility(self):
        """3. Buyer Utility Over Rounds (with detailed breakdowns)"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        all_rounds = set()
        temp_data = {}
        
        # Load data for each temperature
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            rounds_data = self._load_round_data_from_db(exp_id)
            
            if not rounds_data.empty and 'round' in rounds_data.columns:
                all_rounds.update(rounds_data['round'].unique())
                temp_data[temp] = rounds_data
        
        rounds = sorted(all_rounds) if all_rounds else []
        
        if not rounds:
            print("Warning: No rounds data available for buyer utility plot")
            return
        
        # Top Left: Line plot
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_data and not temp_data[temp].empty:
                agg = temp_data[temp].groupby('round')['buyer_utility'].agg(['mean', 'std']).reset_index()
                agg = agg.set_index('round').reindex(rounds).reset_index()
                agg['mean'] = agg['mean'].fillna(0)
                agg['std'] = agg['std'].fillna(0)
                
                axes[0, 0].errorbar(rounds, agg['mean'], yerr=agg['std'],
                                  fmt='o-', label=f'Temperature {temp}',
                                  color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        axes[0, 0].set_xlabel('Round', fontweight='bold')
        axes[0, 0].set_ylabel('Average Buyer Utility ($)', fontweight='bold')
        axes[0, 0].set_title('Buyer Utility Progression', fontweight='bold')
        axes[0, 0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        axes[0, 0].set_xticks(rounds)
        
        # Top Right: KDE distribution comparison
        all_utils_by_temp = {}
        for temp in self.temperatures:
            if temp in temp_data and not temp_data[temp].empty:
                all_utils_by_temp[temp] = temp_data[temp]['buyer_utility'].dropna().values
        
        if all_utils_by_temp:
            for temp, utils in all_utils_by_temp.items():
                if len(utils) > 1 and np.std(utils) > 1e-10:
                    color = COLORS.get(temp, '#000000')
                    kde = stats.gaussian_kde(utils)
                    x_range = np.linspace(utils.min(), utils.max(), 200)
                    axes[0, 1].plot(x_range, kde(x_range), label=f'Temperature {temp}',
                                  color=color, linewidth=2, alpha=0.7)
                    axes[0, 1].fill_between(x_range, kde(x_range), alpha=0.3, color=color)
                elif len(utils) > 0:
                    color = COLORS.get(temp, '#000000')
                    axes[0, 1].hist(utils, bins=20, alpha=0.5, label=f'Temperature {temp}',
                                  color=color, density=True, edgecolor='black', linewidth=0.5)
        
        axes[0, 1].set_xlabel('Buyer Utility ($)', fontweight='bold')
        axes[0, 1].set_ylabel('Density', fontweight='bold')
        axes[0, 1].set_title('Utility Distribution Comparison', fontweight='bold')
        axes[0, 1].legend(frameon=True, fancybox=True, shadow=True)
        axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Bottom Left: Cross-run comparison (for first temperature)
        if self.temperatures:
            first_temp = self.temperatures[0]
            exp_id = self.experiment_ids[first_temp]
            exp_dir = Path(f"experiments/{exp_id}")
            if exp_dir.exists():
                cross_run_data = self._prepare_cross_run_data(exp_id, exp_dir)
                if cross_run_data['run_ids']:
                    color = COLORS.get(first_temp, '#000000')
                    axes[1, 0].bar(cross_run_data['run_ids'], cross_run_data['buyer_utilities'],
                                  alpha=0.7, color=color, edgecolor='black')
                    axes[1, 0].axhline(y=np.mean(cross_run_data['buyer_utilities']),
                                      color='red', linestyle='--', linewidth=1.5,
                                      label=f'Mean: {np.mean(cross_run_data["buyer_utilities"]):.2f}')
                    axes[1, 0].set_xlabel('Run ID', fontweight='bold')
                    axes[1, 0].set_ylabel('Total Utility ($)', fontweight='bold')
                    axes[1, 0].set_title(f'Total Buyer Utilities (Temperature {first_temp})', fontweight='bold')
                    axes[1, 0].legend(frameon=True, fancybox=True, shadow=True)
                    axes[1, 0].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Bottom Right: Individual buyer utility (for first temperature, first run)
        if self.temperatures:
            first_temp = self.temperatures[0]
            exp_id = self.experiment_ids[first_temp]
            buyer_data = self._load_buyer_utility_by_round(exp_id)
            if not buyer_data.empty:
                buyer_ids = sorted(buyer_data['buyer_id'].unique())[:5]  # Limit to 5 buyers
                color = COLORS.get(first_temp, '#000000')
                for buyer_id in buyer_ids:
                    buyer_round_data = buyer_data[buyer_data['buyer_id'] == buyer_id].sort_values('round')
                    if not buyer_round_data.empty:
                        axes[1, 1].plot(buyer_round_data['round'], buyer_round_data['buyer_utility'],
                                      marker='o', linewidth=1.5, markersize=4, alpha=0.7,
                                      label=f'Buyer {buyer_id}')
                axes[1, 1].set_xlabel('Round', fontweight='bold')
                axes[1, 1].set_ylabel('Buyer Utility ($)', fontweight='bold')
                axes[1, 1].set_title(f'Individual Buyer Utility (Temperature {first_temp})', fontweight='bold')
                axes[1, 1].legend(frameon=True, fancybox=True, shadow=True, ncol=2, fontsize=8)
                axes[1, 1].grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '3_buyer_utility.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 3_buyer_utility.png")
    
    def plot_reputation(self):
        """4. Seller Reputation Over Rounds"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        all_rounds = set()
        temp_data = {}
        
        # Load data for each temperature
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            rounds_data = self._load_round_data_from_db(exp_id)
            
            if not rounds_data.empty and 'round' in rounds_data.columns:
                all_rounds.update(rounds_data['round'].unique())
                temp_data[temp] = rounds_data
        
        rounds = sorted(all_rounds) if all_rounds else []
        
        if not rounds:
            print("Warning: No rounds data available for reputation plot")
            return
        
        # Plot reputation for each temperature
        for temp in self.temperatures:
            color = COLORS.get(temp, '#000000')
            if temp in temp_data and not temp_data[temp].empty:
                agg = temp_data[temp].groupby('round')['avg_reputation'].agg(['mean', 'std']).reset_index()
                agg = agg.set_index('round').reindex(rounds).reset_index()
                agg['mean'] = agg['mean'].fillna(0)
                agg['std'] = agg['std'].fillna(0)
                
                ax.errorbar(rounds, agg['mean'], yerr=agg['std'],
                          fmt='o-', label=f'Temperature {temp}',
                          color=color, linewidth=2, markersize=6, capsize=3, alpha=0.7)
        
        ax.set_xlabel('Round', fontweight='bold')
        ax.set_ylabel('Average Reputation Score', fontweight='bold')
        ax.set_title('Seller Reputation Over Rounds', fontweight='bold', pad=15)
        ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xticks(rounds)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '4_reputation.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 4_reputation.png")
    
    def plot_total_market_metrics(self):
        """5. Total Market Metrics Comparison"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Prepare data
        metrics_data = []
        for temp in self.temperatures:
            if temp in self.data and self.data[temp]:
                stats = self.data[temp].get('summary_statistics', {})
                metrics_data.append({
                    'temperature': temp,
                    'total_profit': stats.get('total_seller_profit', 0),
                    'total_utility': stats.get('total_buyer_utility', 0),
                    'avg_price': stats.get('average_price', 0),
                    'total_transactions': stats.get('total_transactions', 0)
                })
        
        if not metrics_data:
            print("Warning: No aggregated statistics available")
            return
        
        df = pd.DataFrame(metrics_data)
        df['temperature'] = df['temperature'].astype(float)
        df = df.sort_values('temperature')
        
        # Plot 1: Total Profit
        axes[0, 0].bar(df['temperature'], df['total_profit'], 
                      color=[COLORS.get(str(t), '#000000') for t in df['temperature']],
                      alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[0, 0].set_xlabel('Temperature', fontweight='bold')
        axes[0, 0].set_ylabel('Total Seller Profit ($)', fontweight='bold')
        axes[0, 0].set_title('Total Seller Profit', fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Plot 2: Total Utility
        axes[0, 1].bar(df['temperature'], df['total_utility'],
                      color=[COLORS.get(str(t), '#000000') for t in df['temperature']],
                      alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[0, 1].set_xlabel('Temperature', fontweight='bold')
        axes[0, 1].set_ylabel('Total Buyer Utility ($)', fontweight='bold')
        axes[0, 1].set_title('Total Buyer Utility', fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Plot 3: Average Price
        axes[1, 0].bar(df['temperature'], df['avg_price'],
                      color=[COLORS.get(str(t), '#000000') for t in df['temperature']],
                      alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[1, 0].set_xlabel('Temperature', fontweight='bold')
        axes[1, 0].set_ylabel('Average Price ($)', fontweight='bold')
        axes[1, 0].set_title('Average Price', fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Plot 4: Total Transactions
        axes[1, 1].bar(df['temperature'], df['total_transactions'],
                      color=[COLORS.get(str(t), '#000000') for t in df['temperature']],
                      alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[1, 1].set_xlabel('Temperature', fontweight='bold')
        axes[1, 1].set_ylabel('Total Transactions', fontweight='bold')
        axes[1, 1].set_title('Total Transactions', fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '5_total_market_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Generated: 5_total_market_metrics.png")
    
    def generate_summary_statistics_table(self):
        """Generate Summary Statistics Table"""
        # Prepare data for each temperature
        all_data = {}
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            exp_dir = Path(f"experiments/{exp_id}")
            if exp_dir.exists():
                all_data[temp] = self._prepare_cross_run_data(exp_id, exp_dir)
        
        if not all_data:
            return
        
        # Calculate statistics for each temperature
        headers = ['Temperature', 'Buyer Utility (Mean ± Std)', 
                  'Seller Profit (Mean ± Std)', 'Transactions (Mean ± Std)',
                  'Deception Rate (Mean ± Std)', 'Market Efficiency (Mean ± Std)']
        
        rows = []
        
        for temp in self.temperatures:
            if temp not in all_data or not all_data[temp]['run_ids']:
                continue
            
            data = all_data[temp]
            utils = data['buyer_utilities']
            profits = data['seller_profits']
            tx = data['transaction_counts']
            deceptions = data['deceptions']
            efficiency = [u + p for u, p in zip(utils, profits)]
            
            rows.append([
                temp,
                f"{self._format_number(np.mean(utils), 1)} ± {self._format_number(np.std(utils), 1)}",
                f"{self._format_number(np.mean(profits), 1)} ± {self._format_number(np.std(profits), 1)}",
                f"{self._format_number(np.mean(tx), 1)} ± {self._format_number(np.std(tx), 1)}",
                f"{self._format_number(np.mean(deceptions), 1)} ± {self._format_number(np.std(deceptions), 1)}",
                f"{self._format_number(np.mean(efficiency), 1)} ± {self._format_number(np.std(efficiency), 1)}"
            ])
        
        if not rows:
            return
        
        # Generate markdown and LaTeX tables
        md_table = self._generate_markdown_table(headers, rows, 
                                                 "Summary Statistics Comparison by Temperature")
        latex_table = self._generate_latex_table(headers, rows,
                                                "Summary Statistics Comparison by Temperature",
                                                "tab:temp_summary_stats")
        
        # Save to file
        table_file = self.table_dir / f"{self.market_type}_summary_statistics.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print(f"✓ Generated: {table_file.name}")
        
        # Table 2: Summary Statistics with Gini Coefficient
        seller_gini_data = {}
        buyer_gini_data = {}
        seller_margin_data = {}
        buyer_margin_data = {}
        
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            seller_gini_mean, seller_gini_std = self._calculate_gini_by_run(exp_id, 'seller_profit')
            buyer_gini_mean, buyer_gini_std = self._calculate_gini_by_run(exp_id, 'buyer_utility')
            seller_gini_data[temp] = (seller_gini_mean, seller_gini_std)
            buyer_gini_data[temp] = (buyer_gini_mean, buyer_gini_std)
            
            # Calculate profit margins
            exp_dir = Path(f"experiments/{exp_id}")
            seller_margins = []
            buyer_margins = []
            
            for db_file in sorted(exp_dir.glob("run_*.db")):
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
                            seller_margins.extend(margins.tolist())
                        
                        buyer_utils = tx_data['buyer_utility'].values
                        valid_mask = prices > 0
                        if np.sum(valid_mask) > 0:
                            margins = buyer_utils[valid_mask] / prices[valid_mask]
                            buyer_margins.extend(margins.tolist())
                except Exception as e:
                    pass
            
            seller_margin_data[temp] = seller_margins
            buyer_margin_data[temp] = buyer_margins
        
        # New table structure
        headers2_row1 = ['Temperature', 'Transaction Count', 'Profit', 'Profit', 
                        'Profit margin', 'Profit margin', 'Gini Coefficient', 'Gini Coefficient']
        headers2_row2 = ['', '', 'Seller', 'Buyer', 'Seller', 'Buyer', 'Seller', 'Buyer']
        rows2 = []
        
        def format_mean_std(values):
            if len(values) == 0:
                return "N/A"
            mean = np.mean(values) if len(values) > 0 else 0.0
            std = np.std(values) if len(values) > 1 else 0.0
            return f"{self._format_number(mean, 1)}±{self._format_number(std, 1)}"
        
        for temp in self.temperatures:
            if temp not in all_data or not all_data[temp]['run_ids']:
                continue
            
            data = all_data[temp]
            tx = data['transaction_counts']
            profits = data['seller_profits']
            utils = data['buyer_utilities']
            
            rows2.append([
                temp,
                format_mean_std(tx),
                format_mean_std(profits),
                format_mean_std(utils),
                format_mean_std(seller_margin_data.get(temp, [])),
                format_mean_std(buyer_margin_data.get(temp, [])),
                f"{self._format_number(seller_gini_data[temp][0], 3)}",
                f"{self._format_number(buyer_gini_data[temp][0], 3)}"
            ])
        
        if rows2:
            md_table2 = self._generate_markdown_table_multi_level(headers2_row1, headers2_row2, rows2,
                                                  "Summary Statistics with Gini Coefficient")
            latex_table2 = self._generate_latex_table_multi_level_gini(headers2_row1, headers2_row2, rows2,
                                                    "Summary Statistics with Gini Coefficient",
                                                    "tab:temp_summary_stats_gini")
            
            with open(table_file, 'a', encoding='utf-8') as f:
                f.write("\n\n")
                f.write(md_table2)
                f.write("\n\n")
                f.write(latex_table2)
            
            print(f"✓ Updated: {table_file.name} (added Gini coefficient table)")
    
    def generate_round_comparison_table(self):
        """Generate Round-by-Round Comparison Table"""
        all_rounds_data = {}
        
        for temp in self.temperatures:
            exp_id = self.experiment_ids[temp]
            rounds_data = self._load_round_data_from_db(exp_id)
            if not rounds_data.empty:
                all_rounds_data[temp] = rounds_data
        
        if not all_rounds_data:
            return
        
        # Get all rounds
        all_rounds = set()
        for data in all_rounds_data.values():
            all_rounds.update(data['round'].unique())
        rounds = sorted(all_rounds)
        
        # Aggregate by round for each temperature
        temp_agg = {}
        for temp, data in all_rounds_data.items():
            temp_agg[temp] = data.groupby('round').agg({
                'buyer_utility': ['mean', 'std'],
                'seller_profit': ['mean', 'std'],
                'transactions': ['mean', 'std']
            }).reset_index()
        
        # Build headers and rows
        headers = ['Round']
        for temp in self.temperatures:
            headers.extend([f'T{temp}-Buyer Utility', f'T{temp}-Seller Profit', f'T{temp}-Transactions'])
        
        rows = []
        for round_num in rounds:
            row = [str(round_num)]
            for temp in self.temperatures:
                if temp in temp_agg:
                    round_data = temp_agg[temp][temp_agg[temp]['round'] == round_num]
                    if not round_data.empty:
                        row.append(f"{self._format_number(round_data[('buyer_utility', 'mean')].values[0])}")
                        row.append(f"{self._format_number(round_data[('seller_profit', 'mean')].values[0])}")
                        row.append(f"{self._format_number(round_data[('transactions', 'mean')].values[0], 1)}")
                    else:
                        row.extend(["N/A", "N/A", "N/A"])
                else:
                    row.extend(["N/A", "N/A", "N/A"])
            rows.append(row)
        
        # Generate markdown and LaTeX tables
        md_table = self._generate_markdown_table(headers, rows,
                                                "Round-by-Round Comparison by Temperature")
        latex_table = self._generate_latex_table(headers, rows,
                                                "Round-by-Round Comparison by Temperature",
                                                "tab:temp_round_comparison")
        
        # Save to file
        table_file = self.table_dir / f"{self.market_type}_round_comparison.md"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(md_table)
            f.write("\n\n")
            f.write(latex_table)
        
        print(f"✓ Generated: {table_file.name}")
    
    def generate_tables(self):
        """Generate all tables"""
        print()
        print("Generating tables...")
        self.generate_summary_statistics_table()
        self.generate_round_comparison_table()
        print(f"✓ All tables generated in: {self.table_dir}")
    
    def generate_all(self):
        """Generate all visualizations and tables"""
        print(f"Generating temperature comparison visualizations...")
        print(f"Market type: {self.market_type}")
        print(f"Temperatures: {', '.join(self.temperatures)}")
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
        self.generate_tables()


def main():
    parser = argparse.ArgumentParser(description='Generate temperature comparison visualizations')
    parser.add_argument('--market-type', dest='market_type', required=True,
                       choices=['r_wo', 'rw_wo'],
                       help='Market type: r_wo (Reputation-Only) or rw_wo (Reputation+Warrant)')
    parser.add_argument('--temps', dest='temperatures', nargs='+', required=True,
                       help='Temperature values (e.g., 0.0 0.5 1.0)')
    parser.add_argument('--exp-prefix', dest='exp_prefix', default='temperature/temp',
                       help='Experiment ID prefix (default: temperature/temp)')
    parser.add_argument('--out', dest='output_dir', default=None,
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Build experiment IDs dictionary
    experiment_ids = {}
    for temp in args.temperatures:
        exp_id = f"{args.exp_prefix}_{temp}/{args.market_type}"
        experiment_ids[temp] = exp_id
    
    visualizer = TempVisualizer(experiment_ids, args.market_type, args.output_dir)
    visualizer.generate_all()


if __name__ == "__main__":
    main()
