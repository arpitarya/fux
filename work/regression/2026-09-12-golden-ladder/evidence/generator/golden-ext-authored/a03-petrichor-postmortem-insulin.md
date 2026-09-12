<!-- golden-ext: sibling 2025-07-22 ext/sibling/a03-petrichor-postmortem-insulin.md -->
---
title: Post-incident review — Siliguri insulin excursion
doc_id: PCC-QA-PIR-04
owner: Poulomi Das
status: closed
effective_date: 2025-07-22
---

# Post-incident review — Siliguri insulin excursion

## Summary

Between 02:10 and 04:35 on a Tuesday in June, room PCC-C1 at the Petrichor Cold
Chain Services Siliguri DC held insulin above +8.0 C for 68 continuous minutes.
Sixty-two cartons belonging to one customer were placed in quarantine bay
PCC-Q4. The customer returned a stability letter and the stock was released
under conditional release nine days later. No product was destroyed.

## Timeline

| time | source | event |
|---|---|---|
| 02:10 | Ostrelle Telematics | High-temperature alarm on PCC-C1 |
| 02:14 | app audit log | Alarm acknowledged from the guard cabin tablet |
| 02:52 | door log | Cold room door opened for the first time that shift |
| 03:07 | phone log | Shift lead calls the site manager |
| 03:21 | photographs | Containment starts; stock moved to PCC-Q4 |
| 04:35 | Ostrelle Telematics | Temperature back inside band |
| 09:40 | MBK-style form PCC-F-11 | Quality opens the investigation record |

## What went wrong

1. **Acknowledging an alarm is not containing an excursion.** The alarm was
   acknowledged in four minutes and nobody walked to the room for another
   sixty-seven. The procedure has said this since its first issue; the app makes
   the wrong action the easy one.

2. **The condenser fan had failed twelve days earlier** and the work order sat
   unassigned. The room held band on a cool night and lost it on a warm one, so
   nothing alarmed until the weather changed.

3. **The spare logger bin was empty.** The second reading came from a hand-held
   probe, which this procedure does not accept as a basis for release.

4. The night shift handover note recorded "C1 running warm, watching it" on two
   previous nights. It was never escalated because a handover note is not a
   quality event and nobody made it one.

## What went right

- The stock was not moved, warmed or re-iced to make the display look normal.
- Photographs were complete: display, seal, dock clock and pallet labels.
- The customer was told inside the 3-hour commitment, in the required wording.

## Actions

| action | owner | due | evidence |
|---|---|---|---|
| Acknowledgement in the app requires a containment checkbox | Harsh Vaidya | next release | screenshot in the ticket |
| Re-stock every spare logger bin, Siliguri and Jamshedpur | Poulomi Das | 2025-08-01 | bin audit sheet |
| Any "running warm" handover line opens a quality event | Poulomi Das | 2025-07-31 | revised handover template |
| Condenser work orders older than 7 days escalate automatically | Girish Pai | 2025-09-15 | maintenance system rule |

## What this review does not decide

It does not change any temperature limit or duration. Limits live in the SOP
and a post-incident review never edits one; it can only ask for the change.
