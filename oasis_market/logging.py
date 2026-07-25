"""
Logging and action recording module for market simulation
Handles saving and managing simulation action logs
"""

import os
import json
import tempfile
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

    def _write_records_atomic(self, records: List[Dict]) -> None:
        """Replace the cumulative action log without exposing partial JSON."""
        output_path = os.path.abspath(self.log_path)
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        file_descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{os.path.basename(output_path)}.",
            suffix=".tmp",
            dir=output_dir,
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    records,
                    handle,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, output_path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
    
    def save_system_prompts(self, agent_graph):
        """
        Save all agent system prompts to JSON file (Round 0)
        
        Args:
            agent_graph: AgentGraph containing all agents
        """
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Load existing records if any
        all_records = []
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
        
        # Collect system prompts from all agents
        system_prompts = {
            'sellers': {},
            'buyers': {}
        }
        
        for agent_id, agent in agent_graph.get_agents():
            role = agent.user_info.profile.get("role")
            system_message_content = agent.system_message.content if hasattr(agent, 'system_message') and agent.system_message else ""
            
            if role == 'seller':
                system_prompts['sellers'][agent_id] = {
                    'agent_id': agent_id,
                    'name': agent.user_info.name,
                    'description': agent.user_info.description,
                    'system_prompt': system_message_content
                }
            elif role == 'buyer':
                system_prompts['buyers'][agent_id] = {
                    'agent_id': agent_id,
                    'name': agent.user_info.name,
                    'description': agent.user_info.description,
                    'system_prompt': system_message_content
                }
        
        # Add system prompts record (Round 0)
        all_records.append({
            'round': 0,
            'phase': 'initialization',
            'timestamp': datetime.now().isoformat(),
            'type': 'system_prompts',
            'system_prompts': system_prompts
        })
        
        self._write_records_atomic(all_records)
    
    def _format_as_one_line(self, obj: Any) -> str:
        """
        Format an object as a one-line JSON string
        
        Args:
            obj: Object to format
            
        Returns:
            One-line JSON string
        """
        if obj is None:
            return ""
        try:
            return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError):
            return str(obj)
    
    def _clean_action_result(self, action_result: Any) -> Dict:
        """
        Clean action_result by removing agent_id, _action_name, _action_args fields
        
        Args:
            action_result: Action result dictionary
            
        Returns:
            Cleaned action result dictionary
        """
        if not isinstance(action_result, dict):
            return action_result
        
        cleaned = {}
        for key, value in action_result.items():
            if key not in ['agent_id', '_action_name', '_action_args']:
                cleaned[key] = value
        
        return cleaned
    
    def _get_agent_name(self, agent_id: int, agent_graph) -> str:
        """
        Get agent name from agent_graph
        
        Args:
            agent_id: Agent ID
            agent_graph: AgentGraph containing agents
            
        Returns:
            Agent name or empty string
        """
        if agent_graph is None:
            return ""
        
        try:
            agent = agent_graph.get_agent(agent_id)
            if agent and hasattr(agent, 'user_info'):
                return agent.user_info.name or ""
        except (KeyError, AttributeError):
            pass
        
        return ""
    
    def save_action_records(self, env, round_num: int, phase: str, agent_graph=None):
        """
        Save env.step() detailed results to JSON file, including prompts sent to agents
        Organized by round and phase with agent_infos array
        
        Args:
            env: Environment object with action results
            round_num: Current round number
            phase: Current phase name
            agent_graph: Optional AgentGraph to retrieve agent names and prompt information
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
        
        # Get prompt information from env if available
        last_step_prompts = getattr(env, '_last_step_prompts', {})
        
        # Build agent_infos array for this round/phase
        agent_infos = []
        
        for result in env._last_step_detailed_results:
            agent_id = result.get('agent_id')
            if agent_id is None:
                continue
            
            # Get agent name
            agent_name = self._get_agent_name(agent_id, agent_graph)
            
            # Get prompt information for this agent
            prompt_info = last_step_prompts.get(agent_id, {})
            
            # Clean action_result
            action_result = result.get('action_result')
            cleaned_action_result = self._clean_action_result(action_result)
            
            # Build agent action info
            agent_action_info = {
                'action_name': result.get('action_name', ''),
                'action_args': self._format_as_one_line(result.get('action_args')),
                'action_results': self._format_as_one_line(cleaned_action_result),
                'action_reasoning': result.get('reasoning', '')
            }
            
            # Build prompts
            prompts = {}
            if prompt_info:
                prompts = {
                    'system_message': prompt_info.get('system_message', ''),
                    'user_message': prompt_info.get('user_message', ''),
                    'environment_prompt': prompt_info.get('environment_prompt', ''),
                    'extra_prompt': prompt_info.get('extra_prompt', '')
                }
            
            # Add agent info
            agent_infos.append({
                'agent_id': agent_id,
                'agent_name': agent_name,
                'agent_action_info': agent_action_info,
                'prompts': prompts
            })
        
        # Create record for this round/phase
        if agent_infos:
            record = {
                'round': round_num,
                'phase': phase,
                'timestamp': datetime.now().isoformat(),
                'agent_infos': agent_infos
            }
            
            all_records.append(record)
        
        self._write_records_atomic(all_records)
    
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
            if record.get('round') == round_num and record.get('phase') == phase
        ]
    
    def get_agent_actions(self, agent_id: int) -> List[Dict]:
        """
        Get all actions for a specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of action records containing the agent
        """
        all_records = self.load_action_records()
        matching_records = []
        for record in all_records:
            if record.get('type') == 'system_prompts':
                continue
            agent_infos = record.get('agent_infos', [])
            for agent_info in agent_infos:
                if agent_info.get('agent_id') == agent_id:
                    matching_records.append(record)
                    break
        return matching_records


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
