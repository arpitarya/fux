---
title: Events Reference
tags: [api, webhooks]
---
# Events reference

Event types emitted over [webhooks](webhooks.md):

- `payment.authorized` — funds held.
- `payment.captured` — charge booked to the ledger.
- `payment.settled` — nightly settlement completed for this payment.
- `payment.failed` — includes a `failure_reason` code.
- `refund.created`, `refund.settled` — see
  [refunds as payments](../adr/0003-refunds-as-payments.md).
- `dispute.opened`, `dispute.resolved` — see the
  [chargeback runbook](../runbooks/chargebacks.md).

Events are delivered at-least-once and may arrive out of order; order by
`occurred_at`, dedupe by `Acme-Event-Id`.
