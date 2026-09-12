---
type: PreRegistration
name: PRE-REG-NODE-2
description: "DRAFT, NOT FROZEN — supersedes PRE-REG-NODE, which L9 voided in part by making fux-playground Arpit's hands only. Arpit ruled 2026-09-12 that the Python/Node equivalence is measured in fux-lab, on the golden ladder, on EVERY change to either reader, and that both must give the same results. Fixes the corpora, the comparison, the bar and what is filed. Ids N5-N9. Two cells are deliberately unfrozen and are Arpit's."
timestamp: 2026-09-12T00:00:00Z
---

# The Node read plane, arm 2 — a STANDING equivalence check, not a phase gate

🔴 **DRAFT. This document is NOT frozen and no number may be measured against
it yet.** PRE-REG-NODE was written unfrozen, Arpit filled its one open cell,
and only then did Phase 1 start. This one follows the same path: §7 lists what
is still his, and the freeze happens in the change that fills them.

**Filed against W-107** ([`../open/W-107-node-read-plane.md`](../open/W-107-node-read-plane.md)) O3.

## 0 · Why this exists rather than an edit

**A frozen pre-registration is never edited** (`CLAUDE.md` §"A pre-registered
threshold may never move"). [PRE-REG-NODE](PRE-REGISTRATION-NODE.md) stays
exactly as frozen, sha `0e3b4c80…`, and is superseded here for two reasons that
are both about *the instrument*, never about a result anyone disliked:

1. 🔴 **Its corpora are unusable.** §4 names `fux-playground`, and N3 says
   *"every distinct term of the playground index"*.
   [L9](../../docs/adr/0011_LAW-9-environments.md) made the playground
   **Arpit's hands only — no agent, no test, no number**. An instrument that
   names a corpus no measurement may touch cannot be run.
2. **It is ambiguous on bytes.** W-107 H2: Python prints `--json` with
   `ensure_ascii=True` and `JSON.stringify` does not, so *"byte-equal"* on raw
   stdout fails on the first em-dash and measures nothing about the engine.
   §2 below states **parsed values**, which is what `node_arm.py` already does.

## 1 · The claim under test

> A Node reader of an index Python committed returns what Python returns —
> same ids, same order, same locators, same band, same graph digest; scores
> equal at the sort key's own resolution.

## 2 · 🔴 It is STANDING, not a gate — Arpit, 2026-09-12

> *"It will always be tested in fux-lab. Whenever we make any changes, both
> through Python and through Node, it'll be tested, and it should be giving
> same results."*

**This is the change that matters most in this document**, and it is not a
detail of scheduling:

| | PRE-REG-NODE | **here** |
|---|---|---|
| when | once, to open a phase | **every change to either reader, forever** |
| what a pass buys | permission to proceed | **nothing — it is the floor** |
| what a fail means | the phase does not start | **the change does not land** |

Three consequences:

- **A green arm is no longer news** and is never reported as an achievement.
  Only a **red** one is information.
- **Either side moving triggers it.** A Python-only change is not exempt; the
  arm exists precisely because the Python half can move alone.
  `tests/test_node_twins.py` is the structural half of the same rule and fires
  when a Python twin moves and its `.mjs` does not.
- **"Same results" is not a new bar** — it is [ADR-RANKING decision
  8a](../../docs/adr/0111_ranking.md), which Arpit ruled on 2026-09-06 and
  which §3 links rather than restates (L0).

## 3 · The comparison — what must be equal, and how

**On PARSED values, never on stdout bytes** (§0.2).

| field | comparison | why not weaker |
|---|---|---|
| `id`, `loc`, `order` of results | **byte-equal** | this is the answer; a different order is a different product |
| `heading`, `title`, `phrases`, `locators` (`path:L<a>-L<b>`) | **byte-equal** | a citation a reader opens; an off-by-one line is a wrong quote |
| `band`, `missing`, `answerable` | **byte-equal** | a claim fux makes out loud |
| `source`, `freshness` | **byte-equal** | the claim-strength vocabulary ([ADR-URL-FRESHNESS](../../docs/adr/0149_url-freshness.md)) |
| `graph.json` plane digest | **byte-equal** | one digest or the arm proves nothing |
| `score` | **equal after `round(9)`** | [ADR-RANKING 8a](../../docs/adr/0111_ranking.md). Not restated here |

⚠ **Ordering is not subject to the score tolerance.** A discordant top-5 fails
the arm even when every score agrees at `round(9)`.

## 4 · Corpora — fux-lab, the golden ladder, ceiling 10 000

| | |
|---|---|
| where | **`fux-lab` only** ([L9](../../docs/adr/0011_LAW-9-environments.md)). Never the playground, never a corpus an agent invented |
| what | the committed golden ladder, [`../golden/ladder/`](../golden/README.md) — rungs **100 · 200 · 500 · 1 000 · 2 000 · 5 000 · 10 000**, plus `rung-seed` |
| ceiling | **10 000 documents, hard.** No rung above it is built, measured, or promised (`CLAUDE.md` §Litmus) |
| adversarial | `tools/differential/adversarial_corpus.py` stays in the matrix — H1's id above U+FFFF exists in no real corpus |
| Python | the version CI runs, ≥ 3.11 (L7) |
| Node | **20 and 22**, the LTS pair the CI matrix names |
| OS / libm | **ubuntu (glibc)**, **macOS arm64 (Apple libm)**, **windows** — all three |

✅ **The ladder is committed to this repo** (2.2 MB, 8 rungs, tracked), so CI
can run the same rungs fux-lab runs. **fux-lab is where a measurement is
*filed* from; it is not a place the data only exists.**

🔴 **`work/golden/golden-answer/` is not read by this arm and not by any Claude
session.** The arm compares **two readers against each other**, never against
an answer key — so it needs no ground truth and must not acquire a reason to
open one.

## 5 · The bar — `N5`–`N9`

**New ids. `N0`–`N4` are retired with the document that froze them and are
never reused** — the same rule that retired R7/R8 rather than reviving them at
a smaller size.

| id | supersedes | what it fixes | the bar |
|---|---|---|---|
| **N5** | N0 | `find --json` over every golden, every rung | **0 discordant** on §3 |
| **N6** | N1 | `ask` + `answer --json` over every golden, every rung | **0 discordant** on §3 |
| **N7** | N2 | the graph plane | Node's in-memory digest **equals** Python's `graph.json` digest, every rung |
| **N8** | N3 | the analyzer and the hash, **pinned not sampled** | **every distinct term of the 10 000 rung** analyzed and hashed identically |
| **N9** | N4 | the Node scan's latency at 10 000 documents | **p95 ≤ 150 ms**, warm, in-process, scan path |

⚠ **N9 is an equivalence document carrying a latency fence, which is a
different kind of claim.** It is kept because dropping it would silently
retire a bar, not because speed is what this arm is for. §7 asks whether it
belongs here or in `fux-benchmark` under L9.

## 6 · What is filed, per run

Per [ADR-RS](../../docs/adr/0133_predictions.md) decisions 11–15, and its 🔴
per-query rule:

- **Per-query rows under `evidence/`** — one row per query per arm, per rung,
  pass/fail. A summary count is not enough and never was: the discordant
  count, `b`, `c` and every later test derive from these rows and from nothing
  else.
- **`blind` or `informed`, declared in the report's frontmatter**, with who
  authored each artifact and what they could reach.
- **A `VERDICT.md`** when a run adjudicates one of `N5`–`N9`.
- ⚠ **A green arm is filed, not announced** (§2). Nothing writes *"N5 passes"*
  into a record as an achievement.

## 7 · 🔴 The cells that are Arpit's — this document freezes when they are filled

1. **Does `N9` (latency) belong here at all?** [L9](../../docs/adr/0011_LAW-9-environments.md)
   gives latency to `fux-benchmark`, and this arm is about equivalence. Keep
   it here, move it, or retire the fence.
2. **Every rung, or the ends?** §4 says all eight on every change. Eight rungs
   × 2 Node versions × 3 OSes is the honest reading of *"whenever we make any
   changes"*, and it is also a CI bill. The alternative is **100 + 10 000 on
   every push, all eight nightly and before a release.**

## 8 · What would make this pre-registration wrong

- **If the ladder stops being representative** — a rung that no longer carries
  `url:` records, non-ASCII headings, or an id above U+FFFF makes N5–N8 pass
  for a reason unrelated to correctness.
- **If `round(9)` stops being the sort key's resolution.** §3 borrows ADR-RANKING
  8a; if `rank.py` changes its key, this document's score row is void, not
  merely loose.
- **If the arm ever compares stdout bytes again** — it would fail on printing
  and be read as an engine divergence (§0.2).
