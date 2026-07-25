import json
import random
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from camel.memories import MemoryRecord
from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole

from oasis_market.checkpointing import (
    CheckpointError,
    SimulationCheckpointManager,
)
from oasis_market.probing import ProbeResult


class DummyConfig:
    MODEL_TYPE = "test-model"
    MARKET_TYPE = "reputation_only"
    SIMULATION_ROUNDS = 3

    @classmethod
    def to_dict(cls):
        return {
            "MODEL_TYPE": cls.MODEL_TYPE,
            "MARKET_TYPE": cls.MARKET_TYPE,
            "SIMULATION_ROUNDS": cls.SIMULATION_ROUNDS,
        }


class FakeMemory:
    def __init__(self, records):
        self.records = list(records)

    def retrieve(self):
        return [
            SimpleNamespace(memory_record=record)
            for record in self.records
        ]

    def clear(self):
        self.records.clear()

    def write_records(self, records):
        self.records.extend(records)


class FakeAgent:
    def __init__(self, agent_id):
        self.social_agent_id = agent_id
        message = BaseMessage.make_user_message(
            role_name="User",
            content=f"memory-{agent_id}",
        )
        self.memory = FakeMemory(
            [
                MemoryRecord(
                    message=message,
                    role_at_backend=OpenAIBackendRole.USER,
                    agent_id=str(agent_id),
                )
            ]
        )
        self.history_summary = f"history-{agent_id}"
        self.cumulative_utility = float(agent_id)
        self.all_purchase_transactions = [
            {"transaction_id": agent_id, "has_warrant": False}
        ]


class FakeGraph:
    def __init__(self, agents):
        self.agents = {agent.social_agent_id: agent for agent in agents}
        self.edges = []

    def get_agents(self):
        return list(self.agents.items())

    def get_edges(self):
        return list(self.edges)

    def add_edge(self, source, target):
        self.edges.append((source, target))


class SimulationCheckpointTests(unittest.TestCase):
    def _build_simulation(self, root):
        database_path = root / "run_1.db"
        connection = sqlite3.connect(database_path)
        connection.execute("CREATE TABLE marker (value TEXT)")
        connection.execute("INSERT INTO marker VALUES ('complete-round')")
        connection.execute(
            "CREATE TABLE user ("
            "agent_id INTEGER PRIMARY KEY, budget REAL, "
            "profit_utility_score REAL, brand_name TEXT)"
        )
        connection.execute(
            "INSERT INTO user VALUES (1, 60.0, 0.0, 'original-brand')"
        )
        connection.execute(
            "CREATE TABLE product ("
            "product_id INTEGER PRIMARY KEY, round_number INTEGER)"
        )
        connection.execute(
            "CREATE TABLE transactions ("
            "transaction_id INTEGER PRIMARY KEY, round_number INTEGER)"
        )
        connection.execute(
            "CREATE TABLE post (post_id INTEGER PRIMARY KEY, content TEXT)"
        )
        connection.execute(
            "CREATE TABLE trace (action TEXT, info TEXT)"
        )
        connection.commit()

        action_path = root / "run_1_actions.json"
        action_path.write_text(
            json.dumps([{"round": 1, "phase": "seller_listing"}]),
            encoding="utf-8",
        )
        graph = FakeGraph([FakeAgent(1), FakeAgent(2)])
        graph.edges.append((1, 2))
        clock = SimpleNamespace(
            k=60,
            time_step=0,
            round_step=1,
            real_start_time=datetime(2026, 7, 24, 12, 0, 0),
        )
        platform = SimpleNamespace(
            db=connection,
            sandbox_clock=clock,
            start_time=datetime(2026, 7, 24, 12, 0, 0),
        )
        env = SimpleNamespace(
            platform=platform,
            current_round=1,
            market_phase="general",
        )
        probe = ProbeResult(
            agent_id=1,
            round_num=1,
            vulnerability_type="reputation_lag",
            prompt="prompt",
            response="response",
            selected_option="B",
            manipulation_detected=False,
            severity_score=None,
            context={},
        )
        simulation = SimpleNamespace(
            agent_graph=graph,
            env=env,
            sellers_history={
                1: [
                    {
                        "round": 1,
                        "product_groups": {
                            ("HQ", "LQ", False): {"count": 1}
                        },
                    }
                ]
            },
            cognitive_probe_results=[probe],
            prober=SimpleNamespace(probe_results=[]),
        )
        return database_path, action_path, simulation

    def test_complete_round_restore_discards_partial_artifacts_and_restores_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seller = root / "seller.json"
            buyer = root / "buyer.json"
            seller.write_text("[]", encoding="utf-8")
            buyer.write_text("[]", encoding="utf-8")
            database_path, action_path, simulation = self._build_simulation(root)
            manager = SimulationCheckpointManager(
                database_path,
                DummyConfig,
                {"seller": seller, "buyer": buyer},
                {"seed": 101, "run_id": 1},
            )

            random.seed(42)
            np.random.seed(42)
            manager.save(simulation, completed_round=1)
            expected_python_random = random.random()
            expected_numpy_random = float(np.random.random())

            simulation.env.platform.db.execute(
                "UPDATE marker SET value = 'partial-round'"
            )
            simulation.env.platform.db.execute(
                "UPDATE user SET budget = 42.0, "
                "profit_utility_score = 18.0, brand_name = 'partial-brand'"
            )
            simulation.env.platform.db.execute(
                "INSERT INTO product VALUES (1, 2)"
            )
            simulation.env.platform.db.execute(
                "INSERT INTO transactions VALUES (1, 2)"
            )
            simulation.env.platform.db.execute(
                "INSERT INTO post VALUES (1, 'partial communication')"
            )
            simulation.env.platform.db.execute(
                "INSERT INTO trace VALUES ('purchase', 'partial action')"
            )
            simulation.env.platform.db.commit()
            simulation.env.platform.db.close()
            action_path.write_text(
                json.dumps(
                    [
                        {"round": 1, "phase": "seller_listing"},
                        {"round": 2, "phase": "buyer_purchase"},
                    ]
                ),
                encoding="utf-8",
            )
            for _, agent in simulation.agent_graph.get_agents():
                agent.memory.clear()
                agent.history_summary = "mutated"
            simulation.agent_graph.edges.clear()
            simulation.sellers_history = {}
            simulation.cognitive_probe_results = []
            random.seed(999)
            np.random.seed(999)

            payload = manager.restore_files()
            restored_round = manager.restore_runtime(simulation, payload)

            with sqlite3.connect(database_path) as restored_database:
                marker = restored_database.execute(
                    "SELECT value FROM marker"
                ).fetchone()[0]
                restored_user = restored_database.execute(
                    "SELECT budget, profit_utility_score, brand_name FROM user"
                ).fetchone()
                partial_row_counts = {
                    table: restored_database.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0]
                    for table in ("product", "transactions", "post", "trace")
                }
            self.assertEqual(marker, "complete-round")
            self.assertEqual(restored_user, (60.0, 0.0, "original-brand"))
            self.assertEqual(
                partial_row_counts,
                {"product": 0, "transactions": 0, "post": 0, "trace": 0},
            )
            self.assertEqual(
                json.loads(action_path.read_text(encoding="utf-8")),
                [{"round": 1, "phase": "seller_listing"}],
            )
            self.assertEqual(restored_round, 1)
            self.assertEqual(simulation.agent_graph.edges, [(1, 2)])
            self.assertIn(("HQ", "LQ", False), simulation.sellers_history[1][0]["product_groups"])
            self.assertEqual(
                simulation.agent_graph.agents[1].history_summary,
                "history-1",
            )
            self.assertEqual(
                simulation.agent_graph.agents[1].memory.records[0].message.content,
                "memory-1",
            )
            self.assertEqual(len(simulation.cognitive_probe_results), 1)
            self.assertAlmostEqual(random.random(), expected_python_random)
            self.assertAlmostEqual(
                float(np.random.random()),
                expected_numpy_random,
            )

    def test_resume_rejects_changed_run_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seller = root / "seller.json"
            buyer = root / "buyer.json"
            seller.write_text("[]", encoding="utf-8")
            buyer.write_text("[]", encoding="utf-8")
            database_path, _, simulation = self._build_simulation(root)
            manager = SimulationCheckpointManager(
                database_path,
                DummyConfig,
                {"seller": seller, "buyer": buyer},
                {"seed": 101},
            )
            manager.save(simulation, completed_round=1)
            simulation.env.platform.db.close()

            incompatible = SimulationCheckpointManager(
                database_path,
                DummyConfig,
                {"seller": seller, "buyer": buyer},
                {"seed": 202},
            )
            with self.assertRaisesRegex(CheckpointError, "identity"):
                incompatible.load_latest()


if __name__ == "__main__":
    unittest.main()
