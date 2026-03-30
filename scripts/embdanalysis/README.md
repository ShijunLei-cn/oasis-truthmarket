# TruthMarketTwin Embedding Analysis Toolkit

Tools for interpretability analysis of `action_reasoning` fields in TruthMarketTwin experiment logs.
Three complementary approaches answer the 6 reviewer questions in `experiments/explanation/Questions.md`.

---

## Overview

```
scripts/embdanalysis/
├── analyze.py                   # General embedding analysis (UMAP, KMeans, metrics)
├── case_embedding_analysis.sh   # Batch runner across all experiment conditions
├── probe_analysis.py            # Approach 1: Probe direction analysis  [STUB]
├── compare_conditions.py        # Approach 2: Cross-condition comparison  [STUB]
├── keyword_filter_analysis.py   # Approach 3: Keyword/snippet filtering  [IMPLEMENTED]
└── restructure4web.py           # Web output restructuring utility
```

---

## Approach 1 — Probe Direction Analysis (`probe_analysis.py`)

**Core idea:** Embed "probe" reference texts that represent specific stances (e.g. "I will advertise HQ but deliver LQ"). Score every `action_reasoning` record by cosine similarity to each probe. The scalar score is continuous and can be tracked over rounds.

**Best for:** Q1, Q2, Q5, Q6
**Output:** `probe_scores.csv`, KDE plots per condition, per-agent trajectory plots, tipping point JSON

**Status:** Stub — implement after keyword analysis validates which conditions show meaningful differences.

---

## Approach 2 — Cross-Condition Comparison (`compare_conditions.py`)

**Core idea:** Embed all records from two or more conditions in a shared space. Measure how the embedding *distribution* shifts: centroid shift vector, MMD test, UMAP overlay coloured by condition.

**Best for:** Q3, Q4, Q5
**Output:** `umap_overlay.png`, `centroid_shift_report.txt`, `mmd_results.json`, `condition_comparison.csv`

**Status:** Stub — implement after keyword analysis.

---

## Approach 3 — Keyword / Snippet Filter Analysis (`keyword_filter_analysis.py`)

**Core idea:** Three-layer pipeline:
1. **Layer 1** — Fast keyword/regex filter → exact match statistics and sample quotes
2. **Layer 2** (`--expand N`) — Use Layer-1 matches as seeds; retrieve N nearest neighbours from embedding space to capture paraphrases
3. **Layer 3** (`--cluster`) — KMeans on the filtered set to discover sub-themes

**Best for:** Q1, Q2, Q3 (high-recall domain vocabulary); complement Q5/Q6 with Approach 1.

**Status:** Fully implemented.

### Built-in presets

| Preset | Question | Recommended action type |
|---|---|---|
| `q1_deception` | Deception reduction mechanism | `list_products` |
| `q2_rep_vs_stakes` | Rep vs stakes perceived value | `list_products` |
| `q3_stakes_changes` | Reasoning changes from stakes | `list_products` |
| `q4_comm_staking` | Communication → staking behavior | `list_products` |
| `q5_comm_priorities` | Communication priority shift | `create_post` |
| `q6_brand_vs_profit` | Brand vs profit conditions | `list_products` |

### Quick start

```bash
# Q1: Compare Rep vs Rep+Warrant on listing deception
python keyword_filter_analysis.py \
    experiments/gpt-4o-mini/paper/rq1/r_wo \
    experiments/gpt-4o-mini/paper/rq1/rw_wo \
    --preset q1_deception --action-types list_products \
    --labels RepOnly RW_NoComm --samples 5

# Q3: Stakes-induced reasoning changes with embedding expansion + clustering
python keyword_filter_analysis.py \
    experiments/gpt-4o-mini/paper/rq1/r_wo \
    experiments/gpt-4o-mini/paper/rq1/rw_wo \
    --preset q3_stakes_changes --action-types list_products \
    --expand 5 --cluster --n-clusters 4

# Custom keyword set
python keyword_filter_analysis.py <exp_dir1> <exp_dir2> \
    --keyword-set my_keywords.json --action-types list_products
```

### Output files
- `keyword_filter_report.txt` — human-readable stats + sample quotes per group
- `keyword_filter_results.json` — machine-readable full results
- `match_rates.csv` — per-condition × per-group match rates with significance markers
- `expanded/` — Layer-2 embedding expansion results (if `--expand`)
- `clusters/` — Layer-3 cluster analysis (if `--cluster`)

---

## General Embedding Analysis (`analyze.py`)

Standalone per-condition embedding analysis: UMAP/t-SNE/PCA dimensionality reduction,
KMeans clustering, cluster quality metrics (Silhouette, Davies-Bouldin, Calinski-Harabasz),
centroid distance heatmaps, silhouette bar charts.

```bash
# Analyse a single condition, list_products only
python analyze.py experiments/gpt-4o-mini/paper/rq1/rw_wo \
    --action-types list_products --n-clusters 8

# Batch run across all RQ/conditions
bash case_embedding_analysis.sh --action-types list_products --clusters 8
```

Key finding from initial analysis: **mixing action types produces uninformative clusters** (clusters
rediscover action type boundaries, not strategic patterns). Always use `--action-types` to restrict
to a single action type for meaningful semantic clustering.

---

## Question → Method Mapping

| Question | Primary approach | Secondary |
|---|---|---|
| Q1: Deception mechanism | Approach 3 (`q1_deception`) | Approach 1 (`q1_deception` probe) |
| Q2: Rep vs stakes value | Approach 3 (`q2_rep_vs_stakes`) | Approach 2 centroid shift |
| Q3: Stakes-induced reasoning | Approach 3 (`q3_stakes_changes`) | Approach 2 centroid shift |
| Q4: Comm → staking | Behavioral stats (warrant rates) + Approach 3 (`q4_comm_staking`) | Approach 2 MMD |
| Q5: Comm priority shift | Approach 1 (`q5_comm_priorities` probe) | Approach 3 (`q5_comm_priorities`) |
| Q6: Brand vs profit | Approach 1 temporal trajectory (`q6_brand_vs_profit`) | Approach 3 (`q6_brand_vs_profit`) |
