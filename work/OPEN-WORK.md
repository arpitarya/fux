---
type: Queue
description: "The single live work queue, two lanes, plus the Blocked-on-Arpit inbox. The list only — its rules live in the record below."
governed_by: SR-WORK-OPEN-QUEUE
governed_by_path: records/0051_WORK-open-queue.md
---

# OPEN-WORK — what is still open

**This file is the LIST, plus the legend below** (Arpit, 2026-09-13).
Everything else — what the queue is, an item's lifecycle, the shape of a row,
ball precedence and the chain, ordering, how the inbox works, and what every
session owes — is stated once in
**[SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md)** and is not repeated
here. Read that record before changing anything below it.

**A ball on every row, always one:** 🔴 blocked on Arpit, directly or through another item · 🟣 gated on a named date, directly or through another item · 🟡 waiting on another item, named right after the id — `waits on **W-mm**`, or `**<project> W-mm**` for another project's · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (Arpit only). Full legend: [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rules 20–34.

---

## Blocked on Arpit

| what he decides | filed | age |
|---|---|---|
| 🔴 **W-289** — **5.0.0 released** 2026-10-25 (PyPI 19 names + npm 2). Left for you: **yank the 14 hand-uploaded 4.1.1 plugin files** on PyPI (they pin a fux-core 4.1.1 that never ships). [the item](open/W-289-plugin-packages.md) | 2026-10-20 | 5d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-258** — **on hold by his word** (2026-10-25, again): say when to run §1 (vanishing source, ~20 min) and §2 (a real 429). §3 parked as B-274. [the item](open/W-258-live-network-captures.md) | 2026-10-04 | 21d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🔴 **W-289** · `arpit` — plugin packages; **5.0.0 released 2026-10-25**, all 15 plugins on PyPI through CI. Left: Arpit yanks the 14 hand-uploaded 4.1.1 plugin files. Filed by Arpit (Cowork). [detail](open/W-289-plugin-packages.md)
- 🟢 **W-299** · `agent` — index packages: `kind = "index"` pin, segment-only digest, resolve/refuse in both runtimes, `runtime/pkg/`; step 0 writes SR-PKG-INDEX. **Opus.** Ratified, not built. Filed by Arpit (Cowork). [detail](open/W-299-index-package-pin.md)
- 🟡 **W-300** waits on **W-299** · `agent` — one query over repo + pinned segments: per-digest hashing, df/n summed, one `rank()`, foreign refused, `scope`; Python ≡ Node. **Opus.** Ratified, not built. Filed by Arpit (Cowork). [detail](open/W-300-merged-query-over-segments.md)
- 🟡 **W-301** waits on **W-299** · `agent` — `pkg:<docs-pkg>@<ver>#<path>` locations; `fux_passage` reads in place after `..`-collapse + containment; drift refused. **Opus.** Ratified, not built. Filed by Arpit (Cowork). [detail](open/W-301-pkg-locations-read-in-place.md)
- 🟢 **W-302** · `agent` — `fux pack <outdir>`: read-only verb emitting shards + identifiers.toml + manifest; refuses dirty/foreign/`url:`; author recipe. W-298 step 1 passed. **Sonnet.** Ratified, not built. Filed by Arpit (Cowork). [detail](open/W-302-fux-pack-publish-path.md)


### testing

- 🟢 **W-281** · `agent` — capture driver built (DoD 1–4, never run); DoD 5 (≤ 30 min, timed) owed by the next capture. **Sonnet.** Filed by Arpit (Claude Code). [detail](open/W-281-capture-harness-speed.md)
- 🔴 **W-258** · `arpit` — on hold by Arpit's word (2026-10-25): §1 (a source vanishes, ~20 min) and §2 (a real 429) run when he says; §3 parked as B-274. Checklist and bars written. Filed by Arpit (Cowork). [detail](open/W-258-live-network-captures.md)

### adr update


### research

- 🟢 **W-268** · `cowork` — ingest of 10 000 docs in under a second. Ruled S1 + P1 (2026-10-25); file the steps, step 0 (measure, **Sonnet**) first. **Cowork.** Filed by Arpit (Cowork). [detail](open/W-268-ingest-under-one-second.md)
- 🟢 **W-263** · `cowork` — research and propose the never-built `enriched` ingest mode: its overlap with `fux enrich`, and whether it may write index records itself. No code. **Opus.** Filed by Arpit (Cowork). [detail](open/W-263-enriched-mode-proposal.md)
- 🟢 **W-265** · `cowork` — deep research: how fux can better spot a question it cannot answer (the coverage floor tested no better than chance). No code. **Opus.** Filed by Arpit (Cowork). [detail](open/W-265-abstention-research.md)
- 🟢 **W-275** · `cowork` — is there a tool to tune `b`, `k1`, field weights, `section_weight` — or can one be built? Survey + proposal; train on retired sets, decide only via L13. No code. **Cowork.** Filed by Arpit (Cowork). [detail](open/W-275-ranking-tuner-research.md)
- 🟢 **W-280** · `cowork` — research: the intent cue lexicon tags 36 of 693 questions. Stronger cues, a yes/no doc type, or close until a consumer declares `[doctype]`; measurable under L13? **Cowork.** Filed by Arpit (Claude Code). [detail](open/W-280-intent-lexicon-research.md)

---
