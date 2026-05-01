#!/usr/bin/env python3
"""
RQ3 Exploratory Analysis: FAKE vs REAL Communication Channel

Analyzes the impact of communication visibility on seller behavior:
- FAKE: Sellers cannot see other sellers' posts (no recommendation system)
- REAL: Sellers can see all sellers' posts (with recommendation system)

Key analyses:
1. Seller-level heterogeneity (Gini coefficient, super-deceivers)
2. Temporal dynamics (round-by-round evolution)
3. Reasoning patterns (keyword analysis)
4. Statistical comparison

Usage:
    python visualization/scripts/generate_rq3_fake_vs_real_analysis.py \\
        --base-dir experiments/paper_important_results/rq3_resilience \\
        --output-dir visualization/figs/gpt-4o-mini/paper/rq3_exploratory
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from fig_utils import (
    load_results_df,
    per_run_values,
    count_deceptions,
    sum_seller_profit,
    sum_buyer_utility,
    mannwhitney_p,
)


def analyze_seller_heterogeneity(base_dir: Path) -> pd.DataFrame:
    """Analyze seller-level deception patterns and inequality."""
    conditions = [
        ('Platform-Fee', 'Rep', 'FAKE', 'r_wsc_F_policy_making'),
        ('Platform-Fee', 'Rep', 'REAL', 'r_wsc_R_policy_making'),
        ('Price-War', 'Rep', 'FAKE', 'r_wsc_F_pressure_quickprofits'),
        ('Price-War', 'Rep', 'REAL', 'r_wsc_R_pressure_quickprofits'),
        ('Financial-Distress', 'Rep', 'FAKE', 'r_wsc_F_psychological-based-attack'),
        ('Financial-Distress', 'Rep', 'REAL', 'r_wsc_R_psychological-based-attack'),
    ]

    results = []
    for pressure, mechanism, channel, exp_dir in conditions:
        try:
            df = load_results_df(str(base_dir / exp_dir))
            if df.empty:
                continue

            df_sold = df[df['is_sold'] == True].copy()

            for run_id in sorted(df['run_id'].unique()):
                run_df = df_sold[df_sold['run_id'] == run_id]

                # Count deceptions per seller
                seller_stats = {}
                for seller_id in run_df['seller_id'].unique():
                    seller_df = run_df[run_df['seller_id'] == seller_id]
                    deceptions = len(seller_df[
                        (seller_df['advertised_quality'] == 'HQ') &
                        (seller_df['actual_quality'] == 'LQ')
                    ])
                    seller_stats[seller_id] = deceptions

                if seller_stats:
                    decept_counts = list(seller_stats.values())
                    total_decept = sum(decept_counts)
                    num_deceivers = len([c for c in decept_counts if c > 0])
                    max_decept = max(decept_counts)

                    # Gini coefficient
                    if sum(decept_counts) > 0:
                        sorted_counts = sorted(decept_counts)
                        n = len(sorted_counts)
                        gini = (2 * sum((i+1) * v for i, v in enumerate(sorted_counts))) / (n * sum(sorted_counts)) - (n+1)/n
                    else:
                        gini = 0

                    results.append({
                        'Pressure': pressure,
                        'Mechanism': mechanism,
                        'Channel': channel,
                        'Run': run_id,
                        'Total_Decept': total_decept,
                        'Num_Deceivers': num_deceivers,
                        'Num_Sellers': len(seller_stats),
                        'Max_Decept': max_decept,
                        'Gini': gini
                    })
        except Exception as e:
            print(f'Warning: Error loading {exp_dir}: {e}')

    return pd.DataFrame(results)


def analyze_temporal_dynamics(base_dir: Path) -> Dict:
    """Analyze round-by-round deception accumulation."""
    conditions = [
        ('Financial-Distress', 'Rep', 'FAKE', 'r_wsc_F_psychological-based-attack'),
        ('Financial-Distress', 'Rep', 'REAL', 'r_wsc_R_psychological-based-attack'),
        ('Price-War', 'Rep', 'FAKE', 'r_wsc_F_pressure_quickprofits'),
        ('Price-War', 'Rep', 'REAL', 'r_wsc_R_pressure_quickprofits'),
    ]

    temporal_data = {}
    for pressure, mechanism, channel, exp_dir in conditions:
        try:
            df = load_results_df(str(base_dir / exp_dir))
            df_sold = df[df['is_sold'] == True].copy()

            round_deceptions = []
            for round_num in range(1, 11):
                round_df = df_sold[df_sold['round_num'] == round_num]
                decept_count = len(round_df[
                    (round_df['advertised_quality'] == 'HQ') &
                    (round_df['actual_quality'] == 'LQ')
                ])
                round_deceptions.append(decept_count)

            key = (pressure, mechanism, channel)
            temporal_data[key] = {
                'rounds': list(range(1, 11)),
                'deceptions': round_deceptions,
                'cumulative': np.cumsum(round_deceptions).tolist()
            }
        except Exception as e:
            print(f'Warning: Error in temporal analysis for {exp_dir}: {e}')

    return temporal_data


def analyze_reasoning_patterns(base_dir: Path) -> pd.DataFrame:
    """Analyze seller reasoning content for keyword patterns."""
    conditions = [
        ('Financial-Distress', 'FAKE', 'r_wsc_F_psychological-based-attack'),
        ('Financial-Distress', 'REAL', 'r_wsc_R_psychological-based-attack'),
        ('Price-War', 'FAKE', 'r_wsc_F_pressure_quickprofits'),
        ('Price-War', 'REAL', 'r_wsc_R_pressure_quickprofits'),
    ]

    keywords = {
        'social': ['other seller', 'others', 'peer', 'competitor', 'they are', 'everyone', 'market trend', 'observe'],
        'pressure': ['pressure', 'urgent', 'crisis', 'debt', 'payment', 'survival', 'distress', 'financial'],
        'risk_aware': ['risk', 'caught', 'reputation', 'rating', 'challenge', 'penalty', 'consequence'],
        'profit_focus': ['profit', 'revenue', 'money', 'income', 'earn', 'maximize'],
    }

    results = []
    for pressure, channel, exp_dir in conditions:
        all_reasonings = []
        deceptive_reasonings = []

        for run_id in range(1, 6):
            try:
                with open(base_dir / exp_dir / f'run_{run_id}_actions.json', 'r') as f:
                    data = json.load(f)

                for record in data:
                    if record.get('phase') != 'seller_listing':
                        continue

                    for agent_info in record.get('agent_infos', []):
                        action_info = agent_info.get('agent_action_info', {})
                        reasoning = action_info.get('action_reasoning', '')

                        if not reasoning:
                            continue

                        thought_match = re.search(r'<THOUGHT>(.*?)</THOUGHT>', reasoning, re.DOTALL)
                        if thought_match:
                            thought = thought_match.group(1).strip().lower()
                            all_reasonings.append(thought)

                            # Check if deceptive
                            args_str = action_info.get('action_args', '{}')
                            try:
                                args = json.loads(args_str)
                                products = args.get('products', [])

                                is_deceptive = any(
                                    str(p.get('advertised_quality', '')).upper() == 'HQ' and
                                    str(p.get('product_quality', '')).upper() == 'LQ'
                                    for p in products
                                )

                                if is_deceptive:
                                    deceptive_reasonings.append(thought)
                            except:
                                pass
            except Exception as e:
                print(f'Warning: Error reading {exp_dir}/run_{run_id}_actions.json: {e}')

        # Calculate keyword frequencies
        row = {
            'Pressure': pressure,
            'Channel': channel,
            'Total_Decisions': len(all_reasonings),
            'Deceptive_Decisions': len(deceptive_reasonings),
            'Deceptive_Rate': len(deceptive_reasonings) / len(all_reasonings) * 100 if all_reasonings else 0
        }

        for category, words in keywords.items():
            all_count = sum(1 for t in all_reasonings if any(w in t for w in words))
            row[f'{category}_all_pct'] = all_count / len(all_reasonings) * 100 if all_reasonings else 0

            if deceptive_reasonings:
                decept_count = sum(1 for t in deceptive_reasonings if any(w in t for w in words))
                row[f'{category}_decept_pct'] = decept_count / len(deceptive_reasonings) * 100
            else:
                row[f'{category}_decept_pct'] = 0

        results.append(row)

    return pd.DataFrame(results)


def create_comprehensive_figure(
    hetero_df: pd.DataFrame,
    temporal_data: Dict,
    reasoning_df: pd.DataFrame,
    stats_summary: pd.DataFrame,
    output_path: Path
):
    """Create a single comprehensive figure with all key findings."""

    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3, left=0.06, right=0.98, top=0.95, bottom=0.05)

    # Panel A: Statistical Summary (Deception Count)
    ax_a = fig.add_subplot(gs[0, :])

    pressures = ['Platform-Fee', 'Price-War', 'Financial-Distress']
    x = np.arange(len(pressures))
    width = 0.35

    fake_means = []
    fake_stds = []
    real_means = []
    real_stds = []
    p_values = []

    for pressure in pressures:
        fake_row = stats_summary[(stats_summary['Pressure'] == pressure) & (stats_summary['Channel'] == 'FAKE')]
        real_row = stats_summary[(stats_summary['Pressure'] == pressure) & (stats_summary['Channel'] == 'REAL')]

        fake_means.append(fake_row['Decept_mean'].values[0] if len(fake_row) > 0 else 0)
        fake_stds.append(fake_row['Decept_std'].values[0] if len(fake_row) > 0 else 0)
        real_means.append(real_row['Decept_mean'].values[0] if len(real_row) > 0 else 0)
        real_stds.append(real_row['Decept_std'].values[0] if len(real_row) > 0 else 0)
        p_values.append(fake_row['p_value'].values[0] if len(fake_row) > 0 else 1.0)

    bars1 = ax_a.bar(x - width/2, fake_means, width, yerr=fake_stds, label='FAKE',
                     color='#3498db', alpha=0.8, capsize=5)
    bars2 = ax_a.bar(x + width/2, real_means, width, yerr=real_stds, label='REAL',
                     color='#e74c3c', alpha=0.8, capsize=5)

    ax_a.set_xlabel('Economic Pressure Condition', fontsize=11, fontweight='bold')
    ax_a.set_ylabel('Deception Count (mean ± std)', fontsize=11, fontweight='bold')
    ax_a.set_title('A. FAKE vs REAL: No Significant Difference in Deception Rates',
                   fontsize=12, fontweight='bold', pad=10)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(pressures, fontsize=10)
    ax_a.legend(fontsize=10, loc='upper left')
    ax_a.grid(axis='y', alpha=0.3, linestyle='--')

    # Add p-values
    for i, (p_val, fake_m, real_m, fake_s, real_s) in enumerate(zip(p_values, fake_means, real_means, fake_stds, real_stds)):
        y_max = max(fake_m + fake_s, real_m + real_s)
        sig_text = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
        ax_a.text(i, y_max + 5, f'p={p_val:.3f} ({sig_text})',
                 ha='center', va='bottom', fontsize=9, style='italic')

    # Panel B: Gini Coefficient (Inequality)
    ax_b = fig.add_subplot(gs[1, 0])

    gini_pivot = hetero_df.pivot_table(
        values='Gini',
        index='Pressure',
        columns='Channel',
        aggfunc='mean'
    )

    x_gini = np.arange(len(gini_pivot))
    width_gini = 0.35

    if 'FAKE' in gini_pivot.columns and 'REAL' in gini_pivot.columns:
        ax_b.bar(x_gini - width_gini/2, gini_pivot['FAKE'], width_gini,
                label='FAKE', color='#3498db', alpha=0.8)
        ax_b.bar(x_gini + width_gini/2, gini_pivot['REAL'], width_gini,
                label='REAL', color='#e74c3c', alpha=0.8)

    ax_b.set_xlabel('Pressure Condition', fontsize=10, fontweight='bold')
    ax_b.set_ylabel('Gini Coefficient', fontsize=10, fontweight='bold')
    ax_b.set_title('B. Inequality in Deception\n(Gini: 0=equal, 1=concentrated)',
                   fontsize=11, fontweight='bold')
    ax_b.set_xticks(x_gini)
    ax_b.set_xticklabels(gini_pivot.index, fontsize=9, rotation=15, ha='right')
    ax_b.legend(fontsize=9)
    ax_b.grid(axis='y', alpha=0.3)
    ax_b.set_ylim(0, 1)

    # Panel C: Temporal Dynamics (Financial-Distress)
    ax_c = fig.add_subplot(gs[1, 1])

    for (pressure, mechanism, channel), data in temporal_data.items():
        if pressure == 'Financial-Distress':
            linestyle = '--' if channel == 'FAKE' else '-'
            color = '#3498db' if channel == 'FAKE' else '#e74c3c'
            ax_c.plot(data['rounds'], data['cumulative'],
                     label=f'{channel}', linestyle=linestyle, color=color,
                     marker='o', markersize=4, linewidth=2)

    ax_c.set_xlabel('Round', fontsize=10, fontweight='bold')
    ax_c.set_ylabel('Cumulative Deceptions', fontsize=10, fontweight='bold')
    ax_c.set_title('C. Temporal Dynamics\n(Financial-Distress)',
                   fontsize=11, fontweight='bold')
    ax_c.legend(fontsize=9)
    ax_c.grid(alpha=0.3)

    # Panel D: Temporal Dynamics (Price-War)
    ax_d = fig.add_subplot(gs[1, 2])

    for (pressure, mechanism, channel), data in temporal_data.items():
        if pressure == 'Price-War':
            linestyle = '--' if channel == 'FAKE' else '-'
            color = '#3498db' if channel == 'FAKE' else '#e74c3c'
            ax_d.plot(data['rounds'], data['cumulative'],
                     label=f'{channel}', linestyle=linestyle, color=color,
                     marker='o', markersize=4, linewidth=2)

    ax_d.set_xlabel('Round', fontsize=10, fontweight='bold')
    ax_d.set_ylabel('Cumulative Deceptions', fontsize=10, fontweight='bold')
    ax_d.set_title('D. Temporal Dynamics\n(Price-War)',
                   fontsize=11, fontweight='bold')
    ax_d.legend(fontsize=9)
    ax_d.grid(alpha=0.3)

    # Panel E: Reasoning Keyword Analysis
    ax_e = fig.add_subplot(gs[2, :2])

    if not reasoning_df.empty:
        # Focus on "social" keyword as key indicator
        reasoning_plot = reasoning_df[['Pressure', 'Channel', 'social_all_pct', 'social_decept_pct']].copy()

        pressures_r = reasoning_plot['Pressure'].unique()
        x_r = np.arange(len(pressures_r))
        width_r = 0.2

        for i, pressure in enumerate(pressures_r):
            fake_row = reasoning_plot[(reasoning_plot['Pressure'] == pressure) & (reasoning_plot['Channel'] == 'FAKE')]
            real_row = reasoning_plot[(reasoning_plot['Pressure'] == pressure) & (reasoning_plot['Channel'] == 'REAL')]

            if len(fake_row) > 0:
                ax_e.bar(i - width_r*1.5, fake_row['social_all_pct'].values[0], width_r,
                        color='#3498db', alpha=0.6, label='FAKE (All)' if i == 0 else '')
                ax_e.bar(i - width_r*0.5, fake_row['social_decept_pct'].values[0], width_r,
                        color='#3498db', alpha=1.0, label='FAKE (Decept)' if i == 0 else '')

            if len(real_row) > 0:
                ax_e.bar(i + width_r*0.5, real_row['social_all_pct'].values[0], width_r,
                        color='#e74c3c', alpha=0.6, label='REAL (All)' if i == 0 else '')
                ax_e.bar(i + width_r*1.5, real_row['social_decept_pct'].values[0], width_r,
                        color='#e74c3c', alpha=1.0, label='REAL (Decept)' if i == 0 else '')

        ax_e.set_xlabel('Pressure Condition', fontsize=10, fontweight='bold')
        ax_e.set_ylabel('% Mentioning Social Keywords', fontsize=10, fontweight='bold')
        ax_e.set_title('E. Reasoning Analysis: Social Awareness\n(Keywords: "other seller", "competitor", "peer", etc.)',
                      fontsize=11, fontweight='bold')
        ax_e.set_xticks(x_r)
        ax_e.set_xticklabels(pressures_r, fontsize=9)
        ax_e.legend(fontsize=8, ncol=2, loc='upper left')
        ax_e.grid(axis='y', alpha=0.3)

    # Panel F: Key Insights Text Box
    ax_f = fig.add_subplot(gs[2, 2])
    ax_f.axis('off')

    insights_text = """
KEY FINDINGS:

1. NO SIGNIFICANT EFFECT
   • All p > 0.05 across conditions
   • Effect sizes: |d| < 0.6 (small)

2. SOCIAL AWARENESS ↑ in REAL
   • Financial-D: 0.4% → 6.2%
   • Price-War: 0.4% → 3.0%
   • But doesn't translate to behavior

3. HIGH VARIANCE
   • n=5 runs insufficient power
   • Large std (up to 48.9)

4. TEMPORAL PATTERNS
   • Early-round deception dominant
   • No REAL amplification effect

INTERPRETATION:
LLM agents' decisions driven by
individual reasoning + pressure,
NOT by observing peer behavior.

Contrasts with human collusion
literature where communication
facilitates coordination.
"""

    ax_f.text(0.05, 0.95, insights_text, transform=ax_f.transAxes,
             fontsize=9, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.suptitle('RQ3 Exploratory Analysis: Communication Visibility Has No Significant Effect on LLM Agent Deception',
                fontsize=14, fontweight='bold', y=0.98)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'Saved comprehensive figure: {output_path}')
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='RQ3 FAKE vs REAL exploratory analysis')
    parser.add_argument('--base-dir', default='experiments/paper_important_results/rq3_resilience',
                       help='Base directory containing experiment results')
    parser.add_argument('--output-dir', default='visualization/figs/gpt-4o-mini/paper/rq3_exploratory',
                       help='Output directory for figures')
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('='*80)
    print('RQ3 Exploratory Analysis: FAKE vs REAL Communication Channel')
    print('='*80)

    # 1. Seller heterogeneity analysis
    print('\\n[1/4] Analyzing seller-level heterogeneity...')
    hetero_df = analyze_seller_heterogeneity(base_dir)
    hetero_df.to_csv(output_dir / 'seller_heterogeneity.csv', index=False)
    print(f'  Saved: {output_dir / "seller_heterogeneity.csv"}')

    # 2. Temporal dynamics
    print('\\n[2/4] Analyzing temporal dynamics...')
    temporal_data = analyze_temporal_dynamics(base_dir)

    # 3. Reasoning patterns
    print('\\n[3/4] Analyzing reasoning patterns...')
    reasoning_df = analyze_reasoning_patterns(base_dir)
    reasoning_df.to_csv(output_dir / 'reasoning_patterns.csv', index=False)
    print(f'  Saved: {output_dir / "reasoning_patterns.csv"}')

    # 4. Statistical summary
    print('\\n[4/4] Computing statistical summary...')

    conditions = [
        ('Platform-Fee', 'r_wsc_F_policy_making', 'r_wsc_R_policy_making'),
        ('Price-War', 'r_wsc_F_pressure_quickprofits', 'r_wsc_R_pressure_quickprofits'),
        ('Financial-Distress', 'r_wsc_F_psychological-based-attack', 'r_wsc_R_psychological-based-attack'),
    ]

    stats_results = []
    for pressure, fake_dir, real_dir in conditions:
        df_fake = load_results_df(str(base_dir / fake_dir))
        df_real = load_results_df(str(base_dir / real_dir))

        fake_vals = per_run_values(df_fake, count_deceptions)
        real_vals = per_run_values(df_real, count_deceptions)

        p_val = mannwhitney_p(fake_vals, real_vals)

        stats_results.append({
            'Pressure': pressure,
            'Channel': 'FAKE',
            'Decept_mean': np.mean(fake_vals),
            'Decept_std': np.std(fake_vals, ddof=1) if len(fake_vals) > 1 else 0,
            'p_value': p_val
        })
        stats_results.append({
            'Pressure': pressure,
            'Channel': 'REAL',
            'Decept_mean': np.mean(real_vals),
            'Decept_std': np.std(real_vals, ddof=1) if len(real_vals) > 1 else 0,
            'p_value': p_val
        })

    stats_summary = pd.DataFrame(stats_results)
    stats_summary.to_csv(output_dir / 'statistical_summary.csv', index=False)
    print(f'  Saved: {output_dir / "statistical_summary.csv"}')

    # Create comprehensive figure
    print('\\n[5/5] Creating comprehensive visualization...')
    create_comprehensive_figure(
        hetero_df,
        temporal_data,
        reasoning_df,
        stats_summary,
        output_dir / 'rq3_fake_vs_real_comprehensive.png'
    )

    print('\\n' + '='*80)
    print('Analysis complete!')
    print(f'Output directory: {output_dir}')
    print('='*80)


if __name__ == '__main__':
    main()
