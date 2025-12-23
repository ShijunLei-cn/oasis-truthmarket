#!/usr/bin/env python3
"""
RQ3 Visualization: Buyer Communication Effects
Analyze seller Fraud Attitude Tags and buyer Transaction Feedback from posts
"""

import sys
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import glob
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.core.communication_effects import plot_with_shaded_area

# Configure matplotlib style
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 100

# Color scheme for Fake vs Real
COLORS = {
    'fake': '#1f77b4',      # Blue
    'real': '#ff7f0e',      # Orange
}

MARKERS = {
    'fake': 'o',      # Circle
    'real': 's',      # Square
}

LINESTYLES = {
    'fake': '-',      # Solid
    'real': '--',     # Dashed
}

CONDITION_LABELS = {
    'fake': 'Fake Channel',
    'real': 'Real Channel'
}


def extract_posts_from_actions(actions_file: str) -> Dict[int, Dict]:
    """
    Extract post information from actions.json file
    
    Returns:
        Dictionary mapping round numbers to post statistics
    """
    round_data = defaultdict(lambda: {
        'seller_tags': {'Pro-Fraud': 0, 'Anti-Fraud': 0, 'Neutral': 0},
        'buyer_feedback': {'Fraudulent': 0, 'Honest': 0}
    })
    
    if not os.path.exists(actions_file):
        print(f"Warning: Actions file not found: {actions_file}")
        return {}
    
    with open(actions_file, 'r', encoding='utf-8') as f:
        actions = json.load(f)
    
    for action in actions:
        if action.get('action_name') == 'create_post':
            round_num = action.get('round')
            phase = action.get('phase', '')
            structured_info = action.get('action_args', {}).get('structured_info', '')
            
            if not round_num or not structured_info:
                continue
            
            # Seller communication: Fraud Attitude Tags
            if phase == 'seller_communication':
                if structured_info == '[Pro-Fraud]':
                    round_data[round_num]['seller_tags']['Pro-Fraud'] += 1
                elif structured_info == '[Anti-Fraud]':
                    round_data[round_num]['seller_tags']['Anti-Fraud'] += 1
                elif structured_info == '[Neutral]':
                    round_data[round_num]['seller_tags']['Neutral'] += 1
            
            # Buyer communication: Transaction Feedback
            elif phase == 'buyer_communication':
                # Parse feedback: "Seller_ID: [Fraudulent/Honest] - ..."
                if structured_info.startswith('Seller_'):
                    if ': Fraudulent' in structured_info or ': Fraudulent' in structured_info:
                        round_data[round_num]['buyer_feedback']['Fraudulent'] += 1
                    elif ': Honest' in structured_info or ': Honest' in structured_info:
                        round_data[round_num]['buyer_feedback']['Honest'] += 1
                    # Also check for variations
                    elif 'Fraudulent' in structured_info:
                        round_data[round_num]['buyer_feedback']['Fraudulent'] += 1
                    elif 'Honest' in structured_info and 'Honesty' not in structured_info:
                        round_data[round_num]['buyer_feedback']['Honest'] += 1
    
    return dict(round_data)


def aggregate_condition_data(experiments_dir: str, experiment_ids: List[str], 
                             market_type: str, communication_type: str) -> Dict[int, Dict]:
    """
    Aggregate post data for a specific condition across multiple experiment runs
    
    Args:
        experiments_dir: Base experiments directory
        experiment_ids: List of experiment IDs (e.g., ['r_wbc_F', 'r_wbc_R'])
        market_type: 'reputation_only' or 'reputation_and_warrant'
        communication_type: 'buyer' or 'seller'
        
    Returns:
        Dictionary mapping round numbers to aggregated statistics
    """
    all_actions_files = []
    
    for exp_id in experiment_ids:
        exp_dir = os.path.join(experiments_dir, exp_id)
        if not os.path.exists(exp_dir):
            print(f"Warning: Experiment directory not found: {exp_dir}")
            continue
        
        # Find all actions.json files in this experiment directory
        pattern = f"*{market_type}_{communication_type}_actions.json"
        actions_files = glob.glob(os.path.join(exp_dir, pattern))
        all_actions_files.extend(actions_files)
    
    if not all_actions_files:
        print(f"Warning: No actions files found for {experiment_ids}, {market_type}, {communication_type}")
        return {}
    
    print(f"Found {len(all_actions_files)} actions files")
    
    # Aggregate across runs
    runs_data = []
    all_rounds = set()
    
    for actions_file in sorted(all_actions_files):
        round_data = extract_posts_from_actions(actions_file)
        all_rounds.update(round_data.keys())
        runs_data.append(round_data)
    
    # Calculate mean and std across runs for each round
    aggregated = {}
    for round_num in sorted(all_rounds):
        pro_fraud_counts = []
        anti_fraud_counts = []
        neutral_counts = []
        fraudulent_feedback_counts = []
        honest_feedback_counts = []
        
        for run_data in runs_data:
            if round_num in run_data:
                data = run_data[round_num]
                pro_fraud_counts.append(data['seller_tags']['Pro-Fraud'])
                anti_fraud_counts.append(data['seller_tags']['Anti-Fraud'])
                neutral_counts.append(data['seller_tags']['Neutral'])
                fraudulent_feedback_counts.append(data['buyer_feedback']['Fraudulent'])
                honest_feedback_counts.append(data['buyer_feedback']['Honest'])
        
        aggregated[round_num] = {
            'pro_fraud_mean': np.mean(pro_fraud_counts) if pro_fraud_counts else 0,
            'pro_fraud_std': np.std(pro_fraud_counts) if pro_fraud_counts else 0,
            'anti_fraud_mean': np.mean(anti_fraud_counts) if anti_fraud_counts else 0,
            'anti_fraud_std': np.std(anti_fraud_counts) if anti_fraud_counts else 0,
            'neutral_mean': np.mean(neutral_counts) if neutral_counts else 0,
            'neutral_std': np.std(neutral_counts) if neutral_counts else 0,
            'fraudulent_feedback_mean': np.mean(fraudulent_feedback_counts) if fraudulent_feedback_counts else 0,
            'fraudulent_feedback_std': np.std(fraudulent_feedback_counts) if fraudulent_feedback_counts else 0,
            'honest_feedback_mean': np.mean(honest_feedback_counts) if honest_feedback_counts else 0,
            'honest_feedback_std': np.std(honest_feedback_counts) if honest_feedback_counts else 0,
        }
    
    return aggregated


def create_rq3_plot(experiments_dir: str, output_file: str):
    """
    Create RQ3 visualization: Buyer Communication Effects
    Analyze seller Fraud Attitude Tags and buyer Transaction Feedback
    """
    
    # Define experiment IDs
    r_fake_id = 'r_wbc_F'
    r_real_id = 'r_wbc_R'
    rw_fake_id = 'rw_wbc_F'
    rw_real_id = 'rw_wbc_R'
    
    # Aggregate data for each condition
    # Note: For buyer communication experiments, we analyze both seller tags and buyer feedback
    condition_data = {
        'r_fake': aggregate_condition_data(experiments_dir, [r_fake_id], 
                                          'reputation_only', 'buyer'),
        'r_real': aggregate_condition_data(experiments_dir, [r_real_id], 
                                          'reputation_only', 'buyer'),
        'rw_fake': aggregate_condition_data(experiments_dir, [rw_fake_id], 
                                            'reputation_and_warrant', 'buyer'),
        'rw_real': aggregate_condition_data(experiments_dir, [rw_real_id], 
                                             'reputation_and_warrant', 'buyer'),
    }
    
    # Get all rounds
    all_rounds = set()
    for cond_data in condition_data.values():
        all_rounds.update(cond_data.keys())
    all_rounds = sorted(all_rounds)
    
    # Create figure with 6 subplots (2 rows x 3 columns)
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    # Plot 1: Seller Pro-Fraud Tags
    ax = axes[0]
    for channel_type in ['fake', 'real']:
        for market_prefix in ['r', 'rw']:
            cond_key = f'{market_prefix}_{channel_type}'
            if cond_key in condition_data and condition_data[cond_key]:
                rounds = [r for r in all_rounds if r in condition_data[cond_key]]
                means = [condition_data[cond_key][r]['pro_fraud_mean'] for r in rounds]
                stds = [condition_data[cond_key][r]['pro_fraud_std'] for r in rounds]
                
                label = f"{market_prefix.upper()}-{CONDITION_LABELS[channel_type]}"
                plot_with_shaded_area(ax, rounds, means, stds,
                                    COLORS[channel_type], label,
                                    MARKERS[channel_type], LINESTYLES[channel_type])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Pro-Fraud Tag Count', fontweight='bold')
    ax.set_title('Seller Pro-Fraud Attitude Tags Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 2: Seller Anti-Fraud Tags
    ax = axes[1]
    for channel_type in ['fake', 'real']:
        for market_prefix in ['r', 'rw']:
            cond_key = f'{market_prefix}_{channel_type}'
            if cond_key in condition_data and condition_data[cond_key]:
                rounds = [r for r in all_rounds if r in condition_data[cond_key]]
                means = [condition_data[cond_key][r]['anti_fraud_mean'] for r in rounds]
                stds = [condition_data[cond_key][r]['anti_fraud_std'] for r in rounds]
                
                label = f"{market_prefix.upper()}-{CONDITION_LABELS[channel_type]}"
                plot_with_shaded_area(ax, rounds, means, stds,
                                    COLORS[channel_type], label,
                                    MARKERS[channel_type], LINESTYLES[channel_type])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Anti-Fraud Tag Count', fontweight='bold')
    ax.set_title('Seller Anti-Fraud Attitude Tags Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 3: Seller Neutral Tags
    ax = axes[2]
    for channel_type in ['fake', 'real']:
        for market_prefix in ['r', 'rw']:
            cond_key = f'{market_prefix}_{channel_type}'
            if cond_key in condition_data and condition_data[cond_key]:
                rounds = [r for r in all_rounds if r in condition_data[cond_key]]
                means = [condition_data[cond_key][r]['neutral_mean'] for r in rounds]
                stds = [condition_data[cond_key][r]['neutral_std'] for r in rounds]
                
                label = f"{market_prefix.upper()}-{CONDITION_LABELS[channel_type]}"
                plot_with_shaded_area(ax, rounds, means, stds,
                                    COLORS[channel_type], label,
                                    MARKERS[channel_type], LINESTYLES[channel_type])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Neutral Tag Count', fontweight='bold')
    ax.set_title('Seller Neutral Attitude Tags Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 4: Buyer Fraudulent Feedback
    ax = axes[3]
    for channel_type in ['fake', 'real']:
        for market_prefix in ['r', 'rw']:
            cond_key = f'{market_prefix}_{channel_type}'
            if cond_key in condition_data and condition_data[cond_key]:
                rounds = [r for r in all_rounds if r in condition_data[cond_key]]
                means = [condition_data[cond_key][r]['fraudulent_feedback_mean'] for r in rounds]
                stds = [condition_data[cond_key][r]['fraudulent_feedback_std'] for r in rounds]
                
                label = f"{market_prefix.upper()}-{CONDITION_LABELS[channel_type]}"
                plot_with_shaded_area(ax, rounds, means, stds,
                                    COLORS[channel_type], label,
                                    MARKERS[channel_type], LINESTYLES[channel_type])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Fraudulent Feedback Count', fontweight='bold')
    ax.set_title('Buyer Fraudulent Transaction Feedback Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 5: Buyer Honest Feedback
    ax = axes[4]
    for channel_type in ['fake', 'real']:
        for market_prefix in ['r', 'rw']:
            cond_key = f'{market_prefix}_{channel_type}'
            if cond_key in condition_data and condition_data[cond_key]:
                rounds = [r for r in all_rounds if r in condition_data[cond_key]]
                means = [condition_data[cond_key][r]['honest_feedback_mean'] for r in rounds]
                stds = [condition_data[cond_key][r]['honest_feedback_std'] for r in rounds]
                
                label = f"{market_prefix.upper()}-{CONDITION_LABELS[channel_type]}"
                plot_with_shaded_area(ax, rounds, means, stds,
                                    COLORS[channel_type], label,
                                    MARKERS[channel_type], LINESTYLES[channel_type])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Honest Feedback Count', fontweight='bold')
    ax.set_title('Buyer Honest Transaction Feedback Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    # Plot 6: Total Feedback (Fraudulent + Honest)
    ax = axes[5]
    for channel_type in ['fake', 'real']:
        for market_prefix in ['r', 'rw']:
            cond_key = f'{market_prefix}_{channel_type}'
            if cond_key in condition_data and condition_data[cond_key]:
                rounds = [r for r in all_rounds if r in condition_data[cond_key]]
                fraudulent_means = [condition_data[cond_key][r]['fraudulent_feedback_mean'] for r in rounds]
                honest_means = [condition_data[cond_key][r]['honest_feedback_mean'] for r in rounds]
                means = [f + h for f, h in zip(fraudulent_means, honest_means)]
                # Approximate std as sum of individual stds
                fraudulent_stds = [condition_data[cond_key][r]['fraudulent_feedback_std'] for r in rounds]
                honest_stds = [condition_data[cond_key][r]['honest_feedback_std'] for r in rounds]
                stds = [np.sqrt(f**2 + h**2) for f, h in zip(fraudulent_stds, honest_stds)]
                
                label = f"{market_prefix.upper()}-{CONDITION_LABELS[channel_type]}"
                plot_with_shaded_area(ax, rounds, means, stds,
                                    COLORS[channel_type], label,
                                    MARKERS[channel_type], LINESTYLES[channel_type])
    
    ax.set_xlabel('Round', fontweight='bold')
    ax.set_ylabel('Total Feedback Count', fontweight='bold')
    ax.set_title('Total Buyer Transaction Feedback Over Rounds', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(all_rounds[::2] if len(all_rounds) > 10 else all_rounds)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved RQ3 plot to {output_file}")
    plt.close()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate RQ3 visualization: Buyer Communication Effects'
    )
    parser.add_argument(
        '--experiments-dir',
        default='experiments',
        help='Base experiments directory (default: experiments)'
    )
    parser.add_argument(
        '--output',
        default='experiments/RQ3_buyer_communication_effects.png',
        help='Output file path'
    )
    
    args = parser.parse_args()
    
    create_rq3_plot(args.experiments_dir, args.output)


if __name__ == '__main__':
    main()
