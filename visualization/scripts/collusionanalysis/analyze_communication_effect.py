#!/usr/bin/env python3
"""
Collusion Analysis: Communication Channel Effects
Analyzes the impact of communication channels on seller collusion behavior.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/case_analysis")

def load_data():
    """Load all relevant data files."""
    df_condition = pd.read_csv(DATA_DIR / "type_distribution_by_condition.csv")
    df_deception = pd.read_csv(DATA_DIR / "deception_rate_by_collusion.csv")
    df_round = pd.read_csv(DATA_DIR / "type_distribution_by_round.csv")
    return df_condition, df_deception, df_round

def analyze_by_mechanism_and_communication(df_condition):
    """Analyze collusion types by mechanism and communication channel."""
    
    # Define groups
    # Rep (No Comm): r_wsc_F_*
    # Rep (Comm): r_wsc_R_*
    # Warrant (No Comm): rw_wsc_F_*
    # Warrant (Comm): rw_wsc_R_*
    
    type_cols = ['type_1', 'type_2', 'type_3', 'type_4', 'type_5', 'type_6']
    
    rep_no_comm = df_condition[df_condition['experiment_id'].str.startswith('r_wsc_F_')][type_cols].mean()
    rep_comm = df_condition[df_condition['experiment_id'].str.startswith('r_wsc_R_')][type_cols].mean()
    warrant_no_comm = df_condition[df_condition['experiment_id'].str.startswith('rw_wsc_F_')][type_cols].mean()
    warrant_comm = df_condition[df_condition['experiment_id'].str.startswith('rw_wsc_R_')][type_cols].mean()
    
    print("=" * 70)
    print("COLLUSION ANALYSIS: Communication Channel Effects")
    print("=" * 70)
    
    print("\n--- By Mechanism and Communication Channel ---")
    print(f"\n{'Type':<25} {'Rep-NoComm':<12} {'Rep-Comm':<12} {'W-NoComm':<12} {'W-Comm':<12}")
    print("-" * 70)
    
    type_names = {
        'type_1': 'Direct Collusion',
        'type_2': 'Strategy Broadcast',
        'type_3': 'Coordination',
        'type_4': 'Social Normalization',
        'type_5': 'Neutral Info',
        'type_6': 'Anti-Collusion'
    }
    
    for col in type_cols:
        print(f"{type_names[col]:<25} {rep_no_comm[col]*100:>8.2f}% {rep_comm[col]*100:>8.2f}% {warrant_no_comm[col]*100:>8.2f}% {warrant_comm[col]*100:>8.2f}%")
    
    # Calculate collusive sum (types 1-4)
    collusive_cols = ['type_1', 'type_2', 'type_3', 'type_4']
    
    print("\n--- Collusive Messaging (Types 1-4) Summary ---")
    
    rep_no_comm_collusive = rep_no_comm[collusive_cols].sum() * 100
    rep_comm_collusive = rep_comm[collusive_cols].sum() * 100
    warrant_no_comm_collusive = warrant_no_comm[collusive_cols].sum() * 100
    warrant_comm_collusive = warrant_comm[collusive_cols].sum() * 100
    
    print(f"Rep (No Comm):      {rep_no_comm_collusive:>6.2f}%")
    print(f"Rep (Comm):         {rep_comm_collusive:>6.2f}%")
    print(f"Warrant (No Comm):  {warrant_no_comm_collusive:>6.2f}%")
    print(f"Warrant (Comm):     {warrant_comm_collusive:>6.2f}%")
    
    print("\n--- Key Findings ---")
    
    # Communication effect under Rep
    comm_effect_rep = rep_comm_collusive - rep_no_comm_collusive
    print(f"\n1. Communication Effect (Rep mechanism):")
    print(f"   With Comm vs Without: {comm_effect_rep:+.2f}% ({'increases' if comm_effect_rep > 0 else 'decreases'} collusive messaging)")
    
    # Communication effect under Warrant
    comm_effect_warrant = warrant_comm_collusive - warrant_no_comm_collusive
    print(f"\n2. Communication Effect (Warrant mechanism):")
    print(f"   With Comm vs Without: {comm_effect_warrant:+.2f}% ({'increases' if comm_effect_warrant > 0 else 'decreases'} collusive messaging)")
    
    # Mechanism effect
    mech_effect_no_comm = rep_no_comm_collusive - warrant_no_comm_collusive
    mech_effect_comm = rep_comm_collusive - warrant_comm_collusive
    print(f"\n3. Mechanism Effect:")
    print(f"   Without Comm: Rep vs Warrant = {mech_effect_no_comm:+.2f}%")
    print(f"   With Comm:    Rep vs Warrant = {mech_effect_comm:+.2f}%")
    
    # Reduction percentage
    if rep_no_comm_collusive > 0:
        reduction = (rep_no_comm_collusive - warrant_no_comm_collusive) / rep_no_comm_collusive * 100
        print(f"\n4. Warrant reduces collusive messaging by {reduction:.1f}% (No Comm)")
    
    if rep_comm_collusive > 0:
        reduction_comm = (rep_comm_collusive - warrant_comm_collusive) / rep_comm_collusive * 100
        print(f"   Warrant reduces collusive messaging by {reduction_comm:.1f}% (With Comm)")

def analyze_deception_by_collusion(df_deception):
    """Analyze deception rates by collusion status."""
    print("\n" + "=" * 70)
    print("DECEPTION RATE BY COLLUSION STATUS")
    print("=" * 70)
    
    no_collusion = df_deception[df_deception['is_collusion'] == False].iloc[0]
    with_collusion = df_deception[df_deception['is_collusion'] == True].iloc[0]
    
    print(f"\nNo Collusion Detected:   {no_collusion['deception_rate']*100:.2f}% (n={no_collusion['n_posts']})")
    print(f"Collusion Detected:       {with_collusion['deception_rate']*100:.2f}% (n={with_collusion['n_posts']})")
    
    increase = with_collusion['deception_rate'] / no_collusion['deception_rate']
    print(f"\nIncrease: {increase:.1f}x (Collusion dramatically increases deception)")

def analyze_by_round(df_round):
    """Analyze collusion patterns over rounds."""
    print("\n" + "=" * 70)
    print("COLLUSION PATTERNS OVER ROUNDS")
    print("=" * 70)
    
    # The round data uses columns 1-6 instead of type_1-6
    type_cols = ['1', '2', '3', '4', '5', '6']
    collusive_cols = ['1', '2', '3', '4']
    
    df_round['collusive_sum'] = df_round[collusive_cols].sum(axis=1)
    
    print(f"\n{'Round':<8} {'Collusive %':<15} {'Trend'}")
    print("-" * 40)
    
    for _, row in df_round.iterrows():
        print(f"Round {int(row['round']):<3} {row['collusive_sum']*100:>8.2f}%")

def main():
    df_condition, df_deception, df_round = load_data()
    
    analyze_by_mechanism_and_communication(df_condition)
    analyze_deception_by_collusion(df_deception)
    analyze_by_round(df_round)
    
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()