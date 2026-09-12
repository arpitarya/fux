---
title: Dock scheduling rules 2026
doc_id: QCL-OPS-DOCK-03
owner: Farhan Qureshi
reviewers:
  - Revathi Iyer
  - Riniki Bora
status: in_force
effective_date: 2026-03-09
supersedes: seed/09-dock-scheduling-wiki-export.html
---

# Dock scheduling rules 2026

This document replaces the exported wiki page. The wiki page stays readable for
people who remember it, but it is not the booking rule any more, and its Kalpa
slot sync link has been dead since the vendor migration.

## 1. Nagpur DC, also written NGP hub

1.1. Book Nagpur slots in Dockwise before 15:00 on the previous day. The old
16:00 cut-off moved because the ammonia plant defrost window moved.

1.2. Dock assignment: pharma uses dock 4, dairy uses docks 1 and 2, frozen food
uses dock 5, and dry grocery uses dock 6. Dock 6 was added in January 2026 and
does not appear on the wiki page.

1.3. No unloading is planned between 12:40 and 13:20 for the daily ammonia plant
defrost check.

1.4. Late arrival is cancelled automatically in Dockwise after 20 minutes for
dairy and after 30 minutes for dry grocery. Pharma and frozen bookings are never
auto-cancelled; they go to holding lane B and the shift lead is called.

## 2. Grace periods

| class | grace | note |
|---|---|---|
| pharma critical | 20 min | call QA and shift lead; check the red sleeve before moving to dock 4 |
| dairy | 15 min | after-hours wait may apply |
| frozen restaurant chain | 10 min | protect freezer order |
| dry grocery | 30 min | not cold chain |

Pharma grace rose from 15 to 20 minutes because the red-sleeve check takes time
that the old grace did not allow. Dairy grace fell from 20 to 15 minutes because
crate returns were blocking lane 1.

## 3. Guwahati DC

3.1. Guwahati moved from phone slots to Dockwise on 1 February 2026. Riniki Bora
still confirms night slots by phone when the VPN is down, and the slot is written
on the guard register as before.

3.2. Do not idle reefers inside the small yard after 21:30. Rain cover over rear
pallets is mandatory during monsoon unloading and is now billed as a handling
line.

## 4. Coimbatore DC

4.1. Use the south gate for reefers. Avoid Temple Street between 07:45 and 08:30.

4.2. Frozen loads are placed before lunch. Coimbatore joined Dockwise on
1 February 2026 with Guwahati.

## 5. What this document does not do

5.1. It does not set any temperature limit, staging allowance, or excursion
definition. Those live in QCL-QA-SOP-17 and a dock booking never overrules them.

5.2. It does not change driver hours. A slot that cannot be met inside the
driver's remaining hours is rebooked, not driven to.
