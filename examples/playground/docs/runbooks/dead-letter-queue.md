---
title: "Runbook: Dead letter queue"
tags: [runbook, webhooks]
---
# Runbook: dead letter queue

When a [webhook](../api/webhooks.md) exhausts its
[retry budget](../adr/0005-retry-budget-v2.md), the event lands in the DLQ.

## Symptoms

`acme_dlq_depth` gauge rising; merchant complains about missing events.

## Procedure

1. Check the merchant's endpoint health — most DLQ growth is one dead
   endpoint.
2. `acmectl dlq inspect <merchant>` — sample the stuck payloads.
3. If the endpoint recovered: `acmectl dlq replay <merchant>` (replays are
   safe — [idempotent delivery](../api/idempotency.md)).
4. If it's dead > 7 days, email the merchant and pause the endpoint;
   unpaused endpoints replay automatically.

Never delete DLQ entries — settlement reconciliation reads them.
