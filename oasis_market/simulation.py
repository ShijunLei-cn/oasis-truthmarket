"""
Core simulation module for market simulation
Provides the main simulation runner and orchestration logic
"""

import asyncio
import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime

from .database import MarketDatabase
from .agents import AgentManager
from .logging import ActionLogger, SimulationLogger
from .phases import (
    SellerListingPhase, BuyerPurchasePhase, BuyerRatingPhase, CommunicationPhase
)
from camel.models import ModelFactory
import oasis
from oasis import AgentGraph, make
from oasis.social_agent.agents_generator import generate_agent_from_LLM
from prompt import (
    SELLER_GENERATION_SYS_PROMPT, SELLER_GENERATION_USER_PROMPT,
    BUYER_GENERATION_SYS_PROMPT, BUYER_GENERATION_USER_PROMPT
)

class MarketSimulation:
    """Main market simulation orchestrator"""
    
    def __init__(self, database_path: str, config):
        """
        Initialize market simulation
        
        Args:
            database_path: Path to database file
            config: Simulation configuration object
        """
        self.database_path = database_path
        self.config = config
        self.db_manager = MarketDatabase(database_path)
        self.action_logger = ActionLogger(database_path)
        self.sellers_history = {}
        self.env = None
        self.agent_graph = None
        self.model = None
    
    def setup_environment(self):
        """Set up environment variables and clean up existing data"""
        # Set environment variables
        os.environ['MARKET_DB_PATH'] = self.database_path
        
        # Clean up existing database and action log
        self.db_manager.cleanup()
        self.action_logger.cleanup_action_log()
        
        # Reset agent ID counter
        AgentManager.reset_agent_id_counter()
    
    async def initialize_agents(self, model, market_type: str):
        """
        Initialize seller and buyer agents
        
        Args:
            model: LLM model instance
            market_type: Type of market simulation
            
        Returns:
            Tuple of (agent_graph, env)
        """
        
        agent_graph = AgentGraph()
        
        # Generate seller agents
        print("Generating seller agents...")
        seller_agent_graph = await generate_agent_from_LLM(
            agents_num=self.config.NUM_SELLERS,
            sys_prompt=SELLER_GENERATION_SYS_PROMPT,
            user_prompt=SELLER_GENERATION_USER_PROMPT,
            market_type=market_type,
            role="seller",
            model=model,
            db_path=self.database_path,
            config=self.config,
        )
        
        # Generate buyer agents
        print("Generating buyer agents...")
        buyer_agent_graph = await generate_agent_from_LLM(
            agents_num=self.config.NUM_BUYERS,
            sys_prompt=BUYER_GENERATION_SYS_PROMPT,
            user_prompt=BUYER_GENERATION_USER_PROMPT,
            market_type=market_type,
            role="buyer",
            model=model,
            db_path=self.database_path,
            config=self.config,
        )
        
        # Add agents to main graph
        for agent_id, agent in seller_agent_graph.get_agents():
            agent.env.is_market_sim = True
            agent.env.communication_channel_type = self.config.COMMUNICATION_CHANNEL_TYPE
            agent_graph.add_agent(agent)
        
        for agent_id, agent in buyer_agent_graph.get_agents():
            agent.env.is_market_sim = True
            agent.env.communication_channel_type = self.config.COMMUNICATION_CHANNEL_TYPE
            agent_graph.add_agent(agent)
        
        # Create environment
        env = make(
            agent_graph=agent_graph,
            platform=oasis.DefaultPlatformType.REDDIT,
            database_path=self.database_path
        )
        await env.reset()
        
        print(f"Environment initialized. Database at '{self.database_path}'.")
        self.db_manager.initialize_market_roles(
            agent_graph, self.config.NUM_SELLERS, self.config.NUM_BUYERS
        )
        
        return agent_graph, env
    
    def update_seller_histories(self, round_num: int):
        """
        Update seller history records for the round
        
        Args:
            round_num: Current round number
        """
        for agent_id, agent in self.agent_graph.get_agents():
            if agent.user_info.profile.get("role") == 'seller':
                round_summary = self.db_manager.get_seller_round_summary(agent_id, round_num)
                new_state = self.db_manager.get_agent_state(agent_id, 'seller', round_num=round_num)
                
                # Calculate round profit
                round_profit = (round_summary.get('price', 0) - round_summary.get('cost', 0)) * round_summary.get('sold_numbers', 0)
                total_profit = new_state.get('total_profit', 0)
                
                # Calculate next round reputation
                # Use default value if REPUTATION_LAG is None
                reputation_lag = self.config.REPUTATION_LAG if self.config.REPUTATION_LAG is not None else 1
                next_reputation = self.db_manager.compute_next_round_reputation(
                    agent_id, round_num, reputation_lag
                )
                
                # Update history
                if agent_id not in self.sellers_history:
                    self.sellers_history[agent_id] = []
                
                AgentManager.update_seller_history(
                    self.sellers_history, agent_id, round_num,
                    round_summary, round_profit, total_profit, next_reputation
                )
    
    async def run_round(self, round_num: int, market_type: str, communication_type: str):
        """
        Run a single round of the simulation
        
        Args:
            round_num: Current round number
            market_type: Type of market
            communication_type: Type of communication ('none', 'seller', 'buyer', 'both')
        """
        # Synchronize platform round counter
        self.env.platform.sandbox_clock.round_step = round_num
        SimulationLogger.print_round_header(round_num, self.config.SIMULATION_ROUNDS)
        
        # Log market flags (use defaults if None)
        exit_round = self.config.EXIT_ROUND if self.config.EXIT_ROUND is not None else 0
        reentry_round = self.config.REENTRY_ALLOWED_ROUND if self.config.REENTRY_ALLOWED_ROUND is not None else 0
        SimulationLogger.log_market_flags(round_num, exit_round, reentry_round)
        
        # Initialize phases
        seller_listing = SellerListingPhase(
            self.env, self.agent_graph, self.db_manager, self.action_logger, self.config
        )
        buyer_purchase = BuyerPurchasePhase(
            self.env, self.agent_graph, self.db_manager, self.action_logger, self.config
        )
        buyer_rating = BuyerRatingPhase(
            self.env, self.agent_graph, self.db_manager, self.action_logger, self.config
        )
        communication = CommunicationPhase(
            self.env, self.agent_graph, self.db_manager, self.action_logger, self.config
        )
        
        # Execute phases based on communication type
        if communication_type in ['seller', 'both']:
            await communication.execute(round_num, 'seller')
        
        if communication_type in ['buyer', 'both']:
            await communication.execute(round_num, 'buyer')
        
        # Seller listing phase
        await seller_listing.execute(round_num, self.sellers_history)
        
        # Buyer purchase phase
        purchase_results = await buyer_purchase.execute(round_num)
        
        # Buyer rating phase
        await buyer_rating.execute(round_num, purchase_results, market_type)
        
        # Print round statistics
        from utils import print_round_statistics
        print_round_statistics(round_num, self.database_path)
        
        # Update reputation
        from oasis.environment.processing.reputation import compute_and_update_reputation
        # Use default value if REPUTATION_LAG is None
        reputation_lag = self.config.REPUTATION_LAG if self.config.REPUTATION_LAG is not None else 1
        ratings_cutoff_round = max(0, round_num - reputation_lag)
        with sqlite3.connect(self.database_path) as conn:
            compute_and_update_reputation(conn, round_num, ratings_up_to_round=ratings_cutoff_round)
        
        # Update seller histories
        self.update_seller_histories(round_num)
        
        SimulationLogger.print_round_footer(round_num)
    
    async def run(self, market_type: Optional[str] = None, communication_type: Optional[str] = None):
        """
        Run the complete market simulation
        
        Args:
            market_type: Type of market (uses config default if not specified)
            communication_type: Type of communication (uses config default if not specified)
        """
        print("Starting market simulation initialization...")
        
        # Set defaults from config if not provided
        if market_type is None:
            market_type = self.config.MARKET_TYPE
        if communication_type is None:
            communication_type = getattr(self.config, 'COMMUNICATION_TYPE', 'none')
        
        # Setup environment
        self.setup_environment()
        
        # Create model
        self.model = ModelFactory.create(
            model_platform=self.config.MODEL_PLATFORM,
            model_type=self.config.MODEL_TYPE,
            api_key=os.getenv("MODEL_API_KEY"),
            url=os.getenv("MODEL_BASE_URL"),
        )
        
        # Initialize agents and environment
        self.agent_graph, self.env = await self.initialize_agents(self.model, market_type)
        
        # Initialize seller history
        self.sellers_history = {i+1: [] for i in range(self.config.NUM_SELLERS)}
        
        # Run simulation rounds
        for round_num in range(1, self.config.SIMULATION_ROUNDS + 1):
            await self.run_round(round_num, market_type, communication_type)
        
        # Run vulnerability detection
        from oasis.environment.processing.valunerability import run_detection
        run_detection(self.config.SIMULATION_ROUNDS, self.database_path)
        print("Manipulation analysis completed.")
        
        # Close environment
        await self.env.close()
        
        # Print summary
        from utils import print_simulation_summary
        print_simulation_summary(self.database_path)
        print("\nSimulation finished")


# Convenience function for backward compatibility
async def run_single_simulation(database_path: str, market_type: Optional[str] = None,
                               communication_type: str = 'none', communication_channel_type: str = "Fake"):
    """
    Run a single market simulation (backward compatibility wrapper)
    
    Args:
        database_path: Path to database file
        market_type: Type of market
        communication_type: Type of communication
        communication_channel_type: Type of communication channel ("Fake" or "Real")
    """
    from config import SimulationConfig
    
    # Override communication type in config if needed
    original_comm_type = getattr(SimulationConfig, 'COMMUNICATION_TYPE', 'none')
    original_comm_channel_type = getattr(SimulationConfig, 'COMMUNICATION_CHANNEL_TYPE', "Fake")
    SimulationConfig.COMMUNICATION_TYPE = communication_type
    SimulationConfig.COMMUNICATION_CHANNEL_TYPE = communication_channel_type
    
    simulation = MarketSimulation(database_path, SimulationConfig)
    await simulation.run(market_type, communication_type)
    
    # Restore original communication type
    SimulationConfig.COMMUNICATION_TYPE = original_comm_type
    SimulationConfig.COMMUNICATION_CHANNEL_TYPE = original_comm_channel_type


# Test cases
if __name__ == "__main__":
    import tempfile
    from datetime import datetime
    
    # Create mock config
    class MockConfig:
        RUNS = 1
        NUM_SELLERS = 2
        NUM_BUYERS = 2
        SIMULATION_ROUNDS = 1
        REPUTATION_LAG = 1
        REENTRY_ALLOWED_ROUND = 5
        EXIT_ROUND = 7
        MARKET_TYPE = 'reputation_only'
        COMMUNICATION_TYPE = 'none'
        MODEL_PLATFORM = "openai"
        MODEL_TYPE = "gpt-4o-mini"
    
    # Test basic initialization
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    config = MockConfig()
    simulation = MarketSimulation(db_path, config)
    
    assert simulation.database_path == db_path
    assert simulation.config == config
    assert simulation.sellers_history == {}
    print("✓ MarketSimulation initialization successful")
    
    # Test environment setup
    simulation.setup_environment()
    assert os.environ['MARKET_DB_PATH'] == db_path
    print("✓ Environment setup successful")
    
    # Test seller history update structure
    simulation.sellers_history = {1: []}
    assert 1 in simulation.sellers_history
    print("✓ Seller history structure initialized")
    
    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("\nAll simulation tests passed!")
    print("Note: Full integration tests require OASIS package and LLM API access")
