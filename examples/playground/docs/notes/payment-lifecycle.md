---
title: Payment Lifecycle
tags: [architecture, payments]
---
# Payment lifecycle

A payment moves through five states: `created` → `authorized` →
`captured` → `settled`, with `failed` reachable from any of the first
three.

Authorization holds funds on the customer's card. Capture books the
charge into the [ledger](architecture.md). Settlement is the nightly batch
that moves money to the merchant's bank account — see the
[settlement runbook](../runbooks/settlement-stuck.md) when it jams.

State transitions emit events; merchants observe them through
[webhooks](../api/webhooks.md). A payment that fails after authorization
must be voided within seven days or the hold expires on its own.

Refunds are modeled as separate payments with a negative amount, linked by
`parent_payment_id` — the reasoning is in
[ADR-0003](../adr/0003-refunds-as-payments.md).
