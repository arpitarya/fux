---
title: "Runbook: Settlement stuck"
tags: [runbook, payments]
---
# Runbook: settlement batch stuck

The nightly settlement moves captured funds to merchant banks. It jams for
two reasons: a bank file rejected, or the
[ledger](../notes/architecture.md) batch transaction deadlocked.

## Procedure

1. `acmectl settlement status` — identifies the stuck batch and its phase.
2. Bank-file rejection: the file is regenerated after fixing the flagged
   rows; rejected rows go to manual review, the rest re-submit.
3. Ledger deadlock: the batch is idempotent — kill and rerun. Never rerun
   without killing; two live batches double-post (it happened once — see
   the [October postmortem](../notes/postmortem-2024-10.md)).
4. If any merchant was paid twice, open the clawback procedure — do NOT
   attempt manual ledger edits.
