---
type: OpenItem
id: W-181
title: "W-181 — the observer hook's latency capture, and the subscriber it needs"
description: "W-170 shipped .fux/observers/ on 2026-09-15 with the byte-identity half discharged by a hostile test and the latency half unfiled, because it needs a real subscriber's observer and a golden rung. Filed 2026-09-15 under SR-WORK-OPEN-QUEUE 23a because W-170 was 🟡 on a subscriber that does not exist yet."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-181 — the observer latency capture

**Model: Sonnet** for the reference observer and the run; **Opus** for the
keep/remove call.

**Why this exists.** [W-170](W-170-cage-search-leg.md) is **BUILT** (`fd674584`,
2026-09-15) and [SR-OBSERVE](../../records/0157_observe.md) is `accepted`. Two
things were left open and stated rather than quietly closed; one of them —
Node's half — is a **declared out-of-scope**
([SR-NODE-SEARCH](../../records/0153_node-search.md) decision 18) and needs no
item. The other is this: the keep/remove call wants **p50 `ask` with no observer
against p50 `ask` with a subscriber's**, and no subscriber exists.

⚠ **This is the row that made the rule.** W-170 read *"waiting on a real
subscriber's observer"* — a wait nothing in fux could ever clear, because the
subscriber is cage's and cage had not written one. Naming the absence was honest;
leaving it unfiled is what rule 23b now forbids.

## The fork this item has to resolve first

**The measurement does not actually need *cage's* observer — it needs *an*
observer.** Two shapes, and picking one is inside this item:

| | what it is | what it costs |
|---|---|---|
| **a reference observer in fux** | a minimal observer under `tools/`, written to be representative rather than real — writes a line and returns | cheap and available now. ⚠ **Its realism is an assertion**: a trivial observer prices the *seam*, not a subscriber's work, and the verdict must say which it measured |
| **cage's real observer** | `cage setup` drops it; it writes cage's ledger | the honest number, and **it is not fux's to write** — it waits on cage |

**Recommended: do both, in that order.** The reference observer prices the seam
now and unblocks W-170's keep/remove call; cage's number, when it exists,
is the reopen trigger. ⚠ **What must not happen is the reference observer's
number being reported as a subscriber's** — that is the whole hazard of the
cheap arm.

## Definition of done

1. The fork above is resolved and the choice is recorded.
2. p50 `ask` with and without an observer, on **this repo and the largest
   golden rung** in `fux-lab`.
3. The verdict names **which observer it priced**, and whether the cap
   (SR-OBSERVE decision 10b) held.
4. Filed under `work/regression/` per SR-RS decision 10a.

⚠ **The cap ABANDONS a thread; it cannot kill one** (SR-OBSERVE 10b corrected
decision 6's wording). What it guarantees is that a consumer's analytics cannot
make `fux ask` slow — only itself. The capture must be read against that claim,
not against *"the observer was stopped"*.

## Closes

[W-170](W-170-cage-search-leg.md)'s remaining obligation. Node's half stays out
of scope and is **not** this item's.
