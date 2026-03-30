"""
Cross-condition embedding comparison for action_reasoning records.
Approach 2 of 3 in the TruthMarketTwin interpretability toolkit.

APPROACH SUMMARY
----------------
Load the same action type from two or more experiment conditions, embed all
records, and measure how the embedding DISTRIBUTION shifts between conditions.
Key tools:

  Centroid shift:   Δ = centroid_B - centroid_A
                    Nearest records to Δ = "what semantically changed"
  MMD test:         Maximum Mean Discrepancy — non-parametric test of whether
                    two embedding distributions are the same
  UMAP overlay:     Plot all conditions in one 2-D space, coloured by condition
                    to visually confirm or deny separation

ANSWERS
-------
  Q1  centroid shift Rep → RW on list_products:
        → nearest records to shift direction = explicit warrant reasoning
  Q3  centroid shift Rep → RW: decompose which semantic axes change most
  Q4  3-way comparison rw_wo / rw_wsc / rw_both on list_products:
        → does MMD(rw_wsc, rw_wo) > MMD(rw_wo, rw_wo_baseline)?
        → if yes: communication changes listing reasoning
  Q5  centroid shift Rep → RW on create_post:
        → direction of shift = priority change in communication

PLANNED CLI
-----------
    python compare_conditions.py <exp_dir_A> <exp_dir_B> [<exp_dir_C> ...]
        --labels RepOnly RW_NoComm RW_BothComm   # human-readable condition names
        --action-types list_products              # filter (required)
        --runs all|1|2|...
        --mmd                                     # run MMD test
        --centroid-shift                          # compute & report centroid shift
        --n-nearest 10                            # records nearest to shift vector
        --output-dir <dir>

OUTPUT
------
    umap_overlay.png                 # all conditions in shared UMAP space
    centroid_shift_report.txt        # shift vector analysis + nearest records
    mmd_results.json                 # MMD scores and p-values for all pairs
    condition_comparison.csv         # per-record embeddings with condition labels

TODO
----
Implement after keyword_filter_analysis.py confirms which conditions show
meaningful behavioural differences, to focus the comparison effort.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ConditionEmbeddings:
    label: str
    embeddings: np.ndarray     # (n_records, dim)
    record_meta: list[dict]    # round, agent_name, action_name per record
    centroid: Optional[np.ndarray] = None

    def __post_init__(self):
        self.centroid = self.embeddings.mean(axis=0)


# ── Core functions (TODO) ─────────────────────────────────────────────────────

def load_condition_embeddings(
    exp_dir: str,
    label: str,
    action_types: list[str] | None,
    runs: str,
    model_name: str,
) -> ConditionEmbeddings:
    """Load records, filter, embed, and return ConditionEmbeddings."""
    raise NotImplementedError("TODO")


def compute_mmd(X: np.ndarray, Y: np.ndarray, kernel: str = "rbf") -> float:
    """
    Maximum Mean Discrepancy between two embedding sets.
    Uses RBF kernel with bandwidth set by median heuristic.
    Returns scalar MMD² value; positive = distributions differ.
    """
    raise NotImplementedError("TODO")


def permutation_mmd_pvalue(
    X: np.ndarray, Y: np.ndarray, n_permutations: int = 500
) -> tuple[float, float]:
    """Return (mmd_score, p_value) via permutation test."""
    raise NotImplementedError("TODO")


def centroid_shift_analysis(
    cond_a: ConditionEmbeddings,
    cond_b: ConditionEmbeddings,
    all_records_embeddings: np.ndarray,
    all_records_meta: list[dict],
    n_nearest: int = 10,
) -> dict:
    """
    Compute shift vector Δ = centroid_B - centroid_A.
    Project all records onto Δ and return the top-n nearest records.
    These records represent what semantically changed between conditions.
    """
    raise NotImplementedError("TODO")


def plot_umap_overlay(
    conditions: list[ConditionEmbeddings], output_path: str
) -> None:
    """UMAP in shared space, coloured by condition label."""
    raise NotImplementedError("TODO")


def generate_comparison_report(
    conditions: list[ConditionEmbeddings],
    mmd_results: dict,
    shift_analyses: dict,
    output_dir: Path,
) -> None:
    """Write centroid_shift_report.txt and mmd_results.json."""
    raise NotImplementedError("TODO")


# ── CLI skeleton ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-condition embedding comparison of action_reasoning.")
    parser.add_argument("exp_dirs", nargs="+",
                        help="Two or more experiment directories to compare")
    parser.add_argument("--labels", nargs="+", default=None,
                        help="Human-readable labels for each condition (same order)")
    parser.add_argument("--action-types", nargs="+", required=True,
                        help="Restrict to these action_name values (required)")
    parser.add_argument("--runs", default="all")
    parser.add_argument("--mmd", action="store_true",
                        help="Run MMD permutation test for each condition pair")
    parser.add_argument("--centroid-shift", action="store_true",
                        help="Compute centroid shift and nearest records")
    parser.add_argument("--n-nearest", type=int, default=10,
                        help="Records nearest to centroid shift vector")
    parser.add_argument("--model", default="all-MiniLM-L6-v2")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    raise NotImplementedError("compare_conditions.py is not yet implemented — see TODO above")


if __name__ == "__main__":
    main()
