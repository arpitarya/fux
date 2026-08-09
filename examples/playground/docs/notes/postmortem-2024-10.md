---
title: "Postmortem: October 2024 double settlement"
tags: [postmortem, payments]
---
# Postmortem: October 2024 double settlement

An operator reran a stuck settlement batch without killing the original;
41 merchants were paid twice.

## What changed

Batches take an advisory lock keyed on batch id — a second instance now
exits loudly. The [settlement runbook](../runbooks/settlement-stuck.md)
gained its "kill before rerun" rule, and clawbacks became a documented
procedure instead of ad-hoc ledger edits.
