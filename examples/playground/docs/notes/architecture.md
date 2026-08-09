---
title: Architecture Overview
tags: [architecture]
---
# Architecture overview

AcmePay is four services behind one gateway.

## Services

- **gateway** — terminates TLS, authenticates API keys, rate-limits.
- **ledger** — double-entry bookkeeping; the only writer to the money tables.
- **processor** — talks to card networks and bank rails; retries live here.
- **notifier** — delivers [webhooks](../api/webhooks.md) to merchants.

## Data stores

The ledger uses Postgres with strict serializable transactions
([ADR-0001](../adr/0001-postgres-for-ledger.md)). The notifier keeps its
delivery queue in Redis; see the
[dead letter runbook](../runbooks/dead-letter-queue.md) for what happens
when deliveries exhaust their retry budget.

## Design rules

Money movements are idempotent by [idempotency key](../api/idempotency.md).
Every external call has a timeout and a retry budget
([ADR-0005](../adr/0005-retry-budget-v2.md)). Nothing calls the ledger
except through the gateway.
