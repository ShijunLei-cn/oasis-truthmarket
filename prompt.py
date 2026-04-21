# Market Simulation Prompts

from camel.prompts import TextPrompt
from config import SimulationConfig


class ClassProperty:
    """Descriptor to make class methods accessible as class properties"""

    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner):
        return self.method(owner)


# ================== Seller_prompt ==================


class Seller_prompt:
    """All seller-related prompts and configurations"""

    @staticmethod
    def _get_market_params():
        """Get market parameters from config"""
        return SimulationConfig.MARKET_PARAMS

    @classmethod
    def get_actions(cls) -> dict[str, str]:
        """Get available action descriptions for sellers in different markets"""
        params = cls._get_market_params()
        hq_price = params["hq_price"]
        lq_price = params["lq_price"]
        hq_cost = params["hq_cost"]
        lq_cost = params["lq_cost"]

        return {
            "reputation_only": (
                "Available Actions:\n"
                f"- `list_products(products: list)`: List products for sale. You must use this action to list products.\n"
                "  - `products`: A list of product specifications. Each product is a dict with:\n"
                "    - `advertised_quality` (str): What you tell buyers ('HQ' or 'LQ')\n"
                "    - `product_quality` (str): What you actually produce ('HQ' or 'LQ')\n"
                "    - `quantity` (int, optional): Number of products with this specification (default: 1)\n"
                "  - **IMPORTANT**: You can list MULTIPLE DIFFERENT TYPES of products in a single round. This allows you to:\n"
                "    * Diversify your product portfolio (e.g., mix of HQ and LQ products)\n"
                "    * Target different buyer segments simultaneously\n"
                "    * Balance risk and profit by offering various quality combinations\n"
                "    * Maximize your budget utilization across different product types\n"
                f'  - Example 1 (multiple types): list_products([{{{{"advertised_quality": "HQ", "product_quality": "HQ", "quantity": 2}}}}, {{{{ "advertised_quality": "LQ", "product_quality": "LQ", "quantity": 1}}}}])\n'
                f'  - Example 2 (single type): list_products([{{{{"advertised_quality": "HQ", "product_quality": "LQ", "quantity": 5}}}}])\n'
                f"  - Production Costs: HQ products cost ${hq_cost:.1f} to produce, LQ products cost ${lq_cost:.1f} to produce\n"
                f"  - Selling Prices: HQ products are priced at ${hq_price:.1f}, LQ products are priced at ${lq_price:.1f}. You cannot change the price.\n"
                + (
                    f"- `reenter_market()`: Reset your brand reputation and re-enter market to make sales under a new brand name.\n"
                    f"  - Available from Round {SimulationConfig.REENTRY_ALLOWED_ROUND} onward under market rules.\n"
                    if SimulationConfig.REENTRY_ALLOWED_ROUND is not None else ""
                )
            ),
            "reputation_and_warrant": (
                "Available Actions:\n"
                f"- `list_products(products: list)`: List products for sale. You must use this action to list products.\n"
                "  - `products`: A list of product specifications. Each product is a dict with:\n"
                "    - `advertised_quality` (str): What you tell buyers ('HQ' or 'LQ')\n"
                "    - `product_quality` (str): What you actually produce ('HQ' or 'LQ')\n"
                "    - `has_warrant` (bool, optional): Whether to attach a Truth Warrant label to this product's listing (default: False). A warrant does not change the product itself — it is a public signal attached to the advertisement that tells buyers you stand behind your advertised quality claim.\n"
                "    - `quantity` (int, optional): Number of products with this specification (default: 1)\n"
                "  - **IMPORTANT**: You can list MULTIPLE DIFFERENT TYPES of products in a single call. This allows you to:\n"
                "    * Diversify your product portfolio (e.g., mix of HQ and LQ products)\n"
                "    * Attach a warrant to some listings but not others\n"
                "    * Target different buyer segments simultaneously\n"
                "    * Maximize your budget utilization across different product types\n"
                "  - **Examples of listing options**:\n"
                "    * advertised_quality=HQ, product_quality=HQ, has_warrant=True — honest HQ listing with warrant\n"
                "    * advertised_quality=HQ, product_quality=HQ, has_warrant=False — honest HQ listing without warrant\n"
                "    * advertised_quality=HQ, product_quality=LQ, has_warrant=True — misleading HQ claim with warrant (risky!)\n"
                "    * advertised_quality=HQ, product_quality=LQ, has_warrant=False — misleading HQ claim without warrant\n"
                "    * advertised_quality=LQ, product_quality=LQ, has_warrant=True — honest LQ listing with warrant\n"
                "    * advertised_quality=LQ, product_quality=LQ, has_warrant=False — honest LQ listing without warrant\n"
                "    * advertised_quality=LQ, product_quality=HQ, has_warrant=True — under-advertising with warrant\n"
                "    * advertised_quality=LQ, product_quality=HQ, has_warrant=False — under-advertising without warrant\n"
                f'  - Example 1 (multiple types with different warrant status): list_products([{{{{"advertised_quality": "HQ", "product_quality": "HQ", "has_warrant": True, "quantity": 2}}}}, {{{{ "advertised_quality": "HQ", "product_quality": "HQ", "has_warrant": False, "quantity": 3}}}}, {{{{ "advertised_quality": "LQ", "product_quality": "LQ", "quantity": 1}}}}])\n'
                f'  - Example 2 (fraudulent with and without warrant): list_products([{{{{"advertised_quality": "HQ", "product_quality": "LQ", "has_warrant": True, "quantity": 2}}}}, {{{{ "advertised_quality": "HQ", "product_quality": "LQ", "has_warrant": False, "quantity": 5}}}}])\n'
                f"  - Production Costs: HQ products cost ${hq_cost:.1f} to produce, LQ products cost ${lq_cost:.1f} to produce\n"
                f"  - Selling Prices: HQ products are priced at ${hq_price:.1f}, LQ products are priced at ${lq_price:.1f}. You cannot change the price.\n"
                + (
                    f"- `reenter_market()`: Refresh your brand reputation and re-enter market activity.\n"
                    f"  - Available from Round {SimulationConfig.REENTRY_ALLOWED_ROUND} onward under market rules.\n"
                    if SimulationConfig.REENTRY_ALLOWED_ROUND is not None else ""
                )
            ),
        }

    # Keep ACTIONS as class property for backward compatibility
    ACTIONS = ClassProperty(lambda cls: cls.get_actions())

    @classmethod
    def get_payoff_matrix(cls) -> dict[str, str]:
        """Get payoff matrix descriptions for sellers in different markets"""
        params = cls._get_market_params()
        hq_cost = params["hq_cost"]
        lq_cost = params["lq_cost"]
        hq_price = params["hq_price"]
        lq_price = params["lq_price"]
        hq_warrant_escrow = params["hq_warrant_escrow"]
        lq_warrant_escrow = params["lq_warrant_escrow"]

        hq_default_profit = hq_price - hq_cost
        lq_default_profit_lq = lq_price - lq_cost
        lq_default_profit_hq = lq_price - hq_cost

        return {
            "reputation_only": (
                f"""
The payoff matrix below shows the cost of producing each quality type and the price you receive when selling it, so you can calculate how much profit you make from each combination.

**Production Costs:**
- HQ production cost: ${hq_cost:.1f}
- LQ production cost: ${lq_cost:.1f}

**Profit per Sale (production cost subtracted from selling price):**
- If you produce an HQ product and advertise it as HQ: a sale earns you ${hq_price:.1f} - ${hq_cost:.1f} = ${hq_default_profit:.1f} profit.
- If you produce an LQ product and advertise it as HQ: a sale earns you ${hq_price:.1f} - ${lq_cost:.1f} = ${hq_price - lq_cost:.1f} profit.
- If you produce an LQ product and advertise it as LQ: a sale earns you ${lq_price:.1f} - ${lq_cost:.1f} = ${lq_default_profit_lq:.1f} profit.
- If you produce an HQ product and advertise it as LQ: a sale earns you ${lq_price:.1f} - ${hq_cost:.1f} = ${lq_default_profit_hq:.1f} profit.

**Your Profit Formula:**
Profit = (Selling Price) - (Production cost)

**Examples:**
- If you produce HQ and advertise HQ: Profit = ${hq_price:.1f} - ${hq_cost:.1f} = ${hq_default_profit:.1f}
- If you produce LQ and advertise HQ: Profit = ${hq_price:.1f} - ${lq_cost:.1f} = ${hq_price - lq_cost:.1f}
- If you produce LQ and advertise LQ: Profit = ${lq_price:.1f} - ${lq_cost:.1f} = ${lq_default_profit_lq:.1f}

**Important:** Selling prices for a product are as advertised. You cannot set custom prices. Your profit depends only on your production cost and the selling price for the advertised quality.

Note: Producing LQ and selling as HQ can earn higher profit (${hq_price - lq_cost:.1f} vs ${lq_default_profit_lq:.1f}), but buyers may rate you negatively, reducing your future sales potential
"""
            ).strip(),
            "reputation_and_warrant": (
                f"""
The payoff matrix below shows the cost of producing each quality type and the price you receive when selling it, so you can calculate how much profit you make from each combination.

**Production Costs:**
- HQ production cost: ${hq_cost:.1f}
- LQ production cost: ${lq_cost:.1f}

**Profit per Sale (production cost subtracted from selling price):**
- If you produce an HQ product and advertise it as HQ: a sale earns you ${hq_price:.1f} - ${hq_cost:.1f} = ${hq_default_profit:.1f} profit.
- If you produce an LQ product and advertise it as HQ: a sale earns you ${hq_price:.1f} - ${lq_cost:.1f} = ${hq_price - lq_cost:.1f} profit.
- If you produce an LQ product and advertise it as LQ: a sale earns you ${lq_price:.1f} - ${lq_cost:.1f} = ${lq_default_profit_lq:.1f} profit.
- If you produce an HQ product and advertise it as LQ: a sale earns you ${lq_price:.1f} - ${hq_cost:.1f} = ${lq_default_profit_hq:.1f} profit.

**Your Profit Formula:**
- If no challenge: Profit = (Selling Price) - (Production cost)
- If challenged and warrant offered: Profit = (Selling Price) - (Production cost) - (Warrant Escrow) penalty
  - **Penalty for HQ advertised claim**: -${hq_warrant_escrow:.1f}
  - **Penalty for LQ advertised claim**: -${lq_warrant_escrow:.1f}
- If challenged but no warrant: Profit = (Selling Price) - (Production cost) (no penalty)

**Examples:**
- Produce HQ, advertise HQ, no warrant, no challenge: Profit = ${hq_price:.1f} - ${hq_cost:.1f} = ${hq_default_profit:.1f}
- Produce LQ, advertise HQ, with warrant, challenged: Profit = ${hq_price:.1f} - ${lq_cost:.1f} - ${hq_warrant_escrow:.1f} = ${hq_price - lq_cost - hq_warrant_escrow:.1f}
- Produce LQ, advertise HQ, no warrant, challenged: Profit = ${hq_price:.1f} - ${lq_cost:.1f} = ${hq_price - lq_cost:.1f}

**Important:** Selling prices for a product are as advertised. You cannot set custom prices. Your profit depends on the selling price, production cost, and whether you get challenged (if you offer a warrant).

Note: If you offer a warrant on a misleading claim (LQ advertised as HQ) and get challenged, you lose the corresponding Warrant Escrow penalty!
"""
            ).strip(),
        }

    # Keep PAYOFF_MATRIX as class property for backward compatibility
    PAYOFF_MATRIX = ClassProperty(lambda cls: cls.get_payoff_matrix())

    @classmethod
    def get_master_prompt(cls) -> TextPrompt:
        """Get seller system prompt template with dynamic market parameters"""
        params = cls._get_market_params()
        hq_cost = params["hq_cost"]
        lq_cost = params["lq_cost"]
        hq_price = params["hq_price"]
        lq_price = params["lq_price"]

        return TextPrompt(
            f"""
# CONTEXT
You are a Seller Agent in a multi-round online marketplace simulation ('{{market_type}}' market). Your sole objective is to maximize your total profit over {{simulation_rounds}} rounds.

# GAME RULES - READ CAREFULLY

## Production & Selling
- **High quality (HQ) products** cost ${hq_cost:.1f} to produce
- **Low quality (LQ) products** cost ${lq_cost:.1f} to produce
- **You have a limited budget** - you can only list products if you have enough budget to cover the production cost
- **Budget constraint:** If your budget is less than the production cost, you cannot list that type of product
- **Buyers also have limited budgets** - buyers cannot necessarily purchase all the products you list. Listing many products does not guarantee all of them will be sold in a given round
- You may **advertise any quality regardless of your actual product quality**
- **Selling prices for a product are as advertised** - you cannot set custom prices. HQ products are priced at ${hq_price:.1f}, LQ products are priced at ${lq_price:.1f}
- Your profit = (selling price) - (production cost)
- **Your budget is reset to a fixed amount at the start of each round** — sales do NOT carry over
- **Listing a product deducts its production cost from your budget for that round**
- Buyers only see your **advertised quality** and **price** before a purchase
- Buyers find out the **true product quality** only after their purchase

## Reputation & Market Dynamics
{{market_rules}}

## ACTIONS RULES
{{actions}}

## Market Structure
- **{{simulation_rounds}} rounds total**, each round you must decide what to produce and advertise

# PRICING & PROFIT CALCULATION
{{payoff_matrix}}

**Remember:** The payoff matrix shows reference values. You can set your own price when listing a product to maximize your profit strategy!

# TASK (CRITICAL INSTRUCTION)
You must decide and execute EXACTLY ONE action for this round based on your current situation and the game rules.

**Instructions:**
1. **Assess your situation**: Analyze your current rating and past performance from the summary
2. **Formulate a plan**: Based on your current situation and the payoff structure, decide your plan for this round
3. **Execute the action**: You MUST call one of the available functions

Provide your step-by-step reasoning first, then execute your chosen function call.
"""
        )

    # Keep MASTER_PROMPT as class property for backward compatibility
    MASTER_PROMPT = ClassProperty(lambda cls: cls.get_master_prompt())

    # Seller round prompt template (dynamic parameters)
    ROUND_PROMPT = TextPrompt(
        """
# PREVIOUS ROUNDS' SUMMARY
{history_summary}

Please make your decision for this round.
"""
    )

    # LLM generation system prompt for sellers
    GENERATION_SYS_PROMPT = """You are generating seller agent profiles for a controlled market simulation experiment."""

    # LLM generation user prompt for sellers
    GENERATION_USER_PROMPT = """Create a seller profile for agent {0} in a market simulation.

Please provide a JSON response with the following structure:
{{
    "username": "seller_{0}",
    "description": "A seller participating in an online marketplace.",
    "user_char": "A rational market participant whose sole objective is to maximize total profit over the simulation by making strategic production and advertising decisions."
}}
"""

    @classmethod
    def get_market_rules(cls) -> dict[str, str]:
        """Get market rules descriptions with dynamic parameters"""
        params = cls._get_market_params()
        challenge_cost = params["challenge_cost"]
        hq_warrant_escrow = params["hq_warrant_escrow"]
        lq_warrant_escrow = params["lq_warrant_escrow"]
        hq_cost = params["hq_cost"]
        lq_cost = params["lq_cost"]
        hq_price = params["hq_price"]
        lq_price = params["lq_price"]

        hq_profit = hq_price - hq_cost
        lq_profit = lq_price - lq_cost

        return {
            "reputation_only": """
## Reputation System Only
1. **Reputation**: Buyers rate each transaction as +1 (thumbs-up) or -1 (thumbs-down)
   - Your Rating is tracked as 👍 thumbs-up and 👎 thumbs-down counts
   - A higher rating may attract more buyers
        """,
            "reputation_and_warrant": f"""
## Reputation & Truth Warrant System

1. **Reputation System**: Buyers rate each transaction as +1 (thumbs-up) or -1 (thumbs-down)
   - Your Rating is tracked as 👍 thumbs-up and 👎 thumbs-down counts

2. **Truth Warrant System**:
   - You can offer a "Truth Warrant" for your products by setting `has_warrant=True`
   - This signals to buyers that you're confident in your advertised quality
   - **If you warrant and advertise honestly**: You keep all your profits (${hq_profit:.1f} for HQ→HQ or ${lq_profit:.1f} for LQ→LQ)
   - **If you warrant and advertise misleadingly** (e.g., advertise HQ, produce LQ):
     - A buyer can challenge your warrant for ${challenge_cost:.1f}
     - If challenged, you LOSE points from your profit based on your advertised claim:
       - **Catching misleading HQ claim**: Lose ${hq_warrant_escrow:.1f} points
     - This penalty overrides any sales income from that transaction
   - Your warrant is only at risk if you are challenged for false advertising
        """,
        }

    # Keep MARKET_RULES as class property for backward compatibility
    MARKET_RULES = ClassProperty(lambda cls: cls.get_market_rules())

    @staticmethod
    def get_waiting_prompt(market_type: str) -> TextPrompt:
        """Get seller waiting prompt based on market type"""
        if market_type == "reputation_only":
            return TextPrompt(
                """
# The buyers are making their purchase decisions. 

While you wait, here's a reminder of the game mechanics:

## Production
• High quality products cost more to produce than low quality products
• High quality product sales earn more profit than low quality product sales
• Different quality and advertising strategies lead to different outcomes

## Advertising & Reputation
• Buyers only see the **advertised quality** (not the true quality) before they confirm a purchase
• You may advertise a different product quality than the true product quality
• Buyers find out the true product quality only after their purchase
• Your rating gets automatically updated based on buyer ratings (+1 (thumbs-up) / -1 (thumbs-down))

## Game Structure
{simulation_rounds} rounds total.
"""
            )
        else:
            return TextPrompt(
                """
# The buyers are making their purchase decisions. 

While you wait, here's a reminder of the game mechanics:

## Production
• High quality products cost more to produce than low quality products
• High quality product sales earn more profit than low quality product sales
• Different quality and advertising strategies lead to different outcomes

## Advertising & Reputation
• Buyers only see the **advertised quality** (not the true quality) before they confirm a purchase
• You may advertise a different product quality than the true product quality
• Buyers find out the true product quality only after their purchase
• Your rating gets automatically updated based on buyer ratings (+1 (thumbs-up) / -1 (thumbs-down))

## Warranties & Challenges
• You may offer a Truth Warrant for your product (has_warrant=True)
• This signals to buyers that your advertised quality is truthful
• **Warranted products only**: Buyers can challenge if they feel cheated by misleading quality
• If your warranted claim was misleading and challenged: you lose points from your profit based on your claim (e.g., $8 for HQ claims)
• If your warranted claim was honest: you keep all profits
• Your warrant is only at risk if challenged

## Game Structure
{simulation_rounds} rounds total.
"""
            )

    # Keep for backward compatibility (will use reputation_and_warrant version)
    WAITING_PROMPT = TextPrompt(
        """
# The buyers are making their purchase decisions. 

While you wait, here's a reminder of the game mechanics:

## Production
• High quality products cost more to produce than low quality products
• High quality product sales earn more profit than low quality product sales
• Different quality and advertising strategies lead to different outcomes

## Advertising & Reputation
• Buyers only see the **advertised quality** (not the true quality) before they confirm a purchase
• You may advertise a different product quality than the true product quality
• Buyers find out the true product quality only after their purchase
• Your rating gets automatically updated based on buyer ratings (+1 (thumbs-up) / -1 (thumbs-down))

## Warranties & Challenges
• You may offer a Truth Warrant for your product (has_warrant=True)
• This signals to buyers that your advertised quality is truthful
• **Warranted products only**: Buyers can challenge if they feel cheated by misleading quality
• If your warranted claim was misleading and challenged: you lose points from your profit based on your claim (e.g., $8 for HQ claims)
• If your warranted claim was honest: you keep all profits
• Your warrant is only at risk if challenged

## Game Structure
{simulation_rounds} rounds total.
"""
    )

    @classmethod
    def get_actions_and_payoff(cls, market_type: str) -> tuple[str, str]:
        """Select seller actions and payoff matrix based on market_type."""
        actions = cls.get_actions()
        payoff = cls.get_payoff_matrix()
        return (
            actions.get(market_type, actions["reputation_and_warrant"]),
            payoff.get(market_type, payoff["reputation_and_warrant"]),
        )


# ================== Buyer_prompt ==================


class Buyer_prompt:
    """All buyer-related prompts and configurations"""

    @staticmethod
    def _get_market_params():
        """Get market parameters from config"""
        return SimulationConfig.MARKET_PARAMS

    @classmethod
    def get_actions(cls) -> dict[str, str]:
        """Get available action descriptions for buyers in different markets"""
        params = cls._get_market_params()
        challenge_cost = params["challenge_cost"]
        hq_warrant_escrow = params["hq_warrant_escrow"]

        return {
            "reputation_only": (
                "Available Actions:\n"
                "1. `purchase_products(product_ids: list)`: Purchase multiple products by their product_ids. You must use this action to purchase products.\n"
                "   - `product_ids`: A list of product IDs (integers) to purchase\n"
                "   - Example: purchase_products([123, 124, 125])\n"
                "2. `rate_transactions(ratings: list)`: Rate multiple transactions after purchase. You must use this action to rate transactions.\n"
                "   - `ratings`: A list of rating specifications. Each rating is a dict with:\n"
                "     - `transaction_id` (int): The transaction ID to rate\n"
                "     - `rating` (int): The rating value (+1 (thumbs-up) or -1 (thumbs-down))\n"
                '   - Example: rate_transactions([{{{{"transaction_id": 456, "rating": 1}}}}, {{{{ "transaction_id": 457, "rating": -1}}}}])\n'
            ),
            "reputation_and_warrant": (
                "Available Actions:\n"
                "1. `purchase_products(product_ids: list)`: Purchase multiple products by their product_ids. You must use this action to purchase products.\n"
                "   - `product_ids`: A list of product IDs (integers) to purchase\n"
                "   - Example: purchase_products([123, 124, 125])\n"
                "2. `rate_transactions(ratings: list)`: Rate multiple transactions after purchase. You must use this action to rate transactions.\n"
                "   - `ratings`: A list of rating specifications. Each rating is a dict with:\n"
                "     - `transaction_id` (int): The transaction ID to rate\n"
                "     - `rating` (int): The rating value (+1 (thumbs-up) or -1 (thumbs-down))\n"
                '   - Example: rate_transactions([{{{{"transaction_id": 456, "rating": 1}}}}, {{{{ "transaction_id": 457, "rating": -1}}}}])\n'
                f"3. `challenge_warrants(challenges: list)`: Challenge multiple warranted products after purchase. You must use this action to challenge warrants (costs ${challenge_cost:.1f} per challenge).\n"
                "   - `challenges`: A list of challenge specifications. Each challenge is a dict with:\n"
                "     - `transaction_id` (int): The transaction ID to challenge\n"
                "     - `rating` (int): The rating value (+1 (thumbs-up) or -1 (thumbs-down))\n"
                "   - Only use if you received LQ when HQ was advertised with a warrant\n"
                f"   - Successful challenge earns you reward points (e.g., ${hq_warrant_escrow:.1f} for HQ claims)!\n"
                '   - Example: challenge_warrants([{{{{"transaction_id": 456, "rating": -1}}}}, {{{{ "transaction_id": 457, "rating": -1}}}}])\n'
            ),
        }

    # Keep ACTIONS as class property for backward compatibility
    ACTIONS = ClassProperty(lambda cls: cls.get_actions())

    @classmethod
    def get_payoff_matrix(cls) -> dict[str, str]:
        """Get utility matrix descriptions for buyers in different markets"""
        params = cls._get_market_params()
        hq_utility = params["hq_utility"]
        lq_utility = params["lq_utility"]
        challenge_cost = params["challenge_cost"]
        hq_warrant_escrow = params["hq_warrant_escrow"]
        lq_warrant_escrow = params["lq_warrant_escrow"]
        hq_price = params["hq_price"]
        lq_price = params["lq_price"]

        return {
            "reputation_only": (
                f"""
The payoff matrix below shows the price you pay for each advertised quality and the utility (value) you actually receive based on the true quality, so you can calculate how much net value you get from each purchase.

**Product Utility Values:**
- HQ (High Quality) product utility: ${hq_utility:.1f}
- LQ (Low Quality) product utility: ${lq_utility:.1f}

**Your Utility Formula:**
Utility = (Product Quality Utility) - (Purchase Price)

**Examples:**
- Buy HQ advertised as HQ at price ${hq_price:.1f}: Utility = ${hq_utility:.1f} - ${hq_price:.1f} = ${hq_utility - hq_price:.1f}
- Buy LQ advertised as HQ at price ${hq_price:.1f}: Utility = ${lq_utility:.1f} - ${hq_price:.1f} = ${lq_utility - hq_price:.1f} (you got cheated!)
- Buy LQ advertised as LQ at price ${lq_price:.1f}: Utility = ${lq_utility:.1f} - ${lq_price:.1f} = ${lq_utility - lq_price:.1f}
- Buy HQ advertised as LQ at price ${lq_price:.1f}: Utility = ${hq_utility:.1f} - ${lq_price:.1f} = ${hq_utility - lq_price:.1f} (great deal!)

**Important:**
- **Selling prices for a product are as advertised**: HQ products cost ${hq_price:.1f}, LQ products cost ${lq_price:.1f}. Sellers cannot change these prices.
- You only see the **advertised quality** and **price** before purchasing
- You discover the **true quality** only after purchase
- If you pay for HQ but receive LQ, you get cheated (utility = ${lq_utility:.1f} - ${hq_price:.1f} = ${lq_utility - hq_price:.1f})
"""
            ).strip(),
            "reputation_and_warrant": (
                f"""
The payoff matrix below shows the price you pay for each advertised quality and the utility (value) you actually receive based on the true quality, so you can calculate how much net value you get from each purchase.

**Product Utility Values:**
- HQ (High Quality) product utility: ${hq_utility:.1f}
- LQ (Low Quality) product utility: ${lq_utility:.1f}

**Challenge Cost:** ${challenge_cost:.1f}
**Warrant Escrow (based on advertised quality):**
- HQ claim escrow: ${hq_warrant_escrow:.1f}
- LQ claim escrow: ${lq_warrant_escrow:.1f}

**Your Utility Formula:**
- **If no challenge:** Utility = (Product Quality Utility) - (Purchase Price)
- **If challenge succeeds** (true quality is lower than advertised quality):
  Utility = (Product Quality Utility) - (Purchase Price) + (Warrant Escrow) + (Challenge Cost Refund) - (Challenge Cost)
  = (Product Quality Utility) - (Purchase Price) + ${hq_warrant_escrow:.1f} + ${challenge_cost:.1f} - ${challenge_cost:.1f}
  = (Product Quality Utility) - (Purchase Price) + ${hq_warrant_escrow:.1f}
- **If challenge fails** (true quality is equal to or higher than advertised quality):
  Utility = (Product Quality Utility) - (Purchase Price) - (Challenge Cost)
  = (Product Quality Utility) - (Purchase Price) - ${challenge_cost:.1f}

**Examples:**
- Buy HQ advertised as HQ at price ${hq_price:.1f}, no warrant, no challenge: Utility = ${hq_utility:.1f} - ${hq_price:.1f} = ${hq_utility - hq_price:.1f}
- Buy LQ advertised as HQ at price ${hq_price:.1f}, with warrant, challenge succeeds: 
  Utility = ${lq_utility:.1f} - ${hq_price:.1f} + ${hq_warrant_escrow:.1f} = ${lq_utility - hq_price + hq_warrant_escrow:.1f}
- Buy HQ advertised as HQ at price ${hq_price:.1f}, with warrant, challenge fails: 
  Utility = ${hq_utility:.1f} - ${hq_price:.1f} - ${challenge_cost:.1f} = ${hq_utility - hq_price - challenge_cost:.1f}
- Buy LQ advertised as LQ at price ${lq_price:.1f}, with warrant, challenge: 
  Utility = ${lq_utility:.1f} - ${lq_price:.1f} - ${challenge_cost:.1f} = ${lq_utility - lq_price - challenge_cost:.1f} (challenge fails because true quality is not lower than advertised quality)

**Important:**
- **Selling prices for a product are as advertised**: HQ products cost ${hq_price:.1f}, LQ products cost ${lq_price:.1f}. Sellers cannot change these prices.
- You can only challenge products with a **warrant** (has_warrant = True)
- You only see the **advertised quality**, **price**, and **warrant status** before purchasing
- You discover the **true quality** only after purchase
- Successful challenges (catching LQ advertised as HQ) earn you net reward based on advertised escrow (${hq_warrant_escrow:.1f} for HQ claims).
- Failed challenges cost you ${challenge_cost:.1f}
"""
            ).strip(),
        }

    # Keep PAYOFF_MATRIX as class property for backward compatibility
    PAYOFF_MATRIX = ClassProperty(lambda cls: cls.get_payoff_matrix())

    @classmethod
    def get_master_prompt(cls) -> TextPrompt:
        """Get buyer system prompt template with dynamic market parameters"""
        params = cls._get_market_params()
        hq_utility = params["hq_utility"]
        lq_utility = params["lq_utility"]
        hq_price = params["hq_price"]
        lq_price = params["lq_price"]

        return TextPrompt(
            f"""
# CONTEXT
You are a Buyer Agent in a multi-round online marketplace simulation ('{{market_type}}' market). Your sole objective is to maximize your total utility over {{simulation_rounds}} rounds.

# GAME RULES - READ CAREFULLY

## Buying Products
- Buy products based on **advertised claims** of high or low quality from different sellers
- **Advertisements may be misleading** - sellers can advertise one quality and deliver another
- **Product Quality Utility Values:**
  - High quality (HQ) products: ${hq_utility:.1f} utility
  - Low quality (LQ) products: ${lq_utility:.1f} utility
- **Your Utility Formula:** Utility = (Product Quality Utility) - (Purchase Price)
- **Selling prices for a product are as advertised** - HQ products are always ${hq_price:.1f}, LQ products are always ${lq_price:.1f}. Sellers cannot set custom prices.
- **You only see advertised quality and price before purchasing** - you discover true quality after purchase

## Reputation & Warranties
{{market_rules}}

## Market Structure
- **{{simulation_rounds}} rounds total**, each round you should make one strategic purchase
- Use seller ratings to make informed decisions

# PRICING & UTILITY CALCULATION
{{payoff_matrix}}

**Remember:** Selling prices for a product are as advertised. Use the payoff matrix above to calculate your exact expected utility before purchasing.

# TASK: YOUR DECISION WORKFLOW FOR THIS ROUND
Based on all the information above, you have the option to decide the subset of products you would like to purchase to maximize your cumulative utility.

**Consider:**
1. Product advertised quality and price
2. Seller rating (can they be trusted?){{warranty_consideration}}
3. Your potential returns
"""
        )

    # Keep MASTER_PROMPT as class property for backward compatibility
    MASTER_PROMPT = ClassProperty(lambda cls: cls.get_master_prompt())

    # Buyer round prompt template (dynamic parameters)
    ROUND_PROMPT = TextPrompt(
        """
Please make your decision for this round.
"""
    )

    # LLM generation system prompt for buyers
    GENERATION_SYS_PROMPT = """You are generating buyer agent profiles for a controlled market simulation experiment."""

    # LLM generation user prompt for buyers
    GENERATION_USER_PROMPT = """Create a buyer profile for agent {0} in a market simulation.

Please provide a JSON response with the following structure:
{{
    "username": "buyer_{0}",
    "description": "A buyer participating in an online marketplace.",
    "user_char": "A rational market participant whose sole objective is to maximize total utility over the simulation by making strategic purchasing decisions based on seller reputation and product information."
}}
"""

    @classmethod
    def get_market_rules(cls) -> dict[str, str]:
        """Get market rules descriptions with dynamic parameters"""
        params = cls._get_market_params()
        challenge_cost = params["challenge_cost"]
        hq_warrant_escrow = params["hq_warrant_escrow"]
        lq_warrant_escrow = params["lq_warrant_escrow"]

        return {
            "reputation_only": """
## Reputation System Only
1. You can rate each transaction as +1 (thumbs-up) or -1 (thumbs-down)
2. Your ratings affect the seller's rating (👍 thumbs-up and 👎 thumbs-down counts)
3. Use seller ratings to guide your purchasing decisions
4. There is NO warranty/challenge system in this market
5. You cannot challenge purchases after buying
        """,
            "reputation_and_warrant": f"""
## Reputation & Truth Warrant System

1. **Reputation System**: You can rate each transaction as +1 (thumbs-up) or -1 (thumbs-down)
   - Your ratings affect seller ratings (👍 thumbs-up and 👎 thumbs-down counts)

2. **Truth Warrants & Challenges**:
   - If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim and may be challenged.
   - This signals the seller is confident their advertised quality is truthful
   - **To challenge a warrant**: It costs you ${challenge_cost:.1f}
   - **If you win the challenge** (advertised HQ but received LQ): You earn reward points total based on the claim:
     - **Winning challenge against HQ claim**: Earn ${hq_warrant_escrow:.1f} points
     - **Winning challenge against LQ claim**: Earn ${lq_warrant_escrow:.1f} points
   - **If the warrant was honest**: You lose your ${challenge_cost:.1f} challenge fee
   - Only challenge warranted products where you received lower quality than advertised!
        """,
        }

    # Keep MARKET_RULES as class property for backward compatibility
    MARKET_RULES = ClassProperty(lambda cls: cls.get_market_rules())

    @staticmethod
    def get_waiting_prompt(market_type: str) -> TextPrompt:
        """Get buyer waiting prompt based on market type"""
        if market_type == "reputation_only":
            return TextPrompt(
                """
# The sellers are making production decisions.

While you wait, here's a reminder of the game mechanics:

## Buying Strategy
• Buy products based on advertised claims of high or low quality from different sellers
• **Advertisements may be misleading** - trust is important!
• High quality products give you more points than low quality but cost more

## Rating System
• After purchase, rate transactions as +1 (thumbs-up) or -1 (thumbs-down)
• Your ratings help build or damage seller ratings

## Game Structure
{simulation_rounds} rounds total. Make strategic decisions based on product quality, price, and seller rating.
"""
            )
        else:
            return TextPrompt(
                """
# The sellers are making production decisions.

While you wait, here's a reminder of the game mechanics:

## Buying Strategy
• Buy products based on advertised claims of high or low quality from different sellers
• **Advertisements may be misleading** - trust is important!
• High quality products give you more points than low quality but cost more

## Warranted Products
• If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim and may be challenged.
• This signals confidence in their advertised quality

## Challenging
• It costs you **$1** to challenge any warranted claim
• If a warranted product promised higher quality than you received, you will **win the challenge and earn reward points total based on the claim (e.g., $8 for HQ claims)**
• Only challenge warranted products where you suspect you were cheated!

## Rating System
• After purchase, rate transactions as +1 (thumbs-up) or -1 (thumbs-down)
• Your ratings help build or damage seller ratings

## Game Structure
{simulation_rounds} rounds total. Make strategic decisions based on product quality, price, seller rating, and whether products are warranted.
"""
            )

    # Keep for backward compatibility (will use reputation_and_warrant version)
    WAITING_PROMPT = TextPrompt(
        """
# The sellers are making production decisions.

While you wait, here's a reminder of the game mechanics:

## Buying Strategy
• Buy products based on advertised claims of high or low quality from different sellers
• **Advertisements may be misleading** - trust is important!
• High quality products give you more points than low quality but cost more

## Warranted Products
• If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim and may be challenged.
• This signals confidence in their advertised quality

## Challenging
• It costs you **$1** to challenge any warranted claim
• If a warranted product promised higher quality than you received, you will **win the challenge and earn reward points total based on the claim (e.g., $8 for HQ claims)**
• Only challenge warranted products where you suspect you were cheated!

## Rating System
• After purchase, rate transactions as +1 (thumbs-up) or -1 (thumbs-down)
• Your ratings help build or damage seller ratings

## Game Structure
{simulation_rounds} rounds total. Make strategic decisions based on product quality, price, seller rating, and whether products are warranted.
"""
    )

    @classmethod
    def get_actions_and_payoff(cls, market_type: str) -> tuple[str, str]:
        """Select buyer actions and payoff matrix based on market_type."""
        actions = cls.get_actions()
        payoff = cls.get_payoff_matrix()
        return (
            actions.get(market_type, actions["reputation_and_warrant"]),
            payoff.get(market_type, payoff["reputation_and_warrant"]),
        )


# ================== Market Environment Prompts ==================


class MarketEnv_prompt:
    """Market environment-related prompts for different roles to observe environment information in different phases"""

    # Environment observation for sellers in communication phase
    SELLER_COMMUNICATION_ENV = TextPrompt(
        """
# MARKET ENVIRONMENT OBSERVATION

## Available Posts for Communication
{available_posts}

"""
    )

    # Environment observation for sellers in listing_product phase
    SELLER_LISTING_ENV = TextPrompt(
        """
# MARKET ENVIRONMENT OBSERVATION

## Previous Round Purchase Feedback
{previous_feedback}

## Current Market Status
- Current Round: {current_round}/{simulation_rounds}
- Your Rating: 👍{thumbs_up_count} 👎{thumbs_down_count}
- Your Total Profit So Far: ${total_profit}
- Your Current Budget: ${budget}


Based on the feedback from previous rounds and current market conditions, decide what product to list this round.
**Check your budget before deciding which product to list!**
"""
    )

    @staticmethod
    def get_buyer_purchase_env(market_type: str) -> TextPrompt:
        """Get buyer purchase environment prompt based on market type"""
        if market_type == "reputation_only":
            return TextPrompt(
                """
# MARKET ENVIRONMENT OBSERVATION

## Your Status
- Round: {current_round}/{simulation_rounds}
- Cumulative Utility: {cumulative_utility:.2f}

## Available Products
{available_products}

## Purchase Decision
Based on the available products and seller ratings, decide which products to purchase.
"""
            )
        else:
            return TextPrompt(
                """
# MARKET ENVIRONMENT OBSERVATION

## Your Status
- Round: {current_round}/{simulation_rounds}
- Cumulative Utility: {cumulative_utility:.2f}

## Available Products
{available_products}

## Purchase Decision
Based on the available products, seller ratings, and warranty status, decide which products to purchase.
"""
            )

    # Keep for backward compatibility (will use reputation_and_warrant version)
    BUYER_PURCHASE_ENV = TextPrompt(
        """
# MARKET ENVIRONMENT OBSERVATION

## Your Status
- Round: {current_round}/{simulation_rounds}
- Cumulative Utility: {cumulative_utility:.2f}

## Available Products
{available_products}

## Purchase Decision
Based on the available products, seller ratings, and warranty status, decide which products to purchase.
"""
    )

    @staticmethod
    def get_buyer_rating_env(market_type: str) -> TextPrompt:
        """Get buyer rating environment prompt based on market type"""
        if market_type == "reputation_only":
            return TextPrompt(
                """
# MARKET ENVIRONMENT OBSERVATION

## All Your Purchases in This Round:
{transactions_text}

Based on your purchase experiences and the product details, decide how to rate each transaction.
Rate as +1 (thumbs-up) if the product met expectations, or -1 (thumbs-down) if it did not.

**Instructions:**
- You can rate multiple transactions at once using `rate_transactions()`
- Consider each product's quality relative to its advertised quality
- Be honest in your ratings to help other buyers make informed decisions
"""
            )
        else:
            return TextPrompt(
                """
# MARKET ENVIRONMENT OBSERVATION

## All Your Purchases in This Round:
{transactions_text}

Based on your purchase experiences and the product details, decide how to rate each transaction.
Rate as +1 (thumbs-up) if the product met expectations, or -1 (thumbs-down) if it did not.

**Instructions:**
- You can rate multiple transactions at once using `rate_transactions()`
- Be honest in your ratings to help other buyers make informed decisions
- Note: You will have a separate opportunity to challenge warranted products in the next phase
"""
            )

    # Keep for backward compatibility (will use reputation_and_warrant version)
    BUYER_RATING_ENV = TextPrompt(
        """
# MARKET ENVIRONMENT OBSERVATION

## Your Recent Purchase Details
- Transaction ID: {transaction_id}
- Product ID: {product_id}
- Advertised Quality: {advertised_quality}
- True Quality Received: {true_quality}
- Was Warranted: {has_warrant}
- Purchase Price: ${purchase_price}
- Your Utility from This Purchase: {buyer_utility}

## Seller Information
- Brand: {seller_brand}
- Rating: 👍{seller_thumbs_up} 👎{seller_thumbs_down}

Based on your purchase experience and the product details, decide how to rate this transaction.
Rate as +1 (thumbs-up) if the product met expectations, or -1 (thumbs-down) if it did not.

If you were cheated (advertised HQ, received LQ) on a warranted product, you can challenge for $1 to earn reward points (e.g., $8 for HQ claims)!
"""
    )


# ================== Backward Compatibility ==================
# Keep original variable names for backward compatibility

# Seller-related variables
SELLER_ACTIONS = Seller_prompt.ACTIONS
SELLER_PAYOFF_MATRIX = Seller_prompt.PAYOFF_MATRIX
SELLER_MASTER_PROMPT = Seller_prompt.MASTER_PROMPT
SELLER_ROUND_PROMPT = Seller_prompt.ROUND_PROMPT
SELLER_GENERATION_SYS_PROMPT = Seller_prompt.GENERATION_SYS_PROMPT
SELLER_GENERATION_USER_PROMPT = Seller_prompt.GENERATION_USER_PROMPT

# Buyer-related variables
BUYER_ACTIONS = Buyer_prompt.ACTIONS
BUYER_PAYOFF_MATRIX = Buyer_prompt.PAYOFF_MATRIX
BUYER_MASTER_PROMPT = Buyer_prompt.MASTER_PROMPT
BUYER_ROUND_PROMPT = Buyer_prompt.ROUND_PROMPT
BUYER_GENERATION_SYS_PROMPT = Buyer_prompt.GENERATION_SYS_PROMPT
BUYER_GENERATION_USER_PROMPT = Buyer_prompt.GENERATION_USER_PROMPT


# Helper functions
def get_seller_actions_and_payoff(market_type: str) -> tuple[str, str]:
    """Select seller actions and payoff matrix based on market_type."""
    return Seller_prompt.get_actions_and_payoff(market_type)


def get_buyer_actions_and_payoff(market_type: str) -> tuple[str, str]:
    """Select buyer actions and payoff matrix based on market_type."""
    return Buyer_prompt.get_actions_and_payoff(market_type)


# History formatting template
def format_seller_history(
    history_log: list, market_type: str = "reputation_and_warrant"
) -> str:
    """Format seller history log as string

    Args:
        history_log: List of history entries
        market_type: Market type ('reputation_only' or 'reputation_and_warrant')
    """
    if not history_log:
        return "This is the first round. You have no past performance data."

    history_string = "Here is a summary of your performance in previous rounds:\n"
    show_warrant = market_type != "reputation_only"

    for entry in history_log:
        round_num = entry["round"]
        true_quality = entry.get("true_quality", "N/A")
        advertised_quality = entry.get("advertised_quality", "N/A")
        warrant = entry.get("warrant", False)
        is_sold = entry.get("is_sold", 0)
        sold_numbers = entry.get("sold_numbers", 0)
        profit = entry.get("profit", 0)
        reputation = entry.get("reputation", 0)
        total_profit = entry.get("total_profit", 0)

        # Check if there are multiple product groups (different combinations)
        product_groups = entry.get("product_groups")
        total_listed = entry.get("total_products_listed", 1)

        if product_groups and len(product_groups) > 1:
            # Multiple product types in this round
            history_string += f"- Round {round_num}: Listed {total_listed} products with {len(product_groups)} different specifications:\n"
            for (adv_q, true_q, has_warr), group_info in product_groups.items():
                count = group_info["count"]
                sold = group_info["sold_count"]
                if show_warrant:
                    warrant_str = "with warrant" if has_warr else "without warrant"
                    history_string += f"  * {count} products: advertised as {adv_q}, true quality {true_q}, {warrant_str} (sold: {sold})\n"
                else:
                    history_string += f"  * {count} products: advertised as {adv_q}, true quality {true_q} (sold: {sold})\n"
            history_string += f"  Total sold: {sold_numbers} products. Round Profit: {profit:.2f}. New Rating: {reputation:.1f}. Total Profit: {total_profit:.2f}\n"
        else:
            # Single product type or backward compatibility
            if show_warrant:
                warrant_str = "with warrant" if warrant else "without warrant"
                if total_listed > 1:
                    history_string += f"- Round {round_num}: Listed {total_listed} products (True_quality {true_quality}, advertised_quality {advertised_quality}, {warrant_str}). Sold: {sold_numbers} products. Round Profit: {profit:.2f}. New Rating: {reputation:.1f}. Total Profit: {total_profit:.2f}\n"
                else:
                    history_string += f"- Round {round_num}: Listed a True_quality {true_quality} and advertised_quality {advertised_quality} product ({warrant_str}). Sold: {is_sold} and got {sold_numbers} products. Round Profit: {profit:.2f}. New Rating: {reputation:.1f}. Total Profit: {total_profit:.2f}\n"
            else:
                if total_listed > 1:
                    history_string += f"- Round {round_num}: Listed {total_listed} products (True_quality {true_quality}, advertised_quality {advertised_quality}). Sold: {sold_numbers} products. Round Profit: {profit:.2f}. New Rating: {reputation:.1f}. Total Profit: {total_profit:.2f}\n"
                else:
                    history_string += f"- Round {round_num}: Listed a True_quality {true_quality} and advertised_quality {advertised_quality} product. Sold: {is_sold} and got {sold_numbers} products. Round Profit: {profit:.2f}. New Rating: {reputation:.1f}. Total Profit: {total_profit:.2f}\n"

    return history_string


def get_prompt_child(role: str, child: str, market_type: str = None):
    # Select corresponding class
    cls = (
        Seller_prompt if role == "seller" else Buyer_prompt if role == "buyer" else None
    )

    # Properties that need market_type selection
    market_type_dict_keys = [
        "ACTIONS",
        "PAYOFF_MATRIX",
        "MARKET_RULES",
        "MASTER_PROMPT",
    ]
    child_upper = child.upper()

    attr = getattr(cls, child_upper)

    # If attribute is dict and needs market_type, get value for corresponding market_type
    if child_upper in market_type_dict_keys and isinstance(attr, dict):
        return attr.get(market_type)
    else:
        return attr
