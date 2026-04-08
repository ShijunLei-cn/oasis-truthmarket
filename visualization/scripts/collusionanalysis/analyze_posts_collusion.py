#!/usr/bin/env python3
"""
Analyze Posts Data for Collusion Detection

This script analyzes the raw posts data to generate additional
collusion-related metrics beyond what was annotated.

It reads from:
- data/case_analysis/posts_extracted.jsonl
- data/case_analysis/posts_labeled.jsonl
- data/case_analysis/sample_labeled.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any

import pandas as pd


def load_jsonl(filepath: str) -> List[Dict]:
    """Load data from a JSONL file."""
    data = []
    path = Path(filepath)
    if not path.exists():
        return data
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data


def analyze_posts_distribution(posts: List[Dict]) -> Dict[str, Any]:
    """Analyze distribution of posts across experiments and rounds."""
    if not posts:
        return {}
    
    exp_counter = Counter()
    round_counter = Counter()
    agent_counter = Counter()
    
    for post in posts:
        exp_id = post.get("experiment_id", "unknown")
        round_num = post.get("round", "unknown")
        agent = post.get("agent_name", "unknown")
        
        exp_counter[exp_id] += 1
        round_counter[round_num] += 1
        agent_counter[agent] += 1
    
    return {
        "total_posts": len(posts),
        "experiments": dict(exp_counter),
        "rounds": dict(round_counter),
        "unique_agents": len(agent_counter),
        "posts_per_round": {
            "mean": sum(round_counter.values()) / len(round_counter) if round_counter else 0,
            "min": min(round_counter.values()) if round_counter else 0,
            "max": max(round_counter.values()) if round_counter else 0,
        }
    }


def analyze_labeled_posts(labeled_posts: List[Dict]) -> Dict[str, Any]:
    """Analyze distribution of labels in labeled posts."""
    if not labeled_posts:
        return {}
    
    type_counter = Counter()
    collusion_counter = 0
    
    for post in labeled_posts:
        label = post.get("label") or post.get("type") or post.get("collusion_type")
        if label:
            type_counter[label] += 1
        
        is_collusion = post.get("is_collusion") or post.get("collusive")
        if is_collusion:
            collusion_counter += 1
    
    total = len(labeled_posts)
    
    return {
        "total_labeled": total,
        "type_distribution": dict(type_counter),
        "collusion_count": collusion_counter,
        "collusion_rate": collusion_counter / total if total > 0 else 0,
        "types": {
            str(k): f"{v/total*100:.2f}%" for k, v in type_counter.items()
        }
    }


def analyze_by_condition(labeled_posts: List[Dict]) -> Dict[str, Dict]:
    """Analyze posts by experimental condition."""
    condition_data = defaultdict(lambda: {
        "total": 0,
        "collusive": 0,
        "types": Counter()
    })
    
    for post in labeled_posts:
        exp_id = post.get("experiment_id", "unknown")
        label = post.get("label") or post.get("type")
        is_collusion = post.get("is_collusion") or post.get("collusive")
        
        condition_data[exp_id]["total"] += 1
        if label:
            condition_data[exp_id]["types"][label] += 1
        if is_collusion:
            condition_data[exp_id]["collusive"] += 1
    
    # Convert to percentage
    result = {}
    for cond, data in condition_data.items():
        total = data["total"]
        result[cond] = {
            "total_posts": total,
            "collusive_posts": data["collusive"],
            "collusion_rate": data["collusive"] / total if total > 0 else 0,
            "type_distribution": {
                str(k): f"{v/total*100:.2f}%" for k, v in data["types"].items()
            }
        }
    
    return dict(result)


def generate_summary_table(labeled_posts: List[Dict]) -> pd.DataFrame:
    """Generate a summary table of posts by condition and type."""
    condition_data = analyze_by_condition(labeled_posts)
    
    rows = []
    for cond, data in condition_data.items():
        row = {
            "condition": cond,
            "total_posts": data["total_posts"],
            "collusion_rate": f"{data['collusion_rate']*100:.2f}%",
            "collusive_posts": data["collusive_posts"],
        }
        # Add type percentages
        for type_id in range(1, 7):
            type_key = str(type_id)
            row[f"type_{type_id}"] = data["type_distribution"].get(type_key, "0.00%")
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df.sort_values("condition")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze posts data for collusion detection"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory"
    )
    parser.add_argument(
        "--output-dir",
        default="visualization/figs/paper/collusion_analysis",
        help="Output directory"
    )
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Posts Data Analysis for Collusion Detection")
    print("=" * 70)
    
    # Load data
    print("\nLoading data files...")
    posts_extracted = load_jsonl(str(data_dir / "case_analysis" / "posts_extracted.jsonl"))
    posts_labeled = load_jsonl(str(data_dir / "case_analysis" / "posts_labeled.jsonl"))
    sample_labeled = load_jsonl(str(data_dir / "case_analysis" / "sample_labeled.jsonl"))
    
    print(f"  - posts_extracted.jsonl: {len(posts_extracted)} posts")
    print(f"  - posts_labeled.jsonl: {len(posts_labeled)} posts")
    print(f"  - sample_labeled.jsonl: {len(sample_labeled)} posts")
    
    # Analyze
    print("\nAnalyzing posts distribution...")
    posts_dist = analyze_posts_distribution(posts_extracted)
    if posts_dist:
        print(f"  Total posts: {posts_dist.get('total_posts', 0)}")
        print(f"  Unique agents: {posts_dist.get('unique_agents', 0)}")
        print(f"  Posts per round: {posts_dist.get('posts_per_round', {}).get('mean', 0):.1f} (mean)")
    
    print("\nAnalyzing labeled posts...")
    labeled_analysis = analyze_labeled_posts(posts_labeled + sample_labeled)
    if labeled_analysis:
        print(f"  Total labeled: {labeled_analysis.get('total_labeled', 0)}")
        print(f"  Collusion rate: {labeled_analysis.get('collusion_rate', 0)*100:.2f}%")
        print(f"  Type distribution:")
        for t, pct in labeled_analysis.get("types", {}).items():
            print(f"    Type {t}: {pct}")
    
    print("\nAnalyzing by condition...")
    condition_analysis = analyze_by_condition(posts_labeled + sample_labeled)
    
    # Generate table
    print("\nGenerating summary table...")
    df = generate_summary_table(posts_labeled + sample_labeled)
    
    # Save table
    table_path = output_dir / "posts_analysis_by_condition.csv"
    df.to_csv(table_path, index=False)
    print(f"  Saved: {table_path}")
    
    # Print table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE: Posts by Condition")
    print("=" * 70)
    print(df.to_string(index=False))
    
    # Save detailed analysis
    detailed_path = output_dir / "posts_analysis_detailed.json"
    detailed_analysis = {
        "posts_distribution": posts_dist,
        "labeled_analysis": labeled_analysis,
        "condition_analysis": condition_analysis,
    }
    with open(detailed_path, "w", encoding="utf-8") as f:
        json.dump(detailed_analysis, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed analysis saved: {detailed_path}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
