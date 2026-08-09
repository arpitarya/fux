---
title: "Runbook: Chargebacks"
tags: [runbook, disputes]
---
# Runbook: chargebacks

A `dispute.opened` [event](../api/events.md) means the card network pulled
the money back pending evidence.

The ledger books a provisional debit against the merchant immediately
([refunds-as-payments](../adr/0003-refunds-as-payments.md) machinery, with
`kind=dispute`). Evidence is due in 20 days; the deadline lives on the
dispute row and the notifier reminds at 15 and 18 days. Won disputes
re-credit automatically on `dispute.resolved`.
