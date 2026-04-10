"""
Plotting modules for visualization
Base classes and specialized plotters for different types of charts
"""

import os
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D

from .utils import plot_save, read_table


class PlotterBase:
    """Base class for all plotters"""
    
    def __init__(self, out_dir: str, title_suffix: str = ''):
        """
        Initialize base plotter
        
        Args:
            out_dir: Output directory for saving plots
            title_suffix: Suffix to add to plot titles
        """
        self.out_dir = out_dir
        self.title_suffix = title_suffix
        os.makedirs(out_dir, exist_ok=True)
    
    def plot(self, *args, **kwargs):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement plot method")


class ReputationPlotter(PlotterBase):
    """Plotter for reputation-related visualizations"""
    
    def plot_reputation_over_rounds(self, reph: pd.DataFrame, filename: str = "reputation_over_rounds") -> None:
        """
        Plot seller reputation over rounds
        
        Args:
            reph: DataFrame with columns: round, seller_id, public_reputation_score
            filename: Output filename (without extension)
        """
        if reph.empty:
            return
        
        required = {"round", "seller_id", "public_reputation_score"}
        if not required.issubset(reph.columns):
            return
        
        df = reph.copy()
        df["round"] = pd.to_numeric(df["round"], errors="coerce")
        df["seller_id"] = pd.to_numeric(df["seller_id"], errors="coerce")
        
        # Create small vertical offsets to reduce overlap
        unique_sellers = np.sort(df["seller_id"].dropna().unique())
        seller_rank = {sid: i for i, sid in enumerate(unique_sellers)}
        delta = 0.15
        k = max(1, len(unique_sellers))
        offsets = {sid: ((seller_rank[sid] - (k - 1) / 2) / max(1, (k - 1))) * delta 
                  for sid in unique_sellers}
        df["rep_plot"] = df.apply(
            lambda r: r["public_reputation_score"] + offsets.get(r["seller_id"], 0.0), 
            axis=1
        )
        
        df = df.sort_values(["seller_id", "round"]).reset_index(drop=True)
        
        # Create plot
        palette = sns.color_palette("tab20", n_colors=max(3, len(unique_sellers)))
        g = sns.relplot(
            data=df,
            x="round",
            y="rep_plot",
            hue="seller_id",
            kind="line",
            marker="o",
            height=5.5,
            aspect=1.7,
            legend=True,
            palette=palette,
            linewidth=1.6,
        )
        g.set_axis_labels("Round", "Public Reputation Score (offset for visibility)")
        title = f"Seller Reputation Over Rounds ({self.title_suffix})" if self.title_suffix else "Seller Reputation Over Rounds"
        g.fig.suptitle(title, y=1.04)
        
        if g._legend is not None:
            g._legend.set_title("Seller ID")
            g._legend.set_bbox_to_anchor((1.02, 1))
            g._legend.set_frame_on(True)
        
        plot_save(g.fig, self.out_dir, filename)


class PricePlotter(PlotterBase):
    """Plotter for price-related visualizations"""
    
    def plot_avg_price_by_advertised_quality(self, products: pd.DataFrame, 
                                            filename: str = "avg_price_by_advertised_quality") -> None:
        """
        Plot average price by advertised quality over rounds
        
        Args:
            products: DataFrame with columns: round_number, advertised_quality, price
            filename: Output filename (without extension)
        """
        if products.empty:
            return
        
        required = {"round_number", "advertised_quality", "price"}
        if not required.issubset(products.columns):
            return
        
        df = products[list(required)].copy()
        df = df.dropna(subset=["round_number", "advertised_quality", "price"])
        if df.empty:
            return
        
        df["round_number"] = pd.to_numeric(df["round_number"], errors="coerce")
        df = df[df["round_number"].notna()]
        if df.empty:
            return
        
        df["advertised_quality"] = df["advertised_quality"].astype(str).str.upper()
        df = df[df["advertised_quality"].isin(["HQ", "LQ"])]
        if df.empty:
            return
        
        agg = (
            df.groupby(["round_number", "advertised_quality"])
            ["price"].agg(["mean", "std"]).reset_index()
            .rename(columns={"mean": "avg_price", "std": "std_price"})
            .sort_values(["advertised_quality", "round_number"])
        )
        if agg.empty:
            return
        
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        palette = {"HQ": "#4C78A8", "LQ": "#F58518"}
        for q in ["HQ", "LQ"]:
            sub = agg[agg["advertised_quality"] == q]
            if sub.empty:
                continue
            ax.errorbar(
                sub["round_number"],
                sub["avg_price"],
                yerr=sub["std_price"],
                fmt="-o",
                capsize=3,
                linewidth=1.8,
                color=palette.get(q, None),
                label=f"{q} (mean±std)",
            )
        
        title = (f"Average Listing Price per Round by Advertised Quality ({self.title_suffix})" 
                if self.title_suffix else "Average Listing Price per Round by Advertised Quality")
        ax.set_title(title)
        ax.set_xlabel("Round")
        ax.set_ylabel("Price (mean ± std)")
        ax.legend(title="Advertised Quality")
        plot_save(fig, self.out_dir, filename)


class ActionPlotter(PlotterBase):
    """Plotter for action-related visualizations"""
    
    def plot_seller_actions_scatter(self, products: pd.DataFrame, trace: pd.DataFrame,
                                   filename: str = "seller_actions_scatter") -> None:
        """
        Plot seller actions as scatter plot
        
        Args:
            products: DataFrame with product listings
            trace: DataFrame with trace/action records
            filename: Output filename (without extension)
        """
        if products.empty and trace.empty:
            return
        
        # Build listing points from product table
        list_df = pd.DataFrame()
        req_p = {"user_id", "round_number", "advertised_quality", "true_quality"}
        if not products.empty and req_p.issubset(products.columns):
            list_df = products[list(req_p)].copy()
            list_df = list_df.rename(columns={
                "user_id": "seller_id", 
                "round_number": "round",
                "advertised_quality": "adv_q", 
                "true_quality": "true_q"
            })
            list_df = list_df.dropna(subset=["seller_id", "round"])
            
            # Classify colors
            def color_for(q_adv: str, q_true: str) -> str:
                qa = str(q_adv).upper()
                qt = str(q_true).upper()
                if qa == "HQ" and qt == "HQ":
                    return "#1f77b4"  # deep blue
                if qa == "LQ" and qt == "LQ":
                    return "#8ecae6"  # light blue
                if qa == "HQ" and qt == "LQ":
                    return "#d62728"  # deep red
                return "#7f7f7f"  # gray
            
            list_df.loc[:, "color"] = [
                color_for(a, t) for a, t in zip(list_df["adv_q"], list_df["true_q"])
            ]
            list_df.loc[:, "round"] = pd.to_numeric(list_df["round"].values, errors="coerce")
            list_df.loc[:, "seller_id"] = pd.to_numeric(list_df["seller_id"].values, errors="coerce")
            list_df = list_df.dropna(subset=["round", "seller_id"])
        
        # Exit/Reentry from trace
        tr_df = pd.DataFrame()
        if not trace.empty and {"user_id", "action"}.issubset(trace.columns):
            tr = trace[["created_at", "user_id", "action"]].copy()
            tr = tr.rename(columns={"user_id": "seller_id"})
            tr = tr[tr["action"].isin(["exit_market", "reenter_market"])].copy()
            
            if not tr.empty:
                tr["created_at"] = pd.to_datetime(tr["created_at"])
                
                def assign_round_for_action(action, timestamp):
                    if action == "reenter_market":
                        return 5
                    elif action == "exit_market":
                        return 7
                    return None
                
                tr["round"] = tr.apply(
                    lambda row: assign_round_for_action(row["action"], row["created_at"]), 
                    axis=1
                )
                tr_df = tr[["round", "seller_id", "action"]].dropna(subset=["round"])
                tr_df.loc[:, "round"] = pd.to_numeric(tr_df["round"].values, errors="coerce")
                tr_df.loc[:, "seller_id"] = pd.to_numeric(tr_df["seller_id"].values, errors="coerce")
                tr_df = tr_df.dropna(subset=["round", "seller_id"])
        
        if list_df.empty and tr_df.empty:
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(9, 6))
        
        if not list_df.empty:
            ax.scatter(
                list_df["round"], list_df["seller_id"],
                c=list_df["color"], marker="o", s=70,
                edgecolor="white", linewidth=0.6, label="list_product",
            )
        
        if not tr_df.empty:
            re_df = tr_df[tr_df["action"] == "reenter_market"]
            ex_df = tr_df[tr_df["action"] == "exit_market"]
            if not re_df.empty:
                ax.scatter(re_df["round"], re_df["seller_id"], c="#444444", marker="s", s=80,
                          edgecolor="white", linewidth=0.6, label="reenter_market")
            if not ex_df.empty:
                ax.scatter(ex_df["round"], ex_df["seller_id"], c="#444444", marker="^", s=80,
                          edgecolor="white", linewidth=0.6, label="exit_market")
        
        title = f"Seller Actions by Round ({self.title_suffix})" if self.title_suffix else "Seller Actions by Round"
        ax.set_title(title)
        ax.set_xlabel("Round")
        ax.set_ylabel("Seller ID")
        
        # Custom legend
        listing_handles = [
            Line2D([0], [0], marker='o', color='w', label='HQ→HQ', 
                  markerfacecolor='#1f77b4', markersize=8, markeredgecolor='white'),
            Line2D([0], [0], marker='o', color='w', label='LQ→LQ', 
                  markerfacecolor='#8ecae6', markersize=8, markeredgecolor='white'),
            Line2D([0], [0], marker='o', color='w', label='HQ→LQ', 
                  markerfacecolor='#d62728', markersize=8, markeredgecolor='white'),
        ]
        action_handles = [
            Line2D([0], [0], marker='s', color='w', label='reenter_market', 
                  markerfacecolor='#444444', markersize=8, markeredgecolor='white'),
            Line2D([0], [0], marker='^', color='w', label='exit_market', 
                  markerfacecolor='#444444', markersize=8, markeredgecolor='white'),
        ]
        handles = listing_handles + action_handles
        ax.legend(handles=handles, title="Legend", bbox_to_anchor=(1.02, 1), 
                 loc="upper left", frameon=True)
        
        plot_save(fig, self.out_dir, filename)


class ManipulationPlotter(PlotterBase):
    """Plotter for manipulation behavior visualizations"""
    
    def plot_manipulation_behavior_statistics(self, analysis_labels: pd.DataFrame,
                                             filename: str = "manipulation_behavior_statistics") -> None:
        """
        Plot bar chart showing statistics of manipulation behaviors
        
        Args:
            analysis_labels: DataFrame with behavioral_pattern column
            filename: Output filename (without extension)
        """
        if analysis_labels.empty:
            return
        
        required = {"seller_id", "behavioral_pattern"}
        if not required.issubset(analysis_labels.columns):
            return
        
        df = analysis_labels[list(required)].copy()
        df = df.dropna(subset=["behavioral_pattern"])
        if df.empty:
            return
        
        pattern_counts = df["behavioral_pattern"].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#32CD32", "#FFD700", "#FF4500", "#9370DB", "#DC143C"]
        bars = ax.bar(pattern_counts.index, pattern_counts.values, 
                     color=colors[:len(pattern_counts)], alpha=0.8, 
                     edgecolor="white", linewidth=1.5)
        
        ax.set_title("Manipulation Behavior Statistics", fontsize=16, fontweight="bold")
        ax.set_xlabel("Behavioral Pattern")
        ax.set_ylabel("Number of Sellers")
        ax.tick_params(axis='x', rotation=45)
        
        # Add count labels on bars
        for bar, count in zip(bars, pattern_counts.values):
            height = bar.get_height()
            ax.annotate(f'{count}', xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plot_save(fig, self.out_dir, filename)
    
    def plot_seller_manipulation_details(self, analysis_labels: pd.DataFrame,
                                        filename: str = "seller_manipulation_details") -> None:
        """
        Plot detailed manipulation behavior statistics for each seller
        
        Args:
            analysis_labels: DataFrame with manipulation analysis data
            filename: Output filename (without extension)
        """
        if analysis_labels.empty:
            return
        
        required = {"seller_id", "behavioral_pattern", "adaptation_detected", 
                   "warrant_abuse_detected", "exit_reentry_detected", "deception_rate_overall"}
        if not required.issubset(analysis_labels.columns):
            return
        
        df = analysis_labels[list(required)].copy()
        df = df.dropna(subset=["seller_id"])
        if df.empty:
            return
        
        df["seller_id"] = df["seller_id"].astype(str)
        df = df.sort_values("seller_id")
        
        # Create figure with multiple subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Top plot: Behavioral patterns by seller
        seller_ids = df["seller_id"].values
        patterns = df["behavioral_pattern"].values
        pattern_colors = {"honest": "#32CD32", "opportunistic": "#FFD700", 
                         "systematic": "#FF4500", "adaptive": "#9370DB"}
        colors = [pattern_colors.get(p, "#808080") for p in patterns]
        
        bars1 = ax1.bar(seller_ids, [1]*len(seller_ids), color=colors, alpha=0.8)
        ax1.set_title("Manipulation Behavior Pattern by Seller", fontsize=14, fontweight="bold")
        ax1.set_xlabel("Seller ID")
        ax1.set_ylabel("Behavioral Pattern")
        ax1.set_ylim(0, 1.2)
        
        # Add pattern labels on bars
        for bar, pattern in zip(bars1, patterns):
            height = bar.get_height()
            ax1.annotate(pattern, xy=(bar.get_x() + bar.get_width() / 2, height/2),
                        ha='center', va='center', fontsize=8, rotation=90, fontweight='bold')
        
        # Bottom plot: Heatmap of manipulation features
        feature_cols = ["adaptation_detected", "warrant_abuse_detected", "exit_reentry_detected"]
        feature_data = df[["seller_id"] + feature_cols].set_index("seller_id")
        
        # Convert boolean to int for visualization
        for col in feature_cols:
            feature_data[col] = feature_data[col].astype(float)
        
        im = ax2.imshow(feature_data.T, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
        ax2.set_title("Manipulation Features by Seller", fontsize=14, fontweight="bold")
        ax2.set_xlabel("Seller ID")
        ax2.set_ylabel("Manipulation Features")
        ax2.set_xticks(range(len(feature_data.index)))
        ax2.set_xticklabels(feature_data.index)
        ax2.set_yticks(range(len(feature_cols)))
        ax2.set_yticklabels(["Adaptation", "Warrant Abuse", "Exit-Reentry"])
        
        # Add text annotations
        for i in range(len(feature_cols)):
            for j in range(len(feature_data.index)):
                value = feature_data.iloc[j, i]
                text = "✓" if value > 0.5 else "✗"
                ax2.text(j, i, text, ha="center", va="center", 
                        color="white" if value > 0.5 else "black", 
                        fontsize=12, fontweight="bold")
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label("Detected (1) / Not Detected (0)")
        
        plot_save(fig, self.out_dir, filename)


# Test cases
if __name__ == "__main__":
    import tempfile
    
    # Create temporary directory
    test_dir = tempfile.mkdtemp()
    
    # Test ReputationPlotter
    plotter = ReputationPlotter(test_dir, "Test")
    test_data = pd.DataFrame({
        'round': [1, 1, 2, 2],
        'seller_id': [1, 2, 1, 2],
        'public_reputation_score': [5.0, 3.0, 6.0, 4.0]
    })
    plotter.plot_reputation_over_rounds(test_data)
    print("✓ ReputationPlotter works")
    
    # Test PricePlotter
    price_plotter = PricePlotter(test_dir, "Test")
    test_products = pd.DataFrame({
        'round_number': [1, 1, 2, 2],
        'advertised_quality': ['HQ', 'LQ', 'HQ', 'LQ'],
        'price': [5.0, 3.0, 5.5, 3.5]
    })
    price_plotter.plot_avg_price_by_advertised_quality(test_products)
    print("✓ PricePlotter works")
    
    print(f"\nAll plotter tests passed! Outputs saved to: {test_dir}")
