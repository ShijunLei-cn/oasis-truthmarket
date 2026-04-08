#!/usr/bin/env python3
"""
Extract Seller Posts from Experiment Actions Files

This script extracts seller communication posts from experiment run files.
These posts will then be annotated by LLM as judge for collusion analysis.

Data Flow:
    experiments/gpt-4o-mini/paper/rqX/.../run_*_actions.json
        ↓
    [Extract seller posts]
        ↓
    paper/data/case_analysis/posts_extracted.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def extract_posts_from_actions(actions_file: Path, experiment_id: str, run_id: int) -> List[Dict]:
    """Extract seller posts from a single run's actions file.
    
    Args:
        actions_file: Path to run_*_actions.json
        experiment_id: Experiment identifier (e.g., "r_wsc_R_policy_making")
        run_id: Run number
        
    Returns:
        List of post dictionaries
    """
    posts = []
    
    try:
        data = json.loads(actions_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ERROR loading {actions_file}: {e}")
        return posts
    
    for round_data in data:
        round_num = round_data.get("round", 0)
        phase = round_data.get("phase", "")
        agent_infos = round_data.get("agent_infos", [])
        
        for agent_info in agent_infos:
            agent_name = agent_info.get("agent_name", "unknown")
            
            # Skip buyers
            if not agent_name.startswith("seller"):
                continue
            
            action_info = agent_info.get("agent_action_info", {})
            if not isinstance(action_info, dict):
                continue
            
            action_name = action_info.get("action_name", "")
            
            # Look for communication actions (posts)
            # Based on diagnostic: action_name is "create_post"
            if action_name in ["create_post", "post_to_forum", "post_to_social_media", 
                              "social_media_post", "forum_post", "make_post", "post"]:
                
                # Try to get content from action_args (JSON string format)
                action_args = action_info.get("action_args", "{}")
                if isinstance(action_args, str):
                    try:
                        args_dict = json.loads(action_args)
                        post_content = args_dict.get("content", "")
                    except json.JSONDecodeError:
                        post_content = ""
                elif isinstance(action_args, dict):
                    post_content = action_args.get("content", "")
                else:
                    post_content = ""
                
                # Fallback to direct content field
                if not post_content:
                    post_content = action_info.get("post_content", "") or \
                                   action_info.get("message", "") or \
                                   action_info.get("content", "")
                
                if post_content and isinstance(post_content, str):
                    # Extract reasoning if available
                    action_reasoning = action_info.get("action_reasoning", "")
                    
                    posts.append({
                        "experiment_id": experiment_id,
                        "run_id": run_id,
                        "round": round_num,
                        "phase": phase,
                        "agent_name": agent_name,
                        "action_type": action_name,
                        "post_content": post_content,
                        "action_reasoning": action_reasoning[:500] if action_reasoning else "",
                        "post_length": len(post_content),
                    })
    
    return posts


def parse_experiment_id(exp_id: str) -> Dict[str, str]:
    """Parse experiment ID to extract components.
    
    Format examples:
        - r_wsc_F_policy_making
        - r_wsc_R_pressure_quickprofits  
        - rw_wsc_F_psychological-based-attack
        - rw_wsc_R_policy_making
        
    Parsed as:
        - r/rw: mechanism (Reputation vs Reputation+Warrant)
        - wsc: fixed string
        - F/R: channel (Fake/No-Comm vs Real/With-Comm)
        - rest: constraint type
    """
    parts = exp_id.split("_")
    
    if len(parts) < 4:
        return {
            "experiment_id": exp_id,
            "mechanism": "unknown",
            "channel": "unknown",
            "has_communication": False,
            "constraint": "unknown",
        }
    
    # First part: r or rw (mechanism)
    mech_prefix = parts[0]
    has_warrant = mech_prefix.startswith("rw")
    mechanism = "Reputation+Warrant" if has_warrant else "Reputation"
    
    # Third part: F or R (channel)
    channel_char = parts[2]
    channel = "Real (With Comm)" if channel_char == "R" else "Fake (No Comm)"
    has_communication = channel_char == "R"
    
    # Rest: constraint type
    constraint = "_".join(parts[3:]) if len(parts) > 3 else "unknown"
    
    result = {
        "experiment_id": exp_id,
        "mechanism": mechanism,
        "mechanism_prefix": mech_prefix,
        "channel": channel,
        "channel_char": channel_char,
        "has_communication": has_communication,
        "has_warrant": has_warrant,
        "constraint": constraint,
    }
    
    return result


def extract_all_posts(experiment_dir: str, experiment_id: str) -> List[Dict]:
    """Extract all posts from all runs in an experiment.
    
    Args:
        experiment_dir: Path to experiment directory
        experiment_id: Experiment identifier
        
    Returns:
        List of all posts from all runs
    """
    path = Path(experiment_dir)
    if not path.exists():
        print(f"  WARNING: Experiment directory not found: {experiment_dir}")
        return []
    
    all_posts = []
    
    # Find all action files
    action_files = sorted(path.glob("run_*_actions.json"))
    
    for action_file in action_files:
        run_id = int(action_file.stem.split("_")[1])
        posts = extract_posts_from_actions(action_file, experiment_id, run_id)
        all_posts.extend(posts)
        print(f"  Run {run_id}: {len(posts)} posts extracted")
    
    return all_posts


def save_posts_jsonl(posts: List[Dict], output_path: Path) -> None:
    """Save posts to JSONL format.
    
    Args:
        posts: List of post dictionaries
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + "\n")
    
    print(f"  Saved {len(posts)} posts to {output_path}")


def generate_summary(posts: List[Dict]) -> Dict[str, Any]:
    """Generate summary statistics of extracted posts.
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        Summary dictionary
    """
    if not posts:
        return {}
    
    # Count by experiment
    exp_counts = defaultdict(int)
    # Count by round
    round_counts = defaultdict(int)
    # Count by agent
    agent_counts = defaultdict(int)
    
    for post in posts:
        exp_counts[post["experiment_id"]] += 1
        round_counts[post["round"]] += 1
        agent_counts[post["agent_name"]] += 1
    
    # Parse experiments
    by_mechanism = defaultdict(int)
    by_channel = defaultdict(int)
    by_constraint = defaultdict(int)
    
    for exp_id in exp_counts.keys():
        parsed = parse_experiment_id(exp_id)
        by_mechanism[parsed["mechanism"]] += exp_counts[exp_id]
        by_channel[parsed["channel"]] += exp_counts[exp_id]
        by_constraint[parsed["constraint"]] += exp_counts[exp_id]
    
    return {
        "total_posts": len(posts),
        "unique_experiments": len(exp_counts),
        "unique_agents": len(agent_counts),
        "rounds_covered": sorted(round_counts.keys()),
        "by_experiment": dict(exp_counts),
        "by_mechanism": dict(by_mechanism),
        "by_channel": dict(by_channel),
        "by_constraint": dict(by_constraint),
        "posts_per_round": {
            "mean": len(posts) / len(round_counts) if round_counts else 0,
            "min": min(round_counts.values()) if round_counts else 0,
            "max": max(round_counts.values()) if round_counts else 0,
        }
    }


def print_summary(summary: Dict[str, Any]) -> None:
    """Print summary in a readable format."""
    print("\n" + "=" * 60)
    print("POSTS EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total posts extracted: {summary.get('total_posts', 0)}")
    print(f"Unique experiments: {summary.get('unique_experiments', 0)}")
    print(f"Unique agents: {summary.get('unique_agents', 0)}")
    
    print("\nBy Mechanism:")
    for mech, count in summary.get("by_mechanism", {}).items():
        print(f"  - {mech}: {count} posts")
    
    print("\nBy Channel:")
    for channel, count in summary.get("by_channel", {}).items():
        print(f"  - {channel}: {count} posts")
    
    print("\nBy Constraint:")
    for constraint, count in summary.get("by_constraint", {}).items():
        print(f"  - {constraint}: {count} posts")
    
    print("\nPosts per Round:")
    ppr = summary.get("posts_per_round", {})
    print(f"  - Mean: {ppr.get('mean', 0):.1f}")
    print(f"  - Range: {ppr.get('min', 0)} - {ppr.get('max', 0)}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract seller posts from experiment actions files"
    )
    parser.add_argument(
        "--experiments-dir",
        default="experiments/gpt-4o-mini/paper",
        help="Path to experiments directory"
    )
    parser.add_argument(
        "--rq",
        choices=["rq1", "rq2", "rq3", "all"],
        default="all",
        help="Which RQ to process"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: experiments/gpt-4o-mini/paper/data)"
    )
    parser.add_argument(
        "--experiment-id",
        default=None,
        help="Specific experiment ID to process (e.g., r_wsc_R_policy_making)"
    )
    args = parser.parse_args()
    
    # Set output directory
    if args.output_dir:
        output_base = Path(args.output_dir)
    else:
        output_base = Path(args.experiments_dir) / "data" / "case_analysis"
    
    experiments_dir = Path(args.experiments_dir)
    
    print("=" * 60)
    print("POSTS EXTRACTION PIPELINE")
    print("=" * 60)
    print(f"Experiments directory: {experiments_dir}")
    print(f"Output directory: {output_base}")
    
    all_posts = []
    
    # Determine which experiments to process
    if args.experiment_id:
        # Process specific experiment
        experiments_to_process = [args.experiment_id]
    elif args.rq == "all":
        # Process all RQs
        experiments_to_process = []
        for rq_dir in sorted(experiments_dir.glob("rq*")):
            for exp_dir in sorted(rq_dir.iterdir()):
                if exp_dir.is_dir() and exp_dir.name != "data":
                    experiments_to_process.append(exp_dir.name)
    else:
        # Process specific RQ
        experiments_to_process = []
        rq_dir = experiments_dir / args.rq
        if rq_dir.exists():
            for exp_dir in sorted(rq_dir.iterdir()):
                if exp_dir.is_dir():
                    experiments_to_process.append(exp_dir.name)
    
    print(f"\nProcessing {len(experiments_to_process)} experiments...")
    
    for exp_id in experiments_to_process:
        # Find experiment directory
        exp_dir = None
        for rq_dir in sorted(experiments_dir.glob("rq*")):
            potential_dir = rq_dir / exp_id
            if potential_dir.exists():
                exp_dir = potential_dir
                break
        
        if not exp_dir:
            print(f"\n[SKIP] {exp_id}: Directory not found")
            continue
        
        print(f"\n[{exp_id}]")
        posts = extract_all_posts(str(exp_dir), exp_id)
        all_posts.extend(posts)
        print(f"  Total posts: {len(posts)}")
    
    # Save all posts
    output_path = output_base / "posts_extracted.jsonl"
    save_posts_jsonl(all_posts, output_path)
    
    # Generate and print summary
    summary = generate_summary(all_posts)
    print_summary(summary)
    
    # Save summary as JSON
    summary_path = output_base / "extraction_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
