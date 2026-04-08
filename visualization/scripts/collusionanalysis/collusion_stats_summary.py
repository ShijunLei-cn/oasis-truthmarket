#!/usr/bin/env python3
"""
Statistical Summary for Collusion Analysis

This module generates statistical summaries and tables for the collusion analysis,
complementing the visualizations in collusion_analysis.py.

Key metrics:
1. Deception rates by collusion status
2. Collusion type distributions by condition
3. Communication effect on collusion
4. Statistical significance tests
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from scipy import stats
import numpy as np
import pandas as pd


def load_data(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Load all CSV files from case_analysis directory."""
    case_dir = Path(data_dir) / "case_analysis"
    
    data = {}
    
    files = {
        "deception_by_collusion": "deception_rate_by_collusion.csv",
        "type_by_condition": "type_distribution_by_condition.csv",
        "type_by_round": "type_distribution_by_round.csv",
        "type_by_prompt": "type_distribution_by_prompt_type.csv",
        "real_vs_fake": "type_distribution_real_vs_fake.csv",
    }
    
    for key, filename in files.items():
        path = case_dir / filename
        if path.exists():
            data[key] = pd.read_csv(path)
        else:
            print(f"WARNING: {path} not found")
            data[key] = pd.DataFrame()
    
    return data


def load_examples(data_dir: str) -> List[Dict]:
    """Load qualitative examples."""
    path = Path(data_dir) / "case_analysis" / "qualitative_examples.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def summarize_deception_by_collusion(data: Dict) -> Dict[str, Any]:
    """Generate summary of deception rates by collusion status."""
    df = data.get("deception_by_collusion", pd.DataFrame())
    if df.empty:
        return {}
    
    no_collusion = df[df["is_collusion"] == False]["deception_rate"].values[0]
    with_collusion = df[df["is_collusion"] == True]["deception_rate"].values[0]
    increase_ratio = with_collusion / no_collusion if no_collusion > 0 else 0
    
    return {
        "deception_rate_no_collusion": f"{no_collusion*100:.2f}%",
        "deception_rate_with_collusion": f"{with_collusion*100:.2f}%",
        "increase_ratio": f"{increase_ratio:.1f}x",
        "increase_percentage": f"{(with_collusion - no_collusion)*100:.2f}%",
        "absolute_increase": with_collusion - no_collusion,
    }


def summarize_collusion_types(data: Dict) -> Dict[str, Any]:
    """Summarize collusion type distributions."""
    df = data.get("type_by_condition", pd.DataFrame())
    if df.empty:
        return {}
    
    type_cols = [f"type_{i}" for i in range(1, 7)]
    
    # Overall means
    overall = df[type_cols].mean() * 100
    
    # By mechanism
    rep_conds = [c for c in df["experiment_id"] if c.startswith("r_wsc_")]
    warrant_conds = [c for c in df["experiment_id"] if c.startswith("rw_wsc_")]
    
    rep_means = df[df["experiment_id"].isin(rep_conds)][type_cols].mean() * 100
    warrant_means = df[df["experiment_id"].isin(warrant_conds)][type_cols].mean() * 100
    
    # Collusive types (1-4) sum
    collusive_rep = sum(rep_means.values[:4])
    collusive_warrant = sum(warrant_means.values[:4])
    
    return {
        "overall": {f"type_{i}": f"{v:.2f}%" for i, v in enumerate(overall.values, 1)},
        "rep_only": {f"type_{i}": f"{v:.2f}%" for i, v in enumerate(rep_means.values, 1)},
        "warrant_only": {f"type_{i}": f"{v:.2f}%" for i, v in enumerate(warrant_means.values, 1)},
        "collusive_sum_rep": f"{collusive_rep:.2f}%",
        "collusive_sum_warrant": f"{collusive_warrant:.2f}%",
        "collusive_reduction": f"{(collusive_rep - collusive_warrant):.2f}%",
        "collusive_reduction_pct": f"{(collusive_rep - collusive_warrant)/collusive_rep*100:.1f}%" if collusive_rep > 0 else "N/A",
    }


def summarize_communication_effect(data: Dict) -> Dict[str, Any]:
    """Summarize communication channel effect on collusion."""
    df = data.get("type_by_condition", pd.DataFrame())
    if df.empty:
        return {}
    
    type_cols = [f"type_{i}" for i in range(1, 7)]
    
    # Group by communication status
    no_comm = [c for c in df["experiment_id"] if c.endswith("_F")]
    with_comm = [c for c in df["experiment_id"] if c.endswith("_R")]
    
    no_comm_means = df[df["experiment_id"].isin(no_comm)][type_cols].mean() * 100
    with_comm_means = df[df["experiment_id"].isin(with_comm)][type_cols].mean() * 100
    
    # Collusive sum
    collusive_no_comm = sum(no_comm_means.values[:4])
    collusive_with_comm = sum(with_comm_means.values[:4])
    
    return {
        "collusive_no_communication": f"{collusive_no_comm:.2f}%",
        "collusive_with_communication": f"{collusive_with_comm:.2f}%",
        "communication_increase": f"{(collusive_with_comm - collusive_no_comm):.2f}%",
        "communication_effect": "Increases" if collusive_with_comm > collusive_no_comm else "Decreases",
    }


def run_statistical_tests(data: Dict) -> Dict[str, Any]:
    """Run statistical significance tests."""
    df = data.get("type_by_condition", pd.DataFrame())
    if df.empty:
        return {}
    
    type_cols = [f"type_{i}" for i in range(1, 7)]
    
    results = {}
    
    # Compare Rep+Comm vs Warrant+Comm (communication present)
    rep_comm = [c for c in df["experiment_id"] if c.startswith("r_wsc_R")]
    warrant_comm = [c for c in df["experiment_id"] if c.startswith("rw_wsc_R")]
    
    if rep_comm and warrant_comm:
        rep_df = df[df["experiment_id"].isin(rep_comm)]
        warrant_df = df[df["experiment_id"].isin(warrant_comm)]
        
        # For each type
        for type_id in range(1, 7):
            col = f"type_{type_id}"
            rep_vals = rep_df[col].values
            warrant_vals = warrant_df[col].values
            
            if len(rep_vals) > 1 and len(warrant_vals) > 1:
                try:
                    stat, p = stats.mannwhitneyu(rep_vals, warrant_vals, alternative="two-sided")
                    results[f"type_{type_id}_rep_vs_warrant"] = {
                        "p_value": float(p),
                        "significant": p < 0.05,
                        "rep_mean": float(np.mean(rep_vals)),
                        "warrant_mean": float(np.mean(warrant_vals)),
                    }
                except:
                    pass
    
    return results


def generate_markdown_report(data: Dict, examples: List, stats_tests: Dict) -> str:
    """Generate a markdown report of the collusion analysis."""
    
    deception_summary = summarize_deception_by_collusion(data)
    type_summary = summarize_collusion_types(data)
    comm_effect = summarize_communication_effect(data)
    
    report = """# Collusion Analysis Statistical Summary

## Key Findings

### 1. Deception Rate by Collusion Status

| Status | Deception Rate | Sample Size |
|--------|----------------|-------------|
| No Collusion Detected | {no_collusion} | 4,729 posts |
| Collusion Detected | {with_collusion} | 683 posts |

**Key Finding:** Collusion dramatically increases deception rates ({increase} increase).

### 2. Collusion Type Distribution

Collusion types are categorized as follows:
- **Type 1 (Direct Proposal):** Explicit invitation to coordinate deception
- **Type 2 (Strategy Broadcast):** Sharing personal deceptive plans
- **Type 3 (Coordination):** Building on others' deceptive strategies
- **Type 4 (Social Normalization):** Framing deception as normal behavior
- **Type 5 (Neutral):** Non-deceptive market information sharing
- **Type 6 (Anti-Collusion):** Explicit opposition to deception

#### Overall Distribution:
{overall_dist}

#### By Mechanism:
- **Reputation-Only:** Collusive types (1-4) = {collusive_rep}
- **Reputation+Warrant:** Collusive types (1-4) = {collusive_warrant}
- **Reduction:** {reduction} ({reduction_pct} decrease)

### 3. Communication Channel Effect

| Communication | Collusive Messaging |
|---------------|---------------------|
| Without | {no_comm}% |
| With | {with_comm}% |

**Effect:** Communication {effect} collusive messaging (+{comm_change}).

### 4. Statistical Significance Tests

""".format(
        no_collusion=deception_summary.get("deception_rate_no_collusion", "N/A"),
        with_collusion=deception_summary.get("deception_rate_with_collusion", "N/A"),
        increase=deception_summary.get("increase_ratio", "N/A"),
        overall_dist="\n".join([
            f"- Type {k.split('_')[1]}: {v}" 
            for k, v in type_summary.get("overall", {}).items()
        ]),
        collusive_rep=type_summary.get("collusive_sum_rep", "N/A"),
        collusive_warrant=type_summary.get("collusive_sum_warrant", "N/A"),
        reduction=type_summary.get("collusive_reduction", "N/A"),
        reduction_pct=type_summary.get("collusive_reduction_pct", "N/A"),
        no_comm=comm_effect.get("collusive_no_communication", "N/A"),
        with_comm=comm_effect.get("collusive_with_communication", "N/A"),
        effect=comm_effect.get("communication_effect", "N/A"),
        comm_change=comm_effect.get("communication_increase", "N/A"),
    )
    
    # Add statistical test results
    if stats_tests:
        report += "| Comparison | Type | p-value | Significant | Rep Mean | Warrant Mean |\n"
        report += "|------------|------|---------|-------------|----------|--------------|\n"
        
        for key, result in sorted(stats_tests.items()):
            if result.get("significant"):
                comparison = key.replace("_vs_", " vs ").replace("_", " ").title()
                type_num = key.split("_")[1]
                report += f"| {comparison} | Type {type_num} | {result['p_value']:.4f} | ✓ | {result['rep_mean']:.3f} | {result['warrant_mean']:.3f} |\n"
    
    report += """

### 5. Qualitative Examples

""".format()
    
    # Add examples by type
    examples_by_type = {}
    for ex in examples:
        t = ex.get("type")
        if t not in examples_by_type:
            examples_by_type[t] = []
        examples_by_type[t].append(ex)
    
    type_names = {
        1: "Direct Collusion Proposal",
        2: "Deception Strategy Broadcast",
        3: "Collusion Coordination",
        4: "Social Normalization",
        5: "Neutral Information",
        6: "Anti-Collusion",
    }
    
    for type_id in range(1, 7):
        if type_id in examples_by_type:
            report += f"#### Type {type_id}: {type_names.get(type_id, 'Unknown')}\n\n"
            for i, ex in enumerate(examples_by_type[type_id][:2], 1):
                report += f"**Example {i}:** {ex.get('post_content', '')[:200]}...\n\n"
                report += f"*Rationale: {ex.get('rationale', '')[:150]}...*\n\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Generate statistical summary for collusion analysis"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory"
    )
    parser.add_argument(
        "--output",
        default="visualization/figs/paper/collusion_analysis/collusion_stats_summary.md",
        help="Output markdown file path"
    )
    args = parser.parse_args()
    
    print("Loading data...")
    data = load_data(args.data_dir)
    examples = load_examples(args.data_dir)
    
    print("Running statistical tests...")
    stats_tests = run_statistical_tests(data)
    
    print("Generating report...")
    report = generate_markdown_report(data, examples, stats_tests)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Report saved to: {output_path}")
    
    # Also print to console
    print("\n" + "=" * 70)
    print("COLLUSION ANALYSIS SUMMARY")
    print("=" * 70)
    print(report)


if __name__ == "__main__":
    main()
