#!/bin/bash
# Embedding analysis of action_reasoning for all (or selected) experiment conditions.
#
# Usage:
#   bash scripts/case_embedding_analysis.sh [options]
#
# Options (all optional — defaults are shown):
#   --rq           RQ filter:        all | rq1 | rq2 | rq3        (default: all)
#   --condition    Condition filter:  all | <exact dir name>        (default: all)
#   --run          Run filter:        all | 1 | 2 | ... | 5        (default: all)
#   --methods      Reduction methods: pca tsne umap (space-sep)    (default: umap)
#   --clusters     Number of clusters (0 = auto via silhouette)    (default: 0)
#   --action-types Restrict to action type(s) (space-sep)          (default: all)
#                  Pass "list" to print available types for first matching file.
#   --skip         Skip if embd_analysis/ already exists           (default: false)
#   --dry-run      Print commands without executing                 (default: false)
#
# Examples:
#   # Quick check — RQ1 only, run_1, UMAP
#   bash scripts/case_embedding_analysis.sh --rq rq1 --run 1
#
#   # Only analyse listing decisions (seller strategy)
#   bash scripts/case_embedding_analysis.sh --action-types "list_products"
#
#   # Seller listing + communication together
#   bash scripts/case_embedding_analysis.sh --action-types "list_products create_post"
#
#   # Print available action types for a condition and exit
#   bash scripts/case_embedding_analysis.sh --condition r_wsc_R_pressure_quickprofits --run 1 --action-types list --dry-run
#
#   # All RQ2 conditions, all runs, all methods, skip already done
#   bash scripts/case_embedding_analysis.sh --rq rq2 --methods "pca tsne umap" --skip
#
#   # Full run (100 jobs), umap only, skip existing
#   bash scripts/case_embedding_analysis.sh --skip

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
MODEL_TYPE="${MODEL_TYPE:-gpt-4o-mini}"
BASE_DIR="experiments/${MODEL_TYPE}/paper"
ANALYZE_SCRIPT="scripts/embdanalysis/analyze.py"
CONDA_ENV="oasismarket"

RQ_FILTER="all"
CONDITION_FILTER="all"
RUN_FILTER="all"
METHODS="umap"
N_CLUSTERS=0
ACTION_TYPES=""
SKIP_EXISTING=false
DRY_RUN=false

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --rq)           RQ_FILTER="$2";        shift 2 ;;
        --condition)    CONDITION_FILTER="$2"; shift 2 ;;
        --run)          RUN_FILTER="$2";       shift 2 ;;
        --methods)      METHODS="$2";          shift 2 ;;
        --clusters)     N_CLUSTERS="$2";       shift 2 ;;
        --action-types) ACTION_TYPES="$2";     shift 2 ;;
        --skip)         SKIP_EXISTING=true;    shift   ;;
        --dry-run)      DRY_RUN=true;          shift   ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Derived args for analyze.py ───────────────────────────────────────────────
METHODS_ARG="--methods ${METHODS}"
CLUSTERS_ARG=""
[[ $N_CLUSTERS -gt 0 ]] && CLUSTERS_ARG="--n-clusters ${N_CLUSTERS}"
ACTION_TYPES_ARG=""
[[ -n "$ACTION_TYPES" ]] && ACTION_TYPES_ARG="--action-types ${ACTION_TYPES}"

# ── Build list of RQ directories to scan ─────────────────────────────────────
if [[ "$RQ_FILTER" == "all" ]]; then
    RQ_DIRS=("${BASE_DIR}/rq1" "${BASE_DIR}/rq2" "${BASE_DIR}/rq3")
else
    RQ_DIRS=("${BASE_DIR}/${RQ_FILTER}")
fi

# ── Counters ─────────────────────────────────────────────────────────────────
total=0
skipped=0
failed=0
done_count=0

echo "=========================================================================="
echo "  Embedding Analysis — TruthMarketTwin"
echo "=========================================================================="
echo "  Model:      ${MODEL_TYPE}"
echo "  RQ filter:  ${RQ_FILTER}"
echo "  Condition:  ${CONDITION_FILTER}"
echo "  Run:        ${RUN_FILTER}"
echo "  Methods:    ${METHODS}"
echo "  Clusters:   $([ $N_CLUSTERS -eq 0 ] && echo 'auto' || echo $N_CLUSTERS)"
echo "  Act.types:  $([ -z "$ACTION_TYPES" ] && echo 'all' || echo "$ACTION_TYPES")"
echo "  Skip exist: ${SKIP_EXISTING}"
echo "  Dry run:    ${DRY_RUN}"
echo "=========================================================================="

# ── Main loop ─────────────────────────────────────────────────────────────────
for rq_dir in "${RQ_DIRS[@]}"; do
    [[ -d "$rq_dir" ]] || { echo "SKIP: directory not found — $rq_dir"; continue; }

    for condition_dir in "${rq_dir}"/*/; do
        [[ -d "$condition_dir" ]] || continue
        condition_name=$(basename "$condition_dir")

        # Condition filter
        if [[ "$CONDITION_FILTER" != "all" && "$condition_name" != "$CONDITION_FILTER" ]]; then
            continue
        fi

        # Collect action JSON files for this condition
        for actions_file in "${condition_dir}"run_*_actions.json; do
            [[ -f "$actions_file" ]] || continue

            # Run filter
            run_num=$(basename "$actions_file" | grep -oP '(?<=run_)\d+')
            if [[ "$RUN_FILTER" != "all" && "$run_num" != "$RUN_FILTER" ]]; then
                continue
            fi

            total=$((total + 1))
            out_dir="${condition_dir}embd_analysis"

            # Skip-existing check
            if $SKIP_EXISTING && [[ -f "${out_dir}/cluster_metrics.json" ]]; then
                echo "[SKIP] ${condition_name}/run_${run_num} — embd_analysis already exists"
                skipped=$((skipped + 1))
                continue
            fi

            echo ""
            echo "── [$(date +%H:%M:%S)] ${condition_name} / run_${run_num} ──────────────────────"

            # When filtering by action type, append a subdir so analyses stay separate
            if [[ -n "$ACTION_TYPES" ]]; then
                type_suffix=$(echo "$ACTION_TYPES" | tr ' ' '+')
                run_out_dir="${out_dir}/run_${run_num}/${type_suffix}"
            else
                run_out_dir="${out_dir}/run_${run_num}"
            fi

            cmd="conda run -n ${CONDA_ENV} python ${ANALYZE_SCRIPT} \
                ${actions_file} \
                ${METHODS_ARG} \
                ${CLUSTERS_ARG} \
                ${ACTION_TYPES_ARG} \
                --output-dir ${run_out_dir}"

            if $DRY_RUN; then
                echo "[DRY-RUN] $cmd"
            else
                if eval "$cmd"; then
                    done_count=$((done_count + 1))
                else
                    echo "[ERROR] Failed: ${actions_file}"
                    failed=$((failed + 1))
                fi
            fi
        done
    done
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=========================================================================="
echo "  Done."
echo "  Total jobs : ${total}"
echo "  Completed  : ${done_count}"
echo "  Skipped    : ${skipped}"
echo "  Failed     : ${failed}"
echo "=========================================================================="

[[ $failed -gt 0 ]] && exit 1 || exit 0
