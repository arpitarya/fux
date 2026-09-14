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
| 🔴 **W-140** — the `--hops` fork: [the compare doc](compare/path-hops-bound.compare.md) proposes **(c) bound the walk's work** with `truncated` in every rendering. The last ruling owed. [detail](open/W-140-guide-authoring-defects.md) | 2026-09-12 | 2d |
| ↳ **blocks:** nothing else in the queue — W-140's own last code row is behind it | | |

---

## Open items

### fux build

- 🟢 **W-161** · `agent` — the graph-composed `ask`: boosted tier + labelled `related` tier, `answer` reads `ask`. W-160's atoms shipped 2026-09-14, inert. **W-156 ruled 2026-09-14**: evidence is SR-RS d19 on golden data; nothing waits. [detail](open/W-161-graph-composed-ask.md)
- 🟢 **W-168** · `agent` — the ten search improvements as one program, ten gated steps (anchor text first, section units last); each step golden question → pre-registration → build → measure. Unblocked 2026-09-14 by the W-156 ruling. [detail](open/W-168-search-improvements.md)
- 🟢 **W-176** · `agent` — the nine abstention gates, ruled (a) 2026-09-14: 1 + 9 + the output surface now; 4, 3, 2, 7, 8, 5 measured behind flags from **2026-09-30** (Codex's unanswerable key); 6 once W-161 has landed. [detail](open/W-176-abstention-gates.md)
- 🟢 **W-170** · `agent` — `.fux/observers/`, the observe-only hook. Both rulings taken 2026-09-14: cage's compare **C**; SR-OBSERVE filed `proposed` with the L10 exemption named. Build it; the record flips to `accepted` in that change. [detail](open/W-170-cage-search-leg.md)
- 🟢 **W-148** · `agent` — ruled 2026-09-14: golden is **local-only** (drop CI's corpus arm), Node's latency goes into `fux-benchmark` beside Python's, the harness stays scratch. Three rows of agent work, then close. [detail](open/W-148-what-the-two-readers-still-owe.md)
- 🔴 **W-140** · `agent`, waiting on Arpit's `--hops` ruling — **1 code row left**: a runner-race flake **not reproduced in 11 attempts**, deliberately unchanged. 20 closed. [detail](open/W-140-guide-authoring-defects.md)

### testing


- 🟡 **W-154** · `agent`, waiting on a quality endpoint that does not exist — **the price is measured** ([run](regression/2026-09-13-rerank-cost/report.md)); the benefit is not, and every obvious endpoint is circular. [detail](open/W-154-rerank-weight-cost.md)
- 🟣 **W-136** · `arpit`, waiting on **2026-09-30** — everything an agent can do is done; **phase 5 scoring is Codex's hands** and is all that is left. [detail](open/W-136-golden-benchmark.md)
- 🟣 **W-145** · `arpit`, waiting on **2026-09-30** — Codex regenerates the golden answer key; until then every golden number is `informed`. [detail](open/W-145-codex-regenerates-the-key.md)
- 🟣 **W-87** · `agent`, waiting on W-145 — P2's `unanswerable` gate is measured (0/124); recall needs phase 5 and **Part B needs an uncontaminated key**. [detail](open/W-87-what-good-means.md)
- 🟣 **W-175** · `agent`, waiting on **2026-09-30** — does a correction help OTHER phrasings? Ruled 2026-09-14: three arms (dogfood · fux's own tree · Codex), N=12 / M=5. Harness now; the numbers wait for Codex's blind paraphrases. [detail](open/W-175-correction-generalisation.md)
- 🟢 **W-144** · `agent` — ruled **(d)** 2026-09-14: sweep `b ∈ {0.75, 0.6, 0.5, 0.4}` over the three measured families, ship the first value positive on all with controls holding; (b) + idf guard is the fallback. [detail](open/W-144-structure-aware-extraction.md)

### adr update

- 🟢 **W-146** · `agent` — L0's remainder, ruled **(a)** 2026-09-14: docstrings may explain mechanism; a key-and-default table becomes a link; `test_docstring_defaults.py` closes the `UrlSource` exposure. Then row 17, then close. [detail](open/W-146-the-rest-of-l0.md)


---
