"""
Statistics calculation module
Provides functions for calculating various statistics from simulation data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from .data_loader import ExperimentDataLoader


class StatisticsCalculator:
    """Calculator for aggregated statistics"""
    
    def __init__(self, run_data: Dict[str, Dict[str, pd.DataFrame]]):
        """
        Initialize statistics calculator
        
        Args:
            run_data: Dictionary mapping run_key (str) to run data dictionaries
        """
        self.run_data = run_data
    
    def calculate_cross_run_statistics(self) -> Dict[str, Any]:
        """
        Calculate cross-run statistics
        
        Returns:
            Dictionary containing aggregated statistics
        """
        if not self.run_data:
            return {}
        
        # Import SimulationConfig here to avoid circular dependency
        import os
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, base_dir)
        from config import SimulationConfig
        
        stats = {
            'summary_stats': {},
            'round_stats': {},
            'seller_profit_by_run': {},
            'buyer_utility_by_run': {}
        }
        
        # Aggregate basic statistics
        total_transactions = []
        total_seller_profits = []
        total_buyer_utilities = []
        
        for run_id, data in self.run_data.items():
            transactions = data.get('transactions', pd.DataFrame())
            if not transactions.empty:
                total_trans = len(transactions)
                total_seller_profit = transactions['seller_profit'].sum() if 'seller_profit' in transactions.columns else 0
                total_buyer_utility = transactions['buyer_utility'].sum() if 'buyer_utility' in transactions.columns else 0
                
                total_transactions.append(total_trans)
                total_seller_profits.append(total_seller_profit)
                total_buyer_utilities.append(total_buyer_utility)
                
                stats['seller_profit_by_run'][run_id] = total_seller_profit
                stats['buyer_utility_by_run'][run_id] = total_buyer_utility
        
        # Compute cross-run statistics
        if total_transactions:
            stats['summary_stats'] = {
                'avg_transactions_per_run': float(np.mean(total_transactions)),
                'std_transactions_per_run': float(np.std(total_transactions)),
                'avg_seller_profit_per_run': float(np.mean(total_seller_profits)),
                'std_seller_profit_per_run': float(np.std(total_seller_profits)),
                'avg_buyer_utility_per_run': float(np.mean(total_buyer_utilities)),
                'std_buyer_utility_per_run': float(np.std(total_buyer_utilities)),
                'total_transactions_all_runs': int(sum(total_transactions)),
                'total_seller_profit_all_runs': float(sum(total_seller_profits)),
                'total_buyer_utility_all_runs': float(sum(total_buyer_utilities))
            }
        
        # Aggregate statistics by round
        round_stats = {}
        for round_num in range(1, SimulationConfig.SIMULATION_ROUNDS + 1):
            round_transactions = []
            round_seller_profits = []
            round_buyer_utilities = []
            
            for run_id, data in self.run_data.items():
                transactions = data.get('transactions', pd.DataFrame())
                if not transactions.empty and 'round_number' in transactions.columns:
                    round_trans = transactions[transactions['round_number'] == round_num]
                    if not round_trans.empty:
                        round_transactions.append(len(round_trans))
                        if 'seller_profit' in round_trans.columns:
                            round_seller_profits.append(round_trans['seller_profit'].sum())
                        if 'buyer_utility' in round_trans.columns:
                            round_buyer_utilities.append(round_trans['buyer_utility'].sum())
            
            if round_transactions:
                round_stats[round_num] = {
                    'avg_transactions': float(np.mean(round_transactions)),
                    'std_transactions': float(np.std(round_transactions)),
                    'avg_seller_profit': float(np.mean(round_seller_profits)) if round_seller_profits else 0.0,
                    'std_seller_profit': float(np.std(round_seller_profits)) if round_seller_profits else 0.0,
                    'avg_buyer_utility': float(np.mean(round_buyer_utilities)) if round_buyer_utilities else 0.0,
                    'std_buyer_utility': float(np.std(round_buyer_utilities)) if round_buyer_utilities else 0.0
                }
        
        stats['round_stats'] = round_stats
        return stats
    
    def calculate_deception_statistics(self) -> Dict[str, Any]:
        """
        Calculate seller deception statistics
        
        Deception behavior: seller advertises HQ but provides LQ products
        
        Returns:
            Dictionary containing deception statistics
        """
        stats = {
            'total_deceptions_by_run': {},
            'deception_rate_by_run': {},
            'seller_deception_count': {},
            'overall_deception_stats': {}
        }
        
        for run_id, data in self.run_data.items():
            products = data.get('product', pd.DataFrame())
            if products is None or products.empty:
                continue
            
            # Count deceptions (advertised HQ but actual LQ)
            if 'advertised_quality' in products.columns and 'true_quality' in products.columns:
                deceptions = products[
                    (products['advertised_quality'] == 'HQ') & 
                    (products['true_quality'] == 'LQ')
                ]
                total_deceptions = len(deceptions)
                
                # Calculate deception rate
                hq_advertised = len(products[products['advertised_quality'] == 'HQ'])
                deception_rate = total_deceptions / hq_advertised if hq_advertised > 0 else 0
                
                stats['total_deceptions_by_run'][run_id] = total_deceptions
                stats['deception_rate_by_run'][run_id] = deception_rate
                
                # Count deceptions by seller
                if not deceptions.empty and 'user_id' in deceptions.columns:
                    seller_deceptions = deceptions.groupby('user_id').size().to_dict()
                    for seller_id, count in seller_deceptions.items():
                        if seller_id not in stats['seller_deception_count']:
                            stats['seller_deception_count'][seller_id] = []
                        stats['seller_deception_count'][seller_id].append(count)
        
        # Compute overall statistics
        if stats['total_deceptions_by_run']:
            total_deceptions_list = list(stats['total_deceptions_by_run'].values())
            deception_rates_list = list(stats['deception_rate_by_run'].values())
            
            stats['overall_deception_stats'] = {
                'avg_deceptions_per_run': float(np.mean(total_deceptions_list)),
                'std_deceptions_per_run': float(np.std(total_deceptions_list)),
                'max_deceptions_per_run': int(max(total_deceptions_list)),
                'min_deceptions_per_run': int(min(total_deceptions_list)),
                'avg_deception_rate': float(np.mean(deception_rates_list)),
                'std_deception_rate': float(np.std(deception_rates_list)),
                'total_deceptions_all_runs': int(sum(total_deceptions_list))
            }
        
        return stats
    
    def prepare_cross_run_comparison_data(self) -> Dict[str, List]:
        """
        Prepare data for cross-run comparison plots
        
        Returns:
            Dictionary containing comparison data with honest/dishonest breakdowns
        """
        if not self.run_data:
            return {}
        
        run_ids = []
        seller_profits = []
        honest_profits = []
        dishonest_profits = []
        buyer_utilities = []
        honest_buyer_utilities = []
        dishonest_buyer_utilities = []
        transaction_counts = []
        honest_transaction_counts = []
        dishonest_transaction_counts = []
        
        for run_id, data in self.run_data.items():
            transactions = data.get('transactions', pd.DataFrame())
            products = data.get('product', pd.DataFrame())
            
            if transactions.empty:
                continue
            
            run_ids.append(run_id)
            
            # Associate transactions with products to distinguish honest/dishonest
            if not products.empty and 'product_id' in transactions.columns:
                merged = transactions.merge(
                    products[['product_id', 'advertised_quality', 'true_quality']],
                    on='product_id',
                    how='left'
                )
                
                # Identify dishonest transactions: advertised HQ but true LQ
                dishonest_mask = (
                    (merged['advertised_quality'] == 'HQ') & 
                    (merged['true_quality'] == 'LQ')
                )
                
                if 'seller_profit' in merged.columns:
                    dishonest_profit = merged[dishonest_mask]['seller_profit'].fillna(0).sum()
                    honest_profit = merged[~dishonest_mask]['seller_profit'].fillna(0).sum()
                else:
                    dishonest_profit = 0
                    honest_profit = 0
                
                if 'buyer_utility' in merged.columns:
                    dishonest_buyer_utility = merged[dishonest_mask]['buyer_utility'].fillna(0).sum()
                    honest_buyer_utility = merged[~dishonest_mask]['buyer_utility'].fillna(0).sum()
                else:
                    dishonest_buyer_utility = 0
                    honest_buyer_utility = 0
                
                dishonest_transaction_count = len(merged[dishonest_mask])
                honest_transaction_count = len(merged[~dishonest_mask])
            else:
                # If cannot merge, use defaults
                if 'seller_profit' in transactions.columns:
                    honest_profit = transactions['seller_profit'].fillna(0).sum()
                else:
                    honest_profit = 0
                dishonest_profit = 0
                
                if 'buyer_utility' in transactions.columns:
                    honest_buyer_utility = transactions['buyer_utility'].fillna(0).sum()
                else:
                    honest_buyer_utility = 0
                dishonest_buyer_utility = 0
                
                honest_transaction_count = len(transactions)
                dishonest_transaction_count = 0
            
            honest_profits.append(float(honest_profit))
            dishonest_profits.append(float(dishonest_profit))
            seller_profits.append(float(honest_profit + dishonest_profit))
            honest_buyer_utilities.append(float(honest_buyer_utility))
            dishonest_buyer_utilities.append(float(dishonest_buyer_utility))
            buyer_utilities.append(float(honest_buyer_utility + dishonest_buyer_utility))
            honest_transaction_counts.append(int(honest_transaction_count))
            dishonest_transaction_counts.append(int(dishonest_transaction_count))
            transaction_counts.append(int(honest_transaction_count + dishonest_transaction_count))
        
        if not run_ids:
            return {}
        
        return {
            'run_ids': run_ids,
            'seller_profits': seller_profits,
            'honest_profits': honest_profits,
            'dishonest_profits': dishonest_profits,
            'buyer_utilities': buyer_utilities,
            'honest_buyer_utilities': honest_buyer_utilities,
            'dishonest_buyer_utilities': dishonest_buyer_utilities,
            'transaction_counts': transaction_counts,
            'honest_transaction_counts': honest_transaction_counts,
            'dishonest_transaction_counts': dishonest_transaction_counts
        }


# Test cases
if __name__ == "__main__":
    print("Statistics calculation module")
    print("This module requires actual data to test.")
    print("Usage:")
    print("  from visualization.core.statistics import StatisticsCalculator")
    print("  calculator = StatisticsCalculator(run_data)")
    print("  stats = calculator.calculate_cross_run_statistics()")
