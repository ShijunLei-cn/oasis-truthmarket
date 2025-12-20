# Parallel Interview Agent Operations Guide

This document explains how to execute interview operations in parallel within the OASIS system, and how to record and query interview results.

## Table of Contents

1. [Parallel Interview Execution](#parallel-interview-execution)
2. [Interview Recording Methods](#interview-recording-methods)
3. [Code Examples](#code-examples)
4. [Querying Interview Records](#querying-interview-records)

---

## Parallel Interview Execution

### Basic Principles

The `env.step()` method in the OASIS environment natively supports parallel execution of multiple interview operations. When you pass a dictionary containing multiple `ManualAction` objects to `env.step()`, all interview operations will be automatically executed in parallel.

### Execution Flow

1. **Create Interview Actions Dictionary**: Create a `ManualAction` for each agent to be interviewed, with `action_type` set to `ActionType.INTERVIEW`
2. **Pass to env.step()**: Pass all interview actions as a dictionary to `env.step()`
3. **Automatic Parallel Execution**: The environment automatically adds all interview tasks to a task list and executes them in parallel using `asyncio.gather()`
4. **Return Results**: All interview results are returned as a list

### Key Code Location

In `oasis/environment/env.py`:

```python
async def step(self, actions: dict):
    tasks = []
    for agent, action in actions.items():
        if isinstance(action, ManualAction):
            if action.action_type == ActionType.INTERVIEW:
                interview_prompt = action.action_args.get("prompt", "")
                tasks.append(self._perform_interview_action(agent, interview_prompt))
    # Execute all tasks in parallel
    responses = await asyncio.gather(*tasks)
```

---

## Interview Recording Methods

### Automatic Recording Mechanism

Interview results are automatically recorded in the `trace` table of the database, containing the following information:

- `user_id`: The ID of the agent being interviewed
- `action`: Fixed as `"interview"`
- `info`: JSON-formatted interview details, containing:
  - `prompt`: The interview question
  - `response`: The agent's response
  - `interview_id`: Unique identifier (format: `{timestamp}_{user_id}`)
- `created_at`: Creation timestamp

### Recording Flow

1. **Agent Executes Interview**: The `agent.perform_interview()` method calls the LLM to generate a response
2. **Platform Recording**: Results are written to the database through the `platform.interview()` method
3. **Storage Format**: Interview data is stored in JSON format in the `trace.info` field

### Code Implementation Locations

**Agent Side** (`oasis/social_agent/agent.py`):
```python
async def perform_interview(self, interview_prompt: str):
    # ... Call LLM to generate response ...
    interview_data = {"prompt": interview_prompt, "response": content}
    result = await self.env.action.perform_action(
        interview_data, ActionType.INTERVIEW.value)
```

**Platform Side** (`oasis/social_platform/platform.py`):
```python
async def interview(self, agent_id: int, interview_data):
    # Supports two formats:
    # 1. String format (prompt only)
    # 2. Dictionary format (prompt + response)
    if isinstance(interview_data, str):
        prompt = interview_data
        response = None
    else:
        prompt = interview_data.get("prompt", "")
        response = interview_data.get("response", "")
    
    # Record to trace table
    self.pl_utils._record_trace(user_id, ActionType.INTERVIEW.value,
                                action_info, current_time)
```

---

## Code Examples

### Example 1: Parallel Interview Multiple Agents

```python
import asyncio
from oasis import make, AgentGraph
from oasis.environment.env_action import ManualAction
from oasis.social_platform.typing import ActionType

async def parallel_interview_example():
    # Assume env and agent_graph are already created
    env = make(...)
    await env.reset()
    
    # Create parallel interview actions
    interview_actions = {}
    
    # Interview Agent 0
    interview_actions[env.agent_graph.get_agent(0)] = ManualAction(
        action_type=ActionType.INTERVIEW,
        action_args={
            "prompt": "What do you think about the shape of the Earth?"
        }
    )
    
    # Interview Agent 1
    interview_actions[env.agent_graph.get_agent(1)] = ManualAction(
        action_type=ActionType.INTERVIEW,
        action_args={
            "prompt": "Why do you believe the Earth is not flat?"
        }
    )
    
    # Interview Agent 2
    interview_actions[env.agent_graph.get_agent(2)] = ManualAction(
        action_type=ActionType.INTERVIEW,
        action_args={
            "prompt": "What are your thoughts on the debate about Earth's shape?"
        }
    )
    
    # Execute all interviews in parallel (automatic parallelization)
    results = await env.step(interview_actions)
    
    # results contains all interview results
    for result in results:
        print(f"Agent {result.get('agent_id')} interview completed")
        print(f"Success: {result.get('success')}")
        print(f"Interview ID: {result.get('interview_id')}")
```

### Example 2: Interview Sellers in Simulation Loop

```python
async def interview_sellers_in_simulation(env, agent_graph, round_num, database_path):
    """Parallel interview all sellers in each round"""
    
    # Create seller interview actions
    seller_interview_actions = {}
    
    for agent_id, agent in agent_graph.get_agents():
        if agent.user_info.profile.get("role") == 'seller':
            # Generate interview prompt based on current state
            state = get_agent_state(agent_id, 'seller', round_num, database_path)
            interview_prompt = (
                f"Round {round_num}: "
                f"Your current reputation is {state.get('reputation_score', 0)}. "
                f"Your total profit is {state.get('total_profit', 0)}. "
                f"What is your strategy for this round?"
            )
            
            seller_interview_actions[agent] = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": interview_prompt}
            )
    
    # Execute all seller interviews in parallel
    if seller_interview_actions:
        results = await env.step(seller_interview_actions)
        print(f"Completed {len(results)} seller interviews in parallel")
        
        # Save interview records
        save_interview_records(env, round_num, 'seller_interview', database_path)
    
    return results
```

### Example 3: Custom Interview Record Saving

```python
import json
import sqlite3
import os
from datetime import datetime
from oasis.social_platform.typing import ActionType

def save_interview_records(env, round_num: int, phase: str, database_path: str):
    """Save interview records to JSON file"""
    log_path = database_path.replace('.db', '_interviews.json')
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Read interview records from database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT user_id, info, created_at
        FROM trace
        WHERE action = ? AND created_at >= (
            SELECT MAX(created_at) - 1 FROM trace WHERE action = ?
        )
        ORDER BY created_at DESC
        """,
        (ActionType.INTERVIEW.value, ActionType.INTERVIEW.value)
    )
    
    all_records = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    for user_id, info_json, timestamp in cursor.fetchall():
        info = json.loads(info_json)
        all_records.append({
            'round': round_num,
            'phase': phase,
            'timestamp': datetime.now().isoformat(),
            'agent_id': user_id,
            'interview_id': info.get('interview_id'),
            'prompt': info.get('prompt'),
            'response': info.get('response'),
            'created_at': timestamp
        })
    
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, indent=2, ensure_ascii=False, default=str)
    except IOError as e:
        print(f"Warning: Failed to save interview records: {e}")
    
    conn.close()
```

---

## Querying Interview Records

### Method 1: Direct Database Query

```python
import sqlite3
import json
from oasis.social_platform.typing import ActionType

def query_interview_records(database_path: str, agent_id: int = None):
    """Query interview records"""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    if agent_id:
        cursor.execute(
            """
            SELECT user_id, info, created_at
            FROM trace
            WHERE action = ? AND user_id = ?
            ORDER BY created_at DESC
            """,
            (ActionType.INTERVIEW.value, agent_id)
        )
    else:
        cursor.execute(
            """
            SELECT user_id, info, created_at
            FROM trace
            WHERE action = ?
            ORDER BY created_at DESC
            """,
            (ActionType.INTERVIEW.value,)
        )
    
    results = []
    for user_id, info_json, timestamp in cursor.fetchall():
        info = json.loads(info_json)
        results.append({
            'agent_id': user_id,
            'timestamp': timestamp,
            'prompt': info.get('prompt', 'N/A'),
            'response': info.get('response', 'N/A'),
            'interview_id': info.get('interview_id', 'N/A')
        })
    
    conn.close()
    return results

# Usage example
interviews = query_interview_records('market_sim.db')
for interview in interviews:
    print(f"\nAgent {interview['agent_id']} (Time: {interview['timestamp']}):")
    print(f"Prompt: {interview['prompt']}")
    print(f"Response: {interview['response']}")
```

### Method 2: Query by Round

```python
def query_interviews_by_round(database_path: str, round_num: int):
    """Query interview records for a specific round"""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Assume round information is stored in a field, or inferred from timestamp
    # This needs to be adjusted based on actual database structure
    cursor.execute(
        """
        SELECT user_id, info, created_at
        FROM trace
        WHERE action = ?
        ORDER BY created_at DESC
        """,
        (ActionType.INTERVIEW.value,)
    )
    
    results = []
    for user_id, info_json, timestamp in cursor.fetchall():
        info = json.loads(info_json)
        results.append({
            'agent_id': user_id,
            'timestamp': timestamp,
            'prompt': info.get('prompt'),
            'response': info.get('response'),
            'interview_id': info.get('interview_id')
        })
    
    conn.close()
    return results
```

### Method 3: Export to JSON File

```python
def export_interviews_to_json(database_path: str, output_path: str):
    """Export all interview records to JSON"""
    interviews = query_interview_records(database_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(interviews, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Exported {len(interviews)} interview records to {output_path}")
```

---

## Best Practices

### 1. Parallel Execution Recommendations

- ✅ **Recommended**: Place multiple interview operations in the same `env.step()` call to achieve true parallelism
- ❌ **Not Recommended**: Call `env.step()` individually, which will execute serially

```python
# ✅ Recommended: Parallel execution
interview_actions = {
    agent1: ManualAction(...),
    agent2: ManualAction(...),
    agent3: ManualAction(...)
}
await env.step(interview_actions)

# ❌ Not Recommended: Serial execution
await env.step({agent1: ManualAction(...)})
await env.step({agent2: ManualAction(...)})
await env.step({agent3: ManualAction(...)})
```

### 2. Interview Prompt Design

- Use clear and specific questions
- Dynamically generate prompts based on agent's current state
- Consider contextual information (round number, history, etc.)

### 3. Record Management

- Regularly export interview records for analysis
- Use JSON files for storage to facilitate subsequent processing
- Save interview snapshots at critical rounds

### 4. Performance Optimization

- Interview operations automatically use `llm_semaphore` to control concurrency
- Be aware of API rate limits when performing many parallel interviews
- Consider batch processing instead of interviewing all agents at once

---

## Reference Files

- `oasis/environment/env.py`: Environment execution logic
- `oasis/social_platform/platform.py`: Interview platform implementation
- `oasis/social_agent/agent.py`: Agent interview execution
- `.temp/twitter_interview.py`: Complete example code

---

## Frequently Asked Questions

### Q: Are interview operations truly executed in parallel?

A: Yes. `env.step()` uses `asyncio.gather()` to execute all tasks in parallel, including interview operations.

### Q: How to ensure interview records are saved correctly?

A: Interview records are automatically saved to the `trace` table in the database. You can verify that records are saved successfully by querying the `trace` table.

### Q: Can I customize the format of interview records?

A: Yes. The `platform.interview()` method accepts dictionary-format `interview_data`, and you can add custom fields. However, standard fields (prompt, response, interview_id) are automatically handled.

### Q: Do interview operations affect agent memory?

A: It depends on the `agent.interview_record` flag. If set to `True`, interviews will be recorded in the agent's memory; if `False`, they will not affect memory.
