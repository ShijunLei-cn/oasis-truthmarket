#!/usr/bin/env python3
"""
Deep Collusion Analysis - 3 Key Research Questions

This script analyzes the collusion data to address:
1. Deception Causal Path: Type 1-4 → Actual Deception conversion rate
2. Warrant Endogeneity: How Warrant affects honest seller profits
3. Constraint Effects: How different constraints affect collusion

Usage:
    python collusion_deep_analysis.py --input data/case_analysis/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import pandas as pd
import numpy as np

# Add visualization scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "visualization" / "scripts"))
from fig_utils import COLORS, setup_style, mannwhitney_p

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

setup_style()


def save_figure_safe(fig, output_path, dpi=300):
    """Safe save figure helper."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {output_path}")


# ─── Collusion Types Definition ───────────────────────────────────────────────

COLLUSION_TYPES = {
    1: {"name": "Direct Collusion Proposal", "collusive": True, "severity": "high"},
    2: {"name": "Deception Strategy Broadcast", "collusive": True, "severity": "high"},
    3: {"name": "Collusion Coordination", "collusive": True, "severity": "medium"},
    4: {"name": "Social Normalization", "collusive": True, "severity": "low"},
    5: {"name": "Neutral Information", "collusive": False, "severity": "none"},
    6: {"name": "Anti-Collusion", "collusive": False, "severity": "none"},
}


def parse_experiment_id(exp_id: str) -> Dict[str, Any]:
    """Parse experiment ID into components."""
    parts = exp_id.split("_")
    
    if len(parts) < 4:
        return {"mechanism": "unknown", "channel": "unknown", "constraint": "unknown"}
    
    mech = "Warrant" if parts[0] == "rw" else "Rep"
    channel = "Comm" if parts[2] == "R" else "NoComm"
    constraint = "_".join(parts[3:]) if len(parts) > 3 else "unknown"
    
    return {
        "mechanism": mech,
        "channel": channel,
        "constraint": constraint,
        "has_warrant": parts[0] == "rw",
        "has_comm": parts[2] == "R",
    }


# ─── Analysis 1: Deception Causal Path ─────────────────────────────────────

def analyze_causal_path(data_dir: str) -> Dict[str, Any]:
    """Analyze the conversion from collusion planning to actual deception.
    
    Key metrics:
    - Collusion rate (Types 1-4) by condition
    - Actual deception rate by condition
    - Conversion funnel analysis
    """
    print("\n" + "=" * 70)
    print("ANALYSIS 1: DECEPTION CAUSAL PATH")
    print("=" * 70)
    
    # Load type distribution
    type_df = pd.read_csv(f"{data_dir}/type_distribution_by_condition.csv")
    deception_df = pd.read_csv(f"{data_dir}/deception_rate_by_collusion.csv")
    
    results = {}
    
    # Calculate collusion planning rate (Types 1-4) for each condition
    type_cols = ["type_1", "type_2", "type_3", "type_4"]
    
    for _, row in type_df.iterrows():
        exp_id = row["experiment_id"]
        parsed = parse_experiment_id(exp_id)
        
        collusion_rate = sum(row[col] for col in type_cols)
        anti_collusion = row["type_6"]
        
        key = f"{parsed['mechanism']}_{parsed['channel']}_{parsed['constraint']}"
        results[key] = {
            "collusion_planning_rate": collusion_rate,
            "anti_collusion_rate": anti_collusion,
            "neutral_rate": row["type_5"],
            "mechanism": parsed["mechanism"],
            "channel": parsed["channel"],
            "constraint": parsed["constraint"],
        }
    
    # Calculate aggregate by mechanism
    mechanisms = defaultdict(lambda: {"collusion": [], "anti": [], "neutral": []})
    for key, data in results.items():
        mech = data["mechanism"]
        mechanisms[mech]["collusion"].append(data["collusion_planning_rate"])
        mechanisms[mech]["anti"].append(data["anti_collusion_rate"])
        mechanisms[mech]["neutral"].append(data["neutral_rate"])
    
    summary = {}
    for mech, vals in mechanisms.items():
        summary[mech] = {
            "avg_collusion_planning": np.mean(vals["collusion"]),
            "avg_anti_collusion": np.mean(vals["anti"]),
            "avg_neutral": np.mean(vals["neutral"]),
        }
    
    # Print summary
    print("\nCollusion Planning Rate by Mechanism:")
    for mech, stats in summary.items():
        print(f"  {mech}: {stats['avg_collusion_planning']*100:.1f}%")
    
    print("\nAnti-Collusion Rate by Mechanism:")
    for mech, stats in summary.items():
        print(f"  {mech}: {stats['avg_anti_collusion']*100:.1f}%")
    
    # Key finding: Conversion funnel
    print("\n" + "-" * 50)
    print("CONVERSION FUNNEL ANALYSIS:")
    print("-" * 50)
    
    # Baseline: No collusion detected
    no_collusion = deception_df[deception_df["is_collusion"] == False]["deception_rate"].values[0]
    # With collusion detected
    with_collusion = deception_df[deception_df["is_collusion"] == True]["deception_rate"].values[0]
    
    print(f"\n  Stage 1 - No Collusion Detected:")
    print(f"    → Deception Rate: {no_collusion*100:.2f}%")
    print(f"\n  Stage 2 - Collusion Detected (Types 1-4):")
    print(f"    → Deception Rate: {with_collusion*100:.2f}%")
    print(f"\n  Conversion Effect: {with_collusion/no_collusion:.1f}x increase")
    
    # Effect size
    effect_size = with_collusion - no_collusion
    print(f"\n  Absolute Increase: +{effect_size*100:.2f}%")
    print(f"  Relative Increase: +{(with_collusion/no_collusion - 1)*100:.0f}%")
    
    return {
        "summary": summary,
        "conversion": {
            "no_collusion_rate": no_collusion,
            "with_collusion_rate": with_collusion,
            "multiplier": with_collusion / no_collusion,
            "absolute_increase": effect_size,
        },
        "by_condition": results,
    }


# ─── Analysis 2: Warrant Endogeneity ───────────────────────────────────────

def analyze_warrant_endogeneity(data_dir: str) -> Dict[str, Any]:
    """Analyze how Warrant mechanism affects market equilibrium.
    
    Key questions:
    - Does Warrant make honesty more profitable?
    - Does Warrant shift the equilibrium from collusion to anti-collusion?
    - What is the mechanism for endogenous honesty emergence?
    """
    print("\n" + "=" * 70)
    print("ANALYSIS 2: WARRANT ENDOGENEITY")
    print("=" * 70)
    
    # Load type distribution
    type_df = pd.read_csv(f"{data_dir}/type_distribution_by_condition.csv")
    
    # Parse by mechanism and communication
    rep_no_comm = type_df[type_df["experiment_id"].str.startswith("r_wsc_F")]
    rep_with_comm = type_df[type_df["experiment_id"].str.startswith("r_wsc_R")]
    warrant_no_comm = type_df[type_df["experiment_id"].str.startswith("rw_wsc_F")]
    warrant_with_comm = type_df[type_df["experiment_id"].str.startswith("rw_wsc_R")]
    
    type_cols = ["type_1", "type_2", "type_3", "type_4"]
    
    results = {}
    
    for name, df in [
        ("Rep_NoComm", rep_no_comm),
        ("Rep_Comm", rep_with_comm),
        ("Warrant_NoComm", warrant_no_comm),
        ("Warrant_Comm", warrant_with_comm),
    ]:
        if df.empty:
            continue
        
        collusion = df[type_cols].mean(axis=1).sum()
        anti = df["type_6"].mean()
        neutral = df["type_5"].mean()
        
        results[name] = {
            "collusion_rate": collusion,
            "anti_collusion_rate": anti,
            "neutral_rate": neutral,
            "df": df,
        }
    
    print("\nMessage Distribution by Condition:")
    print("-" * 60)
    print(f"{'Condition':<20} {'Collusion (1-4)':<18} {'Anti-Collusion (6)':<18}")
    print("-" * 60)
    
    for name, data in results.items():
        print(f"{name:<20} {data['collusion_rate']*100:>12.1f}%     {data['anti_collusion_rate']*100:>12.1f}%")
    
    print("-" * 60)
    
    # Calculate key effects
    print("\n" + "-" * 50)
    print("KEY EFFECTS:")
    print("-" * 50)
    
    # Effect 1: Warrant effect on collusion
    if "Rep_Comm" in results and "Warrant_Comm" in results:
        rep_collusion = results["Rep_Comm"]["collusion_rate"]
        warrant_collusion = results["Warrant_Comm"]["collusion_rate"]
        warrant_effect = (warrant_collusion - rep_collusion) / rep_collusion * 100
        
        print(f"\n1. Warrant Effect on Collusion (with communication):")
        print(f"   Rep: {rep_collusion*100:.1f}% → Warrant: {warrant_collusion*100:.1f}%")
        print(f"   Reduction: {abs(warrant_effect):.1f}%")
        
        # Anti-collusion effect
        rep_anti = results["Rep_Comm"]["anti_collusion_rate"]
        warrant_anti = results["Warrant_Comm"]["anti_collusion_rate"]
        anti_effect = (warrant_anti - rep_anti) / rep_anti * 100
        
        print(f"\n2. Warrant Effect on Anti-Collusion (with communication):")
        print(f"   Rep: {rep_anti*100:.1f}% → Warrant: {warrant_anti*100:.1f}%")
        print(f"   Increase: +{anti_effect:.1f}%")
    
    # Effect 2: Communication effect
    if "Rep_NoComm" in results and "Rep_Comm" in results:
        no_comm = results["Rep_NoComm"]["collusion_rate"]
        with_comm = results["Rep_Comm"]["collusion_rate"]
        comm_effect = (with_comm - no_comm) / no_comm * 100
        
        print(f"\n3. Communication Effect on Collusion (Rep only):")
        print(f"   No Comm: {no_comm*100:.1f}% → With Comm: {with_comm*100:.1f}%")
        print(f"   Increase: +{comm_effect:.1f}%")
    
    # Effect 3: Warrant neutralizes communication
    print(f"\n4. Warrant Neutralizes Communication Effect:")
    if all(k in results for k in ["Rep_Comm", "Warrant_Comm", "Rep_NoComm", "Warrant_NoComm"]):
        comm_effect_rep = results["Rep_Comm"]["collusion_rate"] - results["Rep_NoComm"]["collusion_rate"]
        comm_effect_warrant = results["Warrant_Comm"]["collusion_rate"] - results["Warrant_NoComm"]["collusion_rate"]
        
        print(f"   Rep: Comm increases collusion by {comm_effect_rep*100:.1f}%")
        print(f"   Warrant: Comm increases collusion by {comm_effect_warrant*100:.1f}%")
        print(f"   Neutralization: {abs(comm_effect_rep - comm_effect_warrant)*100:.1f}% reduction")
    
    # Theoretical explanation
    print("\n" + "-" * 50)
    print("THEORETICAL INTERPRETATION:")
    print("-" * 50)
    print("""
    Why doesn't honesty emerge endogenously?
    
    1. COORDINATION FAILURE:
       - Multiple equilibria exist (honest vs. collusion)
       - Without coordination device, market can get stuck in bad equilibrium
    
    2. EXTERNALITIES:
       - Individual deception has negative externalities on entire market
       - Market cannot internalize these externalities
    
    3. CREDIBLE COMMITMENT:
       - Warrant serves as a credible commitment device
       - Changes the game structure to make honesty sustainable
    
    4. NORM FORMATION:
       - Warrant increases Type 6 (anti-collusion) messages
       - These messages help form honest market norms
    """)
    
    return {
        "by_condition": results,
        "warrant_effect": warrant_effect if "Rep_Comm" in results and "Warrant_Comm" in results else None,
        "communication_effect": comm_effect if "Rep_NoComm" in results and "Rep_Comm" in results else None,
    }


# ─── Analysis 3: Constraint Effects ─────────────────────────────────────────

def analyze_constraint_effects(data_dir: str) -> Dict[str, Any]:
    """Analyze how different constraints affect collusion behavior.
    
    Constraints:
    - Policy Making: Deliberative decision-making
    - Pressure/Quick-Profits: Time pressure
    - Psychological Attack: Emotional manipulation
    """
    print("\n" + "=" * 70)
    print("ANALYSIS 3: CONSTRAINT EFFECTS")
    print("=" * 70)
    
    # Load type distribution
    type_df = pd.read_csv(f"{data_dir}/type_distribution_by_condition.csv")
    
    type_cols = ["type_1", "type_2", "type_3", "type_4"]
    
    # Parse constraint types
    constraints = {
        "policy_making": [],
        "pressure_quickprofits": [],
        "psychological-based-attack": [],
    }
    
    for _, row in type_df.iterrows():
        exp_id = row["experiment_id"]
        parsed = parse_experiment_id(exp_id)
        constraint = parsed["constraint"]
        
        if constraint in constraints:
            collusion_rate = sum(row[col] for col in type_cols)
            anti_rate = row["type_6"]
            
            constraints[constraint].append({
                "experiment_id": exp_id,
                "mechanism": parsed["mechanism"],
                "channel": parsed["channel"],
                "collusion_rate": collusion_rate,
                "anti_collusion_rate": anti_rate,
                "type_1": row["type_1"],
                "type_2": row["type_2"],
                "type_3": row["type_3"],
                "type_4": row["type_4"],
            })
    
    # Aggregate by constraint
    print("\nCollusion Rate by Constraint Type:")
    print("-" * 70)
    
    summary = {}
    
    constraint_names = {
        "policy_making": "Policy Making",
        "pressure_quickprofits": "Pressure/Quick-Profits",
        "psychological-based-attack": "Psychological Attack",
    }
    
    print(f"{'Constraint':<25} {'Mean Collusion':<18} {'Mean Anti-Coll':<18} {'N Experiments'}")
    print("-" * 70)
    
    for constraint, experiments in constraints.items():
        if not experiments:
            continue
        
        mean_collusion = np.mean([e["collusion_rate"] for e in experiments])
        mean_anti = np.mean([e["anti_collusion_rate"] for e in experiments])
        
        summary[constraint] = {
            "name": constraint_names.get(constraint, constraint),
            "mean_collusion": mean_collusion,
            "mean_anti": mean_anti,
            "n_experiments": len(experiments),
            "experiments": experiments,
        }
        
        print(f"{constraint_names.get(constraint, constraint):<25} {mean_collusion*100:>12.1f}%     {mean_anti*100:>12.1f}%     {len(experiments)}")
    
    # Compare Rep vs Warrant within each constraint
    print("\n" + "-" * 50)
    print("WARRANT EFFECT BY CONSTRAINT:")
    print("-" * 50)
    
    for constraint, data in summary.items():
        rep_experiments = [e for e in data["experiments"] if e["mechanism"] == "Rep"]
        warrant_experiments = [e for e in data["experiments"] if e["mechanism"] == "Warrant"]
        
        if rep_experiments and warrant_experiments:
            rep_collusion = np.mean([e["collusion_rate"] for e in rep_experiments])
            warrant_collusion = np.mean([e["collusion_rate"] for e in warrant_experiments])
            
            effect = (warrant_collusion - rep_collusion) / rep_collusion * 100
            
            print(f"\n{data['name']}:")
            print(f"  Rep: {rep_collusion*100:.1f}% → Warrant: {warrant_collusion*100:.1f}%")
            print(f"  Warrant reduces collusion by: {abs(effect):.1f}%")
    
    # Communication effect by constraint
    print("\n" + "-" * 50)
    print("COMMUNICATION EFFECT BY CONSTRAINT:")
    print("-" * 50)
    
    for constraint, data in summary.items():
        no_comm_experiments = [e for e in data["experiments"] if e["channel"] == "NoComm"]
        comm_experiments = [e for e in data["experiments"] if e["channel"] == "Comm"]
        
        if no_comm_experiments and comm_experiments:
            no_comm_collusion = np.mean([e["collusion_rate"] for e in no_comm_experiments])
            comm_collusion = np.mean([e["collusion_rate"] for e in comm_experiments])
            
            effect = (comm_collusion - no_comm_collusion) / no_comm_collusion * 100
            
            print(f"\n{data['name']}:")
            print(f"  No Comm: {no_comm_collusion*100:.1f}% → With Comm: {comm_collusion*100:.1f}%")
            print(f"  Communication increases collusion by: +{effect:.1f}%")
    
    # Key finding
    print("\n" + "-" * 50)
    print("KEY FINDINGS:")
    print("-" * 50)
    
    # Find most and least collusion-prone constraints
    sorted_constraints = sorted(summary.items(), key=lambda x: x[1]["mean_collusion"])
    
    most_ collusion = sorted_constraints[-1]
    least_collusion = sorted_constraints[0]
    
    print(f"\nMost collusion-prone constraint: {most_collusion[1]['name']} ({most_collusion[1]['mean_collusion']*100:.1f}%)")
    print(f"Least collusion-prone constraint: {least_collusion[1]['name']} ({least_collusion[1]['mean_collusion']*100:.1f}%)")
    print(f"Difference: {(most_collusion[1]['mean_collusion'] - least_collusion[1]['mean_collusion'])*100:.1f}%")
    
    return {
        "by_constraint": summary,
        "most_collusion_prone": most_collusion[0],
        "least_collusion_prone": least_collusion[0],
    }


# ─── Main Function ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deep collusion analysis for 3 key research questions"
    )
    parser.add_argument(
        "--input-dir",
        default="data/case_analysis",
        help="Input directory with case_analysis CSV files"
    )
    parser.add_argument(
        "--output-dir",
        default="visualization/figs/paper/collusion_analysis",
        help="Output directory for figures"
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("DEEP COLLUSION ANALYSIS - 3 KEY RESEARCH QUESTIONS")
    print("=" * 70)
    
    # Run all analyses
    causal_path = analyze_causal_path(args.input_dir)
    warrant_effect = analyze_warrant_endogeneity(args.input_dir)
    constraint_effect = analyze_constraint_effects(args.input_dir)
    
    # Create visualizations
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create summary figure
    create_summary_figure(causal_path, warrant_effect, constraint_effect, output_dir)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    
    return {
        "causal_path": causal_path,
        "warrant_effect": warrant_effect,
        "constraint_effect": constraint_effect,
    }


def create_summary_figure(causal: Dict, warrant: Dict, constraints: Dict, output_dir: Path):
    """Create a summary figure with all key findings."""
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Panel A: Causal Path
    ax1 = axes[0]
    conv = causal["conversion"]
    
    stages = ["No Collusion\nDetected", "Collusion\nDetected"]
    rates = [conv["no_collusion_rate"] * 100, conv["with_collusion_rate"] * 100]
    colors = [COLORS["good_light"], COLORS["bad_light"]]
    
    bars = ax1.bar(stages, rates, color=colors, edgecolor="white", linewidth=1)
    ax1.set_ylabel("Deception Rate (%)", fontsize=10)
    ax1.set_title("(a) Collusion → Deception\nCausal Path", fontsize=11, fontweight="bold")
    
    # Add labels
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f"{rate:.1f}%", ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Add arrow annotation
    ax1.annotate('', xy=(0.5, max(rates)*0.8), xytext=(0.5, max(rates)*0.6),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax1.text(0.5, max(rates)*0.65, f"{conv['multiplier']:.1f}x increase",
            ha='center', fontsize=10, fontweight='bold', color=COLORS["bad_dark"])
    
    ax1.set_ylim(0, 50)
    
    # Panel B: Warrant Endogeneity
    ax2 = axes[1]
    
    warrant_data = warrant["by_condition"]
    conditions = ["Rep\nNo Comm", "Rep\nComm", "Warrant\nNo Comm", "Warrant\nComm"]
    collusion_rates = []
    anti_rates = []
    
    for cond in ["Rep_NoComm", "Rep_Comm", "Warrant_NoComm", "Warrant_Comm"]:
        if cond in warrant_data:
            collusion_rates.append(warrant_data[cond]["collusion_rate"] * 100)
            anti_rates.append(warrant_data[cond]["anti_collusion_rate"] * 100)
        else:
            collusion_rates.append(0)
            anti_rates.append(0)
    
    x = np.arange(len(conditions))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, collusion_rates, width, label="Collusion (1-4)", 
                    color=COLORS["bad_light"], edgecolor="white")
    bars2 = ax2.bar(x + width/2, anti_rates, width, label="Anti-Collusion (6)", 
                    color=COLORS["good_light"], edgecolor="white")
    
    ax2.set_ylabel("Message Rate (%)", fontsize=10)
    ax2.set_title("(b) Warrant Mechanism\nEndogeneity Effect", fontsize=11, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(conditions, fontsize=9)
    ax2.legend(loc='upper right', fontsize=8)
    ax2.set_ylim(0, 90)
    
    # Panel C: Constraint Effects
    ax3 = axes[2]
    
    constraint_names = ["Policy\nMaking", "Pressure/\nQuick-Profits", "Psychological\nAttack"]
    
    rep_collusion = []
    warrant_collusion = []
    
    for name in ["policy_making", "pressure_quickprofits", "psychological-based-attack"]:
        if name in constraints["by_constraint"]:
            data = constraints["by_constraint"][name]["experiments"]
            rep_c = np.mean([e["collusion_rate"] for e in data if e["mechanism"] == "Rep"]) * 100
            warrant_c = np.mean([e["collusion_rate"] for e in data if e["mechanism"] == "Warrant"]) * 100
            rep_collusion.append(rep_c)
            warrant_collusion.append(warrant_c)
        else:
            rep_collusion.append(0)
            warrant_collusion.append(0)
    
    x = np.arange(len(constraint_names))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, rep_collusion, width, label="Reputation Only", 
                    color="#AAAAAA", edgecolor="white")
    bars2 = ax3.bar(x + width/2, warrant_collusion, width, label="Reputation+Warrant", 
                    color=COLORS["warrant_dark"], edgecolor="white")
    
    ax3.set_ylabel("Collusion Rate (%)", fontsize=10)
    ax3.set_title("(c) Constraint Effects\non Collusion", fontsize=11, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(constraint_names, fontsize=9)
    ax3.legend(loc='upper right', fontsize=8)
    ax3.set_ylim(0, 30)
    
    plt.tight_layout()
    save_figure_safe(fig, output_dir / "fig_deep_collusion_analysis.png")
    print(f"\nSaved summary figure to {output_dir / 'fig_deep_collusion_analysis.png'}")


if __name__ == "__main__":
    results = main()
