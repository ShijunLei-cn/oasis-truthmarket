#!/usr/bin/env python3
"""
Shared data loading and statistics helpers for paper tables/visualizations.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List
import json
import pandas as pd


def load_results(
    experiment_dir: str,
    pattern: str = "run_*_results.json",
    run_id_suffix: str = "_results",
    description: str = "result"
) -> pd.DataFrame:
    """Load experiment result files with a consistent pattern and add run_id."""
    path = Path(experiment_dir)
    all_results: List[Dict[str, Any]] = []

    if not path.exists():
        print(f"ERROR: {description} directory does not exist: {experiment_dir}")
        return pd.DataFrame()

    result_files = list(path.glob(pattern))
    if not result_files:
        print(f"ERROR: No {description} files found in {experiment_dir}")
        return pd.DataFrame()

    print(f"Found {len(result_files)} {description} files")
    for file in result_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data:
                    print(f"  Warning: {file.name} is empty")
                    continue
                run_id = file.stem.replace(run_id_suffix, "").replace("run_", "")
                for item in data:
                    item["run_id"] = run_id
                all_results.extend(data)
                print(f"  Loaded {len(data)} results from {file.name}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  ERROR loading {file.name}: {exc}")

    if not all_results:
        print(f"ERROR: No {description} data loaded")
        return pd.DataFrame()

    return pd.DataFrame(all_results)


def aggregate_stats(stat_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate mean and std for a list of per-run statistics."""
    if not stat_rows:
        return {}

    stats_df = pd.DataFrame(stat_rows)
    if stats_df.empty:
        return {}

    aggregated: Dict[str, float] = {}
    for col in stats_df.columns:
        aggregated[col] = float(stats_df[col].mean())
        aggregated[f"{col}_std"] = float(stats_df[col].std())
    return aggregated


def aggregate_by_run(
    df: pd.DataFrame,
    run_stats_fn: Callable[[pd.DataFrame], Dict[str, float]]
) -> Dict[str, float]:
    """
    Compute metrics for each run_id, then return overall mean/std.
    """
    if df.empty or "run_id" not in df.columns:
        return {}

    per_run_stats: List[Dict[str, float]] = []
    for run_id in df["run_id"].unique():
        run_df = df[df["run_id"] == run_id]
        stats = run_stats_fn(run_df)
        if stats:
            per_run_stats.append(stats)

    return aggregate_stats(per_run_stats)


def market_run_stats(run_df: pd.DataFrame) -> Dict[str, float]:
    """Core market metrics (transactions, profits, utilities, reputation)."""
    # Reputation: use mean rating (0-5) scaled to 0-50 to match paper scale;
    # fall back to sellers' final reputation mean if rating is absent.
    if "rating" in run_df.columns:
        reputation_by_seller = run_df["rating"].mean() * 10
    else:
        reputation_by_seller = (
            run_df.groupby("seller_id")["reputation"].last().mean()
            if "seller_id" in run_df.columns and not run_df.empty
            else run_df["reputation"].mean()
        )
    return {
        "transactions": run_df["transactions"].sum(),
        "seller_profit": run_df["seller_profit"].sum(),
        "buyer_utility": run_df["buyer_utility"].sum(),
        "reputation": reputation_by_seller,
    }


def market_run_stats_with_deceptions(run_df: pd.DataFrame) -> Dict[str, float]:
    """Market metrics plus deception count."""
    stats = market_run_stats(run_df)
    stats["deceptions"] = (run_df["is_honest"] == False).sum()  # noqa: E712
    return stats


def market_run_stats_with_breakdown(run_df: pd.DataFrame) -> Dict[str, float]:
    """Market metrics with honest/dishonest profit breakdown and totals."""
    stats = market_run_stats_with_deceptions(run_df)
    stats["honest_profit"] = run_df[run_df["is_honest"] == True]["seller_profit"].sum()  # noqa: E712
    stats["dishonest_profit"] = run_df[run_df["is_honest"] == False]["seller_profit"].sum()  # noqa: E712
    stats["total_profit"] = stats["honest_profit"] + stats["dishonest_profit"]
    return stats


def product_quality_run_stats(run_df: pd.DataFrame) -> Dict[str, float]:
    """Count products by quality/authenticity."""
    return {
        "hq_authentic_on_sale": len(run_df[(run_df["quality"] == "HQ") & (run_df["is_authentic"] == True)]),  # noqa: E712
        "hq_authentic_sold": len(run_df[(run_df["quality"] == "HQ") & (run_df["is_authentic"] == True) & (run_df["sold"] == True)]),  # noqa: E712
        "lq_authentic_on_sale": len(run_df[(run_df["quality"] == "LQ") & (run_df["is_authentic"] == True)]),  # noqa: E712
        "lq_authentic_sold": len(run_df[(run_df["quality"] == "LQ") & (run_df["is_authentic"] == True) & (run_df["sold"] == True)]),  # noqa: E712
        "hq_counterfeit_on_sale": len(run_df[(run_df["quality"] == "HQ") & (run_df["is_authentic"] == False)]),  # noqa: E712
        "hq_counterfeit_sold": len(run_df[(run_df["quality"] == "HQ") & (run_df["is_authentic"] == False) & (run_df["sold"] == True)]),  # noqa: E712
    }
