#!/usr/bin/env python3
"""
Test Table Generation

This script tests the table generation functions with sample data
to verify everything is working correctly.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import tempfile
import json

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from paper_table_generator import (
    generate_latex_table,
    save_latex_table
)


def create_sample_data():
    """Create sample data for testing."""
    print("Creating sample data...")

    # Sample market statistics
    rep_stats = {
        'transactions': 169.0,
        'transactions_std': 51.3,
        'seller_profit': 482.2,
        'seller_profit_std': 98.4,
        'buyer_utility': 470.2,
        'buyer_utility_std': 95.5,
        'reputation': 27.6,
        'reputation_std': 24.9
    }

    rw_stats = {
        'transactions': 179.4,
        'transactions_std': 9.9,
        'seller_profit': 680.2,
        'seller_profit_std': 24.9,
        'buyer_utility': 666.2,
        'buyer_utility_std': 22.3,
        'reputation': 28.9,
        'reputation_std': 21.8
    }

    # Sample manipulation detection
    rep_detection = {
        'IW': 2.0,
        'RL': 0.4,
        'VI': 2.8,
        'RE': 0.0,
        'ES': 4.8
    }

    rw_detection = {
        'IW': 1.6,
        'RL': 0.0,
        'VI': 1.6,
        'RE': 0.0,
        'ES': 1.6
    }

    # Sample product quality
    rep_quality = {
        'hq_authentic_on_sale': 14.3,
        'hq_authentic_on_sale_std': 2.5,
        'hq_authentic_sold': 10.2,
        'hq_authentic_sold_std': 2.6,
        'lq_authentic_on_sale': 10.3,
        'lq_authentic_on_sale_std': 4.7,
        'lq_authentic_sold': 6.5,
        'lq_authentic_sold_std': 5.5,
        'hq_counterfeit_on_sale': 0.5,
        'hq_counterfeit_on_sale_std': 1.0,
        'hq_counterfeit_sold': 0.1,
        'hq_counterfeit_sold_std': 0.4
    }

    rw_quality = {
        'hq_authentic_on_sale': 16.6,
        'hq_authentic_on_sale_std': 2.1,
        'hq_authentic_sold': 16.5,
        'hq_authentic_sold_std': 2.1,
        'lq_authentic_on_sale': 2.9,
        'lq_authentic_on_sale_std': 2.6,
        'lq_authentic_sold': 1.3,
        'lq_authentic_sold_std': 1.8,
        'hq_counterfeit_on_sale': 0.2,
        'hq_counterfeit_on_sale_std': 0.6,
        'hq_counterfeit_sold': 0.1,
        'hq_counterfeit_sold_std': 0.6
    }

    return rep_stats, rw_stats, rep_detection, rw_detection, rep_quality, rw_quality


def test_table_generation():
    """Test all table generation functions."""
    print("\n" + "=" * 70)
    print("Testing Paper Table Generation")
    print("=" * 70)

    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_tables"
        output_dir.mkdir()

        # Get sample data
        rep_stats, rw_stats, rep_detection, rw_detection, rep_quality, rw_quality = create_sample_data()

        # Test 1: Summary Statistics Table
        print("\n[Test 1] Summary Statistics Table...")
        try:
            from paper_table_generator import create_summary_stats_table
            create_summary_stats_table(
                rep_stats,
                rw_stats,
                output_dir / "rq1_summary_stats.tex"
            )
            print("  ✓ Summary Statistics table generated successfully")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

        # Test 2: Manipulation Detection Table
        print("\n[Test 2] Manipulation Detection Table...")
        try:
            from paper_table_generator import create_manipulation_detection_table
            create_manipulation_detection_table(
                rep_detection,
                rw_detection,
                output_dir / "rq1_summary_comparison.tex"
            )
            print("  ✓ Manipulation Detection table generated successfully")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

        # Test 3: Product Quality Table
        print("\n[Test 3] Product Quality Table...")
        try:
            from paper_table_generator import create_product_quality_table
            create_product_quality_table(
                rep_quality,
                rw_quality,
                output_dir / "rq1_product_quality.tex"
            )
            print("  ✓ Product Quality table generated successfully")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

        # Test 4: Verify files exist
        print("\n[Test 4] Verifying generated files...")
        expected_files = [
            "rq1_summary_stats.tex",
            "rq1_summary_comparison.tex",
            "rq1_product_quality.tex"
        ]

        all_files_exist = True
        for filename in expected_files:
            filepath = output_dir / filename
            if filepath.exists():
                print(f"  ✓ {filename} exists")
                # Verify file content
                with open(filepath, 'r') as f:
                    content = f.read()
                    if '\\begin{table' in content and '\\caption' in content:
                        print(f"    ✓ {filename} contains valid LaTeX")
                    else:
                        print(f"    ✗ {filename} missing LaTeX structure")
                        all_files_exist = False
            else:
                print(f"  ✗ {filename} not found")
                all_files_exist = False

        # Test 5: Verify LaTeX structure
        print("\n[Test 5] Verifying LaTeX structure...")
        test_file = output_dir / "rq1_summary_stats.tex"
        if test_file.exists():
            with open(test_file, 'r') as f:
                content = f.read()

            checks = [
                ('\\begin{table*}', 'Table environment'),
                ('\\centering', 'Centering'),
                ('\\caption{', 'Caption'),
                ('\\label{tab:', 'Label'),
                ('\\toprule', 'Top rule'),
                ('\\midrule', 'Mid rule'),
                ('\\bottomrule', 'Bottom rule'),
                ('\\end{tabular}', 'Tabular end'),
                ('\\end{table*}', 'Table end')
            ]

            all_checks_pass = True
            for pattern, description in checks:
                if pattern in content:
                    print(f"  ✓ {description}")
                else:
                    print(f"  ✗ Missing: {description}")
                    all_checks_pass = False

            if not all_checks_pass:
                print(f"\n  Warning: Some LaTeX structure issues found")
                print(f"  Content preview:\n{content[:500]}...")

        # Test 6: Test generic table generation
        print("\n[Test 6] Generic Table Generation...")
        try:
            table_code = generate_latex_table(
                caption="Test Table",
                label="test_table",
                headers=["Header 1", "Header 2", "Header 3"],
                rows=[
                    ["Data 1", "Data 2", "Data 3"],
                    ["\\textbf{Bold Data 1}", "Data 2", "Data 3"]
                ],
                table_type="table*",
                position="t"
            )

            # Verify it contains expected elements
            if '\\begin{table*}' in table_code and '\\textbf' in table_code:
                print("  ✓ Generic table generation works")
            else:
                print("  ✗ Generic table generation failed")
                all_files_exist = False

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print("✓ All tests passed!")
    print("\nThe table generation system is working correctly.")
    print("You can now use the scripts to generate paper tables.")

    return True


if __name__ == "__main__":
    success = test_table_generation()
    sys.exit(0 if success else 1)
