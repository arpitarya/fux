---
title: "Postmortem: March 2024 retry storm"
tags: [postmortem, retries]
---
# Postmortem: March 2024 retry storm

A 20-minute processor brownout became a 3-hour outage.

## What happened

Fixed-interval retries ([ADR-0002](../adr/0002-retry-budget.md), since
superseded) synchronized thousands of callers into waves that kept the
recovering processor saturated.

## What changed

Exponential backoff with full jitter everywhere —
[ADR-0005](../adr/0005-retry-budget-v2.md). Retry storms are now visible
on the `retry_concurrency` dashboard before they matter.
