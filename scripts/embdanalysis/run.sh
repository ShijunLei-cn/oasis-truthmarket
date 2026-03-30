#!/usr/bin/env bash
# =============================================================================
# TruthMarketTwin — Embedding Analysis Runner
# =============================================================================
# Usage: bash scripts/embdanalysis/run.sh
# Run individual sections by copying the commands directly.
#
# Three approaches:
#   Approach 1  probe_analysis.py      — cosine similarity to probe texts  [STUB]
#   Approach 2  compare_conditions.py  — MMD + centroid shift               [STUB]
#   Approach 3  keyword_filter_analysis.py — keyword/regex filter           [DONE]
#
# See scripts/embdanalysis/README.md for full documentation.
# =============================================================================

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PYTHON="conda run -n oasismarket python"
SCRIPTS="scripts/embdanalysis"
BASE="experiments/gpt-4o-mini/paper"

# Shorthand paths
RQ1="$BASE/rq1"
RQ2="$BASE/rq2"
RQ3="$BASE/rq3"

# ─── Approach 3: Keyword / Snippet Filter Analysis ────────────────────────────
#
# Each block corresponds to one reviewer question.
# Outputs land in <first_exp_dir>/keyword_analysis/<preset>/
# ----------------------------------------------------------------------------- #

# Q1: What is the mechanism through which the stakes market reduces deception?
#     Condition pair: Rep-only vs Rep+Warrant (no sycophancy)
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/r_wo \
    $RQ1/rw_wo \
    --preset q1_deception \
    --action-types list_products \
    --labels RepOnly RW_NoComm \
    --samples 5

# Q1 extended: also check with the full RQ3 conditions (both Rep and RW with pqp)
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ3/r_both_R_pqp \
    $RQ3/rw_both_R_pqp \
    --preset q1_deception \
    --action-types list_products \
    --labels Rep_PQP RW_PQP \
    --samples 5

# Q2: How do agents perceive the relative value of reputation vs financial stakes?
#     Single RW condition — look at internal reasoning about warrant vs reputation
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/rw_wo \
    --preset q2_rep_vs_stakes \
    --action-types list_products \
    --labels RW_NoComm \
    --samples 5

# Q2 extended: compare Rep-only vs RW to see if stakes-absent agents mention rep more
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/r_wo \
    $RQ1/rw_wo \
    --preset q2_rep_vs_stakes \
    --action-types list_products \
    --labels RepOnly RW_NoComm \
    --samples 5

# Q3: How do financial stakes change agent reasoning about product quality decisions?
#     Rep vs RW — Layer 1 only (fast)
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/r_wo \
    $RQ1/rw_wo \
    --preset q3_stakes_changes \
    --action-types list_products \
    --labels RepOnly RW_NoComm \
    --samples 5

# Q3 extended: Layer 2+3 — embedding expansion + clustering (slow, run separately)
# $PYTHON $SCRIPTS/keyword_filter_analysis.py \
#     $RQ1/r_wo \
#     $RQ1/rw_wo \
#     --preset q3_stakes_changes \
#     --action-types list_products \
#     --labels RepOnly RW_NoComm \
#     --samples 5 \
#     --expand 5 --cluster --n-clusters 4

# Q4: Does communication capability combined with staking affect listing decisions?
#     Three-way: RW no-comm  vs  RW+sycophancy(R)  vs  RW+both
#     (R = resistant / policy_making is a natural comparison)
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/rw_wo \
    $RQ2/rw_wsc_R_policy_making \
    $RQ3/rw_both_R_pqp \
    --preset q4_comm_staking \
    --action-types list_products \
    --labels RW_NoComm RW_Comm_R RW_Both_R \
    --samples 5

# Q4 — pressure variant for comparison
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/rw_wo \
    $RQ2/rw_wsc_R_pressure_quickprofits \
    $RQ3/rw_both_R_pqp \
    --preset q4_comm_staking \
    --action-types list_products \
    --labels RW_NoComm RW_Comm_pressure RW_Both_R \
    --samples 5

# Q5: Do communication capabilities shift agents' priorities in their posts?
#     Rep+sycophancy vs RW+sycophancy on create_post action
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ2/r_wsc_R_policy_making \
    $RQ2/rw_wsc_R_policy_making \
    --preset q5_comm_priorities \
    --action-types create_post \
    --labels Rep_Comm_R RW_Comm_R \
    --samples 5

# Q5 — psychological attack variant
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ2/r_wsc_R_psychological-based-attack \
    $RQ2/rw_wsc_R_psychological-based-attack \
    --preset q5_comm_priorities \
    --action-types create_post \
    --labels Rep_PsyAtk RW_PsyAtk \
    --samples 5

# Q6: Do conditions differ in agents' brand-building vs short-term profit reasoning?
#     All four baseline/extended conditions side by side
$PYTHON $SCRIPTS/keyword_filter_analysis.py \
    $RQ1/r_wo \
    $RQ1/rw_wo \
    $RQ3/r_both_R_pqp \
    $RQ3/rw_both_R_pqp \
    --preset q6_brand_vs_profit \
    --action-types list_products \
    --labels RepOnly RW_NoComm Rep_Both RW_Both \
    --samples 5

# ─── Approach 2: Cross-Condition Comparison ─────────────────────────────────
# [STUB — implement compare_conditions.py first]
#
# Q1/Q3 centroid shift: Rep → RW on list_products
# $PYTHON $SCRIPTS/compare_conditions.py \
#     $RQ1/r_wo \
#     $RQ1/rw_wo \
#     --labels RepOnly RW_NoComm \
#     --action-types list_products \
#     --centroid-shift --n-nearest 10 --mmd
#
# Q4 three-way MMD: does communication change listing distribution?
# $PYTHON $SCRIPTS/compare_conditions.py \
#     $RQ1/rw_wo \
#     $RQ2/rw_wsc_R_policy_making \
#     $RQ3/rw_both_R_pqp \
#     --labels RW_NoComm RW_Comm_R RW_Both_R \
#     --action-types list_products \
#     --mmd --centroid-shift
#
# Q5 centroid shift on create_post
# $PYTHON $SCRIPTS/compare_conditions.py \
#     $RQ2/r_wsc_R_policy_making \
#     $RQ2/rw_wsc_R_policy_making \
#     --labels Rep_Comm_R RW_Comm_R \
#     --action-types create_post \
#     --centroid-shift --n-nearest 10

# ─── Approach 1: Probe Direction Analysis ────────────────────────────────────
# [STUB — implement probe_analysis.py first]
#
# Q1 probe: deceptive listing direction vs warrant-honest direction
# $PYTHON $SCRIPTS/probe_analysis.py \
#     $RQ1/r_wo \
#     $RQ1/rw_wo \
#     --preset q1_deception \
#     --action-types list_products \
#     --labels RepOnly RW_NoComm
#
# Q5 probe: profit-focus direction vs quality/trust-focus direction on create_post
# $PYTHON $SCRIPTS/probe_analysis.py \
#     $RQ2/r_wsc_R_policy_making \
#     $RQ2/rw_wsc_R_policy_making \
#     --preset q5_comm_priorities \
#     --action-types create_post \
#     --labels Rep_Comm_R RW_Comm_R
#
# Q6 probe: temporal trajectory of brand_score - profit_score per agent
# $PYTHON $SCRIPTS/probe_analysis.py \
#     $RQ1/r_wo \
#     $RQ1/rw_wo \
#     --preset q6_brand_vs_profit \
#     --action-types list_products \
#     --labels RepOnly RW_NoComm

# ─── General Embedding Analysis (analyze.py) ─────────────────────────────────
# Per-condition UMAP + KMeans + cluster quality metrics
#
# Single condition, list_products only
# $PYTHON $SCRIPTS/analyze.py \
#     $RQ1/rw_wo \
#     --action-types list_products --n-clusters 8
#
# Batch all conditions via shell script
# bash $SCRIPTS/case_embedding_analysis.sh \
#     --action-types list_products --clusters 8
