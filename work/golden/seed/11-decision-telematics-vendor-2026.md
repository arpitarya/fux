---
title: Telematics Vendor Decision 2026
doc_id: QCL-IT-ADR-08
owner: Col. (retd.) H. S. Sandhu
contributors:
  - IT Service Desk
  - Anjali Deshmukh
status: accepted
decision_date: 2026-02-17
supersedes: seed/05-decision-telematics-vendor-2023.md
applies_to:
  - Pune HQ
  - Nagpur DC
  - Guwahati DC
  - Coimbatore DC
---

# Telematics Vendor Decision 2026

Status: Accepted

## Context

The 2023 decision renewed Kalpa Fleet Systems for 36 months from 1 January 2024.
That decision is retired by this record. The cutover thread of July to September
2025 moved Quillfern to Tessaline Telematics for operational data, but no
decision record was ever written, and three audits asked why the accepted record
on file still named a vendor we no longer use.

This record states the present position so that no auditor, trainer, or new
manager has to read an email chain to learn which vendor is current.

## Decision

Tessaline Telematics is the telematics vendor of record for Quillfern Cold
Logistics Pvt. Ltd. from 07 October 2025, confirmed and documented on
17 February 2026. The engagement runs for 48 months from the Nagpur cutover
date and is reviewed no earlier than October 2028.

Commercial control figures, carried forward from purchase order QF-FY26-TSL-044
and unchanged by this record:

| item | figure |
|---|---|
| One-time onboarding after launch credit | Rs. 24.60 lakh |
| Recurring, per active truck per month | Rs. 812 |
| Recurring, per fixed sensor per month | Rs. 265 |
| Kalpa early termination, paid | Rs. 9.30 lakh |
| Support credit, held separately | Rs. 3.10 lakh |

Polling is 60 seconds. The approved export is exception_csv_v2. Trip references
now use the TSL prefix; the KLP prefix is retained only for audit packets
covering trips before 18 August 2025.

## Reasons

The pilot met its acceptance tests. The C2 sensor tracked the USB logger within
0.3 C. Night alerts reached Compliance-Red in the 18 March 2026 test call, which
was the condition Revathi Iyer set after the March 2025 vaccine excursion.

Kalpa's five-minute polling required interpolation in every investigation
timeline. Sixty-second polling removed that argument from three customer
disputes in the first quarter of parallel running.

The local-service argument that carried the 2023 decision no longer holds.
Tessaline's Nagpur field team replaced two truck devices within one working day
during the January 2026 cold wave.

## Consequences

IT retires the Kalpa export script on 30 April 2026. The Kalpa tablet in the
Nagpur guard cabin is a read-only audit device and must not be used to open
alarms. Training material and the QA audit binder are reissued with Tessaline
screenshots before the 2026 vaccine season.

Fleet continues to keep paper driver call logs. That practice survived the
vendor change because network coverage, not the vendor, was the reason for it.

Sandhu's closing comment: "THE DASHBOARD CHANGED; THE DISCIPLINE DOES NOT."
