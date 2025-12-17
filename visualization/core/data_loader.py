"""
Data loading module for visualization
Handles loading data from databases and experiment directories
"""

import os
import sqlite3
import json
import re
from typing import Dict, List, Any, Optional
import pandas as pd
from .utils import read_table


class DataLoader:
    """Base data loader for single database files"""
    
    def __init__(self, db_path: str):
        """
        Initialize data loader
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def load_all_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Load all tables from database
        
        Returns:
            Dictionary mapping table names to DataFrames
        """
        conn = sqlite3.connect(self.db_path)
        tables = {}
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table_name in table_names:
                tables[table_name] = read_table(conn, table_name)
        finally:
            conn.close()
        
        return tables
    
    def load_table(self, table_name: str) -> pd.DataFrame:
        """
        Load a specific table from database
        
        Args:
            table_name: Name of table to load
            
        Returns:
            DataFrame containing table data
        """
        conn = sqlite3.connect(self.db_path)
        try:
            return read_table(conn, table_name)
        finally:
            conn.close()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from config.json in same directory as database
        
        Returns:
            Configuration dictionary
        """
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        config_file = os.path.join(db_dir, 'config.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        return {}


class ExperimentDataLoader:
    """Data loader for multi-run experiments"""
    
    def __init__(self, experiment_id: str):
        """
        Initialize experiment data loader
        
        Args:
            experiment_id: Experiment ID
        """
        self.experiment_id = experiment_id
        
        # Import here to avoid circular dependency
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, base_dir)
        from config import SimulationConfig
        
        self.paths = SimulationConfig.get_experiment_paths(experiment_id)
        self.run_data = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load experiment configuration from config.json or experiment_config.json"""
        # Try config_file first (if exists)
        config_file = self.paths.get('config_file')
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # If it's experiment_config.json format, extract simulation_config
                    if 'simulation_config' in config:
                        return config['simulation_config']
                    return config
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Try experiment_config.json as fallback
        exp_config_file = os.path.join(self.paths['experiment_dir'], 'experiment_config.json')
        if os.path.exists(exp_config_file):
            try:
                with open(exp_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'simulation_config' in config:
                        return config['simulation_config']
            except Exception:
                pass
        
        return {}
    
    def load_experiment_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Load data from all runs in experiment
        
        Returns:
            Dictionary mapping run_key (filename without .db) to run data dictionaries
        """
        print(f"Loading experiment data: {self.experiment_id}")
        
        experiment_dir = self.paths['experiment_dir']
        if not os.path.exists(experiment_dir):
            print(f"Experiment directory does not exist: {experiment_dir}")
            return {}
        
        db_files = [f for f in os.listdir(experiment_dir) 
                   if f.startswith('run_') and f.endswith('.db')]
        print(f"Found {len(db_files)} run database(s)")
        
        for db_file in db_files:
            try:
                # Use filename (without .db) as unique key
                # This handles cases where multiple files have the same numeric prefix
                # but different configurations (e.g., run_1_reputation_only.db vs run_1_reputation_and_warrant.db)
                run_key = db_file.replace('.db', '')
                
                db_path = os.path.join(experiment_dir, db_file)
                run_data = self._load_single_run_data(db_path, run_key)
                self.run_data[run_key] = run_data
                print(f"Loaded {run_key}")
            except Exception as e:
                print(f"Failed to load {db_file}: {e}")
        
        print(f"Successfully loaded data for {len(self.run_data)} run(s)")
        return self.run_data
    
    def _load_single_run_data(self, db_path: str, run_key: str) -> Dict[str, pd.DataFrame]:
        """
        Load data for a single run
        
        Args:
            db_path: Path to run database
            run_key: Run identifier (filename without .db extension)
            
        Returns:
            Dictionary containing all tables for the run
        """
        conn = sqlite3.connect(db_path)
        
        data = {
            'run_key': run_key,
            'transactions': read_table(conn, 'transactions'),
            'user': read_table(conn, 'user'),
            'product': read_table(conn, 'product'),
            'reputation_history': read_table(conn, 'reputation_history'),
            'trace': read_table(conn, 'trace')
        }
        
        conn.close()
        return data
    
    def get_title_suffix(self) -> str:
        """
        Generate title suffix based on experiment configuration
        
        Returns:
            Formatted title suffix string
        """
        from .utils import get_title_suffix
        # Since this is a multi-config experiment, use experiment ID as suffix
        # Individual runs can have their own configs loaded separately
        if not self.config or 'MARKET_TYPE' not in self.config:
            # For multi-config experiments, just return experiment ID
            return self.experiment_id if hasattr(self, 'experiment_id') else ''
        return get_title_suffix(self.config)


# Test cases
if __name__ == "__main__":
    import tempfile
    
    # Test DataLoader with non-existent file
    try:
        loader = DataLoader("nonexistent.db")
        print("✗ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✓ DataLoader correctly raises FileNotFoundError for missing files")
    
    # Test ExperimentDataLoader initialization
    # Note: This requires actual experiment structure, so we'll just test basic init
    print("✓ DataLoader modules initialized successfully")
    print("Note: Full tests require actual database files")
