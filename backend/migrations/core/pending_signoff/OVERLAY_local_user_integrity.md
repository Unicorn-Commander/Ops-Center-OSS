# Optional overlay — local-user referential integrity (per-deployment, NOT in shared core)

The shared core keys `user_credits` / `user_provider_keys` (and `organization_members`,
`credit_transactions`, `usage_events`) on the **Keycloak subject as varchar** — the
portable, node-independent identity that federation relies on. There is intentionally
NO foreign key to a local `users` table in the shared contract, because in the
cloud/federated model Keycloak is authoritative and `users` is a mirror (empty on
commander); an FK to a mirror lags or blocks legitimate writes.

A deployment where the local `users` table is **authoritative** (e.g. an air-gapped
self-host with no external IdP, or one that wants DB-enforced `ON DELETE CASCADE`
erasure) can add the integrity back as a LOCAL overlay WITHOUT diverging the type or
tripping the drift-check (which pins only the column type, not FK presence):

```sql
-- give users a varchar UNIQUE handle equal to the subject (users.id stays uuid;
-- it has ~10 incoming FKs, so we do NOT retype it):
ALTER TABLE users ADD COLUMN IF NOT EXISTS subject varchar UNIQUE;
UPDATE users SET subject = id::text WHERE subject IS NULL;   -- subject == Keycloak sub

-- re-add the integrity FKs against the portable varchar handle:
ALTER TABLE user_credits
  ADD CONSTRAINT user_credits_user_fk
  FOREIGN KEY (user_id) REFERENCES users(subject) ON DELETE CASCADE;
ALTER TABLE user_provider_keys
  ADD CONSTRAINT user_provider_keys_user_fk
  FOREIGN KEY (user_id) REFERENCES users(subject) ON DELETE CASCADE;
```

This composes with the canonical: `user_id` stays `varchar`, so the drift-check is
happy on every node, and only the deployments that want strict local integrity carry
the overlay. A brand-new air-gapped deploy can skip the retrofit entirely and make
`users.subject` (or a subject-typed PK) the FK target from day one.
