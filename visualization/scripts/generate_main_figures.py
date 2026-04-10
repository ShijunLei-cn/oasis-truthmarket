#!/usr/bin/env python3
"""
Unified figure generator for the new 3-RQ framing.

RQ1: Vulnerability intention in reputation-only market
RQ2: Warrant welfare (rep vs rep+warrant, no communication)
RQ3: Communication interference & resistance (seller-communication constraints)
"""

import argparse
from pathlib import Path

from generate_rq1_figures import (
    fig1_2_manipulation_detection_rep_only,
    fig1_profit_and_deceptions,
    fig1_1_manipulation_detection,
    fig2_probe_and_product_mix,
)
from generate_rq2_figures import (
    fig4_deception_by_constraint,
    fig5_profit_decomposition,
    fig6_product_mix,
    fig7_buyer_utility_by_constraint,
    fig_all_constraints_summary,
    fig_rq2_all_markettype_dual_metrics,
)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.write_bytes(src.read_bytes())
        print(f"✓ Saved: {dst}")


def generate_rq1(base_dir: Path, output_dir: Path) -> None:
    r_dir = base_dir / "rq1_intent" / "r_wo"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig1_2_manipulation_detection_rep_only(str(r_dir), output_dir)
    _copy_if_exists(
        output_dir / "rq1_2_rep_only_manipulation_detection.png",
        output_dir / "rq1_intent_rep_only_manipulation_detection.png",
    )


def generate_rq2(base_dir: Path, output_dir: Path) -> None:
    r_dir = base_dir / "rq2_welfare" / "r_wo"
    rw_dir = base_dir / "rq2_welfare" / "rw_wo"
    output_dir.mkdir(parents=True, exist_ok=True)

    fig1_profit_and_deceptions(str(r_dir), str(rw_dir), output_dir)
    fig1_1_manipulation_detection(str(r_dir), str(rw_dir), output_dir)
    fig2_probe_and_product_mix(str(r_dir), str(rw_dir), output_dir)

    for src in output_dir.glob("rq1_*.png"):
        dst = src.with_name(src.name.replace("rq1_", "rq2_", 1))
        _copy_if_exists(src, dst)


def generate_rq3(base_dir: Path, output_dir: Path) -> None:
    rq3_base = base_dir / "rq3_resilience"
    baseline = base_dir / "rq2_welfare"
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = "rq3"

    fig4_deception_by_constraint(str(rq3_base), output_dir, file_prefix=prefix)
    fig5_profit_decomposition(str(rq3_base), output_dir, file_prefix=prefix)
    fig6_product_mix(str(rq3_base), output_dir, file_prefix=prefix)
    fig7_buyer_utility_by_constraint(str(rq3_base), output_dir, file_prefix=prefix)
    fig_all_constraints_summary(str(rq3_base), output_dir, file_prefix=prefix)
    fig_rq2_all_markettype_dual_metrics(
        str(rq3_base),
        output_dir,
        file_prefix=prefix,
        baseline_dir=str(baseline),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all figures for new 3-RQ framing")
    parser.add_argument("--base-dir", required=True, help="Base experiment dir")
    parser.add_argument("--output-dir", required=True, help="Base output dir")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Preflight check for new 3-RQ directory layout.
    required_dirs = [
        base_dir / "rq1_intent" / "r_wo",
        base_dir / "rq2_welfare" / "r_wo",
        base_dir / "rq2_welfare" / "rw_wo",
        base_dir / "rq3_resilience",
    ]
    missing = [str(p) for p in required_dirs if not p.exists()]
    if len(missing) == len(required_dirs):
        raise SystemExit(
            "No compatible experiment data found for new 3-RQ layout.\n"
            + "\n".join(f"- {m}" for m in missing)
        )

    print("Generating RQ1 figures...")
    if (base_dir / "rq1_intent" / "r_wo").exists():
        generate_rq1(base_dir, output_dir / "rq1")
    else:
        print("Skip RQ1: missing rq1_intent/r_wo")
    print("Generating RQ2 figures...")
    if (base_dir / "rq2_welfare" / "r_wo").exists() and (base_dir / "rq2_welfare" / "rw_wo").exists():
        generate_rq2(base_dir, output_dir / "rq2")
    else:
        print("Skip RQ2: missing rq2_welfare baseline dirs")
    print("Generating RQ3 figures...")
    if (base_dir / "rq3_resilience").exists():
        generate_rq3(base_dir, output_dir / "rq3")
    else:
        print("Skip RQ3: missing rq3_resilience")
    print(f"✓ All figures saved to: {output_dir}")


if __name__ == "__main__":
    main()
