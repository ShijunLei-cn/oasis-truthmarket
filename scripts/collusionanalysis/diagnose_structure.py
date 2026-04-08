#!/usr/bin/env python3
"""
Diagnostic script to explore the actual structure of experiment action files.
"""

import json
from pathlib import Path
from collections import defaultdict


def explore_structure():
    """Explore the structure of action files."""
    print("=" * 70)
    print("DIAGNOSTIC: Exploring Action File Structure")
    print("=" * 70)
    
    # Try different possible file paths
    possible_paths = [
        "experiments/gpt-4o-mini/paper/rq2/r_wsc_R_policy_making/run_1_actions.json",
        "experiments/gpt-4o-mini/paper/rq2/r_wsc_R_policy_making/run_1.json",
        "rq2/r_wsc_R_policy_making/run_1_actions.json",
    ]
    
    data = None
    file_path = None
    
    for path in possible_paths:
        p = Path(path)
        if p.exists():
            print(f"\n✓ Found file: {path}")
            with open(p) as f:
                data = json.load(f)
            file_path = p
            break
    
    if data is None:
        print("\n✗ No action file found in standard locations")
        print("\nSearching for any JSON files...")
        for json_file in Path(".").rglob("run_*_*.json"):
            print(f"  Found: {json_file}")
        return
    
    print(f"\n=== Basic Info ===")
    print(f"Type: {type(data)}")
    if isinstance(data, list):
        print(f"Length: {len(data)}")
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
    
    if isinstance(data, list) and len(data) > 0:
        r = data[0]
        print(f"\n=== Round 0 Structure ===")
        print(f"Keys: {list(r.keys())}")
        
        # Explore agent_infos
        if "agent_infos" in r:
            agents = r["agent_infos"]
            print(f"\n=== Agent Infos ({len(agents)} agents) ===")
            
            for i, agent in enumerate(agents[:5]):
                print(f"\n--- Agent {i+1} ---")
                print(f"  Keys: {list(agent.keys())}")
                
                # Check agent_action_info
                action_info = agent.get("agent_action_info", {})
                print(f"  Action Info Keys: {list(action_info.keys())}")
                print(f"  Action Name: {action_info.get('action_name', 'N/A')}")
                
                # Print all action_info content
                for key, val in action_info.items():
                    if isinstance(val, str):
                        preview = val[:150] + "..." if len(val) > 150 else val
                        print(f"    {key}: {preview}")
                    else:
                        print(f"    {key}: {val}")
        
        # Look for alternative structures
        print(f"\n=== Looking for Communication Data ===")
        
        # Check if there's a different field for posts
        for key in r.keys():
            if "post" in key.lower() or "social" in key.lower() or "forum" in key.lower():
                print(f"  Found relevant field: {key}")
        
        # Check all keys for potential communication
        print(f"\n=== All Round 0 Fields ===")
        for key in r.keys():
            val = r[key]
            if isinstance(val, list):
                print(f"  {key}: list of {len(val)} items")
            elif isinstance(val, dict):
                print(f"  {key}: dict with keys {list(val.keys())[:5]}")
            else:
                print(f"  {key}: {type(val).__name__} = {val}")


def find_all_action_fields():
    """Search through all action files to find all possible fields."""
    print("\n" + "=" * 70)
    print("Searching for Communication-Related Fields")
    print("=" * 70)
    
    all_fields = defaultdict(int)
    all_action_names = defaultdict(int)
    all_post_fields = []
    
    for json_file in Path(".").rglob("run_*_actions.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            for round_data in data[:1]:  # Check first round of each file
                for agent in round_data.get("agent_infos", []):
                    action_info = agent.get("agent_action_info", {})
                    action_name = action_info.get("action_name", "")
                    all_action_names[action_name] += 1
                    
                    # Check for post-related fields
                    for key in action_info.keys():
                        if any(x in key.lower() for x in ["post", "message", "content", "text"]):
                            all_fields[key] += 1
        except Exception as e:
            pass
    
    print("\n=== All Action Names ===")
    for name, count in sorted(all_action_names.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count}")
    
    if all_fields:
        print("\n=== Post/Content Related Fields ===")
        for field, count in sorted(all_fields.items(), key=lambda x: -x[1]):
            print(f"  {field}: {count}")


def explore_sample_agent_action():
    """Get a complete sample of one agent's action data."""
    print("\n" + "=" * 70)
    print("Complete Sample of One Agent's Action Data")
    print("=" * 70)
    
    for json_file in Path(".").rglob("run_*_actions.json"):
        with open(json_file) as f:
            data = json.load(f)
        
        for round_data in data:
            for agent in round_data.get("agent_infos", []):
                action_info = agent.get("agent_action_info", {})
                action_name = action_info.get("action_name", "")
                
                # Find a post action if exists
                if "post" in action_name.lower():
                    print(f"\nFile: {json_file}")
                    print(f"Round: {round_data.get('round')}")
                    print(f"Agent: {agent.get('agent_name')}")
                    print(f"Action: {action_name}")
                    print("\nFull action_info:")
                    print(json.dumps(action_info, indent=2, ensure_ascii=False)[:2000])
                    return


if __name__ == "__main__":
    explore_structure()
    find_all_action_fields()
    explore_sample_agent_action()
