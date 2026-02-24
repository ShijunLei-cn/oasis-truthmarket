"""
Common utilities for OASIS Truth Market visualization scripts.

Provides shared functions for:
- Loading experiment results from JSON files
- Consistent color palettes and plot styling
- Multi-run aggregation helpers
- Experiment directory discovery
"""

import json
import os
import glob
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ──────────────────── Global Plot Style ────────────────────

# Use a clean, publication-ready style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "axes.unicode_minus": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "legend.framealpha": 0.9,
    "figure.figsize": (10, 6),
})

sns.set_theme(style="whitegrid", palette="muted")

# ──────────────────── Color Palettes ────────────────────

# Market type colors
MARKET_COLORS = {
    "reputation_only": "#4C78A8",        # Steel blue
    "reputation_and_warrant": "#F58518", # Orange
}

# Channel type colors
CHANNEL_COLORS = {
    "Fake": "#E45756",   # Coral red
    "Real": "#54A24B",   # Green
}

# Quality colors
QUALITY_COLORS = {
    "HQ": "#4C78A8",  # Blue
    "LQ": "#E45756",  # Red
}

# Honesty colors
HONESTY_COLORS = {
    True: "#54A24B",   # Green for honest
    False: "#E45756",  # Red for dishonest
}

# Vulnerability type colors (RQ1)
VULNERABILITY_COLORS = {
    "reputation_lag": "#E45756",
    "value_imbalance": "#F58518",
    "reentry": "#4C78A8",
    "initial_window": "#54A24B",
    "exit_strategy": "#9B59B6",
}

# Communication attack type colors (RQ3)
ATTACK_COLORS = {
    "base": "#4C78A8",
    "policy_making": "#54A24B",
    "pressure_quickprofits": "#F58518",
    "psychological-based-attack": "#E45756",
}

# Nice diverging palette for heatmaps
HEATMAP_CMAP = "RdYlGn"

# ──────────────────── Experiment Name Mapping ────────────────────

# Short labels for experiment configs
CONFIG_LABELS = {
    "r_wo": "R-Only",
    "rw_wo": "R+W",
    "r_wsc_F": "R | Seller-Fake",
    "r_wsc_R": "R | Seller-Real",
    "rw_wsc_F": "R+W | Seller-Fake",
    "rw_wsc_R": "R+W | Seller-Real",
    "r_wbc_F": "R | Buyer-Fake",
    "r_wbc_R": "R | Buyer-Real",
    "rw_wbc_F": "R+W | Buyer-Fake",
    "rw_wbc_R": "R+W | Buyer-Real",
    "rw_wbsc_R": "R+W | Both-Real",
}

ATTACK_LABELS = {
    "base": "Baseline",
    "policy_making": "Policy Making",
    "pressure_quickprofits": "Quick Profits Pressure",
    "psychological-based-attack": "Psychological Attack",
}


# ──────────────────── Data Loading ────────────────────

def load_results(filepath: str) -> pd.DataFrame:
    """Load a run_X_results.json file into a DataFrame."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def load_cognitive_probes(filepath: str) -> pd.DataFrame:
    """Load a run_X_cognitive_probes.json file into a DataFrame."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def load_actions(filepath: str) -> List[Dict]:
    """Load a run_X_actions.json file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_experiment_config(exp_dir: str) -> Dict:
    """Load experiment_config.json from an experiment directory."""
    config_path = os.path.join(exp_dir, "experiment_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def discover_run_files(exp_dir: str, pattern: str = "run_*_results.json") -> List[str]:
    """Discover all run result files in an experiment directory."""
    files = sorted(glob.glob(os.path.join(exp_dir, pattern)))
    return files


def load_all_runs(exp_dir: str) -> pd.DataFrame:
    """
    Load and concatenate all run results from an experiment directory.
    Adds a 'run_id' column to distinguish runs.
    """
    result_files = discover_run_files(exp_dir)
    if not result_files:
        return pd.DataFrame()

    dfs = []
    for fpath in result_files:
        fname = os.path.basename(fpath)
        # Extract run_id from filename like "run_1_results.json"
        run_id = int(fname.split("_")[1])
        df = load_results(fpath)
        df["run_id"] = run_id
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def load_all_cognitive_probes(exp_dir: str) -> pd.DataFrame:
    """Load and concatenate all cognitive probe files from an experiment directory."""
    probe_files = discover_run_files(exp_dir, "run_*_cognitive_probes.json")
    if not probe_files:
        return pd.DataFrame()

    dfs = []
    for fpath in probe_files:
        fname = os.path.basename(fpath)
        run_id = int(fname.split("_")[1])
        df = load_cognitive_probes(fpath)
        df["run_id"] = run_id
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


# ──────────────────── Metric Computation ────────────────────

def compute_round_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-round aggregate metrics from product-level results.

    Returns DataFrame with columns:
        round_num, total_products, sold_count, sale_rate,
        hq_count, lq_count, hq_ratio,
        honest_count, dishonest_count, honesty_rate,
        avg_seller_profit, avg_buyer_utility,
        avg_reputation, avg_price,
        deception_count, deception_rate,
        warrant_count, challenge_count
    """
    if df.empty:
        return pd.DataFrame()

    metrics = []
    for rnd, grp in df.groupby("round_num"):
        total = len(grp)
        sold = grp["sold"].sum() if "sold" in grp.columns else grp["is_sold"].sum()
        sale_rate = sold / total if total > 0 else 0

        hq = (grp["actual_quality"] == "HQ").sum() if "actual_quality" in grp.columns else (grp["quality"] == "HQ").sum()
        lq = total - hq
        hq_ratio = hq / total if total > 0 else 0

        honest = grp["is_honest"].sum() if "is_honest" in grp.columns else 0
        honesty_rate = honest / total if total > 0 else 0

        # Deception: advertised HQ but actual LQ
        if "advertised_quality" in grp.columns and "actual_quality" in grp.columns:
            deception = ((grp["advertised_quality"] == "HQ") & (grp["actual_quality"] == "LQ")).sum()
        else:
            deception = 0
        deception_rate = deception / total if total > 0 else 0

        sold_grp = grp[grp["status"] == "sold"] if "status" in grp.columns else grp[grp["sold"] == True]

        avg_profit = sold_grp["seller_profit"].mean() if len(sold_grp) > 0 and "seller_profit" in sold_grp.columns else 0
        avg_utility = sold_grp["buyer_utility"].mean() if len(sold_grp) > 0 and "buyer_utility" in sold_grp.columns else 0
        avg_rep = grp["reputation"].mean() if "reputation" in grp.columns else 0
        avg_price = sold_grp["price"].mean() if len(sold_grp) > 0 and "price" in sold_grp.columns else 0

        warrant_count = grp["has_warrant"].sum() if "has_warrant" in grp.columns else 0
        challenge_count = grp["is_challenged"].sum() if "is_challenged" in grp.columns else 0

        metrics.append({
            "round_num": rnd,
            "total_products": total,
            "sold_count": int(sold),
            "sale_rate": sale_rate,
            "hq_count": int(hq),
            "lq_count": int(lq),
            "hq_ratio": hq_ratio,
            "honest_count": int(honest),
            "dishonest_count": total - int(honest),
            "honesty_rate": honesty_rate,
            "deception_count": int(deception),
            "deception_rate": deception_rate,
            "avg_seller_profit": avg_profit,
            "avg_buyer_utility": avg_utility,
            "avg_reputation": avg_rep,
            "avg_price": avg_price,
            "warrant_count": int(warrant_count),
            "challenge_count": int(challenge_count),
        })

    return pd.DataFrame(metrics).sort_values("round_num").reset_index(drop=True)


def compute_multirun_round_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-round metrics aggregated across multiple runs.
    Returns mean and std for each metric.
    """
    if df.empty or "run_id" not in df.columns:
        return compute_round_metrics(df)

    all_run_metrics = []
    for run_id, run_df in df.groupby("run_id"):
        rm = compute_round_metrics(run_df)
        rm["run_id"] = run_id
        all_run_metrics.append(rm)

    if not all_run_metrics:
        return pd.DataFrame()

    combined = pd.concat(all_run_metrics, ignore_index=True)

    # Aggregate across runs
    numeric_cols = combined.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ("round_num", "run_id")]

    agg_dict = {col: ["mean", "std"] for col in numeric_cols}
    agg = combined.groupby("round_num").agg(agg_dict).reset_index()

    # Flatten multi-level columns
    agg.columns = [f"{c[0]}_{c[1]}" if c[1] else c[0] for c in agg.columns]
    agg = agg.rename(columns={"round_num_": "round_num"})

    return agg


def compute_overall_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Compute overall summary metrics from product-level results."""
    if df.empty:
        return {}

    total = len(df)
    sold = df["sold"].sum() if "sold" in df.columns else df["is_sold"].sum()

    hq = (df["actual_quality"] == "HQ").sum() if "actual_quality" in df.columns else (df["quality"] == "HQ").sum()
    honest = df["is_honest"].sum() if "is_honest" in df.columns else 0

    sold_df = df[df["status"] == "sold"] if "status" in df.columns else df[df["sold"] == True]

    if "advertised_quality" in df.columns and "actual_quality" in df.columns:
        deception = ((df["advertised_quality"] == "HQ") & (df["actual_quality"] == "LQ")).sum()
    else:
        deception = 0

    return {
        "total_products": total,
        "sale_rate": sold / total if total > 0 else 0,
        "hq_ratio": hq / total if total > 0 else 0,
        "honesty_rate": honest / total if total > 0 else 0,
        "deception_rate": deception / total if total > 0 else 0,
        "avg_seller_profit": sold_df["seller_profit"].mean() if len(sold_df) > 0 else 0,
        "avg_buyer_utility": sold_df["buyer_utility"].mean() if len(sold_df) > 0 else 0,
        "avg_reputation": df["reputation"].mean() if "reputation" in df.columns else 0,
        "warrant_rate": df["has_warrant"].mean() if "has_warrant" in df.columns else 0,
        "challenge_rate": df["is_challenged"].mean() if "is_challenged" in df.columns else 0,
    }


# ──────────────────── Plotting Helpers ────────────────────

def save_fig(fig: plt.Figure, output_dir: str, name: str, formats: List[str] = None):
    """Save figure in multiple formats."""
    if formats is None:
        formats = ["png", "pdf"]
    os.makedirs(output_dir, exist_ok=True)
    for fmt in formats:
        path = os.path.join(output_dir, f"{name}.{fmt}")
        fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_metric_over_rounds(
    data_dict: Dict[str, pd.DataFrame],
    metric: str,
    ylabel: str,
    title: str,
    output_dir: str,
    filename: str,
    colors: Optional[Dict[str, str]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    show_ci: bool = True,
):
    """
    Plot a metric over rounds for multiple experimental conditions.

    Args:
        data_dict: {label: DataFrame with multi-run round metrics}
        metric: column name prefix (e.g., 'honesty_rate')
        ylabel: Y-axis label
        title: Plot title
        output_dir: Output directory
        filename: Output filename (without extension)
        colors: Optional color mapping {label: color}
        ylim: Optional Y-axis limits
        show_ci: Whether to show confidence intervals (std)
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for label, df in data_dict.items():
        mean_col = f"{metric}_mean"
        std_col = f"{metric}_std"

        if mean_col not in df.columns:
            # Fallback: direct column name
            if metric in df.columns:
                mean_col = metric
                std_col = None
            else:
                continue

        x = df["round_num"]
        y = df[mean_col]
        color = colors.get(label) if colors else None

        ax.plot(x, y, marker="o", markersize=5, linewidth=2, label=label, color=color)

        if show_ci and std_col and std_col in df.columns:
            std = df[std_col]
            ax.fill_between(x, y - std, y + std, alpha=0.15, color=color)

    ax.set_xlabel("Round")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="best", frameon=True)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    if ylim is not None:
        ax.set_ylim(ylim)

    save_fig(fig, output_dir, filename)


def plot_grouped_bar(
    labels: List[str],
    data_dict: Dict[str, List[float]],
    ylabel: str,
    title: str,
    output_dir: str,
    filename: str,
    colors: Optional[Dict[str, str]] = None,
    error_dict: Optional[Dict[str, List[float]]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    rotation: int = 0,
):
    """
    Create a grouped bar chart.

    Args:
        labels: X-axis category labels
        data_dict: {group_name: [values per label]}
        ylabel: Y-axis label
        title: Plot title
        output_dir: Output directory
        filename: Output filename
        colors: Optional color mapping
        error_dict: Optional error bars {group_name: [std values]}
        ylim: Y-axis limits
        rotation: X-tick label rotation
    """
    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 1.5), 6))

    n_groups = len(data_dict)
    bar_width = 0.8 / n_groups
    x = np.arange(len(labels))

    for i, (group_name, values) in enumerate(data_dict.items()):
        offset = (i - n_groups / 2 + 0.5) * bar_width
        color = colors.get(group_name) if colors else None
        yerr = error_dict.get(group_name) if error_dict else None

        bars = ax.bar(
            x + offset, values, bar_width,
            label=group_name, color=color, edgecolor="white",
            linewidth=0.8, yerr=yerr, capsize=3,
        )

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(
                    f"{height:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8,
                )

    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=rotation, ha="right" if rotation else "center")
    ax.legend(loc="best", frameon=True)

    if ylim is not None:
        ax.set_ylim(ylim)

    save_fig(fig, output_dir, filename)


def ensure_output_dir(base_output: str, subfolder: str = "") -> str:
    """Create and return output directory."""
    out = os.path.join(base_output, subfolder) if subfolder else base_output
    os.makedirs(out, exist_ok=True)
    return out
