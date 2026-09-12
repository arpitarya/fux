---
type: Report
description: "Every one of the 124 golden questions with the answer fux gave at each of the five built rungs — the artifact a reviewer with the answer key grades."
run: 2026-09-12-golden-ladder
item: W-136
classification: informed
engine: fux-engine 2.0.0-alpha.7
filed: 2026-09-12
---

# The answers fux gave — 124 questions × 5 rungs

**This is the file to grade.** It is generated from
`evidence/<rung>/answers.jsonl` and adds nothing to it.

🔴 **Every number a reviewer derives from this file is `informed`** and **no
delta may be stated from it** — the key in use was authored by Claude as a
stopgap ([W-145](../../open/W-145-codex-regenerates-the-key.md)). Absolute
per-rung scores are fine. "Better than", "worse than" and "unchanged" are not.

## How to read one entry

- **Ranked** is `fux ask --top 10`, in order. Grade `hit@1` against the first
  path and `hit@5` against the first five.
- **Answerable / band** is `fux ask --band`. Abstention is graded from
  `answerable` alone.
- **Answer passage** is `fux answer` — the single best passage with its exact
  line range. This is the *answer*, as against the ranked list of places.
- The passage shown is from **rung-01000**, the largest built rung. The ranked
  lists are shown for all five.

## The rungs

| rung | documents |
|---|---:|
| `rung-seed` | 20 (the seed corpus alone) |
| `rung-00100` | 100 |
| `rung-00200` | 200 |
| `rung-00500` | 500 |
| `rung-01000` | 1 000 |

Every answer-bearing document is under `seed/`. Anything under `ext/` is a
distractor by construction — the extension corpus states no fact about any
seed entity, and the generator refuses to write one that does.

---


## g001

> max hours a driver can be on duty in a day


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/archive/00025-hours-retired.md`<br>4. `ext/sibling/00026-hours.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/archive/00095-hours-retired.md`<br>4. `ext/archive/00025-hours-retired.md`<br>5. `ext/sibling/00026-hours.md` |
| `rung-00500` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/archive/00235-hours-retired.md`<br>4. `ext/archive/00095-hours-retired.md`<br>5. `ext/archive/00305-hours-retired.md` |
| `rung-01000` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00936-hours.md`<br>4. `ext/sibling/00446-hours.md`<br>5. `ext/sibling/00586-hours.md` |

**Answer passage** — `seed/archive/a04-driver-hours-policy-2019.md:L12-L23` · heading *1. Daily limits*

```
## 1. Daily limits

1.1. No driver shall be planned for more than 10 hours on duty in a duty day.
The driving component shall not exceed 8 hours.

1.2. No driver shall drive more than 5 hours continuously without a break of at
least 20 minutes.

1.3. A minimum rest period of 9 consecutive hours is required between duty days.

1.4. Weekly rest is one full day in each calendar week. Fleet Control plans it
with the depot roster.
```

## g002

> our medicine chiller ran warm overnight. after how much time does that become a formal quality event?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `ext/sibling/00229-postmortem.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `ext/sibling/00229-postmortem.md` |

**Answer passage** — `ext/sibling/a03-petrichor-postmortem-insulin.md:L61-L61` · heading *Actions*

```
| action | owner | due | evidence |
|---|---|---|---|
| Any "running warm" handover line opens a quality event | Poulomi Das | 2025-07-31 | revised handover template |
```

## g003

> under revision 2.0 of the SOP, how long above the limit made a vaccine excursion?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00126-sop.md`<br>5. `ext/sibling/a03-petrichor-postmortem-insulin.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00453-sop.md`<br>5. `ext/sibling/00126-sop.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00476-sop.md`<br>5. `ext/sibling/00819-sop.md` |

**Answer passage** — `ext/sibling/a01-marrowbeck-excursion-sop.md:L30-L46` · heading *2. Products and limits*

```
## 2. Products and limits

2.1. Vaccines must remain between +2.0 C and +8.0 C. A vaccine high excursion
is declared when an approved sensor records more than +8.0 C for 25 continuous
minutes. A vaccine low excursion is declared below +2.0 C for 15 continuous
minutes.

2.2. Insulin must remain between +2.0 C and +8.0 C. An insulin high excursion
is declared above +8.0 C for 30 continuous minutes.

2.3. Curd must remain from 0.0 C to +5.0 C in cold rooms and reefer bodies. A
high excursion is declared above +6.0 C for 20 continuous minutes.

2.4. Frozen seafood must remain at or below -18.0 C. An excursion is declared
warmer than -16.0 C for 25 continuous minutes.

2.5. Chilled poultry runs -1.0 C to +2.0 C and has no staging allowance at all.
```

## g004

> acknowledging a tessaline alarm — what does that NOT do?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/00010-postmortem.md`<br>2. `ext/sibling/00043-postmortem.md`<br>3. `ext/sibling/00049-postmortem.md`<br>4. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00010-postmortem.md`<br>2. `ext/sibling/00130-postmortem.md`<br>3. `ext/sibling/00136-postmortem.md`<br>4. `ext/sibling/00066-postmortem.md`<br>5. `ext/sibling/00043-postmortem.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00229-postmortem.md`<br>2. `ext/sibling/00010-postmortem.md`<br>3. `ext/sibling/00310-postmortem.md`<br>4. `ext/sibling/00416-postmortem.md`<br>5. `ext/sibling/00223-postmortem.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00229-postmortem.md`<br>2. `ext/sibling/00589-postmortem.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `ext/sibling/00670-postmortem.md`<br>5. `ext/sibling/00010-postmortem.md` |

**Answer passage** — `ext/sibling/00589-postmortem.md:L27-L35` · heading *What went wrong*

```
## What went wrong

1. **Acknowledging is not containing.** The alarm was acknowledged eleven
   minutes before anyone walked to the room. Acknowledgement silences the app;
   it does nothing to the product.
2. The ammonia plant defrost overlapped the door-open window, so the room had
   no recovery headroom.
3. The spare logger bin was empty, so the second reading came from a hand-held
   probe that the procedure does not accept for release.
```

## g005

> frozen chicken hit -16.2 for 14 minutes then recovered. excursion?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00200` | grounded | true | 1. `ext/filler/00148-release-notes.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `ext/sibling/a01-marrowbeck-excursion-sop.md` |
| `rung-00500` | grounded | true | 1. `ext/filler/00148-release-notes.md`<br>2. `ext/sibling/00349-postmortem.md`<br>3. `ext/sibling/00206-postmortem.md`<br>4. `ext/sibling/00403-postmortem.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-01000` | grounded | true | 1. `ext/filler/00148-release-notes.md`<br>2. `ext/sibling/00349-postmortem.md`<br>3. `ext/sibling/00463-postmortem.md`<br>4. `ext/sibling/00206-postmortem.md`<br>5. `ext/sibling/00613-dockwiki.html` |

**Answer passage** — `ext/filler/00148-release-notes.md:L1-L9` · heading *Release notes*

```
# Release notes

*Sanjot Bhamra · 2021*

## 6.16.2 — 2021-01-14

### Added
- Keyboard navigation for the results list.
- An offline cache so the last query survives a reload.
```

## g006

> what temperature do we have to keep chocolate at?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00100` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/archive/00055-sop-retired.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00039-sop.md` |
| `rung-00200` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00125-sop-retired.md`<br>3. `ext/archive/00055-sop-retired.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/00080-decision.md` |
| `rung-00500` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00125-sop-retired.md`<br>3. `ext/archive/00405-sop-retired.md`<br>4. `ext/archive/00195-sop-retired.md`<br>5. `ext/archive/00265-sop-retired.md` |
| `rung-01000` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00545-sop-retired.md`<br>3. `ext/archive/00475-sop-retired.md`<br>4. `ext/archive/00615-sop-retired.md`<br>5. `ext/archive/00895-sop-retired.md` |

**Answer passage** — `seed/10-new-joiner-faq.md:L27-L32` · heading *Which telematics app do we use?*

```
## Which telematics app do we use?

Old training screenshots still show Kalpa. Most old trips are in Kalpa, and the
guard cabin tablet may still be there for audit lookups. For new trips we are
moving to Tessaline; ask IT for the current login because the app names keep
changing.
```

## g007

> how much extra goes on the bill when fuel gets dear?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00100` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00200` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00500` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-01000` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |

**Answer passage** — `ext/adjacent/a10-vantorix-it-access.md:L36-L36` · heading *Privileged access*

```
| system | who may hold admin | review |
|---|---|---|
| Billing | Finance systems owner | half-yearly |
```

## g008

> can i use a point-and-shoot temperature gun to decide whether goods can leave?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | partial | true | 1. `ext/adjacent/a11-petrichor-hr-leave.md`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/archive/00055-sop-retired.md` |
| `rung-00200` | partial | true | 1. `ext/adjacent/a11-petrichor-hr-leave.md`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/archive/00125-sop-retired.md` |
| `rung-00500` | partial | true | 1. `ext/adjacent/a11-petrichor-hr-leave.md`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/archive/00125-sop-retired.md` |
| `rung-01000` | partial | true | 1. `ext/adjacent/a11-petrichor-hr-leave.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/filler/a16-ward-notice.html`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |

**Answer passage** — `seed/05-decision-telematics-vendor-2023.md:L9-L21` · heading *Context*

```
## Context

Quillfern operates owned reefers, hired peak-season reefers, cold-room probes,
and dock sensors. The current vendor, Kalpa Fleet Systems, has been in use since
2014. The 2023 contract expires on 31 December 2023. Finance asked whether we
should renew Kalpa, move to Tessaline Telematics, or buy a mixed package with
truck devices from one supplier and warehouse sensors from another.

The operating requirement is simple: Fleet Control must see truck location,
temperature, door status, and alert history without calling the driver. QA must
retrieve a trip or room report during an investigation. The vendor must support
Nagpur as central hub, Guwahati and Coimbatore as smaller DCs, and hired trucks
during vaccine and dairy peak months.
```

## g009

> bharatvac order number for the rotavirus consignment


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00100` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>4. `seed/07-rate-card-and-surcharges.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>4. `seed/07-rate-card-and-surcharges.md`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00500` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>4. `seed/07-rate-card-and-surcharges.md`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-01000` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>4. `seed/07-rate-card-and-surcharges.md`<br>5. `seed/12-rate-card-2026-h2.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L13-L21` · heading *Summary*

```
## Summary

At approximately 02:16 on 12 March 2025, Kalpa probe KV-NGP-C2-07 began
reporting a high temperature in C2, the vaccine cold room at Nagpur DC. The
affected consignment was BharatVac order BV-4437, holding 18,400 vials of
rotavirus vaccine in lots ROTA-9A and ROTA-9B. The approved record showed the
room above +8.0 C for 66 minutes. At the time of the event, the SOP required a
QA call after 30 continuous minutes above +8.0 C for vaccines. The current
corrective action is to reduce that duration.
```

## g010

> what is RF-118's fuel consumption?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00100` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/adjacent/00007-finance-close.md`<br>5. `ext/adjacent/00021-finance-close.md` |
| `rung-00200` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00053-decision.md`<br>5. `ext/adjacent/a13-halberd-insurance-claim.eml` |
| `rung-00500` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00053-decision.md`<br>5. `ext/sibling/00353-decision.md` |
| `rung-01000` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00053-decision.md`<br>5. `ext/sibling/00353-decision.md` |

**Answer passage** — `seed/06-re-fw-telematics-cutover.eml#p0` · heading *FW: telematics cutover - revised freeze*

```
# FW: telematics cutover - revised freeze

**From:** Tomás Reyes <tomas.reyes@tessaline.example>

**To:** Farhan Qureshi <farhan.qureshi@quillfern.example>

**Cc:** Anjali Deshmukh <anjali.deshmukh@quillfern.example>

**Date:** Mon, 21 Jul 2025 09:18:04 +0530

Farhan,

Great speaking Friday. Tessaline can move Quillfern faster than the first plan.
We can onboard all owned reefers by 15 September 2025 if Nagpur signs the
installation window this week. Our launch bundle includes 60-second polling,
temperature API v2, door-open alerts, and exception export at no extra charge.

Commercial headline: Rs. 780 per truck per month for 150 or more units, with
warehouse probes priced separately. I know your 2023 ADR liked Kalpa's local
support, but our Pune and Nagpur field teams are ready now.

Regards,
Tom��s

--
Tom��s Reyes
Account Manager, Tessaline Telematics

-----Original Message-----
From: Farhan Qureshi <farhan.qureshi@quillfern.example>
Sent: Monday, July 21, 2025 13:42
To: Anjali Deshmukh <anjali.deshmukh@quillfern.example>
Cc: Col. H. S. Sandhu <hs.sandhu@quillfern.example>
Subject: Re: telematics cutover - revised freeze

Anjali,

15 September is not workable for Nagpur. Banana and dairy overflow start that
week, and dock 3 is already half-dead. If we switch, I want pilot rooms first
and trucks later. My suggested freeze is after 05 October 2025, with C2 and
RF-118 as pilot 
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g011

> how much grace does a pharma truck get at nagpur?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a07-halberd-dock-wiki.html`<br>4. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00200` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a07-halberd-dock-wiki.html`<br>4. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00500` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-01000` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p2` · heading *Nagpur DC / NGP hub*

```
## Nagpur DC / NGP hub

Book Nagpur slots in Dockwise before 16:00 on the previous day. Pharma uses dock 4, dairy uses docks 1 and 2, and frozen food uses dock 5. The old Kalpa slot sync link on the left is broken and should not be used for new bookings.

No unloading is planned between 13:10 and 13:40 because the ammonia plant runs the daily defrost check. Late arrival goes to holding lane B, call shift lead, no automatic cancellation.

Pharma arrivals get 15 minutes grace. Dairy arrivals get 20 minutes grace. Frozen arrivals get 10 minutes grace because the freezer-to-reefer movement is shorter and more sensitive.
```

## g012

> what temperature range do vaccines have to stay in


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/filler/00042-chess.md`<br>5. `ext/filler/00048-chess.md` |
| `rung-00200` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00126-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00500` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `ext/sibling/00453-sop.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/00126-sop.md` |
| `rung-01000` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `ext/sibling/00819-sop.md`<br>4. `ext/sibling/00476-sop.md`<br>5. `ext/sibling/00453-sop.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L73-L78` · heading *What we will not do*

```
## What we will not do

We will not blame the driver. The driver reported the door issue when he saw it.
We will not erase the Kalpa record because it is embarrassing. It is the
approved record for this date. We will not ship any vaccine lot merely because
the temperature returned to range after sunrise.
```

## g013

> what does NOT count as the 30 minute break?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | grounded | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00096-hours.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/00026-hours.md`<br>5. `ext/sibling/00033-sop.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00446-hours.md`<br>2. `ext/sibling/00376-hours.md`<br>3. `ext/sibling/00096-hours.md`<br>4. `ext/sibling/00166-hours.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00446-hours.md`<br>2. `ext/sibling/00796-hours.md`<br>3. `ext/sibling/00376-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `ext/sibling/00656-hours.md` |

**Answer passage** — `ext/sibling/00446-hours.md:L10-L19` · heading *1. Daily limits*

```
# Driver hours and safety policy — Vantorix

## 1. Daily limits

1.1. A driver may drive at most 8 hours in any period of
24 hours, extended to 11 hours no more than twice a week.

1.2. A break of at least 30 minutes is taken after
5 hours of driving. The break is not taken at a dock while
waiting for a slot.
```

## g014

> who insures our cold chain write-offs?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00100` | grounded | true | 1. `ext/sibling/00036-notification.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/sibling/00050-notification.md`<br>4. `ext/sibling/00023-notification.md`<br>5. `ext/sibling/00029-notification.md` |
| `rung-00200` | grounded | true | 1. `ext/sibling/00036-notification.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/sibling/00143-notification.md`<br>4. `ext/sibling/00050-notification.md`<br>5. `ext/sibling/00023-notification.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00323-notification.md`<br>2. `ext/sibling/00036-notification.md`<br>3. `ext/sibling/00203-notification.md`<br>4. `ext/sibling/00269-notification.md`<br>5. `ext/adjacent/a13-halberd-insurance-claim.eml` |
| `rung-01000` | weak | true | 1. `ext/sibling/00590-notification.md`<br>2. `ext/sibling/00323-notification.md`<br>3. `ext/sibling/00036-notification.md`<br>4. `ext/sibling/00869-notification.md`<br>5. `ext/sibling/00563-notification.md` |

**Answer passage** — `ext/sibling/00590-notification.md:L32-L35` · heading *Escalation inside Petrichor Cold Chain Services*

```
## Escalation inside Petrichor Cold Chain Services

Quality, the site manager, Fleet Control when a vehicle is involved, and Finance
when stock is likely to be destroyed.
```

## g015

> which assets were the tessaline pilot


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00200` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00500` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-01000` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |

**Answer passage** — `seed/06-re-fw-telematics-cutover.eml#p0` · heading *FW: telematics cutover - revised freeze*

```
# FW: telematics cutover - revised freeze

**From:** Tomás Reyes <tomas.reyes@tessaline.example>

**To:** Farhan Qureshi <farhan.qureshi@quillfern.example>

**Cc:** Anjali Deshmukh <anjali.deshmukh@quillfern.example>

**Date:** Mon, 21 Jul 2025 09:18:04 +0530

Farhan,

Great speaking Friday. Tessaline can move Quillfern faster than the first plan.
We can onboard all owned reefers by 15 September 2025 if Nagpur signs the
installation window this week. Our launch bundle includes 60-second polling,
temperature API v2, door-open alerts, and exception export at no extra charge.

Commercial headline: Rs. 780 per truck per month for 150 or more units, with
warehouse probes priced separately. I know your 2023 ADR liked Kalpa's local
support, but our Pune and Nagpur field teams are ready now.

Regards,
Tom��s

--
Tom��s Reyes
Account Manager, Tessaline Telematics

-----Original Message-----
From: Farhan Qureshi <farhan.qureshi@quillfern.example>
Sent: Monday, July 21, 2025 13:42
To: Anjali Deshmukh <anjali.deshmukh@quillfern.example>
Cc: Col. H. S. Sandhu <hs.sandhu@quillfern.example>
Subject: Re: telematics cutover - revised freeze

Anjali,

15 September is not workable for Nagpur. Banana and dairy overflow start that
week, and dock 3 is already half-dead. If we switch, I want pilot rooms first
and trucks later. My suggested freeze is after 05 October 2025, with C2 and
RF-118 as pilot 
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g016

> who picks up routine questions while the offices are open?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00100` | grounded | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/filler/a16-ward-notice.html`<br>3. `ext/archive/00035-notification-retired.md`<br>4. `ext/archive/00005-decision-retired.md`<br>5. `ext/archive/00015-ratecard-retired.md` |
| `rung-00200` | weak | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/filler/a16-ward-notice.html`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | weak | true | 1. `ext/filler/a16-ward-notice.html`<br>2. `ext/filler/a17-beekeeping-minutes.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-01000` | weak | true | 1. `ext/filler/a16-ward-notice.html`<br>2. `ext/filler/a17-beekeeping-minutes.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `seed/08-driver-hours-and-safety-policy.md` |

**Answer passage** — `ext/filler/a17-beekeeping-minutes.md:L18-L22` · heading *3. Swarm collection*

```
## 3. Swarm collection

The swarm list is open for the season. Members on the list are asked to keep a
spare nucleus box ready and to answer the phone; last year three calls went to
pest control because nobody on the list picked up.
```

## g017

> the cooling box on a lorry is misbehaving mid-journey. where should the person at the wheel pull in?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/filler/00052-bicycle.txt`<br>3. `ext/filler/00058-bicycle.txt`<br>4. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>5. `ext/filler/00028-release-notes.md` |
| `rung-00200` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/filler/00052-bicycle.txt`<br>3. `ext/filler/00118-bicycle.txt`<br>4. `ext/filler/00112-bicycle.txt`<br>5. `ext/filler/00058-bicycle.txt` |
| `rung-00500` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `ext/filler/00412-bicycle.txt`<br>5. `ext/filler/00238-bicycle.txt` |
| `rung-01000` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/adjacent/a11-petrichor-hr-leave.md`<br>3. `ext/adjacent/a10-vantorix-it-access.md`<br>4. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |

**Answer passage** — `ext/filler/a17-beekeeping-minutes.md:L24-L28` · heading *4. Disease*

```
## 4. Disease

The inspector's visit is expected in May. Members are reminded that comb older
than three years should be rotated out and that a shared hive tool is a shared
infection.
```

## g018

> a manager told someone to keep going past the limit. what is that called?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `ext/filler/00042-chess.md`<br>4. `ext/filler/00048-chess.md`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |
| `rung-00200` | partial | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/filler/00108-chess.md` |
| `rung-00500` | partial | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `ext/sibling/a04-okapi-night-handover.txt` |
| `rung-01000` | partial | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/a04-okapi-night-handover.txt` |

**Answer passage** — `seed/archive/a02-kalpa-alert-routing-guide-2021.md:L14-L23` · heading *Where alerts go*

```
## Where alerts go

- Cold-room high and low alarms email the qa-shared mailbox at
  qa-shared@quillfern.example. This is the correct destination for every room
  alarm, including vaccine rooms.
- Truck alarms raise an SMS to the Fleet Control rota phone and an email to the
  same qa-shared mailbox.
- There is no separate pharma escalation group. If a vaccine room alarms at
  night, the night lead phones the DC manager and the DC manager decides whether
  to wake QA.
```

## g019

> when is a hand written dock reading NOT good enough?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00039-sop.md`<br>4. `ext/sibling/00000-sop.md`<br>5. `ext/sibling/00056-sop.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00060-sop.md`<br>4. `ext/sibling/00120-sop.md`<br>5. `ext/sibling/00126-sop.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00219-sop.md`<br>3. `ext/sibling/00046-quarantine.md`<br>4. `ext/sibling/00300-sop.md`<br>5. `ext/sibling/00406-sop.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00219-sop.md`<br>3. `ext/sibling/00933-sop.md`<br>4. `ext/sibling/00046-quarantine.md`<br>5. `ext/sibling/00300-sop.md` |

**Answer passage** — `ext/sibling/00219-sop.md:L34-L41` · heading *3. Approved records*

```
## 3. Approved records

3.1. Brambleway Sensors is the first electronic source for temperature history at Cindermoor Distribution.
Independent loggers and calibrated probes support an investigation but do not
overrule it unless Quality documents a sensor failure.

3.2. Hand-written dock readings are acceptable only for the first containment
decision and must be replaced by a downloaded record before release or billing.
```

## g020

> what does the wiki page call the place a lorry waits when it misses its turn?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `ext/sibling/00013-dockwiki.html`<br>5. `ext/sibling/00040-dockwiki.html` |
| `rung-00200` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `ext/sibling/00100-dockwiki.html`<br>5. `ext/sibling/00139-dockwiki.html` |
| `rung-00500` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/00379-dockwiki.html`<br>5. `ext/sibling/00100-dockwiki.html` |
| `rung-01000` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/00379-dockwiki.html`<br>5. `ext/sibling/00859-dockwiki.html` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p4` · heading *Coimbatore DC*

```
## Coimbatore DC

Use the south gate for reefers. Avoid Temple Street between 07:45 and 08:30 because school traffic blocks the turn. Frozen loads should be placed before lunch; the afternoon sun hits the outer apron and drivers keep opening doors to check paperwork.
```

## g021

> how long above 8 degrees before it counts as a vaccine excursion


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/00046-quarantine.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `ext/sibling/00033-sop.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/00126-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/00346-postmortem.md`<br>2. `ext/sibling/00276-postmortem.md`<br>3. `ext/sibling/00283-postmortem.md`<br>4. `ext/sibling/00453-sop.md`<br>5. `ext/sibling/00126-sop.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/00550-postmortem.md`<br>2. `ext/sibling/00346-postmortem.md`<br>3. `ext/sibling/00276-postmortem.md`<br>4. `ext/sibling/00529-postmortem.md`<br>5. `ext/sibling/00283-postmortem.md` |

**Answer passage** — `ext/sibling/00276-postmortem.md:L9-L16` · heading *Summary*

```
# Post-incident review — Nashik vaccine excursion

## Summary

On the night in question, room ZAC-D1 at the Zephyrine Agro Cold Nashik site held vaccine
above +8.0 C for 54 continuous minutes. The stock
was placed in quarantine bay ZAC-Q3 and released only after the customer
returned a stability letter.
```

## g022

> fleet control extension


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/archive/a04-driver-hours-policy-2019.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00100` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `ext/filler/00008-syllabus.md`<br>5. `ext/filler/00002-syllabus.md` |
| `rung-00200` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `ext/sibling/00106-notification.md`<br>5. `ext/sibling/00029-notification.md` |
| `rung-00500` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `ext/sibling/00106-notification.md`<br>5. `ext/sibling/00029-notification.md` |
| `rung-01000` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `ext/sibling/00106-notification.md`<br>5. `ext/sibling/00029-notification.md` |

**Answer passage** — `seed/10-new-joiner-faq.md:L20-L25` · heading *Who do I call for a temperature alarm?*

```
## Who do I call for a temperature alarm?

In daytime, call QA desk extension 440. At night in Nagpur, call Bunty or the
shift lead on extension 228, then Fleet Control if a truck is moving. For
patient-critical pharma, Compliance-Red is the escalation group after the 2025
drill. Please do not use the old qa-shared mailbox for urgent alarms.
```

## g023

> what is the dockwise link that works outside the vpn?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00100` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `ext/sibling/a07-halberd-dock-wiki.html`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-01000` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/04-night-shift-handover-log.txt` |

**Answer passage** — `seed/10-new-joiner-faq.md:L34-L42` · heading *What is Dockwise?*

```
## What is Dockwise?

Dockwise is the slot calendar for Nagpur. TODO: ask Farhan for the link that
works outside VPN. Guwahati still uses phone slots with Riniki, and Coimbatore
cares more about the south gate timing than the calendar.

Nagpur late arrival goes to holding lane B, call shift lead, no automatic
cancellation. Yes, this line is copied from the wiki because everyone asks
during induction.
```

## g024

> what does C2 mean


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00060-sop.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00500` | grounded | true | 1. `ext/sibling/00229-postmortem.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `ext/sibling/00060-sop.md`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-01000` | grounded | true | 1. `ext/sibling/00229-postmortem.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `ext/sibling/00060-sop.md`<br>5. `seed/10-new-joiner-faq.md` |

**Answer passage** — `ext/sibling/00229-postmortem.md:L27-L35` · heading *What went wrong*

```
## What went wrong

1. **Acknowledging is not containing.** The alarm was acknowledged eleven
   minutes before anyone walked to the room. Acknowledgement silences the app;
   it does nothing to the product.
2. The ammonia plant defrost overlapped the door-open window, so the room had
   no recovery headroom.
3. The spare logger bin was empty, so the second reading came from a hand-held
   probe that the procedure does not accept for release.
```

## g025

> how often do the sensors sample


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00100` | grounded | true | 1. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00219-sop.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00219-sop.md` |

**Answer passage** — `ext/sibling/a02-vantorix-sensor-thresholds.yaml#p9` · heading *notes*

```
# notes

- Do not open new trips on the retired platform.

- Keep the original sensor in place even when adding a spare logger.

- Auditors ask how the previous vendor was configured, which is why old values stay.
```

## g026

> how long does the tessaline engagement run


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | grounded | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `ext/sibling/a03-petrichor-postmortem-insulin.md` |
| `rung-00200` | grounded | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00500` | grounded | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `ext/sibling/00446-hours.md`<br>5. `ext/sibling/00376-hours.md` |
| `rung-01000` | grounded | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/02-sensor-thresholds.yaml` |

**Answer passage** — `seed/11-decision-telematics-vendor-2026.md:L33-L45` · heading *Decision*

```
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
```

## g027

> which vendor did the 2026 pune audit recommend for curtain replacement?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/12-rate-card-2026-h2.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/sibling/00006-decision.md`<br>4. `ext/sibling/00059-decision.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00200` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/sibling/00006-decision.md`<br>4. `ext/sibling/00146-decision.md`<br>5. `ext/sibling/00059-decision.md` |
| `rung-00500` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/sibling/00173-decision.md`<br>4. `ext/sibling/00216-decision.md`<br>5. `ext/sibling/00006-decision.md` |
| `rung-01000` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/12-rate-card-2026-h2.md`<br>4. `ext/sibling/00479-decision.md`<br>5. `ext/sibling/00173-decision.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L29-L29` · heading *Timeline*

```
| time | event |
|---|---|
| 02:44 | Bunty placed dry ice trays outside the inner curtain but did not move stock. |
```

## g028

> how much does tessaline charge for one warehouse probe?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |
| `rung-00200` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |
| `rung-00500` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/adjacent/a10-vantorix-it-access.md`<br>5. `ext/sibling/a05-norvell-telematics-decision-2026.md` |
| `rung-01000` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/adjacent/a10-vantorix-it-access.md`<br>5. `ext/sibling/a05-norvell-telematics-decision-2026.md` |

**Answer passage** — `seed/05-decision-telematics-vendor-2023.md:L9-L21` · heading *Context*

```
## Context

Quillfern operates owned reefers, hired peak-season reefers, cold-room probes,
and dock sensors. The current vendor, Kalpa Fleet Systems, has been in use since
2014. The 2023 contract expires on 31 December 2023. Finance asked whether we
should renew Kalpa, move to Tessaline Telematics, or buy a mixed package with
truck devices from one supplier and warehouse sensors from another.

The operating requirement is simple: Fleet Control must see truck location,
temperature, door status, and alert history without calling the driver. QA must
retrieve a trip or room report during an investigation. The vendor must support
Nagpur as central hub, Guwahati and Coimbatore as smaller DCs, and hired trucks
during vaccine and dairy peak months.
```

## g029

> karim drove over his hours twice. which rules did that touch?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00100` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `ext/filler/00042-chess.md`<br>5. `ext/filler/00048-chess.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `ext/filler/00108-chess.md`<br>3. `ext/filler/00042-chess.md`<br>4. `ext/filler/00102-chess.md`<br>5. `ext/filler/00048-chess.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `ext/filler/00288-chess.md`<br>3. `ext/filler/00348-chess.md`<br>4. `ext/filler/00108-chess.md`<br>5. `ext/filler/00162-chess.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/filler/00528-chess.md`<br>4. `ext/filler/00288-chess.md`<br>5. `ext/filler/00888-chess.md` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p6` · heading *Customer class grace table*

```
| class | grace | penalty note |
|---|---|---|
| dairy | after-hours wait may apply |  |
```

## g030

> guwahati rain cover — who gets told and does the customer pay for it?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/12-rate-card-2026-h2.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00200` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00500` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-01000` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p3` · heading *Guwahati DC*

```
## Guwahati DC

Guwahati still assigns night slots by phone. Call Riniki Bora before 18:00 and write the slot on the guard register. Do not idle reefers inside the small yard after 21:30; neighbours complain and security closes the side gate. Rain cover is mandatory over rear pallets during monsoon unloading.
```

## g031

> if two write-ups disagree about what the temperature was, which one wins?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00055-sop-retired.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/archive/00035-notification-retired.md`<br>5. `ext/archive/00005-decision-retired.md` |
| `rung-00200` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00125-sop-retired.md`<br>3. `ext/archive/00055-sop-retired.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/adjacent/a13-halberd-insurance-claim.eml` |
| `rung-00500` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00125-sop-retired.md`<br>3. `ext/archive/00405-sop-retired.md`<br>4. `ext/archive/00195-sop-retired.md`<br>5. `ext/archive/00265-sop-retired.md` |
| `rung-01000` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/archive/00545-sop-retired.md`<br>3. `ext/archive/00475-sop-retired.md`<br>4. `ext/archive/00615-sop-retired.md`<br>5. `ext/archive/00895-sop-retired.md` |

**Answer passage** — `seed/10-new-joiner-faq.md:L1-L5` · heading *New joiner FAQ*

```
# New joiner FAQ

Welcome to Quillfern! This is the friendly version, not the legal one. If
Revathi madam and this page disagree, believe Revathi. If Colonel Sandhu and
this page disagree, please do not tell him this page existed 🙂
```

## g032

> how long may somebody stay behind the wheel in one stretch?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/filler/00042-chess.md`<br>3. `ext/filler/00048-chess.md`<br>4. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>5. `ext/filler/00052-bicycle.txt` |
| `rung-00200` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/filler/00108-chess.md`<br>3. `ext/filler/00042-chess.md`<br>4. `ext/filler/00102-chess.md`<br>5. `ext/filler/00048-chess.md` |
| `rung-00500` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/filler/00288-chess.md`<br>4. `ext/filler/00348-chess.md`<br>5. `ext/filler/00108-chess.md` |
| `rung-01000` | partial | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `ext/filler/a15-release-notes-tilecutter.md`<br>4. `ext/filler/00528-chess.md`<br>5. `ext/filler/00288-chess.md` |

**Answer passage** — `ext/filler/a15-release-notes-tilecutter.md:L37-L40` · heading *Security*

```
### Security
- Dependency bump for a transitive parser advisory. No exploit path was found
  in Tilecutter itself; the bump is precautionary and is recorded because
  "precautionary" is a claim somebody will check.
```

## g033

> which room is vaccine stock in at nagpur and which bay does it go to when held?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/00046-quarantine.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `ext/sibling/00010-postmortem.md`<br>5. `ext/sibling/00043-postmortem.md` |
| `rung-00200` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `ext/sibling/00126-sop.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00500` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/00346-postmortem.md`<br>3. `ext/sibling/00276-postmortem.md`<br>4. `ext/sibling/00283-postmortem.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-01000` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/00550-postmortem.md`<br>3. `ext/sibling/00346-postmortem.md`<br>4. `ext/sibling/00276-postmortem.md`<br>5. `ext/sibling/00529-postmortem.md` |

**Answer passage** — `ext/sibling/00550-postmortem.md:L8-L15` · heading *Summary*

```
# Post-incident review — Rajahmundry vaccine excursion

## Summary

On the night in question, room NRL-B4 at the Norvell Reefer Lines Rajahmundry site held vaccine
above +8.0 C for 72 continuous minutes. The stock
was placed in quarantine bay NRL-Q1 and released only after the customer
returned a stability letter.
```

## g034

> which mailbox should an urgent pharma alarm go to?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00100` | grounded | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00200` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-00500` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-01000` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |

**Answer passage** — `seed/archive/a02-kalpa-alert-routing-guide-2021.md:L14-L23` · heading *Where alerts go*

```
## Where alerts go

- Cold-room high and low alarms email the qa-shared mailbox at
  qa-shared@quillfern.example. This is the correct destination for every room
  alarm, including vaccine rooms.
- Truck alarms raise an SMS to the Fleet Control rota phone and an email to the
  same qa-shared mailbox.
- There is no separate pharma escalation group. If a vaccine room alarms at
  night, the night lead phones the DC manager and the DC manager decides whether
  to wake QA.
```

## g035

> a dairy truck waited two hours past its slot. what do we bill and what was free?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00100` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `ext/archive/a20-braidwood-rate-card-2023.md`<br>5. `ext/sibling/a06-braidwood-rate-card-2026.md` |
| `rung-00200` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `ext/archive/a20-braidwood-rate-card-2023.md`<br>5. `ext/sibling/a06-braidwood-rate-card-2026.md` |
| `rung-00500` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/archive/a20-braidwood-rate-card-2023.md`<br>5. `ext/sibling/a06-braidwood-rate-card-2026.md` |
| `rung-01000` | weak | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/archive/a20-braidwood-rate-card-2023.md`<br>5. `ext/sibling/a06-braidwood-rate-card-2026.md` |

**Answer passage** — `seed/07-rate-card-and-surcharges.md:L21-L21` · heading *Surcharges*

```
| item | 2024 rule | 2026 rule |
|---|---|---|
| After-hours dock wait | first 60 minutes free, then Rs. 500/hour | first 45 minutes free, then Rs. 650/hour |
```

## g036

> what is the continuous driving limit and break length now?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/00026-hours.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `ext/sibling/00033-sop.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/00026-hours.md`<br>2. `ext/sibling/00096-hours.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/00446-hours.md`<br>2. `ext/sibling/00376-hours.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `ext/sibling/00236-hours.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/00936-hours.md`<br>2. `ext/sibling/00446-hours.md`<br>3. `ext/sibling/00586-hours.md`<br>4. `ext/sibling/00866-hours.md`<br>5. `ext/sibling/00796-hours.md` |

**Answer passage** — `ext/sibling/00446-hours.md:L10-L19` · heading *1. Daily limits*

```
# Driver hours and safety policy — Vantorix

## 1. Daily limits

1.1. A driver may drive at most 8 hours in any period of
24 hours, extended to 11 hours no more than twice a week.

1.2. A break of at least 30 minutes is taken after
5 hours of driving. The break is not taken at a dock while
waiting for a slot.
```

## g037

> how much of the tessaline export was missing for RF-221


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00100` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00200` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00500` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/10-new-joiner-faq.md`<br>5. `ext/sibling/00426-decision.md` |
| `rung-01000` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |

**Answer passage** — `seed/02-sensor-thresholds.yaml#p10` · heading *tessaline_mapping*

```
# tessaline_mapping

**pilot_live_date:** 2025-08-18

**api_export:** exception_csv_v2

**nagpur_room_C2_sensor:** TSL-NGP-C2-07

**nagpur_room_C3_sensor:** TSL-NGP-C3-02

**frozen_F1_sensor:** TSL-NGP-F1-04

**truck_RF_118_sensor:** TSL-RF-118-A

**truck_RF_221_sensor:** TSL-RF-221-A
```

## g038

> what do we charge now for putting solid CO2 into a box?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/12-rate-card-2026-h2.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/07-rate-card-and-surcharges.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00100` | partial | true | 1. `ext/filler/00028-release-notes.md`<br>2. `ext/filler/00022-release-notes.md`<br>3. `ext/filler/a16-ward-notice.html`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00200` | partial | true | 1. `ext/filler/a16-ward-notice.html`<br>2. `ext/filler/00028-release-notes.md`<br>3. `ext/filler/00148-release-notes.md`<br>4. `ext/filler/00088-release-notes.md`<br>5. `ext/filler/00022-release-notes.md` |
| `rung-00500` | partial | true | 1. `ext/filler/a16-ward-notice.html`<br>2. `ext/filler/00028-release-notes.md`<br>3. `ext/filler/00442-release-notes.md`<br>4. `ext/filler/00448-release-notes.md`<br>5. `ext/filler/00322-release-notes.md` |
| `rung-01000` | partial | true | 1. `ext/filler/a16-ward-notice.html`<br>2. `ext/filler/00028-release-notes.md`<br>3. `ext/filler/00442-release-notes.md`<br>4. `ext/filler/00928-release-notes.md`<br>5. `ext/filler/00448-release-notes.md` |

**Answer passage** — `ext/filler/a16-ward-notice.html#p1` · heading *Solid waste*

```
## Solid waste

Wet and dry waste are collected on alternate days. Garden waste in bulk is collected on the first Saturday of the month, from the collection point only. Construction debris is not collected and must be removed by the owner.
```

## g039

> under the old 2019 policy, how many hours could a driver actually drive?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/archive/00025-hours-retired.md`<br>5. `ext/archive/00035-notification-retired.md` |
| `rung-00200` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `ext/archive/00095-hours-retired.md` |
| `rung-00500` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00446-hours.md`<br>4. `ext/sibling/00376-hours.md`<br>5. `ext/sibling/00026-hours.md` |
| `rung-01000` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `ext/archive/00725-hours-retired.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `ext/sibling/00936-hours.md`<br>5. `ext/sibling/00446-hours.md` |

**Answer passage** — `seed/archive/a04-driver-hours-policy-2019.md:L8-L10` · heading *Driver Hours and Road Discipline Policy (2019)*

```
# Driver Hours and Road Discipline Policy (2019)

Issued to all Quillfern drivers and hired-truck providers. Kept for record.
```

## g040

> when may somebody back a vehicle up in the yard late at night?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |
| `rung-00200` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |
| `rung-00500` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |
| `rung-01000` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |

**Answer passage** — `ext/sibling/a07-halberd-dock-wiki.html#p3` · heading *Jalandhar cross-dock*

```
## Jalandhar cross-dock

Jalandhar still assigns night slots by phone. Call Elango Subramani before 19:00 and write the slot on the guard register. Do not idle reefers inside the yard after 22:00; the yard backs onto housing. Rain cover over rear pallets is mandatory during monsoon unloading.
```

## g041

> insulin high excursion duration?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `seed/15-customer-notification-matrix-2026.md`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00100` | weak | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/00033-sop.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/00033-sop.md`<br>3. `ext/sibling/00060-sop.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/00033-sop.md`<br>3. `ext/sibling/00300-sop.md`<br>4. `ext/sibling/00060-sop.md`<br>5. `ext/sibling/00289-postmortem.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/00709-postmortem.md`<br>3. `ext/sibling/00033-sop.md`<br>4. `ext/sibling/00943-postmortem.md`<br>5. `ext/sibling/00289-postmortem.md` |

**Answer passage** — `ext/sibling/00033-sop.md:L10-L20` · heading *1. Purpose*

```
# Temperature Excursion Response SOP

## 1. Purpose

1.1. This procedure defines how Cindermoor Distribution responds to a suspected or confirmed
temperature excursion in its cold rooms, docks, cross-dock lanes and reefer
bodies at the Raipur site. It applies to insulin and to any customer stock moved
under a written temperature commitment.

1.2. An excursion means a recorded temperature outside the allowed band for
longer than the allowed duration. One hand-held reading does not release stock.
```

## g042

> monthly charge per fixed sensor now


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/12-rate-card-2026-h2.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `ext/sibling/00059-decision.md`<br>2. `ext/sibling/00006-decision.md`<br>3. `ext/sibling/00020-decision.md`<br>4. `ext/sibling/00053-decision.md`<br>5. `ext/archive/a19-norvell-telematics-decision-2022.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00146-decision.md`<br>2. `ext/sibling/00059-decision.md`<br>3. `ext/sibling/00006-decision.md`<br>4. `ext/sibling/00020-decision.md`<br>5. `ext/sibling/00080-decision.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00216-decision.md`<br>2. `ext/sibling/00359-decision.md`<br>3. `ext/sibling/00299-decision.md`<br>4. `ext/sibling/00146-decision.md`<br>5. `ext/sibling/00413-decision.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00216-decision.md`<br>2. `ext/sibling/00566-decision.md`<br>3. `ext/sibling/00359-decision.md`<br>4. `ext/sibling/00299-decision.md`<br>5. `ext/sibling/00146-decision.md` |

**Answer passage** — `ext/sibling/00216-decision.md:L18-L25` · heading *Decision*

```
## Decision

Cindermoor Distribution will move to Brambleway Sensors for 48 months. The migration
and onboarding charge is Rs. 26.39 lakh. The
recurring charge is Rs. 1312 per active truck per month and
Rs. 190 per fixed sensor per month.

No split-vendor model will be used. One support desk, one monthly export.
```

## g043

> is a cold-chain crisis on its own enough to let somebody stay on the road longer?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/archive/a04-driver-hours-policy-2019.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/filler/a15-release-notes-tilecutter.md`<br>4. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>5. `ext/sibling/a08-sundari-notification-matrix.md` |
| `rung-00200` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/filler/a15-release-notes-tilecutter.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00500` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `ext/filler/a15-release-notes-tilecutter.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `ext/filler/a15-release-notes-tilecutter.md`<br>5. `seed/01-sop-temperature-excursion.md` |

**Answer passage** — `ext/sibling/a08-sundari-notification-matrix.md:L26-L26` · heading *1. Deadlines*

```
| customer class | trigger | notify within | channel |
|---|---|---:|---|
| frozen restaurant chain | vehicle still on the road | immediately | phone to the receiving kitchen |
```

## g044

> what notification window did the 2025 matrix set for patient critical stock?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/15-customer-notification-matrix-2026.md`<br>2. `seed/14-customer-notification-matrix-2025.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00050-notification.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/15-customer-notification-matrix-2026.md`<br>5. `ext/sibling/00023-notification.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00050-notification.md`<br>2. `ext/sibling/00083-notification.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00050-notification.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `ext/sibling/00269-notification.md`<br>4. `ext/sibling/00083-notification.md`<br>5. `ext/sibling/00170-notification.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00050-notification.md`<br>3. `ext/sibling/00863-notification.md`<br>4. `ext/sibling/00736-notification.md`<br>5. `ext/sibling/00683-notification.md` |

**Answer passage** — `ext/sibling/00050-notification.md:L8-L14` · heading *Who is told, and how fast*

```
# Customer notification matrix — Cindermoor 2025

## Who is told, and how fast

| customer class | trigger | notify within | channel |
|---|---|---:|---|
| patient critical | confirmed excursion | 3 h | phone then written |
```

## g045

> an auditor wants the kalpa-era commercial figures. where are they?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-01000` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |

**Answer passage** — `seed/11-decision-telematics-vendor-2026.md:L33-L45` · heading *Decision*

```
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
```

## g046

> how often does the new kit send a reading?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/adjacent/a14-sundari-onboarding.html`<br>3. `seed/15-customer-notification-matrix-2026.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00200` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `ext/adjacent/a14-sundari-onboarding.html`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `ext/adjacent/a14-sundari-onboarding.html`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-01000` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |

**Answer passage** — `seed/10-new-joiner-faq.md:L1-L5` · heading *New joiner FAQ*

```
# New joiner FAQ

Welcome to Quillfern! This is the friendly version, not the legal one. If
Revathi madam and this page disagree, believe Revathi. If Colonel Sandhu and
this page disagree, please do not tell him this page existed 🙂
```

## g047

> when was coimbatore supposed to cut over


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00100` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `ext/adjacent/a11-petrichor-hr-leave.md` |
| `rung-00200` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `ext/adjacent/a11-petrichor-hr-leave.md` |
| `rung-00500` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `ext/adjacent/a11-petrichor-hr-leave.md` |
| `rung-01000` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |

**Answer passage** — `seed/archive/a03-dock-scheduling-wiki-2021.html#p6` · heading *Guwahati and Coimbatore*

```
## Guwahati and Coimbatore

Both sites assign slots by phone. Guwahati calls the yard supervisor; Coimbatore calls the security desk. Neither site has a calendar.

Last edited by Nalini Patil. Page id: WIKI-NGP-DOCK-12.
```

## g048

> does dozing in the cab while queueing count as proper time off?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/00026-hours.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00200` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/00026-hours.md`<br>3. `ext/sibling/00096-hours.md`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00500` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/00446-hours.md`<br>3. `ext/sibling/00376-hours.md`<br>4. `ext/sibling/00026-hours.md`<br>5. `ext/sibling/00096-hours.md` |
| `rung-01000` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/00936-hours.md`<br>3. `ext/sibling/00446-hours.md`<br>4. `ext/sibling/00586-hours.md`<br>5. `ext/sibling/00866-hours.md` |

**Answer passage** — `seed/04-night-shift-handover-log.txt:L1-L35` · heading *—*

```
Nagpur DC night handover log
kept at security desk copy, typed from WhatsApp + notebook. spelling not fixed.

2025-09-17 / Bunty
f1 freezer door gasket sweating again. frozen peas from Mangal Foods moved from rack F1-A to F1-B at 01:20 because left side had ice fog and floor wet. temp display said -17.4 then -18.2 after unit defrost. told Prakash maint to check morning. no customer issue yet. reefer RF-203 came 25 min late, driver said ring road jam. dock 5 still took him because frozen queue empty.

2025-10-05 / Bunty
manjara milk crates waiting lane 2 at 6.2 C for 38 mins while dock 1 blocked by empty crate return. i told Farhan sir on phone. he said count as staging, not excursion, because crates were not handed to QA yet. writing here only so day shift knows. please check with madam because SOP is confusing on milk. same night Tessaline alarm was not showing for lane sensor, only room D1.

2025-10-18 / Saira
two hired trucks came without red sleeve packets. guard sent them inside because rain heavy. i made red tags from old labels and kept seal tape in office drawer. one packet short for BharatVac sample return. ask stores for proper sleeves. driver on RF-118 asked what Compliance-Red means. new boys don't know all these groups.

2025-11-02 / Bunty
kalpa old tablet still in guard cabin. IT said keep for past trips only. do not send tablet photo to customer unless QA asks. T
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g049

> night extension number for nagpur


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00100` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00200` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00500` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-01000` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |

**Answer passage** — `seed/10-new-joiner-faq.md:L20-L25` · heading *Who do I call for a temperature alarm?*

```
## Who do I call for a temperature alarm?

In daytime, call QA desk extension 440. At night in Nagpur, call Bunty or the
shift lead on extension 228, then Fleet Control if a truck is moving. For
patient-critical pharma, Compliance-Red is the escalation group after the 2025
drill. Please do not use the old qa-shared mailbox for urgent alarms.
```

## g050

> how quickly does a vaccine customer have to hear from us?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00200` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/07-rate-card-and-surcharges.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00346-postmortem.md`<br>3. `ext/sibling/00276-postmortem.md`<br>4. `ext/sibling/00283-postmortem.md`<br>5. `seed/07-rate-card-and-surcharges.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00550-postmortem.md`<br>3. `ext/sibling/00346-postmortem.md`<br>4. `ext/sibling/00276-postmortem.md`<br>5. `ext/sibling/00529-postmortem.md` |

**Answer passage** — `ext/sibling/a08-sundari-notification-matrix.md:L62-L67` · heading *5. What this matrix does not do*

```
## 5. What this matrix does not do

5.1. It sets no temperature limit and no staging allowance.

5.2. It does not authorise a disposition. A customer being notified quickly is
not a customer agreeing to anything.
```

## g051

> what is NOT accepted as evidence that a corrective action is finished?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00010-postmortem.md`<br>5. `ext/sibling/00043-postmortem.md` |
| `rung-00200` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00010-postmortem.md`<br>5. `ext/sibling/00130-postmortem.md` |
| `rung-00500` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00229-postmortem.md`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-01000` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `ext/sibling/00229-postmortem.md` |

**Answer passage** — `seed/01-sop-temperature-excursion.md:L205-L218` · heading *10. Closure*

```
## 10. Closure

10.1. The QA head or nominated deputy closes pharma critical investigations. The
DC manager may close dairy and frozen investigations only after QA records the
disposition.

10.2. Corrective and preventive actions must have an owner, a due date, and
evidence of completion. "Discussed on call" is not completion evidence.

10.3. Training actions shall be assigned by role, not by name alone, so that new
staff receive the same correction.

10.4. The case file must be kept for seven years for pharma critical stock and
three years for food stock.
```

## g052

> minimum rest between two duty days


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00100` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/filler/a16-ward-notice.html` |
| `rung-00200` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00446-hours.md`<br>4. `ext/sibling/00376-hours.md`<br>5. `ext/sibling/00026-hours.md` |
| `rung-01000` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00936-hours.md`<br>4. `ext/sibling/00446-hours.md`<br>5. `ext/sibling/00586-hours.md` |

**Answer passage** — `seed/archive/a04-driver-hours-policy-2019.md:L12-L23` · heading *1. Daily limits*

```
## 1. Daily limits

1.1. No driver shall be planned for more than 10 hours on duty in a duty day.
The driving component shall not exceed 8 hours.

1.2. No driver shall drive more than 5 hours continuously without a break of at
least 20 minutes.

1.3. A minimum rest period of 9 consecutive hours is required between duty days.

1.4. Weekly rest is one full day in each calendar week. Fleet Control plans it
with the depot roster.
```

## g053

> which late bookings are NOT cancelled automatically?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/00013-dockwiki.html`<br>4. `ext/sibling/00040-dockwiki.html`<br>5. `ext/sibling/00019-dockwiki.html` |
| `rung-00200` | weak | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/00100-dockwiki.html`<br>4. `ext/sibling/00139-dockwiki.html`<br>5. `ext/sibling/00013-dockwiki.html` |
| `rung-00500` | weak | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/00379-dockwiki.html`<br>4. `ext/sibling/00100-dockwiki.html`<br>5. `ext/sibling/00139-dockwiki.html` |
| `rung-01000` | weak | true | 1. `ext/sibling/a07-halberd-dock-wiki.html`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/00379-dockwiki.html`<br>4. `ext/sibling/00859-dockwiki.html`<br>5. `ext/sibling/00700-dockwiki.html` |

**Answer passage** — `ext/sibling/00379-dockwiki.html#p7` · heading *Late arrivals*

```
## Late arrivals

A late arrival goes to the south holding lane and the shift lead is called. Booking is not cancelled automatically.

Last edited by Vikram Sethi. Page id: WIKI-OKF-82.
```

## g054

> who is allowed to change the alarm numbers in the tracking software?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00100` | partial | true | 1. `ext/archive/00035-notification-retired.md`<br>2. `ext/archive/00005-decision-retired.md`<br>3. `ext/archive/00015-ratecard-retired.md`<br>4. `ext/archive/00045-quarantine-retired.md`<br>5. `ext/archive/00025-hours-retired.md` |
| `rung-00200` | partial | true | 1. `ext/archive/00035-notification-retired.md`<br>2. `ext/archive/00085-ratecard-retired.md`<br>3. `ext/archive/00005-decision-retired.md`<br>4. `ext/archive/00105-notification-retired.md`<br>5. `ext/archive/00015-ratecard-retired.md` |
| `rung-00500` | partial | true | 1. `ext/archive/00035-notification-retired.md`<br>2. `ext/archive/00245-notification-retired.md`<br>3. `ext/archive/00455-notification-retired.md`<br>4. `ext/archive/00435-ratecard-retired.md`<br>5. `ext/archive/00175-notification-retired.md` |
| `rung-01000` | partial | true | 1. `ext/archive/00035-notification-retired.md`<br>2. `ext/archive/00625-postmortem-retired.md`<br>3. `ext/archive/00485-postmortem-retired.md`<br>4. `ext/archive/00245-notification-retired.md`<br>5. `ext/archive/00455-notification-retired.md` |

**Answer passage** — `ext/archive/00035-notification-retired.md:L13-L23` · heading *What this edition said*

```
## What this edition said

1. The Surat site booked slots by telephone and wrote them on the guard
   register. There was no calendar system.
2. The alarm threshold for the curd room was
   6.0 C for 51 continuous minutes —
   longer than the current edition allows.
3. Notification to patient-critical customers was "the same working day". The
   current edition states a number of hours instead.
4. Quarantine was a marked corner of the dispatch bay rather than a separate
   room with its own door log.
```

## g055

> pharma dock grace — what did the night team have in feb 2026 and what would they have now?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `ext/sibling/00013-dockwiki.html`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `ext/filler/00042-chess.md` |
| `rung-00200` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `ext/sibling/00013-dockwiki.html`<br>4. `ext/sibling/00073-dockwiki.html`<br>5. `ext/filler/00042-chess.md` |
| `rung-00500` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `ext/sibling/00379-dockwiki.html`<br>3. `ext/sibling/00373-dockwiki.html`<br>4. `ext/sibling/00013-dockwiki.html`<br>5. `ext/sibling/00199-dockwiki.html` |
| `rung-01000` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `ext/sibling/00379-dockwiki.html`<br>3. `ext/sibling/00700-dockwiki.html`<br>4. `ext/sibling/00499-dockwiki.html`<br>5. `ext/sibling/00373-dockwiki.html` |

**Answer passage** — `seed/13-dock-scheduling-rules-2026.md:L48-L56` · heading *3. Guwahati DC*

```
## 3. Guwahati DC

3.1. Guwahati moved from phone slots to Dockwise on 1 February 2026. Riniki Bora
still confirms night slots by phone when the VPN is down, and the slot is written
on the guard register as before.

3.2. Do not idle reefers inside the small yard after 21:30. Rain cover over rear
pallets is mandatory during monsoon unloading and is now billed as a handling
line.
```

## g056

> what may the first note to the client say, and what may it not promise?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/07-rate-card-and-surcharges.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00050-notification.md`<br>3. `ext/sibling/00023-notification.md`<br>4. `ext/sibling/00029-notification.md`<br>5. `ext/sibling/00036-notification.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00143-notification.md`<br>3. `ext/sibling/00050-notification.md`<br>4. `ext/sibling/00023-notification.md`<br>5. `ext/sibling/00106-notification.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00143-notification.md`<br>3. `ext/sibling/00050-notification.md`<br>4. `ext/sibling/00443-notification.md`<br>5. `ext/sibling/00263-notification.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/a08-sundari-notification-matrix.md`<br>2. `ext/sibling/00143-notification.md`<br>3. `ext/sibling/00890-notification.md`<br>4. `ext/sibling/00809-notification.md`<br>5. `ext/sibling/00929-notification.md` |

**Answer passage** — `ext/sibling/00890-notification.md:L21-L25` · heading *Wording*

```
## Wording

The first notice says *"temperature excursion under investigation"* and nothing
more. Nobody promises release, replacement credit or insurance recovery before
Quality records a disposition.
```

## g057

> what is the approved export file called


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `ext/sibling/00033-sop.md` |
| `rung-00200` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00500` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-01000` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |

**Answer passage** — `seed/archive/a01-sop-temperature-excursion-rev2.md:L38-L48` · heading *3. Approved records*

```
## 3. Approved records

3.1. Kalpa Fleet Systems is the first electronic source for approved temperature
history. The monthly Kalpa trip export is the preferred file, and the KLP trip
number is quoted in every audit packet.

3.2. Kalpa polls every five minutes. Investigators may interpolate between
readings where a timeline requires it, and must say in the record that they did.

3.3. Independent USB loggers and calibrated hand-held thermometers may support an
investigation but do not overrule Kalpa.
```

## g058

> the tracking box starts beeping while the vehicle is moving. what is the person at the wheel supposed to do?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00100` | partial | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/filler/00028-release-notes.md`<br>3. `ext/filler/00022-release-notes.md`<br>4. `ext/sibling/00026-hours.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/00026-hours.md`<br>3. `ext/sibling/00096-hours.md`<br>4. `ext/filler/00028-release-notes.md`<br>5. `ext/filler/00148-release-notes.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/00446-hours.md`<br>3. `ext/sibling/00376-hours.md`<br>4. `ext/sibling/00026-hours.md`<br>5. `ext/sibling/00096-hours.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/sibling/00936-hours.md`<br>3. `ext/sibling/00446-hours.md`<br>4. `ext/sibling/00586-hours.md`<br>5. `ext/sibling/00866-hours.md` |

**Answer passage** — `ext/sibling/00446-hours.md:L38-L44` · heading *4. Mobile phones, alcohol and seat belts*

```
## 4. Mobile phones, alcohol and seat belts

4.1. No hand-held device while the vehicle is moving, telematics included.

4.2. Zero alcohol. A positive test ends the shift immediately.

4.3. Seat belts are worn by every occupant including yard moves.
```

## g059

> how many vials were in lot ROTA-9A on its own?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00100` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00200` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00500` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-01000` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/02-sensor-thresholds.yaml` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L13-L21` · heading *Summary*

```
## Summary

At approximately 02:16 on 12 March 2025, Kalpa probe KV-NGP-C2-07 began
reporting a high temperature in C2, the vaccine cold room at Nagpur DC. The
affected consignment was BharatVac order BV-4437, holding 18,400 vials of
rotavirus vaccine in lots ROTA-9A and ROTA-9B. The approved record showed the
room above +8.0 C for 66 minutes. At the time of the event, the SOP required a
QA call after 30 continuous minutes above +8.0 C for vaccines. The current
corrective action is to reduce that duration.
```

## g060

> what rest applies to a driver on a two week international run?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | weak | true | 1. `ext/sibling/00026-hours.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00200` | weak | true | 1. `ext/sibling/00026-hours.md`<br>2. `ext/sibling/00096-hours.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00500` | weak | true | 1. `ext/sibling/00446-hours.md`<br>2. `ext/sibling/00376-hours.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `ext/sibling/00236-hours.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00936-hours.md`<br>2. `ext/sibling/00446-hours.md`<br>3. `ext/sibling/00586-hours.md`<br>4. `ext/sibling/00866-hours.md`<br>5. `ext/sibling/00796-hours.md` |

**Answer passage** — `ext/sibling/00446-hours.md:L21-L27` · heading *2. Rest*

```
## 2. Rest

2.1. Daily rest is 11 continuous hours. Weekly rest is
48 hours.

2.2. Sleeping in a running reefer cab is permitted only at a lit plaza with the
handbrake engaged and the doors locked.
```

## g061

> what are the four dispositions


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/archive/a04-driver-hours-policy-2019.md`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00100` | weak | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `ext/filler/a17-beekeeping-minutes.md`<br>4. `ext/filler/00012-bee.md`<br>5. `ext/filler/00018-bee.md` |
| `rung-00200` | weak | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `ext/filler/00138-bee.md`<br>4. `ext/filler/00012-bee.md`<br>5. `ext/filler/00018-bee.md` |
| `rung-00500` | weak | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `ext/filler/00318-bee.md`<br>4. `ext/filler/00138-bee.md`<br>5. `ext/filler/00192-bee.md` |
| `rung-01000` | weak | true | 1. `seed/14-customer-notification-matrix-2025.md`<br>2. `ext/filler/00318-bee.md`<br>3. `ext/filler/00138-bee.md`<br>4. `ext/filler/00192-bee.md`<br>5. `ext/filler/00612-bee.md` |

**Answer passage** — `seed/14-customer-notification-matrix-2025.md:L25-L33` · heading *2. Wording*

```
## 2. Wording

2.1. The first notice says "temperature excursion under investigation" and
nothing more definite. No release, replacement credit, or insurance recovery may
be promised in the first notice.

2.2. The second notice, sent after disposition, names the disposition in the
four words the SOP uses: release, conditional release, hold pending external
decision, or destroy.
```

## g062

> a trip from july 2025 is being audited. whose temperature record counts?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00200` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00500` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-01000` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/sibling/00706-decision.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |

**Answer passage** — `seed/11-decision-telematics-vendor-2026.md:L18-L31` · heading *Telematics Vendor Decision 2026*

```
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
```

## g063

> who do i call at night in nagpur and who is the escalation group for patient critical stock?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00100` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00200` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00500` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |

**Answer passage** — `seed/10-new-joiner-faq.md:L20-L25` · heading *Who do I call for a temperature alarm?*

```
## Who do I call for a temperature alarm?

In daytime, call QA desk extension 440. At night in Nagpur, call Bunty or the
shift lead on extension 228, then Fleet Control if a truck is moving. For
patient-critical pharma, Compliance-Red is the escalation group after the 2025
drill. Please do not use the old qa-shared mailbox for urgent alarms.
```

## g064

> a lorry carrying chilled milk turns up very late. what happens to its booking?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/00039-sop.md`<br>3. `ext/archive/00045-quarantine-retired.md`<br>4. `ext/sibling/00013-dockwiki.html`<br>5. `ext/sibling/00040-dockwiki.html` |
| `rung-00200` | partial | true | 1. `ext/sibling/00099-sop.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/00039-sop.md`<br>4. `ext/archive/00045-quarantine-retired.md`<br>5. `ext/archive/00075-decision-retired.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/00099-sop.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/00266-sop.md`<br>4. `ext/sibling/00039-sop.md`<br>5. `ext/sibling/00393-sop.md` |
| `rung-01000` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/00099-sop.md`<br>3. `ext/sibling/00746-quarantine.md`<br>4. `ext/sibling/00873-sop.md`<br>5. `ext/sibling/00266-sop.md` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p9` · heading *Late arrivals*

```
## Late arrivals

Late arrival goes to holding lane B, call shift lead, no automatic cancellation. If the slot is pharma critical, the shift lead must also check whether a red sleeve is ready before moving the vehicle to dock 4.

This paragraph was copied from the old Nagpur page and may conflict with Dockwise automatic rules. Farhan kept it because drivers understand holding lane B better than a cancelled booking message.
```

## g065

> which sensor ids cover the nagpur rooms, and who may change what they trigger on?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00200` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00500` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-01000` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |

**Answer passage** — `seed/01-sop-temperature-excursion.md:L189-L203` · heading *9. Sensor problems*

```
## 9. Sensor problems

9.1. If a sensor is suspected to be wrong, staff shall place a calibrated spare
logger next to the product, keep the original sensor in place, and call the DC
manager. Removing or covering the original sensor is prohibited.

9.2. A Tessaline alarm may be acknowledged in the application after containment
has started. Acknowledging an alarm is not the same as closing an excursion.

9.3. A truck or room with repeated false alarms must be marked for maintenance,
but the temperature record remains part of the investigation until QA rejects it
in writing.

9.4. Sensor configuration changes must be requested through QA and IT together.
No DC staff may change threshold values directly in Tessaline.
```

## g066

> where do damaged goods wait while somebody decides what happens to them?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `ext/filler/a15-release-notes-tilecutter.md`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00005-decision-retired.md`<br>4. `ext/archive/00015-ratecard-retired.md`<br>5. `ext/archive/00045-quarantine-retired.md` |
| `rung-00200` | partial | true | 1. `ext/filler/a15-release-notes-tilecutter.md`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00085-ratecard-retired.md`<br>4. `ext/archive/00005-decision-retired.md`<br>5. `ext/archive/00105-notification-retired.md` |
| `rung-00500` | partial | true | 1. `ext/filler/a15-release-notes-tilecutter.md`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00245-notification-retired.md`<br>4. `ext/archive/00455-notification-retired.md`<br>5. `ext/archive/00435-ratecard-retired.md` |
| `rung-01000` | partial | true | 1. `ext/filler/a15-release-notes-tilecutter.md`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00625-postmortem-retired.md`<br>4. `ext/archive/00485-postmortem-retired.md`<br>5. `ext/archive/00245-notification-retired.md` |

**Answer passage** — `ext/archive/00035-notification-retired.md:L32-L36` · heading *Do not use this document to*

```
## Do not use this document to

- decide a disposition today;
- quote a rate;
- answer a customer question about the current rule.
```

## g067

> quarantine bay at guwahati


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00100` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `ext/archive/00045-quarantine-retired.md`<br>3. `ext/sibling/00046-quarantine.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00200` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `ext/archive/00045-quarantine-retired.md`<br>3. `ext/archive/00115-quarantine-retired.md`<br>4. `ext/sibling/00046-quarantine.md`<br>5. `ext/sibling/00116-quarantine.md` |
| `rung-00500` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/archive/00255-quarantine-retired.md`<br>5. `ext/archive/00045-quarantine-retired.md` |
| `rung-01000` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `ext/archive/00255-quarantine-retired.md` |

**Answer passage** — `seed/02-sensor-thresholds.yaml#p5` · heading *guwahati_dc*

```
## guwahati_dc

**aliases**

- Guwahati DC

- GHY

**rooms**

**G-COLD-1**

**product:** vaccines

**low_celsius:** 2.0

**high_celsius:** 8.0

**quarantine_bay:** Q-G2

**G-DAIRY-2**

**product:** milk

**low_celsius:** 0.0

**high_celsius:** 5.0
```

## g068

> how long can pharma pallets sit on an open dock


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00100` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00200` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00500` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-01000` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |

**Answer passage** — `seed/01-sop-temperature-excursion.md:L170-L187` · heading *8. Dock and staging rules*

```
## 8. Dock and staging rules

8.1. A dock is not a temperature-controlled room. Staging time begins when the
pallet crosses the cold-room threshold and ends when the reefer body is closed
or the pallet returns to the cold room.

8.2. Pharma pallets may not be staged on an open dock for more than 10 minutes
unless a validated passive shipper is used.

8.3. Dairy pallets may be staged on a covered dock for loading, but the dairy
high-excursion rule in clause 2.3 still applies. Staff shall not reclassify
staging time as "not cold chain time" after the fact.

8.4. Frozen stock must move directly between freezer and reefer body. Any delay
longer than 8 minutes must be called to the shift lead.

8.5. The dock team may request a slot change, but it may not waive a temperature
limit. Only QA may decide whether an excursion occurred.
```

## g069

> add up what the tessaline move cost us one way or another


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00200` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00500` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-01000` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |

**Answer passage** — `seed/05-decision-telematics-vendor-2023.md:L9-L21` · heading *Context*

```
## Context

Quillfern operates owned reefers, hired peak-season reefers, cold-room probes,
and dock sensors. The current vendor, Kalpa Fleet Systems, has been in use since
2014. The 2023 contract expires on 31 December 2023. Finance asked whether we
should renew Kalpa, move to Tessaline Telematics, or buy a mixed package with
truck devices from one supplier and warehouse sensors from another.

The operating requirement is simple: Fleet Control must see truck location,
temperature, door status, and alert history without calling the driver. QA must
retrieve a trip or room report during an investigation. The vendor must support
Nagpur as central hub, Guwahati and Coimbatore as smaller DCs, and hired trucks
during vaccine and dairy peak months.
```

## g070

> before the vendor switch, how often did the trackers report a reading


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00200` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00500` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-01000` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/10-new-joiner-faq.md` |

**Answer passage** — `seed/11-decision-telematics-vendor-2026.md:L69-L79` · heading *Consequences*

```
## Consequences

IT retires the Kalpa export script on 30 April 2026. The Kalpa tablet in the
Nagpur guard cabin is a read-only audit device and must not be used to open
alarms. Training material and the QA audit binder are reissued with Tessaline
screenshots before the 2026 vaccine season.

Fleet continues to keep paper driver call logs. That practice survived the
vendor change because network coverage, not the vendor, was the reason for it.

Sandhu's closing comment: "THE DASHBOARD CHANGED; THE DISCIPLINE DOES NOT."
```

## g071

> how warm can milk crates get on a covered dock before QA has to be told?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/00039-sop.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00200` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/00039-sop.md`<br>3. `ext/sibling/00099-sop.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00500` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `ext/sibling/00266-sop.md`<br>5. `ext/sibling/00039-sop.md` |
| `rung-01000` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/01-sop-temperature-excursion.md` |

**Answer passage** — `seed/archive/a01-sop-temperature-excursion-rev2.md:L21-L36` · heading *2. Products and limits*

```
## 2. Products and limits

2.1. Vaccines must remain between +2.0 C and +8.0 C. A vaccine high excursion is
declared when any approved sensor records more than +8.0 C for 30 continuous
minutes.

2.2. Insulin must remain between +2.0 C and +8.0 C. An insulin high excursion is
declared when the approved record is more than +8.0 C for 20 continuous minutes.

2.3. Milk and paneer must remain from 0.0 C to +4.0 C in cold rooms and reefer
bodies. Milk crates may remain on a covered dock until +7.0 C for 45 minutes
before QA notice is required.

2.4. Frozen food must remain at or below -18.0 C. A frozen-food excursion is
declared when the approved record is warmer than -12.0 C for 30 continuous
minutes.
```

## g072

> the old wiki page gave pharma arrivals how long?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00100` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/sibling/00013-dockwiki.html`<br>4. `ext/sibling/00040-dockwiki.html`<br>5. `ext/sibling/00019-dockwiki.html` |
| `rung-00200` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/sibling/00100-dockwiki.html`<br>4. `ext/sibling/00139-dockwiki.html`<br>5. `ext/sibling/00013-dockwiki.html` |
| `rung-00500` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/sibling/00379-dockwiki.html`<br>4. `ext/sibling/00100-dockwiki.html`<br>5. `ext/sibling/00139-dockwiki.html` |
| `rung-01000` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/sibling/00379-dockwiki.html`<br>4. `ext/sibling/00859-dockwiki.html`<br>5. `ext/sibling/00700-dockwiki.html` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p9` · heading *Late arrivals*

```
## Late arrivals

Late arrival goes to holding lane B, call shift lead, no automatic cancellation. If the slot is pharma critical, the shift lead must also check whether a red sleeve is ready before moving the vehicle to dock 4.

This paragraph was copied from the old Nagpur page and may conflict with Dockwise automatic rules. Farhan kept it because drivers understand holding lane B better than a cancelled booking message.
```

## g073

> what do we actually pay per truck per month, and what was the number that turned out to be wrong?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00100` | weak | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/adjacent/a14-sundari-onboarding.html`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/adjacent/a14-sundari-onboarding.html`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00500` | weak | true | 1. `ext/adjacent/a14-sundari-onboarding.html`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-01000` | weak | true | 1. `ext/adjacent/a14-sundari-onboarding.html`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `ext/archive/a19-norvell-telematics-decision-2022.md` |

**Answer passage** — `ext/sibling/a04-okapi-night-handover.txt:L1-L46` · heading *—*

```
MYSURU NIGHT SHIFT HANDOVER LOG — OKAPI FROZEN LOGISTICS
Shift lead: Tanmay Joshi
Night of 2026-05-11 into 2026-05-12
Register: OKF-NIGHT-REG-7

21:40  Handover taken from evening shift. 11 reefers on yard, 2 hired.
       Two pallets still on hold in OKF-Q3 from Saturday, paperwork with Quality.

22:05  Room OKF-F2 (ice cream) alarm, -17.4 C against a -20.0 C target.
       Placed spare logger next to the stock. Original sensor LEFT IN PLACE.
       Called Leela Nambiar. She said watch for 20 min before calling Quality.

22:31  Recovered to -20.6 C. Duration 26 min, which is over our 15 min rule for
       the hardening room, so I opened a quality event anyway. OKF-F-11 number
       is 2026-0214.

23:15  Truck OKF-482 door-open event on the Hunsur road. Driver says he stopped
       for the toll queue and the seal is intact. Told him NOT to touch the
       telematics unit while moving. He parked at the plaza and called back.

00:20  Dock 3 leveller sticking again. Third time this month. Raised with the
       workshop, they will look at it Wednesday. Dairy loads moved to dock 2.

01:05  Guard cabin tablet lost network for 40 min. Wrote readings by hand in the
       register as per the procedure. IT ticket OKF-IT-3391.

02:50  Ammonia plant defrost check ran late because the fitter was on the other
       site. No unloading 02:50 to 03:25.

04:10  Quality called back on 2026
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g074

> what code does fleet control log an exception under


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00100` | grounded | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |
| `rung-00200` | grounded | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `ext/sibling/00026-hours.md` |
| `rung-00500` | weak | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `ext/sibling/00446-hours.md`<br>5. `ext/sibling/00376-hours.md` |
| `rung-01000` | weak | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `ext/sibling/00936-hours.md` |

**Answer passage** — `seed/08-driver-hours-and-safety-policy.md:L58-L75` · heading *3. Exceptions*

```
## 3. Exceptions

3.1. If weather, police stoppage, road closure, civil disturbance, vehicle
breakdown, medical emergency, or a safety threat would cause a driver to exceed
a limit, the driver must stop at the nearest lit fuel plaza, toll rest area,
police post, customer secure yard, or Quillfern DC.

3.2. Fleet Control shall log the exception under code SANDHU-EXC with the time,
place, reason, stock type, driver statement, and revised plan. The exception is
not closed until a rest plan is recorded.

3.3. A cold-chain emergency is not by itself a driving-hours exception. The
correct response is to secure the vehicle, protect the product, and arrange a
replacement driver, mobile service, or customer-approved transfer.

3.4. Managers shall not instruct a driver to "push through", "make up time", or
"just reach the next DC" after the legal or Quillfern limit is reached. Such an
instruction is misconduct even when no crash occurs.
```

## g075

> what did it cost to get out of kalpa early


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00200` | weak | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00500` | weak | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-01000` | weak | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p2` · heading *Nagpur DC / NGP hub*

```
## Nagpur DC / NGP hub

Book Nagpur slots in Dockwise before 16:00 on the previous day. Pharma uses dock 4, dairy uses docks 1 and 2, and frozen food uses dock 5. The old Kalpa slot sync link on the left is broken and should not be used for new bookings.

No unloading is planned between 13:10 and 13:40 because the ammonia plant runs the daily defrost check. Late arrival goes to holding lane B, call shift lead, no automatic cancellation.

Pharma arrivals get 15 minutes grace. Dairy arrivals get 20 minutes grace. Frozen arrivals get 10 minutes grace because the freezer-to-reefer movement is shorter and more sensitive.
```

## g076

> RF-118's display was jumping about. did the night team handle it properly?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/filler/00042-chess.md`<br>5. `ext/filler/00048-chess.md` |
| `rung-00200` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `ext/filler/00108-chess.md`<br>4. `ext/filler/00042-chess.md`<br>5. `ext/filler/00102-chess.md` |
| `rung-00500` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/filler/00288-chess.md`<br>5. `ext/filler/00348-chess.md` |
| `rung-01000` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `ext/filler/00528-chess.md`<br>5. `ext/filler/00288-chess.md` |

**Answer passage** — `seed/04-night-shift-handover-log.txt:L1-L35` · heading *—*

```
Nagpur DC night handover log
kept at security desk copy, typed from WhatsApp + notebook. spelling not fixed.

2025-09-17 / Bunty
f1 freezer door gasket sweating again. frozen peas from Mangal Foods moved from rack F1-A to F1-B at 01:20 because left side had ice fog and floor wet. temp display said -17.4 then -18.2 after unit defrost. told Prakash maint to check morning. no customer issue yet. reefer RF-203 came 25 min late, driver said ring road jam. dock 5 still took him because frozen queue empty.

2025-10-05 / Bunty
manjara milk crates waiting lane 2 at 6.2 C for 38 mins while dock 1 blocked by empty crate return. i told Farhan sir on phone. he said count as staging, not excursion, because crates were not handed to QA yet. writing here only so day shift knows. please check with madam because SOP is confusing on milk. same night Tessaline alarm was not showing for lane sensor, only room D1.

2025-10-18 / Saira
two hired trucks came without red sleeve packets. guard sent them inside because rain heavy. i made red tags from old labels and kept seal tape in office drawer. one packet short for BharatVac sample return. ask stores for proper sleeves. driver on RF-118 asked what Compliance-Red means. new boys don't know all these groups.

2025-11-02 / Bunty
kalpa old tablet still in guard cabin. IT said keep for past trips only. do not send tablet photo to customer unless QA asks. T
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g077

> what was the write off amount for the vaccine excursion


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00100` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00200` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/sibling/00126-sop.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00500` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/00346-postmortem.md`<br>3. `ext/sibling/00276-postmortem.md`<br>4. `ext/sibling/00283-postmortem.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/00550-postmortem.md`<br>3. `ext/sibling/00346-postmortem.md`<br>4. `ext/sibling/00276-postmortem.md`<br>5. `ext/sibling/00529-postmortem.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L1-L11` · heading *Postmortem: Nagpur vaccine excursion, March 2025*

```
---
docname: Nagpur rotavirus cold-room excursion
authr: Revathi Iyer
date_seen: 12/03/25
statuss: rushed-review

# Postmortem: Nagpur vaccine excursion, March 2025

This note was written on the afternoon of 12 March 2025 after the C2 cold room
temperature event at Nagpur DC. I am recording the timeline while memories are
fresh. Spelling and header cleanup can wait; evidence cannot.
```

## g078

> what must nobody do to a probe just to make the display look normal?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00039-sop.md`<br>4. `ext/sibling/00000-sop.md`<br>5. `ext/sibling/00056-sop.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00060-sop.md`<br>4. `ext/sibling/00120-sop.md`<br>5. `ext/sibling/00126-sop.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00219-sop.md`<br>3. `ext/sibling/00046-quarantine.md`<br>4. `ext/sibling/00300-sop.md`<br>5. `ext/sibling/00406-sop.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00033-sop.md`<br>2. `ext/sibling/00219-sop.md`<br>3. `ext/sibling/00933-sop.md`<br>4. `ext/sibling/00046-quarantine.md`<br>5. `ext/sibling/00300-sop.md` |

**Answer passage** — `ext/sibling/00219-sop.md:L43-L51` · heading *4. Immediate containment*

```
## 4. Immediate containment

4.1. Stop movement of the affected pallet, crate, reefer body or room bay.

4.2. Photograph the sensor display, seal number, dock clock and pallet labels
before anyone debates disposition. Truck CDM-841 carries a spare logger bin.

4.3. Do not warm, chill, ventilate or shield the probe to make a display look
normal.
```

## g079

> final PO number for the tessaline deal


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-01000` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/01-sop-temperature-excursion.md` |

**Answer passage** — `seed/06-re-fw-telematics-cutover.eml#p1` · heading *FW: telematics cutover - revised freeze*

```
We commit to exception_csv_v2 from day one, 60-second polling, door-open alerts,
and no extra charge for API access. I am confident we can still complete all
sites close to the original date, but I accept Farhan's pilot-first sequence.

Tom��s

-----Original Message-----
From: Farhan Qureshi <farhan.qureshi@quillfern.example>
Sent: Tuesday, August 19, 2025 07:35
To: Revathi Iyer <revathi.iyer@quillfern.example>; Col. H. S. Sandhu <hs.sandhu@quillfern.example>; Anjali Deshmukh <anjali.deshmukh@quillfern.example>
Subject: Re: telematics cutover - revised freeze

Pilot live since 18 August in Nagpur. C2 Tessaline sensor TSL-NGP-C2-07 is
within 0.3 C of the USB logger. RF-118 install done, but driver training needs
one more night shift. Guwahati is not ready and Coimbatore wants south-gate
slots first.

Please do not cite 15 September as the cutover date. The working date remains
07 October for Nagpur, later for the other DCs.

Farhan

-----Original Message-----
From: Anjali Deshmukh <anjali.deshmukh@quillfern.example>
Sent: Monday, September 8, 2025 16:52
To: Col. H. S. Sandhu <hs.sandhu@quillfern.example>; Farhan Qureshi <farhan.qureshi@quillfern.example>; "Tom��s Reyes" <tomas.reyes@tessaline.example>
Subject: Re: telematics cutover - revised freeze

Final PO QF-FY26-TSL-044 is raised. Commercial control numbers are Rs. 24.60
lakh one-time onboarding, Rs. 812 per active truck pe
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g080

> back in the kalpa days, where did a cold room alarm actually land?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a05-induction-checklist-2020.txt`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00200` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00500` | grounded | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-01000` | grounded | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/archive/a05-induction-checklist-2020.txt`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |

**Answer passage** — `seed/archive/a05-induction-checklist-2020.txt:L1-L27` · heading *—*

```
Quillfern Cold Logistics - new joiner induction checklist
Version 3, June 2020. Retired 2024. Kept in the archive because HR audits ask for it.

Day 1
 [ ] gate photo and temporary pass
 [ ] licence, PAN card copy, bank details, two photos
 [ ] sign the 2019 driver hours acknowledgement
 [ ] Kalpa Fleet Systems app installed on the depot tablet
 [ ] learn the KLP trip number format, you will write it on every audit packet
 [ ] shown the qa-shared mailbox, this is where every temperature alarm lands

Day 2
 [ ] cold room walkthrough, C2 vaccines, C3 insulin, D1 milk, F1 frozen
 [ ] red sleeve packet contents, ask Stores if a packet is short
 [ ] dock desk email booking, before 18:00 previous day
 [ ] paper dock board is the truth, the wiki page is a copy

Day 3
 [ ] ride along on a Nagpur city dairy route
 [ ] hand-held probe use and calibration sticker check
 [ ] escalation is night lead, then DC manager, then QA in the morning
 [ ] there is no separate pharma escalation group

Notes for the HR file
 - Induction is three days for drivers and two days for office staff.
 - New joiners are not rostered on night shift in the first 30 days.
 - This checklist does not cover Guwahati or Coimbatore; those sites run their own.
```

## g081

> what do i need to bring on my first day


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00100` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `ext/adjacent/a14-sundari-onboarding.html`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/sibling/a05-norvell-telematics-decision-2026.md` |
| `rung-00200` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `ext/adjacent/a14-sundari-onboarding.html`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md` |
| `rung-00500` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `ext/adjacent/a14-sundari-onboarding.html`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md` |
| `rung-01000` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `ext/adjacent/a14-sundari-onboarding.html`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `seed/04-night-shift-handover-log.txt` |

**Answer passage** — `seed/10-new-joiner-faq.md:L44-L52` · heading *First day driver checklist*

```
## First day driver checklist

Bring licence, Aadhaar copy, bank details, two photos, and any vendor letter if
you are hired-truck staff. At the gate you sign the safety acknowledgement, get
the dispatch note, confirm seal numbers, and check whether the load is pharma,
dairy, frozen, or dry grocery.

Never troubleshoot a telematics device while driving. Park first. If a manager
says "just reach", call Fleet Control and ask them to record the instruction.
```

## g082

> there is a trick in the handover log for staging alarms. is it allowed?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00100` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/a01-marrowbeck-excursion-sop.md` |
| `rung-00200` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/a01-marrowbeck-excursion-sop.md` |
| `rung-00500` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |
| `rung-01000` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/01-sop-temperature-excursion.md` |

**Answer passage** — `seed/04-night-shift-handover-log.txt:L1-L35` · heading *—*

```
Nagpur DC night handover log
kept at security desk copy, typed from WhatsApp + notebook. spelling not fixed.

2025-09-17 / Bunty
f1 freezer door gasket sweating again. frozen peas from Mangal Foods moved from rack F1-A to F1-B at 01:20 because left side had ice fog and floor wet. temp display said -17.4 then -18.2 after unit defrost. told Prakash maint to check morning. no customer issue yet. reefer RF-203 came 25 min late, driver said ring road jam. dock 5 still took him because frozen queue empty.

2025-10-05 / Bunty
manjara milk crates waiting lane 2 at 6.2 C for 38 mins while dock 1 blocked by empty crate return. i told Farhan sir on phone. he said count as staging, not excursion, because crates were not handed to QA yet. writing here only so day shift knows. please check with madam because SOP is confusing on milk. same night Tessaline alarm was not showing for lane sensor, only room D1.

2025-10-18 / Saira
two hired trucks came without red sleeve packets. guard sent them inside because rain heavy. i made red tags from old labels and kept seal tape in office drawer. one packet short for BharatVac sample return. ask stores for proper sleeves. driver on RF-118 asked what Compliance-Red means. new boys don't know all these groups.

2025-11-02 / Bunty
kalpa old tablet still in guard cabin. IT said keep for past trips only. do not send tablet photo to customer unless QA asks. T
… (truncated; full text in evidence/rung-01000/answers.jsonl)
```

## g083

> an auditor is asking what the diesel surcharge rule was on the 2024 card. what was it?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/07-rate-card-and-surcharges.md`<br>2. `seed/12-rate-card-2026-h2.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00100` | weak | true | 1. `seed/07-rate-card-and-surcharges.md`<br>2. `ext/archive/a20-braidwood-rate-card-2023.md`<br>3. `ext/archive/00015-ratecard-retired.md`<br>4. `seed/12-rate-card-2026-h2.md`<br>5. `ext/sibling/a06-braidwood-rate-card-2026.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00129-ratecard.md`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `ext/archive/a20-braidwood-rate-card-2023.md`<br>4. `ext/archive/00085-ratecard-retired.md`<br>5. `ext/archive/00015-ratecard-retired.md` |
| `rung-00500` | weak | true | 1. `ext/archive/00365-ratecard-retired.md`<br>2. `ext/sibling/00129-ratecard.md`<br>3. `ext/sibling/00296-ratecard.md`<br>4. `ext/sibling/00423-ratecard.md`<br>5. `ext/sibling/00369-ratecard.md` |
| `rung-01000` | weak | true | 1. `ext/archive/00365-ratecard-retired.md`<br>2. `ext/sibling/00129-ratecard.md`<br>3. `ext/sibling/00296-ratecard.md`<br>4. `ext/sibling/00926-ratecard.md`<br>5. `ext/sibling/00549-ratecard.md` |

**Answer passage** — `ext/archive/00365-ratecard-retired.md:L8-L11` · heading *Rate card and surcharges — Norvell (2022)*

```
# Rate card and surcharges — Norvell (2022)

> This edition is history. It is kept because auditors ask what the rule was at
> the time, and because customer annexes signed in 2022 still quote it.
```

## g084

> what makes frozen stock an excursion today?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/00049-postmortem.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `ext/sibling/00010-postmortem.md`<br>4. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>5. `ext/sibling/00043-postmortem.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00120-sop.md`<br>2. `ext/sibling/00049-postmortem.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `ext/sibling/00010-postmortem.md`<br>5. `ext/sibling/00130-postmortem.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00349-postmortem.md`<br>2. `ext/sibling/00430-postmortem.md`<br>3. `ext/sibling/00206-postmortem.md`<br>4. `ext/sibling/00403-postmortem.md`<br>5. `ext/sibling/00196-sop.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00349-postmortem.md`<br>2. `ext/sibling/00430-postmortem.md`<br>3. `ext/sibling/00463-postmortem.md`<br>4. `ext/sibling/00949-postmortem.md`<br>5. `ext/sibling/00206-postmortem.md` |

**Answer passage** — `ext/sibling/00349-postmortem.md:L8-L15` · heading *Summary*

```
# Post-incident review — Bilaspur frozen seafood excursion

## Summary

On the night in question, room CDM-D4 at the Cindermoor Distribution Bilaspur site held frozen seafood
above -18.0 C for 25 continuous minutes. The stock
was placed in quarantine bay CDM-Q1 and released only after the customer
returned a stability letter.
```

## g085

> how many vials were destroyed in the nagpur incident


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00100` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-00200` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>5. `ext/archive/00135-postmortem-retired.md` |
| `rung-00500` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-01000` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>5. `seed/01-sop-temperature-excursion.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L36-L47` · heading *Impact*

```
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
```

## g086

> night driving limit for one driver alone


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `seed/08-driver-hours-and-safety-policy.md`<br>2. `seed/archive/a04-driver-hours-policy-2019.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/filler/a18-bicycle-bench-notes.txt`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | weak | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `ext/filler/a18-bicycle-bench-notes.txt` |
| `rung-00500` | weak | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00446-hours.md`<br>4. `ext/sibling/00376-hours.md`<br>5. `ext/sibling/00026-hours.md` |
| `rung-01000` | weak | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/sibling/00936-hours.md`<br>4. `ext/sibling/00446-hours.md`<br>5. `ext/sibling/00586-hours.md` |

**Answer passage** — `seed/08-driver-hours-and-safety-policy.md:L30-L56` · heading *2. Daily limits*

```
## 2. Daily limits

2.1. No driver shall be planned for more than 12 hours on duty in a duty day.
The driving component inside that duty day shall not exceed 9 hours.

2.2. No driver shall drive for more than 4 hours and 30 minutes continuously
without a break of at least 30 minutes. Loading supervision does not count as
the break if the driver is responsible for vehicle movement or seal watching.

2.3. Night driving between 22:00 and 05:00 shall not exceed 6 hours for a
single-driver vehicle. A two-driver vehicle may cover the night segment only if
both drivers are named on the dispatch note before departure.

2.4. A minimum rest period of 11 consecutive hours is required between duty
days. Sleeping in the driver's seat while waiting for a dock is not counted as
the 11-hour rest unless Fleet Control has released the driver and the vehicle is
parked in a safe rest location.

2.5. Every driver must receive one 24-hour weekly rest period in each rolling
seven-day period. Fleet Control shall plan the rest, not discover the breach
after payroll.

2.6. Festival shuttle amendment (amended by Meera Krishnan on 10 June 2026):
for approved religious festival shuttle rosters only, rest may be split into
7 hours plus 4 hours inside the same 24-hour period, provided Fleet Control
approves before dispatch and the driver signs consent after being offered normal
rest.
```

## g087

> which lots were in the affected rotavirus consignment


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/01-sop-temperature-excursion.md` |
| `rung-00100` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00200` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00500` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00219-sop.md` |
| `rung-01000` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00219-sop.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L13-L21` · heading *Summary*

```
## Summary

At approximately 02:16 on 12 March 2025, Kalpa probe KV-NGP-C2-07 began
reporting a high temperature in C2, the vaccine cold room at Nagpur DC. The
affected consignment was BharatVac order BV-4437, holding 18,400 vials of
rotavirus vaccine in lots ROTA-9A and ROTA-9B. The approved record showed the
room above +8.0 C for 66 minutes. At the time of the event, the SOP required a
QA call after 30 continuous minutes above +8.0 C for vaccines. The current
corrective action is to reduce that duration.
```

## g088

> what grace period did the 2021 dock page give?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00100` | partial | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/00013-dockwiki.html`<br>4. `ext/sibling/00040-dockwiki.html`<br>5. `ext/sibling/00019-dockwiki.html` |
| `rung-00200` | partial | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/00100-dockwiki.html`<br>4. `ext/sibling/00139-dockwiki.html`<br>5. `ext/sibling/00013-dockwiki.html` |
| `rung-00500` | partial | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/00379-dockwiki.html`<br>4. `ext/sibling/00373-dockwiki.html`<br>5. `ext/sibling/00193-dockwiki.html` |
| `rung-01000` | partial | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/00379-dockwiki.html`<br>4. `ext/sibling/00859-dockwiki.html`<br>5. `ext/sibling/00700-dockwiki.html` |

**Answer passage** — `seed/archive/a03-dock-scheduling-wiki-2021.html#p0` · heading *Quillfern Wiki - Dock scheduling (2021 page)*

```
# Quillfern Wiki - Dock scheduling (2021 page)

Home | NGP Hub | Dock calendar | Kalpa slot sync | Edit this page
```

## g089

> who puts their signature on the letter that goes to the client when medicine stock is affected?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `ext/filler/00032-library.md` |
| `rung-00200` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `ext/filler/00158-library.md`<br>5. `ext/filler/00152-library.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/sibling/a08-sundari-notification-matrix.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/filler/00452-library.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/a08-sundari-notification-matrix.md`<br>5. `ext/filler/00638-library.md` |

**Answer passage** — `seed/01-sop-temperature-excursion.md:L109-L129` · heading *5. Notifications*

```
## 5. Notifications

5.1. Pharma critical stock means vaccines, insulin, and any medicine named by a
customer as patient critical. The customer must be notified within 2 hours of a
confirmed pharma critical excursion.

5.2. Dairy customers must be notified by the next scheduled customer service
check-in unless spoilage is visible, odour is present, or the temperature is
above +8.0 C. In those cases customer service must notify within 4 hours.

5.3. Frozen-food restaurant chains must receive an exception notice by the end of
the business day when the excursion is confirmed. If the vehicle is still on the
road, Fleet Control must also call the receiving kitchen.

5.4. Internal escalation for all pharma critical events goes to Compliance-Red,
the DC manager, Fleet Control if a truck is involved, and Finance if stock is
likely to be destroyed.

5.5. Customer notice must say "temperature excursion under investigation" until
QA approves a final wording. Staff must not promise release, replacement credit,
or insurance recovery in the first notice.
```

## g090

> how many people work at the guwahati DC?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00100` | grounded | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00200` | grounded | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-00500` | grounded | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/02-sensor-thresholds.yaml` |
| `rung-01000` | grounded | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/02-sensor-thresholds.yaml` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p3` · heading *Guwahati DC*

```
## Guwahati DC

Guwahati still assigns night slots by phone. Call Riniki Bora before 18:00 and write the slot on the guard register. Do not idle reefers inside the small yard after 21:30; neighbours complain and security closes the side gate. Rain cover is mandatory over rear pallets during monsoon unloading.
```

## g091

> tessaline sensor id for the C2 room


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00100` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00200` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00500` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-01000` | grounded | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/05-decision-telematics-vendor-2023.md` |

**Answer passage** — `seed/02-sensor-thresholds.yaml#p10` · heading *tessaline_mapping*

```
# tessaline_mapping

**pilot_live_date:** 2025-08-18

**api_export:** exception_csv_v2

**nagpur_room_C2_sensor:** TSL-NGP-C2-07

**nagpur_room_C3_sensor:** TSL-NGP-C3-02

**frozen_F1_sensor:** TSL-NGP-F1-04

**truck_RF_118_sensor:** TSL-RF-118-A

**truck_RF_221_sensor:** TSL-RF-221-A
```

## g092

> which SOP change came out of the march 2025 nagpur incident?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00100` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00200` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/sibling/00136-postmortem.md` |
| `rung-00500` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/sibling/00416-postmortem.md` |
| `rung-01000` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/02-sensor-thresholds.yaml` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L1-L11` · heading *Postmortem: Nagpur vaccine excursion, March 2025*

```
---
docname: Nagpur rotavirus cold-room excursion
authr: Revathi Iyer
date_seen: 12/03/25
statuss: rushed-review

# Postmortem: Nagpur vaccine excursion, March 2025

This note was written on the afternoon of 12 March 2025 after the C2 cold room
temperature event at Nagpur DC. I am recording the timeline while memories are
fresh. Spelling and header cleanup can wait; evidence cannot.
```

## g093

> how are guwahati slots booked these days?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00100` | weak | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00200` | weak | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-00500` | weak | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-01000` | weak | true | 1. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/04-night-shift-handover-log.txt` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p3` · heading *Guwahati DC*

```
## Guwahati DC

Guwahati still assigns night slots by phone. Call Riniki Bora before 18:00 and write the slot on the guard register. Do not idle reefers inside the small yard after 21:30; neighbours complain and security closes the side gate. Rain cover is mandatory over rear pallets during monsoon unloading.
```

## g094

> what is supposed to be inside the red sleeve


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00100` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00200` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-00500` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |
| `rung-01000` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a05-induction-checklist-2020.txt` |

**Answer passage** — `seed/10-new-joiner-faq.md:L13-L18` · heading *What is a red sleeve?*

```
## What is a red sleeve?

Red sleeve means the red plastic packet clipped to an excursion file or pharma
truck file. It should contain the customer intimation form, red hold tags, seal
tape, and one spare calibrated logger. If the packet is missing, ask Stores or
print the form and write RED SLEEVE MISSING.
```

## g095

> milk on a covered dock — is the 7 degree 45 minute rule still usable?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/archive/00045-quarantine-retired.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-00200` | partial | true | 1. `seed/04-night-shift-handover-log.txt`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/archive/00045-quarantine-retired.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-00500` | partial | true | 1. `ext/sibling/00429-ratecard.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `ext/archive/00045-quarantine-retired.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/00429-ratecard.md`<br>2. `ext/sibling/00716-ratecard.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `ext/sibling/00746-quarantine.md`<br>5. `ext/sibling/00886-quarantine.md` |

**Answer passage** — `ext/sibling/00716-ratecard.md:L29-L29` · heading *Surcharges*

```
| item | rule |
|---|---|
| After-hours dock wait | first 45 minutes free, then Rs. 545/hour |
```

## g096

> did the two-person night watch on C2 ever actually happen?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/adjacent/a11-petrichor-hr-leave.md`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |
| `rung-00200` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |
| `rung-00500` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |
| `rung-01000` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/11-decision-telematics-vendor-2026.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L70-L70` · heading *Actions*

```
| action | owner | due | status |
|---|---|---|---|
| Add two-person night watch for C2 during vaccine loading | Farhan Qureshi | 20 Mar 2025 | no follow-up evidence found |
```

## g097

> a quote is going out in august 2026. which rate card applies?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |
| `rung-00100` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `ext/sibling/a06-braidwood-rate-card-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `ext/sibling/00016-ratecard.md`<br>5. `ext/archive/a20-braidwood-rate-card-2023.md` |
| `rung-00200` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `ext/sibling/a06-braidwood-rate-card-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `ext/sibling/00016-ratecard.md`<br>5. `ext/sibling/00156-ratecard.md` |
| `rung-00500` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `ext/sibling/a06-braidwood-rate-card-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `ext/sibling/00450-ratecard.md`<br>5. `ext/sibling/00016-ratecard.md` |
| `rung-01000` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `ext/sibling/a06-braidwood-rate-card-2026.md`<br>3. `seed/07-rate-card-and-surcharges.md`<br>4. `ext/sibling/00450-ratecard.md`<br>5. `ext/sibling/00669-ratecard.md` |

**Answer passage** — `ext/sibling/a06-braidwood-rate-card-2026.md:L41-L48` · heading *Notes*

```
## Notes

* The 2023 card's footnote about a 5.50% diesel surcharge was never applied
  after 1 April 2026. Quote 8.00%.
* Dry-ice packing moved from Rs. 41 to Rs. 52 per kg because the Kanpur
  supplier revised its slab in February 2026.
* Two customers hold annex pricing and are not quoted from this card. Finance
  holds the list; do not guess from the customer name.
```

## g098

> how many people have to watch when medicine stock is written off?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00200` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `ext/sibling/a01-marrowbeck-excursion-sop.md` |
| `rung-00500` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `ext/sibling/a01-marrowbeck-excursion-sop.md` |
| `rung-01000` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L36-L47` · heading *Impact*

```
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
```

## g099

> which form does QA open the investigation in


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/15-customer-notification-matrix-2026.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-00200` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/15-customer-notification-matrix-2026.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00500` | weak | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `seed/15-customer-notification-matrix-2026.md`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-01000` | grounded | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/09-dock-scheduling-wiki-export.html`<br>4. `seed/15-customer-notification-matrix-2026.md`<br>5. `ext/sibling/a03-petrichor-postmortem-insulin.md` |

**Answer passage** — `seed/01-sop-temperature-excursion.md:L131-L152` · heading *6. Investigation record*

```
## 6. Investigation record

6.1. QA opens an investigation in QCL-F-17 before the end of the same shift. The
record must contain the sensor source, product owner, SKU, batch or lot number,
route, room, dock, seal number, driver name when applicable, and first staff
member who observed the event.

6.2. The investigator shall build a minute-level timeline from the approved
temperature record, door log, dock schedule, driver call log, maintenance ticket,
and shift handover note. Missing pieces must be listed as missing; do not fill
them with assumptions.

6.3. Where records conflict, use the source hierarchy in section 3 and explain
the conflict. A convenient record is not a better record.

6.4. For pharma critical stock, QA must ask the customer for a stability letter
before release when the product was above the high limit or below the low limit
for any confirmed duration.

6.5. The investigation shall name one of four dispositions: release, conditional
release, hold pending external decision, or destroy. Finance may record value
only after QA records the disposition.
```

## g100

> how fast must a vaccine customer be told, and which document sets that today?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | weak | true | 1. `ext/archive/00005-decision-retired.md`<br>2. `ext/sibling/00050-notification.md`<br>3. `ext/sibling/00023-notification.md`<br>4. `ext/sibling/00029-notification.md`<br>5. `ext/sibling/00036-notification.md` |
| `rung-00200` | weak | true | 1. `ext/archive/00005-decision-retired.md`<br>2. `ext/sibling/00143-notification.md`<br>3. `ext/sibling/00050-notification.md`<br>4. `ext/sibling/00023-notification.md`<br>5. `ext/sibling/00106-notification.md` |
| `rung-00500` | weak | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00453-sop.md`<br>4. `ext/sibling/00126-sop.md`<br>5. `ext/archive/00435-ratecard-retired.md` |
| `rung-01000` | weak | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `ext/archive/00945-notification-retired.md`<br>3. `ext/sibling/00046-quarantine.md`<br>4. `ext/sibling/00476-sop.md`<br>5. `ext/sibling/00819-sop.md` |

**Answer passage** — `ext/archive/00945-notification-retired.md:L32-L36` · heading *Do not use this document to*

```
## Do not use this document to

- decide a disposition today;
- quote a rate;
- answer a customer question about the current rule.
```

## g101

> who do i escalate to at each of the three DCs?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/archive/a05-induction-checklist-2020.txt`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | grounded | true | 1. `seed/archive/a05-induction-checklist-2020.txt`<br>2. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>5. `ext/sibling/a02-vantorix-sensor-thresholds.yaml` |
| `rung-00200` | grounded | true | 1. `seed/archive/a05-induction-checklist-2020.txt`<br>2. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>3. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00500` | weak | true | 1. `seed/archive/a05-induction-checklist-2020.txt`<br>2. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>3. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-01000` | weak | true | 1. `seed/archive/a05-induction-checklist-2020.txt`<br>2. `ext/sibling/a02-vantorix-sensor-thresholds.yaml`<br>3. `ext/sibling/a05-norvell-telematics-decision-2026.md`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |

**Answer passage** — `seed/archive/a05-induction-checklist-2020.txt:L1-L27` · heading *—*

```
Quillfern Cold Logistics - new joiner induction checklist
Version 3, June 2020. Retired 2024. Kept in the archive because HR audits ask for it.

Day 1
 [ ] gate photo and temporary pass
 [ ] licence, PAN card copy, bank details, two photos
 [ ] sign the 2019 driver hours acknowledgement
 [ ] Kalpa Fleet Systems app installed on the depot tablet
 [ ] learn the KLP trip number format, you will write it on every audit packet
 [ ] shown the qa-shared mailbox, this is where every temperature alarm lands

Day 2
 [ ] cold room walkthrough, C2 vaccines, C3 insulin, D1 milk, F1 frozen
 [ ] red sleeve packet contents, ask Stores if a packet is short
 [ ] dock desk email booking, before 18:00 previous day
 [ ] paper dock board is the truth, the wiki page is a copy

Day 3
 [ ] ride along on a Nagpur city dairy route
 [ ] hand-held probe use and calibration sticker check
 [ ] escalation is night lead, then DC manager, then QA in the morning
 [ ] there is no separate pharma escalation group

Notes for the HR file
 - Induction is three days for drivers and two days for office staff.
 - New joiners are not rostered on night shift in the first 30 days.
 - This checklist does not cover Guwahati or Coimbatore; those sites run their own.
```

## g102

> which amount must NOT be set off against the monthly telematics charges?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/06-re-fw-telematics-cutover.eml`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00053-decision.md`<br>3. `seed/05-decision-telematics-vendor-2023.md`<br>4. `ext/sibling/00020-decision.md`<br>5. `ext/sibling/00059-decision.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00080-decision.md`<br>3. `ext/sibling/00053-decision.md`<br>4. `ext/sibling/00140-decision.md`<br>5. `seed/05-decision-telematics-vendor-2023.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00080-decision.md`<br>3. `ext/sibling/00419-decision.md`<br>4. `ext/sibling/00200-decision.md`<br>5. `ext/sibling/00053-decision.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00953-decision.md`<br>3. `ext/sibling/00080-decision.md`<br>4. `ext/sibling/00419-decision.md`<br>5. `ext/sibling/00920-decision.md` |

**Answer passage** — `ext/sibling/00080-decision.md:L17-L24` · heading *Decision*

```
## Decision

Braidwood Temperature Control will move to Ostrelle Telematics for 48 months. The migration
and onboarding charge is Rs. 24.75 lakh. The
recurring charge is Rs. 941 per active truck per month and
Rs. 188 per fixed sensor per month.

No split-vendor model will be used. One support desk, one monthly export.
```

## g103

> paneer is at 5.5 C — excursion or not?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00100` | grounded | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `ext/sibling/00000-sop.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00116-quarantine.md`<br>2. `ext/sibling/00130-postmortem.md`<br>3. `ext/sibling/00103-postmortem.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00219-sop.md`<br>2. `ext/sibling/00406-sop.md`<br>3. `ext/sibling/00180-sop.md`<br>4. `ext/sibling/00310-postmortem.md`<br>5. `ext/sibling/00416-postmortem.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00639-sop.md`<br>2. `ext/sibling/00219-sop.md`<br>3. `ext/sibling/00406-sop.md`<br>4. `ext/sibling/00180-sop.md`<br>5. `ext/sibling/00840-sop.md` |

**Answer passage** — `ext/sibling/00639-sop.md:L22-L32` · heading *2. Products and limits*

```
## 2. Products and limits

2.1. Paneer must remain between +0.0 C and +5.0 C. A high
excursion is declared when an approved sensor records more than +5.0 C for
10 continuous minutes.

2.2. A low excursion is declared below +0.0 C for 5 continuous
minutes. Staging time on a covered dock counts towards both.

2.3. Room OKF-D5 is the paneer room at Hubballi. Quarantine bay OKF-Q5 receives any
stock placed on hold.
```

## g104

> how many pallets does the coimbatore quarantine bay hold?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | grounded | true | 1. `ext/sibling/00046-quarantine.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/00033-sop.md`<br>4. `ext/sibling/00039-sop.md`<br>5. `ext/sibling/00000-sop.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00046-quarantine.md`<br>2. `ext/sibling/00116-quarantine.md`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00060-sop.md` |
| `rung-00500` | weak | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00186-quarantine.md`<br>4. `ext/sibling/00396-quarantine.md`<br>5. `ext/sibling/00326-quarantine.md` |
| `rung-01000` | grounded | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00746-quarantine.md`<br>4. `ext/sibling/00186-quarantine.md`<br>5. `ext/sibling/00816-quarantine.md` |

**Answer passage** — `seed/13-dock-scheduling-rules-2026.md:L58-L63` · heading *4. Coimbatore DC*

```
## 4. Coimbatore DC

4.1. Use the south gate for reefers. Avoid Temple Street between 07:45 and 08:30.

4.2. Frozen loads are placed before lunch. Coimbatore joined Dockwise on
1 February 2026 with Guwahati.
```

## g105

> the qa-shared mailbox keeps coming up. who says use it and who says do not?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | weak | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00200` | grounded | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00500` | grounded | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-01000` | grounded | true | 1. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>2. `seed/10-new-joiner-faq.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |

**Answer passage** — `seed/10-new-joiner-faq.md:L20-L25` · heading *Who do I call for a temperature alarm?*

```
## Who do I call for a temperature alarm?

In daytime, call QA desk extension 440. At night in Nagpur, call Bunty or the
shift lead on extension 228, then Fleet Control if a truck is moving. For
patient-critical pharma, Compliance-Red is the escalation group after the 2025
drill. Please do not use the old qa-shared mailbox for urgent alarms.
```

## g106

> nobody picked up the phone at the client's end. what now?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/05-decision-telematics-vendor-2023.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `ext/adjacent/a10-vantorix-it-access.md`<br>4. `ext/sibling/00050-notification.md`<br>5. `ext/sibling/00023-notification.md` |
| `rung-00200` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `ext/sibling/00143-notification.md`<br>4. `ext/sibling/00050-notification.md`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |
| `rung-00500` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/adjacent/a10-vantorix-it-access.md`<br>5. `ext/sibling/00143-notification.md` |
| `rung-01000` | partial | true | 1. `ext/filler/a17-beekeeping-minutes.md`<br>2. `ext/sibling/a08-sundari-notification-matrix.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/filler/00028-release-notes.md`<br>5. `ext/filler/00442-release-notes.md` |

**Answer passage** — `ext/filler/a17-beekeeping-minutes.md:L18-L22` · heading *3. Swarm collection*

```
## 3. Swarm collection

The swarm list is open for the season. Members on the list are asked to keep a
spare nucleus box ready and to answer the phone; last year three calls went to
pest control because nobody on the list picked up.
```

## g107

> the SOP and the sensor file disagree on the vaccine high limit. which is right?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00039-sop.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00126-sop.md`<br>2. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/00033-sop.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00453-sop.md`<br>2. `ext/sibling/00126-sop.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00476-sop.md`<br>2. `ext/sibling/00819-sop.md`<br>3. `ext/sibling/00453-sop.md`<br>4. `ext/sibling/00546-sop.md`<br>5. `ext/sibling/00126-sop.md` |

**Answer passage** — `ext/sibling/00476-sop.md:L23-L33` · heading *2. Products and limits*

```
## 2. Products and limits

2.1. Vaccine must remain between +2.0 C and +8.0 C. A high
excursion is declared when an approved sensor records more than +8.0 C for
45 continuous minutes.

2.2. A low excursion is declared below +2.0 C for 8 continuous
minutes. Staging time on a covered dock counts towards both.

2.3. Room NRL-F4 is the vaccine room at Visakhapatnam. Quarantine bay NRL-Q6 receives any
stock placed on hold.
```

## g108

> what is the salary band for a night shift lead?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00500` | partial | true | 1. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/adjacent/a11-petrichor-hr-leave.md`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-01000` | partial | true | 1. `ext/adjacent/a11-petrichor-hr-leave.md`<br>2. `ext/sibling/a03-petrichor-postmortem-insulin.md`<br>3. `ext/sibling/a07-halberd-dock-wiki.html`<br>4. `ext/sibling/a04-okapi-night-handover.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |

**Answer passage** — `ext/adjacent/a11-petrichor-hr-leave.md:L34-L38` · heading *Night shift*

```
## Night shift

A night-shift worker who has worked a full night is not rostered onto the
following day shift. This is not a courtesy; it is the same reasoning as the
driver hours rule, and it is not waived for a slot.
```

## g109

> what did the 2023 vendor decision conclude, and on what numbers?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/archive/a03-dock-scheduling-wiki-2021.html` |
| `rung-00100` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/archive/00005-decision-retired.md`<br>4. `ext/archive/a19-norvell-telematics-decision-2022.md`<br>5. `ext/sibling/00006-decision.md` |
| `rung-00200` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `ext/archive/00005-decision-retired.md`<br>4. `ext/archive/00075-decision-retired.md`<br>5. `ext/archive/00145-decision-retired.md` |
| `rung-00500` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `ext/sibling/00200-decision.md`<br>3. `ext/sibling/00413-decision.md`<br>4. `ext/sibling/00353-decision.md`<br>5. `ext/archive/00285-decision-retired.md` |
| `rung-01000` | partial | true | 1. `seed/05-decision-telematics-vendor-2023.md`<br>2. `ext/sibling/00953-decision.md`<br>3. `ext/sibling/00200-decision.md`<br>4. `ext/sibling/00620-decision.md`<br>5. `ext/sibling/00500-decision.md` |

**Answer passage** — `seed/05-decision-telematics-vendor-2023.md:L1-L7` · heading *ADR: Telematics Vendor Decision 2023*

```
# ADR: Telematics Vendor Decision 2023

Status: Accepted

Date: 2023-11-28

Owners: Col. (retd.) H. S. Sandhu, IT Service Desk
```

## g110

> how long can they drive before a break is due


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | weak | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/00026-hours.md`<br>3. `seed/archive/a04-driver-hours-policy-2019.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `ext/adjacent/a14-sundari-onboarding.html` |
| `rung-00200` | weak | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/00026-hours.md`<br>3. `ext/sibling/00096-hours.md`<br>4. `seed/archive/a04-driver-hours-policy-2019.md`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00500` | grounded | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/00446-hours.md`<br>3. `ext/sibling/00376-hours.md`<br>4. `ext/sibling/00026-hours.md`<br>5. `ext/sibling/00096-hours.md` |
| `rung-01000` | grounded | true | 1. `ext/adjacent/a10-vantorix-it-access.md`<br>2. `ext/sibling/00936-hours.md`<br>3. `ext/sibling/00446-hours.md`<br>4. `ext/sibling/00586-hours.md`<br>5. `ext/sibling/00866-hours.md` |

**Answer passage** — `ext/sibling/00446-hours.md:L10-L19` · heading *1. Daily limits*

```
# Driver hours and safety policy — Vantorix

## 1. Daily limits

1.1. A driver may drive at most 8 hours in any period of
24 hours, extended to 11 hours no more than twice a week.

1.2. A break of at least 30 minutes is taken after
5 hours of driving. The break is not taken at a dock while
waiting for a slot.
```

## g111

> spoilage register number


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/15-customer-notification-matrix-2026.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/08-driver-hours-and-safety-policy.md`<br>5. `seed/archive/a04-driver-hours-policy-2019.md` |
| `rung-00100` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00005-decision-retired.md`<br>4. `ext/archive/00015-ratecard-retired.md`<br>5. `ext/archive/00045-quarantine-retired.md` |
| `rung-00200` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00085-ratecard-retired.md`<br>4. `ext/archive/00005-decision-retired.md`<br>5. `ext/archive/00105-notification-retired.md` |
| `rung-00500` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00245-notification-retired.md`<br>4. `ext/archive/00455-notification-retired.md`<br>5. `ext/archive/00435-ratecard-retired.md` |
| `rung-01000` | grounded | true | 1. `ext/sibling/a04-okapi-night-handover.txt`<br>2. `ext/archive/00035-notification-retired.md`<br>3. `ext/archive/00625-postmortem-retired.md`<br>4. `ext/archive/00485-postmortem-retired.md`<br>5. `ext/archive/00245-notification-retired.md` |

**Answer passage** — `ext/archive/00035-notification-retired.md:L13-L23` · heading *What this edition said*

```
## What this edition said

1. The Surat site booked slots by telephone and wrote them on the guard
   register. There was no calendar system.
2. The alarm threshold for the curd room was
   6.0 C for 51 continuous minutes —
   longer than the current edition allows.
3. Notification to patient-critical customers was "the same working day". The
   current edition states a number of hours instead.
4. Quarantine was a marked corner of the dispatch bay rather than a separate
   room with its own door log.
```

## g112

> somebody thinks a probe is lying. what are they meant to do with it?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>4. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00100` | partial | true | 1. `ext/filler/a15-release-notes-tilecutter.md`<br>2. `ext/adjacent/a14-sundari-onboarding.html`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00200` | partial | true | 1. `ext/adjacent/a14-sundari-onboarding.html`<br>2. `ext/filler/a15-release-notes-tilecutter.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00500` | partial | true | 1. `ext/adjacent/a14-sundari-onboarding.html`<br>2. `ext/filler/a15-release-notes-tilecutter.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |
| `rung-01000` | partial | true | 1. `ext/adjacent/a14-sundari-onboarding.html`<br>2. `ext/filler/a15-release-notes-tilecutter.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |

**Answer passage** — `ext/filler/a15-release-notes-tilecutter.md:L37-L40` · heading *Security*

```
### Security
- Dependency bump for a transitive parser advisory. No exploit path was found
  in Tilecutter itself; the bump is precautionary and is recorded because
  "precautionary" is a claim somebody will check.
```

## g113

> what penalty does tessaline pay if it misses an uptime target?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/08-driver-hours-and-safety-policy.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00100` | partial | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `ext/sibling/00049-postmortem.md` |
| `rung-00200` | partial | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00500` | partial | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-01000` | partial | true | 1. `seed/02-sensor-thresholds.yaml`<br>2. `seed/06-re-fw-telematics-cutover.eml`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |

**Answer passage** — `seed/04-night-shift-handover-log.txt:L37-L47` · heading *—*

```
2026-04-06 / Bunty
new SOP print came rev 4.2. front desk copy replaced. old paragraph about milk 7 C is still inside and everyone laughed because same SOP says 5 C. Farhan sir said follow 5 C, don't argue at 3 am. dairy coop complained about too many holds. i say fix dock 1 empty crate return first.

2026-04-18 / Mahesh
generator diesel 420 L at start of night, 310 L at end. power blink 23:40, freezer fine. guwahati truck GHY-7 reached without rain cover over rear pallets; told Riniki by phone. NGP hub and Nagpur DC same place for forms, new driver wrote two locations on challan and security rejected first copy.

2026-05-06 / Bunty
Tessaline export for RF-221 missing first 15 min after midnight. driver said network gone near Samruddhi tunnel. usb logger ok. QA told keep both files and write missing piece as missing, not guessed. restaurant frozen chicken at -16.2 for 14 min only, came back -18.4. no excursion as per Revathi on call.

2026-05-28 / Saira
night team short two people. dock 3 duplicated booking, Wiki still says late arrival goes holding lane B, call shift lead, no automatic cancellation. Dockwise says cancel after 20 min for dairy. Farhan said wiki old but useful for Guwahati phone numbers. please day shift update one source, we are tired.
```

## g114

> two documents give different times for the ammonia defrost. which two and what do they say?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/archive/a03-dock-scheduling-wiki-2021.html`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00100` | partial | true | 1. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-00200` | partial | true | 1. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>2. `seed/13-dock-scheduling-rules-2026.md`<br>3. `ext/sibling/a04-okapi-night-handover.txt`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-00500` | partial | true | 1. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | partial | true | 1. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>2. `ext/sibling/a04-okapi-night-handover.txt`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/01-sop-temperature-excursion.md` |

**Answer passage** — `ext/adjacent/a09-marrowbeck-ammonia-facilities.md:L9-L19` · heading *1. The defrost window*

```
# Facilities and ammonia plant maintenance — Marrowbeck

## 1. The defrost window

1.1. The daily defrost check runs at a fixed time and is **not** moved to suit a
dock booking. If the two collide, the booking moves. Facilities does not
negotiate this at the dock; the site manager decides it the day before or not
at all.

1.2. Bhopal runs 13:05 to 13:40. Indore runs 11:20 to 11:50. The two differ
because the Indore plant is smaller and the cross-dock has no storage.
```

## g115

> why did dry ice get more expensive?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/13-dock-scheduling-rules-2026.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/12-rate-card-2026-h2.md` |
| `rung-00100` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `ext/sibling/a07-halberd-dock-wiki.html` |
| `rung-00200` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>4. `ext/sibling/a07-halberd-dock-wiki.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00500` | grounded | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>4. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>5. `ext/adjacent/a10-vantorix-it-access.md` |
| `rung-01000` | weak | true | 1. `seed/09-dock-scheduling-wiki-export.html`<br>2. `ext/sibling/a07-halberd-dock-wiki.html`<br>3. `ext/adjacent/a10-vantorix-it-access.md`<br>4. `ext/adjacent/a13-halberd-insurance-claim.eml`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |

**Answer passage** — `seed/09-dock-scheduling-wiki-export.html#p2` · heading *Nagpur DC / NGP hub*

```
## Nagpur DC / NGP hub

Book Nagpur slots in Dockwise before 16:00 on the previous day. Pharma uses dock 4, dairy uses docks 1 and 2, and frozen food uses dock 5. The old Kalpa slot sync link on the left is broken and should not be used for new bookings.

No unloading is planned between 13:10 and 13:40 because the ammonia plant runs the daily defrost check. Late arrival goes to holding lane B, call shift lead, no automatic cancellation.

Pharma arrivals get 15 minutes grace. Dairy arrivals get 20 minutes grace. Frozen arrivals get 10 minutes grace because the freezer-to-reefer movement is shorter and more sensitive.
```

## g116

> was the night alert condition revathi asked for ever proved?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/06-re-fw-telematics-cutover.eml`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00100` | weak | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00200` | weak | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-00500` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/archive/a02-kalpa-alert-routing-guide-2021.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-01000` | weak | true | 1. `seed/03-postmortem-nagpur-vaccine-excursion.md`<br>2. `seed/11-decision-telematics-vendor-2026.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/archive/a02-kalpa-alert-routing-guide-2021.md` |

**Answer passage** — `seed/03-postmortem-nagpur-vaccine-excursion.md:L80-L85` · heading *Closing note*

```
## Closing note

This event is the reason I am asking for two changes: faster pharma escalation
and a shorter vaccine high-duration trigger. If the telematics vendor changes,
the first acceptance test must prove night alerts reach Compliance-Red, not only
the DC manager.
```

## g117

> i am quoting a new dairy contract this week. what diesel surcharge goes on it?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/06-re-fw-telematics-cutover.eml` |
| `rung-00100` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `ext/archive/a20-braidwood-rate-card-2023.md`<br>4. `ext/sibling/a06-braidwood-rate-card-2026.md`<br>5. `seed/10-new-joiner-faq.md` |
| `rung-00200` | weak | true | 1. `seed/12-rate-card-2026-h2.md`<br>2. `seed/07-rate-card-and-surcharges.md`<br>3. `ext/archive/a20-braidwood-rate-card-2023.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `ext/sibling/a06-braidwood-rate-card-2026.md` |
| `rung-00500` | weak | true | 1. `seed/07-rate-card-and-surcharges.md`<br>2. `seed/12-rate-card-2026-h2.md`<br>3. `ext/archive/a20-braidwood-rate-card-2023.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |
| `rung-01000` | weak | true | 1. `seed/07-rate-card-and-surcharges.md`<br>2. `seed/12-rate-card-2026-h2.md`<br>3. `ext/archive/a20-braidwood-rate-card-2023.md`<br>4. `seed/10-new-joiner-faq.md`<br>5. `seed/04-night-shift-handover-log.txt` |

**Answer passage** — `seed/07-rate-card-and-surcharges.md:L24-L31` · heading *Surcharges*

```
GST at 18% is charged on freight, surcharge, and wait time unless the customer
has a written exemption letter.

* Footnote A: From 1 June 2026, the diesel surcharge for standard contracts is
6.25% when HSD exceeds Rs. 92/litre. The table above was not updated before
this note was sent.
* Footnote B: BharatVac and Manjara Dairy use customer annex pricing; do not
quote this card without checking Finance.
```

## g118

> what is dockwise and why could the new joiners not open it?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/10-new-joiner-faq.md`<br>2. `seed/04-night-shift-handover-log.txt`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/09-dock-scheduling-wiki-export.html`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00200` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/archive/a05-induction-checklist-2020.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-00500` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |
| `rung-01000` | grounded | true | 1. `seed/10-new-joiner-faq.md`<br>2. `ext/adjacent/a10-vantorix-it-access.md`<br>3. `seed/archive/a05-induction-checklist-2020.txt`<br>4. `seed/04-night-shift-handover-log.txt`<br>5. `seed/09-dock-scheduling-wiki-export.html` |

**Answer passage** — `seed/10-new-joiner-faq.md:L1-L5` · heading *New joiner FAQ*

```
# New joiner FAQ

Welcome to Quillfern! This is the friendly version, not the legal one. If
Revathi madam and this page disagree, believe Revathi. If Colonel Sandhu and
this page disagree, please do not tell him this page existed 🙂
```

## g119

> when is frozen food an excursion


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `seed/14-customer-notification-matrix-2025.md`<br>4. `seed/15-customer-notification-matrix-2026.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00100` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>4. `seed/14-customer-notification-matrix-2025.md`<br>5. `seed/15-customer-notification-matrix-2026.md` |
| `rung-00200` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/01-sop-temperature-excursion.md`<br>3. `ext/sibling/00120-sop.md`<br>4. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00500` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `ext/sibling/00196-sop.md`<br>3. `ext/sibling/00459-sop.md`<br>4. `ext/sibling/00120-sop.md`<br>5. `ext/sibling/00213-sop.md` |
| `rung-01000` | weak | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `ext/sibling/00196-sop.md`<br>3. `ext/sibling/00459-sop.md`<br>4. `ext/sibling/00879-sop.md`<br>5. `ext/sibling/00120-sop.md` |

**Answer passage** — `seed/archive/a01-sop-temperature-excursion-rev2.md:L21-L36` · heading *2. Products and limits*

```
## 2. Products and limits

2.1. Vaccines must remain between +2.0 C and +8.0 C. A vaccine high excursion is
declared when any approved sensor records more than +8.0 C for 30 continuous
minutes.

2.2. Insulin must remain between +2.0 C and +8.0 C. An insulin high excursion is
declared when the approved record is more than +8.0 C for 20 continuous minutes.

2.3. Milk and paneer must remain from 0.0 C to +4.0 C in cold rooms and reefer
bodies. Milk crates may remain on a covered dock until +7.0 C for 45 minutes
before QA notice is required.

2.4. Frozen food must remain at or below -18.0 C. A frozen-food excursion is
declared when the approved record is warmer than -12.0 C for 30 continuous
minutes.
```

## g120

> what high limit does the sensor file give for paneer


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/02-sensor-thresholds.yaml`<br>4. `seed/11-decision-telematics-vendor-2026.md`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | partial | true | 1. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>2. `seed/02-sensor-thresholds.yaml`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/00116-quarantine.md`<br>2. `ext/sibling/00130-postmortem.md`<br>3. `ext/sibling/00103-postmortem.md`<br>4. `seed/02-sensor-thresholds.yaml`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/00219-sop.md`<br>2. `ext/sibling/00406-sop.md`<br>3. `ext/sibling/00180-sop.md`<br>4. `ext/sibling/00116-quarantine.md`<br>5. `ext/sibling/00416-postmortem.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/00219-sop.md`<br>2. `ext/sibling/00639-sop.md`<br>3. `ext/sibling/00406-sop.md`<br>4. `ext/sibling/00720-sop.md`<br>5. `ext/sibling/00180-sop.md` |

**Answer passage** — `ext/sibling/00219-sop.md:L22-L32` · heading *2. Products and limits*

```
## 2. Products and limits

2.1. Paneer must remain between +0.0 C and +5.0 C. A high
excursion is declared when an approved sensor records more than +5.0 C for
45 continuous minutes.

2.2. A low excursion is declared below +0.0 C for 20 continuous
minutes. Staging time on a covered dock counts towards both.

2.3. Room CDM-B2 is the paneer room at Bilaspur. Quarantine bay CDM-Q6 receives any
stock placed on hold.
```

## g121

> speed limit for a loaded reefer on the highway


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `seed/13-dock-scheduling-rules-2026.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00100` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/adjacent/a12-okapi-workshop.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/13-dock-scheduling-rules-2026.md` |
| `rung-00200` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/adjacent/a12-okapi-workshop.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `ext/sibling/00046-quarantine.md` |
| `rung-00500` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/adjacent/a12-okapi-workshop.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | grounded | true | 1. `seed/archive/a04-driver-hours-policy-2019.md`<br>2. `seed/08-driver-hours-and-safety-policy.md`<br>3. `ext/adjacent/a12-okapi-workshop.md`<br>4. `ext/adjacent/a14-sundari-onboarding.html`<br>5. `ext/sibling/00936-hours.md` |

**Answer passage** — `seed/archive/a04-driver-hours-policy-2019.md:L25-L28` · heading *2. Speed*

```
## 2. Speed

2.1. The maximum permitted speed for a loaded Quillfern reefer is 65 km/h on
open highway, 55 km/h in rain or fog, and 40 km/h on ghat roads.
```

## g122

> how long is the daily plant shutdown when nothing is taken off the lorries?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | partial | true | 1. `seed/13-dock-scheduling-rules-2026.md`<br>2. `seed/09-dock-scheduling-wiki-export.html`<br>3. `seed/15-customer-notification-matrix-2026.md`<br>4. `seed/archive/a04-driver-hours-policy-2019.md`<br>5. `seed/14-customer-notification-matrix-2025.md` |
| `rung-00100` | partial | true | 1. `ext/sibling/00026-hours.md`<br>2. `ext/adjacent/a12-okapi-workshop.md`<br>3. `ext/sibling/00010-postmortem.md`<br>4. `ext/sibling/00043-postmortem.md`<br>5. `ext/sibling/00049-postmortem.md` |
| `rung-00200` | partial | true | 1. `ext/sibling/00026-hours.md`<br>2. `ext/sibling/00096-hours.md`<br>3. `ext/adjacent/a12-okapi-workshop.md`<br>4. `ext/adjacent/a09-marrowbeck-ammonia-facilities.md`<br>5. `ext/sibling/00010-postmortem.md` |
| `rung-00500` | partial | true | 1. `ext/sibling/00446-hours.md`<br>2. `ext/sibling/00376-hours.md`<br>3. `ext/sibling/00026-hours.md`<br>4. `ext/sibling/00096-hours.md`<br>5. `ext/sibling/00236-hours.md` |
| `rung-01000` | partial | true | 1. `ext/sibling/00936-hours.md`<br>2. `ext/sibling/00446-hours.md`<br>3. `ext/sibling/00586-hours.md`<br>4. `ext/sibling/00866-hours.md`<br>5. `ext/sibling/00796-hours.md` |

**Answer passage** — `ext/sibling/00446-hours.md:L10-L19` · heading *1. Daily limits*

```
# Driver hours and safety policy — Vantorix

## 1. Daily limits

1.1. A driver may drive at most 8 hours in any period of
24 hours, extended to 11 hours no more than twice a week.

1.2. A break of at least 30 minutes is taken after
5 hours of driving. The break is not taken at a dock while
waiting for a slot.
```

## g123

> which telematics vendor are we on?


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | weak | true | 1. `seed/11-decision-telematics-vendor-2026.md`<br>2. `seed/05-decision-telematics-vendor-2023.md`<br>3. `seed/10-new-joiner-faq.md`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/08-driver-hours-and-safety-policy.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00053-decision.md`<br>3. `seed/11-decision-telematics-vendor-2026.md`<br>4. `ext/archive/00005-decision-retired.md`<br>5. `ext/sibling/00020-decision.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00080-decision.md`<br>3. `ext/sibling/00053-decision.md`<br>4. `ext/sibling/00140-decision.md`<br>5. `seed/11-decision-telematics-vendor-2026.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00080-decision.md`<br>3. `ext/sibling/00419-decision.md`<br>4. `ext/sibling/00200-decision.md`<br>5. `ext/sibling/00053-decision.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00006-decision.md`<br>2. `ext/sibling/00953-decision.md`<br>3. `ext/sibling/00080-decision.md`<br>4. `ext/sibling/00419-decision.md`<br>5. `ext/sibling/00920-decision.md` |

**Answer passage** — `ext/sibling/00080-decision.md:L1-L6` · heading *—*

```
---
title: Telematics vendor decision — Braidwood 2024
status: accepted
owner: Kavya Reddy
effective_date: 2024-05-21
---
```

## g124

> how many years do we keep the case file for vaccine stock


| rung | band | answerable | top 5 (ranked) |
|---|---|---|---|
| `rung-seed` | grounded | true | 1. `seed/01-sop-temperature-excursion.md`<br>2. `seed/archive/a01-sop-temperature-excursion-rev2.md`<br>3. `seed/04-night-shift-handover-log.txt`<br>4. `seed/06-re-fw-telematics-cutover.eml`<br>5. `seed/03-postmortem-nagpur-vaccine-excursion.md` |
| `rung-00100` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `seed/01-sop-temperature-excursion.md`<br>4. `ext/sibling/00033-sop.md`<br>5. `ext/sibling/00039-sop.md` |
| `rung-00200` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00126-sop.md`<br>4. `seed/01-sop-temperature-excursion.md`<br>5. `seed/archive/a01-sop-temperature-excursion-rev2.md` |
| `rung-00500` | weak | true | 1. `ext/sibling/a01-marrowbeck-excursion-sop.md`<br>2. `ext/sibling/00046-quarantine.md`<br>3. `ext/sibling/00453-sop.md`<br>4. `ext/sibling/00126-sop.md`<br>5. `seed/01-sop-temperature-excursion.md` |
| `rung-01000` | weak | true | 1. `ext/sibling/00046-quarantine.md`<br>2. `ext/sibling/00476-sop.md`<br>3. `ext/sibling/00819-sop.md`<br>4. `ext/sibling/00453-sop.md`<br>5. `ext/sibling/a01-marrowbeck-excursion-sop.md` |

**Answer passage** — `ext/sibling/00476-sop.md:L62-L67` · heading *6. Closure*

```
## 6. Closure

6.1. Quality closes the investigation and records one of release, conditional
release, hold, or destroy. Finance records value only afterwards.

6.2. The case file is kept for 7 years.
```
