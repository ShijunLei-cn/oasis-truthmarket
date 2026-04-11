#!/usr/bin/env python3
"""
Collusion Analysis Visualization for TruthMarketTwin Project

This module generates visualizations for analyzing seller collusion behavior
in the marketplace experiments.

Data sources:
- data/case_analysis/deception_rate_by_collusion.csv
- data/case_analysis/type_distribution_by_condition.csv
- data/case_analysis/type_distribution_by_round.csv
- data/case_analysis/type_distribution_by_prompt_type.csv
- data/case_analysis/posts_labeled.jsonl

Collusion types (annotated by Claude Sonnet 4.6):
1. Direct Collusion Proposal - Explicit invitation to coordinate deception
2. Deception Strategy Broadcast - Sharing personal deceptive plans
3. Collusion Coordination & Reinforcement - Building on others' deceptive strategies
4. Social Normalization of Deception - Framing deception as normal market behavior
5. Neutral / Market Information Sharing - Non-deceptive information exchange
6. Anti-Collusion / Pro-Honesty - Explicit opposition to deception
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from fig_utils import (
    COLORS,
    setup_style,
    label_panel,
    mannwhitney_p,
    sig_marker_display,
    add_significance_bracket,
    add_sig_footnote,
    save_figure,
)

setup_style()

# ── Collusion Type Definitions ───────────────────────────────────────────────

COLLUSION_TYPES = {
    1: {
        "name": "Direct Collusion Proposal",
        "abbrev": "Type 1",
        "description": "Explicit invitation to coordinate deception",
        "color": "#9B2226",  # dark red - most severe
        "collusive": True,
    },
    2: {
        "name": "Deception Strategy Broadcast",
        "abbrev": "Type 2",
        "description": "Sharing personal deceptive plans",
        "color": "#AE2012",  # bright red
        "collusive": True,
    },
    3: {
        "name": "Collusion Coordination",
        "abbrev": "Type 3",
        "description": "Building on others' deceptive strategies",
        "color": "#D4866A",  # terracotta
        "collusive": True,
    },
    4: {
        "name": "Social Normalization",
        "abbrev": "Type 4",
        "description": "Framing deception as normal behavior",
        "color": "#E8A87C",  # light orange
        "collusive": True,
    },
    5: {
        "name": "Neutral Information",
        "abbrev": "Type 5",
        "description": "Non-deceptive market information",
        "color": "#6B6B6B",  # gray - neutral
        "collusive": False,
    },
    6: {
        "name": "Anti-Collusion",
        "abbrev": "Type 6",
        "description": "Opposition to deception",
        "color": "#2D6A4F",  # green - pro-honesty
        "collusive": False,
    },
}

# ── Experiment Conditions ─────────────────────────────────────────────────────

CONDITIONS = {
    "r_wsc_F_policy_making": "Rep (Policy)",
    "r_wsc_F_pressure_quickprofits": "Rep (Pressure)",
    "r_wsc_F_psychological-based-attack": "Rep (Psych)",
    "r_wsc_R_policy_making": "Rep+Comm (Policy)",
    "r_wsc_R_pressure_quickprofits": "Rep+Comm (Pressure)",
    "r_wsc_R_psychological-based-attack": "Rep+Comm (Psych)",
    "rw_wsc_F_policy_making": "Warrant (Policy)",
    "rw_wsc_F_pressure_quickprofits": "Warrant (Pressure)",
    "rw_wsc_F_psychological-based-attack": "Warrant (Psych)",
    "rw_wsc_R_policy_making": "Warrant+Comm (Policy)",
    "rw_wsc_R_pressure_quickprofits": "Warrant+Comm (Pressure)",
    "rw_wsc_R_psychological-based-attack": "Warrant+Comm (Psych)",
}

# ── Data Loading Functions ────────────────────────────────────────────────────

def load_deception_by_collusion(data_dir: str) -> pd.DataFrame:
    """Load deception rate by collusion status data."""
    path = Path(data_dir) / "case_analysis" / "deception_rate_by_collusion.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_type_distribution_by_condition(data_dir: str) -> pd.DataFrame:
    """Load type distribution by experiment condition."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_by_condition.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_type_distribution_by_round(data_dir: str) -> pd.DataFrame:
    """Load type distribution by round."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_by_round.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_type_distribution_by_prompt(data_dir: str) -> pd.DataFrame:
    """Load type distribution by prompt type."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_by_prompt_type.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_qualitative_examples(data_dir: str) -> List[Dict]:
    """Load qualitative examples for each type."""
    path = Path(data_dir) / "case_analysis" / "qualitative_examples.json"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_type_distribution_real_vs_fake(data_dir: str) -> pd.DataFrame:
    """Load type distribution for real vs fake communication channels."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_real_vs_fake.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def _load_labeled_posts(data_dir: str) -> List[Dict]:
    """Load all labeled posts from posts_labeled.jsonl."""
    path = Path(data_dir) / "case_analysis" / "posts_labeled.jsonl"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return []
    posts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    posts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Focused Collusion → Behavior Consistency Figure (Rep vs Rep+Warrant)
# ─────────────────────────────────────────────────────────────────────────────

def _market_group(exp_id: str) -> str:
    if exp_id.startswith("rw_"):
        return "Rep+Warrant"
    if exp_id.startswith("r_"):
        return "Rep"
    return "Unknown"


def _collusion_behavior_category(is_collusion: bool, is_deceptive: bool) -> str:
    if is_collusion and is_deceptive:
        return "Collusion + Fraud"
    if (not is_collusion) and is_deceptive:
        return "No Collusion + Fraud"
    if is_collusion and (not is_deceptive):
        return "Collusion + No Fraud"
    return "No Collusion + No Fraud"


def fig_collusion_behavior_consistency(data_dir: str, output_dir: Path) -> None:
    """
    Combined figure:
      Left: Agent-level consistency boxplots (collusion-rate vs fraud-rate), by market.
      Right: 4-way category heatmap (post-level), by market.
    """
    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for collusion consistency figure")
        return

    df = pd.DataFrame(posts)
    df["market_group"] = df["experiment_id"].apply(_market_group)
    df = df[df["market_group"].isin(["Rep", "Rep+Warrant"])]
    if df.empty:
        print("  WARNING: No Rep/Rep+Warrant posts found for collusion consistency figure")
        return

    df["is_collusion"] = df["type"].astype(int).isin([1, 2, 3, 4])
    df["is_deceptive"] = df["deceptive_listing"].astype(bool)

    # ── Agent-level consistency metrics ───────────────────────────────────
    agent_stats = (
        df.groupby(["market_group", "agent_name"])
        .agg(
            collusion_rate=("is_collusion", "mean"),
            deception_rate=("is_deceptive", "mean"),
            n_posts=("is_collusion", "size"),
        )
        .reset_index()
    )

    # ── Post-level 4-way category heatmap ────────────────────────────────
    df["category"] = [
        _collusion_behavior_category(c, d)
        for c, d in zip(df["is_collusion"].tolist(), df["is_deceptive"].tolist())
    ]
    categories = [
        "Collusion + Fraud",
        "No Collusion + Fraud",
        "Collusion + No Fraud",
        "No Collusion + No Fraud",
    ]
    market_order = ["Rep", "Rep+Warrant"]
    present_markets = [m for m in market_order if (df["market_group"] == m).any()]
    if not present_markets:
        print("  WARNING: No valid market groups found for collusion consistency figure")
        return
    heatmap = []
    for market in present_markets:
        mdf = df[df["market_group"] == market]
        total = len(mdf)
        row = []
        for cat in categories:
            count = int((mdf["category"] == cat).sum())
            row.append(count / total if total > 0 else 0.0)
        heatmap.append(row)
    heatmap = np.array(heatmap)

    # ── Plotting ─────────────────────────────────────────────────────────
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(12.5, 5.0))

    # Left: boxplots with jittered points
    box_colors = {
        "Collusion": "#9B2226",
        "Fraud": "#AE2012",
    }
    positions = []
    data = []
    labels = []
    x_base = np.arange(len(present_markets))
    offsets = {"Collusion": -0.18, "Fraud": 0.18}

    for i, market in enumerate(present_markets):
        mstats = agent_stats[agent_stats["market_group"] == market]
        for metric_name, metric_key in [("Collusion", "collusion_rate"), ("Fraud", "deception_rate")]:
            values = mstats[metric_key].dropna().tolist()
            positions.append(x_base[i] + offsets[metric_name])
            data.append(values if values else [0.0])
            labels.append(f"{market}\n{metric_name}")

    bp = ax_left.boxplot(
        data,
        positions=positions,
        widths=0.28,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "#1F2937", "linewidth": 1.2},
    )
    for patch, label in zip(bp["boxes"], labels):
        color = box_colors["Collusion"] if "Collusion" in label else box_colors["Fraud"]
        patch.set_facecolor(color)
        patch.set_alpha(0.45)
        patch.set_edgecolor(color)

    # Jittered points
    rng = np.random.default_rng(7)
    for pos, values, label in zip(positions, data, labels):
        jitter = rng.normal(0, 0.02, size=len(values))
        color = box_colors["Collusion"] if "Collusion" in label else box_colors["Fraud"]
        ax_left.scatter(
            np.full(len(values), pos) + jitter,
            values,
            s=14,
            color=color,
            alpha=0.7,
            edgecolors="white",
            linewidth=0.3,
            zorder=3,
        )

    ax_left.set_xticks(x_base)
    ax_left.set_xticklabels(present_markets, fontsize=10)
    ax_left.set_ylabel("Rate (per agent)", fontsize=10)
    ax_left.set_ylim(0, 1.05)
    ax_left.set_title("Agent-Level Consistency\n(Collusion vs Fraud Rates)", fontsize=11, fontweight="bold")
    ax_left.grid(True, axis="y", alpha=0.25, linestyle=":")

    legend_handles = [
        mpatches.Patch(color=box_colors["Collusion"], alpha=0.5, label="Collusion Post Rate"),
        mpatches.Patch(color=box_colors["Fraud"], alpha=0.5, label="Deceptive Listing Rate"),
    ]
    ax_left.legend(handles=legend_handles, frameon=False, fontsize=8, loc="upper right")

    # Right: heatmap
    im = ax_right.imshow(heatmap, cmap="YlOrRd", vmin=0, vmax=max(0.2, heatmap.max()))
    ax_right.set_xticks(np.arange(len(categories)))
    ax_right.set_xticklabels(
        ["C+F", "NC+F", "C+NF", "NC+NF"],
        fontsize=9
    )
    ax_right.set_yticks(np.arange(len(present_markets)))
    ax_right.set_yticklabels(present_markets, fontsize=10)
    ax_right.set_title("Post-Level 4-Way Categories\n(Share of Posts)", fontsize=11, fontweight="bold")

    for i in range(heatmap.shape[0]):
        for j in range(heatmap.shape[1]):
            ax_right.text(
                j, i, f"{heatmap[i, j] * 100:.1f}%",
                ha="center", va="center", fontsize=9, color="#1F2937"
            )

    cbar = fig.colorbar(im, ax=ax_right, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle("Collusion Speech vs Fraud Behavior (Rep vs Rep+Warrant)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, output_dir / "collusion_consistency_rep_vs_warrant.png")
    print("  [Fig-Collusion] Consistency + 4-way heatmap saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Expanded Collusion Analysis Suite (5方案)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    import re
    return re.findall(r"[a-zA-Z']{2,}", (text or "").lower())


def _prepare_posts_df(data_dir: str) -> pd.DataFrame:
    posts = _load_labeled_posts(data_dir)
    if not posts:
        return pd.DataFrame()
    df = pd.DataFrame(posts)
    df["market_group"] = df["experiment_id"].apply(_market_group)
    df = df[df["market_group"].isin(["Rep", "Rep+Warrant"])]
    df["is_collusion"] = df["type"].astype(int).isin([1, 2, 3, 4])
    df["is_deceptive"] = df["deceptive_listing"].astype(bool)
    return df


def fig_scheme1_time_series_and_lag(data_dir: str, output_dir: Path) -> None:
    """Scheme 1: time series + lagged correlation heatmap."""
    df = _prepare_posts_df(data_dir)
    if df.empty:
        print("  WARNING: No data for scheme 1")
        return

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12.8, 4.8))
    lags = list(range(-3, 4))
    corr_mat = []

    for market in ["Rep", "Rep+Warrant"]:
        mdf = df[df["market_group"] == market].copy()
        if mdf.empty:
            corr_mat.append([0.0] * len(lags))
            continue
        rounds = sorted(mdf["round"].unique())
        coll_by_round = mdf.groupby("round")["is_collusion"].mean().reindex(rounds).fillna(0.0)
        dec_by_round = mdf.groupby("round")["is_deceptive"].mean().reindex(rounds).fillna(0.0)

        # Left subplot time series (collusion this round vs deception next round)
        ax_l.plot(rounds, coll_by_round.values, marker="o", label=f"{market} Collusion")
        ax_l.plot(rounds[1:], dec_by_round.shift(-1).dropna().values, marker="s",
                  label=f"{market} Fraud (next round)")

        # Lag correlation
        row_corr = []
        for lag in lags:
            if lag > 0:
                x = coll_by_round.iloc[:-lag]
                y = dec_by_round.iloc[lag:]
            elif lag < 0:
                x = coll_by_round.iloc[-lag:]
                y = dec_by_round.iloc[:lag]
            else:
                x = coll_by_round
                y = dec_by_round
            if len(x) < 2:
                row_corr.append(0.0)
            else:
                row_corr.append(float(np.corrcoef(x, y)[0, 1]))
        corr_mat.append(row_corr)

    ax_l.set_title("Round Trends: Collusion vs Next-Round Fraud", fontsize=11, fontweight="bold")
    ax_l.set_xlabel("Round")
    ax_l.set_ylabel("Rate")
    ax_l.set_ylim(0, 1.0)
    ax_l.grid(True, alpha=0.25, linestyle=":")
    ax_l.legend(frameon=False, fontsize=8)

    corr_mat = np.array(corr_mat)
    im = ax_r.imshow(corr_mat, cmap="coolwarm", vmin=-1, vmax=1)
    ax_r.set_xticks(range(len(lags)))
    ax_r.set_xticklabels(lags, fontsize=8)
    ax_r.set_yticks([0, 1])
    ax_r.set_yticklabels(["Rep", "Rep+Warrant"], fontsize=9)
    ax_r.set_title("Lag Correlation: Collusion → Fraud", fontsize=11, fontweight="bold")
    for i in range(corr_mat.shape[0]):
        for j in range(corr_mat.shape[1]):
            ax_r.text(j, i, f"{corr_mat[i, j]:.2f}", ha="center", va="center", fontsize=7, color="#111")
    fig.colorbar(im, ax=ax_r, fraction=0.046, pad=0.04)

    fig.tight_layout()
    save_figure(fig, output_dir / "collusion_scheme1_time_lag.png")
    print("  [Scheme1] Time series + lag heatmap saved.")


def fig_scheme2_agent_scatter_and_quartile(data_dir: str, output_dir: Path) -> None:
    """Scheme 2: agent scatter + quartile boxplot."""
    df = _prepare_posts_df(data_dir)
    if df.empty:
        print("  WARNING: No data for scheme 2")
        return

    agent_stats = (
        df.groupby(["market_group", "agent_name"])
        .agg(
            collusion_rate=("is_collusion", "mean"),
            deception_rate=("is_deceptive", "mean"),
            n_posts=("is_collusion", "size"),
        )
        .reset_index()
    )

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12.8, 4.8))

    # Scatter by market
    colors = {"Rep": "#4F5D73", "Rep+Warrant": "#1F6FB2"}
    for market in ["Rep", "Rep+Warrant"]:
        sdf = agent_stats[agent_stats["market_group"] == market]
        if sdf.empty:
            continue
        ax_l.scatter(
            sdf["collusion_rate"], sdf["deception_rate"],
            s=np.clip(sdf["n_posts"].values, 10, 80),
            alpha=0.7, color=colors[market], label=market, edgecolors="white", linewidth=0.3
        )
    ax_l.set_title("Agent Scatter: Collusion vs Fraud", fontsize=11, fontweight="bold")
    ax_l.set_xlabel("Collusion Rate")
    ax_l.set_ylabel("Fraud Rate")
    ax_l.set_xlim(0, 1.0)
    ax_l.set_ylim(0, 1.0)
    ax_l.grid(True, alpha=0.25, linestyle=":")
    ax_l.legend(frameon=False, fontsize=8)

    # Quartile boxplot (by collusion-rate quartile)
    bins = [0, 0.25, 0.5, 0.75, 1.0]
    agent_stats["collusion_q"] = pd.cut(agent_stats["collusion_rate"], bins=bins, include_lowest=True)
    labels = ["Q1", "Q2", "Q3", "Q4"]
    data = []
    for q in agent_stats["collusion_q"].cat.categories:
        data.append(agent_stats.loc[agent_stats["collusion_q"] == q, "deception_rate"].tolist() or [0.0])
    ax_r.boxplot(data, tick_labels=labels, patch_artist=True)
    ax_r.set_title("Fraud Rate by Collusion Quartile", fontsize=11, fontweight="bold")
    ax_r.set_xlabel("Collusion Rate Quartile")
    ax_r.set_ylabel("Fraud Rate")
    ax_r.set_ylim(0, 1.0)
    ax_r.grid(True, axis="y", alpha=0.25, linestyle=":")

    fig.tight_layout()
    save_figure(fig, output_dir / "collusion_scheme2_agent_scatter_quartile.png")
    print("  [Scheme2] Agent scatter + quartile boxplot saved.")


def fig_scheme3_keywords_and_embedding(data_dir: str, output_dir: Path) -> None:
    """Scheme 3: log-odds keywords + embedding map."""
    df = _prepare_posts_df(data_dir)
    if df.empty:
        print("  WARNING: No data for scheme 3")
        return

    # Log-odds keyword comparison: collusion vs non-collusion
    tokens_coll = []
    tokens_non = []
    for _, row in df.iterrows():
        toks = _tokenize(row.get("post_content", ""))
        if row["is_collusion"]:
            tokens_coll.extend(toks)
        else:
            tokens_non.extend(toks)

    from collections import Counter
    c1 = Counter(tokens_coll)
    c0 = Counter(tokens_non)
    vocab = set(c1.keys()) | set(c0.keys())
    alpha = 0.1
    n1 = sum(c1.values()) + alpha * len(vocab)
    n0 = sum(c0.values()) + alpha * len(vocab)

    scores = {}
    for w in vocab:
        p1 = (c1.get(w, 0) + alpha) / n1
        p0 = (c0.get(w, 0) + alpha) / n0
        scores[w] = np.log(p1 / p0)
    top_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:20]

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12.8, 4.8))
    words = [w for w, _ in top_words]
    vals = [v for _, v in top_words]
    ax_l.barh(words[::-1], vals[::-1], color="#9B2226")
    ax_l.set_title("Distinctive Words (Collusion vs Non)", fontsize=11, fontweight="bold")
    ax_l.set_xlabel("Log-Odds (Collusion / Non)")

    # Embedding map: sentence-transformers if available, else TF-IDF+SVD
    texts = df["post_content"].fillna("").tolist()
    coords = None
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        emb = model.encode(texts, show_progress_bar=False, batch_size=64)
        try:
            import umap as umap_module
            reducer = umap_module.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric="cosine", random_state=42)
            coords = reducer.fit_transform(emb)
        except Exception:
            from sklearn.manifold import TSNE
            coords = TSNE(n_components=2, random_state=42, perplexity=30).fit_transform(emb)
    except Exception:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        vec = TfidfVectorizer(max_features=2000, stop_words="english")
        X = vec.fit_transform(texts)
        coords = TruncatedSVD(n_components=2, random_state=42).fit_transform(X)

    colors = df["market_group"].map({"Rep": "#4F5D73", "Rep+Warrant": "#1F6FB2"}).values
    ax_r.scatter(coords[:, 0], coords[:, 1], s=8, alpha=0.6, c=colors)
    ax_r.set_title("Embedding Map (colored by market)", fontsize=11, fontweight="bold")
    ax_r.set_xticks([])
    ax_r.set_yticks([])

    fig.tight_layout()
    save_figure(fig, output_dir / "collusion_scheme3_keywords_embedding.png")
    print("  [Scheme3] Keywords + embedding map saved.")


def fig_scheme4_topics_and_fraud(data_dir: str, output_dir: Path) -> None:
    """Scheme 4: LDA topic distribution + topic fraud rate."""
    df = _prepare_posts_df(data_dir)
    if df.empty:
        print("  WARNING: No data for scheme 4")
        return

    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation

    texts = df["post_content"].fillna("").tolist()
    vec = CountVectorizer(max_features=1500, stop_words="english")
    X = vec.fit_transform(texts)
    n_topics = 6
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    topic_dist = lda.fit_transform(X)
    df["topic"] = topic_dist.argmax(axis=1)

    # Topic share by market
    topic_counts = (
        df.groupby(["market_group", "topic"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    topic_counts["share"] = topic_counts["count"] / topic_counts.groupby("market_group")["count"].transform("sum")
    topic_share = topic_counts[["market_group", "topic", "share"]]

    # Fraud rate by topic
    topic_fraud = (
        df.groupby("topic")["is_deceptive"].mean()
        .reset_index(name="fraud_rate")
    )

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12.8, 4.8))
    for market, color in [("Rep", "#4F5D73"), ("Rep+Warrant", "#1F6FB2")]:
        sub = topic_share[topic_share["market_group"] == market]
        ax_l.plot(sub["topic"], sub["share"], marker="o", label=market, color=color)
    ax_l.set_title("Topic Share by Market", fontsize=11, fontweight="bold")
    ax_l.set_xlabel("Topic")
    ax_l.set_ylabel("Share")
    ax_l.set_xticks(range(n_topics))
    ax_l.grid(True, alpha=0.25, linestyle=":")
    ax_l.legend(frameon=False, fontsize=8)

    ax_r.bar(topic_fraud["topic"], topic_fraud["fraud_rate"], color="#9B2226")
    ax_r.set_title("Fraud Rate by Topic", fontsize=11, fontweight="bold")
    ax_r.set_xlabel("Topic")
    ax_r.set_ylabel("Fraud Rate")
    ax_r.set_xticks(range(n_topics))
    ax_r.set_ylim(0, 1.0)
    ax_r.grid(True, axis="y", alpha=0.25, linestyle=":")

    fig.tight_layout()
    save_figure(fig, output_dir / "collusion_scheme4_topics_fraud.png")
    print("  [Scheme4] Topic share + fraud rate saved.")


def _draw_mosaic(ax, data: Dict[str, float], colors: Dict[str, str], title: str) -> None:
    # data keys: Collusion+Fraud, No Collusion+Fraud, Collusion+No Fraud, No Collusion+No Fraud
    coll_fraud = data["Collusion + Fraud"]
    coll_nofraud = data["Collusion + No Fraud"]
    nocoll_fraud = data["No Collusion + Fraud"]
    nocoll_nofraud = data["No Collusion + No Fraud"]

    coll_total = coll_fraud + coll_nofraud
    nocoll_total = nocoll_fraud + nocoll_nofraud
    total = coll_total + nocoll_total if (coll_total + nocoll_total) > 0 else 1.0

    x0 = 0.0
    w_coll = coll_total / total
    w_nocoll = nocoll_total / total

    # Collusion column
    h_cf = coll_fraud / coll_total if coll_total > 0 else 0
    h_cnf = coll_nofraud / coll_total if coll_total > 0 else 0
    ax.add_patch(Rectangle((x0, 0), w_coll, h_cf, facecolor=colors["Collusion + Fraud"], edgecolor="white"))
    ax.add_patch(Rectangle((x0, h_cf), w_coll, h_cnf, facecolor=colors["Collusion + No Fraud"], edgecolor="white"))

    # No-collusion column
    x1 = x0 + w_coll
    h_ncf = nocoll_fraud / nocoll_total if nocoll_total > 0 else 0
    h_ncnf = nocoll_nofraud / nocoll_total if nocoll_total > 0 else 0
    ax.add_patch(Rectangle((x1, 0), w_nocoll, h_ncf, facecolor=colors["No Collusion + Fraud"], edgecolor="white"))
    ax.add_patch(Rectangle((x1, h_ncf), w_nocoll, h_ncnf, facecolor=colors["No Collusion + No Fraud"], edgecolor="white"))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=11, fontweight="bold")


def _draw_sankey_two_layer(ax, data: Dict[str, float], colors: Dict[str, str], title: str) -> None:
    # Simple 2-layer sankey: Collusion vs No Collusion -> Fraud vs No Fraud
    coll_fraud = data["Collusion + Fraud"]
    coll_nofraud = data["Collusion + No Fraud"]
    nocoll_fraud = data["No Collusion + Fraud"]
    nocoll_nofraud = data["No Collusion + No Fraud"]
    total = sum(data.values()) if sum(data.values()) > 0 else 1.0

    left = {"Collusion": (coll_fraud + coll_nofraud) / total,
            "No Collusion": (nocoll_fraud + nocoll_nofraud) / total}
    right = {"Fraud": (coll_fraud + nocoll_fraud) / total,
             "No Fraud": (coll_nofraud + nocoll_nofraud) / total}

    x_l, x_r = 0.05, 0.75
    w = 0.12
    y = 0.05

    # Left bars
    y1 = y
    for k in ["Collusion", "No Collusion"]:
        h = left[k]
        ax.add_patch(Rectangle((x_l, y1), w, h, facecolor=colors[k], edgecolor="white"))
        y1 += h

    # Right bars
    y2 = y
    for k in ["Fraud", "No Fraud"]:
        h = right[k]
        ax.add_patch(Rectangle((x_r, y2), w, h, facecolor=colors[k], edgecolor="white"))
        y2 += h

    # Ribbons (approximate with polygons)
    def ribbon(x0, x1, y0, y1, y2, y3, color):
        verts = [(x0 + w, y0), (x1, y2), (x1, y3), (x0 + w, y1)]
        ax.add_patch(mpatches.Polygon(verts, closed=True, facecolor=color, alpha=0.6, edgecolor="none"))

    # Collusion -> Fraud
    left_coll_top = y + left["Collusion"]
    left_coll_bottom = y
    right_fraud_top = y + right["Fraud"]
    right_fraud_bottom = y
    cf = coll_fraud / total
    cnf = coll_nofraud / total
    ncf = nocoll_fraud / total

    # Collusion to Fraud
    ribbon(x_l, x_r, left_coll_bottom, left_coll_bottom + cf, right_fraud_bottom, right_fraud_bottom + cf,
           colors["Collusion + Fraud"])
    # Collusion to No Fraud
    ribbon(x_l, x_r, left_coll_bottom + cf, left_coll_bottom + cf + cnf,
           right_fraud_top, right_fraud_top + cnf, colors["Collusion + No Fraud"])
    # No Collusion to Fraud
    ribbon(x_l, x_r, left_coll_top, left_coll_top + ncf,
           right_fraud_bottom + cf, right_fraud_bottom + cf + ncf, colors["No Collusion + Fraud"])

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=11, fontweight="bold")


def fig_scheme5_mosaic_and_sankey(data_dir: str, output_dir: Path) -> None:
    """Scheme 5: Mosaic + Sankey."""
    df = _prepare_posts_df(data_dir)
    if df.empty:
        print("  WARNING: No data for scheme 5")
        return

    df["category"] = [
        _collusion_behavior_category(c, d)
        for c, d in zip(df["is_collusion"].tolist(), df["is_deceptive"].tolist())
    ]
    categories = [
        "Collusion + Fraud",
        "No Collusion + Fraud",
        "Collusion + No Fraud",
        "No Collusion + No Fraud",
    ]
    colors = {
        "Collusion + Fraud": "#9B2226",
        "No Collusion + Fraud": "#E07A5F",
        "Collusion + No Fraud": "#D4866A",
        "No Collusion + No Fraud": "#6B6B6B",
        "Collusion": "#9B2226",
        "No Collusion": "#6B6B6B",
        "Fraud": "#AE2012",
        "No Fraud": "#52B788",
    }

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12.8, 4.8))
    for ax, market in zip([ax_l, ax_r], ["Rep", "Rep+Warrant"]):
        mdf = df[df["market_group"] == market]
        total = len(mdf)
        data = {cat: float((mdf["category"] == cat).sum()) / total if total > 0 else 0.0 for cat in categories}
        _draw_mosaic(ax, data, colors, f"Mosaic: {market}")

    fig.tight_layout()
    save_figure(fig, output_dir / "collusion_scheme5_mosaic.png")
    print("  [Scheme5] Mosaic plot saved.")

    fig2, (ax_l2, ax_r2) = plt.subplots(1, 2, figsize=(12.8, 4.8))
    for ax, market in zip([ax_l2, ax_r2], ["Rep", "Rep+Warrant"]):
        mdf = df[df["market_group"] == market]
        total = len(mdf)
        data = {cat: float((mdf["category"] == cat).sum()) / total if total > 0 else 0.0 for cat in categories}
        _draw_sankey_two_layer(ax, data, colors, f"Sankey: {market}")

    fig2.tight_layout()
    save_figure(fig2, output_dir / "collusion_scheme5_sankey.png")
    print("  [Scheme5] Sankey plot saved.")
# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: Deception Rate by Collusion Status
# ─────────────────────────────────────────────────────────────────────────────

def fig1_deception_by_collusion(data_dir: str, output_dir: Path) -> None:
    """Create bar chart showing deception rates with/without collusion."""
    df = load_deception_by_collusion(data_dir)
    if df.empty:
        print("  WARNING: Empty dataframe for fig1")
        return

    fig, ax = plt.subplots(figsize=(5, 4))

    x_pos = [0, 1]
    bars = ax.bar(x_pos, df["deception_rate"].values,
                  color=[COLORS["neutral"], "#AE2012"],
                  width=0.5, edgecolor="white", linewidth=0.5)

    # Add value labels
    for bar, rate, n in zip(bars, df["deception_rate"].values, df["n_posts"].values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f"{rate*100:.1f}%\n(n={n})",
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(["No Collusion Detected\n(4729 posts)",
                        "Collusion Detected\n(683 posts)"],
                       fontsize=10)
    ax.set_ylabel("Deception Rate", fontsize=11)
    ax.set_title("Seller Collusion Dramatically Increases Deception\n"
                 "(4.9% → 41.3%, 8.4x increase)",
                 fontsize=11, fontweight='bold', pad=10)
    ax.set_ylim(0, 0.55)
    ax.axhline(y=0.05, color='gray', linestyle='--', alpha=0.5, label='5% threshold')

    # Add annotation
    increase = (df["deception_rate"].values[1] / df["deception_rate"].values[0])
    ax.annotate(f"{increase:.1f}x increase",
                xy=(0.5, 0.25), xytext=(0.5, 0.40),
                fontsize=12, fontweight='bold', color='#AE2012',
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#AE2012', lw=2))

    add_sig_footnote(fig, extra="Collusion detected via Claude Sonnet 4.6 annotation")
    save_figure(fig, output_dir / "fig1_deception_by_collusion.png")
    print("  [Fig1] Deception by collusion status saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1-1: Sankey Diagrams by Round
# ─────────────────────────────────────────────────────────────────────────────

def _compute_agent_transitions(df: pd.DataFrame,
                                rnd1: int, rnd2: int) -> Tuple[int, int, int, int]:
    """
    Track agents across two rounds.  For each unique (experiment_id, run_id, agent_name):
      - R1 deceptive: any deceptive_listing in rnd1
      - R2 collusive: any post with primary_type in 1-4 in rnd2
    Only agents appearing in BOTH rounds are counted.
    Returns (dec_coll, dec_nocoll, nodec_coll, nodec_nocoll).
    """
    dc = dn = nc_c = nc_n = 0
    for _, grp in df.groupby(["experiment_id", "run_id", "agent_name"]):
        r1 = grp[grp["round"] == rnd1]
        r2 = grp[grp["round"] == rnd2]
        if len(r1) == 0 or len(r2) == 0:
            continue
        was_dec = bool(r1["behavior_deception"].any())
        is_coll = bool(r2["post_collusion"].any())
        if   was_dec and     is_coll: dc   += 1
        elif was_dec and not is_coll: dn   += 1
        elif not was_dec and is_coll: nc_c += 1
        else:                         nc_n += 1
    return dc, dn, nc_c, nc_n


def _draw_sankey_ax(ax, cc: int, cn: int, nc: int, nn: int,
                    x_offset: float = 0.0, x_scale: float = 1.0,
                    sublabel: str = "") -> None:
    """
    Draw a simple mini Sankey diagram on the given axis.
    
    Parameters:
    - cc: Collusion post + Deception behavior
    - cn: Collusion post + No deception
    - nc: No collusion post + Deception behavior  
    - nn: No collusion post + No deception
    - x_offset: Horizontal offset
    - x_scale: Horizontal scale
    - sublabel: Sublabel for the plot
    """
    total = cc + cn + nc + nn
    if total == 0:
        ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=8)
        return
    
    # Calculate proportions (absolute flow shares)
    p_cc = cc / total  # Coll -> Dec
    p_cn = cn / total  # Coll -> NoDec
    p_nc = nc / total  # NoColl -> Dec
    p_nn = nn / total  # NoColl -> NoDec
    
    # Node positions (normalized to 0-1, then scaled)
    left = 0.15 * x_scale + x_offset
    right = 0.85 * x_scale + x_offset
    node_width = 0.12 * x_scale
    
    # Colors
    C_COLL = "#AE2012"      # Collusion - red
    C_NOCOLL = "#6B6B6B"   # No Collusion - gray
    C_DEC = "#9B2226"      # Deception - dark red
    C_NODEC = "#52B788"    # No Deception - green
    
    # Left nodes (Post Collusion Status)
    coll_height = p_cc + p_cn
    nocoll_height = p_nc + p_nn
    
    # Draw left nodes
    if coll_height > 0:
        ax.add_patch(plt.Rectangle((left, 1 - coll_height), node_width, coll_height,
                                    facecolor=C_COLL, edgecolor='white', linewidth=0.5))
        if coll_height > 0.1:
            ax.text(left + node_width/2, 1 - coll_height/2, f"{coll_height:.0%}", 
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    if nocoll_height > 0:
        ax.add_patch(plt.Rectangle((left, 0), node_width, nocoll_height,
                                    facecolor=C_NOCOLL, edgecolor='white', linewidth=0.5))
        if nocoll_height > 0.1:
            ax.text(left + node_width/2, nocoll_height/2, f"{nocoll_height:.0%}",
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    # Right nodes (Behavior)
    dec_height = p_cc + p_nc
    nodec_height = p_cn + p_nn
    
    if dec_height > 0:
        ax.add_patch(plt.Rectangle((right, 1 - dec_height), node_width, dec_height,
                                    facecolor=C_DEC, edgecolor='white', linewidth=0.5))
        if dec_height > 0.1:
            ax.text(right + node_width/2, 1 - dec_height/2, f"{dec_height:.0%}",
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    if nodec_height > 0:
        ax.add_patch(plt.Rectangle((right, 0), node_width, nodec_height,
                                    facecolor=C_NODEC, edgecolor='white', linewidth=0.5))
        if nodec_height > 0.1:
            ax.text(right + node_width/2, nodec_height/2, f"{nodec_height:.0%}",
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    # Draw flow ribbons between left and right nodes using cubic Bezier curves
    # Flow colors: Coordinated (cc), Verbal (cn), Hidden (nc), Honest (nn)
    R_CC = "#AE2012"   # Coll→Dec (Coordinated Deception)
    R_CN = "#E07A5F"   # Coll→NoDec (Verbal Collusion) 
    R_NC = "#9B2226"   # NoColl→Dec (Hidden Deception)
    R_NN = "#52B788"   # NoColl→NoDec (Honest)
    
    # Helper to draw a ribbon with cubic Bezier curves
    def ribbon(xleft, xright, ly0, ly1, ry0, ry1, color, alpha):
        """Draw a ribbon/flow using cubic Bezier curves."""
        if (ly1 - ly0) < 4e-4 or (ry1 - ry0) < 4e-4:
            return
        mx = (xleft + xright) / 2
        verts = [
            (xleft, ly1), (mx, ly1), (mx, ry1), (xright, ry1),
            (xright, ry0), (mx, ry0), (mx, ly0), (xleft, ly0),
            (xleft, ly1),
        ]
        codes = [MPath.MOVETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes),
                               fc=color, ec='none', alpha=alpha, zorder=2))
    
    # Flow boundaries with strict 1:1 thickness matching across both sides.
    # Left:  top block=Coll, bottom block=NoColl
    l_coll_bottom = 1.0 - coll_height
    l_cc0, l_cc1 = 1.0 - p_cc, 1.0
    l_cn0, l_cn1 = l_coll_bottom, l_coll_bottom + p_cn
    l_nc0, l_nc1 = p_nn, p_nn + p_nc
    l_nn0, l_nn1 = 0.0, p_nn

    # Right: top block=Dec, bottom block=NoDec
    r_dec_bottom = 1.0 - dec_height
    r_cc0, r_cc1 = 1.0 - p_cc, 1.0
    r_nc0, r_nc1 = r_dec_bottom, r_dec_bottom + p_nc
    r_cn0, r_cn1 = p_nn, p_nn + p_cn
    r_nn0, r_nn1 = 0.0, p_nn

    # Draw flows
    if cc > 0:
        ribbon(left + node_width, right,
               l_cc0, l_cc1,
               r_cc0, r_cc1,
               R_CC, 0.65)

    if cn > 0:
        ribbon(left + node_width, right,
               l_cn0, l_cn1,
               r_cn0, r_cn1,
               R_CN, 0.60)

    if nc > 0:
        ribbon(left + node_width, right,
               l_nc0, l_nc1,
               r_nc0, r_nc1,
               R_NC, 0.60)

    if nn > 0:
        ribbon(left + node_width, right,
               l_nn0, l_nn1,
               r_nn0, r_nn1,
               R_NN, 0.55)
    
    # Node labels (folded for long terms to improve readability)
    coll_y = 1.0 - coll_height / 2
    nocoll_y = nocoll_height / 2
    dec_y = 1.0 - dec_height / 2
    nodec_y = nodec_height / 2
    ax.text(left - 0.02, coll_y, "Coll" if coll_height > 0.10 else "", 
           ha='right', va='center', fontsize=5, fontweight='bold', color=C_COLL)
    ax.text(left - 0.02, nocoll_y, "No\nColl" if nocoll_height > 0.10 else "", 
           ha='right', va='center', fontsize=5, fontweight='bold', color=C_NOCOLL, linespacing=0.9)
    ax.text(right + node_width + 0.02, dec_y, "Dec" if dec_height > 0.10 else "",
           ha='left', va='center', fontsize=5, fontweight='bold', color=C_DEC)
    ax.text(right + node_width + 0.02, nodec_y, "No\nDec" if nodec_height > 0.10 else "",
           ha='left', va='center', fontsize=5, fontweight='bold', color=C_NODEC, linespacing=0.9)
    
    # Sublabel
    if sublabel:
        ax.text(0.5, -0.05, sublabel, ha='center', va='top', fontsize=5, style='italic')


def _draw_threestage_sankey_panel(ax,
                                   r1_cc: int, r1_cn: int, r1_nc: int, r1_nn: int,
                                   tr_dc: int, tr_dn: int, tr_nc_c: int, tr_nc_n: int,
                                   r10_cc: int, r10_cn: int, r10_nc: int, r10_nn: int,
                                   rnd1: int, rnd2: int) -> None:
    """
    3-stage Sankey on one axes — 4 node columns:
      Stage A  Col1→Col2 : R1 Post Collusion  → R1 Deception Behavior
      Stage B  Col2→Col3 : R1 Deception       → R10 Post Collusion  (agent tracking)
      Stage C  Col3→Col4 : R10 Post Collusion → R10 Deception Behavior

    Column heights are self-consistent: each column sums to 1, and the
    node-split proportions propagate correctly from stage to stage.
    """
    # ── Semantic colors ───────────────────────────────────────────────────
    C_NOCOLL = "#6E8CAB"    # steel-blue-gray  – No Collusion post
    C_COLL   = "#C0392B"    # vivid red        – Collusion post
    C_NODEC  = "#27AE60"    # forest green     – No Deception behavior
    C_DEC    = "#7B241C"    # deep crimson     – Deception behavior

    # Ribbon fills (semi-transparent)
    R_NN = "#A4BCC9"   # NoColl→NoDec : muted blue-gray
    R_ND = "#E8A04E"   # NoColl→Dec   : amber (the "unexpected" flow)
    R_CN = "#EDAB96"   # Coll→NoDec   : salmon
    R_CD = "#C0392B"   # Coll→Dec     : vivid red

    RB_NN = "#7DCEA0"  # NoDec→NoColl : light green (maintained honesty)
    RB_NC = "#EDAB96"  # NoDec→Coll   : salmon (new colluder)
    RB_DN = "#A4BCC9"  # Dec→NoColl   : muted blue (de-escalation)
    RB_DC = "#C0783A"  # Dec→Coll     : burnt orange (escalation)

    # ── Node column x-positions ───────────────────────────────────────────
    COLS = [
        (0.04, 0.13),  # Col1: R1 Post Collusion
        (0.37, 0.46),  # Col2: R1 Behavior
        (0.64, 0.73),  # Col3: R10 Post Collusion
        (0.97, 1.06),  # Col4: R10 Behavior
    ]
    GAP = 0.010  # vertical gap between stacked nodes

    x1l, x1r = COLS[0]
    x2l, x2r = COLS[1]
    x3l, x3r = COLS[2]
    x4l, x4r = COLS[3]

    # ── Stage A: heights from R1 post data ───────────────────────────────
    r1_total = r1_cc + r1_cn + r1_nc + r1_nn
    if r1_total == 0:
        ax.axis('off')
        return

    f_cc = r1_cc / r1_total;  f_cn = r1_cn / r1_total
    f_nc = r1_nc / r1_total;  f_nn = r1_nn / r1_total

    h1_nocoll = f_nc + f_nn    # Col1 bottom node height
    h1_coll   = f_cc + f_cn    # Col1 top node height
    h2_nodec  = f_nn + f_cn    # Col2 bottom node height
    h2_dec    = f_cc + f_nc    # Col2 top node height

    # ── Stage B: agent transitions, scaled to match Col2 heights ─────────
    tr_dec_tot   = max(tr_dc + tr_dn,   1)
    tr_nodec_tot = max(tr_nc_c + tr_nc_n, 1)

    b_dec_coll   = h2_dec   * (tr_dc   / tr_dec_tot)
    b_dec_nocoll = h2_dec   * (tr_dn   / tr_dec_tot)
    b_nodec_coll   = h2_nodec * (tr_nc_c / tr_nodec_tot)
    b_nodec_nocoll = h2_nodec * (tr_nc_n / tr_nodec_tot)

    h3_coll   = b_dec_coll   + b_nodec_coll
    h3_nocoll = b_dec_nocoll + b_nodec_nocoll

    # ── Stage C: deception rates from R10 post data ───────────────────────
    r10c_tot  = max(r10_cc + r10_cn, 1)
    r10nc_tot = max(r10_nc + r10_nn, 1)

    c_coll_dec     = h3_coll   * (r10_cc / r10c_tot)
    c_coll_nodec   = h3_coll   * (r10_cn / r10c_tot)
    c_nocoll_dec   = h3_nocoll * (r10_nc / r10nc_tot)
    c_nocoll_nodec = h3_nocoll * (r10_nn / r10nc_tot)

    h4_nodec = c_coll_nodec + c_nocoll_nodec
    h4_dec   = c_coll_dec   + c_nocoll_dec

    # ── Ribbon helper (cubic Bezier) ──────────────────────────────────────
    def ribbon(xleft, xright, ly0, ly1, ry0, ry1, color, alpha):
        if (ly1 - ly0) < 4e-4 or (ry1 - ry0) < 4e-4:
            return
        mx = (xleft + xright) / 2
        verts = [
            (xleft, ly1), (mx, ly1), (mx, ry1), (xright, ry1),
            (xright, ry0), (mx, ry0), (mx, ly0), (xleft, ly0),
            (xleft, ly1),
        ]
        codes = [MPath.MOVETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes),
                               fc=color, ec='none', alpha=alpha, zorder=2))
        # thin center-line highlight for depth
        cy_l = (ly0 + ly1) / 2;  cy_r = (ry0 + ry1) / 2
        hl = min((ly1-ly0), (ry1-ry0)) * 0.18
        verts_hl = [
            (xleft, cy_l+hl), (mx, cy_l+hl), (mx, cy_r+hl), (xright, cy_r+hl),
            (xright, cy_r-hl), (mx, cy_r-hl), (mx, cy_l-hl), (xleft, cy_l-hl),
            (xleft, cy_l+hl),
        ]
        ax.add_patch(PathPatch(MPath(verts_hl, codes),
                               fc='white', ec='none', alpha=0.15, zorder=3))

    # ── Node helper (rounded rect + labels) ──────────────────────────────
    def node(xl, xr, yb_raw, yt_raw, color, pct_val,
             outer_lbl, side, count=None):
        h = yt_raw - yb_raw
        if h < 5e-5:
            return
        yb = yb_raw + GAP * 0.4
        yt = yt_raw - GAP * 0.4
        if yt - yb < 1e-4:
            return
        # shadow
        ax.add_patch(mpatches.FancyBboxPatch(
            (xl + 0.005, yb - 0.006), xr - xl, yt - yb,
            boxstyle="round,pad=0.007",
            fc='#333333', ec='none', alpha=0.13, zorder=3))
        # body
        ax.add_patch(mpatches.FancyBboxPatch(
            (xl, yb), xr - xl, yt - yb,
            boxstyle="round,pad=0.007",
            fc=color, ec='white', lw=1.4, zorder=4))
        # percentage text inside
        cy = (yb + yt) / 2
        if h > 0.10:
            ax.text((xl+xr)/2, cy, f"{pct_val*100:.0f}%",
                    ha='center', va='center', fontsize=8,
                    color='white', fontweight='bold', zorder=5)
        elif h > 0.050:
            ax.text((xl+xr)/2, cy, f"{pct_val*100:.0f}%",
                    ha='center', va='center', fontsize=6.5,
                    color='white', fontweight='bold', zorder=5)
        # outer label
        if outer_lbl:
            pad = 0.020
            lbl_str = outer_lbl if count is None else f"{outer_lbl}\nn={count}"
            fs_lbl = 6.5
            if side == 'left':
                ax.text(xl - pad, cy, lbl_str,
                        ha='right', va='center', fontsize=fs_lbl,
                        color=color, fontweight='bold', zorder=5,
                        linespacing=1.2)
            else:
                ax.text(xr + pad, cy, lbl_str,
                        ha='left', va='center', fontsize=fs_lbl,
                        color=color, fontweight='bold', zorder=5,
                        linespacing=1.2)

    # ── Draw nodes ────────────────────────────────────────────────────────
    node(x1l, x1r, 0,        h1_nocoll, C_NOCOLL, h1_nocoll,
         "No Coll", 'left', count=r1_nc+r1_nn)
    node(x1l, x1r, h1_nocoll, 1.0,      C_COLL,   h1_coll,
         "Coll",    'left', count=r1_cc+r1_cn)

    node(x2l, x2r, 0,        h2_nodec,  C_NODEC, h2_nodec,
         "No Dec",  'right', count=r1_nn+r1_cn)
    node(x2l, x2r, h2_nodec, 1.0,       C_DEC,   h2_dec,
         "Dec",     'right', count=r1_cc+r1_nc)

    node(x3l, x3r, 0,        h3_nocoll, C_NOCOLL, h3_nocoll,
         "No Coll", 'left', count=tr_dn+tr_nc_n)
    node(x3l, x3r, h3_nocoll, 1.0,      C_COLL,   h3_coll,
         "Coll",    'left', count=tr_dc+tr_nc_c)

    node(x4l, x4r, 0,        h4_nodec,  C_NODEC, h4_nodec,
         "No Dec",  'right', count=r10_nn+r10_cn)
    node(x4l, x4r, h4_nodec, 1.0,       C_DEC,   h4_dec,
         "Dec",     'right', count=r10_cc+r10_nc)

    # ── Stage A ribbons (Col1 → Col2) ─────────────────────────────────────
    # Col1 stacking (within NoColl: [0,f_nn]→NoDec, [f_nn,h1_nocoll]→Dec)
    # Col1 stacking (within Coll:   [h1_nocoll,h1_nocoll+f_cn]→NoDec, [+f_cn,1]→Dec)
    # Col2 sink stacking (NoDec: [0,f_nn]←NoColl, [f_nn,h2_nodec]←Coll)
    #                    (Dec:  [h2_nodec,h2_nodec+f_nc]←NoColl, [+f_nc,1]←Coll)
    for (ly0, ly1, ry0, ry1, col, alp) in [
        (0,               f_nn,             0,               f_nn,                R_NN, 0.58),
        (f_nn,            h1_nocoll,        h2_nodec,        h2_nodec + f_nc,     R_ND, 0.72),
        (h1_nocoll,       h1_nocoll + f_cn, f_nn,            h2_nodec,            R_CN, 0.62),
        (h1_nocoll + f_cn, 1.0,             h2_nodec + f_nc, 1.0,                 R_CD, 0.72),
    ]:
        ribbon(x1r, x2l, ly0, ly1, ry0, ry1, col, alp)

    # ── Stage B ribbons (Col2 → Col3) ─────────────────────────────────────
    # Col2 source (NoDec: [0,b_nn_n]→NoColl, [b_nn_n,h2_nodec]→Coll)
    #             (Dec:  [h2_nodec,h2_nodec+b_dec_n]→NoColl, [+b_dec_n,1]→Coll)
    # Col3 sink   (NoColl: [0,b_nn_n]←NoDec, [b_nn_n,h3_nocoll]←Dec)
    #             (Coll:  [h3_nocoll,h3_nocoll+b_nn_c]←NoDec, [+b_nn_c,1]←Dec)
    for (ly0, ly1, ry0, ry1, col, alp) in [
        (0,                    b_nodec_nocoll,          0,                        b_nodec_nocoll,          RB_NN, 0.58),
        (b_nodec_nocoll,       h2_nodec,                h3_nocoll,                h3_nocoll + b_nodec_coll, RB_NC, 0.68),
        (h2_nodec,             h2_nodec + b_dec_nocoll, b_nodec_nocoll,           h3_nocoll,               RB_DN, 0.62),
        (h2_nodec + b_dec_nocoll, 1.0,                  h3_nocoll + b_nodec_coll, 1.0,                     RB_DC, 0.72),
    ]:
        ribbon(x2r, x3l, ly0, ly1, ry0, ry1, col, alp)

    # ── Stage C ribbons (Col3 → Col4) ─────────────────────────────────────
    # Col3 source (NoColl: [0,c_nc_n]→NoDec, [c_nc_n,h3_nocoll]→Dec)
    #             (Coll:   [h3_nocoll,h3_nocoll+c_c_n]→NoDec, [+c_c_n,1]→Dec)
    # Col4 sink   (NoDec: [0,c_nc_n]←NoColl, [c_nc_n,h4_nodec]←Coll)
    #             (Dec:   [h4_nodec,h4_nodec+c_nc_d]←NoColl, [+c_nc_d,1]←Coll)
    for (ly0, ly1, ry0, ry1, col, alp) in [
        (0,                    c_nocoll_nodec,             0,                      c_nocoll_nodec,            R_NN, 0.58),
        (c_nocoll_nodec,       h3_nocoll,                  h4_nodec,               h4_nodec + c_nocoll_dec,   R_ND, 0.72),
        (h3_nocoll,            h3_nocoll + c_coll_nodec,   c_nocoll_nodec,         h4_nodec,                  R_CN, 0.62),
        (h3_nocoll + c_coll_nodec, 1.0,                    h4_nodec + c_nocoll_dec, 1.0,                      R_CD, 0.72),
    ]:
        ribbon(x3r, x4l, ly0, ly1, ry0, ry1, col, alp)

    # ── Column header labels ──────────────────────────────────────────────
    HDR_Y = 1.115
    for (xl, xr), lbl in zip(COLS, [
        f"Rnd {rnd1}  Post Collusion",
        f"Rnd {rnd1}  Behavior",
        f"Rnd {rnd2}  Post Collusion",
        f"Rnd {rnd2}  Behavior",
    ]):
        ax.text((xl + xr) / 2, HDR_Y, lbl,
                ha='center', va='bottom', fontsize=7.5,
                fontweight='bold', color='#2C3E50')

    # Stage connector labels at the bottom
    for mx, lbl in [
        ((x1r + x2l) / 2, "A: post→beh"),
        ((x2r + x3l) / 2, "B: beh→post\n(agent)"),
        ((x3r + x4l) / 2, "C: post→beh"),
    ]:
        ax.text(mx, -0.055, lbl,
                ha='center', va='top', fontsize=5.5,
                color='#888888', style='italic')

    ax.set_xlim(-0.22, 1.28)
    ax.set_ylim(-0.12, 1.25)
    ax.axis('off')


def fig1_1_sankey_by_condition(data_dir: str, output_dir: Path,
                               rounds: Tuple[int, int] = (1, 10)) -> None:
    """
    2x2 grid of panels, one per market condition.
    Each panel contains two side-by-side mini-Sankeys for the two selected rounds.

    rounds: tuple of two round numbers to compare (default: first vs last).
    """
    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for fig1-1")
        return

    df = pd.DataFrame(posts)
    df["post_collusion"] = df["type"].isin([1, 2, 3, 4])
    df["behavior_deception"] = df["deceptive_listing"].astype(bool)

    COND_GROUPS = [
        ("Rep  (No Seller Comm)",
         lambda e: e.startswith("r_wsc_")  and "_F_" in e),
        ("Rep  (Seller Comm)",
         lambda e: e.startswith("r_wsc_")  and "_R_" in e),
        ("Rep + Warrant  (No Seller Comm)",
         lambda e: e.startswith("rw_wsc_") and "_F_" in e),
        ("Rep + Warrant  (Seller Comm)",
         lambda e: e.startswith("rw_wsc_") and "_R_" in e),
    ]
    layout = [(0, 0), (0, 1), (1, 0), (1, 1)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.subplots_adjust(wspace=0.55, hspace=0.55)

    # Two mini-Sankeys per panel: left half [0, 0.47], right half [0.53, 1.0]
    # x_offset + x_scale must keep unit-space bars [0.18..0.82] within [0, 1]
    SLOTS = [
        (0.00, 0.47),   # left slot:  Round rounds[0]
        (0.53, 0.47),   # right slot: Round rounds[1]
    ]

    for (row, col), (title, mask_fn) in zip(layout, COND_GROUPS):
        ax = axes[row][col]
        cdf = df[df["experiment_id"].apply(mask_fn)]

        for slot_idx, (x_off, x_sc) in enumerate(SLOTS):
            rnd = rounds[slot_idx]
            rdf = cdf[cdf["round"] == rnd]
            cc = int((rdf["post_collusion"] & rdf["behavior_deception"]).sum())
            cn = int((rdf["post_collusion"] & ~rdf["behavior_deception"]).sum())
            nc = int((~rdf["post_collusion"] & rdf["behavior_deception"]).sum())
            nn = int((~rdf["post_collusion"] & ~rdf["behavior_deception"]).sum())
            _draw_sankey_ax(ax, cc, cn, nc, nn,
                            x_offset=x_off, x_scale=x_sc,
                            sublabel=f"Round {rnd}")

        # Separator line between the two mini-Sankeys
        ax.axvline(x=0.50, color='#CCCCCC', linewidth=0.8, linestyle='--', zorder=1)

        ax.set_xlim(-0.08, 1.08)
        ax.set_ylim(-0.05, 1.22)
        ax.set_title(title, fontsize=9, fontweight='bold', pad=6)
        ax.axis('off')

    fig.suptitle(
        f"Post Collusion → Seller Deception Behavior: Round {rounds[0]} vs Round {rounds[1]}\n"
        "by Market Condition  (Left node: Post Collusion Status | Right node: Behavior)",
        fontsize=12, fontweight='bold', y=1.02
    )

    legend_handles = [
        mpatches.Patch(fc="#AE2012", label="Collusion post (types 1-4)"),
        mpatches.Patch(fc="#6B6B6B", label="No Collusion\npost (types 5-6)"),
        mpatches.Patch(fc="#9B2226", label="Deception (behavior)"),
        mpatches.Patch(fc="#52B788", label="No Deception\n(behavior)"),
        mpatches.Patch(fc="#E09B70", label="No-Collusion post → Deception"),
        mpatches.Patch(fc="#D4866A", label="Collusion post → No Deception"),
    ]
    fig.legend(handles=legend_handles, loc='lower center', ncol=3,
               frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.07))

    add_sig_footnote(fig, y=-0.13,
                     extra="Flow width proportional to post fraction within each condition × round")
    save_figure(fig, output_dir / "fig1_1_sankey_by_condition.png")
    print("  [Fig1-1] Sankey by condition (2 rounds) saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1-2: Embedding Cluster + Word Clouds
# ─────────────────────────────────────────────────────────────────────────────

_WC_STOPWORDS_EXTRA = {
    "will", "can", "us", "also", "one", "let", "well", "may", "want",
    "need", "use", "get", "make", "just", "way", "product", "products",
    "market", "marketplace", "seller", "sellers", "buyer", "customers",
    "customer", "business", "quality", "high", "low", "think", "know",
    "time", "good", "like", "new", "ensure", "help", "believe", "important",
    "fellow", "approach", "strategy", "strategies", "consider",
}

# 4 market conditions for fig1-2
_COND_DEFS = [
    ("Rep\n(No Seller Comm)",
     lambda e: e.startswith("r_wsc_")  and "_F_" in e,
     "#6B6B6B", "Greys"),
    ("Rep\n(Seller Comm)",
     lambda e: e.startswith("r_wsc_")  and "_R_" in e,
     "#52B788", "Greens"),
    ("Rep + Warrant\n(No Seller Comm)",
     lambda e: e.startswith("rw_wsc_") and "_F_" in e,
     "#1565c0", "Blues"),
    ("Rep + Warrant\n(Seller Comm)",
     lambda e: e.startswith("rw_wsc_") and "_R_" in e,
     "#9B2226", "Reds"),
]


def _assign_condition(exp_id: str) -> str:
    for name, mask_fn, _, _ in _COND_DEFS:
        if mask_fn(exp_id):
            return name
    return "Unknown"


def fig1_2_embedding_cluster(data_dir: str, output_dir: Path) -> None:
    """
    UMAP scatter + word clouds organized by 4 market conditions (2x2).

    Left 2/3 of figure: UMAP scatter colored by market condition.
    Right 2x2: one word cloud per condition.
    Embeddings cached to data/case_analysis/post_embeddings_cache.npy.
    """
    try:
        import umap as umap_module
        from wordcloud import WordCloud, STOPWORDS as WC_STOPWORDS
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"  WARNING: Missing package for fig1-2 ({e}). Skipping.")
        return

    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for fig1-2")
        return

    df = pd.DataFrame(posts)
    df["condition"] = df["experiment_id"].apply(_assign_condition)

    # ── Embeddings (with cache) ───────────────────────────────────────────
    cache_path = Path(data_dir) / "case_analysis" / "post_embeddings_cache.npy"
    texts = df["post_content"].tolist()
    embeddings = None

    if cache_path.exists():
        cached = np.load(cache_path)
        if len(cached) == len(texts):
            embeddings = cached

    if embeddings is None:
        print(f"  Computing sentence embeddings for {len(texts)} posts "
              "(first run, ~1-2 min; cached afterwards)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)
        np.save(cache_path, embeddings)
        print("  Embeddings cached.")

    # ── UMAP reduction ────────────────────────────────────────────────────
    print("  Running UMAP dimensionality reduction...")
    reducer = umap_module.UMAP(
        n_components=2, n_neighbors=15, min_dist=0.1,
        metric='cosine', random_state=42
    )
    coords = reducer.fit_transform(embeddings)
    df["ux"] = coords[:, 0]
    df["uy"] = coords[:, 1]

    # ── Figure layout: UMAP left (2 rows × 2 cols), word clouds right 2x2 ──
    fig = plt.figure(figsize=(18, 8))
    gs = fig.add_gridspec(2, 4, wspace=0.40, hspace=0.50)
    ax_scatter = fig.add_subplot(gs[:, :2])

    # Word cloud axes: top-left, top-right, bottom-left, bottom-right
    wc_axes = [
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[0, 3]),
        fig.add_subplot(gs[1, 2]),
        fig.add_subplot(gs[1, 3]),
    ]

    # ── UMAP scatter ─────────────────────────────────────────────────────
    for name, _, color, _ in _COND_DEFS:
        mask = df["condition"] == name
        label_str = name.replace("\n", " ")
        ax_scatter.scatter(
            df.loc[mask, "ux"], df.loc[mask, "uy"],
            c=color, label=f"{label_str} (n={mask.sum()})",
            s=7, alpha=0.5, linewidths=0, rasterized=True
        )

    ax_scatter.set_title(
        "Post Content Embedding Clusters\n(UMAP; colored by Market Condition)",
        fontsize=11, fontweight='bold'
    )
    ax_scatter.set_xlabel("UMAP Dimension 1", fontsize=10)
    ax_scatter.set_ylabel("UMAP Dimension 2", fontsize=10)
    ax_scatter.legend(loc='lower left', fontsize=8, frameon=True,
                      framealpha=0.85, markerscale=3)
    ax_scatter.tick_params(labelsize=8)

    # ── Word Clouds ───────────────────────────────────────────────────────
    stopwords = set(WC_STOPWORDS) | _WC_STOPWORDS_EXTRA

    for ax, (cond_name, _, color, cmap) in zip(wc_axes, _COND_DEFS):
        cond_df = df[df["condition"] == cond_name]
        title_str = cond_name.replace("\n", " ")
        ax.set_title(f"{title_str}\n(n={len(cond_df)})",
                     fontsize=8, fontweight='bold', color=color, pad=3)

        if len(cond_df) < 3:
            ax.axis('off')
            continue

        text_blob = " ".join(cond_df["post_content"].tolist())
        wc = WordCloud(
            width=380, height=180,
            background_color='white',
            stopwords=stopwords,
            colormap=cmap,
            max_words=60,
            prefer_horizontal=0.85,
            collocations=False,
            min_font_size=7,
        )
        wc.generate(text_blob)
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')

    fig.suptitle(
        "Post Content Analysis: Embedding Clusters & Word Frequency by Market Condition",
        fontsize=13, fontweight='bold', y=1.02
    )

    add_sig_footnote(
        fig,
        extra="Embeddings: all-MiniLM-L6-v2; UMAP(neighbors=15, min_dist=0.1, cosine)"
    )
    save_figure(fig, output_dir / "fig1_2_embedding_cluster.png")
    print("  [Fig1-2] Embedding cluster + word clouds saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: Collusion Type Distribution by Mechanism × Communication (4 bars)
# ─────────────────────────────────────────────────────────────────────────────

def fig2_collusion_by_mechanism(data_dir: str, output_dir: Path) -> None:
    """
    Stacked bar chart: 4 groups —
      Rep (No Seller Comm) | Rep (Seller Comm) | Warrant (No Comm) | Warrant (Comm)
    experiment_id pattern: {r|rw}_wsc_{F|R}_* where F=Fake(No Comm), R=Real(Comm)
    """
    df = load_type_distribution_by_condition(data_dir)
    if df.empty:
        print("  WARNING: Empty dataframe for fig2")
        return

    exp_ids = df["experiment_id"].tolist()

    groups = {
        "Rep\n(No Seller Comm)":    [c for c in exp_ids if c.startswith("r_wsc_")  and "_F_" in c],
        "Rep\n(Seller Comm)":       [c for c in exp_ids if c.startswith("r_wsc_")  and "_R_" in c],
        "Warrant\n(No Seller Comm)":[c for c in exp_ids if c.startswith("rw_wsc_") and "_F_" in c],
        "Warrant\n(Seller Comm)":   [c for c in exp_ids if c.startswith("rw_wsc_") and "_R_" in c],
    }

    type_cols = [f"type_{i}" for i in range(1, 7)]

    group_means = {}
    for label, conds in groups.items():
        if conds:
            group_means[label] = df[df["experiment_id"].isin(conds)][type_cols].mean()
        else:
            group_means[label] = pd.Series(np.zeros(6), index=type_cols)

    group_labels = list(group_means.keys())
    n_groups = len(group_labels)
    x_pos = np.arange(n_groups)
    width = 0.55

    fig, ax = plt.subplots(figsize=(11, 5))
    bottom = np.zeros(n_groups)

    for type_id in [1, 2, 3, 4, 5, 6]:
        col = f"type_{type_id}"
        values = np.array([group_means[lab][col] * 100 for lab in group_labels])
        type_info = COLLUSION_TYPES[type_id]

        ax.bar(x_pos, values, width=width, bottom=bottom,
               color=type_info["color"], label=type_info["abbrev"],
               edgecolor="white", linewidth=0.5)

        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 7:
                ax.text(x_pos[i], bot + val / 2, f"{val:.1f}%",
                        ha='center', va='center', fontsize=8,
                        color='white', fontweight='bold')

        bottom = bottom + values

    # Divider between Rep and Warrant groups
    ax.axvline(x=1.5, color='gray', linestyle='--', linewidth=1.0, alpha=0.6)
    ax.text(0.5, 108, "Reputation Only", ha='center', va='center',
            fontsize=9, color='gray', style='italic')
    ax.text(2.5, 108, "Reputation + Warrant", ha='center', va='center',
            fontsize=9, color='gray', style='italic')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(group_labels, fontsize=10)
    ax.set_ylabel("Percentage of Posts (%)", fontsize=11)
    ax.set_title(
        "Collusion Type Distribution by Mechanism and Seller Communication\n"
        "(Seller Comm = sellers allowed to post in shared channel)",
        fontsize=11, fontweight='bold', pad=10
    )
    ax.set_ylim(0, 115)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.13),
              ncol=3, frameon=False, fontsize=9)

    add_sig_footnote(fig, y=-0.20, extra="Types 1-4 = collusive, Type 5 = neutral, Type 6 = anti-collusion")
    save_figure(fig, output_dir / "fig2_collusion_by_mechanism.png")
    print("  [Fig2] Collusion by mechanism (4 groups) saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: Collusion Evolution Over Rounds (two subplots)
# ─────────────────────────────────────────────────────────────────────────────

def fig3_collusion_evolution(data_dir: str, output_dir: Path) -> None:
    """
    Two-panel figure:
    (a) Left: Types 1-4 (collusive messaging) evolution over rounds
    (b) Right: Types 5-6 (neutral / anti-collusion) evolution over rounds
    """
    df = load_type_distribution_by_round(data_dir)
    if df.empty:
        print("  WARNING: Empty dataframe for fig3")
        return

    rounds = df["round"].values

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(14, 5))
    fig.subplots_adjust(wspace=0.30)

    # ── (a) Collusive types 1-4 ───────────────────────────────────────────
    for type_id in [1, 2, 3, 4]:
        col = str(type_id)
        values = df[col].values * 100
        ti = COLLUSION_TYPES[type_id]
        ax_a.plot(rounds, values, color=ti["color"], label=ti["abbrev"],
                  linestyle='-', linewidth=1.5, marker='o', markersize=5,
                  markevery=2)

    ax_a.set_xlabel("Round", fontsize=11)
    ax_a.set_ylabel("Percentage of Posts (%)", fontsize=11)
    ax_a.set_title("(a) Collusive Messaging Evolution\n(Types 1–4)",
                   fontsize=11, fontweight='bold')
    ax_a.set_xticks(rounds)
    ax_a.legend(loc='upper right', frameon=False, fontsize=9)
    ax_a.grid(True, alpha=0.3, linestyle=':')
    ax_a.set_ylim(bottom=0)

    # ── (b) Neutral & Anti-collusion types 5-6 ────────────────────────────
    styles = {5: ('--', 'o'), 6: ('-', 's')}
    for type_id in [5, 6]:
        col = str(type_id)
        values = df[col].values * 100
        ti = COLLUSION_TYPES[type_id]
        ls, mk = styles[type_id]
        ax_b.plot(rounds, values, color=ti["color"], label=ti["abbrev"],
                  linestyle=ls, linewidth=1.8, marker=mk, markersize=5,
                  markevery=2)

    ax_b.set_xlabel("Round", fontsize=11)
    ax_b.set_ylabel("Percentage of Posts (%)", fontsize=11)
    ax_b.set_title("(b) Neutral & Anti-Collusion Evolution\n(Types 5–6)",
                   fontsize=11, fontweight='bold')
    ax_b.set_xticks(rounds)
    ax_b.legend(loc='upper right', frameon=False, fontsize=9)
    ax_b.grid(True, alpha=0.3, linestyle=':')
    ax_b.set_ylim(bottom=0)

    fig.suptitle("Collusion Patterns Evolve Across Rounds",
                 fontsize=13, fontweight='bold', y=1.02)

    add_sig_footnote(fig)
    save_figure(fig, output_dir / "fig3_collusion_evolution.png")
    print("  [Fig3] Collusion evolution (2 subplots) saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1-3: 2x2 Stacked Bar Chart (Communication vs Behavior)
# ─────────────────────────────────────────────────────────────────────────────

def fig1_3_2x2_stacked_bar(data_dir: str, output_dir: Path) -> None:
    """
    Stacked bar chart showing non-honest categories across 4 market conditions.
    
    Categories:
    - Hidden Deception: No collusive post + Deception
    - Verbal Collusion: Collusive post + No deception
    - Coordinated Deception: Collusive post + Deception
    
    4 Market Conditions:
    - Rep (No Comm)
    - Rep + Comm  
    - Rep + Warrant (No Comm)
    - Rep + Warrant + Comm
    """
    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for fig1-3")
        return
    
    df = pd.DataFrame(posts)
    df["post_collusion"] = df["type"].isin([1, 2, 3, 4])
    df["behavior_deception"] = df["deceptive_listing"].astype(bool)
    
    def get_condition_group(exp_id: str) -> str:
        if exp_id.startswith('r_wsc_F_'):
            return 'Rep_NoComm'
        elif exp_id.startswith('r_wsc_R_'):
            return 'Rep_Comm'
        elif exp_id.startswith('rw_wsc_F_'):
            return 'Warrant_NoComm'
        elif exp_id.startswith('rw_wsc_R_'):
            return 'Warrant_Comm'
        return 'Unknown'
    
    def get_2x2_category(row: pd.Series) -> str:
        if not row['post_collusion'] and not row['behavior_deception']:
            return 'Honest'
        elif not row['post_collusion'] and row['behavior_deception']:
            return 'Hidden_Deception'
        elif row['post_collusion'] and not row['behavior_deception']:
            return 'Verbal_Collusion'
        else:
            return 'Coordinated_Deception'
    
    df['condition'] = df['experiment_id'].apply(get_condition_group)
    df['category'] = df.apply(get_2x2_category, axis=1)
    
    # Filter out unknown conditions
    df = df[df['condition'] != 'Unknown']
    
    # Calculate counts per condition
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    categories = ['Hidden_Deception', 'Verbal_Collusion', 'Coordinated_Deception']
    
    # Colors for each category
    cat_colors = {
        'Hidden_Deception': '#9B2226',           # Dark red
        'Verbal_Collusion': '#E07A5F',           # Pink/salmon
        'Coordinated_Deception': '#AE2012',      # Red
    }
    
    # Aggregate data
    data = {cond: {cat: 0 for cat in categories} for cond in conditions}
    for _, row in df.iterrows():
        cond = row['condition']
        cat = row['category']
        if cond in data and cat in data[cond]:
            data[cond][cat] += 1
    
    # Convert to percentages (denominator includes Honest + non-honest)
    totals_all = {
        cond: int((df['condition'] == cond).sum())
        for cond in conditions
    }
    percentages = {}
    for cond in conditions:
        percentages[cond] = {}
        for cat in categories:
            if totals_all[cond] > 0:
                percentages[cond][cat] = (data[cond][cat] / totals_all[cond]) * 100
            else:
                percentages[cond][cat] = 0
    
    # Create stacked bar chart (Honest removed from display, but kept in denominator)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(conditions))
    width = 0.6
    
    # Build stacked bars
    bottom = np.zeros(len(conditions))
    for cat in categories:
        values = [percentages[cond][cat] for cond in conditions]
        bars = ax.bar(x, values, width, label=cat, bottom=bottom, 
                      color=cat_colors[cat], edgecolor='white', linewidth=0.5)
        
        # Add text labels on bars if segment is large enough
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val >= 5:  # Only show label if segment >= 5%
                ax.text(x[i], bot + val/2, f'{val:.1f}%',
                       ha='center', va='center', fontsize=8, 
                       color='white', fontweight='bold')
        
        bottom += values
    
    # Formatting
    ax.set_xlabel('Market Condition', fontsize=12)
    ax.set_ylabel('Percentage of Posts (%)', fontsize=12)
    ax.set_title('Deception Categories by Market Condition\n(Honest Removed)',
                 fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Rep\n(No Comm)', 'Rep\n(Comm)', 
                        'Rep + Warrant\n(No Comm)', 'Rep + Warrant\n(Comm)'],
                       fontsize=10)
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    max_stack = float(np.max(bottom)) if len(bottom) > 0 else 0.0
    y_top = max(10.0, max_stack * 1.15)
    y_bottom = -max(2.0, y_top * 0.08)
    ax.set_ylim(y_bottom, y_top)
    ax.grid(True, axis='y', alpha=0.3, linestyle=':')
    
    # Add sample size annotations (all posts, including Honest)
    for i, cond in enumerate(conditions):
        ax.text(x[i], y_bottom * 0.55, f'n={totals_all[cond]}',
               ha='center', va='top', fontsize=8, color='gray')
    
    plt.tight_layout()
    save_figure(fig, output_dir / "fig1_3_2x2_stacked_bar.png")
    print("  [Fig1-3] 2x2 Stacked bar chart saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate collusion analysis visualizations"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory containing case_analysis/"
    )
    parser.add_argument(
        "--output-dir",
        default="visualization/figs/paper/collusion_analysis",
        help="Output directory for figures"
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="Skip fig1-2 (embedding + word cloud) — useful for quick iteration"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Run legacy multi-figure suite instead of the focused Rep vs Rep+Warrant figure"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Collusion Analysis Visualization Generator")
    print("=" * 70)
    print(f"\nData directory: {args.data_dir}")
    print(f"Output directory: {output_dir}")

    if args.legacy:
        print("\n[Fig1] Deception Rate by Collusion Status...")
        fig1_deception_by_collusion(args.data_dir, output_dir)

        print("\n[Fig1-1] Sankey: Post Collusion → Behavior Deception by Condition...")
        fig1_1_sankey_by_condition(args.data_dir, output_dir)

        if not args.skip_embedding:
            print("\n[Fig1-2] Embedding Cluster + Word Clouds (4 categories)...")
            fig1_2_embedding_cluster(args.data_dir, output_dir)
        else:
            print("\n[Fig1-2] Skipped (--skip-embedding).")

        print("\n[Fig1-3] 2x2 Stacked Bar: Communication vs Behavior...")
        fig1_3_2x2_stacked_bar(args.data_dir, output_dir)

        print("\n[Fig2] Collusion by Mechanism × Communication (4 groups)...")
        fig2_collusion_by_mechanism(args.data_dir, output_dir)

        print("\n[Fig3] Collusion Evolution Over Rounds (2 subplots)...")
        fig3_collusion_evolution(args.data_dir, output_dir)
    else:
        print("\n[Fig-Collusion] Rep vs Rep+Warrant: consistency + 4-way categories...")
        fig_collusion_behavior_consistency(args.data_dir, output_dir)
        print("\n[Scheme1] Time series + lag correlation...")
        fig_scheme1_time_series_and_lag(args.data_dir, output_dir)
        print("\n[Scheme2] Agent scatter + quartile boxplot...")
        fig_scheme2_agent_scatter_and_quartile(args.data_dir, output_dir)
        print("\n[Scheme3] Keywords + embedding map...")
        fig_scheme3_keywords_and_embedding(args.data_dir, output_dir)
        print("\n[Scheme4] Topic share + fraud rate...")
        fig_scheme4_topics_and_fraud(args.data_dir, output_dir)
        print("\n[Scheme5] Mosaic + sankey...")
        fig_scheme5_mosaic_and_sankey(args.data_dir, output_dir)

    print("\n" + "=" * 70)
    print(f"All figures saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
