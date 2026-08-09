---
title: Widget Guide
description: How to install, configure and deploy the widget service.
---

# Widget Guide

The widget service converts raw telemetry into daily reports.

## Install

Install the widget service with `pip install widget-service`.
The installer needs Python 3.11 or newer and about 50 MB of disk space.

### Verify

Run `widget --version` to verify the install succeeded.

## Configure

Configuration lives in `widget.toml` next to the binary.

| key  | meaning          |
|------|------------------|
| rate | polls per minute |
| mode | live or replay   |

## Deploy

The deploy uses a blue-green rollout with health checks before cutover.
Rollbacks complete within two minutes when a health check fails.

```bash
widget deploy --env prod
```
