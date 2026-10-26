---
type: Handoff
name: W-305
description: "Arpit's direction (2026-10-26): design the core engine to be built on Rust — the whole ingest path runs only in Rust and Python's ingest is replaced, not kept as a fallback. Research done in Cowork the same day; the proposal is work/proposals/rust-ingest-core.md. Eight forks (R1–R8) are Arpit's; once ruled, the six build steps are filed as their own items. Reverses W-268's F1 = S1 and F3 = P1."
item: W-305
filed: 2026-10-26
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-26
updated_by: "Cowork (Opus 5.5)"
ball: cowork
---

# W-305 — the ingest engine in Rust, Python's ingest replaced

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Map what today's Python ingest is made of, and what blocks a Rust-only one | ~15 000 lines on the path; four hazards no earlier doc named (the regex dialect, float repr, Unicode version, JSON share) | ✅ 2026-10-26 |
| 2 | Write the proposal: one Rust module behind PyO3, incremental from day one, Python decoders called back | [`rust-ingest-core.md`](../proposals/rust-ingest-core.md) | ✅ 2026-10-26 |
| 3 | Arpit closes the eight forks R1–R8 (proposal §4) | the design is decided | ✅ ruled 2026-10-26 — [compare doc](../compare/rust-ingest-core.compare.md) |
| 4 | Arpit creates the PyPI trusted publisher for `fux-native` (R8 = a) | wheels can be published from CI | ⏳ owed before the crate-and-wheels step publishes — filed with that step, not now |
| 5 | File the seven build steps (0–6) as their own items, each with its bar named before it runs; step 0 (measure on the Mac, Sonnet) first | work that can start | ⏳ next (Cowork) |

**Arpit, 2026-10-26 (Cowork):** *"Okay, the core engine. Let's design for it
to be built on Rust. And Python will be replaced by Rust. The whole ingest
part, which is slow today, would be only in Rust. Research, propose, create a
work item. Ask me if there are any blockers."*

**Status 2026-10-26: RULED the same session** — R1 = a (straight to Rust) ·
**R2/R3 = b (Python ingest KEPT as fallback and reference)** · R4 = a (text +
JSON native) · R5 = both analyzers, held equal · R6 = a (`fancy-regex`) · R7 = a
(runtime in Rust) · R8 = a (`fux-native`). Decision record:
[`rust-ingest-core.compare.md`](../compare/rust-ingest-core.compare.md). Next:
file the build steps. No code, no record change.

**The forks, in one line each** (detail and recommendations in the proposal §4):
**R1** incremental in Python first, or straight to Rust · **R2** Python ingest
deleted with a frozen byte oracle, kept as fallback, or deleted bare ·
**R3** a machine with no wheel: refused at install, or a fallback · **R4** which
decoders go native (recommended: text formats + JSON) · **R5** Rust as Python's
only analyzer, or writer-only · **R6** the PII/identifier/refusal regex dialect
(`fancy-regex`, a new dialect, or redaction left in Python) · **R7** the runtime
build in Rust or Python · **R8** a new `fux-native` distribution, or `fux-core`
goes platform-specific.

**Relation to W-268:** W-268 holds the goal (10 000 documents under a second)
and the measured clock; this item replaces its build plan. W-268 waits on this
item's rulings.

**Model:** **Cowork** (research, rule 37a). The build items it files name their
own models — Sonnet for steps 0–1, Opus for 2–6.

**Records it will update** (through its build items, not itself): SR-INGEST,
SR-DECODE, SR-PLUGINS, SR-PII, SR-RANKING, SR-T1-ACCELERATOR, SR-LAW-2,
SR-LAW-4, SR-WORK-RELEASE, and the layer map in `records/README.md`.

## Definition of done

1. The proposal filed with its sources — **done 2026-10-26**.
2. 🔴 Arpit closes R1–R8; the rulings are written into the proposal and a
   compare doc, and W-268's compare doc records that F1 and F3 were superseded.
3. The six build steps filed as W-items, step 0 first, each with its bar named
   before it runs; the proposal marked `graduated`; W-268 and this item
   archived with successors named.
