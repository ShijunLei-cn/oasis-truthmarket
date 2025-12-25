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
        
        return {
            "reputation_only": (
                "Available Actions:\n"
                f"- `list_product(advertised_quality: str, product_quality: str, price: float = None)`: Your primary action to make a profit.\n"
                "  - `advertised_quality`: What you tell buyers ('HQ' or 'LQ')\n"
                "  - `product_quality`: What you actually produce ('HQ' or 'LQ')\n"
                f"  - `price`: (Optional) The price you want to set for this product. If not specified, defaults to HQ: ${hq_price:.1f}, LQ: ${lq_price:.1f}. You can set any positive price to maximize profit or compete with other sellers.\n"
                "  - Note: `has_warrant` is NOT available in this market\n"
                "- `exit_market()`: Exit the market\n"
                "- `reenter_market()`: Re-enter with fresh reputation (available at round {reentry_round})"
            ),
            "reputation_and_warrant": (
                "Available Actions:\n"
                f"- `list_product(advertised_quality: str, product_quality: str, has_warrant: bool, price: float = None)`: Your primary action to make a profit.\n"
                "  - `advertised_quality`: What you tell buyers ('HQ' or 'LQ')\n"
                "  - `product_quality`: What you actually produce ('HQ' or 'LQ')\n"
                "  - `has_warrant`: Whether to offer a Truth Warrant (True/False)\n"
                f"  - `price`: (Optional) The price you want to set for this product. If not specified, defaults to HQ: ${hq_price:.1f}, LQ: ${lq_price:.1f}. You can set any positive price to maximize profit or compete with other sellers.\n"
                "- `exit_market()`: Exit the market\n"
                "- `reenter_market()`: Re-enter with fresh reputation (available at round {reentry_round})"
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
        warrant_escrow = params['warrant_escrow']
        
        hq_default_profit = hq_price - hq_cost
        lq_default_profit_lq = lq_price - lq_cost
        lq_default_profit_hq = lq_price - hq_cost
        
        return {
            "reputation_only": (
                f"""
**Production Costs:**
- HQ production cost: ${hq_cost:.1f}
- LQ production cost: ${lq_cost:.1f}

**Default Prices (if you don't specify a price):**
- HQ advertised: ${hq_price:.1f} (default profit: ${hq_default_profit:.1f})
- LQ advertised: ${lq_price:.1f} (default profit: ${lq_default_profit_lq:.1f} for LQ, ${lq_default_profit_hq:.1f} for HQ)

**Your Profit Formula:**
Profit = (Price you set) - (Production cost)

**Examples:**
- If you produce HQ, advertise HQ, and set price ${hq_price + 1:.1f}: Profit = ${hq_price + 1:.1f} - ${hq_cost:.1f} = ${hq_price + 1 - hq_cost:.1f}
- If you produce LQ, advertise HQ, and set price ${hq_price + 2:.1f}: Profit = ${hq_price + 2:.1f} - ${lq_cost:.1f} = ${hq_price + 2 - lq_cost:.1f}
- If you produce LQ, advertise LQ, and set price ${lq_price + 1:.1f}: Profit = ${lq_price + 1:.1f} - ${lq_cost:.1f} = ${lq_price + 1 - lq_cost:.1f}

**Important:** You can set any positive price you want! Higher prices mean higher profits if the product sells, but may reduce the chance of buyers purchasing. Lower prices may attract more buyers but reduce your profit per sale.

Note: Producing LQ and selling as HQ with a high price can earn very high profit BUT damages your reputation!
"""
            ).strip(),
            "reputation_and_warrant": (
                f"""
**Production Costs:**
- HQ production cost: ${hq_cost:.1f}
- LQ production cost: ${lq_cost:.1f}

**Default Prices (if you don't specify a price):**
- HQ advertised: ${hq_price:.1f} (default profit: ${hq_default_profit:.1f})
- LQ advertised: ${lq_price:.1f} (default profit: ${lq_default_profit_lq:.1f} for LQ, ${lq_default_profit_hq:.1f} for HQ)

**Your Profit Formula:**
- If no challenge: Profit = (Price you set) - (Production cost)
- If challenged and warrant offered: Profit = (Price you set) - (Production cost) - ${warrant_escrow:.1f} penalty
- If challenged but no warrant: Profit = (Price you set) - (Production cost) (no penalty)

**Examples:**
- Produce HQ, advertise HQ, set price ${hq_price + 1:.1f}, no warrant, no challenge: Profit = ${hq_price + 1:.1f} - ${hq_cost:.1f} = ${hq_price + 1 - hq_cost:.1f}
- Produce LQ, advertise HQ, set price ${hq_price + 2:.1f}, with warrant, challenged: Profit = ${hq_price + 2:.1f} - ${lq_cost:.1f} - ${warrant_escrow:.1f} = ${hq_price + 2 - lq_cost - warrant_escrow:.1f}
- Produce LQ, advertise HQ, set price ${hq_price + 2:.1f}, no warrant, challenged: Profit = ${hq_price + 2:.1f} - ${lq_cost:.1f} = ${hq_price + 2 - lq_cost:.1f}

**Important:** You can set any positive price you want! Higher prices mean higher profits if the product sells, but may reduce the chance of buyers purchasing.

Note: If you offer a warrant on a misleading claim (LQ advertised as HQ) and get challenged, you lose ${warrant_escrow:.1f} penalty!
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
- You can **set your own price** when listing a product. If you don't specify a price, the system will use default prices (HQ: ${hq_price:.1f}, LQ: ${lq_price:.1f})
- Your profit = (price you set) - (production cost)
- **Your budget decreases by the production cost when you list a product**
- **Your budget increases when you make a sale** (you receive the selling price)
- Buyers only see your **advertised quality** and **price** before a purchase
- Buyers find out the **true product quality** only after their purchase
- **Producing LQ and selling it as HQ** can earn high profit if you set a high price, BUT damages your reputation

## Reputation & Market Dynamics
{{market_rules}}

## ACTIONS RULES
{{actions}}

## Market Structure
- **{{simulation_rounds}} rounds total**, each round you must decide what to produce and advertise
- You can **exit and re-enter the market** to reset your reputation:
  - Exit available after round {{exit_round}}
  - Re-entry available at round {{reentry_round}}
  - Re-entering resets your reputation to zero (fresh start)
- Strategic exits can help you escape a damaged reputation

# PRICING & PROFIT CALCULATION
{{payoff_matrix}}

**Remember:** The payoff matrix shows reference values. You can set your own price when listing a product to maximize your profit strategy!

# TASK (CRITICAL INSTRUCTION)
You must decide and execute EXACTLY ONE action for this round based on your personality, current situation, and the game rules.

**Instructions:**
1. **Assess your situation**: Analyze your current reputation and past performance from the summary
2. **Consider your strategy**: Should you build trust or maximize short-term profit? Should you exit and rebrand?
3. **Formulate a plan**: Based on your PERSONALITY, decide your plan for this round
4. **Execute the action**: You MUST call one of the available functions

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
        warrant_escrow = params['warrant_escrow']
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
   - Your Reputation Score is the average of all ratings you receive
   - A higher reputation may attract more buyers
2. There is NO warranty system in this market
3. You cannot offer warranties for your products
        """,
            "reputation_and_warrant": f"""
## Reputation & Truth Warrant System

1. **Reputation System**: Buyers can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
   - Your Reputation Score is the average of all ratings you receive

2. **Truth Warrant System**:
   - You can offer a "Truth Warrant" for your products by setting `has_warrant=True`
   - This signals to buyers that you're confident in your advertised quality
   - **If you warrant and advertise honestly**: You keep all your profits (${hq_profit:.1f} for HQ→HQ or ${lq_profit:.1f} for LQ→LQ)
   - **If you warrant and advertise misleadingly** (e.g., advertise HQ, produce LQ):
     - A buyer can challenge your warrant for ${challenge_cost:.1f}
     - If challenged, you LOSE ${warrant_escrow:.1f} points from your profit (heavy penalty: -${warrant_escrow:.1f} total)
     - This overrides any sales income from that transaction
   - Your warrant is only at risk if you are challenged for false advertising
        """,
        }
    
    # Keep MARKET_RULES as class property for backward compatibility
    MARKET_RULES = ClassProperty(lambda cls: cls.get_market_rules())

    # Seller waiting/observation prompt (shown during buyer phase)
    WAITING_PROMPT = TextPrompt(
        """
# The buyers are making their purchase decisions. 

While you wait, here's a reminder of the game mechanics:

## Production
• High quality products cost more to produce than low quality products
• High quality product sales earn more profit than low quality product sales
• **Producing low quality and selling it as high quality earns the most profit BUT hurts your reputation**

## Advertising & Reputation
• Buyers only see the **advertised quality** (not the true quality) before they confirm a purchase
• You may advertise a different product quality than the true product quality
• Buyers find out the true product quality only after their purchase
• Your reputation gets automatically updated based on buyer ratings (-2 to +2 scale)

## Warranties & Challenges (if available)
• You may offer a Truth Warrant for your product (has_warrant=True)
• This signals to buyers that your advertised quality is truthful
• **Warranted products only**: Buyers can challenge if they feel cheated by misleading quality
• If your warranted claim was misleading and challenged: you lose 4 points penalty
• If your warranted claim was honest: you keep all profits
• Your warrant is only at risk if challenged

## Game Structure
{simulation_rounds} rounds total. You can exit (after round {exit_round}) and re-enter (at round {reentry_round}) the market to reset reputation.
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
        warrant_escrow = params['warrant_escrow']
        
        return {
            "reputation_only": (
                "Available Actions:\n"
                "1. `purchase_product_id(product_id: int)`: Purchase a product by its product_id\n"
                "2. `rate_transaction(transaction_id: int, rating: int)`: Rate a transaction after purchase\n"
                "   - rating scale: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)\n"
            ),
            "reputation_and_warrant": (
                "Available Actions:\n"
                "1. `purchase_product_id(product_id: int)`: Purchase a product by its product_id\n"
                "2. `rate_transaction(transaction_id: int, rating: int)`: Rate a transaction after purchase\n"
                "   - rating scale: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)\n"
                f"3. `challenge_warrant(product_id: int)`: Challenge a warranted product after purchase (costs ${challenge_cost:.1f})\n"
                "   - Only use if you received LQ when HQ was advertised with a warrant\n"
                f"   - Successful challenge earns you ${warrant_escrow:.1f} points!\n"
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
        warrant_escrow = params['warrant_escrow']
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
- You never get cheated when buying LQ (worst case: you get what you paid for)
"""
            ).strip(),
            "reputation_and_warrant": (
                f"""
**Product Utility Values:**
- HQ (High Quality) product utility: ${hq_utility:.1f}
- LQ (Low Quality) product utility: ${lq_utility:.1f}

**Challenge Cost:** ${challenge_cost:.1f}
**Warrant Escrow:** ${warrant_escrow:.1f} (rewarded to buyer if challenge succeeds)

**Your Utility Formula:**
- **If no challenge:** Utility = (Product Quality Utility) - (Purchase Price)
- **If challenge succeeds** (LQ advertised as HQ with warrant): 
  Utility = (Product Quality Utility) - (Purchase Price) + (Warrant Escrow) + (Challenge Cost Refund) - (Challenge Cost)
  = (Product Quality Utility) - (Purchase Price) + ${warrant_escrow:.1f} + ${challenge_cost:.1f} - ${challenge_cost:.1f}
  = (Product Quality Utility) - (Purchase Price) + ${warrant_escrow:.1f}
- **If challenge fails** (HQ advertised as HQ with warrant): 
  Utility = (Product Quality Utility) - (Purchase Price) - (Challenge Cost)
  = (Product Quality Utility) - (Purchase Price) - ${challenge_cost:.1f}

**Examples:**
- Buy HQ advertised as HQ at price ${hq_price:.1f}, no warrant, no challenge: Utility = ${hq_utility:.1f} - ${hq_price:.1f} = ${hq_utility - hq_price:.1f}
- Buy LQ advertised as HQ at price ${hq_price:.1f}, with warrant, challenge succeeds: 
  Utility = ${lq_utility:.1f} - ${hq_price:.1f} + ${warrant_escrow:.1f} = ${lq_utility - hq_price + warrant_escrow:.1f}
- Buy HQ advertised as HQ at price ${hq_price:.1f}, with warrant, challenge fails: 
  Utility = ${hq_utility:.1f} - ${hq_price:.1f} - ${challenge_cost:.1f} = ${hq_utility - hq_price - challenge_cost:.1f}
- Buy LQ advertised as LQ at price ${lq_price:.1f}, with warrant, challenge: 
  Utility = ${lq_utility:.1f} - ${lq_price:.1f} - ${challenge_cost:.1f} = ${lq_utility - lq_price - challenge_cost:.1f} (challenge fails because product matches advertisement)

**Important:** 
- The price is set by the seller (they can set any price they want)
- You can only challenge products with a **warrant** (has_warrant = True)
- You only see the **advertised quality**, **price**, and **warrant status** before purchasing
- You discover the **true quality** only after purchase
- Successful challenges (catching LQ advertised as HQ) earn you ${warrant_escrow:.1f} net reward (${warrant_escrow:.1f} warrant escrow + ${challenge_cost:.1f} challenge cost refund - ${challenge_cost:.1f} challenge cost = ${warrant_escrow:.1f})
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
- **You never get cheated by buying LQ** - worst case: you get what you paid for
- **You CAN get cheated by buying HQ** - if you pay for HQ but receive LQ, your utility = ${lq_utility:.1f} - price (could be negative!)
- Sellers can exit and re-enter to reset their reputation

## Reputation & Warranties
{{market_rules}}

## Market Structure
- **{{simulation_rounds}} rounds total**, each round you should make one strategic purchase
- Sellers may exit and re-enter, resetting their reputation
- Use seller reputation and warranty signals to make informed decisions

# PRICING & UTILITY CALCULATION
{{payoff_matrix}}

**Remember:** The payoff matrix shows the calculation formula. The actual utility depends on the price set by sellers, which can vary!

# TASK: YOUR DECISION WORKFLOW FOR THIS ROUND
Based on all the information above, decide which product you should purchase to maximize your cumulative utility. (You should only purchase once per round!)

**Consider:**
1. Product advertised quality and price
2. Seller reputation (can they be trusted?)
3. Whether the product has a warranty (seller has something at risk)
4. Your potential returns
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
        warrant_escrow = params['warrant_escrow']
        
        return {
            "reputation_only": """
## Reputation System Only
1. You can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
2. Your ratings affect the seller's reputation score (average of all ratings)
3. Use reputation scores to guide your purchasing decisions
4. There is NO warranty/challenge system in this market
5. You cannot challenge purchases after buying
        """,
            "reputation_and_warrant": f"""
## Reputation & Truth Warrant System

1. **Reputation System**: You can rate each transaction on a scale from -2 to +2:
   - +2 = very good, +1 = good, 0 = neutral, -1 = bad, -2 = very bad
   - Your ratings affect seller reputation scores (average of all ratings)

2. **Truth Warrants & Challenges**:
   - If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim
   - This signals the seller is confident their advertised quality is truthful
   - **To challenge a warrant**: It costs you ${challenge_cost:.1f}
   - **If you win the challenge** (advertised HQ but received LQ): You earn ${warrant_escrow:.1f} points total (great reward!)
   - **If the warrant was honest**: You lose your ${challenge_cost:.1f} challenge fee
   - Only challenge warranted products where you received lower quality than advertised!
        """,
        }
    
    # Keep MARKET_RULES as class property for backward compatibility
    MARKET_RULES = ClassProperty(lambda cls: cls.get_market_rules())

    # Buyer waiting/observation prompt (shown during seller phase)
    WAITING_PROMPT = TextPrompt(
        """
# The sellers are making production decisions.

While you wait, here's a reminder of the game mechanics:

## Buying Strategy
• Buy products based on advertised claims of high or low quality from different sellers
• **Advertisements may be misleading** - trust is important!
• High quality products give you more points than low quality but cost more
• **You never get cheated buying low quality** - you always get what's advertised
• **You CAN get cheated buying high quality** - might receive low quality instead
• Sellers can exit and re-enter to reset their reputation

## Warranted Products (if available)
• If a product has a **"Truth Warrant"** (has_warrant=True), the seller has staked their claim
• This signals confidence in their advertised quality

## Challenging (if available)
• It costs you **$1** to challenge any warranted claim
• If a warranted product promised higher quality than you received, you will **win the challenge and earn 4 points**
• Only challenge warranted products where you suspect you were cheated!

## Rating System
• After purchase, rate transactions on a -2 to +2 scale:
  - +2 (very good), +1 (good), 0 (neutral), -1 (bad), -2 (very bad)
• Your ratings help build or damage seller reputations

## Game Structure
{simulation_rounds} rounds total. Make strategic decisions based on product quality, price, seller reputation, and whether products are warranted.
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
- Your Reputation Score: {reputation_score}
- Your Total Profit So Far: ${total_profit}
- Your Current Budget: ${budget}


Based on the feedback from previous rounds and current market conditions, decide what product to list this round.
Remember: Producing LQ and selling as HQ earns 4 points but damages reputation. Building trust with honest advertising may lead to better long-term outcomes.
**Check your budget before deciding which product to list!**
"""
    )

    # Environment observation for buyers in purchase phase
    BUYER_PURCHASE_ENV = TextPrompt(
        """
# MARKET ENVIRONMENT OBSERVATION

## Current Market Status
- Current Round: {current_round}/{simulation_rounds}
- Your Cumulative Utility: {cumulative_utility}

## Available Products for Purchase
{available_products}


Based on the available products and seller reputations, decide which product to purchase.
Remember: You never get cheated buying LQ. You can get cheated buying HQ. Use reputation and warranty signals wisely!
"""
    )

    # Environment observation for buyers in rating phase
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
- Seller ID: {seller_id}
- Seller Reputation: {seller_reputation}

Based on your purchase experience and the product details, decide how to rate this transaction.
Rate on a scale from -2 to +2: -2 (very bad), -1 (bad), 0 (neutral), +1 (good), +2 (very good)

If you were cheated (advertised HQ, received LQ) on a warranted product, you can challenge for $1 to earn 4 points!
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
def format_seller_history(history_log: list) -> str:
    """Format seller history log as string"""
    if not history_log:
        return "This is the first round. You have no past performance data."

    history_string = "Here is a summary of your performance in previous rounds:\n"
    for entry in history_log:
        history_string += f"- Round {entry['round']}: Listed a True_quality {entry['true_quality']} and advertised_quality {entry['advertised_quality']} product. Sold: {entry['is_sold']} and got {entry['sold_numbers']} products. Round Profit: {entry['profit']:.2f}. New Reputation: {entry['reputation']:.1f}. Total Profit: {entry.get('total_profit', 0):.2f}\n"

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
