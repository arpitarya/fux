---
title: Webhooks
tags: [api, webhooks]
---
# Webhooks

AcmePay notifies your server about payment events by POSTing a JSON
payload to your configured endpoint.

## Webhook payload

Every payload carries `event_type`, `payment_id`, `occurred_at`, and a
`data` object. The full list of event types is in the
[events reference](events.md).

## Signature verification

Each request carries an `Acme-Signature` header — an HMAC-SHA256 of the
raw body using your endpoint secret. Verify it before trusting the
payload. Rotate secrets from the dashboard; both old and new are valid
for 24 hours during rotation.

## Retry backoff

Failed deliveries are retried on an exponential backoff schedule: 1m, 5m,
30m, 2h, 8h, then hourly to a maximum of 72 hours. The retry budget and
its history are covered in [ADR-0005](../adr/0005-retry-budget-v2.md).
After the budget is exhausted the event moves to the
[dead letter queue](../runbooks/dead-letter-queue.md).

Deliveries are idempotent: replay is safe if you honor the
[idempotency key](idempotency.md) carried in `Acme-Event-Id`.
