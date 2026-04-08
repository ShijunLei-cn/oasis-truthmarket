# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from string import Template

import os
from oasis.social_agent.agent_action import SocialAction
from oasis.social_platform.database import get_db_path
from config import SimulationConfig


class Environment(ABC):
    @abstractmethod
    def to_text_prompt(self) -> str:
        r"""Convert the environment to text prompt."""
        raise NotImplementedError


class SocialEnvironment(Environment):
    followers_env_template = Template("I have $num_followers followers.")
    follows_env_template = Template("I have $num_follows follows.")

    posts_env_template = Template(
        "After refreshing, you see some posts $posts")

    groups_env_template = Template(
        "And there are many group chat channels $all_groups\n"
        "And You are already in some groups $joined_groups\n"
        "You receive some messages from them $messages\n"
        "You can join the groups you are interested, "
        "leave the groups you already in, send messages to the group "
        "you already in.\n"
        "You must make sure you can only send messages to the group you "
        "are already in")
    env_template = Template(
        "$groups_env\n"
        "$posts_env\npick one you want to perform action that best "
        "reflects your current inclination based on your profile and "
        "posts content. Do not limit your action in just `like` to like posts")
    
    market_env_template = Template(
        "Current Round: $current_round / $simulation_rounds\n"
        "Reputation Score: $reputation_score\n"
        "Cumulative Utility: $cumulative_utility\n\n"
        "Current available products:\n$products")
    
    def __init__(self, action: SocialAction, db_path: str = "", config: SimulationConfig = None):
        self.action = action
        self.db_path = db_path if db_path else get_db_path()
        # === market-sim: add a flag to distinguish modes ===
        self.is_market_sim = False 
        self.config = config if config else SimulationConfig()
        self.communication_channel_type = "Fake"  # Fake or Real

    def get_product_listings_for_env(self, market_type: str = None) -> str:
        """Query all products on sale from database and format as string.
        
        Args:
            market_type: Market type ('reputation_only' or 'reputation_and_warrant').
                        If None, warranty info will be shown by default.
        """
        if not os.path.exists(self.db_path):
            return "No products are currently on sale."
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        listings = "No products are currently on sale."
        try:
            cursor.execute(
                """
                SELECT p.product_id, p.user_id, p.advertised_quality, p.price, p.has_warrant,
                    COALESCE(u.brand_name, 'Unknown') AS brand_name,
                    COALESCE(u.thumbs_up_count, 0) AS thumbs_up_count,
                    COALESCE(u.thumbs_down_count, 0) AS thumbs_down_count
                FROM product p
                LEFT JOIN user u ON u.user_id = p.user_id
                WHERE p.status = 'on_sale'
                """
            )
            products = cursor.fetchall()
            if products:
                listings = f"Available Products ({len(products)} total):\n"
                for p in products:
                    product_id, seller_id, adv_quality, price, has_warrant, brand_name, thumbs_up, thumbs_down = p
                    # Only show warranty info if market_type is not 'reputation_only'
                    if market_type == 'reputation_only':
                        listings += (
                            f"  Product {product_id}: {adv_quality} quality, "
                            f"Price ${price:.2f}, "
                            f"Brand {brand_name} (👍{thumbs_up} 👎{thumbs_down})\n"
                        )
                    else:
                        warrant_str = "Warranted" if has_warrant else "No Warrant"
                        listings += (
                            f"  Product {product_id}: {adv_quality} quality, "
                            f"Price ${price:.2f}, "
                            f"Brand {brand_name} (👍{thumbs_up} 👎{thumbs_down}), "
                            f"{warrant_str}\n"
                        )
        except sqlite3.Error as e:
            print(f"Database query error (get_product_listings_for_env): {e}")
        finally:
            conn.close()
        return listings

    def get_posts_communication_for_env(self) -> str:
        """Query all posts from database and format as string with structured information.
        
        Args:
            current_user_id: The user_id of the current agent viewing the environment.
                           Used for filtering posts in Fake communication channel mode.
        """
        if not os.path.exists(self.db_path):
            return "No posts are currently available."
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        posts_env = "No posts are currently available."
        
        try:
            # Query all posts regardless of status, ordered by creation time (newest first)
            # In market simulation, posts don't have 'on_sale' status, so we query all posts
            cursor.execute(
                            """
                            SELECT p.post_id, p.content, p.user_id, p.created_at, u.role
                            FROM post p
                            LEFT JOIN user u ON u.user_id = p.user_id
                            WHERE p.original_post_id IS NULL
                            ORDER BY p.created_at DESC, p.post_id DESC
                            LIMIT 50
                            """
            )
            posts = cursor.fetchall()
            if posts:
                posts_env = "Here is the list of posts currently available:\n\n"
                current_agent_role = None
                current_agent_id = self.action.agent_id
                
                # 获取当前 agent 的 role
                if current_agent_id is not None:
                    cursor.execute(
                        "SELECT role FROM user WHERE agent_id = ?",
                        (current_agent_id,)
                    )
                    role_result = cursor.fetchone()
                    if role_result:
                        current_agent_role = role_result[0]
                
                for p in posts:
                    post_id, content, user_id, created_at, author_role = p
                    
                    # Fake 模式下的过滤逻辑
                    if self.communication_channel_type == "Fake":
                        continue

                    if current_agent_role != author_role:
                        continue

                    posts_env += f"- Post ID: {post_id}, Author ID: {user_id}\n"
                    posts_env += f"  Content: {content}\n"
                    posts_env += "\n"

        except sqlite3.Error as e:
            print(f"Database query error (get_posts_communication_for_env): {e}")
        finally:
            conn.close()
        return posts_env
    

    async def get_posts_env(self) -> str:
        posts = await self.action.refresh()
        # TODO: Replace posts json format string to other formats
        if posts["success"]:
            posts_env = json.dumps(posts["posts"], indent=4)
            posts_env = self.posts_env_template.substitute(posts=posts_env)
        else:
            posts_env = "After refreshing, there are no existing posts."
        return posts_env

    async def get_followers_env(self) -> str:
        # TODO: Implement followers env
        agent_id = self.action.agent_id
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT num_followers FROM user WHERE agent_id = ?",
                           (agent_id, ))
            result = cursor.fetchone()
            num_followers = result[0] if result else 0
            conn.close()
        except Exception:
            num_followers = 0
        return self.followers_env_template.substitute(
            {"num_followers": num_followers})

    async def get_follows_env(self) -> str:
        # TODO: Implement follows env
        agent_id = self.action.agent_id
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT num_followings FROM user WHERE agent_id = ?",
                (agent_id, ))
            result = cursor.fetchone()
            num_followings = result[0] if result else 0
            conn.close()
        except Exception:
            num_followings = 0
        return self.follows_env_template.substitute(
            {"num_follows": num_followings})

    async def get_group_env(self) -> str:
        groups = await self.action.listen_from_group()
        if groups["success"]:
            all_groups = json.dumps(groups["all_groups"])
            joined_groups = json.dumps(groups["joined_groups"])
            messages = json.dumps(groups["messages"])
            groups_env = self.groups_env_template.substitute(
                all_groups=all_groups,
                joined_groups=joined_groups,
                messages=messages,
            )
        else:
            groups_env = "No groups."
        return groups_env

    async def get_market_environment(self, agent=None, current_round=1, market_phase="general") -> str:
        """Get environment information for market simulation, providing different observation content based on different market phases."""
        from prompt import MarketEnv_prompt
        
        if not agent:
            # If no agent information, return basic environment information
            return f"Current Round: {current_round}/{self.config.SIMULATION_ROUNDS}\nNo agent information available."
        
        role = agent.user_info.profile.get("role")
        
        if market_phase == "communication":
            # Use direct database query instead of refresh() to get all posts
            # refresh() relies on rec table which may not be properly updated in market simulation
            posts_env = self.get_posts_communication_for_env()
            return posts_env
        
        elif market_phase == "listing" and role == "seller":
            # Seller in listing phase: observe previous phase purchase feedback and current market status
            previous_feedback = self._get_previous_feedback(agent)
            total_profit = getattr(agent, 'total_profit', 0)
            # Get budget from agent or database
            budget = getattr(agent, 'current_budget', None)
            if budget is None:
                # Try to get from database if not in agent
                db_path = get_db_path()
                if db_path and os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT budget FROM user WHERE agent_id = ?", (agent.social_agent_id,))
                        result = cursor.fetchone()
                        default_budget = SimulationConfig.MARKET_PARAMS.get('seller_budget', 60.0)
                        budget = result[0] if result and result[0] is not None else default_budget
                        conn.close()
                    except Exception:
                        budget = SimulationConfig.MARKET_PARAMS.get('seller_budget', 60.0)
                else:
                    budget = SimulationConfig.MARKET_PARAMS.get('seller_budget', 60.0)
            
            # Get thumbs-up and thumbs-down counts from agent
            thumbs_up_count = getattr(agent, 'thumbs_up_count', 0)
            thumbs_down_count = getattr(agent, 'thumbs_down_count', 0)
            
            return MarketEnv_prompt.SELLER_LISTING_ENV.format(
                previous_feedback=previous_feedback,
                current_round=current_round,
                simulation_rounds=self.config.SIMULATION_ROUNDS,
                thumbs_up_count=thumbs_up_count,
                thumbs_down_count=thumbs_down_count,
                total_profit=total_profit,
                budget=budget,
            )
            
        elif market_phase == "purchase" and role == "buyer":
            # Buyer in purchase phase: observe currently purchasable products
            # Get market_type from agent profile
            market_type = agent.user_info.profile.get("market_type", "reputation_and_warrant")
            available_products = self.get_product_listings_for_env(market_type=market_type)
            
            # Use dynamic prompt based on market_type
            purchase_env = MarketEnv_prompt.get_buyer_purchase_env(market_type)
            return purchase_env.format(
                current_round=current_round,
                simulation_rounds=self.config.SIMULATION_ROUNDS,
                cumulative_utility=agent.cumulative_utility,
                available_products=available_products,
            )
            
        elif market_phase == "rating" and role == "buyer":
            # Buyer in rating phase: observe specific product information after purchase
            # Get all purchase transactions (for multiple purchases)
            all_transactions = getattr(agent, 'all_purchase_transactions', None)
            if all_transactions is None:
                # Fallback to last_purchase_info for backward compatibility
                purchase_info = getattr(agent, 'last_purchase_info', {})
                all_transactions = [purchase_info] if purchase_info.get('transaction_id') else []
            
            # If no transactions, return a simple message (should not happen if BuyerRatingPhase is correct)
            if not all_transactions or not any(t.get('transaction_id') for t in all_transactions):
                return (
                    f"# MARKET ENVIRONMENT OBSERVATION\n\n"
                    f"## Your Status\n"
                    f"- Round: {current_round}/{self.config.SIMULATION_ROUNDS}\n\n"
                    f"You did not purchase any products in this round, so there are no transactions to rate or challenge."
                )
            
            # Filter out transactions without valid transaction_id
            valid_transactions = [t for t in all_transactions if t.get('transaction_id')]
            if not valid_transactions:
                return (
                    f"# MARKET ENVIRONMENT OBSERVATION\n\n"
                    f"## Your Status\n"
                    f"- Round: {current_round}/{self.config.SIMULATION_ROUNDS}\n\n"
                    f"You did not purchase any products in this round, so there are no transactions to rate or challenge."
                )
            
            # Get market_type from agent profile
            market_type = agent.user_info.profile.get("market_type", "reputation_and_warrant")
            
            # Collect all unique seller_ids from transactions
            unique_seller_ids = list(set(t.get('seller_id') for t in valid_transactions if t.get('seller_id')))
            
            # Fetch brand_name and reputation for all sellers in one query
            seller_info = {}
            if unique_seller_ids:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    placeholders = ','.join('?' * len(unique_seller_ids))
                    cursor.execute(f"SELECT user_id, brand_name, thumbs_up_count, thumbs_down_count FROM user WHERE user_id IN ({placeholders})", unique_seller_ids)
                    for row in cursor.fetchall():
                        seller_info[row[0]] = {
                            'brand_name': row[1] if row[1] else 'Unknown',
                            'thumbs_up': row[2] if row[2] else 0,
                            'thumbs_down': row[3] if row[3] else 0
                        }
                    conn.close()
                    print(f"DEBUG: Fetched seller_info for {len(seller_info)} sellers: {seller_info}")
                except Exception as e:
                    print(f"Error fetching seller info: {e}")
            else:
                print(f"DEBUG: No valid seller_ids found in transactions. Unique seller_ids: {unique_seller_ids}")
            
            # Format transactions information for display with brand_name
            transactions_text = "\n".join([
                f"  - Transaction ID: {t.get('transaction_id', 'N/A')}, "
                f"Product ID: {t.get('product_id', 'N/A')}, "
                f"Brand: {seller_info.get(t.get('seller_id'), {}).get('brand_name', 'Unknown')}, "
                f"Advertised: {t.get('advertised_quality', 'N/A')}, "
                f"True Quality: {t.get('true_quality', 'N/A')}, "
                f"Price: ${t.get('purchase_price', 0):.2f}, "
                f"Utility: {t.get('buyer_utility', 0):.2f}"
                + (f", Has Warrant: {t.get('has_warrant', False)}" if market_type != 'reputation_only' else "")
                for t in valid_transactions
            ])
            
            # Use dynamic prompt based on market_type
            rating_env = MarketEnv_prompt.get_buyer_rating_env(market_type)
            rating_prompt = rating_env.format(
                transactions_text=transactions_text
            )
            return rating_prompt
        
        elif market_phase == "challenge" and role == "buyer":
            # Buyer in challenge phase: observe specific product information after purchase (only for warranted products)
            # Get all purchase transactions (for multiple purchases)
            all_transactions = getattr(agent, 'all_purchase_transactions', None)
            if all_transactions is None:
                # Fallback to last_purchase_info for backward compatibility
                purchase_info = getattr(agent, 'last_purchase_info', {})
                all_transactions = [purchase_info] if purchase_info.get('transaction_id') else []
            
            # If no transactions, return a simple message
            if not all_transactions or not any(t.get("transaction_id") for t in all_transactions):
                return (
                    f"# MARKET ENVIRONMENT OBSERVATION\n\n"
                    f"## Your Status\n"
                    f"- Round: {current_round}/{self.config.SIMULATION_ROUNDS}\n\n"
                    f"You did not purchase any products in this round, so there are no transactions to challenge."
                )
            
            # Filter out transactions without valid transaction_id and only include warranted products
            valid_transactions = [
                t for t in all_transactions 
                if t.get('transaction_id') and t.get('has_warrant', False)
            ]
            if not valid_transactions:
                return (
                    f"# MARKET ENVIRONMENT OBSERVATION\n\n"
                    f"## Your Status\n"
                    f"- Round: {current_round}/{self.config.SIMULATION_ROUNDS}\n\n"
                    f"You have no warranted products to challenge in this round."
                )
            
            # Get market_type from agent profile
            market_type = agent.user_info.profile.get("market_type", "reputation_and_warrant")
            
            # Collect all unique seller_ids from transactions
            unique_seller_ids = list(set(t.get('seller_id') for t in valid_transactions if t.get('seller_id')))
            
            # Fetch brand_name and reputation for all sellers in one query
            seller_info = {}
            if unique_seller_ids:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    placeholders = ','.join('?' * len(unique_seller_ids))
                    cursor.execute(f"SELECT user_id, brand_name, thumbs_up_count, thumbs_down_count FROM user WHERE user_id IN ({placeholders})", unique_seller_ids)
                    for row in cursor.fetchall():
                        seller_info[row[0]] = {
                            'brand_name': row[1] if row[1] else 'Unknown',
                            'thumbs_up': row[2] if row[2] else 0,
                            'thumbs_down': row[3] if row[3] else 0
                        }
                    conn.close()
                except Exception as e:
                    print(f"Error fetching seller info: {e}")
            
            # Format transactions information for display with brand_name (only warranted products)
            transactions_text = "\n".join([
                f"  - Transaction ID: {t.get('transaction_id', 'N/A')}, "
                f"Product ID: {t.get('product_id', 'N/A')}, "
                f"Brand: {seller_info.get(t.get('seller_id'), {}).get('brand_name', 'Unknown')}, "
                f"Advertised: {t.get('advertised_quality', 'N/A')}, "
                f"True Quality: {t.get('true_quality', 'N/A')}, "
                f"Price: ${t.get('purchase_price', 0):.2f}, "
                f"Utility: {t.get('buyer_utility', 0):.2f}, "
                f"Has Warrant: {t.get('has_warrant', False)}"
                for t in valid_transactions
            ])
            
            # Use challenge-specific prompt
            challenge_prompt = (
                f"# MARKET ENVIRONMENT OBSERVATION\n\n"
                f"## Your Warranted Purchases in This Round:\n"
                f"{transactions_text}\n\n"
                f"Based on your purchase experiences and the product details, decide whether to challenge any warranted products.\n"
                f"**Instructions:**\n"
                f"- You can challenge warranted products where you received lower quality than advertised using `challenge_warrants()`\n"
                f"- Challenging costs $1 but rewards you if the seller was fraudulent (e.g., $8 for HQ claims)\n"
                f"- Only challenge if you received lower quality than advertised!\n"
            )
            return challenge_prompt
            
        else:
            # Other cases return basic environment information
            return f"Current Round: {current_round}/{self.config.SIMULATION_ROUNDS}\nRole: {role}, Phase: {market_phase}\nNo specific environment template available."
    
    def _get_previous_feedback(self, agent) -> str:
        """Get previous phase historical performance feedback information"""
        # Get historical feedback information from agent's history_summary attribute
        # This attribute is updated through sellers_history in run_single_simulation.py
        if hasattr(agent, 'history_summary') and agent.history_summary:
            # Check if it's a hidden message during initial window period
            if agent.history_summary == "History hidden in initial window.":
                return "This is within the initial window period. Historical performance data is not available yet."
            return agent.history_summary
        else:
            return "No previous feedback available. This is your first round."
    
    def _get_seller_reputation_info(self) -> str:
        """Get seller reputation information"""
        # Should get all sellers' reputation information from database or platform here
        # Return simulated data for now
        return "Seller reputation information can't be view."

    async def to_text_prompt(
        self,
        include_posts: bool = True,
        include_followers: bool = True,
        include_follows: bool = True,
        agent=None,
        current_round=1,
        market_phase="general",
    ) -> str:

        if self.is_market_sim:
            return await self.get_market_environment(agent, current_round, market_phase)
        else:
            followers_env = (await self.get_followers_env()
                            if include_follows else "No followers.")
            follows_env = (await self.get_follows_env()
                        if include_followers else "No follows.")
            posts_env = await self.get_posts_env() if include_posts else ""
        
            return self.env_template.substitute(
                followers_env=followers_env,
                follows_env=follows_env,
                posts_env=posts_env,
                groups_env=await self.get_group_env(),
            )
