---
title: Idempotency
tags: [api]
---
# Idempotency keys

Every mutating API call accepts an `Idempotency-Key` header. Two requests
with the same key and same body return the same result; same key with a
different body returns `409 Conflict`.

Keys are scoped per merchant and expire after 24 hours. The gateway stores
them in Redis; the [ledger](../notes/architecture.md) additionally enforces
uniqueness on `(merchant_id, key)` as the last line of defense.

Use one key per logical operation, not per HTTP attempt — retries of a
timed-out request must reuse the key, which is what makes
[webhook retries](webhooks.md) and [processor retries](../adr/0005-retry-budget-v2.md)
safe.
