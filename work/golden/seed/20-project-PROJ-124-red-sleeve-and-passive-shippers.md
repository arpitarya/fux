---
title: "PROJ-124: Red sleeve replenishment and passive shipper pilot"
doc_id: PROJ-124
owner: Revathi Iyer
department: QA and Compliance
status: in_progress
opened_on: 2026-06-24
effective_date: 2026-06-24
---

# PROJ-124: Red sleeve replenishment and passive shipper pilot

**PROJ-124** is open. It has two halves that share a sponsor and a budget line
but nothing else: getting physical red sleeve packets back into every DC, and
piloting validated passive shippers at Nagpur. It is not
[PROJ-123](19-project-PROJ-123-dockwise-rollout.md), which was a dock calendar
project and is closed.

## Half one: red sleeves

The red sleeve is the packet clipped to an excursion file or a pharma truck
file. What it must contain is fixed by clause 4.2 of
[the Temperature Excursion Response SOP](01-sop-temperature-excursion.md); this
project buys the packets and does not change the contents list.

The trigger was operational, not a policy gap. Stores had been promising vendor
plastic sleeves "next week" since April 2026, and the Nagpur night team recorded
a second short packet on 19 June 2026, writing RED SLEEVE MISSING on a printout
for a BharatVac return — see
[the night shift handover log](04-night-shift-handover-log.txt). The same log
records hired trucks arriving without sleeves in October 2025 and staff making
red tags out of old labels.

Ordered: 60 packets at Rs. 1,180 each, split 30 Nagpur, 15 Guwahati,
15 Coimbatore. Each packet is made up with a spare calibrated logger before it
leaves QA, because a sleeve without a logger is the failure this project is
meant to end.

## Half two: passive shippers

Pharma pallets may not be staged on an open dock beyond a short limit unless a
validated passive shipper is used; the limit and the exception are clause 8.2 of
[the SOP](01-sop-temperature-excursion.md).

Quillfern has been refusing bookings it could have taken, including chilled
pharma on [RF-119](17-reefer-RF-119-asset-file.md), which has no shipper cradle
and therefore cannot take pharma critical stock without one. The pilot puts
twelve validated passive shippers at Nagpur from August 2026.

Hire is charged to the customer per shipper per trip at the rate printed on
[the H2 2026 rate card](12-rate-card-2026-h2.md). Finance added that line to the
card when this project was approved, so the card and the project were signed in
the same week.

## Milestones

| milestone | owner | due |
|---|---|---|
| First 20 sleeve packets made up and issued at Nagpur | Revathi Iyer | 15 July 2026 |
| Guwahati and Coimbatore packets issued | Riniki Bora, S. Venkatesan | 31 July 2026 |
| Twelve passive shippers validated and in service at Nagpur | Revathi Iyer | 31 August 2026 |
| Shipper hire billing tested end to end with one customer | Anjali Deshmukh | 15 September 2026 |

## Out of scope

PROJ-124 does not change any notification timing, any excursion duration or any
dock grace period. It does not buy shippers for Guwahati or Coimbatore; those
sites continue to refuse pharma staging beyond the SOP limit until a later
project is approved.
