"""
Keyword/snippet-based filtering analysis of action_reasoning records.
Approach 3 of 3 in the TruthMarketTwin interpretability toolkit.

THREE-LAYER DESIGN
------------------
  Layer 1 (this script) — Keyword/regex filter
      Fast, precise seed selection. Produces exact match statistics,
      cross-condition comparisons, and sample quotes per group.

  Layer 2 (--expand N) — Embedding nearest-neighbour expansion
      Use Layer-1 matched records as seeds; retrieve N nearest neighbours
      from the embedding space to capture paraphrases the keywords missed.
      Boosts recall while preserving semantic relevance.

  Layer 3 (--cluster) — Cluster the filtered set
      Run KMeans on the final (possibly expanded) set to discover
      sub-themes within each keyword group.

QUESTION → PRESET MAPPING
--------------------------
  --preset q1_deception        list_products  Rep vs RW
  --preset q2_rep_vs_stakes    list_products  RW condition only
  --preset q3_stakes_changes   list_products  Rep vs RW
  --preset q4_comm_staking     list_products  rw_wo vs rw_wsc vs rw_both
  --preset q5_comm_priorities  create_post    Rep vs RW
  --preset q6_brand_vs_profit  list_products  temporal, any condition

USAGE
-----
    # Compare Rep vs RW on listing deception patterns
    python keyword_filter_analysis.py \\
        experiments/gpt-4o-mini/paper/rq1/r_wo \\
        experiments/gpt-4o-mini/paper/rq1/rw_wo \\
        --preset q1_deception --action-types list_products

    # Custom keyword set from file
    python keyword_filter_analysis.py <exp_dir> \\
        --keyword-set my_keywords.json --action-types list_products

    # Expand with embeddings + cluster the filtered set
    python keyword_filter_analysis.py <exp_dir1> <exp_dir2> \\
        --preset q3_stakes_changes --action-types list_products \\
        --expand 5 --cluster

OUTPUT
------
    keyword_filter_report.txt    human-readable report with stats + samples
    keyword_filter_results.json  machine-readable full results
    match_rates.csv              per-condition × per-group match rates
    [expanded/]                  Layer-2 embedding expansion results (if --expand)
    [clusters/]                  Layer-3 cluster analysis (if --cluster)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


# ── Built-in keyword set presets ──────────────────────────────────────────────
# Pattern syntax:
#   Plain string  → case-insensitive substring match
#   "regex:..."   → re.search (case-insensitive)
# Group logic:
#   "any" (default) → record matches if ANY pattern fires  (OR)
#   "all"           → record matches only if ALL patterns fire (AND)
# cooccurrence:
#   List of [group_A, group_B] pairs; reports records matching BOTH groups.

PRESETS: dict[str, dict] = {

    "q1_deception": {
        "question": "Q1: What is the mechanism through which the stakes market reduces deception?",
        "recommended_action_types": ["list_products"],
        "groups": {
            "lq_listing": {
                "description": "Agent explicitly decides to list LQ products",
                "patterns": ["LQ product", "low-quality product", "low quality product",
                             "list LQ", "listing LQ", "sell LQ", "selling LQ"],
                "logic": "any",
            },
            "dishonest_advertising": {
                "description": "Agent reasons about advertising HQ while delivering LQ",
                "patterns": ["regex:advertis.*HQ.*LQ", "regex:LQ.*advertis.*HQ",
                             "regex:list.*as HQ.*true.*LQ", "regex:claim.*high.*quality.*low",
                             "misrepresent", "false.*quality", "mislabel",
                             "regex:HQ.*but.*actually.*LQ", "regex:present.*as.*high"],
                "logic": "any",
            },
            "warrant_honest_signal": {
                "description": "Agent uses warrant as a credible quality signal",
                "patterns": ["warrant", "escrow", "stake", "guarantee.*quality",
                             "prove.*genuine", "back.*claim"],
                "logic": "any",
            },
            "reputation_deception_risk": {
                "description": "Agent weighs deception risk against reputation cost",
                "patterns": ["reputation.*deceiv", "rating.*fraud", "caught.*dishonest",
                             "negative.*feedback.*quality", "reputation.*risk",
                             "regex:deceiv.*reputation", "regex:risk.*rating"],
                "logic": "any",
            },
        },
        "cooccurrence": [
            ["dishonest_advertising", "reputation_deception_risk"],
        ],
    },

    "q2_rep_vs_stakes": {
        "question": "Q2: What is the perceived value of reputation signaling versus using stakes?",
        "recommended_action_types": ["list_products"],
        "groups": {
            "reputation_as_signal": {
                "description": "Using reputation/ratings as the primary credibility mechanism",
                "patterns": ["reputation", "rating", "thumbs", "track record",
                             "trust.*buyer", "feedback", "standing", "reviews"],
                "logic": "any",
            },
            "stake_as_signal": {
                "description": "Using warrant/stake as a credibility mechanism",
                "patterns": ["warrant", "stake", "escrow", "credibility.*signal",
                             "back.*claim", "guarantee", "pledge"],
                "logic": "any",
            },
            "explicit_comparison": {
                "description": "Explicit comparison or trade-off between reputation and stakes",
                "patterns": ["regex:reputation.*warrant", "regex:warrant.*reputation",
                             "instead of.*warrant", "beyond.*reputation",
                             "signal.*quality.*without warrant",
                             "regex:stake.*vs.*reputation"],
                "logic": "any",
            },
        },
        "cooccurrence": [
            ["reputation_as_signal", "stake_as_signal"],
        ],
    },

    "q3_stakes_changes": {
        "question": "Q3: What changes in agentic reasoning are induced by the introduction of stakes?",
        "recommended_action_types": ["list_products"],
        "groups": {
            "stake_decision_attach": {
                "description": "Agent actively decides to attach a warrant",
                "patterns": ["regex:will.*warrant", "regex:attach.*warrant",
                             "regex:use.*warrant", "regex:provide.*warrant",
                             "regex:offer.*warrant", "regex:include.*warrant",
                             "regex:apply.*stake", "with warrant"],
                "logic": "any",
            },
            "stake_decision_skip": {
                "description": "Agent actively decides NOT to attach a warrant",
                "patterns": ["regex:not.*warrant", "regex:without.*warrant",
                             "regex:no.*warrant", "regex:skip.*warrant",
                             "regex:avoid.*warrant", "regex:forgo.*warrant",
                             "regex:decline.*warrant"],
                "logic": "any",
            },
            "stake_cost_reasoning": {
                "description": "Agent reasons about the economic cost or risk of staking",
                "patterns": ["escrow cost", "cost of warrant", "challenge cost",
                             "risk.*challenge", "penalty", "lose.*escrow",
                             "regex:cost.*stake", "regex:risky.*warrant",
                             "regime.*challenge"],
                "logic": "any",
            },
            "stake_quality_criterion": {
                "description": "Agent uses product quality as the criterion for staking",
                "patterns": ["regex:quality.*warrant", "regex:warrant.*quality",
                             "regex:HQ.*warrant", "regex:warrant.*HQ",
                             "regex:confident.*warrant", "regex:genuine.*stake",
                             "safe to warrant", "worth warranting"],
                "logic": "any",
            },
        },
        "cooccurrence": [
            ["stake_decision_attach", "stake_quality_criterion"],
            ["stake_decision_skip", "stake_cost_reasoning"],
        ],
    },

    "q4_comm_staking": {
        "question": "Q4: Does the ability to communicate change agents' use of staking as a credibility signal?",
        "recommended_action_types": ["list_products"],
        "groups": {
            "listing_references_comm": {
                "description": "Listing reasoning that references communication or other sellers",
                "patterns": ["others said", "sellers discussed", "from the post",
                             "based on.*communication", "shared strategy",
                             "regex:heard.*from.*seller", "regex:post.*mention",
                             "regex:discussion.*warrant"],
                "logic": "any",
            },
            "warrant_with_comm_context": {
                "description": "Warrant decision made in context of what others communicated",
                "patterns": ["regex:others.*warrant", "regex:sellers.*stake",
                             "regex:shared.*warrant", "regex:heard.*warrant",
                             "regex:post.*stake", "regex:communicated.*warrant"],
                "logic": "any",
            },
        },
        "cooccurrence": [],
    },

    "q5_comm_priorities": {
        "question": "Q5: Does communication in the stakes market focus on different priorities?",
        "recommended_action_types": ["create_post"],
        "groups": {
            "quality_trust_focus": {
                "description": "Communication focused on quality, honesty, and long-term trust",
                "patterns": ["quality", "honest", "authentic", "genuine", "integrity",
                             "trustworthy", "reliable", "long-term", "sustainable"],
                "logic": "any",
            },
            "profit_sales_focus": {
                "description": "Communication focused on profit, revenue, and sales targets",
                "patterns": ["profit", "revenue", "maximize", "sales", "short-term",
                             "quick", "earnings", "target", "volume"],
                "logic": "any",
            },
            "deception_coordination": {
                "description": "Communication that promotes or coordinates deceptive strategies",
                "patterns": ["regex:low quality.*high price", "misrepresent",
                             "regex:buyer.*can.t tell", "exploit.*asymmetry",
                             "regex:advertise.*HQ.*LQ", "fake.*quality"],
                "logic": "any",
            },
            "warrant_as_topic": {
                "description": "Communication posts that discuss warrants or staking",
                "patterns": ["warrant", "stake", "escrow", "guarantee.*quality",
                             "credibility.*signal"],
                "logic": "any",
            },
        },
        "cooccurrence": [
            ["quality_trust_focus", "profit_sales_focus"],
        ],
    },

    "q6_brand_vs_profit": {
        "question": "Q6: Under what conditions do agents prefer brand building vs profit maximization?",
        "recommended_action_types": ["list_products"],
        "groups": {
            "brand_building": {
                "description": "Reasoning focused on long-term brand and reputation",
                "patterns": ["long-term", "build.*reputation", "sustainable",
                             "consistent.*quality", "loyal.*customer",
                             "regex:reputation.*long", "brand", "relationship.*buyer"],
                "logic": "any",
            },
            "profit_maximizing": {
                "description": "Reasoning focused on maximizing short-term profit",
                "patterns": ["maximize.*profit", "maximize profit", "quick profit",
                             "short-term profit", "aggressive", "revenue target",
                             "regex:profit.*maximiz", "regex:maximiz.*profit"],
                "logic": "any",
            },
            "explicit_tradeoff": {
                "description": "Explicit trade-off between reputation and profit",
                "patterns": ["regex:profit.*reputation", "regex:reputation.*profit",
                             "sacrifice.*reputation", "reputation.*cost",
                             "regex:balance.*profit.*quality",
                             "regex:tradeoff.*brand.*profit"],
                "logic": "any",
            },
        },
        "cooccurrence": [
            ["brand_building", "profit_maximizing"],
        ],
    },
}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ActionRecord:
    condition: str
    run: int
    round: int
    phase: Optional[str]
    agent_id: int
    agent_name: str
    action_name: str
    reasoning: str


@dataclass
class GroupMatch:
    group_name: str
    matched_patterns: list[str]


@dataclass
class MatchedRecord:
    record: ActionRecord
    groups_matched: list[str]


@dataclass
class GroupStats:
    group_name: str
    n_matched: int
    n_total: int

    @property
    def rate(self) -> float:
        return self.n_matched / self.n_total if self.n_total else 0.0

    @property
    def pct(self) -> str:
        return f"{self.rate * 100:.1f}%"


# ── Loading ───────────────────────────────────────────────────────────────────

def load_records_from_dir(
    exp_dir: str | Path,
    condition_label: str,
    action_types: list[str] | None = None,
    run_filter: str = "all",
) -> list[ActionRecord]:
    """Load action_reasoning records from all run_*_actions.json in exp_dir."""
    exp_dir = Path(exp_dir)
    if not exp_dir.is_dir():
        raise FileNotFoundError(f"Experiment directory not found: {exp_dir}")

    records: list[ActionRecord] = []
    action_files = sorted(exp_dir.glob("run_*_actions.json"))
    if not action_files:
        raise FileNotFoundError(f"No run_*_actions.json found in {exp_dir}")

    for af in action_files:
        run_num_match = re.search(r"run_(\d+)_actions", af.name)
        if not run_num_match:
            continue
        run_num = int(run_num_match.group(1))
        if run_filter != "all" and str(run_num) != str(run_filter):
            continue

        with open(af) as f:
            data = json.loads(f.read(), strict=False)

        for item in data:
            if "agent_infos" not in item:
                continue
            for ai in item["agent_infos"]:
                aai = ai.get("agent_action_info", {})
                reasoning = aai.get("action_reasoning", "")
                action_name = aai.get("action_name", "unknown")
                if not reasoning:
                    continue
                if action_types and action_name not in action_types:
                    continue
                records.append(ActionRecord(
                    condition=condition_label,
                    run=run_num,
                    round=item.get("round", -1),
                    phase=item.get("phase"),
                    agent_id=ai.get("agent_id", -1),
                    agent_name=ai.get("agent_name", "unknown"),
                    action_name=action_name,
                    reasoning=reasoning,
                ))

    return records


# ── Matching engine ───────────────────────────────────────────────────────────

def match_pattern(text: str, pattern: str) -> bool:
    """
    Match a single pattern against text.
      - "regex:..."  → re.search (case-insensitive)
      - plain text   → case-insensitive substring match
    """
    if pattern.startswith("regex:"):
        return bool(re.search(pattern[6:], text, re.IGNORECASE))
    return pattern.lower() in text.lower()


def match_group(record: ActionRecord, group: dict) -> tuple[bool, list[str]]:
    """
    Return (matched: bool, fired_patterns: list[str]).
    logic="any"  → matched if at least one pattern fires
    logic="all"  → matched only if every pattern fires
    """
    patterns = group["patterns"]
    logic = group.get("logic", "any")
    fired = [p for p in patterns if match_pattern(record.reasoning, p)]

    if logic == "all":
        matched = len(fired) == len(patterns)
    else:
        matched = len(fired) > 0

    return matched, fired


def apply_keyword_set(
    records: list[ActionRecord],
    keyword_set: dict,
) -> dict[str, list[MatchedRecord]]:
    """
    For each group in keyword_set, return the list of matched records.
    Also handles cooccurrence groups.
    """
    groups = keyword_set.get("groups", {})
    results: dict[str, list[MatchedRecord]] = {}

    # Per-group matches
    for gname, gdef in groups.items():
        matched: list[MatchedRecord] = []
        for rec in records:
            ok, fired = match_group(rec, gdef)
            if ok:
                matched.append(MatchedRecord(record=rec, groups_matched=[gname]))
        results[gname] = matched

    # Co-occurrence groups
    for pair in keyword_set.get("cooccurrence", []):
        key = " ∩ ".join(pair)
        # A record must appear in ALL groups of the pair
        sets = [set(id(m.record) for m in results.get(g, [])) for g in pair]
        shared_ids = set.intersection(*sets) if sets else set()
        # Collect the actual records
        all_matched = {id(m.record): m.record for g in pair for m in results.get(g, [])}
        results[key] = [
            MatchedRecord(record=all_matched[rid], groups_matched=list(pair))
            for rid in shared_ids
        ]

    return results


# ── Statistics ────────────────────────────────────────────────────────────────

def significance_marker(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def compare_two_conditions(
    n_match_a: int, n_total_a: int,
    n_match_b: int, n_total_b: int,
) -> tuple[float, str]:
    """Fisher's exact test; returns (p_value, marker)."""
    try:
        from scipy.stats import fisher_exact
        table = [
            [n_match_a, n_total_a - n_match_a],
            [n_match_b, n_total_b - n_match_b],
        ]
        _, p = fisher_exact(table)
        return p, significance_marker(p)
    except ImportError:
        return float("nan"), "n/a"


def compare_multi_conditions(counts: list[tuple[int, int]]) -> tuple[float, str]:
    """Chi-square test for 3+ conditions; returns (p_value, marker)."""
    try:
        from scipy.stats import chi2_contingency
        table = [[n, tot - n] for n, tot in counts]
        _, p, _, _ = chi2_contingency(table)
        return p, significance_marker(p)
    except (ImportError, ValueError):
        return float("nan"), "n/a"


# ── Report generation ─────────────────────────────────────────────────────────

def _sample_records(matched: list[MatchedRecord], n: int = 3) -> list[str]:
    """Return up to n sample reasoning snippets (first 200 chars each)."""
    samples = []
    for mr in matched[:n]:
        r = mr.record
        snippet = r.reasoning.replace("\n", " ")[:200]
        samples.append(f"    [{r.agent_name} r{r.round} run_{r.run}] {snippet}…")
    return samples


def generate_report(
    keyword_set: dict,
    results_per_condition: dict[str, dict[str, list[MatchedRecord]]],
    condition_totals: dict[str, int],
    output_dir: Path,
    n_samples: int = 3,
) -> None:
    """Write keyword_filter_report.txt and keyword_filter_results.json."""

    conditions = list(results_per_condition)
    groups = list(keyword_set.get("groups", {}))
    cooccurrences = [" ∩ ".join(p) for p in keyword_set.get("cooccurrence", [])]
    all_group_keys = groups + cooccurrences

    lines: list[str] = [
        "=" * 68,
        "KEYWORD FILTER ANALYSIS",
        "=" * 68,
        f"  Keyword set : {keyword_set.get('name', '(custom)')}",
        f"  Question    : {keyword_set.get('question', '')}",
        f"  Conditions  : {', '.join(conditions)}",
        "",
    ]

    # ── Per-group section ──
    for gkey in all_group_keys:
        is_cooccurrence = "∩" in gkey
        if is_cooccurrence:
            lines.append(f"── Co-occurrence: {gkey} " + "─" * max(0, 58 - len(gkey)))
        else:
            gdef = keyword_set["groups"][gkey]
            lines.append(f"── Group: {gkey} " + "─" * max(0, 58 - len(gkey)))
            lines.append(f"  {gdef.get('description', '')}")
            pats = gdef.get("patterns", [])
            lines.append(f"  Patterns ({gdef.get('logic','any').upper()}): "
                         + " | ".join(pats[:5])
                         + (" …" if len(pats) > 5 else ""))

        # Stats table header
        lines.append("")
        lines.append(f"  {'Condition':<35} {'Matches':>8} {'Total':>7} {'Rate':>8}")
        lines.append("  " + "-" * 62)

        cond_stats: list[tuple[str, int, int]] = []
        for cname in conditions:
            matched = results_per_condition[cname].get(gkey, [])
            total = condition_totals[cname]
            rate = len(matched) / total * 100 if total else 0.0
            cond_stats.append((cname, len(matched), total))
            lines.append(f"  {cname:<35} {len(matched):>8} {total:>7} {rate:>7.1f}%")

        # Statistical comparison
        if len(conditions) == 2:
            (_, n_a, tot_a), (_, n_b, tot_b) = cond_stats[0], cond_stats[1]
            p, marker = compare_two_conditions(n_a, tot_a, n_b, tot_b)
            delta = (n_b / tot_b - n_a / tot_a) * 100 if tot_a and tot_b else 0
            lines.append(f"  {'':35} {'Δ':>8} {delta:>+6.1f}pp  p={p:.3f}{marker}")
        elif len(conditions) > 2:
            counts = [(n, tot) for _, n, tot in cond_stats]
            p, marker = compare_multi_conditions(counts)
            lines.append(f"  {'χ² test across conditions':35} {'':>15}  p={p:.3f}{marker}")

        # Sample quotes per condition
        lines.append("")
        for cname in conditions:
            matched = results_per_condition[cname].get(gkey, [])
            if matched:
                lines.append(f"  Sample — {cname} ({len(matched)} matches):")
                lines.extend(_sample_records(matched, n=n_samples))
        lines.append("")

    # Write text report
    report_path = output_dir / "keyword_filter_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved report: {report_path}")

    # Write JSON results
    json_out: dict = {
        "keyword_set": keyword_set.get("name"),
        "question": keyword_set.get("question"),
        "conditions": conditions,
        "groups": {},
    }
    for gkey in all_group_keys:
        json_out["groups"][gkey] = {}
        for cname in conditions:
            matched = results_per_condition[cname].get(gkey, [])
            total = condition_totals[cname]
            json_out["groups"][gkey][cname] = {
                "n_matched": len(matched),
                "n_total": total,
                "rate": round(len(matched) / total, 4) if total else 0.0,
                "sample_records": [
                    {
                        "agent": m.record.agent_name,
                        "round": m.record.round,
                        "run": m.record.run,
                        "reasoning_snippet": m.record.reasoning[:300],
                    }
                    for m in matched[:5]
                ],
            }

    json_path = output_dir / "keyword_filter_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, indent=2, ensure_ascii=False)
    print(f"Saved results: {json_path}")

    # Write CSV match-rate table
    csv_path = output_dir / "match_rates.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["group"] + conditions + ["delta_pp", "p_value", "sig"])
        for gkey in all_group_keys:
            row = [gkey]
            rates: list[float] = []
            counts_: list[tuple[int, int]] = []
            for cname in conditions:
                matched = results_per_condition[cname].get(gkey, [])
                total = condition_totals[cname]
                rate = len(matched) / total * 100 if total else 0.0
                rates.append(rate)
                counts_.append((len(matched), total))
                row.append(f"{rate:.1f}%")
            if len(conditions) == 2:
                delta = rates[1] - rates[0]
                p, marker = compare_two_conditions(*counts_[0], *counts_[1])
                row += [f"{delta:+.1f}", f"{p:.3f}", marker]
            elif len(conditions) > 2:
                p, marker = compare_multi_conditions(counts_)
                row += ["", f"{p:.3f}", marker]
            else:
                row += ["", "n/a", ""]
            writer.writerow(row)
    print(f"Saved CSV: {csv_path}")


# ── Optional: embedding expansion (Layer 2) ───────────────────────────────────

def expand_with_embeddings(
    seed_records: list[ActionRecord],
    candidate_pool: list[ActionRecord],
    n_neighbors: int,
    model_name: str = "all-MiniLM-L6-v2",
) -> list[ActionRecord]:
    """
    Embed seed_records and candidate_pool; for each seed find the
    n_neighbors nearest candidates (excluding exact matches).
    Returns the union of seeds + neighbours, deduplicated.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    seed_texts = [r.reasoning for r in seed_records]
    pool_texts = [r.reasoning for r in candidate_pool]

    seed_emb = model.encode(seed_texts, show_progress_bar=False, batch_size=32,
                            normalize_embeddings=True)
    pool_emb = model.encode(pool_texts, show_progress_bar=True, batch_size=32,
                            normalize_embeddings=True)

    # Cosine similarity: seed (n_s, d) × pool (n_p, d)^T → (n_s, n_p)
    sims = seed_emb @ pool_emb.T
    seed_ids = {id(r) for r in seed_records}

    expanded_ids: set[int] = set(seed_ids)
    added: list[ActionRecord] = list(seed_records)

    for row in sims:
        top_idx = np.argsort(row)[::-1]
        count = 0
        for idx in top_idx:
            rec = candidate_pool[idx]
            if id(rec) not in expanded_ids:
                expanded_ids.add(id(rec))
                added.append(rec)
                count += 1
            if count >= n_neighbors:
                break

    return added


# ── Optional: cluster filtered set (Layer 3) ─────────────────────────────────

def cluster_filtered_set(
    records: list[ActionRecord],
    output_dir: Path,
    model_name: str = "all-MiniLM-L6-v2",
    n_clusters: int | None = None,
) -> None:
    """Embed + cluster the filtered records; save UMAP plot and summary."""
    # Delegate to the existing analyze.py logic by writing a temp JSON and calling it,
    # or inline here for a lighter dependency.
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    texts = [r.reasoning for r in records]
    if len(texts) < 4:
        print("Too few records for clustering (need ≥4). Skipping.")
        return

    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    if n_clusters is None:
        k_range = [k for k in range(2, min(11, len(texts))) ]
        scores = [
            silhouette_score(
                embeddings,
                KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(embeddings)
            )
            for k in k_range
        ]
        n_clusters = k_range[int(np.argmax(scores))]
        print(f"Auto-selected k={n_clusters} (silhouette scores: "
              f"{ {k: round(s, 3) for k, s in zip(k_range, scores)} })")

    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(embeddings)

    # Cluster summary
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_lines: list[str] = []
    for k in range(n_clusters):
        cluster_recs = [records[i] for i, l in enumerate(labels) if l == k]
        summary_lines.append(f"=== Cluster {k} ({len(cluster_recs)} records) ===")
        agents = [r.agent_name for r in cluster_recs]
        rounds = [r.round for r in cluster_recs]
        summary_lines.append(f"  Rounds: {min(rounds)}–{max(rounds)}")
        from collections import Counter
        summary_lines.append(f"  Agents: {dict(Counter(agents))}")
        for r in cluster_recs[:3]:
            snippet = r.reasoning.replace("\n", " ")[:160]
            summary_lines.append(f"    [{r.agent_name} r{r.round}] {snippet}…")
        summary_lines.append("")

    summary_path = output_dir / "cluster_summary.txt"
    with open(summary_path, "w") as f:
        f.write("\n".join(summary_lines))
    print(f"Saved cluster summary: {summary_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Keyword/snippet-based filtering analysis of action_reasoning records.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("exp_dirs", nargs="+",
                        help="One or more experiment directories (each becomes a condition)")
    parser.add_argument("--labels", nargs="+", default=None,
                        help="Human-readable labels for conditions (same order as exp_dirs)")
    parser.add_argument("--preset", default=None, choices=list(PRESETS),
                        help="Built-in keyword set for a specific question")
    parser.add_argument("--keyword-set", default=None,
                        help="Path to a custom keyword set JSON file")
    parser.add_argument("--action-types", nargs="+", default=None, metavar="ACTION",
                        help="Restrict to these action_name values "
                             "(pass 'list' to print available types and exit)")
    parser.add_argument("--runs", default="all",
                        help="Run filter: all | 1 | 2 | ... | 5")
    parser.add_argument("--samples", type=int, default=3,
                        help="Number of sample quotes per group per condition (default: 3)")
    parser.add_argument("--expand", type=int, default=0, metavar="N",
                        help="Layer 2: for each keyword-matched record, retrieve N nearest "
                             "neighbours from embedding space (0 = disabled)")
    parser.add_argument("--cluster", action="store_true",
                        help="Layer 3: cluster the filtered set and save summary")
    parser.add_argument("--n-clusters", type=int, default=None,
                        help="Number of clusters for --cluster (default: auto)")
    parser.add_argument("--model", default="all-MiniLM-L6-v2",
                        help="SentenceTransformer model for --expand and --cluster")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: <first exp_dir>/keyword_analysis/)")
    args = parser.parse_args()

    # ── Resolve keyword set ──
    if args.preset is not None:
        keyword_set = dict(PRESETS[args.preset])
        keyword_set["name"] = args.preset
    elif args.keyword_set is not None:
        with open(args.keyword_set) as f:
            keyword_set = json.load(f)
    else:
        parser.error("Specify either --preset or --keyword-set")

    # ── Resolve condition labels ──
    exp_dirs = args.exp_dirs
    if args.labels:
        if len(args.labels) != len(exp_dirs):
            parser.error("--labels must have the same number of entries as exp_dirs")
        labels = args.labels
    else:
        labels = [Path(d).name for d in exp_dirs]

    # ── Resolve action types ──
    # Recommend from preset if not specified
    action_types = args.action_types
    if action_types is None and "recommended_action_types" in keyword_set:
        action_types = keyword_set["recommended_action_types"]
        print(f"Using recommended action types from preset: {action_types}")

    # ── Resolve output dir ──
    output_dir = (
        Path(args.output_dir) if args.output_dir
        else Path(exp_dirs[0]) / "keyword_analysis" / (keyword_set.get("name") or "custom")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load records ──
    print("\nLoading records…")
    all_records_per_condition: dict[str, list[ActionRecord]] = {}
    for exp_dir, label in zip(exp_dirs, labels):
        records = load_records_from_dir(
            exp_dir, label, action_types=action_types, run_filter=args.runs
        )
        all_records_per_condition[label] = records
        print(f"  {label}: {len(records)} records")

    # ── Handle --action-types list ──
    if action_types and action_types == ["list"]:
        all_recs = [r for recs in all_records_per_condition.values() for r in recs]
        from collections import Counter
        counts = Counter(r.action_name for r in all_recs)
        print("\nAvailable action types:")
        for name, count in counts.most_common():
            print(f"  {name:<30} ({count} records)")
        return

    # ── Apply keyword sets ──
    print("\nApplying keyword filters…")
    results_per_condition: dict[str, dict[str, list[MatchedRecord]]] = {}
    for label, records in all_records_per_condition.items():
        results_per_condition[label] = apply_keyword_set(records, keyword_set)
        for gkey, matched in results_per_condition[label].items():
            rate = len(matched) / len(records) * 100 if records else 0.0
            print(f"  {label} / {gkey}: {len(matched)}/{len(records)} ({rate:.1f}%)")

    condition_totals = {label: len(recs)
                        for label, recs in all_records_per_condition.items()}

    # ── Layer 2: embedding expansion ──
    if args.expand > 0:
        print(f"\nLayer 2: expanding with {args.expand} nearest neighbours…")
        expand_dir = output_dir / "expanded"
        expand_dir.mkdir(exist_ok=True)
        for label, records in all_records_per_condition.items():
            for gkey in list(keyword_set.get("groups", {})):
                seed_recs = [m.record for m in results_per_condition[label].get(gkey, [])]
                if not seed_recs:
                    continue
                expanded = expand_with_embeddings(
                    seed_recs, records, n_neighbors=args.expand, model_name=args.model
                )
                added = len(expanded) - len(seed_recs)
                print(f"  {label}/{gkey}: {len(seed_recs)} seeds → +{added} neighbours")
                if args.cluster:
                    cluster_filtered_set(
                        expanded, expand_dir / label / gkey,
                        model_name=args.model, n_clusters=args.n_clusters
                    )

    # ── Layer 3: cluster (without expansion) ──
    elif args.cluster:
        print("\nLayer 3: clustering filtered sets…")
        cluster_dir = output_dir / "clusters"
        for label in labels:
            for gkey in list(keyword_set.get("groups", {})):
                matched_recs = [m.record for m in results_per_condition[label].get(gkey, [])]
                if len(matched_recs) < 4:
                    continue
                print(f"  Clustering {label}/{gkey} ({len(matched_recs)} records)…")
                cluster_filtered_set(
                    matched_recs, cluster_dir / label / gkey,
                    model_name=args.model, n_clusters=args.n_clusters
                )

    # ── Generate report ──
    print("\nGenerating report…")
    generate_report(
        keyword_set=keyword_set,
        results_per_condition=results_per_condition,
        condition_totals=condition_totals,
        output_dir=output_dir,
        n_samples=args.samples,
    )

    print(f"\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
