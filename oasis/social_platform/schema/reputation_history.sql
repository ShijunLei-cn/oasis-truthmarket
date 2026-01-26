CREATE TABLE reputation_history (
    run_id INTEGER,
    seed INTEGER,
    round INTEGER,
    seller_id INTEGER,
    public_thumbs_up INTEGER DEFAULT 0,
    public_thumbs_down INTEGER DEFAULT 0,
    FOREIGN KEY(seller_id) REFERENCES user(user_id)
);

CREATE INDEX IF NOT EXISTS idx_reputation_history_seller_round
ON reputation_history (seller_id, round);
