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
| 🔴 **W-146** — one ruling: does *never restates* reach into docstrings? `UrlSource` can state a wrong default and SR-CONFIG's key-tree gate stays green — it checks names, not values. [detail](open/W-146-the-rest-of-l0.md) | 2026-09-12 | 2d |
| ↳ **blocks:** nothing else in the queue — they decide whether two named exposures get closed, not whether work runs | | |
| 🔴 **W-112** — W-106 closed **without a PASS and cannot produce one** (no corpus carries DENSE-CHUNK's bar). Proceed on the narrowed claim, wait for an instrument, or close? [detail](open/W-112-vector-plane.md) | 2026-09-12 | 2d |
| ↳ **blocks:** nothing else in the queue — search-v3's last item, and the only one left of §5 | | |
| 🔴 **W-156** — every measurement must be on golden data; golden is one synthetic corpus; so *never ship a ranking change off one* can never be met. Which rule gives? [detail](open/W-156-prevalence-outside-golden.md) | 2026-09-13 | 1d |
| ↳ **blocks:** nothing else in the queue — it decides what evidence a ranking change may HAVE, not whether work runs | | |
| 🔴 **W-144** — excluding table cells from `flen` **ranks better** ([verdict](regression/2026-09-12-reaim-and-instruments/VERDICT-W144.md)); one synthetic corpus may not ship a ranking change, so accept or override [the compare doc](compare/table-tokens-in-flen.compare.md). | 2026-09-12 | 2d |
| ↳ **blocks:** nothing else in the queue — the measurement is filed and the code is written; what is missing is the call | | |
| 🔴 **W-148** — two calls left over from W-107: how CI reaches a golden corpus (self-hosted runner / commit `rung-00100` / portable builder), and whether `fux-benchmark` gets built or Node's latency stays unmeasured. [detail](open/W-148-what-the-two-readers-still-owe.md) | 2026-09-12 | 2d |
| ↳ **blocks:** nothing else in the queue — the Node plane is built and measured; these decide where a future measurement runs and what it may CLAIM | | |

---

## Open items

### fux build

- 🟡 **W-140** · `agent`, waiting on Arpit's `--hops` ruling — **1 code row left**: a runner-race flake **not reproduced in 11 attempts**, deliberately unchanged. 20 closed. [detail](open/W-140-guide-authoring-defects.md)
- 🔴 **W-148** · `arpit` — what the two readers still owe: CI cannot reach the golden corpora, Node's latency has no instrument, and the renderer split is staged. [detail](open/W-148-what-the-two-readers-still-owe.md)
- 🔴 **W-112** · `arpit` — the vector plane. W-106 closed without a PASS **and cannot produce one**: no corpus carries DENSE-CHUNK's bar. Determinism narrowed to *same embedder build*. [detail](open/W-112-vector-plane.md)

### testing

- 🟢 **W-159** · `agent` — `fux doctor`'s shadowing row **cannot fire on Windows**: `shutil.which` resolves through PATHEXT and npm writes `fux.cmd`, not a shebang shim. [detail](open/W-159-windows-shadowing-row.md)
- 🟢 **W-158** · `agent` — the benchmark harness must emit its CAP-7 report from the template, and `2026-09-12-benchmark-l9` still has none. **Filed rows only; no run re-executed.** [detail](open/W-158-the-harness-emits-the-templated-report.md)

- 🟡 **W-154** · `agent`, waiting on a quality endpoint that does not exist — **the price is measured** ([run](regression/2026-09-13-rerank-cost/report.md)); the benefit is not, and every obvious endpoint is circular. [detail](open/W-154-rerank-weight-cost.md)
- 🟣 **W-136** · `arpit`, waiting on **2026-09-30** — everything an agent can do is done; **phase 5 scoring is Codex's hands** and is all that is left. [detail](open/W-136-golden-benchmark.md)
- 🟣 **W-145** · `arpit`, waiting on **2026-09-30** — Codex regenerates the golden answer key; until then every golden number is `informed`. [detail](open/W-145-codex-regenerates-the-key.md)
- 🟣 **W-87** · `agent`, waiting on W-145 — P2's `unanswerable` gate is measured (0/124); recall needs phase 5 and **Part B needs an uncontaminated key**. [detail](open/W-87-what-good-means.md)
- 🔴 **W-144** · `arpit` — **W-155 answered the last open test: YES, (b) over-promotes a data dump** ([verdict](regression/2026-09-13-table-is-the-answer/VERDICT.md)). Accept, move to (c)/(d), or wait on W-156. [detail](open/W-144-structure-aware-extraction.md)

### adr update

- 🔴 **W-156** · `arpit` — the environments rule and the single-corpus rule cannot both hold; the resolution decides what evidence any ranking change may have. [detail](open/W-156-prevalence-outside-golden.md)

- 🔴 **W-146** · `arpit` — L0's remainder: ten unhoused `CLAUDE.md` sections want records, and one ruling is owed. [detail](open/W-146-the-rest-of-l0.md)

---
