import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import numpy as np

def load_probe_results(experiment_dir: str):
    """Load all cognitive probe results from the experiment directory."""
    path = Path(experiment_dir)
    all_results = []
    
    # Find all run_*_cognitive_probes.json files
    probe_files = list(path.glob("run_*_cognitive_probes.json"))
    if not probe_files:
        print(f"Warning: No probe result files found in {experiment_dir}")
        return pd.DataFrame()
        
    for file in probe_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.extend(data)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            
    return pd.DataFrame(all_results)

def plot_manipulation_heatmap(df: pd.DataFrame, output_path: Path):
    """Create a heatmap of manipulation detection rates per seller and probe type."""
    if df.empty:
        print("No data to plot.")
        return

    # Calculate detection rate: sum(manipulation_detected) / count(*)
    # Group by agent_id and vulnerability_type
    stats = df.groupby(['agent_id', 'vulnerability_type']).agg(
        detected_count=('manipulation_detected', 'sum'),
        total_count=('manipulation_detected', 'count')
    ).reset_index()
    
    stats['detection_rate'] = stats['detected_count'] / stats['total_count']
    
    # Pivot for heatmap: index=agent_id, columns=vulnerability_type, values=detection_rate
    pivot_df = stats.pivot(index='agent_id', columns='vulnerability_type', values='detection_rate')
    
    # Sort index and columns for better presentation
    pivot_df = pivot_df.sort_index()
    
    # Plotting
    plt.figure(figsize=(12, 8))
    
    # Academic style
    sns.set_theme(style="white")
    
    # Map vulnerability type names to more readable labels
    rename_map = {
        'initial_window': 'Initial Window',
        'reputation_lag': 'Reputation Lag',
        'value_imbalance': 'Value Imbalance',
        'reentry': 'Re-entry',
        'exit_strategy': 'Exit Strategy'
    }
    pivot_df.columns = [rename_map.get(col, col) for col in pivot_df.columns]
    
    ax = sns.heatmap(
        pivot_df, 
        annot=True, 
        fmt=".2f", 
        cmap="YlOrRd", 
        linewidths=.5, 
        cbar_kws={'label': 'Detection Rate (Detected / Total Tests)'},
        vmin=0, vmax=1
    )
    
    plt.title('RQ1: Cognitive Manipulation Detection Rate by Seller and Probe Type', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Probe Type (Manipulation Strategy)', fontsize=12, fontweight='bold')
    plt.ylabel('Seller ID', fontsize=12, fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated heatmap: {output_path}")

def extract_prefix_from_path(path_str: str) -> str:
    """Extract prefix from path (e.g., 'experiments/1230/r_wo' -> '1230', '1230/r_wo' -> '1230')"""
    path = Path(path_str)
    parts = path.parts
    
    # First, try to find pattern like 'experiments/1230/xxx' or '1230/xxx'
    for i, part in enumerate(parts):
        # Check if this part contains a slash (like '1230/r_wo')
        if '/' in part:
            prefix = part.split('/')[0]
            if prefix:
                return prefix
        # Check if this part is a numeric prefix and next part exists (like '1230' followed by 'r_wo')
        if part and part[0].isdigit() and i + 1 < len(parts):
            return part
    
    # Fallback: look for any numeric prefix
    for part in parts:
        if part and part[0].isdigit():
            return part
    return ""

def main():
    parser = argparse.ArgumentParser(description="Visualize RQ1 Cognitive Probe Results")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing run_*_cognitive_probes.json")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save figures (default: visualization/figs/{prefix}/rq1_analysis)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    
    # Determine output directory
    if args.output_dir is None:
        prefix = extract_prefix_from_path(args.input_dir)
        if prefix:
            output_dir = Path(f"visualization/figs/{prefix}/rq1_analysis")
        else:
            output_dir = Path("visualization/figs/rq1_analysis")
    else:
        output_dir = Path(args.output_dir)
    
    print(f"Analyzing probe results in {input_path}...")
    df = load_probe_results(args.input_dir)
    
    if not df.empty:
        # Plot 1: Heatmap
        plot_manipulation_heatmap(df, output_dir / "1_manipulation_heatmap.png")
        
        # We can add more plots later if needed
    else:
        print("Analysis skipped due to lack of data.")

if __name__ == "__main__":
    main()

