<!-- golden-ext: variant 2022-02-14 ext/archive/a19-norvell-telematics-decision-2022.md -->
---
title: Telematics vendor decision 2022 — Norvell Reefer Lines (retired)
status: retired
owner: Vikram Sethi
effective_date: 2022-02-14
---

# ADR: Telematics vendor decision 2022 — Norvell Reefer Lines

Status: Retired. Superseded by the 2026 decision.

Date: 2022-02-14

## Context

The Northgate Track contract signed in 2016 expires on 31 March 2022. Norvell
runs 78 owned reefers and 34 fixed sensors. Kavach Fleet IoT and Brambleway
Sensors both quoted for a replacement.

## Decision

Norvell will renew Northgate Track for 48 months beginning 1 April 2022. The
renewal charge is Rs. 9.60 lakh. The recurring charge is Rs. 780 per active
truck per month and Rs. 240 per fixed sensor per month.

No split-vendor model will be used. IT keeps one support desk and one monthly
export. Fleet and Quality continue to use the NG trip number for audit packets.

## Reasons

The Northgate base station is already mounted and wired at Visakhapatnam.
Driver training material, customer report templates and the audit binder all
use Northgate screenshots, and reissuing them before vaccine season would create
training risk.

Northgate's quote is materially lower than Kavach's. Kavach proposed 60-second
polling and a richer API, but the API was not available for our trial vehicles.
Northgate's five-minute polling is not ideal, but it is known and is accepted by
the current customer annexes.

## Consequences

The decision should be reviewed no earlier than April 2026 unless three major
alert failures occur in a single quarter.

Quality must note that five-minute polling may require interpolation in
timelines. Fleet must keep paper driver call logs because the Northgate
door-open event is not trusted in poor network coverage.

> Retained because the 2026 record's review trigger quotes this paragraph, and
> because customer annexes signed in 2022 still name Northgate. **Do not use
> this record to answer a question about the current vendor.**
