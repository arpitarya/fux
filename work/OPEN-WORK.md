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
| 🔴 **W-168 step 1** — an anchor field makes a document's bytes a function of OTHER documents while re-index is per-document, so full and incremental ingest disagree on the incremental path only. Dirty the out-edge targets too, or don't build it? | 2026-09-15 | 0d |
| ↳ **blocks:** nothing else in the queue — W-168's own steps 1 and 5; steps 2, 4 and 6–10 are unaffected. | | |

---

## Open items

### fux build

- 🟢 **W-178** · `agent` — **consumer fetchers open like their decoders already do**: `fetch=` becomes a typed, shape-validated name. Ruled 2026-09-15. 🔴 No third fetcher is possible today. Ratified, not built. [detail](open/W-178-consumer-planes-open-sets.md)
- 🟢 **W-177** · `agent` — **`fux update` is deleted; `fux ingest` absorbs its whole surface**, ruled 2026-09-15. Reverses W-63 decision 3; no law edit. [detail](open/W-177-ingest-absorbs-update.md)
- 🟣 **W-161** · `agent`, waiting on **2026-09-30** — **BUILT 2026-09-15**, both readers, 0 discordant; both tiers ship on and unmeasured. Only the two arms remain, and they need Codex's link-dependent questions. [detail](open/W-161-graph-composed-ask.md)
- 🔴 **W-168** · `agent` — the ten search improvements. **Step 1 scoped 2026-09-15, not started:** an anchor field makes a document's bytes depend on other documents while re-index is per-document. Needs the inbox ruling. [detail](open/W-168-search-improvements.md)
- 🟣 **W-176** · `agent`, waiting on **2026-09-30** — **steps 1–3 landed 2026-09-15**: `weak` ⇒ `answerable: false`, the steering text, `failed`. The seven measured gates need Codex's key. [detail](open/W-176-abstention-gates.md)
- 🟢 **W-170** · `agent` — `.fux/observers/`, the observe-only hook. Both rulings taken 2026-09-14: cage's compare **C**; SR-OBSERVE filed `proposed` with the L10 exemption named. Build it; the record flips to `accepted` in that change. [detail](open/W-170-cage-search-leg.md)
- 🟢 **W-148** · `agent` — ruled 2026-09-14: golden is **local-only** (drop CI's corpus arm), Node's latency goes into `fux-benchmark` beside Python's, the harness stays scratch. Three rows of agent work, then close. [detail](open/W-148-what-the-two-readers-still-owe.md)
- 🟢 **W-140** · `agent` — `--hops` ruled **(c)** 2026-09-14: bound the walk's work, `truncated` in every rendering; build row 12's last third. Row 21's runner-race flake stays unreproduced (11 attempts). 20 closed. [detail](open/W-140-guide-authoring-defects.md)

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
