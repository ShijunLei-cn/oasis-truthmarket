import os
import sqlite3
from typing import Optional, Tuple

def _connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def ensure_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    # reputation_history schema should already exist via SQL files,
    # but we defensively ensure it here to avoid runtime failures.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reputation_history (
            run_id INTEGER,
            seed INTEGER,
            round INTEGER,
            seller_id INTEGER,
            public_thumbs_up INTEGER DEFAULT 0,
            public_thumbs_down INTEGER DEFAULT 0,
            FOREIGN KEY(seller_id) REFERENCES user(user_id)
        );
        """
    )
    # Simple index for query speed
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reputation_history_seller_round
        ON reputation_history (seller_id, round);
        """
    )
    conn.commit()


def _get_previous_reputation(conn: sqlite3.Connection, seller_id: int) -> Tuple[int, int]:
    """Return (thumbs_up, thumbs_down) from latest history row if exists, else defaults (0, 0)."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT public_thumbs_up, public_thumbs_down
        FROM reputation_history
        WHERE seller_id = ?
        ORDER BY round DESC
        LIMIT 1
        """,
        (seller_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return 0, 0
    return int(row[0] or 0), int(row[1] or 0)


def _get_run_meta() -> Tuple[int, Optional[int]]:
    # In absence of a run manager, default run_id=1 and optional seed from env
    run_id = int(os.getenv("RUN_ID", "1"))
    seed_env = os.getenv("SEED")
    seed = int(seed_env) if seed_env is not None and seed_env.isdigit() else None
    return run_id, seed


def compute_and_update_reputation(conn: sqlite3.Connection, round_number: int, ratings_up_to_round: Optional[int] = None) -> None:
    """
    Calculate each seller's public reputation using thumbs-up/thumbs-down counting system.
    Rating mapping:
    - rating +1 → thumbs_up +1
    - rating +2 → thumbs_up +2
    - rating -1 → thumbs_down +1
    - rating -2 → thumbs_down +2
    
    - round_number: round that current snapshot belongs to (used for writing reputation_history.round)
    - ratings_up_to_round: maximum round considered for rating aggregation (used to implement lag display).
      If None, equivalent to using round_number.
    """
    ensure_tables(conn)
    cursor = conn.cursor()

    effective_max_round = round_number if ratings_up_to_round is None else max(0, int(ratings_up_to_round))

    # Get all sellers
    cursor.execute("SELECT user_id FROM user WHERE role = 'seller'")
    seller_ids = [row[0] for row in cursor.fetchall()]

    run_id, seed = _get_run_meta()

    for seller_id in seller_ids:
        # Get all ratings for this seller up to the effective max round
        cursor.execute(
            """
            SELECT t.rating
            FROM transactions t
            WHERE t.seller_id = ? AND t.rating IS NOT NULL 
            AND t.round_number <= ?
            """,
            (seller_id, effective_max_round),
        )
        
        ratings = [row[0] for row in cursor.fetchall()]
        
        # Calculate thumbs up and down counts
        thumbs_up = 0
        thumbs_down = 0
        for rating in ratings:
            if rating > 0:
                thumbs_up += rating  # +1 → +1, +2 → +2
            else:
                thumbs_down += abs(rating)  # -1 → +1, -2 → +2
                
        # Persist snapshot
        cursor.execute(
            """
            INSERT INTO reputation_history (
                run_id, seed, round, seller_id, public_thumbs_up, public_thumbs_down
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, seed, round_number, seller_id, int(thumbs_up), int(thumbs_down)),
        )

        # Update user table for live access in prompts
        cursor.execute(
            "UPDATE user SET thumbs_up_count = ?, thumbs_down_count = ? WHERE user_id = ?",
            (int(thumbs_up), int(thumbs_down), seller_id),
        )

    conn.commit()


def backfill_reputation_for_all_rounds(max_round: int, db_path: Optional[str] = None) -> None:
    """Utility to recompute and snapshot reputation for rounds 1..max_round."""
    with _connect(db_path) as conn:
        for r in range(1, max_round + 1):
            compute_and_update_reputation(conn, r)
