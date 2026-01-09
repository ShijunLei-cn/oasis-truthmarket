"""
Market Simulation Configuration
Configuration file: contains all simulation parameters and settings
Supports loading from YAML configuration files
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import yaml


class SimulationConfig:
    """Market simulation configuration class"""

    # Experiment configuration
    RUNS = 5
    NUM_SELLERS = 5
    NUM_BUYERS = 5
    SIMULATION_ROUNDS = 10

    # Market parameters (Updated to match economic model)
    MARKET_PARAMS = {
        # Production costs
        "hq_cost": 4.0,  # Cost C for High Quality Product
        "lq_cost": 2.0,  # Cost C for Low Quality Product
        # Prices
        "hq_price": 8.0,  # Price P for High Quality Product
        "lq_price": 3.0,  # Price P for Low Quality Product
        # Consumer values (utility)
        "hq_utility": 12.0,  # Value V for High Quality Product
        "lq_utility": 4.0,  # Value V for Low Quality Product
        # Warranty/Escrow system (quality-dependent)
        "hq_warrant_escrow": 8.0,  # Escrow for HQ products (V_h - V_l = 12 - 4)
        "lq_warrant_escrow": 2.0,  # Escrow for LQ products
        # Challenge mechanism
        "challenge_cost": 1.0,  # Cost for buyer to challenge a warrant
        # Budget configuration (refreshed at the start of each round)
        "seller_budget": 18.0,  # Initial budget for sellers per round
        "buyer_budget": 60.0,  # Initial budget for buyers per round
        # Initial reputation configuration
        "initial_seller_reputation": 0.0,  # Initial reputation score for all sellers at the start of simulation
    }

    # Pre version Params
    # MARKET_PARAMS = {
    #     "hq_cost": 2.0,
    #     "lq_cost": 1.0,
    #     "hq_price": 5.0,
    #     "lq_price": 3.0,
    #     "hq_utility": 8.0,
    #     "lq_utility": 5.0,
    #     "hq_warrant_escrow": 5.0,
    #     "lq_warrant_escrow": 5.0,
    #     "challenge_cost": 1.0,
    # }

    # Market rule parameters
    REPUTATION_LAG = None  # Reputation lag display rounds
    REENTRY_ALLOWED_ROUND = None  # Re-entry market allowed rounds
    INITIAL_WINDOW_ROUNDS = []  # Initial rounds with hidden complete history
    EXIT_ROUND = None  # Exit market allowed rounds
    MARKET_TYPE = 'reputation_only'
    COMMUNICATION_TYPE = 'none'  # Communication type: 'none', 'seller', 'buyer', 'both'
    COMMUNICATION_CHANNEL_TYPE = "Fake"  # Communication channel type: "Fake" or "Real"
    
    # Model configuration
    MODEL_PLATFORM = "openai"
    # MODEL_PLATFORM = "vllm"
    MODEL_TYPE = "gpt-4o-mini"
    # MODEL_TYPE = "gpt-4.1"
    # MODEL_TYPE = "Qwen3-8B"

    # Path configuration
    BASE_DATA_PATH = "experiments"
    BASE_ANALYSIS_PATH = "analysis"

    @classmethod
    def get_experiment_id(cls) -> str:
        """Generate experiment ID (based on timestamp)"""
        return datetime.now().strftime("experiment_%Y%m%d_%H%M%S")

    @classmethod
    def get_experiment_paths(cls, experiment_id: str) -> Dict[str, str]:
        """Get experiment related paths"""
        experiment_dir = os.path.join(cls.BASE_DATA_PATH, experiment_id)
        analysis_dir = os.path.join(cls.BASE_ANALYSIS_PATH, experiment_id)

        return {
            "experiment_dir": experiment_dir,
            "analysis_dir": analysis_dir,
            "individual_analysis_dir": os.path.join(analysis_dir, "individual_runs"),
            "aggregated_analysis_dir": os.path.join(analysis_dir, "aggregated"),
            "config_file": os.path.join(experiment_dir, "config.json"),
        }

    @classmethod
    def get_run_db_path(cls, experiment_id: str, run_id: int) -> str:
        """Get database path for specified run"""
        experiment_dir = os.path.join(cls.BASE_DATA_PATH, experiment_id)
        return os.path.join(experiment_dir, f"run_{run_id}.db")

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary format"""
        return {
            'RUNS': cls.RUNS,
            'NUM_SELLERS': cls.NUM_SELLERS,
            'NUM_BUYERS': cls.NUM_BUYERS,
            'SIMULATION_ROUNDS': cls.SIMULATION_ROUNDS,
            'MARKET_PARAMS': cls.MARKET_PARAMS,
            'REPUTATION_LAG': cls.REPUTATION_LAG,
            'REENTRY_ALLOWED_ROUND': cls.REENTRY_ALLOWED_ROUND,
            'INITIAL_WINDOW_ROUNDS': cls.INITIAL_WINDOW_ROUNDS,
            'EXIT_ROUND': cls.EXIT_ROUND,
            'MARKET_TYPE': cls.MARKET_TYPE,
            'COMMUNICATION_TYPE': cls.COMMUNICATION_TYPE,
            'COMMUNICATION_CHANNEL_TYPE': cls.COMMUNICATION_CHANNEL_TYPE,
            'MODEL_PLATFORM': cls.MODEL_PLATFORM,
            'MODEL_TYPE': cls.MODEL_TYPE
        }

    @classmethod
    def save_config(cls, experiment_id: str):
        """Save configuration to experiment directory"""
        import json

        paths = cls.get_experiment_paths(experiment_id)
        os.makedirs(os.path.dirname(paths["config_file"]), exist_ok=True)

        config_data = cls.to_dict()
        config_data["experiment_id"] = experiment_id
        config_data["created_at"] = datetime.now().isoformat()

        with open(paths["config_file"], "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> 'SimulationConfig':
        """
        Load configuration from a YAML file and return a new config instance
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            SimulationConfig instance with loaded values
        """
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        # Create a new instance (or modify class attributes)
        # Since we're using class attributes, we'll modify them directly
        # but return a reference to the class for consistency
        
        # Load experiment configuration
        if 'experiment' in config_dict:
            exp_config = config_dict['experiment']
            cls.RUNS = exp_config.get('runs', cls.RUNS)
            cls.NUM_SELLERS = exp_config.get('num_sellers', cls.NUM_SELLERS)
            cls.NUM_BUYERS = exp_config.get('num_buyers', cls.NUM_BUYERS)
            cls.SIMULATION_ROUNDS = exp_config.get('simulation_rounds', cls.SIMULATION_ROUNDS)
        
        # Load market parameters
        if 'market_params' in config_dict:
            market_params = config_dict['market_params']
            # Update existing dict to preserve structure
            cls.MARKET_PARAMS.update(market_params)
        
        # Load market rule parameters
        if 'market_rules' in config_dict:
            rules = config_dict['market_rules']
            cls.REPUTATION_LAG = rules.get('reputation_lag', cls.REPUTATION_LAG)
            cls.REENTRY_ALLOWED_ROUND = rules.get('reentry_allowed_round', cls.REENTRY_ALLOWED_ROUND)
            cls.INITIAL_WINDOW_ROUNDS = rules.get('initial_window_rounds', cls.INITIAL_WINDOW_ROUNDS)
            cls.EXIT_ROUND = rules.get('exit_round', cls.EXIT_ROUND)
            cls.MARKET_TYPE = rules.get('market_type', cls.MARKET_TYPE)
            cls.COMMUNICATION_TYPE = rules.get('communication_type', cls.COMMUNICATION_TYPE)
            cls.COMMUNICATION_CHANNEL_TYPE = rules.get('communication_channel_type', cls.COMMUNICATION_CHANNEL_TYPE)
        
        # Load model configuration
        if 'model' in config_dict:
            model_config = config_dict['model']
            cls.MODEL_PLATFORM = model_config.get('platform', cls.MODEL_PLATFORM)
            cls.MODEL_TYPE = model_config.get('type', cls.MODEL_TYPE)
        
        # Load path configuration
        if 'paths' in config_dict:
            paths = config_dict['paths']
            cls.BASE_DATA_PATH = paths.get('base_data_path', cls.BASE_DATA_PATH)
            cls.BASE_ANALYSIS_PATH = paths.get('base_analysis_path', cls.BASE_ANALYSIS_PATH)
        
        return cls
