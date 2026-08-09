---
title: Merchant Quickstart
tags: [onboarding]
---
# Merchant quickstart

1. Create an API key in the dashboard.
2. Make a test charge with an `Idempotency-Key`
   ([why](../api/idempotency.md)).
3. Register a webhook endpoint and verify the
   [signature](../adr/0004-webhook-signatures.md).
4. Handle `payment.captured` and `payment.failed`
   [events](../api/events.md) — everything else can wait.
5. Go live after passing the test-mode checklist.
