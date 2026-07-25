import asyncio
import unittest
from types import SimpleNamespace

from oasis.environment.env import OasisEnv


class _TransientProviderAgent:
    social_agent_id = 7
    system_message = SimpleNamespace(content="system")

    def __init__(self):
        self.calls = 0

    async def perform_market_action(self, *args):
        self.calls += 1
        if self.calls == 1:
            return (
                {
                    "success": False,
                    "_failure_kind": "model_or_provider",
                    "error": "503 upstream_unavailable",
                },
                "",
            )
        return ({"success": True, "agent_id": self.social_agent_id}, "ok")


class _ParseFailureAgent:
    social_agent_id = 8
    system_message = SimpleNamespace(content="system")

    def __init__(self):
        self.calls = 0

    async def perform_market_action(self, *args):
        self.calls += 1
        return (
            {
                "success": False,
                "_failure_kind": "action_or_parse",
                "error": "invalid action JSON",
            },
            "",
        )


class OasisEnvModelRetryTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _make_env():
        env = object.__new__(OasisEnv)
        env.llm_semaphore = asyncio.Semaphore(1)
        env.current_round = 4
        env.market_phase = "listing"
        env.model_action_max_attempts = 2
        env.model_action_retry_base_seconds = 0
        return env

    async def test_transient_provider_failure_retries_same_agent_action(self):
        env = self._make_env()
        agent = _TransientProviderAgent()
        action = SimpleNamespace(
            level="market",
            extra_action=None,
            extra_prompt=None,
        )

        result = await env._perform_llm_action(agent, action)

        self.assertEqual(result, ({"success": True, "agent_id": 7}, "ok"))
        self.assertEqual(agent.calls, 2)

    async def test_parse_failure_is_not_retried(self):
        env = self._make_env()
        agent = _ParseFailureAgent()
        action = SimpleNamespace(
            level="market",
            extra_action=None,
            extra_prompt=None,
        )

        result = await env._perform_llm_action(agent, action)

        self.assertEqual(result[0]["_failure_kind"], "action_or_parse")
        self.assertEqual(agent.calls, 1)


if __name__ == "__main__":
    unittest.main()
