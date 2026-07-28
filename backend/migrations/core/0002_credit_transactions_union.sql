-- core parity 0002 — credit_transactions ledger-shape union (Phase B)
-- bigboy records credits_consumed; commander records balance_after. Carry BOTH
-- columns (nullable) on both nodes so either ledger writer/reader works
-- regardless of which node the cherry-picked code lands on. 427 rows on
-- commander, 0 on bigboy — nullable ADD COLUMN is metadata-only / instant.
ALTER TABLE credit_transactions ADD COLUMN IF NOT EXISTS credits_consumed NUMERIC;
ALTER TABLE credit_transactions ADD COLUMN IF NOT EXISTS balance_after NUMERIC;
