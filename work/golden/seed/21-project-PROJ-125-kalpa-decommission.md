---
title: "PROJ-125: Kalpa decommission and audit export"
doc_id: PROJ-125
owner: IT Service Desk
department: IT
status: closed
opened_on: 2025-10-31
closed_on: 2026-05-12
effective_date: 2026-05-12
---

# PROJ-125: Kalpa decommission and audit export

**PROJ-125** ended Quillfern's use of Kalpa Fleet Systems as a running platform
and preserved its history as files. It is closed. PROJ-125 is the last of the
three projects in this series; the other two are
[PROJ-123](19-project-PROJ-123-dockwise-rollout.md) and
[PROJ-124](20-project-PROJ-124-red-sleeve-and-passive-shippers.md), and neither
of them touched a telematics platform.

## Scope

The vendor change itself was not this project. It was decided in the cutover
thread of 2025 and recorded afterwards in
[Telematics Vendor Decision 2026](11-decision-telematics-vendor-2026.md), which
retired [the 2023 decision](05-decision-telematics-vendor-2023.md). PROJ-125 only
did the shutdown work that decision left behind.

## What was done

- Kalpa platform access ended on **30 April 2026**, the date the 2026 decision
  record set for retiring the export script.
- Trip data from 2014 to 2025 was exported to cold storage: 48,900 trips, all
  carrying the KLP prefix, 2.1 TB including the raw probe series. Two copies,
  one on the Pune HQ archive volume and one with the audit vendor.
- The alert routing that Kalpa used was retired with it. What it looked like is
  described in [the Kalpa Alert Routing Guide](archive/a02-kalpa-alert-routing-guide-2021.md),
  which is kept only so auditors can see how alarms were routed before
  Compliance-Red existed.
- The guard cabin tablet at Nagpur was wiped of its login and left in place as a
  read-only audit device. It must not be used to open or acknowledge an alarm.
- The Kalpa sticker on the Nagpur admin wall was removed on 5 May 2026. The
  night team had asked for this twice because new drivers were reading it as
  current.

## What was deliberately not done

The KLP trip number format was not rewritten into TSL form. An audit packet
covering a trip before the pilot still quotes the KLP number it was filed under,
and rewriting it would have broken every customer claim reference.

Paper driver call logs were not retired. Fleet keeps them because network
coverage, not the vendor, was the reason for them in the first place.

## Cost

| line | figure |
|---|---|
| export and cold storage, one time | Rs. 2.85 lakh |
| audit vendor copy, annual | Rs. 0.36 lakh |
| internal effort | 22 person-days, IT Service Desk |

The Kalpa early termination charge is not carried here. It was a commercial
control figure of the vendor decision and is recorded in
[Telematics Vendor Decision 2026](11-decision-telematics-vendor-2026.md), not in
this project's cost.
