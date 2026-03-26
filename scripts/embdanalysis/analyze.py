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

import json

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
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
# Clustering Metrics
# ──────────────────────────────────────────────

def compute_cluster_metrics(embeddings: np.ndarray, labels: np.ndarray) -> dict:
    """
    Compute quantitative clustering quality metrics for reporting in papers:

    Global:
      - Silhouette Score        [-1, 1]  higher = better separated
      - Davies-Bouldin Index    [0, ∞)   lower  = better separated
      - Calinski-Harabasz Index [0, ∞)   higher = better separated
      - Mean intra-cluster dist          lower  = more cohesive
      - Mean inter-cluster dist          higher = better separated

    Per-cluster:
      - N points
      - Mean / std distance to centroid  (intra-cluster cohesion)
      - Mean silhouette coefficient

    Inter-cluster:
      - Full pairwise centroid distance matrix
    """
    n_clusters = len(set(labels))

    # Global scores
    sil_global = silhouette_score(embeddings, labels)
    dbi = davies_bouldin_score(embeddings, labels)
    chi = calinski_harabasz_score(embeddings, labels)

    # Per-sample silhouette for per-cluster breakdown
    sil_per_sample = silhouette_samples(embeddings, labels)

    # Centroids
    centroids = np.array([
        embeddings[labels == k].mean(axis=0) for k in range(n_clusters)
    ])

    # Intra-cluster: mean / std distance of each point to its centroid
    per_cluster: dict[int, dict] = {}
    mean_intra_list = []
    for k in range(n_clusters):
        mask = labels == k
        pts = embeddings[mask]
        dists = np.linalg.norm(pts - centroids[k], axis=1)
        per_cluster[k] = {
            "n_points": int(mask.sum()),
            "mean_dist_to_centroid": float(dists.mean()),
            "std_dist_to_centroid": float(dists.std()),
            "mean_silhouette": float(sil_per_sample[mask].mean()),
        }
        mean_intra_list.append(float(dists.mean()))

    # Inter-cluster: full pairwise centroid distance matrix
    centroid_dist_matrix = cdist(centroids, centroids, metric="euclidean")
    inter_pairs: dict[str, float] = {}
    for i in range(n_clusters):
        for j in range(i + 1, n_clusters):
            inter_pairs[f"{i}-{j}"] = float(centroid_dist_matrix[i, j])

    off_diag = centroid_dist_matrix[~np.eye(n_clusters, dtype=bool)]
    mean_inter = float(off_diag.mean())

    return {
        "n_clusters": n_clusters,
        "n_points": int(len(labels)),
        "global": {
            "silhouette_score": round(sil_global, 4),
            "davies_bouldin_index": round(dbi, 4),
            "calinski_harabasz_index": round(chi, 2),
            "mean_intra_cluster_dist": round(float(np.mean(mean_intra_list)), 4),
            "mean_inter_cluster_dist": round(mean_inter, 4),
        },
        "per_cluster": per_cluster,
        "inter_cluster_pairs": inter_pairs,
        "centroid_distance_matrix": centroid_dist_matrix.round(4).tolist(),
    }


def save_cluster_metrics(metrics: dict, output_dir: "Path") -> None:
    """Save metrics as machine-readable JSON and a human-readable text report."""
    # JSON
    with open(output_dir / "cluster_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Text report
    g = metrics["global"]
    lines = [
        "=" * 62,
        "CLUSTERING QUALITY METRICS",
        "=" * 62,
        f"  k = {metrics['n_clusters']} clusters   |   n = {metrics['n_points']} points",
        "",
        "── Global ──────────────────────────────────────────────────",
        f"  Silhouette Score        : {g['silhouette_score']:+.4f}   (range [-1,1]; ↑ better)",
        f"  Davies-Bouldin Index    : {g['davies_bouldin_index']:.4f}    (≥0; ↓ better)",
        f"  Calinski-Harabasz Index : {g['calinski_harabasz_index']:.2f}   (≥0; ↑ better)",
        f"  Mean intra-cluster ‖d‖  : {g['mean_intra_cluster_dist']:.4f}   (↓ = more cohesive)",
        f"  Mean inter-cluster ‖d‖  : {g['mean_inter_cluster_dist']:.4f}   (↑ = better separated)",
        "",
        "── Per-cluster ─────────────────────────────────────────────",
        f"  {'Cluster':>8}  {'N':>6}  {'Intra ‖d‖ mean':>16}  {'±std':>8}  {'Silhouette':>12}",
    ]
    for k, v in metrics["per_cluster"].items():
        lines.append(
            f"  {k:>8}  {v['n_points']:>6}"
            f"  {v['mean_dist_to_centroid']:>16.4f}"
            f"  {v['std_dist_to_centroid']:>8.4f}"
            f"  {v['mean_silhouette']:>+12.4f}"
        )

    lines += [
        "",
        "── Inter-cluster Centroid Distance Matrix ───────────────────",
    ]
    mat = np.array(metrics["centroid_distance_matrix"])
    n = len(mat)
    lines.append("        " + "".join(f"  C{j:>3}" for j in range(n)))
    for i in range(n):
        row = f"  C{i:>3}  " + "".join(f"  {mat[i, j]:>5.3f}" for j in range(n))
        lines.append(row)
    lines.append("")

    with open(output_dir / "cluster_metrics_report.txt", "w") as f:
        f.write("\n".join(lines))

    print(f"Saved cluster_metrics.json")
    print(f"Saved cluster_metrics_report.txt")


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


def plot_intercluster_heatmap(metrics: dict, output_path: str) -> None:
    """Heatmap of pairwise centroid distances — visualises inter-cluster separation."""
    mat = np.array(metrics["centroid_distance_matrix"])
    n = len(mat)
    fig, ax = plt.subplots(figsize=(max(5, n + 1), max(4, n)))
    im = ax.imshow(mat, cmap="coolwarm_r", aspect="auto")
    plt.colorbar(im, ax=ax, label="Euclidean Distance Between Centroids")
    ax.set_xticks(range(n))
    ax.set_xticklabels([f"C{i}" for i in range(n)])
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"C{i}" for i in range(n)])
    for i in range(n):
        for j in range(n):
            val = mat[i, j]
            color = "white" if val > mat.max() * 0.65 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=9, color=color)
    ax.set_title(f"Inter-cluster Centroid Distance Heatmap ({n} clusters)", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved heatmap: {output_path}")


def plot_silhouette_bars(embeddings: np.ndarray, labels: np.ndarray, output_path: str) -> None:
    """
    Silhouette coefficient plot per cluster (sorted within each cluster).
    Equivalent to the canonical sklearn silhouette visualisation; useful for
    identifying which clusters are well-separated vs. overlapping.
    """
    sil_vals = silhouette_samples(embeddings, labels)
    n_clusters = len(set(labels))
    cmap = matplotlib.colormaps.get_cmap("tab10")

    fig, ax = plt.subplots(figsize=(9, 5))
    y_lower = 10
    for k in range(n_clusters):
        cluster_sil = np.sort(sil_vals[labels == k])
        y_upper = y_lower + len(cluster_sil)
        ax.fill_betweenx(
            np.arange(y_lower, y_upper), 0, cluster_sil,
            facecolor=cmap(k), edgecolor=cmap(k), alpha=0.7,
        )
        ax.text(-0.06, (y_lower + y_upper) / 2, f"C{k}", fontsize=9, va="center")
        y_lower = y_upper + 10

    mean_sil = sil_vals.mean()
    ax.axvline(mean_sil, color="red", linestyle="--", linewidth=1.5,
               label=f"Mean = {mean_sil:.3f}")
    ax.set_xlabel("Silhouette Coefficient")
    ax.set_ylabel("Cluster")
    ax.set_title(f"Per-cluster Silhouette Coefficients ({n_clusters} clusters)", fontsize=12)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved silhouette bar plot: {output_path}")


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
    parser.add_argument("--action-types", nargs="+", default=None,
                        metavar="ACTION",
                        help="Restrict analysis to these action_name values "
                             "(e.g. --action-types list_products create_post). "
                             "Pass 'list' to print available types and exit.")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: alongside json file)")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    # Load data
    records = load_reasoning_records(str(json_path))
    if not records:
        print("No action_reasoning records found.")
        return

    # --action-types list: print available types and exit
    if args.action_types and args.action_types == ["list"]:
        available = sorted(set(r.action_name for r in records))
        print("Available action types in this file:")
        for a in available:
            count = sum(1 for r in records if r.action_name == a)
            print(f"  {a:30s}  ({count} records)")
        return

    # Filter by action type(s)
    if args.action_types:
        requested = set(args.action_types)
        available = set(r.action_name for r in records)
        unknown = requested - available
        if unknown:
            print(f"WARNING: unknown action type(s) ignored: {unknown}")
            print(f"  Available: {sorted(available)}")
        records = [r for r in records if r.action_name in requested]
        if not records:
            print("No records remain after action-type filter.")
            return
        print(f"Filtered to action_types={sorted(requested & available)}: "
              f"{len(records)} records remain")

    print(f"Loaded {len(records)} reasoning records from {json_path.name}")

    # Output dir — append action-type suffix when filtering, to keep analyses separate
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        base = json_path.parent / "embd_analysis"
        if args.action_types:
            suffix = "+".join(sorted(args.action_types))
            output_dir = base / suffix
        else:
            output_dir = base
    output_dir.mkdir(parents=True, exist_ok=True)

    texts = [r.action_reasoning for r in records]

    # Embed
    embeddings = compute_embeddings(texts, model_name=args.model)

    # Cluster
    plot_silhouette_curve(embeddings, str(output_dir / "silhouette_curve.png"))
    n_clusters = args.n_clusters if args.n_clusters else auto_select_k(embeddings)
    labels = cluster_kmeans(embeddings, n_clusters)
    save_cluster_summary(records, labels, str(output_dir / "cluster_summary.txt"))

    # Quantitative metrics (intra/inter-cluster distances, silhouette, DBI, CHI)
    print("\nComputing cluster quality metrics...")
    metrics = compute_cluster_metrics(embeddings, labels)
    save_cluster_metrics(metrics, output_dir)
    plot_intercluster_heatmap(metrics, str(output_dir / "intercluster_heatmap.png"))
    plot_silhouette_bars(embeddings, labels, str(output_dir / "silhouette_bars.png"))

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
