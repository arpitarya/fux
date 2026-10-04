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
| 🔴 **W-228** — run [prompt 13](golden/prompts/13-claude-gen4-planted-misfits.md) in a fresh claude.ai chat (6 short docs, 3 planted misfits) and commit its three blocks. No key this time | 2026-10-03 | 1d |
| ↳ **blocks:** W-240, W-236 | | |
| 🔴 **W-243** — rule W-242's **Fork A**: may Node read `.fux/runtime/graph.json` when fresh instead of rebuilding the graph per query? Recommended **yes** (N2 still forces a rebuild). Unblocks CI step 1. [compare doc](compare/shared-runtime.compare.md) | 2026-10-04 | 0d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-251** — the backlog audit: 11 lines only he can answer, in [the item](open/W-251-backlog-audit-rulings.md) §3 — two Laws (L4, L3), three options he declined (SR-RS d12 is back), two reservations, `find --no-archived`, the graph verbs' shape, a size bar | 2026-10-03 | 1d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-257** — launch the enriched-rung authoring session ([the item](open/W-257-enriched-rung.md) says how, and why the author must be blind); it is his tokens. Or say *no* and the three doc2query rows stay unmeasured | 2026-10-04 | 0d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-258** — twenty minutes at his own machine for the three captures only a real network gives ([the item](open/W-258-live-network-captures.md) is the checklist); nothing else in the queue waits on it | 2026-10-04 | 0d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🔴 **W-228** · `arpit` — document families. The lens is built, but its misfit threshold is a placeholder: no known misfits exist yet. Arpit runs prompt 13 to plant 3, riding in gen 4 with W-240. [detail](open/W-228-document-families.md)
- 🔴 **W-236** · `agent` — W-168 step 10 (U2). Part A done: [SR-SECTIONS](../records/0161_sections.md) proposed, [size PASS](regression/2026-09-30-section-size/VERDICT.md) (+98.4 % index). Part B waits on W-240. **Opus.** [detail](open/W-236-section-records.md)
- 🔴 **W-240** · `agent` — a question set that can test section scoring. Prompt 12's docs and 90 questions are in (ruled: accept). Ladder rebuild waits on W-228, then 🔴 Arpit scores. **Opus.** [detail](open/W-240-section-pool-set.md)
- 🟢 **W-249** · `agent` — `fux mcp` and `fux serve` keep the index open across calls, keyed on `.fux/runtime/stamp.json` — residency, not W-242's refused result cache. **Opus.** [detail](open/W-249-resident-index-mcp-serve.md)
- 🟢 **W-250** · `agent` — run `fux hooks` in this repository so `.gitattributes` carries the merge driver where it was written. **Sonnet.** [detail](open/W-250-dogfood-fux-hooks.md)

### testing

- 🔴 **W-243** · `agent` — CI in ~2 min. On `main`: the key saves ✅, a docs-only push skips FULL ✅, `test_node_accel` trimmed. DoD 1 (FAST ≤ 2 min) needs step 1, which is STOP until Arpit rules Fork A. **Opus.** [detail](open/W-243-ci-two-minutes.md)
- 🟢 **W-246** · `agent` — the gates the records asked for and nobody wrote: 16 small stdlib tests and 5 `doctor` rows, each named with the sentence it enforces. **Sonnet.** [detail](open/W-246-mechanical-gates.md)
- 🟢 **W-252** · `agent` — a pre-registration for the Node arm on lab rungs (the live one names the voided playground), then one rerun; parity has read 0 discordant three times. **Sonnet.** [detail](open/W-252-node-arm-preregistration-2.md)
- 🟢 **W-256** · `agent` — three measurements needing no key and no hands: how much of an ingest is the walk vs the extract; whether `doc_coverage` spots an unanswerable question; the daemon on Windows and on a loopback 429. **Sonnet.** [detail](open/W-256-no-key-measurements.md)
- 🔴 **W-257** · `arpit` — an enriched rung: an agent writes questions over rung-01000 so doc2query can finally be measured; the author must be blind to the question sets or the numbers prove nothing. Arpit launches it (his tokens). **Opus.** [detail](open/W-257-enriched-rung.md)
- 🔴 **W-258** · `arpit` — one hands-on session on his machine: a journalled answer whose source then vanishes, a real 429 from a real host, and parallel CDP fetches in signed-in Chrome. Checklist and bars are written. [detail](open/W-258-live-network-captures.md)

### adr update

- 🔴 **W-251** · `arpit` — the backlog audit's rulings: 12 of 24 forks ruled by his delegation on 2026-10-04 (§4), 3 in part; 11 lines are his alone (§3): two Laws, three options he declined, two reservations, taste, tokens, hands. [detail](open/W-251-backlog-audit-rulings.md)

---
