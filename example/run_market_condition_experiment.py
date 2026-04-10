#!/usr/bin/env python3
"""Semantic entrypoint for single-condition batch runs (RQ2/RQ3 replacement name)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_market_condition_batch_experiment import main


if __name__ == "__main__":
    main()
