---
title: "Runbook: Reconciliation"
tags: [runbook, ledger]
---
# Runbook: reconciliation

The reconciliation job compares processor records, bank statements, and
the [ledger](../adr/0001-postgres-for-ledger.md) every morning.

A `network_timeout` [error](../api/errors.md) leaves payment state
unknown; reconciliation resolves it from the processor's settlement file.
Discrepancies open tickets automatically — a nonzero discrepancy count
two days running pages the money-movement on-call.
