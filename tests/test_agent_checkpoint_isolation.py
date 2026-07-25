import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from example.run_market_condition_batch_experiment import run_experiment
from oasis.social_agent.agents_generator import generate_agent_from_LLM


class AgentCheckpointIsolationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generator_uses_explicit_checkpoint_instead_of_shared_data_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            isolated = Path(temp_dir) / "agent_checkpoint_seller.json"
            isolated.write_text("[]", encoding="utf-8")

            with patch(
                "oasis.social_agent.agents_generator.ChatAgent",
                return_value=object(),
            ):
                await generate_agent_from_LLM(
                    agents_num=0,
                    sys_prompt="unused",
                    user_prompt="unused {}",
                    role="seller",
                    model=object(),
                    market_type="reputation_only",
                    agent_graph=object(),
                    agent_checkpoint_path=isolated,
                )

            self.assertEqual(json.loads(isolated.read_text(encoding="utf-8")), [])

    async def test_batch_run_forwards_its_snapshots_to_simulation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exp_dir = Path(temp_dir) / "seed"
            exp_dir.mkdir()
            checkpoints = {
                "seller": exp_dir / "inputs" / "agent_checkpoint_seller.json",
                "buyer": exp_dir / "inputs" / "agent_checkpoint_buyer.json",
            }

            simulation = AsyncMock()
            with patch(
                "oasis_market.simulation.run_single_simulation",
                simulation,
            ):
                await run_experiment(
                    exp_dir=exp_dir,
                    market_type="reputation_only",
                    communication_type="none",
                    run_id=1,
                    seed=2026072401,
                    agent_checkpoint_paths=checkpoints,
                )

            simulation.assert_awaited_once()
            self.assertEqual(
                simulation.await_args.kwargs["agent_checkpoint_paths"],
                checkpoints,
            )


if __name__ == "__main__":
    unittest.main()
