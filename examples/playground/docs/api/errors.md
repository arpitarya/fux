---
title: Error Codes
tags: [api]
---
# Error codes

- `card_declined` — issuer said no; do not retry more than once.
- `insufficient_funds` — retriable after a delay.
- `rate_limited` — you hit the gateway limiter; honor `Retry-After`.
- `idempotency_conflict` — same [idempotency key](idempotency.md),
  different body.
- `network_timeout` — the processor's upstream timed out; the payment
  state is unknown until the reconciliation job runs
  ([runbook](../runbooks/reconciliation.md)).
