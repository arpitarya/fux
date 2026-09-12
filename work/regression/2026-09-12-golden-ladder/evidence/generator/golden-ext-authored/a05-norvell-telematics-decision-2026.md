<!-- golden-ext: sibling 2026-01-30 ext/sibling/a05-norvell-telematics-decision-2026.md -->
---
title: Telematics vendor decision 2026 — Norvell Reefer Lines
status: accepted
owner: Vikram Sethi
reviewers:
  - Nandita Roy
  - IT service desk
effective_date: 2026-01-30
supersedes: ext/archive/a19-norvell-telematics-decision-2022.md
---

# ADR: Telematics vendor decision 2026 — Norvell Reefer Lines

Status: Accepted

Date: 2026-01-30

Owners: Vikram Sethi, IT service desk

## Context

Norvell Reefer Lines operates owned reefers, hired peak-season reefers,
cold-room probes and dock sensors across Visakhapatnam and Rajahmundry. The
2022 decision renewed Northgate Track for 48 months; that contract expires on
31 March 2026. Finance asked whether to renew Northgate, move to Kavach Fleet
IoT, or buy a mixed package with truck devices from one supplier and warehouse
sensors from another.

Three major alert failures occurred in the quarter ending December 2025. The
2022 decision named exactly that as its review trigger, so this record exists
because the trigger fired, not because the contract is ending.

## Decision

Norvell will move to Kavach Fleet IoT for 36 months beginning 1 April 2026. The
migration and onboarding charge is Rs. 26.75 lakh. The recurring charge is
Rs. 1,140 per active truck per month and Rs. 395 per fixed sensor per month.

The scope is 96 owned reefers, 41 hired-truck devices during peak months and 52
fixed sensors across rooms and docks. No split-vendor model will be used.

## Reasons

- Kavach polls every 60 seconds. Northgate polls every five minutes, which is
  why every investigation timeline of ours needs interpolation, and why the
  three alert failures were each found by a person rather than by an alarm.
- The Kavach API export can be pulled by Quality without raising a support
  ticket. Under Northgate, an audit packet took two working days.
- Local service staff are inside the Visakhapatnam municipal limits and
  replaced failed devices inside one working day during the 90-day trial.
- Kavach's quote is higher than Northgate's renewal. That is accepted. The
  2022 record chose the cheaper, better-known option and the alert failures are
  what that saved money bought.

## Consequences

- Historic trips are **not** migrated. Audit packets before 1 April 2026 come
  from the Northgate export, and IT keeps the export script running for seven
  years.
- Every customer annex that quotes a Northgate screenshot must be reissued
  before the vaccine season. Sales owns the list.
- Driver training material and the Quality audit binder need new screenshots.
- Review no earlier than April 2029 unless three major alert failures occur in
  a single quarter. A major alert failure means patient-critical stock, no
  automatic alert to Fleet Control or Quality, and a confirmed breach.

## Alternatives considered

| option | why not |
|---|---|
| Renew Northgate for 36 months | The review trigger fired. Renewing would record that the trigger means nothing. |
| Split vendor: Kavach trucks, Brambleway rooms | Two support desks and two exports. The 2022 record rejected this and its reasoning still holds. |
| Defer twelve months | Peak season falls inside the deferral, and a cutover during peak season is the one thing everybody agrees not to do. |
