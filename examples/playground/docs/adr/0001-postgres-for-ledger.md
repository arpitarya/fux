---
title: "ADR-0001: Postgres for the ledger"
status: accepted
tags: [adr, ledger]
---
# ADR-0001: Postgres for the ledger

**Status:** accepted (2024-03)

## Decision

The ledger uses Postgres with `SERIALIZABLE` isolation, not an event store.

## Why

Double-entry bookkeeping is relational at heart: every movement is two
rows that must commit together. Serializable transactions give us that
without hand-rolled locking. The team knows Postgres; the audit story
(point-in-time recovery, WAL archiving) is mature.

## Consequences

Throughput ceiling ~2k movements/s per shard — fine for years. Sharding
by merchant when we get there. Event sourcing revisited only if the
[reconciliation](../runbooks/reconciliation.md) burden proves it.
