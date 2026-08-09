---
title: "ADR-0005: Retry budget (v2)"
status: accepted
tags: [adr, retries]
---
# ADR-0005: Retry budget v2 — exponential backoff with jitter

**Status:** accepted (2024-04) · supersedes [ADR-0002](0002-retry-budget.md)

## Decision

All retries use exponential backoff with full jitter. Webhook deliveries:
1m, 5m, 30m, 2h, 8h, then hourly, capped at 72 hours total. Processor
calls: 100ms base, factor 4, cap 30s, budget 5 attempts.

## Why

The [March 2024 outage](../notes/postmortem-2024-03.md) demonstrated
synchronized retries amplifying a partial failure into a full one. Full
jitter (per the classic AWS analysis) empties retry storms.

## Consequences

Delivery latency after transient failures is bounded and spread; the
[dead letter queue](../runbooks/dead-letter-queue.md) is the terminal
state, not an ever-growing retry loop.
