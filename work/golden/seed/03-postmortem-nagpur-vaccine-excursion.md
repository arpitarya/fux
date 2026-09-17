---
docname: Nagpur rotavirus cold-room excursion
authr: Revathi Iyer
date_seen: 12/03/25
statuss: rushed-review

# Postmortem: Nagpur vaccine excursion, March 2025

This note was written on the afternoon of 12 March 2025 after the C2 cold room
temperature event at Nagpur DC. I am recording the timeline while memories are
fresh. Spelling and header cleanup can wait; evidence cannot.

## Summary

At approximately 02:16 on 12 March 2025, Kalpa probe KV-NGP-C2-07 began
reporting a high temperature in C2, the vaccine cold room at Nagpur DC. The
affected consignment was BharatVac order BV-4437, holding 18,400 vials of
rotavirus vaccine in lots ROTA-9A and ROTA-9B. The approved record showed the
room above +8.0 C for 66 minutes. At the time of the event, the SOP required a
QA call after 30 continuous minutes above +8.0 C for vaccines. The current
corrective action is to reduce that duration.

## Timeline

| time | event |
|---|---|
| 02:16 | Kalpa probe KV-NGP-C2-07 recorded +9.1 C in cold room C2. |
| 02:31 | Alert email went to qa-shared@quillfern.example; no SMS reached Compliance. |
| 02:44 | Bunty placed dry ice trays outside the inner curtain but did not move stock. |
| 03:05 | Driver for paneer route NGP-PNR-18 reported that the C2 door was held open during cross-dock spillover. |
| 03:22 | Cold room record remained at +8.7 C; the door curtain was visibly torn at the left rail. |
| 04:10 | Revathi was called by Farhan after the shift lead escalated by phone. |
| 05:40 | Vaccine pallets were sealed and moved to quarantine row Q-3. |
| 11:30 | Customer notice was sent to BharatVac quality contact. |

## Impact

The stock was not released on the morning route. BharatVac provided a stability
letter for part of the consignment after reviewing lot data. QA destroyed
13,200 vials and conditionally released 5,200 vials under BharatVac letter
BV-QA-2025-0312. Finance booked a write-off of Rs. 7.82 lakh for the destroyed
vials, packaging, and reverse logistics.

The customer notification was late. Under the incident practice then in use, we
treated customer notice as a same-day item after QA review. That is not
acceptable for patient critical stock. The revised procedure must require
customer notice within two hours after confirmation.

The incident also consumed most of the night shift's available quarantine space.
Two dairy returns were left in the outer holding lane while Q-3 was cleared for
the vaccine pallets. No dairy spoilage was confirmed, but the congestion made
the response slower and showed that pharma critical quarantine cannot depend on
moving unrelated stock at the last minute.

Customer service received three different numbers during the morning: 18,400
vials affected, 13,200 vials destroyed, and 5,200 vials conditionally released.
All three numbers were true in their own context, but the first customer draft
mixed them together. The final notice separated affected quantity, destroyed
quantity, and released quantity.

## Root cause

The immediate cause was warm air ingress through a torn door curtain and door
opening during dairy cross-dock spillover. The deeper cause was that the Kalpa
alert routing still pointed to the old qa-shared mailbox, which was not watched
by the night team. The shift lead tried to protect the room by placing dry ice
near the curtain, but the team did not quarantine stock until the manager was
awake.

We also found that dock scheduling pushed paneer loading next to the vaccine
cold-room door. This did not create the torn curtain, but it increased door
traffic during the vulnerable period. The dock plan must separate pharma
loading from dairy overflow during night shift.

## Actions

| action | owner | due | status |
|---|---|---|---|
| Replace C2 left curtain rail and full strip curtain | Farhan Qureshi | 15 Mar 2025 | closed, invoice NGP-MNT-552 |
| Change pharma critical alerts from qa-shared to Compliance-Red SMS and phone tree | IT Service Desk | 18 Mar 2025 | open at time of note |
| Reduce vaccine high-duration trigger from 30 minutes to 15 minutes in SOP | Revathi Iyer | 14 Mar 2025 | closed in SOP rev 3.1 |
| Add two-person night watch for C2 during vaccine loading | Farhan Qureshi | 20 Mar 2025 | no follow-up evidence found |
| Block dairy spillover at C2 door during pharma storage | Farhan Qureshi | 16 Mar 2025 | agreed verbally, not audited |

## What we will not do

We will not blame the driver. The driver reported the door issue when he saw it.
We will not erase the Kalpa record because it is embarrassing. It is the
approved record for this date. We will not ship any vaccine lot merely because
the temperature returned to range after sunrise.

## Closing note

This event is the reason I am asking for two changes: faster pharma escalation
and a shorter vaccine high-duration trigger. If the telematics vendor changes,
the first acceptance test must prove night alerts reach Compliance-Red, not only
the DC manager.

I have deliberately left the rough timeline language in place because the audit
packet should show how the team understood the event on the day. Later SOP
revisions may be cleaner, but this note is the incident record, not a training
poster. Any future reader should compare it with the live SOP before using its
thresholds.
