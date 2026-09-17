---
type: PreRegistration
name: PRE-REG-NODE-2
description: "FROZEN 2026-09-12. Supersedes PRE-REG-NODE, which SR-WORK-ENVIRONMENTS voided in part by making fux-playground Arpit's hands only. Arpit ruled that the Python/Node equivalence is measured in fux-lab, on the committed golden ladder, on EVERY change to either reader, and that both must give the same results. Fixes the corpora, the cadence, the comparison, the bar and what is filed. Ids N5-N8; the latency fence moved to fux-benchmark."
timestamp: 2026-09-12T00:00:00Z
---

# The Node read plane, arm 2 — a STANDING equivalence check, not a phase gate

## 0 · ✅ BOTH CELLS ARE FILLED — THIS DOCUMENT IS FROZEN

**Written unfrozen, as PRE-REG-NODE was; Arpit filled both open cells on
2026-09-12 (§7) and it froze in that change.** From here it is never edited —
a successor supersedes it, the way this one supersedes PRE-REG-NODE.

**Filed against W-107** ([`../open/W-107-node-read-plane.md`](../open/W-107-node-read-plane.md)) O3.

## 0a · Why this exists rather than an edit

**A frozen pre-registration is never edited** (`CLAUDE.md` §"A pre-registered
threshold may never move"). [PRE-REG-NODE](PRE-REGISTRATION-NODE.md) stays
exactly as frozen, sha `0e3b4c80…`, and is superseded here for two reasons that
are both about *the instrument*, never about a result anyone disliked:

1. 🔴 **Its corpora are unusable.** §4 names `fux-playground`, and N3 says
   *"every distinct term of the playground index"*.
   [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) made the playground
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
- **"Same results" is not a new bar** — it is [SR-RANKING decision
  8a](../../records/0111_ranking.md), which Arpit ruled on 2026-09-06 and
  which §3 links rather than restates (L0).

## 3 · The comparison — what must be equal, and how

**On PARSED values, never on stdout bytes** (§0.2).

| field | comparison | why not weaker |
|---|---|---|
| `id`, `loc`, `order` of results | **byte-equal** | this is the answer; a different order is a different product |
| `heading`, `title`, `phrases`, `locators` (`path:L<a>-L<b>`) | **byte-equal** | a citation a reader opens; an off-by-one line is a wrong quote |
| `band`, `missing`, `answerable` | **byte-equal** | a claim fux makes out loud |
| `source`, `freshness` | **byte-equal** | the claim-strength vocabulary ([SR-URL-FRESHNESS](../../records/0147_url-freshness.md)) |
| `graph.json` plane digest | **byte-equal** | one digest or the arm proves nothing |
| `score` | **equal after `round(9)`** | [SR-RANKING 8a](../../records/0111_ranking.md). Not restated here |

⚠ **Ordering is not subject to the score tolerance.** A discordant top-5 fails
the arm even when every score agrees at `round(9)`.

## 4 · Corpora — fux-lab, the golden ladder, ceiling 10 000

| | |
|---|---|
| where | **`fux-lab` only** ([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)). Never the playground, never a corpus an agent invented |
| what | the committed golden ladder, [`../golden/ladder/`](../golden/README.md) — rungs **100 · 200 · 500 · 1 000 · 2 000 · 5 000 · 10 000**, plus `rung-seed` |
| ceiling | **10 000 documents, hard.** No rung above it is built, measured, or promised (`CLAUDE.md` §Litmus) |
| adversarial | `tools/differential/adversarial_corpus.py` stays in the matrix — H1's id above U+FFFF exists in no real corpus |
| Python | the version CI runs, ≥ 3.11 (L7) |
| Node | **20 and 22**, the LTS pair the CI matrix names |
| OS / libm | **ubuntu (glibc)**, **macOS arm64 (Apple libm)**, **windows** — all three |

### Cadence — ✅ ruled 2026-09-12, **RE-RULED LOCAL 2026-09-14** (W-148 row 1)

🔴 **AMENDED, not silently edited.** The cadence below was written as a CI
cadence — *every push*, *the full OS × Node matrix* — and **a GitHub runner
could never meet it**, because the ladder corpus is not in this repository and
is not going to be. Arpit ruled on 2026-09-14: **the golden corpus is not for
CI.** Golden runs **local-only, in `fux-lab`**; no self-hosted runner, no
committed rung, no portable builder.

**What that changes, precisely:** *every push* and *nightly* become **every
change to either reader** and **before any release**, run by hand in `fux-lab`.
The rungs, the matrix and the bar are untouched — only where and when.

⚠ **The `FUX_GOLDEN_CORPORA` arm in `node-arm.yml` is REMOVED**, not disabled.
It ran the real arm whenever a repository variable happened to point at a
corpus, so a green tick meant either *the arm passed* or *there was no corpus*,
and nothing in the tree said which. CI now checks the **manifests only**
(`ladder_check.py`) and says so in its job name.

| when | rungs | where |
|---|---|---|
| **every change to either reader**, full OS × Node matrix as available | **`rung-00100` and `rung-10000`** — the two ends | `fux-lab`, by hand |
| **before any release** | **all eight** | `fux-lab`, by hand |
| every push | the ladder **manifests** only — the instrument, not the measurement | CI |

⚠ **The matrix is a local one now, and one machine is not three OSes.** A local
run covers the OS and Node version that machine has. **That is a real loss** and
it is the price of the ruling: the cross-OS half of §4 is now *aspirational
until somebody runs it there*, rather than something CI was quietly failing to
do.

**Why the ends and not all eight per push.** The 100 rung exercises every code
path cheaply; the 10 000 rung is the only one that can expose anything
scale-dependent. The six in between differ from those two in size, not in
kind — so per push they buy coverage that is nearly free to get nightly, at
**48 arm runs instead of 12**. ⚠ **The cost that decided it is not the bill,
it is the latency: slow CI is what teaches people to skip CI**, and an arm
people route around is worth less than one that runs on two rungs.

🔴 **CORRECTED 2026-09-14 — this paragraph was WRONG, in the direction that
flatters.** It read: *"The ladder is committed to this repo (2.2 MB, 8 rungs,
tracked), so CI can run the same rungs fux-lab runs."*

**What is committed is the ladder's MANIFESTS** —
`work/golden/ladder/*.{index,sha256}`, and 2.2 MB is *their* size. **The rungs
themselves are not committed and cannot be**: `rung-10000` alone is 120 MB, and
[L2](../../records/0004_LAW-2-content-never-durable.md) is the law the whole
architecture rests on. So *"CI can run the same rungs"* was never true, and the
conditional arm that appeared to act on it is what made the falsehood survive a
year of green ticks.

**What is still true:** a measurement is *filed* from `fux-lab` into
[`work/regression/`](../regression/README.md), and the manifests are what let
any environment verify it is looking at the same rung.

🔴 **`work/golden/golden-answer/` is not read by this arm and not by any Claude
session.** The arm compares **two readers against each other**, never against
an answer key — so it needs no ground truth and must not acquire a reason to
open one.

## 5 · The bar — `N5`–`N8`

**New ids. `N0`–`N4` are retired with the document that froze them and are
never reused** — the same rule that retired R7/R8 rather than reviving them at
a smaller size.

| id | supersedes | what it fixes | the bar |
|---|---|---|---|
| **N5** | N0 | `find --json` over every golden, on every rung the run covers (§4) | **0 discordant** on §3 |
| **N6** | N1 | `ask` + `answer --json` over every golden, on every rung the run covers (§4) | **0 discordant** on §3 |
| **N7** | N2 | the graph plane | Node's in-memory digest **equals** Python's `graph.json` digest, on every rung the run covers (§4) |
| **N8** | N3 | the analyzer and the hash, **pinned not sampled** | **every distinct term of the 10 000 rung** analyzed and hashed identically |

🔴 **N4's latency fence is NOT here — Arpit moved it to `fux-benchmark`,
2026-09-12.** [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) gives latency to
that environment by name, and this document asks whether two readers *agree*,
which is a different kind of claim from how fast one of them is.

⚠ **A moved fence is not a kept fence until it has a home.** The bar —
**p95 ≤ 150 ms at 10 000 documents, warm, in-process, scan path** — is written
into [SETUP-BENCHMARK](../setup/fux-benchmark.md) §"Inherited 2026-09-12",
which is the spec of record for that environment. 🔴 **`fux-benchmark` is not
built and no open item carries it** — W-139 was removed from the queue on
2026-09-12 — so **nothing measures Node's latency today.** Stated, not
silent.

## 6 · What is filed, per run

Per [SR-RS](../../records/0133_predictions.md) decisions 11–15, and its 🔴
per-query rule:

- **Per-query rows under `evidence/`** — one row per query per arm, per rung,
  pass/fail. A summary count is not enough and never was: the discordant
  count, `b`, `c` and every later test derive from these rows and from nothing
  else.
- **`blind` or `informed`, declared in the report's frontmatter**, with who
  authored each artifact and what they could reach.
- **A `VERDICT.md`** when a run adjudicates one of `N5`–`N8`.
- ⚠ **A green arm is filed, not announced** (§2). Nothing writes *"N5 passes"*
  into a record as an achievement.

## 7 · ✅ The two open cells, filled — Arpit, 2026-09-12

1. **Does the latency fence belong here?** **No — moved to `fux-benchmark`.**
   SR-WORK-ENVIRONMENTS gives latency to that environment; equivalence and speed are different
   claims and one document asserting both makes neither easy to check. §5
   carries the obligation W-139 inherits, so the fence is moved rather than
   dropped.
2. **Every rung, or the ends?** **The ends per push; all eight nightly and
   before a release.** §4's cadence table. The middle six differ in size, not
   in kind, and CI that is slow enough to route around is worth less than CI
   that runs.

**With both answered, this document is frozen** (§0).

## 8 · What would make this pre-registration wrong

- **If the ladder stops being representative** — a rung that no longer carries
  `url:` records, non-ASCII headings, or an id above U+FFFF makes N5–N8 pass
  for a reason unrelated to correctness.
- **If `round(9)` stops being the sort key's resolution.** §3 borrows SR-RANKING
  8a; if `rank.py` changes its key, this document's score row is void, not
  merely loose.
- **If the arm ever compares stdout bytes again** — it would fail on printing
  and be read as an engine divergence (§0.2).
