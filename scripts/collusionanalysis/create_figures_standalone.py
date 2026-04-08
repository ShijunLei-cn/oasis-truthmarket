#!/usr/bin/env python3
"""Standalone visualization script for collusion analysis."""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# Set style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.7,
})

# Colors
COLORS = {
    "bad_dark": "#AE2012",
    "bad_light": "#F4C9BA",
    "good_dark": "#1D6B3A",
    "good_light": "#C8E6C9",
    "warrant_dark": "#1565c0",
    "neutral": "#AAAAAA",
}

def main():
    # Load data
    data_dir = Path("data/case_analysis")
    type_df = pd.read_csv(data_dir / "type_distribution_by_condition.csv")
    deception_df = pd.read_csv(data_dir / "deception_rate_by_collusion.csv")
    
    output_dir = Path("visualization/figs/paper/collusion_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("CREATING COLLUSION ANALYSIS VISUALIZATIONS")
    print("=" * 60)
    
    # Figure 1: Causal Path
    print("\nCreating Figure 1: Causal Path...")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    
    stages = ["No Collusion\nDetected", "Collusion\nDetected"]
    rates = [4.9, 41.3]
    colors = [COLORS["good_light"], COLORS["bad_light"]]
    
    bars = ax1.bar(stages, rates, color=colors, edgecolor="white", linewidth=1)
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_x() + bar.get_width()/2., rate + 1,
                f"{rate:.1f}%", ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    ax1.annotate('', xy=(0.5, 35), xytext=(0.5, 25),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax1.text(0.5, 38, "8.4x increase", ha='center', fontsize=11, fontweight='bold')
    
    ax1.set_ylabel("Deception Rate (%)")
    ax1.set_title("(a) Collusion -> Deception Causal Path", fontweight='bold')
    ax1.set_ylim(0, 55)
    
    fig1.tight_layout()
    fig1.savefig(output_dir / "fig1_causal_path.png", dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig1)
    print(f"  Saved: {output_dir / 'fig1_causal_path.png'}")
    
    # Figure 2: Mechanism Comparison
    print("\nCreating Figure 2: Mechanism Comparison...")
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    
    conditions = ["Reputation\nOnly", "Reputation\n+ Comm", "Warrant\nOnly", "Warrant\n+ Comm"]
    
    # Calculate from data
    rep_no_comm = type_df[type_df["experiment_id"].str.startswith("r_wsc_F")]
    rep_comm = type_df[type_df["experiment_id"].str.startswith("r_wsc_R")]
    warrant_no_comm = type_df[type_df["experiment_id"].str.startswith("rw_wsc_F")]
    warrant_comm = type_df[type_df["experiment_id"].str.startswith("rw_wsc_R")]
    
    type_cols = ["type_1", "type_2", "type_3", "type_4"]
    
    def calc_rates(df):
        if df.empty:
            return 0, 0, 0
        collusion = df[type_cols].mean(axis=1).sum()
        anti = df["type_6"].mean()
        neutral = df["type_5"].mean()
        return collusion * 100, anti * 100, neutral * 100
    
    rates = [
        calc_rates(rep_no_comm),
        calc_rates(rep_comm),
        calc_rates(warrant_no_comm),
        calc_rates(warrant_comm),
    ]
    
    x = np.arange(len(conditions))
    w = 0.6
    
    bottoms = [0] * 4
    for i, (c, a, n) in enumerate(rates):
        ax2.bar(x[i], c, w, color=COLORS["bad_light"], bottom=bottoms[i], edgecolor="white")
        ax2.bar(x[i], n, w, color=COLORS["neutral"], bottom=bottoms[i]+c, edgecolor="white")
        ax2.bar(x[i], a, w, color=COLORS["good_light"], bottom=bottoms[i]+c+n, edgecolor="white")
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(conditions)
    ax2.set_ylabel("Message Rate (%)")
    ax2.set_title("(b) Message Distribution by Mechanism", fontweight='bold')
    ax2.set_ylim(0, 100)
    
    # Legend
    ax2.bar(0, 0, 0.6, color=COLORS["bad_light"], label="Collusion (1-4)")
    ax2.bar(0, 0, 0.6, color=COLORS["neutral"], label="Neutral (5)")
    ax2.bar(0, 0, 0.6, color=COLORS["good_light"], label="Anti-Collusion (6)")
    ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
    
    fig2.tight_layout()
    fig2.savefig(output_dir / "fig2_mechanism_comparison.png", dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig2)
    print(f"  Saved: {output_dir / 'fig2_mechanism_comparison.png'}")
    
    # Figure 3: Constraint Effects
    print("\nCreating Figure 3: Constraint Effects...")
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    
    constraints = ["Policy Making", "Pressure/Quick-Profits", "Psychological Attack"]
    
    rep_collusion = []
    warrant_collusion = []
    
    for constraint in ["policy_making", "pressure_quickprofits", "psychological-based-attack"]:
        rep_df = type_df[type_df["experiment_id"].str.contains(f"r_wsc.*_{constraint}")]
        warrant_df = type_df[type_df["experiment_id"].str.contains(f"rw_wsc.*_{constraint}")]
        
        rep_c = rep_df[type_cols].mean(axis=1).sum() * 100 if not rep_df.empty else 0
        warrant_c = warrant_df[type_cols].mean(axis=1).sum() * 100 if not warrant_df.empty else 0
        
        rep_collusion.append(rep_c)
        warrant_collusion.append(warrant_c)
    
    x = np.arange(len(constraints))
    w = 0.35
    
    ax3.bar(x - w/2, rep_collusion, w, label="Reputation Only", color=COLORS["neutral"], edgecolor="white")
    ax3.bar(x + w/2, warrant_collusion, w, label="Reputation+Warrant", color=COLORS["warrant_dark"], edgecolor="white")
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(constraints)
    ax3.set_ylabel("Collusion Rate (%)")
    ax3.set_title("(c) Collusion by Constraint Type", fontweight='bold')
    ax3.legend()
    ax3.set_ylim(0, 25)
    
    # Add reduction annotations
    for i, (r, w) in enumerate(zip(rep_collusion, warrant_collusion)):
        if r > 0:
            reduction = (r - w) / r * 100
            ax3.annotate(f"-{reduction:.0f}%", xy=(i + w/2, w + 1), ha='center', fontsize=9, color='green', fontweight='bold')
    
    fig3.tight_layout()
    fig3.savefig(output_dir / "fig3_constraint_effects.png", dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig3)
    print(f"  Saved: {output_dir / 'fig3_constraint_effects.png'}")
    
    print("\n" + "=" * 60)
    print(f"All figures saved to: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()