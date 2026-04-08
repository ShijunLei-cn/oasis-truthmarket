#!/usr/bin/env python3
"""Extract seller behavior data including deception."""

import json
from pathlib import Path
import pandas as pd

def analyze_structure():
    """Analyze action file structure."""
    action_file = Path("experiments/gpt-4o-mini/paper/rq2/r_wsc_F_policy_making/run_1_actions.json")
    
    with open(action_file) as f:
        data = json.load(f)
    
    results = []
    
    for round_data in data:
        round_num = round_data.get("round")
        
        for agent in round_data.get("agent_infos", []):
            agent_name = agent.get("agent_name", "")
            if not agent_name.startswith("seller"):
                continue
            
            action_info = agent.get("agent_action_info", {})
            action_name = action_info.get("action_name", "")
            
            if action_name == "list_products":
                action_args = action_info.get("action_args", "{}")
                if isinstance(action_args, str):
                    try:
                        args = json.loads(action_args)
                    except:
                        args = {}
                else:
                    args = action_args
                
                products = args.get("products", [])
                
                for product in products:
                    results.append({
                        "round": round_num,
                        "agent": agent_name,
                        "action": action_name,
                        "advertised": product.get("advertised_quality", product.get("quality", "unknown")),
                        "actual": product.get("actual_quality", product.get("quality", "unknown")),
                        "product_id": product.get("product_id", ""),
                    })
    
    return results

def main():
    results = analyze_structure()
    
    print("=" * 60)
    print("ANALYZING ACTION STRUCTURE")
    print("=" * 60)
    
    print(f"\nFound {len(results)} product listings")
    
    if results:
        # 分析quality字段
        print("\nFirst 5 results:")
        for r in results[:5]:
            print(f"  {r}")
        
        # 检查所有可能的quality字段
        print("\nChecking all unique quality patterns...")
        
        # 统计
        from collections import Counter
        advertised = Counter([r['advertised'] for r in results])
        actual = Counter([r['actual'] for r in results])
        
        print("\nAdvertised quality values:", dict(advertised))
        print("Actual quality values:", dict(actual))
        
        # 检查是否有deception
        deception_count = sum(1 for r in results if r['advertised'] == 'HQ' and r['actual'] == 'LQ')
        print(f"\nDeception count (advertised HQ, actual LQ): {deception_count}")
        
        # 保存详细数据
        df = pd.DataFrame(results)
        df.to_csv("data/case_analysis/seller_actions_debug.csv", index=False)
        print("\nSaved to data/case_analysis/seller_actions_debug.csv")

if __name__ == "__main__":
    main()