"""
Extract action_reasoning from experiment action logs into a structured JSON file.

Usage:
    python restructure4web.py <actions_json_file> [--output <output_file>]

Examples:
    python restructure4web.py experiments/gpt-4o-mini/paper/rq2/r_wsc_R_pressure_quickprofits/run_1_actions.json
    python restructure4web.py run_1_actions.json --output reasoning.json
"""

import argparse
import json
from pathlib import Path


def extract_reasoning(json_path: str) -> list[dict]:
    with open(json_path) as f:
        data = json.load(f)

    records = []
    for item in data:
        if "agent_infos" not in item:
            continue
        round_num = item.get("round", -1)
        phase = item.get("phase")
        for agent_info in item["agent_infos"]:
            aai = agent_info.get("agent_action_info", {})
            reasoning = aai.get("action_reasoning", "")
            if not reasoning:
                continue
            records.append({
                "round": round_num,
                "phase": phase,
                "agent_id": agent_info.get("agent_id", -1),
                "agent_name": agent_info.get("agent_name", "unknown"),
                "action_name": aai.get("action_name", "unknown"),
                "action_reasoning": reasoning,
            })
    return records


def main():
    parser = argparse.ArgumentParser(description="Extract action_reasoning from actions.json into structured JSON.")
    parser.add_argument("json_file", help="Path to run_*_actions.json")
    parser.add_argument("--output", default=None, help="Output JSON file path (default: <input_dir>/reasoning.json)")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    records = extract_reasoning(str(json_path))
    print(f"Extracted {len(records)} action_reasoning records from {json_path.name}")

    output_path = Path(args.output) if args.output else json_path.parent / "reasoning.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
