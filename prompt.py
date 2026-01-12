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
        hq_price = params['hq_price']
        lq_price = params['lq_price']
        hq_cost = params['hq_cost']
        lq_cost = params['lq_cost']
        
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
                f"  - Example 1 (multiple types): list_products([{{{{\"advertised_quality\": \"HQ\", \"product_quality\": \"HQ\", \"quantity\": 2}}}}, {{{{ \"advertised_quality\": \"LQ\", \"product_quality\": \"LQ\", \"quantity\": 1}}}}])\n"
                f"  - Example 2 (single type): list_products([{{{{\"advertised_quality\": \"HQ\", \"product_quality\": \"LQ\", \"quantity\": 5}}}}])\n"
                f"  - Production Costs: HQ products cost ${hq_cost:.1f} to produce, LQ products cost ${lq_cost:.1f} to produce\n"
                f"  - Fixed Prices: HQ products are priced at ${hq_price:.1f}, LQ products are priced at ${lq_price:.1f}. You cannot change the price.\n"
        ),
        "reputation_and_warrant": (
            "Available Actions:\n"
                f"- `list_products(products: list)`: List products for sale. You must use this action to list products.\n"
            "  - `products`: A list of product specifications. Each product is a dict with:\n"
            "    - `advertised_quality` (str): What you tell buyers ('HQ' or 'LQ')\n"
            "    - `product_quality` (str): What you actually produce ('HQ' or 'LQ')\n"
            "    - `has_warrant` (bool, optional): Whether to offer a Truth Warrant (default: False)\n"
            "    - `quantity` (int, optional): Number of products with this specification (default: 1)\n"
            "  - **CRITICAL**: Each unique combination of (advertised_quality, product_quality, has_warrant) is a DIFFERENT product type.\n"
            "    For example, (LQ, HQ, has_warrant=True) and (LQ, HQ, has_warrant=False) are TWO different product types.\n"
            "    You can specify different quantities for each unique combination in a single `list_products()` call.\n"
            "  - **IMPORTANT**: You can list MULTIPLE DIFFERENT TYPES of products in a single call. This allows you to:\n"
            "    * Diversify your product portfolio (e.g., mix of HQ and LQ products, with or without warrants)\n"
            "    * Target different buyer segments simultaneously\n"
            "    * Balance risk and profit by offering various quality and warranty combinations\n"
            "    * Maximize your budget utilization across different product types\n"
            "  - **Examples of different product type combinations**:\n"
            "    * (HQ, HQ, has_warrant=True) - Honest high quality with warrant\n"
            "    * (HQ, HQ, has_warrant=False) - Honest high quality without warrant\n"
            "    * (HQ, LQ, has_warrant=True) - Fraudulent high quality claim with warrant (risky!)\n"
            "    * (HQ, LQ, has_warrant=False) - Fraudulent high quality claim without warrant\n"
            "    * (LQ, LQ, has_warrant=True) - Honest low quality with warrant\n"
            "    * (LQ, LQ, has_warrant=False) - Honest low quality without warrant\n"
            "    * (LQ, HQ, has_warrant=True) - Under-advertising with warrant\n"
            "    * (LQ, HQ, has_warrant=False) - Under-advertising without warrant\n"
                f"  - Example 1 (multiple types with different warrant status): list_products([{{{{\"advertised_quality\": \"HQ\", \"product_quality\": \"HQ\", \"has_warrant\": True, \"quantity\": 2}}}}, {{{{ \"advertised_quality\": \"HQ\", \"product_quality\": \"HQ\", \"has_warrant\": False, \"quantity\": 3}}}}, {{{{ \"advertised_quality\": \"LQ\", \"product_quality\": \"LQ\", \"quantity\": 1}}}}])\n"
                f"  - Example 2 (fraudulent with and without warrant): list_products([{{{{\"advertised_quality\": \"HQ\", \"product_quality\": \"LQ\", \"has_warrant\": True, \"quantity\": 2}}}}, {{{{ \"advertised_quality\": \"HQ\", \"product_quality\": \"LQ\", \"has_warrant\": False, \"quantity\": 5}}}}])\n"
                f"  - Production Costs: HQ products cost ${hq_cost:.1f} to produce, LQ products cost ${lq_cost:.1f} to produce\n"
                f"  - Fixed Prices: HQ products are priced at ${hq_price:.1f}, LQ products are priced at ${lq_price:.1f}. You cannot change the price.\n"
        ),
    }

    # Keep ACTIONS as class property for backward compatibility
    ACTIONS = ClassProperty(lambda cls: cls.get_actions())

    @classmethod
    def get_payoff_matrix(cls) -> dict[str, str]:
        """Get payoff matrix descriptions for sellers in different markets"""
        params = cls._get_market_params()
        hq_cost = params['hq_cost']
        lq_cost = params['lq_cost']
        hq_price = params['hq_price']
        lq_price = params['lq_price']
        hq_warrant_escrow = params['hq_warrant_escrow']
        lq_warrant_escrow = params['lq_warrant_escrow']
        
        hq_default_profit = hq_price - hq_cost
        lq_default_profit_lq = lq_price - lq_cost
        lq_default_profit_hq = lq_price - hq_cost
        
        return {
        "reputation_only": (
                f"""
**Production Costs:**
- HQ production cost: ${hq_cost:.1f}
- LQ production cost: ${lq_cost:.1f}

**Fixed Prices (set by the market, you cannot change them):**
- HQ advertised: ${hq_price:.1f} (profit: ${hq_default_profit:.1f})
- LQ advertised: ${lq_price:.1f} (profit: ${lq_default_profit_lq:.1f} for LQ, ${lq_default_profit_hq:.1f} for HQ)

**Your Profit Formula:**
Profit = (Fixed Price) - (Production cost)

**Examples:**
- If you produce HQ and advertise HQ: Profit = ${hq_price:.1f} - ${hq_cost:.1f} = ${hq_default_profit:.1f}
- If you produce LQ and advertise HQ: Profit = ${hq_price:.1f} - ${lq_cost:.1f} = ${hq_price - lq_cost:.1f}
- If you produce LQ and advertise LQ: Profit = ${lq_price:.1f} - ${lq_cost:.1f} = ${lq_default_profit_lq:.1f}

**Important:** Prices are FIXED by the market. You cannot set custom prices. Your profit depends only on your production cost and the fixed price for the advertised quality.

Note: Producing LQ and selling as HQ can earn higher profit (${hq_price - lq_cost:.1f} vs ${lq_default_profit_lq:.1f}), but buyers may rate you negatively, reducing your future sales potential
"""
        ).strip(),
        "reputation_and_warrant": (
                f"""
**Production Costs:**
- HQ production cost: ${hq_cost:.1f}
- LQ production cost: ${lq_cost:.1f}

**Fixed Prices (set by the market, you cannot change them):**
- HQ advertised: ${hq_price:.1f} (profit: ${hq_default_profit:.1f})
- LQ advertised: ${lq_price:.1f} (profit: ${lq_default_profit_lq:.1f} for LQ, ${lq_default_profit_hq:.1f} for HQ)

**Your Profit Formula:**
- If no challenge: Profit = (Fixed Price) - (Production cost)
- If challenged and warrant offered: Profit = (Fixed Price) - (Production cost) - (Warrant Escrow) penalty
  - **Penalty for HQ advertised claim**: -${hq_warrant_escrow:.1f}
  - **Penalty for LQ advertised claim**: -${lq_warrant_escrow:.1f}
- If challenged but no warrant: Profit = (Fixed Price) - (Production cost) (no penalty)

**Examples:**
- Produce HQ, advertise HQ, no warrant, no challenge: Profit = ${hq_price:.1f} - ${hq_cost:.1f} = ${hq_default_profit:.1f}
- Produce LQ, advertise HQ, with warrant, challenged: Profit = ${hq_price:.1f} - ${lq_cost:.1f} - ${hq_warrant_escrow:.1f} = ${hq_price - lq_cost - hq_warrant_escrow:.1f}
- Produce LQ, advertise HQ, no warrant, challenged: Profit = ${hq_price:.1f} - ${lq_cost:.1f} = ${hq_price - lq_cost:.1f}

**Important:** Prices are FIXED by the market. You cannot set custom prices. Your profit depends on the fixed price, production cost, and whether you get challenged (if you offer a warrant).

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
        hq_cost = params['hq_cost']
        lq_cost = params['lq_cost']
        hq_price = params['hq_price']
        lq_price = params['lq_price']
        
        return TextPrompt(
            f"""
# CONTEXT
You are a Seller Agent in a multi-round online marketplace simulation ('{{market_type}}' market). Your sole objective is to maximize your total profit over {{simulation_rounds}} rounds.

# YOUR PERSONALITY
{{user_profile}}

# GAME RULES - READ CAREFULLY

## Production & Selling
- **High quality (HQ) products** cost ${hq_cost:.1f} to produce
- **Low quality (LQ) products** cost ${lq_cost:.1f} to produce
- **You have a limited budget** - you can only list products if you have enough budget to cover the production cost
- **Budget constraint:** If your budget is less than the production cost, you cannot list that type of product
- You may **advertise any quality regardless of your actual product quality**
- **Prices are FIXED by the market** - you cannot set custom prices. HQ products are priced at ${hq_price:.1f}, LQ products are priced at ${lq_price:.1f}
- Your profit = (fixed price) - (production cost)
- **Your budget decreases by the production cost when you list a product**
- **Your budget increases when you make a sale** (you receive the selling price)
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
You must decide and execute EXACTLY ONE action for this round based on your personality, current situation, and the game rules.

**Instructions:**
1. **Assess your situation**: Analyze your current rating and past performance from the summary
2. **Formulate a plan**: Based on your PERSONALITY, decide your plan for this round
3. **Execute the action**: You MUST call one of the available functions

Provide your step-by-step reasoning first, then execute your chosen function call.
Please actively take actions and participate in the market. Do not repeatedly refuse to execute any action.
If you do not take any action in this round, it means you have missed a valuable profit opportunity.

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
    GENERATION_SYS_PROMPT = """You are an expert in creating diverse seller personas for a market simulation.
Your task is to generate unique seller characteristics that will lead to different behaviors in an online marketplace.
Each seller should have distinct backgrounds, professions, ages, interests, genders, and personal mottos, resulting in a wide variety of personalities and approaches."""

    # LLM generation user prompt for sellers
    GENERATION_USER_PROMPT = """Create a unique seller persona for agent {0} in a market simulation.
The seller operates in an online marketplace where they can list products with different quality levels.

Please provide a JSON response with the following structure:
{{
    "username": "seller_{0}",
    "description": "A brief description of this seller's background, such as profession, age, interests, gender, and personal motto.",
    "user_char": "A detailed character description including their motivation, strategy, risk tolerance, and typical behavior patterns. This should be 2-3 sentences that will guide their decision-making in the marketplace, focusing on their life experience, personality, and unique perspective."
}}

Make each seller distinct by varying:
- Profession (e.g., student, retired engineer, artist, single parent, etc.)
- Age group (e.g., young adult, middle-aged, senior)
- Interests and hobbies
- Gender identity
- Personal motto or signature
- Approach to business (e.g., enthusiastic, cautious, innovative, traditional)
- Long-term vs short-term thinking"""

    @classmethod
    def get_market_rules(cls) -> dict[str, str]:
        """Get market rules descriptions with dynamic parameters"""
        params = cls._get_market_params()
        challenge_cost = params['challenge_cost']
        hq_warrant_escrow = params['hq_warrant_escrow']
        lq_warrant_escrow = params['lq_warrant_escrow']
        hq_cost = params['hq_cost']
        lq_cost = params['lq_cost']
        hq_price = params['hq_price']
        lq_price = params['lq_price']
        
        hq_profit = hq_price - hq_cost
        lq_profit = lq_price - lq_cost
        
        return {
        "reputation_only": """
## Reputation System Only
1. **Reputation**: Buyers can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
   - Your Rating is tracked as 👍 thumbs-up and 👎 thumbs-down counts
   - A higher rating may attract more buyers
         """,
            "reputation_and_warrant": f"""
## Reputation & Truth Warrant System

1. **Reputation System**: Buyers can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
   - Your Rating is tracked as 👍 thumbs-up and 👎 thumbs-down counts

2. **Truth Warrant System**:
   - You can offer a "Truth Warrant" for your products by setting `has_warrant=True`
   - This signals to buyers that you're confident in your advertised quality
   - **If you warrant and advertise honestly**: You keep all your profits (${hq_profit:.1f} for HQ→HQ or ${lq_profit:.1f} for LQ→LQ)
   - **If you warrant and advertise misleadingly** (e.g., advertise HQ, produce LQ):
     - A buyer can challenge your warrant for ${challenge_cost:.1f}
     - If challenged, you LOSE points from your profit based on your advertised claim:
       - **Catching misleading HQ claim**: Lose ${hq_warrant_escrow:.1f} points
       - **Catching misleading LQ claim**: Lose ${lq_warrant_escrow:.1f} points
     - This penalty overrides any sales income from that transaction
   - Your warrant is only at risk if you are challenged for false advertising
         """,
    }

    # Keep MARKET_RULES as class property for backward compatibility
    MARKET_RULES = ClassProperty(lambda cls: cls.get_market_rules())

    @staticmethod
    def get_waiting_prompt(market_type: str) -> TextPrompt:
        """Get seller waiting prompt based on market type"""
        if market_type == 'reputation_only':
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
• Your rating gets automatically updated based on buyer ratings (-2 to +2 scale)

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
• Your rating gets automatically updated based on buyer ratings (-2 to +2 scale)

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
• Your rating gets automatically updated based on buyer ratings (-2 to +2 scale)

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
            payoff.get(market_type, payoff["reputation_and_warrant"])
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
        challenge_cost = params['challenge_cost']
        hq_warrant_escrow = params['hq_warrant_escrow']
        
        return {
        "reputation_only": (
            "Available Actions:\n"
            "1. `purchase_products(product_ids: list)`: Purchase multiple products by their product_ids. You must use this action to purchase products.\n"
            "   - `product_ids`: A list of product IDs (integers) to purchase\n"
            "   - Example: purchase_products([123, 124, 125])\n"
            "2. `rate_transactions(ratings: list)`: Rate multiple transactions after purchase. You must use this action to rate transactions.\n"
            "   - `ratings`: A list of rating specifications. Each rating is a dict with:\n"
            "     - `transaction_id` (int): The transaction ID to rate\n"
            "     - `rating` (int): The rating value (range: -2 to 2)\n"
            "   - Rating scale: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)\n"
            "   - Example: rate_transactions([{{{{\"transaction_id\": 456, \"rating\": 2}}}}, {{{{ \"transaction_id\": 457, \"rating\": 1}}}}])\n"
        ),
        "reputation_and_warrant": (
            "Available Actions:\n"
            "1. `purchase_products(product_ids: list)`: Purchase multiple products by their product_ids. You must use this action to purchase products.\n"
            "   - `product_ids`: A list of product IDs (integers) to purchase\n"
            "   - Example: purchase_products([123, 124, 125])\n"
            "2. `rate_transactions(ratings: list)`: Rate multiple transactions after purchase. You must use this action to rate transactions.\n"
            "   - `ratings`: A list of rating specifications. Each rating is a dict with:\n"
            "     - `transaction_id` (int): The transaction ID to rate\n"
            "     - `rating` (int): The rating value (range: -2 to 2)\n"
            "   - Rating scale: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)\n"
            "   - Example: rate_transactions([{{{{\"transaction_id\": 456, \"rating\": 2}}}}, {{{{ \"transaction_id\": 457, \"rating\": 1}}}}])\n"
                f"3. `challenge_warrants(challenges: list)`: Challenge multiple warranted products after purchase. You must use this action to challenge warrants (costs ${challenge_cost:.1f} per challenge).\n"
            "   - `challenges`: A list of challenge specifications. Each challenge is a dict with:\n"
            "     - `transaction_id` (int): The transaction ID to challenge\n"
            "     - `rating` (int): The rating value (range: -2 to 2)\n"
            "   - Only use if you received LQ when HQ was advertised with a warrant\n"
                f"   - Successful challenge earns you reward points (e.g., ${hq_warrant_escrow:.1f} for HQ claims)!\n"
            "   - Example: challenge_warrants([{{{{\"transaction_id\": 456, \"rating\": -2}}}}, {{{{ \"transaction_id\": 457, \"rating\": -1}}}}])\n"
        ),
    }

    # Keep ACTIONS as class property for backward compatibility
    ACTIONS = ClassProperty(lambda cls: cls.get_actions())

    @classmethod
    def get_payoff_matrix(cls) -> dict[str, str]:
        """Get utility matrix descriptions for buyers in different markets"""
        params = cls._get_market_params()
        hq_utility = params['hq_utility']
        lq_utility = params['lq_utility']
        challenge_cost = params['challenge_cost']
        hq_warrant_escrow = params['hq_warrant_escrow']
        lq_warrant_escrow = params['lq_warrant_escrow']
        hq_price = params['hq_price']
        lq_price = params['lq_price']
        
        return {
        "reputation_only": (
                f"""
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
- The price is set by the seller (they can set any price they want)
- You only see the **advertised quality** and **price** before purchasing
- You discover the **true quality** only after purchase
- If you pay for HQ but receive LQ, you get cheated (utility = ${lq_utility:.1f} - price, which could be negative if price > ${lq_utility:.1f})
"""
        ).strip(),
        "reputation_and_warrant": (
                f"""
**Product Utility Values:**
- HQ (High Quality) product utility: ${hq_utility:.1f}
- LQ (Low Quality) product utility: ${lq_utility:.1f}

**Challenge Cost:** ${challenge_cost:.1f}
**Warrant Escrow (based on advertised quality):**
- HQ claim escrow: ${hq_warrant_escrow:.1f}
- LQ claim escrow: ${lq_warrant_escrow:.1f}

**Your Utility Formula:**
- **If no challenge:** Utility = (Product Quality Utility) - (Purchase Price)
- **If challenge succeeds** (LQ advertised as HQ with warrant): 
  Utility = (Product Quality Utility) - (Purchase Price) + (Warrant Escrow) + (Challenge Cost Refund) - (Challenge Cost)
  = (Product Quality Utility) - (Purchase Price) + ${hq_warrant_escrow:.1f} + ${challenge_cost:.1f} - ${challenge_cost:.1f}
  = (Product Quality Utility) - (Purchase Price) + ${hq_warrant_escrow:.1f}
- **If challenge fails** (HQ advertised as HQ with warrant): 
  Utility = (Product Quality Utility) - (Purchase Price) - (Challenge Cost)
  = (Product Quality Utility) - (Purchase Price) - ${challenge_cost:.1f}

**Examples:**
- Buy HQ advertised as HQ at price ${hq_price:.1f}, no warrant, no challenge: Utility = ${hq_utility:.1f} - ${hq_price:.1f} = ${hq_utility - hq_price:.1f}
- Buy LQ advertised as HQ at price ${hq_price:.1f}, with warrant, challenge succeeds: 
  Utility = ${lq_utility:.1f} - ${hq_price:.1f} + ${hq_warrant_escrow:.1f} = ${lq_utility - hq_price + hq_warrant_escrow:.1f}
- Buy HQ advertised as HQ at price ${hq_price:.1f}, with warrant, challenge fails: 
  Utility = ${hq_utility:.1f} - ${hq_price:.1f} - ${challenge_cost:.1f} = ${hq_utility - hq_price - challenge_cost:.1f}
- Buy LQ advertised as LQ at price ${lq_price:.1f}, with warrant, challenge: 
  Utility = ${lq_utility:.1f} - ${lq_price:.1f} - ${challenge_cost:.1f} = ${lq_utility - lq_price - challenge_cost:.1f} (challenge fails because product matches advertisement)

**Important:** 
- The price is set by the seller (they can set any price they want)
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
        hq_utility = params['hq_utility']
        lq_utility = params['lq_utility']
        hq_price = params['hq_price']
        lq_price = params['lq_price']
        
        return TextPrompt(
            f"""
# CONTEXT
You are a Buyer Agent in a multi-round online marketplace simulation ('{{market_type}}' market). Your sole objective is to maximize your total utility over {{simulation_rounds}} rounds.

# YOUR PERSONALITY
{{user_profile}}

# GAME RULES - READ CAREFULLY

## Buying Products
- Buy products based on **advertised claims** of high or low quality from different sellers
- **Advertisements may be misleading** - sellers can advertise one quality and deliver another
- **Product Quality Utility Values:**
  - High quality (HQ) products: ${hq_utility:.1f} utility
  - Low quality (LQ) products: ${lq_utility:.1f} utility
- **Your Utility Formula:** Utility = (Product Quality Utility) - (Purchase Price)
- **The price is set by sellers** - they can set any price they want (default: HQ ${hq_price:.1f}, LQ ${lq_price:.1f})
- **You only see advertised quality and price before purchasing** - you discover true quality after purchase

## Reputation & Warranties
{{market_rules}}

## Market Structure
- **{{simulation_rounds}} rounds total**, each round you should make one strategic purchase
- Use seller ratings to make informed decisions

# PRICING & UTILITY CALCULATION
{{payoff_matrix}}

**Remember:** The payoff matrix shows the calculation formula. The actual utility depends on the price set by sellers, which can vary!

# TASK: YOUR DECISION WORKFLOW FOR THIS ROUND
Based on all the information above, decide which product you should purchase to maximize your cumulative utility. (You should only purchase once per round!)

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
    GENERATION_SYS_PROMPT = """You are an expert in creating diverse buyer personas for a market simulation.
Your task is to generate unique buyer characteristics that will lead to different purchasing behaviors in an online marketplace.
Each buyer should have distinct backgrounds, professions, ages, interests, genders, and personal mottos, resulting in a wide variety of personalities and decision-making styles."""

    # LLM generation user prompt for buyers
    GENERATION_USER_PROMPT = """Create a unique buyer persona for agent {0} in a market simulation.
The buyer operates in an online marketplace where they can purchase products from sellers with different reputation levels and choose whether to buy warranted or unwarranted products.

Please provide a JSON response with the following structure:
{{
    "username": "buyer_{0}",
    "description": "A brief description of this buyer's background, such as profession, age, interests, gender, and personal motto.",
    "user_char": "A detailed character description including their purchasing preferences, risk tolerance, and decision-making criteria. This should be 2-3 sentences that will guide their buying behavior in the marketplace, focusing on their life experience, personality, and unique perspective."
}}

Make each buyer distinct by varying:
- Profession (e.g., tech enthusiast, retiree, student, parent, etc.)
- Age group (e.g., teenager, adult, senior)
- Interests and hobbies
- Gender identity
- Personal motto or signature
- Shopping style (e.g., impulsive, analytical, bargain-seeker, quality-focused)
- Information gathering behavior"""

    @classmethod
    def get_market_rules(cls) -> dict[str, str]:
        """Get market rules descriptions with dynamic parameters"""
        params = cls._get_market_params()
        challenge_cost = params['challenge_cost']
        hq_warrant_escrow = params['hq_warrant_escrow']
        lq_warrant_escrow = params['lq_warrant_escrow']
        
        return {
        "reputation_only": """
## Reputation System Only
1. You can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
2. Your ratings affect the seller's rating (👍 thumbs-up and 👎 thumbs-down counts)
3. Use seller ratings to guide your purchasing decisions
4. There is NO warranty/challenge system in this market
5. You cannot challenge purchases after buying
         """,
            "reputation_and_warrant": f"""
## Reputation & Truth Warrant System

1. **Reputation System**: You can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
   - Your ratings affect seller ratings (👍 thumbs-up and 👎 thumbs-down counts)

2. **Truth Warrants & Challenges**:
   - If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim
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
        if market_type == 'reputation_only':
            return TextPrompt(
                """
# The sellers are making production decisions.

While you wait, here's a reminder of the game mechanics:

## Buying Strategy
• Buy products based on advertised claims of high or low quality from different sellers
• **Advertisements may be misleading** - trust is important!
• High quality products give you more points than low quality but cost more

## Rating System
• After purchase, rate transactions on a -2 to +2 scale:
  - +2 (very good), +1 (good), 0 (neutral), -1 (bad), -2 (very bad)
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
• If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim
• This signals confidence in their advertised quality

## Challenging
• It costs you **$1** to challenge any warranted claim
• If a warranted product promised higher quality than you received, you will **win the challenge and earn reward points total based on the claim (e.g., $8 for HQ claims)**
• Only challenge warranted products where you suspect you were cheated!

## Rating System
• After purchase, rate transactions on a -2 to +2 scale:
  - +2 (very good), +1 (good), 0 (neutral), -1 (bad), -2 (very bad)
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
• If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim
• This signals confidence in their advertised quality

## Challenging
• It costs you **$1** to challenge any warranted claim
• If a warranted product promised higher quality than you received, you will **win the challenge and earn reward points total based on the claim (e.g., $8 for HQ claims)**
• Only challenge warranted products where you suspect you were cheated!

## Rating System
• After purchase, rate transactions on a -2 to +2 scale:
  - +2 (very good), +1 (good), 0 (neutral), -1 (bad), -2 (very bad)
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
            payoff.get(market_type, payoff["reputation_and_warrant"])
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
        if market_type == 'reputation_only':
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
        if market_type == 'reputation_only':
            return TextPrompt(
                """
# MARKET ENVIRONMENT OBSERVATION

## All Your Purchases in This Round:
{transactions_text}

Based on your purchase experiences and the product details, decide how to rate each transaction.
Rate on a scale from -2 to +2: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)

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
Rate on a scale from -2 to +2: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)

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
Rate on a scale from -2 to +2: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)

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
def format_seller_history(history_log: list, market_type: str = "reputation_and_warrant") -> str:
    """Format seller history log as string
    
    Args:
        history_log: List of history entries
        market_type: Market type ('reputation_only' or 'reputation_and_warrant')
    """
    if not history_log:
        return "This is the first round. You have no past performance data."

    history_string = "Here is a summary of your performance in previous rounds:\n"
    show_warrant = (market_type != 'reputation_only')
    
    for entry in history_log:
        round_num = entry['round']
        true_quality = entry.get('true_quality', 'N/A')
        advertised_quality = entry.get('advertised_quality', 'N/A')
        warrant = entry.get('warrant', False)
        is_sold = entry.get('is_sold', 0)
        sold_numbers = entry.get('sold_numbers', 0)
        profit = entry.get('profit', 0)
        reputation = entry.get('reputation', 0)
        total_profit = entry.get('total_profit', 0)
        
        # Check if there are multiple product groups (different combinations)
        product_groups = entry.get('product_groups')
        total_listed = entry.get('total_products_listed', 1)
        
        if product_groups and len(product_groups) > 1:
            # Multiple product types in this round
            history_string += f"- Round {round_num}: Listed {total_listed} products with {len(product_groups)} different specifications:\n"
            for (adv_q, true_q, has_warr), group_info in product_groups.items():
                count = group_info['count']
                sold = group_info['sold_count']
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
