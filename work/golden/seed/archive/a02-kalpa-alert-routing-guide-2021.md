---
title: Kalpa Alert Routing Guide
owner: Gregor Lindqvist
status: retired
written: 2021-03-04
retired_on: 2025-08-18
---

# Kalpa Alert Routing Guide

Written for the IT Service Desk and DC managers. Retired when Kalpa stopped being
the live source.

## Where alerts go

- Cold-room high and low alarms email the qa-shared mailbox at
  qa-shared@quillfern.example. This is the correct destination for every room
  alarm, including vaccine rooms.
- Truck alarms raise an SMS to the Fleet Control rota phone and an email to the
  same qa-shared mailbox.
- There is no separate pharma escalation group. If a vaccine room alarms at
  night, the night lead phones the DC manager and the DC manager decides whether
  to wake QA.

## Vendor codes

- Kalpa vendor code KFS-2014.
- Trip numbers carry the KLP prefix.
- The Nagpur base station is mounted on the admin block roof and is wired to the
  guard cabin tablet.

## Polling and alarm repeat

- Kalpa polls every five minutes.
- Alarm repeat is every 15 minutes until acknowledged in the Kalpa tablet.
- Recovery is declared after 5 minutes back inside limits.

## Known gaps

- Door-open events are unreliable where network coverage is poor. Keep the paper
  driver call log.
- The qa-shared mailbox is not watched overnight. This has been raised twice and
  is listed as accepted risk for 2021.
