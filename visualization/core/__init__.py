"""
Visualization core module
Provides modular visualization and analysis tools for market simulation results
"""

from .utils import (
    read_table,
    ensure_output_dir,
    plot_save,
    load_config_from_db_path,
    get_title_suffix,
    setup_plot_style,
    summarize_basic
)
from .data_loader import DataLoader, ExperimentDataLoader
from .plotters import (
    PlotterBase,
    ReputationPlotter,
    PricePlotter,
    ActionPlotter,
    ManipulationPlotter
)
from .statistics import StatisticsCalculator
from .single_run_analysis import SingleRunAnalyzer, analyze_single_run
from .multi_run_analysis import MultiRunAnalyzer
from .comparison_analysis import ComparisonAnalyzer, compare_experiments

__version__ = '1.0.0'

__all__ = [
    'read_table',
    'ensure_output_dir',
    'plot_save',
    'load_config_from_db_path',
    'get_title_suffix',
    'setup_plot_style',
    'summarize_basic',
    'DataLoader',
    'ExperimentDataLoader',
    'PlotterBase',
    'ReputationPlotter',
    'PricePlotter',
    'ActionPlotter',
    'ManipulationPlotter',
    'StatisticsCalculator',
    'SingleRunAnalyzer',
    'analyze_single_run',
    'MultiRunAnalyzer',
    'ComparisonAnalyzer',
    'compare_experiments'
]
