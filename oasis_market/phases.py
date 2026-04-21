"""
Market phases module for simulation
Handles different phases of the market simulation including seller actions, buyer actions, and communication phases
"""

import random
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from oasis.environment.env_action import LLMAction
from prompt import SELLER_ROUND_PROMPT, BUYER_ROUND_PROMPT, MarketEnv_prompt


class MarketPhase:
    """Base class for market phases"""

    def __init__(self, env, agent_graph, db_manager, action_logger, config):
        """
        Initialize market phase

        Args:
            env: Environment instance
            agent_graph: Agent graph instance
            db_manager: Database manager instance
            action_logger: Action logger instance
            config: Simulation configuration
        """
        self.env = env
        self.agent_graph = agent_graph
        self.db_manager = db_manager
        self.action_logger = action_logger
        self.config = config

    async def execute(self, round_num: int, **kwargs) -> Any:
        """
        Execute the phase

        Args:
            round_num: Current round number
            **kwargs: Additional phase-specific arguments

        Returns:
            Phase execution results
        """
        raise NotImplementedError("Subclasses must implement execute method")


class SellerListingPhase(MarketPhase):
    """Handles seller product listing phase"""

    async def execute(
        self,
        round_num: int,
        sellers_history: Dict,
        market_type: str = "reputation_and_warrant",
    ) -> None:
        """
        Execute seller listing phase

        Args:
            round_num: Current round number
            sellers_history: Dictionary of seller histories
            market_type: Market type ('reputation_only' or 'reputation_and_warrant')
        """
        from .agents import AgentManager
        from .logging import SimulationLogger

        SimulationLogger.print_phase_header(round_num, "Seller Action Phase")

        seller_actions = {}
        self.env.market_phase = "listing"

        for agent_id, agent in self.agent_graph.get_agents():
            if agent.user_info.profile.get("role") == "seller":
                # Get market_type from agent profile if not provided
                agent_market_type = agent.user_info.profile.get(
                    "market_type", market_type
                )

                # Prepare seller state
                state, visible_history_string = AgentManager.prepare_seller_state(
                    agent,
                    agent_id,
                    round_num,
                    sellers_history.get(agent_id, []),
                    self.db_manager,
                    self.config,
                    market_type=agent_market_type,
                )

                # Update environment state
                self.env.current_round = round_num

                # Prepare round prompt with budget information
                budget = state.get("budget", 10.0)
                total_profit = state.get("total_profit", 0)
                thumbs_up = state.get("thumbs_up_count", 0)
                thumbs_down = state.get("thumbs_down_count", 0)

                # Add budget information to the prompt
                seller_round_prompt = SELLER_ROUND_PROMPT.format(
                    history_summary=visible_history_string
                )

                # Tools available for sellers
                listing_tools = ["list_products"]

                seller_actions[agent] = LLMAction(
                    extra_action=listing_tools,
                    extra_prompt=seller_round_prompt,
                    level="market",
                )

        if seller_actions:
            await self.env.step(seller_actions)
            self.action_logger.save_action_records(
                self.env, round_num, "seller_listing", self.agent_graph
            )

        print("All seller actions are complete.")


class BuyerPurchasePhase(MarketPhase):
    """Handles buyer purchase phase"""

    async def execute(self, round_num: int) -> List[Dict]:
        """
        Execute buyer purchase phase

        Args:
            round_num: Current round number

        Returns:
            List of purchase results
        """
        from .agents import AgentManager
        from .logging import SimulationLogger

        SimulationLogger.print_phase_header(round_num, "Buyer Action Phase 1: Purchase")

        self.env.market_phase = "purchase"
        purchase_results = []

        # Get and shuffle buyers
        agent_lists = self.agent_graph.get_agents()
        buyers = [
            pair
            for pair in agent_lists
            if pair[1].user_info.profile.get("role") == "buyer"
        ]
        random.shuffle(buyers)

        for agent_id, agent in buyers:
            buyer_actions = {}
            state = AgentManager.prepare_buyer_state(
                agent, agent_id, round_num, self.db_manager
            )

            # Prepare round prompt
            buyer_round_prompt = (
                "\n\nIn this phase, you are only allowed to perform the purchase_products action to purchase products. "
                "Based on the available product and seller information, and your own preferences, choose whether and which products to purchase."
                "You can purchase multiple products at once. You cannot perform any other actions during this phase.\n"
            )

            # Tools available for buyers in purchase phase
            purchase_tools = ["purchase_products"]
            buyer_actions[agent] = LLMAction(
                extra_action=purchase_tools,
                extra_prompt=buyer_round_prompt,
                level="market",
            )

            results = await self.env.step(buyer_actions)
            self.action_logger.save_action_records(
                self.env, round_num, "buyer_purchase", self.agent_graph
            )

            # Collect results
            if isinstance(results, list):
                purchase_results.extend(results)
            elif isinstance(results, dict):
                purchase_results.append(results)

        print("All purchase actions are attempted.")
        return purchase_results


class BuyerRatingPhase(MarketPhase):
    """Handles buyer rating phase"""

    async def execute(
        self, round_num: int, purchase_results: List[Dict], market_type: str
    ) -> None:
        """
        Execute buyer rating phase

        Args:
            round_num: Current round number
            purchase_results: Results from purchase phase
            market_type: Type of market ('reputation_only' or 'reputation_and_warrant')
        """
        from .agents import AgentManager
        from .logging import SimulationLogger

        SimulationLogger.print_phase_header(round_num, "Buyer Action Phase 2: Rate")

        rating_purchase_actions = {}
        self.env.market_phase = "rating"

        successful_purchases = [
            res for res in purchase_results if res and res.get("success")
        ]
        rating_results = None

        if successful_purchases:
            for purchase_result in successful_purchases:
                agent_id = purchase_result.get("agent_id")
                if agent_id is None:
                    continue

                agent = self.agent_graph.get_agent(agent_id)

                # Handle multiple transactions from purchase_products
                transactions = purchase_result.get("transactions", [])
                if not transactions:
                    # Fallback: if no transactions list, treat the whole result as a single transaction
                    transactions = (
                        [purchase_result]
                        if purchase_result.get("transaction_id")
                        else []
                    )

                # Only proceed if buyer has actual transactions
                # Skip buyers who didn't purchase anything
                if not transactions or not any(
                    t.get("transaction_id") for t in transactions
                ):
                    continue

                # Store all transactions information in agent
                # Store the first transaction as last_purchase_info for backward compatibility
                # Get seller thumbs-up/thumbs-down counts for each transaction
                for transaction in transactions:
                    seller_id = transaction.get("seller_id")
                    if seller_id:
                        thumbs_up, thumbs_down = self.db_manager.get_user_reputation(
                            seller_id
                        )
                        transaction["seller_thumbs_up"] = thumbs_up
                        transaction["seller_thumbs_down"] = thumbs_down
                    else:
                        transaction["seller_thumbs_up"] = 0
                        transaction["seller_thumbs_down"] = 0

                # Store all transactions in a new attribute for rating phase (must be done before env.step)
                agent.all_purchase_transactions = transactions

                # Store the first transaction as last_purchase_info (for backward compatibility with env)
                AgentManager.store_purchase_info(agent, transactions[0])

                # Tools available for buyers in rating phase (only rating, no challenge)
                rating_tools = ["rate_transactions"]

                # Prepare rating prompt
                buyer_rating_prompt = (
                    "\n\nIn this phase, you are allowed to perform the rate_transactions action to rate transactions. "
                    "Based on your transaction details above (advertised quality, true quality received, price paid, and seller reputation), choose whether and which transactions to rate. "
                    "You can rate multiple transactions at once. You cannot perform any other actions during this phase.\n"
                )

                rating_purchase_actions[agent] = LLMAction(
                    extra_action=rating_tools,
                    extra_prompt=buyer_rating_prompt,
                    level="market",
                )

        if rating_purchase_actions:
            rating_results = await self.env.step(rating_purchase_actions)
            self.action_logger.save_action_records(
                self.env, round_num, "buyer_rating", self.agent_graph
            )

        print("All rating actions are complete.")

        return rating_results


class BuyerChallengePhase(MarketPhase):
    """Handles buyer challenge phase (only for reputation_and_warrant market)"""

    async def execute(
        self, round_num: int, purchase_results: List[Dict], market_type: str
    ) -> None:
        """
        Execute buyer challenge phase

        Args:
            round_num: Current round number
            purchase_results: Results from purchase phase
            market_type: Type of market ('reputation_only' or 'reputation_and_warrant')
        """
        from .agents import AgentManager
        from .logging import SimulationLogger

        # Only execute challenge phase for reputation_and_warrant market
        if market_type != "reputation_and_warrant":
            return

        SimulationLogger.print_phase_header(
            round_num, "Buyer Action Phase 3: Challenge Warrants"
        )

        challenge_actions = {}
        self.env.market_phase = "challenge"

        successful_purchases = [
            res for res in purchase_results if res and res.get("success")
        ]
        challenge_results = []

        if successful_purchases:
            for purchase_result in successful_purchases:
                agent_id = purchase_result.get("agent_id")
                if agent_id is None:
                    continue

                agent = self.agent_graph.get_agent(agent_id)

                # Handle multiple transactions from purchase_products
                transactions = purchase_result.get("transactions", [])
                if not transactions:
                    # Fallback: if no transactions list, treat the whole result as a single transaction
                    transactions = (
                        [purchase_result]
                        if purchase_result.get("transaction_id")
                        else []
                    )

                # Only proceed if buyer has actual transactions
                # Skip buyers who didn't purchase anything
                if not transactions or not any(
                    t.get("transaction_id") for t in transactions
                ):
                    continue

                # Ensure transactions are stored in agent (should already be set in rating phase)
                if (
                    not hasattr(agent, "all_purchase_transactions")
                    or not agent.all_purchase_transactions
                ):
                    # Store all transactions information in agent
                    for transaction in transactions:
                        seller_id = transaction.get("seller_id")
                        if seller_id:
                            thumbs_up, thumbs_down = (
                                self.db_manager.get_user_reputation(seller_id)
                            )
                            transaction["seller_thumbs_up"] = thumbs_up
                            transaction["seller_thumbs_down"] = thumbs_down
                        else:
                            transaction["seller_thumbs_up"] = 0
                            transaction["seller_thumbs_down"] = 0

                    agent.all_purchase_transactions = transactions
                    AgentManager.store_purchase_info(agent, transactions[0])

                # Tools available for buyers in challenge phase (only challenge)
                challenge_tools = ["challenge_warrants"]

                # Prepare challenge prompt
                buyer_challenge_prompt = (
                    "\n\nIn this phase, you are allowed to perform the challenge_warrants action to challenge the warrants of transactions. "
                    "Based on your transaction details above (advertised quality, true quality received, price paid, and warrant status), choose whether and which warranted transactions to challenge. "
                    "You can challenge multiple transactions at once. You cannot perform any other actions during this phase.\n"
                )

                challenge_actions[agent] = LLMAction(
                    extra_action=challenge_tools,
                    extra_prompt=buyer_challenge_prompt,
                    level="market",
                )

        if challenge_actions:
            challenge_results = await self.env.step(challenge_actions)
            self.action_logger.save_action_records(
                self.env, round_num, "buyer_challenge", self.agent_graph
            )

        for result in challenge_results:
            if result.get("success"):
                print("good")
        print("All challenge actions are complete.")
        return challenge_results


class CommunicationPhase(MarketPhase):
    """Handles communication phases for sellers or buyers"""

    async def execute(self, round_num: int, role: str) -> None:
        """
        Execute communication phase

        Args:
            round_num: Current round number
            role: 'seller' or 'buyer' indicating who is communicating
        """
        from .agents import AgentManager
        from .logging import SimulationLogger

        phase_name = f"{role.capitalize()} Communication Phase"
        SimulationLogger.print_phase_header(round_num, phase_name)

        communication_actions = {}
        self.env.market_phase = "communication"

        for agent_id, agent in self.agent_graph.get_agents():
            if agent.user_info.profile.get("role") == role:
                if role == "seller":
                    # Prepare seller state for communication
                    state = self.db_manager.get_agent_state(
                        agent_id, "seller", round_num=round_num
                    )
                    self.env.current_round = round_num

                    communication_prompt = (
                        "\n\nIn this phase, you are allowed to communicate with other sellers. "
                        "You cannot perform any other actions during this phase.\n"
                        "You can share your plan of listing products, product information, your experience, or any other information with other sellers to help them make listing decisions.\n"
                    )
                else:  # buyer
                    # Prepare buyer state for communication
                    state = AgentManager.prepare_buyer_state(
                        agent, agent_id, round_num, self.db_manager
                    )
                    self.env.current_round = round_num

                    # Get buyer's transaction info if available (from previous rounds)
                    # Note: Buyer communication happens BEFORE purchase phase, so this is from previous rounds
                    all_transactions = getattr(agent, "all_purchase_transactions", None)
                    if all_transactions is None:
                        # Fallback to last_purchase_info for backward compatibility
                        last_purchase_info = getattr(agent, "last_purchase_info", {})
                        all_transactions = (
                            [last_purchase_info]
                            if last_purchase_info.get("transaction_id")
                            else []
                        )

                    # Build communication prompt with transaction context if available
                    if all_transactions and any(
                        t.get("transaction_id") for t in all_transactions
                    ):
                        # Buyer has previous purchase experience to share
                        transaction_summary = f"You have {len(all_transactions)} previous transaction(s) from earlier rounds that you can share information about."
                        communication_prompt = (
                            f"\n\nIn this phase, you are allowed to communicate with other buyers. "
                            f"You cannot perform any other actions during this phase.\n"
                            f"{transaction_summary}\n"
                            f"You can share your purchase experience, product information, seller reputation, or any other information with other buyers to help them make purchase decisions.\n"
                        )
                    else:
                        # First round or no previous purchases - buyer can still communicate but has no purchase history
                        communication_prompt = (
                            "\n\nIn this phase, you are allowed to communicate with other buyers. "
                            "You cannot perform any other actions during this phase.\n"
                            "You can share your observations, expectations, or any other information with other buyers to help them make purchase decisions.\n"
                        )

                # Common communication tools
                communication_tools = [
                    "create_post",
                    "quote_post",
                    "like_post",
                    "dislike_post",
                ]

                communication_actions[agent] = LLMAction(
                    extra_action=communication_tools,
                    extra_prompt=communication_prompt,
                    level="communication",
                )

        if communication_actions:
            await self.env.step(communication_actions)
            self.action_logger.save_action_records(
                self.env, round_num, f"{role}_communication", self.agent_graph
            )

        print(f"All {role} communication actions are complete.")


# Test cases
if __name__ == "__main__":
    print("Phase module tests")
    print(
        "This module contains phase execution logic that requires async environment and agent setup."
    )
    print("Integration tests should be run with the full simulation.")

    # Test basic phase structure
    class MockEnv:
        def __init__(self):
            self.market_phase = None
            self.current_round = None

    class MockAgentGraph:
        def get_agents(self):
            return []

    class MockConfig:
        EXIT_ROUND = 7
        REENTRY_ALLOWED_ROUND = 5

    # Create mock instances
    env = MockEnv()
    agent_graph = MockAgentGraph()
    config = MockConfig()

    # Test phase initialization
    phase = MarketPhase(env, agent_graph, None, None, config)
    assert phase.env == env
    assert phase.agent_graph == agent_graph
    assert phase.config == config
    print("✓ Phase initialization successful")

    # Test specific phases can be instantiated
    seller_phase = SellerListingPhase(env, agent_graph, None, None, config)
    assert isinstance(seller_phase, MarketPhase)
    print("✓ SellerListingPhase instantiated")

    buyer_purchase_phase = BuyerPurchasePhase(env, agent_graph, None, None, config)
    assert isinstance(buyer_purchase_phase, MarketPhase)
    print("✓ BuyerPurchasePhase instantiated")

    buyer_rating_phase = BuyerRatingPhase(env, agent_graph, None, None, config)
    assert isinstance(buyer_rating_phase, MarketPhase)
    print("✓ BuyerRatingPhase instantiated")

    communication_phase = CommunicationPhase(env, agent_graph, None, None, config)
    assert isinstance(communication_phase, MarketPhase)
    print("✓ CommunicationPhase instantiated")

    print("\nAll phase tests passed!")
