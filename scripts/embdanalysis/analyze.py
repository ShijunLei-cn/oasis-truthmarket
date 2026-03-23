"""
Embedding analysis of LLM action_reasoning from experiment action logs.

Usage:
    python analyze.py <actions_json_file> [options]

Examples:
    python analyze.py experiments/gpt-4o-mini/paper/rq2/r_wsc_R_pressure_quickprofits/run_1_actions.json
    python analyze.py experiments/gpt-4o-mini/paper/rq2/r_wsc_R_pressure_quickprofits/run_1_actions.json \
        --n-clusters 5 --output-dir output/
"""

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from umap import UMAP


# ──────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────

@dataclass
class ReasoningRecord:
    round: int
    phase: Optional[str]
    agent_id: int
    agent_name: str
    action_name: str
    action_reasoning: str


def load_reasoning_records(json_path: str) -> list[ReasoningRecord]:
    with open(json_path) as f:
        data = json.load(f)

    records: list[ReasoningRecord] = []
    for item in data:
        if "agent_infos" not in item:
            continue
        round_num = item.get("round", -1)
        phase = item.get("phase")
        for agent_info in item["agent_infos"]:
            aai = agent_info.get("agent_action_info", {})
            reasoning = aai.get("action_reasoning", "")
            if not reasoning:
                continue
            records.append(
                ReasoningRecord(
                    round=round_num,
                    phase=phase,
                    agent_id=agent_info.get("agent_id", -1),
                    agent_name=agent_info.get("agent_name", "unknown"),
                    action_name=aai.get("action_name", "unknown"),
                    action_reasoning=reasoning,
                )
            )
    return records


# ──────────────────────────────────────────────
# Embedding
# ──────────────────────────────────────────────

def compute_embeddings(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    print(f"Computing embeddings with '{model_name}' for {len(texts)} texts...")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings


# ──────────────────────────────────────────────
# Dimensionality reduction
# ──────────────────────────────────────────────

def reduce_pca(embeddings: np.ndarray, n_components: int = 2) -> np.ndarray:
    return PCA(n_components=n_components, random_state=42).fit_transform(embeddings)


def reduce_tsne(embeddings: np.ndarray, n_components: int = 2, perplexity: float = 30.0) -> np.ndarray:
    perplexity = min(perplexity, len(embeddings) - 1)
    return TSNE(n_components=n_components, perplexity=perplexity, random_state=42, init="pca").fit_transform(embeddings)


def reduce_umap(embeddings: np.ndarray, n_components: int = 2) -> np.ndarray:
    n_neighbors = min(15, len(embeddings) - 1)
    return UMAP(n_components=n_components, n_neighbors=n_neighbors, random_state=42).fit_transform(embeddings)


# ──────────────────────────────────────────────
# Clustering
# ──────────────────────────────────────────────

def auto_select_k(embeddings: np.ndarray, k_range: range = range(2, 11)) -> int:
    """Select k using silhouette score."""
    if len(embeddings) <= 2:
        return 2
    k_range = [k for k in k_range if k < len(embeddings)]
    scores = []
    for k in k_range:
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(embeddings)
        scores.append(silhouette_score(embeddings, labels))
    best_k = k_range[int(np.argmax(scores))]
    print(f"Silhouette scores: { {k: round(s, 3) for k, s in zip(k_range, scores)} }")
    print(f"Auto-selected k={best_k}")
    return best_k


def cluster_kmeans(embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
    return KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(embeddings)


# ──────────────────────────────────────────────
# Visualization
# ──────────────────────────────────────────────

REDUCTION_METHODS = {"pca": reduce_pca, "tsne": reduce_tsne, "umap": reduce_umap}


def _base_scatter(
    coords: np.ndarray,
    color_values,
    title: str,
    xlabel: str,
    ylabel: str,
    cmap,
    legend_handles=None,
    colorbar_label: Optional[str] = None,
    ax=None,
):
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=color_values, cmap=cmap, alpha=0.7, s=40)
    if colorbar_label is not None:
        plt.colorbar(sc, ax=ax, label=colorbar_label)
    if legend_handles:
        ax.legend(handles=legend_handles, loc="best", fontsize=8, title="Cluster")
    ax.set_title(title, fontsize=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    if standalone:
        plt.tight_layout()
    return ax


def plot_clusters(
    coords: np.ndarray,
    labels: np.ndarray,
    records: list[ReasoningRecord],
    method: str,
    output_path: str,
):
    n_clusters = len(set(labels))
    cmap = matplotlib.colormaps.get_cmap("tab10").resampled(n_clusters)
    colors = [cmap(l) for l in labels]

    from matplotlib.patches import Patch
    legend_handles = [Patch(color=cmap(k), label=f"Cluster {k}") for k in range(n_clusters)]

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(coords[:, 0], coords[:, 1], c=labels, cmap="tab10", vmin=0, vmax=n_clusters - 1, alpha=0.7, s=40)
    ax.legend(handles=legend_handles, loc="best", fontsize=8, title="Cluster")
    ax.set_title(f"Cluster Analysis ({method.upper()}) — {n_clusters} clusters", fontsize=13)
    ax.set_xlabel(f"{method.upper()} dim 1")
    ax.set_ylabel(f"{method.upper()} dim 2")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved cluster plot: {output_path}")


def plot_by_round(
    coords: np.ndarray,
    records: list[ReasoningRecord],
    method: str,
    output_path: str,
):
    rounds = np.array([r.round for r in records])
    fig, ax = plt.subplots(figsize=(9, 7))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=rounds, cmap="viridis", alpha=0.7, s=40)
    plt.colorbar(sc, ax=ax, label="Round")
    ax.set_title(f"Action Reasoning by Round ({method.upper()})", fontsize=13)
    ax.set_xlabel(f"{method.upper()} dim 1")
    ax.set_ylabel(f"{method.upper()} dim 2")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved round plot: {output_path}")


def plot_by_agent(
    coords: np.ndarray,
    records: list[ReasoningRecord],
    method: str,
    output_path: str,
):
    agent_names = sorted(set(r.agent_name for r in records))
    agent_to_idx = {name: i for i, name in enumerate(agent_names)}
    agent_ids = np.array([agent_to_idx[r.agent_name] for r in records])
    n_agents = len(agent_names)
    cmap = matplotlib.colormaps.get_cmap("tab20").resampled(n_agents)

    from matplotlib.patches import Patch
    legend_handles = [Patch(color=cmap(i), label=name) for i, name in enumerate(agent_names)]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(coords[:, 0], coords[:, 1], c=agent_ids, cmap="tab20", vmin=0, vmax=n_agents - 1, alpha=0.7, s=40)
    ax.legend(handles=legend_handles, loc="best", fontsize=7, title="Agent", ncol=2)
    ax.set_title(f"Action Reasoning by Agent ({method.upper()})", fontsize=13)
    ax.set_xlabel(f"{method.upper()} dim 1")
    ax.set_ylabel(f"{method.upper()} dim 2")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved agent plot: {output_path}")


def plot_by_action(
    coords: np.ndarray,
    records: list[ReasoningRecord],
    method: str,
    output_path: str,
):
    action_names = sorted(set(r.action_name for r in records))
    action_to_idx = {name: i for i, name in enumerate(action_names)}
    action_ids = np.array([action_to_idx[r.action_name] for r in records])
    n_actions = len(action_names)
    cmap = matplotlib.colormaps.get_cmap("Set1").resampled(n_actions)

    from matplotlib.patches import Patch
    legend_handles = [Patch(color=cmap(i), label=name) for i, name in enumerate(action_names)]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(coords[:, 0], coords[:, 1], c=action_ids, cmap="Set1", vmin=0, vmax=n_actions - 1, alpha=0.7, s=40)
    ax.legend(handles=legend_handles, loc="best", fontsize=8, title="Action")
    ax.set_title(f"Action Reasoning by Action Type ({method.upper()})", fontsize=13)
    ax.set_xlabel(f"{method.upper()} dim 1")
    ax.set_ylabel(f"{method.upper()} dim 2")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved action plot: {output_path}")


def plot_silhouette_curve(embeddings: np.ndarray, output_path: str, k_range: range = range(2, 11)):
    k_range = [k for k in k_range if k < len(embeddings)]
    scores = []
    for k in k_range:
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(embeddings)
        scores.append(silhouette_score(embeddings, labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(k_range, scores, marker="o")
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Silhouette Score vs. Number of Clusters")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved silhouette plot: {output_path}")


def save_cluster_summary(records: list[ReasoningRecord], labels: np.ndarray, output_path: str):
    from collections import Counter
    cluster_info: dict[int, list] = {}
    for rec, label in zip(records, labels):
        cluster_info.setdefault(int(label), []).append(rec)

    lines = []
    for cluster_id in sorted(cluster_info.keys()):
        recs = cluster_info[cluster_id]
        actions = Counter(r.action_name for r in recs)
        agents = Counter(r.agent_name for r in recs)
        rounds = [r.round for r in recs]
        lines.append(f"=== Cluster {cluster_id} ({len(recs)} records) ===")
        lines.append(f"  Rounds: {min(rounds)}–{max(rounds)}")
        lines.append(f"  Actions: {dict(actions)}")
        lines.append(f"  Agents: {dict(agents)}")
        lines.append(f"  Sample reasoning (truncated):")
        for rec in recs[:3]:
            snippet = rec.action_reasoning.replace("\n", " ")[:150]
            lines.append(f"    [{rec.agent_name} r{rec.round}] {snippet}...")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Saved cluster summary: {output_path}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Embedding analysis of action_reasoning from experiment logs.")
    parser.add_argument("json_file", help="Path to run_*_actions.json")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--methods", nargs="+", default=["pca", "tsne", "umap"],
                        choices=["pca", "tsne", "umap"], help="Dimensionality reduction methods")
    parser.add_argument("--n-clusters", type=int, default=None,
                        help="Number of clusters (auto-selected via silhouette if not set)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: alongside json file)")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    output_dir = Path(args.output_dir) if args.output_dir else json_path.parent / "embd_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    records = load_reasoning_records(str(json_path))
    if not records:
        print("No action_reasoning records found.")
        return
    print(f"Loaded {len(records)} reasoning records from {json_path.name}")

    texts = [r.action_reasoning for r in records]

    # Embed
    embeddings = compute_embeddings(texts, model_name=args.model)

    # Cluster
    plot_silhouette_curve(embeddings, str(output_dir / "silhouette_curve.png"))
    n_clusters = args.n_clusters if args.n_clusters else auto_select_k(embeddings)
    labels = cluster_kmeans(embeddings, n_clusters)
    save_cluster_summary(records, labels, str(output_dir / "cluster_summary.txt"))

    # Visualize with each reduction method
    for method in args.methods:
        print(f"\nReducing with {method.upper()}...")
        reducer = REDUCTION_METHODS[method]
        coords = reducer(embeddings)

        plot_clusters(coords, labels, records, method, str(output_dir / f"clusters_{method}.png"))
        plot_by_round(coords, records, method, str(output_dir / f"by_round_{method}.png"))
        plot_by_agent(coords, records, method, str(output_dir / f"by_agent_{method}.png"))
        plot_by_action(coords, records, method, str(output_dir / f"by_action_{method}.png"))

    print(f"\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
