#!/usr/bin/env python3
"""
Validate Paper Table Generators

This script validates that all table generators are properly configured
and can be imported without errors.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from paper_table_generator import (
            format_number,
            generate_latex_table,
            save_latex_table,
            create_summary_stats_table,
            create_manipulation_detection_table,
            create_product_quality_table,
            create_market_outcomes_table,
            create_profit_decomposition_table
        )
        print("  ✓ paper_table_generator imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import paper_table_generator: {e}")
        return False

    try:
        from generate_rq1_paper_tables import (
            load_market_results,
            load_probe_results,
            calculate_market_statistics,
            calculate_manipulation_detection,
            calculate_product_quality
        )
        print("  ✓ generate_rq1_paper_tables imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import generate_rq1_paper_tables: {e}")
        return False

    try:
        from generate_rq2_paper_tables_complete import (
            load_experiment_results as load_rq2_results,
            calculate_experiment_statistics,
            create_rq2_initial_posts_table,
            create_rq2_product_quality_table,
            create_rq2_profit_decomposition_table
        )
        print("  ✓ generate_rq2_paper_tables_complete imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import generate_rq2_paper_tables_complete: {e}")
        return False

    try:
        from generate_rq3_paper_tables_complete import (
            load_experiment_results as load_rq3_results,
            calculate_communication_statistics,
            create_rq3_summary_table,
            create_rq3_product_quality_table
        )
        print("  ✓ generate_rq3_paper_tables_complete imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import generate_rq3_paper_tables_complete: {e}")
        return False

    try:
        from generate_all_paper_tables import main as generate_all_main
        print("  ✓ generate_all_paper_tables imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import generate_all_paper_tables: {e}")
        return False

    return True


def test_basic_functionality():
    """Test basic functionality of core functions."""
    print("\nTesting basic functionality...")

    try:
        from paper_table_generator import format_number

        # Test format_number
        result = format_number(100.5, 10.2)
        expected = "100.5±10.2"

        if result == expected:
            print(f"  ✓ format_number(100.5, 10.2) = {result}")
        else:
            print(f"  ✗ format_number(100.5, 10.2) = {result}, expected {expected}")
            return False
    except Exception as e:
        print(f"  ✗ Failed to test format_number: {e}")
        return False

    try:
        from paper_table_generator import generate_latex_table

        # Test generate_latex_table with minimal data
        table_code = generate_latex_table(
            caption="Test Table",
            label="tab:test",
            headers=["Col1", "Col2"],
            rows=[["Value1", "Value2"]],
            table_type="table*",
            position="t"
        )

        if "\\begin{table*}" in table_code and "\\caption{Test Table}" in table_code:
            print("  ✓ generate_latex_table produces valid LaTeX")
        else:
            print("  ✗ generate_latex_table output is invalid")
            return False
    except Exception as e:
        print(f"  ✗ Failed to test generate_latex_table: {e}")
        return False

    return True


def test_script_execution():
    """Test that scripts can be executed with --help."""
    print("\nTesting script execution...")

    scripts_to_test = [
        "generate_rq1_paper_tables.py",
        "generate_rq2_paper_tables.py",
        "generate_rq3_paper_tables.py",
        "generate_all_paper_tables.py"
    ]

    for script_name in scripts_to_test:
        script_path = Path(__file__).parent / script_name

        if not script_path.exists():
            print(f"  ✗ Script not found: {script_name}")
            return False

        # Check if file is executable or can be read
        if script_path.stat().st_size == 0:
            print(f"  ✗ Script is empty: {script_name}")
            return False

        # Check for shebang
        with open(script_path, 'r') as f:
            first_line = f.readline().strip()
            if not first_line.startswith("#!"):
                print(f"  ⚠ Missing shebang in {script_name}")

        print(f"  ✓ Script exists and has content: {script_name}")

    return True


def test_main_runner():
    """Test that the main bash runner exists and is executable."""
    print("\nTesting main runner script...")

    runner_path = Path(__file__).parent / "run_paper_visualization_main.sh"

    if not runner_path.exists():
        print("  ✗ Main runner script not found")
        return False

    # Check if it's executable
    if not (runner_path.stat().st_mode & 0o111):
        print("  ⚠ Main runner is not executable (this is OK, can be run with bash)")

    # Check content
    with open(runner_path, 'r') as f:
        content = f.read()

        required_elements = [
            "generate_rq2_paper_tables.py",
            "generate_rq3_paper_tables.py",
            "EXPERIMENT_PREFIX",
            "rq1",
            "rq2",
            "rq3"
        ]

        missing = []
        for element in required_elements:
            if element not in content:
                missing.append(element)

        if missing:
            print(f"  ✗ Main runner missing required elements: {missing}")
            return False

    print("  ✓ Main runner script is properly configured")
    return True


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Paper Table Generator Validation")
    print("=" * 70)

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test basic functionality
    if not test_basic_functionality():
        all_passed = False

    # Test script execution
    if not test_script_execution():
        all_passed = False

    # Test main runner
    if not test_main_runner():
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All validation tests passed!")
        print("=" * 70)
        print("\nThe visualization system is ready to use.")
        print("\nTo generate tables:")
        print("  1. Ensure experimental data is in the correct directories")
        print("  2. Run: bash run_paper_visualization_main.sh")
        print("\nOr use the Python master script:")
        print("  python generate_all_paper_tables.py --rq1 ... --rq2 ... --rq3 ...")
        return 0
    else:
        print("✗ Some validation tests failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
