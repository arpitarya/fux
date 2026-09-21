---
title: Reefer asset file RF-120
doc_id: RF-120
owner: Fleet Control
department: Fleet
status: in_force
effective_date: 2026-04-24
fleet_class: owned_reefer_frozen
base: Nagpur DC
---

# Reefer asset file RF-120

Asset **RF-120** is the owned frozen reefer at Nagpur DC. It is the newest of the
three RF-11x assets and the only one on the frozen profile;
[RF-118](16-reefer-RF-118-asset-file.md) and
[RF-119](17-reefer-RF-119-asset-file.md) are chilled bodies and cannot hold the
frozen target. RF-120 was commissioned on 2 December 2025 and went into service
directly on Tessaline, so it has no Kalpa trip history at all.

## Identity

| field | value |
|---|---|
| asset id | RF-120 |
| chassis year | 2025 |
| body | 16-pallet frozen, single compartment |
| base | Nagpur DC |
| Tessaline sensor | TSL-RF-120-A |
| Kalpa device | never fitted |
| commissioned | 2 December 2025 |

## What RF-120 may carry

RF-120 carries frozen food only: frozen restaurant-chain loads, frozen peas and
frozen chicken on the Nagpur intercity lanes.

**RF-120 must never be loaded with vaccines, insulin, milk or paneer.** A frozen
body cannot be run warm for a chilled load, and a chilled load in a frozen body
is a product loss whether or not a sensor alarms. If a chilled consignment is
offered to RF-120 at the gate, the dock team refuses the load and calls Fleet
Control; the dock team may not reclassify the stock to make the booking work.

The frozen target, the excursion threshold and the defrost allowance that apply
to RF-120 are in the `owned_reefer_frozen` truck profile of
[the legacy sensor threshold file](02-sensor-thresholds.yaml), and the excursion
definition that governs a dispute is clause 2.4 of
[the Temperature Excursion Response SOP](01-sop-temperature-excursion.md). This
file deliberately repeats neither, because the two have disagreed before.

## Dock and staging

RF-120 loads at dock 5 at Nagpur, per
[Dock scheduling rules 2026](13-dock-scheduling-rules-2026.md). Frozen stock
moves directly between freezer and reefer body; the short delay allowance before
the shift lead must be called is in
[the SOP](01-sop-temperature-excursion.md), clause 8.4.

Frozen arrivals get the shortest grace of any class at Nagpur, which is why a
late RF-120 is called in rather than left in the queue.

## Known history

On 6 May 2026 a restaurant-chain frozen chicken load on the Nagpur lane sat at
-16.2 C for 14 minutes and recovered to -18.4 C. QA recorded no excursion. The
case is kept in this file because drivers keep asking why that one was not an
excursion when a similar reading on a hired US-import reefer was: the imported
profile is in Fahrenheit and must be converted before comparison, which is noted
in [the sensor threshold file](02-sensor-thresholds.yaml).

## Servicing

First scheduled service falls due at 500 engine hours. RF-120 is under vendor
warranty until 1 December 2027 and no third-party garage may open the reefer
unit before then without Fleet head approval.
