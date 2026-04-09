#!/usr/bin/env python3
"""
Collusion 2x2 Analysis: Communication vs Behavior
Analyzes the relationship between collusive messaging and deceptive behavior.
"""

import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple

DATA_DIR = Path("data/case_analysis")
OUTPUT_DIR = Path("visualization/figs/paper/collusion_analysis")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_posts():
    """Load labeled posts data."""
    posts = []
    with open(DATA_DIR / "posts_labeled.jsonl", 'r') as f:
        for line in f:
            if line.strip():
                posts.append(json.loads(line.strip()))
    return posts

def get_condition_group(experiment_id: str) -> str:
    """Map experiment_id to condition group."""
    if experiment_id.startswith('r_wsc_F_'):
        return 'Rep_NoComm'
    elif experiment_id.startswith('r_wsc_R_'):
        return 'Rep_Comm'
    elif experiment_id.startswith('rw_wsc_F_'):
        return 'Warrant_NoComm'
    elif experiment_id.startswith('rw_wsc_R_'):
        return 'Warrant_Comm'
    return 'Unknown'

def get_2x2_category(post: dict) -> str:
    """
    Classify each post into 2x2 categories:
    - Communication (Post): Did the post contain collusive messaging? (types 1-4)
    - Behavior: Did the seller engage in deceptive listing?
    
    Categories:
    - Honest: No collusive post + No deception
    - Hidden Deception: No collusive post + Deception
    - Verbal Collusion: Collusive post + No deception
    - Coordinated Deception: Collusive post + Deception
    """
    collusive_post = post['primary_type'] in [1, 2, 3, 4]
    deceptive_behavior = bool(post['deceptive_listing'])
    
    if not collusive_post and not deceptive_behavior:
        return 'Honest'
    elif not collusive_post and deceptive_behavior:
        return 'Hidden_Deception'
    elif collusive_post and not deceptive_behavior:
        return 'Verbal_Collusion'
    else:  # collusive_post and deceptive_behavior
        return 'Coordinated_Deception'

def analyze_2x2(posts):
    """Perform 2x2 analysis by condition and communication channel."""
    
    # Group by condition
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    stats = {cond: defaultdict(int) for cond in conditions}
    
    for post in posts:
        cond = get_condition_group(post['experiment_id'])
        if cond == 'Unknown':
            continue
        
        category = get_2x2_category(post)
        stats[cond][category] += 1
    
    # Calculate percentages
    print("=" * 80)
    print("2x2 COLLUSION ANALYSIS: Communication vs Behavior")
    print("=" * 80)
    print("\nCategories:")
    print("  - Honest: No collusive post + No deception")
    print("  - Hidden Deception: No collusive post + Deception") 
    print("  - Verbal Collusion: Collusive post + No deception")
    print("  - Coordinated Deception: Collusive post + Deception")
    print()
    
    # Print table
    headers = ["Condition", "Honest", "Hidden Deception", "Verbal Collusion", "Coordinated", "Total"]
    print(f"{'Condition':<20} {'Honest':>12} {'Hidden':>12} {'Verbal':>12} {'Coordinated':>12} {'Total':>8}")
    print("-" * 80)
    
    results = {}
    for cond in conditions:
        total = sum(stats[cond].values())
        if total == 0:
            continue
        
        honest = stats[cond].get('Honest', 0)
        hidden = stats[cond].get('Hidden_Deception', 0)
        verbal = stats[cond].get('Verbal_Collusion', 0)
        coordinated = stats[cond].get('Coordinated_Deception', 0)
        
        results[cond] = {
            'total': total,
            'honest': honest / total * 100,
            'hidden': hidden / total * 100,
            'verbal': verbal / total * 100,
            'coordinated': coordinated / total * 100
        }
        
        print(f"{cond:<20} {honest/total*100:>10.1f}% {hidden/total*100:>10.1f}% {verbal/total*100:>10.1f}% {coordinated/total*100:>10.1f}% {total:>6}")
    
    return results

def create_visualization(results):
    """Create visualization for the 2x2 analysis."""
    
    # Define categories and order
    categories = ['Honest', 'Hidden_Deception', 'Verbal_Collusion', 'Coordinated_Deception']
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    condition_labels = ['Rep\n(No Comm)', 'Rep\n(Comm)', 'Warrant\n(No Comm)', 'Warrant\n(Comm)']
    
    # Colors for each category
    colors = {
        'Honest': '#52B788',           # Green - honest
        'Hidden_Deception': '#E09B70',  # Orange - hidden
        'Verbal_Collusion': '#D4866A',  # Terracotta - verbal
        'Coordinated_Deception': '#AE2012'  # Red - coordinated
    }
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # --- Subplot 1: Stacked bar chart ---
    ax1 = axes[0]
    x = np.arange(len(conditions))
    width = 0.6
    
    bottom = np.zeros(len(conditions))
    # Map category names to result keys
    key_map = {
        'Honest': 'honest',
        'Hidden_Deception': 'hidden', 
        'Verbal_Collusion': 'verbal',
        'Coordinated_Deception': 'coordinated'
    }
    for cat in categories:
        values = [results[cond][key_map[cat]] for cond in conditions]
        
        bars = ax1.bar(x, values, width, bottom=bottom, label=cat, color=colors[cat], edgecolor='white', linewidth=0.5)
        
        # Add percentage labels
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 5:
                ax1.text(x[i], bot + val/2, f'{val:.1f}%', ha='center', va='center', 
                        fontsize=8, color='white', fontweight='bold')
        
        bottom += values
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(condition_labels, fontsize=10)
    ax1.set_ylabel('Percentage (%)', fontsize=11)
    ax1.set_title('2x2 Collusion Categories by Condition', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 105)
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)
    ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
    
    # --- Subplot 2: Deception rate comparison ---
    ax2 = axes[1]
    
    # Calculate total deception rates
    deception_rates = []
    for cond in conditions:
        hidden = results[cond]['hidden']
        coordinated = results[cond]['coordinated']
        deception_rates.append(hidden + coordinated)
    
    bars = ax2.bar(x, deception_rates, width=0.5, color=['#6B6B6B', '#9B2226', '#6B6B6B', '#9B2226'], 
                   edgecolor='white', linewidth=0.5)
    
    # Add value labels
    for bar, rate in zip(bars, deception_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(condition_labels, fontsize=10)
    ax2.set_ylabel('Deception Rate (%)', fontsize=11)
    ax2.set_title('Total Deception Rate\n(Hidden + Coordinated)', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, max(deception_rates) * 1.2)
    
    # Add connecting lines for communication effect
    # Rep: No Comm -> Comm
    ax2.plot([0, 1], [deception_rates[0], deception_rates[1]], 'b--', alpha=0.5, linewidth=1.5)
    ax2.annotate('', xy=(1, deception_rates[1]), xytext=(0, deception_rates[0]),
                arrowprops=dict(arrowstyle='->', color='blue', alpha=0.5))
    
    # Warrant: No Comm -> Comm
    ax2.plot([2, 3], [deception_rates[2], deception_rates[3]], 'b--', alpha=0.5, linewidth=1.5)
    
    # Add percentage change annotations
    rep_change = (deception_rates[1] - deception_rates[0]) / deception_rates[0] * 100
    w_change = (deception_rates[3] - deception_rates[2]) / deception_rates[2] * 100
    
    ax2.text(0.5, max(deception_rates) * 0.5, f'Rep: {rep_change:+.1f}%', 
            ha='center', fontsize=9, color='blue', style='italic')
    ax2.text(2.5, max(deception_rates) * 0.5, f'Warrant: {w_change:+.1f}%', 
            ha='center', fontsize=9, color='blue', style='italic')
    
    plt.tight_layout()
    
    # Save figure
    output_path = OUTPUT_DIR / "fig4_2x2_collusion_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nVisualization saved to: {output_path}")
    
    return output_path


def create_hidden_deception_analysis(posts):
    """
    Create fig4_1_2x2 focusing on Hidden Deception analysis.
    
    This visualization shows:
    1. Hidden Deception rate by condition (stacked breakdown)
    2. Communication effect on Hidden Deception
    3. Breakdown by prompt type
    """
    from collections import defaultdict, Counter
    import matplotlib.pyplot as plt
    import numpy as np
    
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    condition_labels = ['Rep\n(No Comm)', 'Rep\n(Comm)', 'Rep+Warrant\n(No Comm)', 'Rep+Warrant\n(Comm)']
    
    # Colors
    COLORS = {
        'hidden': '#E09B70',      # Orange - Hidden Deception
        'verbal': '#D4866A',       # Terracotta - Verbal Collusion  
        'coordinated': '#AE2012', # Red - Coordinated
        'honest': '#52B788',       # Green - Honest
    }
    
    # Group posts by condition
    stats = {cond: defaultdict(int) for cond in conditions}
    prompt_stats = {cond: defaultdict(lambda: defaultdict(int)) for cond in conditions}
    
    for post in posts:
        cond = get_condition_group(post['experiment_id'])
        if cond == 'Unknown':
            continue
        
        category = get_2x2_category(post)
        stats[cond][category] += 1
        
        # Also track by prompt type
        prompt_type = post.get('post_prompt_type', 'unknown')
        if category == 'Hidden_Deception':
            prompt_stats[cond][prompt_type]['hidden'] += 1
        prompt_stats[cond][prompt_type]['total'] += 1
    
    # Calculate totals
    totals = {cond: sum(stats[cond].values()) for cond in conditions}
    
    # Calculate percentages
    results = {}
    for cond in conditions:
        total = totals[cond]
        if total == 0:
            continue
        results[cond] = {
            'hidden': stats[cond].get('Hidden_Deception', 0) / total * 100,
            'verbal': stats[cond].get('Verbal_Collusion', 0) / total * 100,
            'coordinated': stats[cond].get('Coordinated_Deception', 0) / total * 100,
            'honest': stats[cond].get('Honest', 0) / total * 100,
        }
    
    print("\n" + "="*80)
    print("FIG4_1_2x2: HIDDEN DECEPTION ANALYSIS")
    print("="*80)
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Hidden Deception Analysis: Communication Effect by Market Type', 
                 fontsize=13, fontweight='bold', y=1.02)
    
    # --- Subplot 1: Hidden Deception focused stacked bars ---
    ax1 = axes[0]
    x = np.arange(len(conditions))
    width = 0.6
    
    # Focus on deception categories only (reorder for better visualization)
    deception_cats = ['Hidden_Deception', 'Verbal_Collusion', 'Coordinated_Deception']
    cat_labels = ['Hidden\nDeception', 'Verbal\nCollusion', 'Coordinated\nDeception']
    cat_keys = ['hidden', 'verbal', 'coordinated']
    cat_colors = [COLORS['hidden'], COLORS['verbal'], COLORS['coordinated']]
    
    bottom = np.zeros(len(conditions))
    for cat, cat_key, color, label in zip(deception_cats, cat_keys, cat_colors, cat_labels):
        values = [results[cond][cat_key] for cond in conditions]
        bars = ax1.bar(x, values, width, bottom=bottom, label=label, color=color, 
                       edgecolor='white', linewidth=0.5)
        
        # Add percentage labels
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 2:  # Only show if > 2%
                ax1.text(x[i], bot + val/2, f'{val:.1f}%', ha='center', va='center', 
                        fontsize=8, color='white', fontweight='bold')
        
        bottom += values
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(condition_labels, fontsize=10)
    ax1.set_ylabel('Percentage of Posts (%)', fontsize=11)
    ax1.set_title('Deception Categories by Condition\n(Excluding Honest)', fontsize=11, fontweight='bold')
    ax1.set_ylim(0, 30)  # Focus on lower range since we're excluding honest
    ax1.legend(loc='upper right', fontsize=9)
    
    # Add grid
    ax1.grid(True, axis='y', alpha=0.3, linestyle=':')
    
    # --- Subplot 2: Communication effect on Hidden Deception ---
    ax2 = axes[1]
    
    hidden_rates = [results[cond]['hidden'] for cond in conditions]
    
    # Create grouped bars for Rep vs Warrant comparison
    groups = [('Rep', [results['Rep_NoComm']['hidden'], results['Rep_Comm']['hidden']]),
              ('Rep+Warrant', [results['Warrant_NoComm']['hidden'], results['Warrant_Comm']['hidden']])]
    
    x_pos = np.array([0, 1, 3, 4])
    bar_width = 0.7
    
    # No Comm bars
    no_comm_values = [results['Rep_NoComm']['hidden'], results['Warrant_NoComm']['hidden']]
    comm_values = [results['Rep_Comm']['hidden'], results['Warrant_Comm']['hidden']]
    
    bars1 = ax2.bar(x_pos[:2], no_comm_values, bar_width, label='No Communication', 
                    color='#6B6B6B', edgecolor='white')
    bars2 = ax2.bar(x_pos[2:], comm_values, bar_width, label='With Communication', 
                    color='#9B2226', edgecolor='white')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, height + 0.2, 
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Add connecting lines showing communication effect
    # Rep effect
    ax2.annotate('', xy=(1, results['Rep_Comm']['hidden']), 
                xytext=(0, results['Rep_NoComm']['hidden']),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
    rep_effect = results['Rep_Comm']['hidden'] - results['Rep_NoComm']['hidden']
    ax2.text(0.5, max(results['Rep_NoComm']['hidden'], results['Rep_Comm']['hidden']) + 1.5, 
             f'{rep_effect:+.1f}%', ha='center', fontsize=9, color='blue', fontweight='bold')
    
    # Warrant effect
    ax2.annotate('', xy=(4, results['Warrant_Comm']['hidden']), 
                xytext=(3, results['Warrant_NoComm']['hidden']),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
    warrant_effect = results['Warrant_Comm']['hidden'] - results['Warrant_NoComm']['hidden']
    ax2.text(3.5, max(results['Warrant_NoComm']['hidden'], results['Warrant_Comm']['hidden']) + 1.5, 
             f'{warrant_effect:+.1f}%', ha='center', fontsize=9, color='green', fontweight='bold')
    
    ax2.set_xticks([0.5, 3.5])
    ax2.set_xticklabels(['Rep Only', 'Rep + Warrant'], fontsize=11)
    ax2.set_ylabel('Hidden Deception Rate (%)', fontsize=11)
    ax2.set_title('Communication Effect on Hidden Deception', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 15)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, axis='y', alpha=0.3, linestyle=':')
    
    # Add horizontal dashed line at overall average
    avg_hidden = np.mean(hidden_rates)
    ax2.axhline(y=avg_hidden, color='gray', linestyle='--', alpha=0.5, label=f'Avg: {avg_hidden:.1f}%')
    
    plt.tight_layout()
    
    # Save figure
    output_path = OUTPUT_DIR / "fig4_1_2x2_hidden_deception_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nHidden Deception analysis saved to: {output_path}")
    
    # Print summary stats
    print("\n" + "-"*60)
    print("KEY FINDINGS:")
    print("-"*60)
    print(f"Hidden Deception Rates:")
    print(f"  Rep (No Comm):    {results['Rep_NoComm']['hidden']:.1f}%")
    print(f"  Rep (Comm):       {results['Rep_Comm']['hidden']:.1f}%")
    print(f"  Comm Effect Rep:  {rep_effect:+.1f}%")
    print()
    print(f"  Warrant (No Comm): {results['Warrant_NoComm']['hidden']:.1f}%")
    print(f"  Warrant (Comm):    {results['Warrant_Comm']['hidden']:.1f}%")
    print(f"  Comm Effect Warr: {warrant_effect:+.1f}%")
    print()
    print(f"Warrant reduces Hidden Deception by: {results['Rep_NoComm']['hidden'] - results['Warrant_NoComm']['hidden']:.1f}% (absolute)")
    print(f"                          {((results['Rep_NoComm']['hidden'] - results['Warrant_NoComm']['hidden']) / results['Rep_NoComm']['hidden'] * 100):.1f}% (relative)")
    
    return output_path


def create_fig5_absolute_counts(posts):
    """
    Create fig5: Absolute counts version of fig4_2x2.
    
    Same structure as fig4_2x2 but showing absolute numbers instead of percentages.
    """
    from collections import defaultdict
    
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    condition_labels = ['Rep\n(No Comm)', 'Rep\n(Comm)', 'Rep+Warrant\n(No Comm)', 'Rep+Warrant\n(Comm)']
    
    # Colors for each category
    colors = {
        'Honest': '#52B788',           # Green - honest
        'Hidden_Deception': '#E09B70',  # Orange - hidden
        'Verbal_Collusion': '#D4866A',  # Terracotta - verbal
        'Coordinated_Deception': '#AE2012'  # Red - coordinated
    }
    
    # Group posts by condition and category
    stats = {cond: defaultdict(int) for cond in conditions}
    
    for post in posts:
        cond = get_condition_group(post['experiment_id'])
        if cond == 'Unknown':
            continue
        category = get_2x2_category(post)
        stats[cond][category] += 1
    
    # Calculate totals
    totals = {cond: sum(stats[cond].values()) for cond in conditions}
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # --- Subplot 1: Stacked bar chart with absolute counts ---
    ax1 = axes[0]
    x = np.arange(len(conditions))
    width = 0.6
    
    categories = ['Honest', 'Hidden_Deception', 'Verbal_Collusion', 'Coordinated_Deception']
    
    bottom = np.zeros(len(conditions))
    for cat in categories:
        values = [stats[cond][cat] for cond in conditions]
        
        bars = ax1.bar(x, values, width, bottom=bottom, label=cat, color=colors[cat], 
                       edgecolor='white', linewidth=0.5)
        
        # Add count labels
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 50:  # Only show if > 50
                ax1.text(x[i], bot + val/2, f'{int(val)}', ha='center', va='center', 
                        fontsize=8, color='white', fontweight='bold')
        
        bottom += values
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(condition_labels, fontsize=10)
    ax1.set_ylabel('Number of Posts', fontsize=11)
    ax1.set_title('2x2 Collusion Categories by Condition\n(Absolute Counts)', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, max(bottom) * 1.1)
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)
    
    # --- Subplot 2: Total deception counts ---
    ax2 = axes[1]
    
    # Calculate total deception counts
    deception_counts = []
    for cond in conditions:
        hidden = stats[cond].get('Hidden_Deception', 0)
        coordinated = stats[cond].get('Coordinated_Deception', 0)
        deception_counts.append(hidden + coordinated)
    
    bars = ax2.bar(x, deception_counts, width=0.5, 
                   color=['#6B6B6B', '#9B2226', '#6B6B6B', '#9B2226'], 
                   edgecolor='white', linewidth=0.5)
    
    # Add value labels
    for bar, count in zip(bars, deception_counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                f'{int(count)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(condition_labels, fontsize=10)
    ax2.set_ylabel('Number of Deceptive Posts', fontsize=11)
    ax2.set_title('Total Deception Count\n(Hidden + Coordinated)', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, max(deception_counts) * 1.2)
    
    # Add connecting lines for communication effect
    ax2.plot([0, 1], [deception_counts[0], deception_counts[1]], 'b--', alpha=0.5, linewidth=1.5)
    ax2.plot([2, 3], [deception_counts[2], deception_counts[3]], 'b--', alpha=0.5, linewidth=1.5)
    
    # Add count change annotations
    rep_change = deception_counts[1] - deception_counts[0]
    w_change = deception_counts[3] - deception_counts[2]
    
    ax2.text(0.5, max(deception_counts) * 0.5, f'Rep: {rep_change:+d}', 
            ha='center', fontsize=9, color='blue', style='italic')
    ax2.text(2.5, max(deception_counts) * 0.5, f'Warrant: {w_change:+d}', 
            ha='center', fontsize=9, color='blue', style='italic')
    
    plt.tight_layout()
    
    # Save figure
    output_path = OUTPUT_DIR / "fig5_absolute_counts.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nfig5 (absolute counts) saved to: {output_path}")
    
    return output_path


def create_fig5_1_hidden_deception_absolute(posts):
    """
    Create fig5_1: Absolute counts version of fig4_1_2x2.
    
    Focuses on Hidden Deception analysis with absolute counts instead of percentages.
    """
    from collections import defaultdict
    
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    condition_labels = ['Rep\n(No Comm)', 'Rep\n(Comm)', 'Rep+Warrant\n(No Comm)', 'Rep+Warrant\n(Comm)']
    
    # Colors
    COLORS = {
        'hidden': '#E09B70',      # Orange - Hidden Deception
        'verbal': '#D4866A',       # Terracotta - Verbal Collusion  
        'coordinated': '#AE2012', # Red - Coordinated
        'honest': '#52B788',       # Green - Honest
    }
    
    # Group posts by condition
    stats = {cond: defaultdict(int) for cond in conditions}
    
    for post in posts:
        cond = get_condition_group(post['experiment_id'])
        if cond == 'Unknown':
            continue
        category = get_2x2_category(post)
        stats[cond][category] += 1
    
    # Calculate totals
    totals = {cond: sum(stats[cond].values()) for cond in conditions}
    
    print("\n" + "="*80)
    print("FIG5_1: HIDDEN DECEPTION ANALYSIS (Absolute Counts)")
    print("="*80)
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Hidden Deception Analysis: Absolute Counts', 
                 fontsize=13, fontweight='bold', y=1.02)
    
    # --- Subplot 1: Deception categories as absolute counts ---
    ax1 = axes[0]
    x = np.arange(len(conditions))
    width = 0.6
    
    deception_cats = ['Hidden_Deception', 'Verbal_Collusion', 'Coordinated_Deception']
    cat_labels = ['Hidden\nDeception', 'Verbal\nCollusion', 'Coordinated\nDeception']
    cat_keys = ['hidden', 'verbal', 'coordinated']
    cat_colors = [COLORS['hidden'], COLORS['verbal'], COLORS['coordinated']]
    
    bottom = np.zeros(len(conditions))
    for cat, cat_key, color, label in zip(deception_cats, cat_keys, cat_colors, cat_labels):
        values = [stats[cond][cat] for cond in conditions]
        bars = ax1.bar(x, values, width, bottom=bottom, label=label, color=color, 
                       edgecolor='white', linewidth=0.5)
        
        # Add count labels
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 10:  # Only show if > 10
                ax1.text(x[i], bot + val/2, f'{int(val)}', ha='center', va='center', 
                        fontsize=8, color='white', fontweight='bold')
        
        bottom += values
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(condition_labels, fontsize=10)
    ax1.set_ylabel('Number of Posts', fontsize=11)
    ax1.set_title('Deception Categories by Condition\n(Excluding Honest)', fontsize=11, fontweight='bold')
    ax1.set_ylim(0, max(bottom) * 1.15)
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, axis='y', alpha=0.3, linestyle=':')
    
    # --- Subplot 2: Communication effect on Hidden Deception (absolute) ---
    ax2 = axes[1]
    
    hidden_counts = [stats[cond].get('Hidden_Deception', 0) for cond in conditions]
    
    x_pos = np.array([0, 1, 3, 4])
    bar_width = 0.7
    
    # No Comm bars
    no_comm_values = [stats['Rep_NoComm'].get('Hidden_Deception', 0), 
                      stats['Warrant_NoComm'].get('Hidden_Deception', 0)]
    comm_values = [stats['Rep_Comm'].get('Hidden_Deception', 0), 
                   stats['Warrant_Comm'].get('Hidden_Deception', 0)]
    
    bars1 = ax2.bar(x_pos[:2], no_comm_values, bar_width, label='No Communication', 
                    color='#6B6B6B', edgecolor='white')
    bars2 = ax2.bar(x_pos[2:], comm_values, bar_width, label='With Communication', 
                    color='#9B2226', edgecolor='white')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, height + 2, 
                    f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Add connecting lines showing communication effect
    # Rep effect
    ax2.annotate('', xy=(1, hidden_counts[1]), 
                xytext=(0, hidden_counts[0]),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
    rep_effect = hidden_counts[1] - hidden_counts[0]
    ax2.text(0.5, max(hidden_counts[0], hidden_counts[1]) + 15, 
             f'{rep_effect:+d}', ha='center', fontsize=9, color='blue', fontweight='bold')
    
    # Warrant effect
    ax2.annotate('', xy=(4, hidden_counts[3]), 
                xytext=(3, hidden_counts[2]),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
    warrant_effect = hidden_counts[3] - hidden_counts[2]
    ax2.text(3.5, max(hidden_counts[2], hidden_counts[3]) + 15, 
             f'{warrant_effect:+d}', ha='center', fontsize=9, color='green', fontweight='bold')
    
    ax2.set_xticks([0.5, 3.5])
    ax2.set_xticklabels(['Rep Only', 'Rep + Warrant'], fontsize=11)
    ax2.set_ylabel('Hidden Deception Count', fontsize=11)
    ax2.set_title('Communication Effect on Hidden Deception', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, max(hidden_counts) * 1.3)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, axis='y', alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    
    # Save figure
    output_path = OUTPUT_DIR / "fig5_1_hidden_deception_absolute.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nfig5_1 (hidden deception absolute counts) saved to: {output_path}")
    
    # Print summary stats
    print("\n" + "-"*60)
    print("KEY FINDINGS (Absolute Counts):")
    print("-"*60)
    print(f"Hidden Deception Counts:")
    print(f"  Rep (No Comm):    {hidden_counts[0]}")
    print(f"  Rep (Comm):       {hidden_counts[1]}")
    print(f"  Comm Effect Rep:  {rep_effect:+d}")
    print()
    print(f"  Warrant (No Comm): {hidden_counts[2]}")
    print(f"  Warrant (Comm):    {hidden_counts[3]}")
    print(f"  Comm Effect Warr: {warrant_effect:+d}")
    print()
    print(f"Warrant reduces Hidden Deception by: {hidden_counts[0] - hidden_counts[2]} (absolute)")
    
    return output_path


def main():
    print("Loading posts data...")
    posts = load_posts()
    print(f"Loaded {len(posts)} posts")
    
    print("\n" + "=" * 80)
    print("2x2 COLLUSION ANALYSIS: Communication vs Behavior")
    print("=" * 80)
    print("\nCategories:")
    print("  - Honest: No collusive post + No deception")
    print("  - Hidden Deception: No collusive post + Deception") 
    print("  - Verbal Collusion: Collusive post + No deception")
    print("  - Coordinated Deception: Collusive post + Deception")
    print()
    
    results = analyze_2x2(posts)
    
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATION")
    print("=" * 80)
    
    output_path = create_visualization(results)
    
    print("\n" + "=" * 80)
    print("GENERATING HIDDEN DECEPTION ANALYSIS (fig4_1_2x2)")
    print("=" * 80)
    
    hidden_deception_path = create_hidden_deception_analysis(posts)
    
    print("\n" + "=" * 80)
    print("GENERATING ABSOLUTE COUNT VISUALIZATIONS")
    print("=" * 80)
    
    fig5_path = create_fig5_absolute_counts(posts)
    fig5_1_path = create_fig5_1_hidden_deception_absolute(posts)
    
    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print(f"fig4_2x2 output: {output_path}")
    print(f"fig4_1_2x2 output: {hidden_deception_path}")
    print(f"fig5 output: {fig5_path}")
    print(f"fig5_1 output: {fig5_1_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()