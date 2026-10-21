"""Round-boundary checkpoints for resumable market simulations.

The live SQLite database is not itself a safe checkpoint: market actions commit
individually, so a failed round can leave a valid but semantically partial
database.  This module snapshots the last fully completed round together with
the in-process agent state needed to continue from the next round.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sqlite3
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from camel.memories import MemoryRecord


CHECKPOINT_SCHEMA_VERSION = 1
_DYNAMIC_AGENT_FIELDS = (
    "reputation_score",
    "cumulative_utility",
    "history_summary",
    "current_budget",
    "thumbs_up_count",
    "thumbs_down_count",
    "total_profit",
    "last_purchase_info",
    "all_purchase_transactions",
)
_SENSITIVE_KEY_FRAGMENTS = ("api_key", "token", "secret", "password")


class CheckpointError(RuntimeError):
    """Raised when a checkpoint is absent, incompatible, or corrupt."""


def checkpoint_root_for(database_path: str | os.PathLike[str]) -> Path:
    """Return the dedicated checkpoint directory for one run database."""
    path = Path(database_path)
    return path.parent / f"{path.stem}_checkpoints"


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


def _encode_json_value(value: Any) -> Any:
    """Encode tuples and non-string-key mappings without unsafe pickle."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return {
            "__checkpoint_type__": "tuple",
            "items": [_encode_json_value(item) for item in value],
        }
    if isinstance(value, list):
        return [_encode_json_value(item) for item in value]
    if isinstance(value, Mapping):
        if all(isinstance(key, str) for key in value):
            return {
                key: _encode_json_value(child)
                for key, child in value.items()
            }
        return {
            "__checkpoint_type__": "mapping",
            "items": [
                [_encode_json_value(key), _encode_json_value(child)]
                for key, child in value.items()
            ],
        }
    if is_dataclass(value):
        return _encode_json_value(asdict(value))
    raise TypeError(
        f"checkpoint state contains unsupported value type: {type(value).__name__}"
    )


def _decode_json_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_json_value(item) for item in value]
    if not isinstance(value, dict):
        return value
    value_type = value.get("__checkpoint_type__")
    tagged_value = set(value) == {"__checkpoint_type__", "items"}
    if tagged_value and value_type == "tuple":
        return tuple(_decode_json_value(item) for item in value["items"])
    if tagged_value and value_type == "mapping":
        return {
            _decode_json_value(key): _decode_json_value(child)
            for key, child in value["items"]
        }
    return {
        key: _decode_json_value(child)
        for key, child in value.items()
    }


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _quick_check(path: Path) -> None:
    try:
        with sqlite3.connect(path) as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()
    except sqlite3.Error as exc:
        raise CheckpointError(f"cannot open checkpoint database: {path}") from exc
    if not result or result[0] != "ok":
        detail = result[0] if result else "no result"
        raise CheckpointError(
            f"checkpoint database failed PRAGMA quick_check: {detail}"
        )


class SimulationCheckpointManager:
    """Create and restore complete-round snapshots for one simulation run."""

    def __init__(
        self,
        database_path: str | os.PathLike[str],
        config: type,
        agent_checkpoint_paths: Mapping[str, str | os.PathLike[str]] | None = None,
        run_identity: Mapping[str, Any] | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.action_log_path = Path(
            str(self.database_path).replace(".db", "_actions.json")
        )
        self.root = checkpoint_root_for(self.database_path)
        self.identity = self._build_identity(
            config,
            agent_checkpoint_paths or {},
            run_identity or {},
        )
        serialized = json.dumps(
            self.identity,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        self.identity_sha256 = hashlib.sha256(serialized).hexdigest()

    @staticmethod
    def _build_identity(
        config: type,
        agent_checkpoint_paths: Mapping[str, str | os.PathLike[str]],
        run_identity: Mapping[str, Any],
    ) -> dict[str, Any]:
        profiles = {}
        for role, raw_path in sorted(agent_checkpoint_paths.items()):
            path = Path(raw_path)
            if not path.is_file():
                raise FileNotFoundError(
                    f"missing {role} profile checkpoint: {path}"
                )
            profiles[str(role)] = {
                "sha256": _sha256(path),
                "name": path.name,
            }
        config_dict = (
            config.to_dict()
            if hasattr(config, "to_dict")
            else {
                key: value
                for key, value in vars(config).items()
                if key.isupper()
            }
        )
        return {
            "config": _without_sensitive_values(config_dict),
            "profiles": profiles,
            "run": _without_sensitive_values(dict(run_identity)),
        }

    @staticmethod
    def _memory_records(agent: Any) -> list[dict[str, Any]]:
        records = []
        for item in agent.memory.retrieve():
            record = getattr(item, "memory_record", item)
            if not hasattr(record, "to_dict"):
                raise TypeError(
                    f"agent {agent.social_agent_id} memory record is not serializable"
                )
            records.append(record.to_dict())
        return records

    @staticmethod
    def _capture_rng_state() -> dict[str, Any]:
        state: dict[str, Any] = {
            "python": _encode_json_value(random.getstate()),
        }
        try:
            import numpy as np
        except ImportError:
            return state
        algorithm, keys, position, has_gauss, cached_gaussian = (
            np.random.get_state()
        )
        state["numpy"] = {
            "algorithm": algorithm,
            "keys": keys.tolist(),
            "position": int(position),
            "has_gauss": int(has_gauss),
            "cached_gaussian": float(cached_gaussian),
        }
        return state

    @staticmethod
    def _restore_rng_state(state: Mapping[str, Any]) -> None:
        random.setstate(_decode_json_value(state["python"]))
        numpy_state = state.get("numpy")
        if numpy_state is None:
            return
        try:
            import numpy as np
        except ImportError as exc:
            raise CheckpointError(
                "checkpoint contains NumPy RNG state but NumPy is unavailable"
            ) from exc
        np.random.set_state(
            (
                numpy_state["algorithm"],
                np.asarray(numpy_state["keys"], dtype="uint32"),
                int(numpy_state["position"]),
                int(numpy_state["has_gauss"]),
                float(numpy_state["cached_gaussian"]),
            )
        )

    def _capture_runtime_state(
        self,
        simulation: Any,
        completed_round: int,
    ) -> dict[str, Any]:
        agents = {}
        for agent_id, agent in simulation.agent_graph.get_agents():
            dynamic = {
                field: _encode_json_value(getattr(agent, field))
                for field in _DYNAMIC_AGENT_FIELDS
                if hasattr(agent, field)
            }
            agents[str(agent_id)] = {
                "memory": self._memory_records(agent),
                "dynamic": dynamic,
            }

        clock = simulation.env.platform.sandbox_clock
        probe_results = [
            asdict(result) if is_dataclass(result) else dict(result)
            for result in simulation.cognitive_probe_results
        ]
        return {
            "completed_round": completed_round,
            "agents": agents,
            "agent_graph_edges": [
                list(edge) for edge in simulation.agent_graph.get_edges()
            ],
            "sellers_history": _encode_json_value(simulation.sellers_history),
            "environment": {
                "current_round": int(simulation.env.current_round),
                "market_phase": str(simulation.env.market_phase),
                "clock": {
                    "k": int(clock.k),
                    "time_step": int(clock.time_step),
                    "round_step": int(clock.round_step),
                    "real_start_time": clock.real_start_time.isoformat(),
                    "platform_start_time": (
                        simulation.env.platform.start_time.isoformat()
                    ),
                },
            },
            "cognitive_probe_results": _encode_json_value(probe_results),
            "rng": self._capture_rng_state(),
        }

    def save(self, simulation: Any, completed_round: int) -> Path:
        """Persist one immutable, complete-round checkpoint."""
        if completed_round < 0:
            raise ValueError("completed_round must be non-negative")
        self.root.mkdir(parents=True, exist_ok=True)
        final_directory = self.root / f"round_{completed_round:04d}"
        if final_directory.exists():
            self._read_checkpoint(final_directory, validate_identity=True)
            return final_directory

        temporary_directory = Path(
            tempfile.mkdtemp(prefix=".checkpoint-", dir=self.root)
        )
        try:
            checkpoint_database = temporary_directory / "market.db"
            with sqlite3.connect(checkpoint_database) as destination:
                simulation.env.platform.db.backup(destination)
            _quick_check(checkpoint_database)

            checkpoint_actions = temporary_directory / "actions.json"
            if self.action_log_path.is_file():
                shutil.copy2(self.action_log_path, checkpoint_actions)
            else:
                _write_json(checkpoint_actions, [])

            runtime_state = self._capture_runtime_state(
                simulation,
                completed_round,
            )
            payload = {
                "schema_version": CHECKPOINT_SCHEMA_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_round": completed_round,
                "identity_sha256": self.identity_sha256,
                "identity": self.identity,
                "database_sha256": _sha256(checkpoint_database),
                "actions_sha256": _sha256(checkpoint_actions),
                "runtime_state": runtime_state,
            }
            _write_json(temporary_directory / "checkpoint.json", payload)
            os.replace(temporary_directory, final_directory)
        except Exception:
            shutil.rmtree(temporary_directory, ignore_errors=True)
            raise
        return final_directory

    def _read_checkpoint(
        self,
        directory: Path,
        *,
        validate_identity: bool,
    ) -> dict[str, Any]:
        metadata_path = directory / "checkpoint.json"
        database_path = directory / "market.db"
        actions_path = directory / "actions.json"
        try:
            with metadata_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckpointError(
                f"cannot read checkpoint metadata: {metadata_path}"
            ) from exc

        if payload.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
            raise CheckpointError(
                f"unsupported checkpoint schema in {metadata_path}"
            )
        if validate_identity and payload.get("identity_sha256") != self.identity_sha256:
            raise CheckpointError(
                "checkpoint identity does not match the resolved config, "
                "profile snapshots, seed, or condition"
            )
        for path, expected in (
            (database_path, payload.get("database_sha256")),
            (actions_path, payload.get("actions_sha256")),
        ):
            if not path.is_file() or not expected or _sha256(path) != expected:
                raise CheckpointError(
                    f"checkpoint artifact is missing or corrupt: {path}"
                )
        _quick_check(database_path)
        payload["_directory"] = str(directory)
        return payload

    def load_latest(self) -> dict[str, Any]:
        """Load the newest valid checkpoint for the same run identity."""
        if not self.root.is_dir():
            raise CheckpointError(
                f"no checkpoint directory exists for {self.database_path}"
            )
        candidates = sorted(
            (
                path
                for path in self.root.glob("round_[0-9][0-9][0-9][0-9]")
                if path.is_dir()
            ),
            reverse=True,
        )
        if not candidates:
            raise CheckpointError(
                f"no round checkpoint exists in {self.root}"
            )

        corruption_errors = []
        for directory in candidates:
            try:
                return self._read_checkpoint(
                    directory,
                    validate_identity=True,
                )
            except CheckpointError as exc:
                if "identity does not match" in str(exc):
                    raise
                corruption_errors.append(str(exc))
        raise CheckpointError(
            "no valid checkpoint remains; " + "; ".join(corruption_errors)
        )

    def restore_files(self) -> dict[str, Any]:
        """Replace partial live artifacts with the newest complete snapshot."""
        payload = self.load_latest()
        directory = Path(payload["_directory"])

        # A killed SQLite process can leave sidecar files for the partial
        # round. Remove them before replacing the main database so they can
        # never be replayed against the complete-round snapshot.
        for suffix in ("-wal", "-shm"):
            Path(f"{self.database_path}{suffix}").unlink(missing_ok=True)

        _atomic_copy(directory / "market.db", self.database_path)
        _atomic_copy(directory / "actions.json", self.action_log_path)
        _quick_check(self.database_path)
        return payload

    def restore_runtime(self, simulation: Any, payload: Mapping[str, Any]) -> int:
        """Restore agent, environment, history, probe, and RNG state."""
        state = payload["runtime_state"]
        saved_agents = state["agents"]
        current_ids = {
            str(agent_id) for agent_id, _ in simulation.agent_graph.get_agents()
        }
        if current_ids != set(saved_agents):
            raise CheckpointError(
                "checkpoint agent IDs do not match reconstructed profile agents"
            )

        for agent_id, agent in simulation.agent_graph.get_agents():
            saved = saved_agents[str(agent_id)]
            agent.memory.clear()
            agent.memory.write_records(
                [
                    MemoryRecord.from_dict(record)
                    for record in saved["memory"]
                ]
            )
            for field, value in saved["dynamic"].items():
                setattr(agent, field, _decode_json_value(value))

        for source, target in state.get("agent_graph_edges", []):
            simulation.agent_graph.add_edge(source, target)

        simulation.sellers_history = _decode_json_value(
            state["sellers_history"]
        )
        environment = state["environment"]
        simulation.env.current_round = int(environment["current_round"])
        simulation.env.market_phase = environment["market_phase"]
        clock_state = environment["clock"]
        clock = simulation.env.platform.sandbox_clock
        clock.k = int(clock_state["k"])
        clock.time_step = int(clock_state["time_step"])
        clock.round_step = int(clock_state["round_step"])
        clock.real_start_time = datetime.fromisoformat(
            clock_state["real_start_time"]
        )
        simulation.env.platform.start_time = datetime.fromisoformat(
            clock_state["platform_start_time"]
        )

        from oasis_market.probing import ProbeResult

        simulation.cognitive_probe_results = [
            ProbeResult(**result)
            for result in _decode_json_value(
                state.get("cognitive_probe_results", [])
            )
        ]
        if simulation.prober is not None:
            simulation.prober.probe_results = list(
                simulation.cognitive_probe_results
            )

        self._restore_rng_state(state["rng"])
        completed_round = int(state["completed_round"])
        if completed_round != int(payload["completed_round"]):
            raise CheckpointError(
                "checkpoint round metadata is internally inconsistent"
            )
        return completed_round
