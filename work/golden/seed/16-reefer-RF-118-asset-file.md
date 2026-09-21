---
title: Reefer asset file RF-118
doc_id: RF-118
owner: Fleet Control
department: Fleet
status: in_force
effective_date: 2026-04-22
fleet_class: owned_reefer_chilled
base: Nagpur DC
---

# Reefer asset file RF-118

Asset **RF-118** is an owned chilled reefer based at Nagpur DC. It is one of the
two pilot assets named in the 2025 telematics cutover, the other being cold room
C2 — see [Telematics Vendor Decision 2026](11-decision-telematics-vendor-2026.md).

⚠ Write the asset number as RF-118 on every dispatch note, challan and seal
photo. RF-119 and RF-120 are different vehicles with different profiles, and the
three numbers differ by one digit. A wrong digit on a challan has twice sent a
dairy crate run to a frozen body.

## Identity

| field | value |
|---|---|
| asset id | RF-118 |
| chassis year | 2021 |
| body | 14-pallet chilled, dual compartment |
| base | Nagpur DC |
| Tessaline sensor | TSL-RF-118-A |
| Kalpa device | removed 31 October 2025 |
| replaced asset | RF-117, retired 2024 — [reefer asset file RF-117](archive/a06-reefer-RF-117-retired.md) |
| odometer at last service | 41,280 km |

## What RF-118 may carry

RF-118 is a chilled asset. It may carry vaccines, insulin, milk and paneer. It
must not be loaded with frozen food: the body cannot hold the frozen target and
the frozen profile belongs to [RF-120](18-reefer-RF-120-asset-file.md).

This file sets no temperature limit of its own. Every limit and every excursion
duration for the products RF-118 carries is in
[the Temperature Excursion Response SOP](01-sop-temperature-excursion.md), and
the sensor configuration is documented in
[the legacy sensor threshold file](02-sensor-thresholds.yaml). Where this file
and the SOP appear to differ, the SOP wins.

## Known history

On the night of 9 February 2026 the Tessaline display on RF-118 jumped between
9.8 C and 3.4 C inside one minute while a hand-held gun read 3.4 C and a spare
logger read 3.6 C on the same insulin carton. The night team kept the original
sensor in place and put the spare logger next to the product, which is what
section 9 of [the SOP](01-sop-temperature-excursion.md) requires, and refused
the driver's request to restart the app. The sensor was re-seated on 11 February
2026 under maintenance ticket NGP-MNT-731 and the alarm history was not closed
until QA had the export.

RF-118 also appears in the Nagpur night handover log for 18 October 2025, when
its driver asked what Compliance-Red means. Fleet Control has since printed the
escalation groups on the RF-118 cab card.

## Standing instructions

- **Night pharma runs.** Fleet Control's standing instruction for RF-118 is a
  two-driver dispatch for any pharma critical night segment, because a single
  driver cannot legally cover the whole Nagpur-Pune night leg. The limit itself
  is in [the Driver Hours and Road Safety Policy](08-driver-hours-and-safety-policy.md),
  clause 2.3, and this file does not restate it.
- **Red sleeve.** The red sleeve lives in the cab locker, never in the load
  compartment. Contents are listed in
  [the SOP](01-sop-temperature-excursion.md), clause 4.2.
- **Docks.** RF-118 books dock 4 at Nagpur for pharma and docks 1 or 2 for
  dairy, per [Dock scheduling rules 2026](13-dock-scheduling-rules-2026.md).

## Servicing

Reefer unit service is every 500 engine hours or six months, whichever comes
first. The last service was 14 March 2026. RF-118 is planned off-road for its next
service in the first week of September 2026; Fleet Control must reassign its
standing dairy slots before the window opens.
