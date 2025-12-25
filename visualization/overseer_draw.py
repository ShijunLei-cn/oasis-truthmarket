#!/usr/bin/env python3
"""
Overseer Collusion Analysis Visualization
Analyzes collusion behavior across multiple experiments and generates visualizations

Usage:
    # Analyze single experiment
    python visualization/overseer_draw.py --experiment-id r_wsc_F
    
    # Analyze multiple experiments
    python visualization/overseer_draw.py --experiment-ids r_wsc_F r_wsc_R rw_wsc_F rw_wsc_R
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.core.overseer_agent import analyze_collusion
from visualization.core.data_loader import ExperimentDataLoader
from visualization.core.utils import plot_save, setup_plot_style
from config import SimulationConfig


def find_db_files(experiment_dir: str) -> List[str]:
    """
    Find all database files in an experiment directory
    
    Args:
        experiment_dir: Path to experiment directory
        
    Returns:
        List of database file paths
    """
    if not os.path.exists(experiment_dir):
        return []
    
    db_files = []
    for file in os.listdir(experiment_dir):
        if file.startswith('run_') and file.endswith('.db'):
            db_files.append(os.path.join(experiment_dir, file))
    
    return sorted(db_files)


async def analyze_experiment_collusion(experiment_id: str, 
                                      output_dir: Optional[str] = None,
                                      model_platform: str = "openai",
                                      model_type: str = "gpt-4o-mini",
                                      temperature: float = 0.1) -> Dict[str, Any]:
    """
    Analyze collusion for all database files in an experiment
    
    Args:
        experiment_id: Experiment ID
        output_dir: Directory to save analysis results (default: experiments/{experiment_id}/collusion_analysis)
        model_platform: LLM platform
        model_type: LLM model type
        temperature: Temperature for LLM
        
    Returns:
        Dictionary containing analysis results for all runs
    """
    experiment_dir = os.path.join("experiments", experiment_id)
    if not os.path.exists(experiment_dir):
        raise FileNotFoundError(f"Experiment directory not found: {experiment_dir}")
    
    if output_dir is None:
        output_dir = os.path.join(experiment_dir, "collusion_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    db_files = find_db_files(experiment_dir)
    if not db_files:
        print(f"Warning: No database files found in {experiment_dir}")
        return {}
    
    print(f"\nAnalyzing {len(db_files)} database files in experiment {experiment_id}...")
    
    experiment_results = {
        'experiment_id': experiment_id,
        'analysis_timestamp': datetime.now().isoformat(),
        'runs': {}
    }
    
    for db_path in db_files:
        db_name = os.path.basename(db_path)
        run_key = db_name.replace('.db', '')
        
        print(f"  Analyzing {db_name}...")
        
        try:
            # Analyze collusion for this database
            output_path = os.path.join(output_dir, f"{run_key}_collusion_analysis.json")
            results = await analyze_collusion(
                db_path=db_path,
                model_platform=model_platform,
                model_type=model_type,
                temperature=temperature,
                output_path=output_path
            )
            
            experiment_results['runs'][run_key] = {
                'db_path': db_path,
                'analysis_path': output_path,
                'results': results
            }
            
        except Exception as e:
            print(f"    Error analyzing {db_name}: {e}")
            experiment_results['runs'][run_key] = {
                'db_path': db_path,
                'error': str(e)
            }
    
    # Save experiment-level summary
    summary_path = os.path.join(output_dir, "experiment_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(experiment_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nExperiment analysis complete. Results saved to: {output_dir}")
    return experiment_results


def load_collusion_results(experiment_id: str) -> Dict[str, Any]:
    """
    Load collusion analysis results for an experiment
    
    Args:
        experiment_id: Experiment ID
        
    Returns:
        Dictionary containing loaded results
    """
    collusion_dir = os.path.join("experiments", experiment_id, "collusion_analysis")
    
    if not os.path.exists(collusion_dir):
        print(f"Warning: Collusion analysis directory not found: {collusion_dir}")
        return {'experiment_id': experiment_id, 'runs': {}}
    
    # Try to load experiment summary first
    summary_path = os.path.join(collusion_dir, "experiment_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Otherwise, load individual run analyses
    results = {
        'experiment_id': experiment_id,
        'runs': {}
    }
    
    for file in os.listdir(collusion_dir):
        if file.endswith('_collusion_analysis.json') and not file == 'experiment_summary.json':
            run_key = file.replace('_collusion_analysis.json', '')
            analysis_path = os.path.join(collusion_dir, file)
            
            try:
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                    results['runs'][run_key] = {
                        'analysis_path': analysis_path,
                        'summary': analysis_data.get('summary', {}),
                        'round_analyses': analysis_data.get('round_analyses', [])
                    }
            except Exception as e:
                print(f"Warning: Could not load {analysis_path}: {e}")
    
    return results


def prepare_round_data(experiment_results: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Prepare collusion score data by round for visualization
    
    Args:
        experiment_results: Experiment analysis results
        
    Returns:
        Dictionary mapping round numbers to score statistics
    """
    round_scores = defaultdict(list)  # round -> list of scores from different runs
    
    for run_key, run_data in experiment_results.get('runs', {}).items():
        if 'error' in run_data:
            continue
        
        # Try to get round_analyses from different possible structures
        round_analyses = None
        if 'results' in run_data and isinstance(run_data['results'], list):
            round_analyses = run_data['results']
        elif 'round_analyses' in run_data:
            round_analyses = run_data['round_analyses']
        elif 'analysis_path' in run_data:
            # Try to load from file
            try:
                analysis_path = run_data['analysis_path']
                if os.path.exists(analysis_path):
                    with open(analysis_path, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                        round_analyses = analysis_data.get('round_analyses', [])
            except Exception as e:
                print(f"Warning: Could not load analysis from {run_data.get('analysis_path', 'unknown')}: {e}")
                continue
        
        if not round_analyses:
            continue
        
        # Extract scores by round
        for analysis in round_analyses:
            round_num = analysis.get('round')
            score = analysis.get('collusion_score')
            if round_num is not None and score is not None:
                round_scores[int(round_num)].append(float(score))
    
    # Calculate statistics
    round_stats = {}
    for round_num in sorted(round_scores.keys()):
        scores = round_scores[round_num]
        if scores:
            round_stats[round_num] = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores) if len(scores) > 1 else 0.0),
                'count': len(scores),
                'scores': scores
            }
    
    return round_stats


def plot_single_experiment(experiment_id: str, 
                           output_dir: str,
                           experiment_results: Dict[str, Any],
                           color: str = None,
                           marker: str = None,
                           linestyle: str = None) -> None:
    """
    Plot collusion score progression for a single experiment
    
    Args:
        experiment_id: Experiment ID
        output_dir: Output directory for saving plots
        experiment_results: Experiment analysis results
        color: Line color
        marker: Marker style
        linestyle: Line style
    """
    round_stats = prepare_round_data(experiment_results)
    
    if not round_stats:
        print(f"Warning: No round data available for {experiment_id}")
        return
    
    rounds = sorted(round_stats.keys())
    means = [round_stats[r]['mean'] for r in rounds]
    stds = [round_stats[r]['std'] for r in rounds]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot with shaded area
    ax.plot(rounds, means, color=color or 'blue', marker=marker or 'o', 
            linestyle=linestyle or '-', linewidth=2, label=experiment_id, markersize=6)
    
    # Add shaded area for std
    ax.fill_between(rounds, 
                    np.array(means) - np.array(stds),
                    np.array(means) + np.array(stds),
                    color=color or 'blue', alpha=0.25)
    
    ax.set_xlabel('Round', fontweight='bold', fontsize=12)
    ax.set_ylabel('Collusion Score', fontweight='bold', fontsize=12)
    ax.set_title(f'Collusion Score Progression - {experiment_id}', fontweight='bold', fontsize=14)
    ax.set_ylim(0.5, 4.5)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(['1 (No)', '2 (Mild)', '3 (Moderate)', '4 (Strong)'])
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Save plot
    plot_save(fig, output_dir, f'collusion_score_{experiment_id}')
    
    # Save data
    data_path = os.path.join(output_dir, f'collusion_score_data_{experiment_id}.json')
    data_dict = {
        'experiment_id': experiment_id,
        'rounds': rounds,
        'means': means,
        'stds': stds,
        'round_stats': {str(k): v for k, v in round_stats.items()}
    }
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)


def plot_multiple_experiments(experiment_ids: List[str],
                              output_dir: str,
                              experiment_results_dict: Dict[str, Dict[str, Any]]) -> None:
    """
    Plot collusion score progression for multiple experiments on the same figure
    
    Args:
        experiment_ids: List of experiment IDs
        output_dir: Output directory for saving plots
        experiment_results_dict: Dictionary mapping experiment_id to results
    """
    # Color palette for multiple experiments
    colors = sns.color_palette("tab10", n_colors=len(experiment_ids))
    markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'X']
    linestyles = ['-', '--', '-.', ':', '-', '--', '-.', ':']
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    for i, experiment_id in enumerate(experiment_ids):
        if experiment_id not in experiment_results_dict:
            continue
        
        experiment_results = experiment_results_dict[experiment_id]
        round_stats = prepare_round_data(experiment_results)
        
        if not round_stats:
            continue
        
        rounds = sorted(round_stats.keys())
        means = [round_stats[r]['mean'] for r in rounds]
        stds = [round_stats[r]['std'] for r in rounds]
        
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]
        linestyle = linestyles[i % len(linestyles)]
        
        # Plot with shaded area
        ax.plot(rounds, means, color=color, marker=marker, linestyle=linestyle,
                linewidth=2, label=experiment_id, markersize=6, alpha=0.8)
        
        # Add shaded area for std
        ax.fill_between(rounds,
                        np.array(means) - np.array(stds),
                        np.array(means) + np.array(stds),
                        color=color, alpha=0.2)
    
    ax.set_xlabel('Round', fontweight='bold', fontsize=12)
    ax.set_ylabel('Collusion Score', fontweight='bold', fontsize=12)
    ax.set_title('Collusion Score Progression Across Experiments', fontweight='bold', fontsize=14)
    ax.set_ylim(0.5, 4.5)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(['1 (No)', '2 (Mild)', '3 (Moderate)', '4 (Strong)'])
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    
    # Save plot
    plot_save(fig, output_dir, 'collusion_score_comparison')
    
    # Save aggregated data
    aggregated_data = {
        'experiment_ids': experiment_ids,
        'analysis_timestamp': datetime.now().isoformat(),
        'experiments': {}
    }
    
    for experiment_id in experiment_ids:
        if experiment_id in experiment_results_dict:
            experiment_results = experiment_results_dict[experiment_id]
            round_stats = prepare_round_data(experiment_results)
            
            if round_stats:
                rounds = sorted(round_stats.keys())
                aggregated_data['experiments'][experiment_id] = {
                    'rounds': rounds,
                    'means': [round_stats[r]['mean'] for r in rounds],
                    'stds': [round_stats[r]['std'] for r in rounds],
                    'round_stats': {str(k): v for k, v in round_stats.items()}
                }
    
    data_path = os.path.join(output_dir, 'collusion_score_comparison_data.json')
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated_data, f, indent=2, ensure_ascii=False)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze and visualize seller collusion behavior across experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single experiment
  %(prog)s --experiment-id r_wsc_F
  
  # Analyze multiple experiments
  %(prog)s --experiment-ids r_wsc_F r_wsc_R rw_wsc_F rw_wsc_R
  
  # Analyze without re-running LLM analysis (use existing results)
  %(prog)s --experiment-ids r_wsc_F r_wsc_R --skip-analysis
        """
    )
    
    parser.add_argument(
        '--experiment-id',
        dest='experiment_id',
        help='Single experiment ID to analyze'
    )
    
    parser.add_argument(
        '--experiment-ids',
        dest='experiment_ids',
        nargs='+',
        help='Multiple experiment IDs to analyze and compare'
    )
    
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        default='analysis/communication_effects',
        help='Output directory for plots and data (default: analysis/communication_effects)'
    )
    
    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip LLM analysis, only load existing results and generate plots'
    )
    
    parser.add_argument(
        '--model-platform',
        default='openai',
        help='LLM platform (default: openai)'
    )
    
    parser.add_argument(
        '--model-type',
        default='gpt-4o-mini',
        help='LLM model type (default: gpt-4o-mini)'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Temperature for LLM (default: 0.1)'
    )
    
    args = parser.parse_args()
    
    # Determine experiment IDs
    experiment_ids = []
    if args.experiment_ids:
        experiment_ids = args.experiment_ids
    elif args.experiment_id:
        experiment_ids = [args.experiment_id]
    else:
        parser.error("Must provide either --experiment-id or --experiment-ids")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup plotting style
    setup_plot_style()
    
    # Analyze or load results for each experiment
    experiment_results_dict = {}
    
    for experiment_id in experiment_ids:
        print(f"\n{'='*60}")
        print(f"Processing experiment: {experiment_id}")
        print(f"{'='*60}")
        
        if args.skip_analysis:
            # Load existing results
            print(f"Loading existing analysis results for {experiment_id}...")
            experiment_results_dict[experiment_id] = load_collusion_results(experiment_id)
        else:
            # Run analysis
            print(f"Running collusion analysis for {experiment_id}...")
            results = await analyze_experiment_collusion(
                experiment_id=experiment_id,
                model_platform=args.model_platform,
                model_type=args.model_type,
                temperature=args.temperature
            )
            experiment_results_dict[experiment_id] = results
    
    # Generate visualizations
    print(f"\n{'='*60}")
    print("Generating visualizations...")
    print(f"{'='*60}")
    
    if len(experiment_ids) == 1:
        # Single experiment: generate individual plot
        experiment_id = experiment_ids[0]
        plot_single_experiment(
            experiment_id=experiment_id,
            output_dir=args.output_dir,
            experiment_results=experiment_results_dict[experiment_id]
        )
        print(f"\n✓ Single experiment plot saved to {args.output_dir}/collusion_score_{experiment_id}.png")
    else:
        # Multiple experiments: generate comparison plot and individual plots
        plot_multiple_experiments(
            experiment_ids=experiment_ids,
            output_dir=args.output_dir,
            experiment_results_dict=experiment_results_dict
        )
        print(f"\n✓ Comparison plot saved to {args.output_dir}/collusion_score_comparison.png")
        
        # Also generate individual plots
        for experiment_id in experiment_ids:
            if experiment_id in experiment_results_dict:
                plot_single_experiment(
                    experiment_id=experiment_id,
                    output_dir=args.output_dir,
                    experiment_results=experiment_results_dict[experiment_id]
                )
    
    print(f"\n{'='*60}")
    print("Analysis complete!")
    print(f"Results saved to: {args.output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())

