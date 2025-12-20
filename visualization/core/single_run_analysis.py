"""
Single run analysis module
Analyzes individual simulation run results and generates visualizations
"""

import os
import sqlite3
from typing import Optional
from .data_loader import DataLoader
from .plotters import ReputationPlotter, PricePlotter, ActionPlotter, ManipulationPlotter
from .utils import (
    ensure_output_dir, 
    load_config_from_db_path, 
    get_title_suffix,
    summarize_basic,
    setup_plot_style
)


class SingleRunAnalyzer:
    """Analyzer for single simulation run"""
    
    def __init__(self, db_path: str, out_dir: Optional[str] = None):
        """
        Initialize single run analyzer
        
        Args:
            db_path: Path to database file
            out_dir: Output directory (default: auto-generated in analysis/outputs)
        """
        self.data_loader = DataLoader(db_path)
        self.db_path = db_path
        
        if out_dir is None:
            db_dir = os.path.dirname(os.path.abspath(db_path))
            self.out_dir = ensure_output_dir(db_dir)
        else:
            self.out_dir = out_dir
            os.makedirs(out_dir, exist_ok=True)
        
        self.config = load_config_from_db_path(db_path)
        self.title_suffix = get_title_suffix(self.config)
    
    def analyze(self) -> None:
        """
        Run complete analysis and generate all visualizations
        """
        print(f"Analyzing database: {self.db_path}")
        print(f"Output directory: {self.out_dir}")
        
        # Print database summary
        with sqlite3.connect(self.db_path) as conn:
            summary = summarize_basic(conn)
            print("Database Summary:")
            for k, v in summary.items():
                print(f"  {k}: {v}")
            
            # Load tables
            reph = self.data_loader.load_table("reputation_history")
            analysis_labels = self.data_loader.load_table("analysis_labels")
            products = self.data_loader.load_table("product")
            trace = self.data_loader.load_table("trace")
        
        # Setup plotting style
        setup_plot_style()
        
        # Create plotters
        reputation_plotter = ReputationPlotter(self.out_dir, self.title_suffix)
        price_plotter = PricePlotter(self.out_dir, self.title_suffix)
        action_plotter = ActionPlotter(self.out_dir, self.title_suffix)
        manipulation_plotter = ManipulationPlotter(self.out_dir, self.title_suffix)
        
        # Generate visualizations
        print("Generating visualizations...")
        
        # Basic market analysis
        reputation_plotter.plot_reputation_over_rounds(reph)
        price_plotter.plot_avg_price_by_advertised_quality(products)
        action_plotter.plot_seller_actions_scatter(products, trace)
        
        # Manipulation analysis (if data available)
        has_manipulator_data = not analysis_labels.empty and "label_manipulator" in analysis_labels.columns
        if has_manipulator_data:
            print("Generating manipulator analysis visualizations...")
            manipulation_plotter.plot_manipulation_behavior_statistics(analysis_labels)
            manipulation_plotter.plot_seller_manipulation_details(analysis_labels)
        else:
            print("No manipulator analysis data found. Skipping advanced analysis.")
        
        print(f"Analysis complete. Figures saved to: {self.out_dir}")


def analyze_single_run(db_path: str, out_dir: Optional[str] = None) -> None:
    """
    Convenience function to analyze a single run
    
    Args:
        db_path: Path to database file
        out_dir: Output directory (optional)
    """
    analyzer = SingleRunAnalyzer(db_path, out_dir)
    analyzer.analyze()


# Test cases
if __name__ == "__main__":
    print("Single run analysis module")
    print("This module requires actual database files to test.")
    print("Usage:")
    print("  from visualization.core.single_run_analysis import analyze_single_run")
    print("  analyze_single_run('path/to/database.db')")
