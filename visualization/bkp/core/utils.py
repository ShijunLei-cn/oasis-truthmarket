"""
Utility functions for visualization and analysis
Common helper functions used across visualization modules
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns


def read_table(conn: sqlite3.Connection, table: str) -> Any:
    """
    Read a table from SQLite database connection
    
    Args:
        conn: SQLite database connection
        table: Table name to read
        
    Returns:
        pandas DataFrame or empty DataFrame if table doesn't exist
    """
    import pandas as pd
    try:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
    except Exception:
        return pd.DataFrame()


def ensure_output_dir(base_dir: Optional[str] = None) -> str:
    """
    Ensure output directory exists and return its path
    
    Args:
        base_dir: Base directory for output (default: current directory)
        
    Returns:
        Path to output directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if base_dir:
        out_dir = os.path.join(base_dir, "analysis", "outputs", timestamp)
    else:
        out_dir = os.path.join("analysis", "outputs", timestamp)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def plot_save(fig: plt.Figure, out_dir: str, name: str, dpi: int = 150) -> None:
    """
    Save matplotlib figure to file
    
    Args:
        fig: Matplotlib figure object
        out_dir: Output directory path
        name: File name (without extension)
        dpi: Resolution for saved image (default: 150)
    """
    path = os.path.join(out_dir, f"{name}.png")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)


def load_config_from_db_path(db_path: str) -> Dict[str, Any]:
    """
    Load configuration from config.json based on database path
    
    Args:
        db_path: Path to database file
        
    Returns:
        Configuration dictionary
    """
    # Try to find config.json in the same directory as database
    db_dir = os.path.dirname(os.path.abspath(db_path))
    config_file = os.path.join(db_dir, 'config.json')
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    return {}


def get_title_suffix(config: Dict[str, Any]) -> str:
    """
    Generate title suffix based on configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Formatted title suffix string
    """
    parts = []
    market_type = config.get('MARKET_TYPE', 'unknown')
    comm_type = config.get('COMMUNICATION_TYPE', 'none')
    
    # Format market type
    if market_type == 'reputation_only':
        parts.append('Reputation-Only')
    elif market_type == 'reputation_and_warrant':
        parts.append('Reputation+Warrant')
    else:
        parts.append(market_type.replace('_', ' ').title())
    
    # Format communication type
    if comm_type and comm_type != 'none':
        parts.append(f'{comm_type.title()} Comm.')
    
    return ' | '.join(parts) if parts else ''


def setup_plot_style(style: str = 'whitegrid', font: Optional[str] = None) -> None:
    """
    Setup matplotlib and seaborn plotting style
    
    Args:
        style: Seaborn style (default: 'whitegrid')
        font: Font family for matplotlib (default: ['DejaVu Sans', 'Arial'])
    """
    sns.set_theme(style=style)
    if font:
        plt.rcParams['font.sans-serif'] = [font]
    else:
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False


def summarize_basic(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Summarize basic database structure and row counts
    
    Args:
        conn: SQLite database connection
        
    Returns:
        Dictionary with table existence and row count information
    """
    summary = {}
    cur = conn.cursor()
    try:
        for t in ["user", "product", "transactions", "reputation_history", "trace"]:
            cur.execute("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name=?", (t,))
            exists = cur.fetchone()[0] == 1
            summary[f"has_{t}"] = exists
            if exists:
                cur.execute(f"SELECT COUNT(1) FROM {t}")
                summary[f"rows_{t}"] = cur.fetchone()[0]
    except Exception:
        pass
    return summary


# Test cases
if __name__ == "__main__":
    import tempfile
    
    # Test ensure_output_dir
    test_dir = ensure_output_dir()
    assert os.path.exists(test_dir)
    print(f"✓ ensure_output_dir works: {test_dir}")
    
    # Test load_config_from_db_path (with non-existent file)
    config = load_config_from_db_path("nonexistent.db")
    assert config == {}
    print("✓ load_config_from_db_path handles missing files")
    
    # Test get_title_suffix
    test_config = {'MARKET_TYPE': 'reputation_only', 'COMMUNICATION_TYPE': 'buyer'}
    suffix = get_title_suffix(test_config)
    assert 'Reputation-Only' in suffix
    assert 'Buyer Comm' in suffix
    print(f"✓ get_title_suffix works: {suffix}")
    
    # Test setup_plot_style
    setup_plot_style()
    assert sns.axes_style()['axes.grid'] is True
    print("✓ setup_plot_style works")
    
    print("\nAll utility tests passed!")
