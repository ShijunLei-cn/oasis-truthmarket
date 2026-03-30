"""
Probe Direction Analysis of action_reasoning embeddings.
Approach 1 of 3 in the TruthMarketTwin interpretability toolkit.

APPROACH SUMMARY
----------------
Create "probe" reference texts that represent specific behaviours or stances
(e.g. "deceptive listing", "warrant as quality signal").  Embed every
action_reasoning record and compute its cosine similarity to each probe
direction.  This yields a continuous scalar score per record that can be:
  - Plotted as KDE distributions, comparing conditions
  - Tracked as a time-series per agent across rounds (trajectory)
  - Used to find "tipping points" where an agent's stance shifts

ANSWERS
-------
  Q1  Deception mechanism: probe "list LQ as HQ" vs "warrant proves HQ"
  Q2  Rep vs stakes value: probe "reputation sufficient" vs "stake needed"
  Q5  Communication priorities: probe "quality/trust focus" vs "profit focus"
  Q6  Brand vs profit: probe "long-term brand" vs "short-term profit max"
      → temporal: plot brand_score - profit_score per agent per round
      → tipping point = round where curve crosses zero

PLANNED CLI
-----------
    python probe_analysis.py <exp_dir> [<exp_dir2> ...]
        --probes <probes.json>        # JSON list of {name, text} objects
        --preset  q1|q2|q5|q6        # built-in probe sets for each question
        --action-types list_products  # filter (default: all)
        --runs all|1|2|...            # which runs to include
        --output-dir <dir>

OUTPUT
------
    probe_scores.csv                  # every record × every probe score
    kde_<probe_name>.png              # KDE per condition for each probe
    trajectory_<agent>_<probe>.png    # per-agent probe score over rounds
    tipping_points.json               # round/conditions where score crosses 0
    probe_report.txt                  # human-readable summary

TODO
----
Implement after keyword_filter_analysis.py is validated and Questions.md
answers have been drafted.  Probe texts should be informed by the actual
language found via keyword filtering.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


# ── Probe set presets ─────────────────────────────────────────────────────────

PROBE_PRESETS: dict[str, list[dict]] = {
    "q1_deception": [
        {"name": "deceptive_listing",
         "text": "I will advertise this as high quality but actually deliver low quality to maximize profit"},
        {"name": "honest_warrant",
         "text": "I attach a warranty because it proves my product is genuinely high quality"},
    ],
    "q2_rep_vs_stakes": [
        {"name": "reputation_sufficient",
         "text": "My reputation and past ratings are enough to signal quality to buyers"},
        {"name": "stake_needed",
         "text": "I need to use a warrant with escrow to credibly signal quality beyond reputation"},
    ],
    "q5_comm_priorities": [
        {"name": "quality_trust_focus",
         "text": "I communicate to build long-term trust through honest quality signaling"},
        {"name": "profit_sales_focus",
         "text": "I communicate to maximize sales volume and short-term revenue"},
    ],
    "q6_brand_vs_profit": [
        {"name": "brand_building",
         "text": "I prioritize building a sustainable brand and long-term reputation over immediate profit"},
        {"name": "profit_maximizing",
         "text": "I maximize short-term profit even if it damages my reputation"},
    ],
}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ProbeSpec:
    name: str
    text: str
    embedding: Optional[np.ndarray] = None


# ── Core functions (TODO) ─────────────────────────────────────────────────────

def load_probe_specs(source: str | list[dict]) -> list[ProbeSpec]:
    """Load probe specs from a preset name, JSON file path, or list of dicts."""
    raise NotImplementedError("TODO")


def embed_probes(probes: list[ProbeSpec], model_name: str = "all-MiniLM-L6-v2") -> list[ProbeSpec]:
    """Embed each probe text using sentence-transformers."""
    raise NotImplementedError("TODO")


def compute_probe_scores(
    embeddings: np.ndarray,        # (n_records, dim)
    probe_embeddings: np.ndarray,  # (n_probes, dim)
) -> np.ndarray:
    """
    Return cosine similarity matrix of shape (n_records, n_probes).
    Each value is the cosine similarity of a record to a probe direction.
    """
    raise NotImplementedError("TODO")


def plot_kde_comparison(scores_per_condition: dict[str, np.ndarray],
                         probe_name: str, output_path: str) -> None:
    """KDE distribution of probe scores, one curve per condition."""
    raise NotImplementedError("TODO")


def plot_agent_trajectory(scores_by_round: dict[int, float],
                           agent_name: str, probe_name: str,
                           output_path: str) -> None:
    """Per-agent probe score over rounds; marks tipping point if score crosses 0."""
    raise NotImplementedError("TODO")


def find_tipping_points(
    agent_trajectories: dict[str, dict[int, float]]
) -> list[dict]:
    """Return list of {agent, round} where brand_score - profit_score crosses zero."""
    raise NotImplementedError("TODO")


# ── CLI skeleton ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe direction analysis of action_reasoning embeddings.")
    parser.add_argument("exp_dirs", nargs="+",
                        help="One or more experiment directories to analyse")
    parser.add_argument("--probes", default=None,
                        help="JSON file with list of {name, text} probe specs")
    parser.add_argument("--preset", default=None,
                        choices=list(PROBE_PRESETS),
                        help="Built-in probe set for a specific question")
    parser.add_argument("--action-types", nargs="+", default=None,
                        help="Restrict to these action_name values")
    parser.add_argument("--runs", default="all",
                        help="Run filter: all | 1 | 2 | ...")
    parser.add_argument("--model", default="all-MiniLM-L6-v2")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    raise NotImplementedError("probe_analysis.py is not yet implemented — see TODO above")


if __name__ == "__main__":
    main()
