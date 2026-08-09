---
title: "ADR-0004: HMAC webhook signatures"
status: accepted
tags: [adr, webhooks, security]
---
# ADR-0004: HMAC-SHA256 webhook signatures

**Status:** accepted (2024-08)

## Decision

Webhook payloads are signed with HMAC-SHA256 over the raw body, keyed by a
per-endpoint secret, sent as `Acme-Signature`.

## Why

Asymmetric signatures (considered: Ed25519) are stronger but push key
management onto every merchant; HMAC verification is three lines in any
language. Replay is bounded by the timestamp embedded in the signed body
plus [idempotent delivery](../api/idempotency.md).

## Consequences

Secret rotation needs a dual-validity window (24h — see
[webhooks](../api/webhooks.md)). If a merchant leaks their secret, we
rotate and replay undelivered events.
