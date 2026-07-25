import json
import random
import tempfile
import unittest
from pathlib import Path

from experiment_control import (
    apply_cli_overrides,
    build_execution_manifest,
    copy_file_exclusive,
    parse_seed_list,
    reserve_experiment_directory,
    safe_experiment_path,
    seed_simulator,
    verify_pairing_compatibility,
    write_json_atomic,
    write_json_exclusive,
)


class DummyConfig:
    MODEL_PLATFORM = "yaml-platform"
    MODEL_TYPE = "yaml-model"
    RUNS = 5
    BASE_DATA_PATH = "experiments"

    @classmethod
    def to_dict(cls):
        return {
            "MODEL_PLATFORM": cls.MODEL_PLATFORM,
            "MODEL_TYPE": cls.MODEL_TYPE,
            "RUNS": cls.RUNS,
        }


class ExperimentControlTests(unittest.TestCase):
    def setUp(self):
        DummyConfig.MODEL_PLATFORM = "yaml-platform"
        DummyConfig.MODEL_TYPE = "yaml-model"
        DummyConfig.RUNS = 5

    def test_cli_model_values_override_loaded_config(self):
        apply_cli_overrides(
            DummyConfig,
            model_platform="cli-platform",
            model_type="cli-model",
            runs=7,
        )

        self.assertEqual(DummyConfig.MODEL_PLATFORM, "cli-platform")
        self.assertEqual(DummyConfig.MODEL_TYPE, "cli-model")
        self.assertEqual(DummyConfig.RUNS, 7)

    def test_parse_seed_list_requires_exact_run_count(self):
        self.assertEqual(parse_seed_list("11,12,13", 3), [11, 12, 13])
        with self.assertRaisesRegex(ValueError, "3 seeds"):
            parse_seed_list("11,12", 3)

    def test_seed_simulator_is_reproducible(self):
        seed_simulator(2026072401)
        first = [random.random() for _ in range(3)]
        seed_simulator(2026072401)
        second = [random.random() for _ in range(3)]
        self.assertEqual(first, second)

    def test_reserve_experiment_directory_refuses_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "family" / "condition"
            reserve_experiment_directory(target)
            self.assertTrue(target.is_dir())
            with self.assertRaises(FileExistsError):
                reserve_experiment_directory(target)

    def test_safe_experiment_path_rejects_escape_and_allows_nested_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "experiments"
            self.assertEqual(
                safe_experiment_path(base, "family/reputation_only"),
                base / "family" / "reputation_only",
            )
            for unsafe in ("../outside", "/tmp/outside", "family/../../outside"):
                with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                    safe_experiment_path(base, unsafe)

    def test_write_json_exclusive_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "manifest.json"
            write_json_exclusive(output, {"version": 1})
            with self.assertRaises(FileExistsError):
                write_json_exclusive(output, {"version": 2})
            self.assertEqual(json.loads(output.read_text()), {"version": 1})

    def test_write_json_atomic_replaces_mutable_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "status.json"
            write_json_atomic(output, {"version": 1})
            write_json_atomic(output, {"version": 2})
            self.assertEqual(json.loads(output.read_text()), {"version": 2})

    def test_copy_file_exclusive_snapshots_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            target = Path(tmp) / "inputs" / "snapshot.json"
            source.write_text('{"profile": 1}', encoding="utf-8")
            copy_file_exclusive(source, target)
            self.assertEqual(target.read_text(encoding="utf-8"), '{"profile": 1}')
            with self.assertRaises(FileExistsError):
                copy_file_exclusive(source, target)

    def test_execution_manifest_hashes_profiles_without_env_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            seller = Path(tmp) / "seller.json"
            buyer = Path(tmp) / "buyer.json"
            seller.write_text('{"agents": ["s1"]}', encoding="utf-8")
            buyer.write_text('{"agents": ["b1"]}', encoding="utf-8")

            manifest = build_execution_manifest(
                experiment_id="EXP-TEST/reputation_only",
                config=DummyConfig,
                market_type="reputation_only",
                communication_type="none",
                communication_channel_type="Fake",
                seeds=[101, 102],
                profile_paths={"seller": seller, "buyer": buyer},
            )

            self.assertEqual(manifest["seeds"], [101, 102])
            self.assertEqual(len(manifest["profiles"]["seller"]["sha256"]), 64)
            self.assertEqual(len(manifest["profiles"]["buyer"]["sha256"]), 64)
            serialized = json.dumps(manifest).lower()
            self.assertNotIn("api_key", serialized)
            self.assertNotIn("token", serialized)
            self.assertNotIn(".env", serialized)

    def test_pairing_requires_equal_seeds_profiles_and_nonmechanism_config(self):
        base = {
            "market_type": "reputation_only",
            "communication_type": "none",
            "communication_channel_type": "Fake",
            "seeds": [1, 2],
            "profiles": {
                "seller": {"sha256": "a" * 64, "snapshot_path": "rep/seller.json"},
                "buyer": {"sha256": "b" * 64, "snapshot_path": "rep/buyer.json"},
            },
            "simulation_config": {
                "MODEL_TYPE": "model-a",
                "MARKET_TYPE": "reputation_only",
                "NUM_SELLERS": 10,
            },
        }
        warranted = json.loads(json.dumps(base))
        warranted["market_type"] = "reputation_and_warrant"
        warranted["simulation_config"]["MARKET_TYPE"] = "reputation_and_warrant"
        warranted["profiles"]["seller"]["snapshot_path"] = "warrant/seller.json"
        self.assertTrue(verify_pairing_compatibility(base, warranted))

        warranted["seeds"] = [1, 3]
        with self.assertRaisesRegex(ValueError, "seed"):
            verify_pairing_compatibility(base, warranted)


if __name__ == "__main__":
    unittest.main()
