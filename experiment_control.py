"""Pure helpers for safe, reproducible market experiment execution."""

from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


_SENSITIVE_KEY_FRAGMENTS = ("api_key", "token", "secret", "password", ".env")


def apply_cli_overrides(
    config: type,
    *,
    model_platform: str | None = None,
    model_type: str | None = None,
    runs: int | None = None,
) -> None:
    """Apply explicit CLI values after YAML has been loaded."""
    if model_platform is not None:
        config.MODEL_PLATFORM = model_platform
    if model_type is not None:
        config.MODEL_TYPE = model_type
    if runs is not None:
        if runs < 1:
            raise ValueError("runs must be a positive integer")
        config.RUNS = runs


def parse_seed_list(raw: str | None, run_count: int) -> list[int]:
    """Parse a comma-separated seed list and require one seed per run."""
    if run_count < 1:
        raise ValueError("run_count must be a positive integer")
    if raw is None:
        raise ValueError(f"exactly {run_count} seeds are required")
    try:
        seeds = [int(value.strip()) for value in raw.split(",") if value.strip()]
    except ValueError as exc:
        raise ValueError("seeds must be comma-separated integers") from exc
    if len(seeds) != run_count:
        raise ValueError(f"exactly {run_count} seeds are required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be unique within an experiment condition")
    return seeds


def seed_simulator(seed: int) -> None:
    """Seed simulator-side random generators; provider nondeterminism may remain."""
    random.seed(seed)
    try:
        import numpy as np
    except ImportError:
        return
    np.random.seed(seed % (2**32))


def reserve_experiment_directory(path: str | Path) -> Path:
    """Create a fresh experiment directory and refuse all existing targets."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(exist_ok=False)
    return target


def safe_experiment_path(base: str | Path, experiment_id: str) -> Path:
    """Resolve a nested experiment ID without allowing traversal outside base."""
    relative = Path(experiment_id)
    if not experiment_id.strip() or relative.is_absolute():
        raise ValueError("experiment_id must be a non-empty relative path")
    if any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError("experiment_id contains an unsafe path component")
    return Path(base) / relative


def write_json_exclusive(path: str | Path, payload: Any) -> None:
    """Write JSON once without permitting accidental overwrite."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_json_atomic(path: str | Path, payload: Any) -> None:
    """Atomically replace a mutable JSON status artifact."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def copy_file_exclusive(source: str | Path, target: str | Path) -> None:
    """Copy an input snapshot once without permitting overwrite."""
    source_path = Path(source)
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with source_path.open("rb") as source_handle, target_path.open("xb") as target_handle:
        for chunk in iter(lambda: source_handle.read(1024 * 1024), b""):
            target_handle.write(chunk)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _without_sensitive_values(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned = {}
        for key, child in value.items():
            normalized = str(key).lower()
            if any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS):
                continue
            cleaned[str(key)] = _without_sensitive_values(child)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [_without_sensitive_values(child) for child in value]
    return value


def build_execution_manifest(
    *,
    experiment_id: str,
    config: type,
    market_type: str,
    communication_type: str,
    communication_channel_type: str,
    seeds: Sequence[int],
    profile_paths: Mapping[str, str | Path],
) -> dict[str, Any]:
    """Build a resolved, credential-free execution manifest."""
    profiles = {}
    for role, raw_path in profile_paths.items():
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"missing {role} profile checkpoint: {path}")
        profiles[role] = {
            "path": str(path),
            "sha256": _sha256(path),
        }

    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": experiment_id,
        "market_type": market_type,
        "communication_type": communication_type,
        "communication_channel_type": communication_channel_type,
        "seeds": list(seeds),
        "profiles": profiles,
        "simulation_config": _without_sensitive_values(config.to_dict()),
        "provider_nondeterminism_caveat": (
            "Seeds control simulator-side randomness only; provider nondeterminism may remain."
        ),
    }


def verify_pairing_compatibility(rep: Mapping[str, Any], warranted: Mapping[str, Any]) -> bool:
    """Verify manifest-only matching before any outcome is inspected."""
    if rep.get("market_type") != "reputation_only":
        raise ValueError("Rep manifest has the wrong market_type")
    if warranted.get("market_type") != "reputation_and_warrant":
        raise ValueError("Rep+Warrant manifest has the wrong market_type")

    rep_seeds = rep.get("seeds")
    warranted_seeds = warranted.get("seeds")
    if not rep_seeds or rep_seeds != warranted_seeds:
        raise ValueError("pairing requires identical non-empty seed lists")

    for role in ("seller", "buyer"):
        rep_hash = rep.get("profiles", {}).get(role, {}).get("sha256")
        warranted_hash = warranted.get("profiles", {}).get(role, {}).get("sha256")
        if not rep_hash or rep_hash != warranted_hash:
            raise ValueError(f"pairing requires identical {role} profile hashes")

    for key in (
        "communication_type",
        "communication_channel_type",
        "posts4seller",
        "cognitive_probing_enabled",
        "probe_interval",
    ):
        if rep.get(key) != warranted.get(key):
            raise ValueError(f"pairing requires identical {key}")

    rep_simulation = dict(rep.get("simulation_config", {}))
    warranted_simulation = dict(warranted.get("simulation_config", {}))
    rep_simulation.pop("MARKET_TYPE", None)
    warranted_simulation.pop("MARKET_TYPE", None)
    if rep_simulation != warranted_simulation:
        raise ValueError("pairing requires identical non-mechanism simulation_config")
    return True
