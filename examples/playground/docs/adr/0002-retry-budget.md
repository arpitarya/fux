---
title: "ADR-0002: Retry budget (v1)"
status: superseded by 0005
tags: [adr, retries]
---
# ADR-0002: Retry budget — v1

**Status: SUPERSEDED by [ADR-0005](0005-retry-budget-v2.md).**

## Decision (historical)

Every external call retries at most 3 times with fixed 5-second spacing.

## Why it was replaced

Fixed spacing synchronized retries across callers and amplified outages —
the [March incident](../notes/postmortem-2024-03.md) showed the thundering
herd clearly. Kept here because old code comments still reference it.
