#!/usr/bin/env python3
"""
Export Market Results from SQLite Database to JSON
This script extracts market results from .db files and creates *_results.json files
that are compatible with the table generation scripts.
"""

import sqlite3
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import sys


def extract_market_results(db_path: str) -> List[Dict[str, Any]]:
    """
    Extract market results from database.

    Returns product-level data for compatibility with table generation scripts.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []

    # Get all products with seller and transaction information
    cursor.execute("""
        SELECT
            p.product_id,
            p.user_id as seller_id,
            p.round_number,
            p.advertised_quality,
            p.true_quality as actual_quality,
            p.price,
            p.cost,
            p.has_warrant,
            p.is_sold,
            p.status,
            t.buyer_id,
            t.rating,
            t.seller_profit,
            t.buyer_utility,
            t.is_challenged,
            u.agent_id,
            u.thumbs_up_count,
            u.thumbs_down_count,
            u.budget,
            u.profit_utility_score
        FROM product p
        LEFT JOIN transactions t ON p.product_id = t.product_id
        LEFT JOIN user u ON p.user_id = u.user_id
        WHERE u.role = 'seller'
        ORDER BY p.round_number, p.user_id, p.product_id
    """)

    products = cursor.fetchall()

    for product in products:
        # Calculate reputation score
        thumbs_up = product['thumbs_up_count'] or 0
        thumbs_down = product['thumbs_down_count'] or 0

        if thumbs_up + thumbs_down > 0:
            reputation = (thumbs_up - thumbs_down) / (thumbs_up + thumbs_down) * 100
        else:
            reputation = 0.0

        # Determine if transaction was honest
        is_honest = (product['advertised_quality'] == product['actual_quality'])

        # Determine if product is authentic (no counterfeit in current schema)
        # Assume all products are authentic unless quality is misrepresented
        is_authentic = is_honest

        # Get transaction data
        if product['is_sold']:
            seller_profit = float(product['seller_profit']) if product['seller_profit'] is not None else (product['price'] - product['cost'])
            buyer_utility = float(product['buyer_utility']) if product['buyer_utility'] is not None else 0.0
            transactions = 1
            buyer_id = product['buyer_id']
        else:
            seller_profit = 0.0
            buyer_utility = 0.0
            transactions = 0
            buyer_id = None

        # Create result entry for this product
        result = {
            'product_id': product['product_id'],
            'agent_id': product['agent_id'],
            'seller_id': product['seller_id'],
            'round_num': product['round_number'],
            'quality': product['actual_quality'],
            'advertised_quality': product['advertised_quality'],
            'actual_quality': product['actual_quality'],
            'is_authentic': is_authentic,
            'is_honest': is_honest,
            'price': float(product['price']),
            'cost': float(product['cost']),
            'has_warrant': bool(product['has_warrant']),
            'sold': bool(product['is_sold']),
            'is_sold': bool(product['is_sold']),
            'status': product['status'],
            'buyer_id': buyer_id,
            'rating': product['rating'],
            'is_challenged': bool(product['is_challenged']) if product['is_challenged'] is not None else False,
            'transactions': transactions,
            'seller_profit': seller_profit,
            'buyer_utility': buyer_utility,
            'reputation': reputation,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'budget': float(product['budget']) if product['budget'] is not None else 0.0,
            'profit_utility_score': float(product['profit_utility_score']) if product['profit_utility_score'] is not None else 0.0
        }

        results.append(result)

    conn.close()
    return results


def export_results_for_run(db_path: str, output_path: str):
    """Export results from a single run database to JSON."""
    print(f"Exporting results from {db_path}...")

    results = extract_market_results(db_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"  Exported {len(results)} results to {output_path}")


def export_experiment_directory(experiment_dir: str):
    """Export all run databases in an experiment directory."""
    exp_path = Path(experiment_dir)

    if not exp_path.exists():
        print(f"ERROR: Directory does not exist: {experiment_dir}")
        return

    # Find all .db files
    db_files = list(exp_path.glob("run_*.db"))

    if not db_files:
        print(f"No database files found in {experiment_dir}")
        return

    print(f"Found {len(db_files)} database files")

    for db_file in sorted(db_files):
        # Generate output filename
        run_name = db_file.stem  # e.g., "run_1"
        output_file = exp_path / f"{run_name}_results.json"

        try:
            export_results_for_run(str(db_file), str(output_file))
        except Exception as e:
            print(f"ERROR exporting {db_file.name}: {e}")

    print(f"\n✅ Export complete for {experiment_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Export market results from SQLite databases to JSON"
    )
    parser.add_argument(
        "experiment_dir",
        type=str,
        help="Path to experiment directory containing run_*.db files"
    )

    args = parser.parse_args()

    export_experiment_directory(args.experiment_dir)


if __name__ == "__main__":
    main()
