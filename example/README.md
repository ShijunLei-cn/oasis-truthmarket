# Example Runners (Simplified)

This directory now keeps only the active runners used by the current experiment pipeline.

## Active Entrypoints

- `run_intent_probe_experiment.py`
  - Semantic entrypoint for intent probing runs (reputation-only, cognitive probing).
  - Delegates to `run_intent_probe_batch_experiment.py`.

- `run_market_condition_experiment.py`
  - Semantic entrypoint for market-condition batch runs.
  - Delegates to `run_market_condition_batch_experiment.py`.

## Core Runner Modules

- `run_intent_probe_batch_experiment.py`
- `run_market_condition_batch_experiment.py`

These contain the real argument parsing and execution logic.

## Legacy Scripts

Older demo/ablation/general scripts were moved to:

- `example/legacy/`

Use them only for backward compatibility or archival comparison.
