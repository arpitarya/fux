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

**A ball on every row, always one:** 🔴 blocked on Arpit, directly or through another item · 🟣 gated on a named date, directly or through another item · 🟡 waiting on another item · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (Arpit only). Full legend: [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rules 20–34.

---

## Blocked on Arpit

| what he decides | filed | age |
|---|---|---|
| 🔴 **W-258** — **on hold by his word** (2026-10-04): say when to run the live URL-source checks. Recommended: §1 vanishing source + §2 real 429; park §3. [the item](open/W-258-live-network-captures.md) | 2026-10-04 | 14d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-268** — ingest of 10 000 docs in under a second, in Rust (his direction; no consumer installs Rust). Pick the order and the no-wheel fallback — rec. Python incremental first; Python engine as fallback. [the item](open/W-268-ingest-under-one-second.md) | 2026-10-10 | 8d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🟢 **W-288** · `agent` — decoder extensions: versioned shared modules under the decoders, in the reuse key; W-287's table module becomes `ext/table.py` first. **Opus.** Filed by Arpit (Cowork). [detail](open/W-288-decoder-extensions.md)
- 🟡 **W-289** · `agent` — plugin packages: only the engine is mandatory; 12 decoders, 2 fetchers, the table extension become opt-in packages declared in `.fux/plugins.toml`; L2 amended. After W-288. **Opus.** Filed by Arpit (Cowork). [detail](open/W-289-plugin-packages.md)

### testing

- 🟢 **W-281** · `agent` — capture and ladder speed: unsigned ladder commits (rung-10000 stalled 12 h on gpg); G1 and G3 in parallel; latency stays standalone. **Sonnet.** Filed by Arpit (Claude Code). [detail](open/W-281-capture-harness-speed.md)
- 🔴 **W-258** · `arpit` — one hands-on session on his machine: an answer whose source then vanishes, a real 429 from a real host, parallel CDP fetches in signed-in Chrome. Checklist and bars written. Filed by Arpit (Cowork). [detail](open/W-258-live-network-captures.md)

### adr update


### research

- 🔴 **W-268** · `cowork` — ingest of 10 000 docs in under a second. Proposal + compare doc filed; Rust is his direction. Arpit picks the order and the fallback. **Cowork.** Filed by Arpit (Cowork). [detail](open/W-268-ingest-under-one-second.md)
- 🟢 **W-263** · `cowork` — research and propose the never-built `enriched` ingest mode: its overlap with `fux enrich`, and whether it may write index records itself. No code. **Opus.** Filed by Arpit (Cowork). [detail](open/W-263-enriched-mode-proposal.md)
- 🟢 **W-265** · `cowork` — deep research: how fux can better spot a question it cannot answer (the coverage floor tested no better than chance). No code. **Opus.** Filed by Arpit (Cowork). [detail](open/W-265-abstention-research.md)
- 🟢 **W-275** · `cowork` — is there a tool to tune `b`, `k1`, field weights, `section_weight` — or can one be built? Survey + proposal; train on retired sets, decide only via L13. No code. **Cowork.** Filed by Arpit (Cowork). [detail](open/W-275-ranking-tuner-research.md)
- 🟢 **W-280** · `cowork` — research: the intent cue lexicon tags 36 of 693 questions. Stronger cues, a yes/no doc type, or close until a consumer declares `[doctype]`; measurable under L13? **Cowork.** Filed by Arpit (Claude Code). [detail](open/W-280-intent-lexicon-research.md)

---
