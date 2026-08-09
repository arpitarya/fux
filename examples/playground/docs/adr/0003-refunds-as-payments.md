---
title: "ADR-0003: Refunds are payments"
status: accepted
tags: [adr, payments]
---
# ADR-0003: Refunds are payments with negative amounts

**Status:** accepted (2024-06)

## Decision

A refund is a payment row with a negative amount and a
`parent_payment_id`, not a separate entity.

## Why

The [ledger](../notes/architecture.md) already knows how to move money;
a second entity would duplicate every state machine. Reporting sums
naturally. Partial refunds are just smaller negatives.

## Consequences

Refund-specific validation lives in the gateway (cannot exceed parent
amount, parent must be `captured` or `settled`). The
[events](../api/events.md) still present refunds as their own event types
so merchants are not confused by negative payments.
