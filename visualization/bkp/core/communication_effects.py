"""
Visualization module for communication effects in rep-only market
Plots mean ± std with shaded areas, comparing 4 communication conditions
"""

import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import os
import glob
from typing import Dict, List, Tuple, Optional

# Configure matplotlib style
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 100

# Color scheme matching the reference image style
COLORS = {
    'no_com': '#1f77b4',      # Blue (solid)
    'buyer_com': '#ff7f0e',   # Orange (dashed)
    'seller_com': '#2ca02c',  # Green (dashed)
    'both_com': '#d62728'     # Red (dashed)
}

MARKERS = {
    'no_com': 'o',      # Circle
    'buyer_com': 's',   # Square
    'seller_com': '^',  # Triangle
    'both_com': 'x'     # X
}

LINESTYLES = {
    'no_com': '-',      # Solid
    'buyer_com': '--',  # Dashed
    'seller_com': '--', # Dashed
    'both_com': '--'    # Dashed
}

CONDITION_LABELS = {
    'no_com': 'No Communication',
    'buyer_com': 'Buyer Communication',
    'seller_com': 'Seller Communication',
    'both_com': 'Both Communication'
}


def extract_round_data_from_db(db_file: str) -> Dict[int, Dict]:
    """Extract per-round statistics from a single database file"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    round_data = defaultdict(lambda: {
        'seller_profit': [],
        'buyer_utility': [],
        'dishonest_count': 0,
        'total_transactions': 0,
        'ratings': [],
        'transaction_count': 0
    })
    
    try:
        # Extract seller profit and buyer utility per round
        cursor.execute("""
            SELECT round_number, seller_profit, buyer_utility, rating
            FROM transactions
            WHERE seller_profit IS NOT NULL AND buyer_utility IS NOT NULL
            ORDER BY round_number
        """)
        
        for row in cursor.fetchall():
            round_num, seller_profit, buyer_utility, rating = row
            if round_num:
                round_data[round_num]['seller_profit'].append(seller_profit or 0)
                round_data[round_num]['buyer_utility'].append(buyer_utility or 0)
                if rating is not None:
                    round_data[round_num]['ratings'].append(rating)
                round_data[round_num]['transaction_count'] += 1
        
        # Extract dishonest product count per round
        cursor.execute("""
            SELECT t.round_number, COUNT(*) as dishonest_count
            FROM transactions t
            JOIN product p ON t.product_id = p.product_id
            WHERE p.advertised_quality = 'HQ' AND p.true_quality = 'LQ'
            GROUP BY t.round_number
        """)
        
        for row in cursor.fetchall():
            round_num, count = row
            if round_num:
                round_data[round_num]['dishonest_count'] = count
        
        # Get total transactions per round
        cursor.execute("""
            SELECT round_number, COUNT(*) as total_count
            FROM transactions
            GROUP BY round_number
        """)
        
        for row in cursor.fetchall():
            round_num, count = row
            if round_num:
                round_data[round_num]['total_transactions'] = count
        
    finally:
        conn.close()
    
    return dict(round_data)


def plot_with_shaded_area(ax, rounds: List[int], mean_values: List[float], 
                          std_values: List[float], color: str, label: str,
                          marker: str, linestyle: str, alpha: float = 0.25):
    """Plot line with shaded area for mean ± std"""
    mean_values = np.array(mean_values)
    std_values = np.array(std_values)
    
    # Plot mean line with smaller markers
    ax.plot(rounds, mean_values, color=color, label=label, marker=marker,
            linestyle=linestyle, linewidth=2.5, markersize=4, zorder=3, 
            markeredgewidth=1, markeredgecolor='white')
    
    # Fill area for std
    ax.fill_between(rounds, mean_values - std_values, mean_values + std_values,
                    color=color, alpha=alpha, zorder=1, edgecolor='none')
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def create_communication_effects_plot(experiments_dir: str, output_file: str):
    """Create comprehensive plot comparing communication conditions"""
    
    # Pattern to match database files for each condition
    condition_patterns = {
        'no_com': 'reputation_only_none',
        'buyer_com': 'reputation_only_buyer',
        'seller_com': 'reputation_only_seller',
        'both_com': 'reputation_only_both'
    }
    
    # Aggregate data for each condition
    condition_data = {}
    for cond_name in condition_patterns.keys():
        # Find all matching database files in all experiment directories
        pattern = f"*{condition_patterns[cond_name]}.db"
        db_files = glob.glob(os.path.join(experiments_dir, 'exp_*', pattern))
        
        if not db_files:
            print(f"Warning: No files found for {cond_name} with pattern {pattern}")
            continue
        
        print(f"Found {len(db_files)} files for {cond_name}")
        
        # Aggregate across runs - collect per-run statistics
        runs_data = []
        all_rounds = set()
        
        for db_file in sorted(db_files):
            round_data = extract_round_data_from_db(db_file)
            all_rounds.update(round_data.keys())
            runs_data.append(round_data)
        
        # Calculate mean and std across runs for each round
        condition_data[cond_name] = {}
        for round_num in sorted(all_rounds):
            # Collect per-run values for this round
            seller_profit_sums = []
            buyer_utility_sums = []
            total_benefit_sums = []
            dishonest_counts = []
            transaction_counts = []
            rating_means = []
            dishonest_ratios = []
            
            for run_data in runs_data:
                if round_num in run_data:
                    data = run_data[round_num]
                    # Sum per run (not per transaction)
                    seller_sum = sum(data['seller_profit']) if data['seller_profit'] else 0
                    buyer_sum = sum(data['buyer_utility']) if data['buyer_utility'] else 0
                    seller_profit_sums.append(seller_sum)
                    buyer_utility_sums.append(buyer_sum)
                    total_benefit_sums.append(seller_sum + buyer_sum)
                    dishonest_counts.append(data['dishonest_count'])
                    transaction_counts.append(data['transaction_count'])
                    if data['ratings']:
                        rating_means.append(np.mean(data['ratings']))
                    # Calculate ratio for this run
                    if data['transaction_count'] > 0:
                        dishonest_ratios.append(data['dishonest_count'] / data['transaction_count'])
                    else:
                        dishonest_ratios.append(0)
            
            condition_data[cond_name][round_num] = {
                'seller_profit_mean': np.mean(seller_profit_sums) if seller_profit_sums else 0,
                'seller_profit_std': np.std(seller_profit_sums) if seller_profit_sums else 0,
                'buyer_utility_mean': np.mean(buyer_utility_sums) if buyer_utility_sums else 0,
                'buyer_utility_std': np.std(buyer_utility_sums) if buyer_utility_sums else 0,
                'total_benefit_mean': np.mean(total_benefit_sums) if total_benefit_sums else 0,
                'total_benefit_std': np.std(total_benefit_sums) if total_benefit_sums else 0,
                'dishonest_count_mean': np.mean(dishonest_counts) if dishonest_counts else 0,
                'dishonest_count_std': np.std(dishonest_counts) if dishonest_counts else 0,
                'transaction_count_mean': np.mean(transaction_counts) if transaction_counts else 0,
                'transaction_count_std': np.std(transaction_counts) if transaction_counts else 0,
                'rating_mean': np.mean(rating_means) if rating_means else 0,
                'rating_std': np.std(rating_means) if rating_means else 0,
                'dishonest_ratio_mean': np.mean(dishonest_ratios) if dishonest_ratios else 0,
                'dishonest_ratio_std': np.std(dishonest_ratios) if dishonest_ratios else 0
            }
    
    if not condition_data:
        print("Error: No data found for any condition")
        return
    
    # Get all rounds across all conditions
    all_rounds = set()
    for cond_data in condition_data.values():
        all_rounds.update(cond_data.keys())
    all_rounds = sorted(all_rounds)
    
    # Create figure with 6 subplots (2 rows x 3 columns)
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    # Plot 1: Seller Profit
    ax = axes[0]
    for cond_name in ['no_com', 'buyer_com', 'seller_com', 'both_com']:
        if cond_name in condition_data:
            rounds = [r for r in all_rounds if r in condition_data[cond_name]]
            means = [condition_data[cond_name][r]['seller_profit_mean'] for r in rounds]
            stds = [condition_data[cond_name][r]['seller_profit_std'] for r in rounds]
            
            plot_with_shaded_area(ax, rounds, means, stds,
                                COLORS[cond_name], CONDITION_LABELS[cond_name],
                                MARKERS[cond_name], LINESTYLES[cond_name])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Seller Profit', fontweight='bold')
    ax.set_title('Seller Profit Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 2: Buyer Utility
    ax = axes[1]
    for cond_name in ['no_com', 'buyer_com', 'seller_com', 'both_com']:
        if cond_name in condition_data:
            rounds = [r for r in all_rounds if r in condition_data[cond_name]]
            means = [condition_data[cond_name][r]['buyer_utility_mean'] for r in rounds]
            stds = [condition_data[cond_name][r]['buyer_utility_std'] for r in rounds]
            
            plot_with_shaded_area(ax, rounds, means, stds,
                                COLORS[cond_name], CONDITION_LABELS[cond_name],
                                MARKERS[cond_name], LINESTYLES[cond_name])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Buyer Utility', fontweight='bold')
    ax.set_title('Buyer Utility Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 3: Dishonest Product Count
    ax = axes[2]
    for cond_name in ['no_com', 'buyer_com', 'seller_com', 'both_com']:
        if cond_name in condition_data:
            rounds = [r for r in all_rounds if r in condition_data[cond_name]]
            means = [condition_data[cond_name][r]['dishonest_count_mean'] for r in rounds]
            stds = [condition_data[cond_name][r]['dishonest_count_std'] for r in rounds]
            
            plot_with_shaded_area(ax, rounds, means, stds,
                                COLORS[cond_name], CONDITION_LABELS[cond_name],
                                MARKERS[cond_name], LINESTYLES[cond_name])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Dishonest Product Count', fontweight='bold')
    ax.set_title('Dishonest Products Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 4: Transaction Rating
    ax = axes[3]
    for cond_name in ['no_com', 'buyer_com', 'seller_com', 'both_com']:
        if cond_name in condition_data:
            rounds = [r for r in all_rounds if r in condition_data[cond_name]]
            means = [condition_data[cond_name][r]['rating_mean'] for r in rounds]
            stds = [condition_data[cond_name][r]['rating_std'] for r in rounds]
            
            plot_with_shaded_area(ax, rounds, means, stds,
                                COLORS[cond_name], CONDITION_LABELS[cond_name],
                                MARKERS[cond_name], LINESTYLES[cond_name])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Transaction Rating', fontweight='bold')
    ax.set_title('Transaction Rating Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 5: Transaction Count
    ax = axes[4]
    for cond_name in ['no_com', 'buyer_com', 'seller_com', 'both_com']:
        if cond_name in condition_data:
            rounds = [r for r in all_rounds if r in condition_data[cond_name]]
            means = [condition_data[cond_name][r]['transaction_count_mean'] for r in rounds]
            stds = [condition_data[cond_name][r]['transaction_count_std'] for r in rounds]
            
            plot_with_shaded_area(ax, rounds, means, stds,
                                COLORS[cond_name], CONDITION_LABELS[cond_name],
                                MARKERS[cond_name], LINESTYLES[cond_name])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Transaction Count', fontweight='bold')
    ax.set_title('Transaction Count Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 6: Total Benefit (changed from Dishonest Ratio)
    ax = axes[5]
    for cond_name in ['no_com', 'buyer_com', 'seller_com', 'both_com']:
        if cond_name in condition_data:
            rounds = [r for r in all_rounds if r in condition_data[cond_name]]
            means = [condition_data[cond_name][r]['total_benefit_mean'] for r in rounds]
            stds = [condition_data[cond_name][r]['total_benefit_std'] for r in rounds]
            
            plot_with_shaded_area(ax, rounds, means, stds,
                                COLORS[cond_name], CONDITION_LABELS[cond_name],
                                MARKERS[cond_name], LINESTYLES[cond_name])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Total Benefit', fontweight='bold')
    ax.set_title('Total Benefit Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {output_file}")
    plt.close()

