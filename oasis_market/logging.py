"""
Logging and action recording module for market simulation
Handles saving and managing simulation action logs
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class ActionLogger:
    """Manages action logging for market simulation"""
    
    def __init__(self, database_path: str):
        """
        Initialize action logger
        
        Args:
            database_path: Path to database file (used to derive log path)
        """
        self.database_path = database_path
        self.log_path = self.get_action_log_path()
    
    def get_action_log_path(self) -> str:
        """
        Generate action log JSON file path from database path
        
        Returns:
            Path to action log file
        """
        return self.database_path.replace('.db', '_actions.json')
    
    def cleanup_action_log(self):
        """Clean up action log JSON file if it exists"""
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
            print(f"Action log cleaned up: {self.log_path}")
    
    def save_action_records(self, env, round_num: int, phase: str):
        """
        Save env.step() detailed results to JSON file
        
        Args:
            env: Environment object with action results
            round_num: Current round number
            phase: Current phase name
        """
        if not hasattr(env, '_last_step_detailed_results') or not env._last_step_detailed_results:
            return
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Load existing records if any
        all_records = []
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
        
        # Add new records
        for result in env._last_step_detailed_results:
            all_records.append({
                'round': round_num,
                'phase': phase,
                'timestamp': datetime.now().isoformat(),
                'agent_id': result.get('agent_id'),
                'action_name': result.get('action_name'),
                'action_args': result.get('action_args'),
                'action_result': result.get('action_result'),
                'reasoning': result.get('reasoning', '')
            })
        
        # Save all records
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, indent=2, ensure_ascii=False, default=str)
    
    def load_action_records(self) -> List[Dict]:
        """
        Load action records from log file
        
        Returns:
            List of action record dictionaries
        """
        if not os.path.exists(self.log_path):
            return []
        
        with open(self.log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_phase_actions(self, round_num: int, phase: str) -> List[Dict]:
        """
        Get actions for a specific round and phase
        
        Args:
            round_num: Round number to filter
            phase: Phase name to filter
            
        Returns:
            List of action records matching criteria
        """
        all_records = self.load_action_records()
        return [
            record for record in all_records
            if record['round'] == round_num and record['phase'] == phase
        ]
    
    def get_agent_actions(self, agent_id: int) -> List[Dict]:
        """
        Get all actions for a specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of action records for the agent
        """
        all_records = self.load_action_records()
        return [
            record for record in all_records
            if record['agent_id'] == agent_id
        ]


class SimulationLogger:
    """Provides simulation-wide logging utilities"""
    
    @staticmethod
    def print_round_header(round_num: int, total_rounds: int):
        """
        Print formatted round header
        
        Args:
            round_num: Current round number
            total_rounds: Total number of rounds
        """
        print(f"\n{'='*20} Starting Round {round_num}/{total_rounds} {'='*20}")
    
    @staticmethod
    def print_round_footer(round_num: int):
        """
        Print formatted round footer
        
        Args:
            round_num: Current round number
        """
        print(f"\n{'='*20} End of Round {round_num} {'='*20}")
    
    @staticmethod
    def print_phase_header(round_num: int, phase_name: str):
        """
        Print formatted phase header
        
        Args:
            round_num: Current round number
            phase_name: Name of the phase
        """
        print(f"\n--- [Round {round_num}] {phase_name} ---")
    
    @staticmethod
    def log_market_flags(round_num: int, exit_round: int, reentry_round: int):
        """
        Log market mechanism flags
        
        Args:
            round_num: Current round number
            exit_round: Round when exit is allowed
            reentry_round: Round when re-entry is allowed
        """
        if round_num == exit_round:
            print("Sellers may exit market. (soft flag)")
        
        if round_num == reentry_round:
            print("Re-entry policy active for low-reputation/manipulators. (soft flag)")


# Test cases
if __name__ == "__main__":
    import tempfile
    
    # Create temporary database path for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Test ActionLogger
    logger = ActionLogger(db_path)
    
    # Test log path generation
    log_path = logger.get_action_log_path()
    assert log_path.endswith('_actions.json')
    print(f"✓ Log path generated: {log_path}")
    
    # Create mock environment with results
    class MockEnv:
        def __init__(self):
            self._last_step_detailed_results = [
                {
                    'agent_id': 1,
                    'action_name': 'list_product',
                    'action_args': {'quality': 'HQ'},
                    'action_result': 'success',
                    'reasoning': 'Test reasoning'
                }
            ]
    
    env = MockEnv()
    
    # Test saving action records
    logger.save_action_records(env, round_num=1, phase='seller_listing')
    assert os.path.exists(log_path)
    print("✓ Action records saved")
    
    # Test loading action records
    records = logger.load_action_records()
    assert len(records) == 1
    assert records[0]['agent_id'] == 1
    assert records[0]['phase'] == 'seller_listing'
    print(f"✓ Action records loaded: {len(records)} records")
    
    # Test filtering by phase
    phase_actions = logger.get_phase_actions(1, 'seller_listing')
    assert len(phase_actions) == 1
    print(f"✓ Phase actions filtered: {len(phase_actions)} actions")
    
    # Test filtering by agent
    agent_actions = logger.get_agent_actions(1)
    assert len(agent_actions) == 1
    print(f"✓ Agent actions filtered: {len(agent_actions)} actions")
    
    # Clean up
    logger.cleanup_action_log()
    assert not os.path.exists(log_path)
    print("✓ Action log cleaned up")
    
    # Test SimulationLogger
    print("\nTesting SimulationLogger...")
    SimulationLogger.print_round_header(1, 7)
    SimulationLogger.print_phase_header(1, "Seller Action Phase")
    SimulationLogger.log_market_flags(8, 7, 5)
    SimulationLogger.print_round_footer(1)
    print("✓ Simulation logging methods tested")
    
    # Final cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("\nAll logging tests passed!")
