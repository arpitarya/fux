---
title: "Probe calibration: terms and tolerances"
doc_id: QCL-QA-CAL-03
owner: Revathi Iyer
department: QA and Compliance
status: in_force
effective_date: 2025-09-16
---

# Probe calibration: terms and tolerances

## Terms

- **ice point** — 0.0 C, the temperature of a stirred slurry of crushed ice and potable water.
- **bench master** — the lab-certified logger kept in the QA calibration chamber at Nagpur, serial UL-M01, recertified every 12 months by Metrosure Labs.
- **drift** — the change in an instrument's error between two checks.
- **pass band** — the largest error an instrument may show and still be used.

## Instruments

| instrument | prefix | pass band | in-house check | external calibration |
|---|---|---|---|---|
| hand-held probe | HP- | ±0.5 C at the ice point | every 30 days | every 12 months |
| USB logger | UL- | ±0.3 C against the bench master | before red-sleeve issue, and every 90 days in stock | every 12 months |
| infrared gun | IR- | ±1.0 C | every 30 days | every 24 months |

An infrared gun reads a carton surface, not the product, and is never the
reading used to release stock.

## Sticker colours

- **green** — in date.
- **yellow** — check due within 7 days; the instrument may still be used.
- **red** — failed; out of use until QA clears it.

## Drift

A probe that drifts more than 0.3 C between two monthly checks goes for external calibration even if it passed both.

## Notes on the lab

Drift is normal in cheap probes and is the main reason the bench exists. Monthly
figures are kept on QCL-F-12 so that a trend can be seen. External labs issue
one certificate per instrument, which QA files against the prefix number. An
instrument that passed at the lab still needs its in-house check when it comes
back.
