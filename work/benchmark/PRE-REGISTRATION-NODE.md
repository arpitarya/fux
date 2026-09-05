---
type: PreRegistration
name: PRE-REG-NODE
description: "Frozen before node/ gets a line. The third arm of the differential law: a Node reader of an index Python committed must produce what Python produces. Fixes what must be byte-equal, the corpora, the runtimes and ISAs, the p95 fence at 10 000 documents, and the per-query rows. Ids N0-N4. ONE cell is deliberately unfrozen and is Arpit's."
timestamp: 2026-09-05T00:00:00Z
---

# The Node read plane — the third differential arm. Frozen before Phase 1.

**Filed against W-107** ([`../open/W-107-node-read-plane.md`](../open/W-107-node-read-plane.md)).
The measurement behind it is
[`2026-09-05-node-log-divergence`](../regression/2026-09-05-node-log-divergence/report.md),
Phase 0's first bullet, filed **before** this document.

```
PYTHON SHA = ________________________________________   # written in before the first Node comparison runs
NODE  SHA  = ________________________________________
```

⚠ **New id space — `N0`–`N4`.** `P`, `R`, `B`, `C` and `T` ids keep their
meanings. **This is not a version comparison**: one index, two readers.

---

## 0 · 🔴 ONE CELL IS NOT FROZEN, AND IT IS ARPIT'S

**§2's score-comparison mode is blank on purpose.** W-107 Phase 0's third
bullet is his call and the ratification of 2026-09-05 left both options
unstruck; **nothing in this document defaults it**, and **this pre-registration
is not frozen until he fills it in**. Phase 1 does not start before then — not
because the code cannot be written, but because a threshold written after a
number exists is not a pre-registration.

Everything else below **is** frozen and does not depend on the pick.

---

## 1 · The claim under test

> `npx fux-search ask|find|answer|explain|graph|path|mcp`, run on a repo whose
> index **Python** committed, with **no Python on the host**, produces what
> Python produces.

**A port that "improves" anything has diverged.** Every difference is a defect
until this document says otherwise.

---

## 2 · The comparison — what must be equal, and how

**Frozen.** Per verb, over `--json` output:

| field | comparison | why not weaker |
|---|---|---|
| `id`, `loc`, `order` of results | **byte-equal** | this is the answer; a different order is a different product |
| `heading`, `title`, `phrases`, `locators` (`path:L<a>-L<b>`) | **byte-equal** | a citation a reader opens; an off-by-one line is a wrong quote |
| `band`, `missing`, `answerable` | **byte-equal** | a claim fux makes out loud |
| `source`, `freshness` | **byte-equal** | the claim-strength vocabulary ([ADR-URL-FRESHNESS](../../docs/adr/0052_url-freshness.md)) |
| `graph.json` plane digest | **byte-equal** | one digest or the arm proves nothing |
| **`score`** | 🔴 **`________________`** — **(a)** byte-equal, on one portable `log` in both runtimes · **(b)** equal after `round(9)` | **Arpit's, per §0** |

**The measurement he picks from, in one line:** `Math.log` and `math.log`
differ on **655 / 100 000** wide doubles on darwin/arm64 — **every difference
one ulp** (max rel `2.211e-16`), **none surviving `round(9)`** — and over the
two corpora themselves, **0 discordant scores and 0 discordant top-5 on 197 233
scored documents**. ⚠ **Two limits bound that**: the `idf` argument population
in those corpora is **13 distinct values**, and **glibc was not measured**.

**Whichever he picks, the ORDERING assertion is byte-equal and is not
negotiable.** Option (b) tolerates a difference in the printed score field; it
never tolerates a different ranking. A discordant top-5 fails the arm under
either option.

---

## 3 · The bar — `N0`–`N4`, frozen

| id | what it fixes | the bar |
|---|---|---|
| **N0** | `find --json` over every golden, both corpora | **0 discordant**, on §2's table |
| **N1** | `ask` + `answer --json` over every golden, both corpora | **0 discordant**, on §2's table |
| **N2** | the graph plane | Node's in-memory plane digest **equals** Python's `graph.json` digest, both corpora |
| **N3** | the analyzer and the hash, pinned rather than sampled | **every distinct term of the playground index** analyzed both sides, 0 discordant; BLAKE2b against **RFC 7693 Appendix A** and Python `hashlib` at digest sizes **1, 8, 20**; Porter against the published `voc.txt`/`output.txt`, 0 discordant |
| **N4** | the Node scan's latency at 10 000 documents | **p95 ≤ 150 ms**, warm, in-process, scan path |

**N4's number and why it is 150 and not 50.** Python's own scan p95 at 10 000
documents is **50.2 ms** on this machine
([the run](../regression/2026-09-05-node-log-divergence/report.md), 240
queries, in-process, warm). The fence is set at **3×** that: a transcription in
a JIT runtime with no derived plane is allowed to be slower than the reference,
and the fence exists to catch an **algorithmic** divergence — an accidental
O(n²), a per-document JSON re-parse — not to police a constant factor. **A
fence tighter than the thing it measures is a fence that gets moved.**

⚠ **N4 is a fence, not a goal.** Beating it buys nothing and a Node-side cache
(`--fast`) stays out of scope until it is measured (W-107 §Out of scope).

---

## 4 · Corpora, runtimes, ISAs — frozen

| | |
|---|---|
| corpora | `fux-playground` (10 documents, 50 goldens) **and** `fux-benchmark` `t10000` (**10 000 documents**, 240 pairs) |
| Python | the version CI runs, ≥ 3.11 (L7) |
| Node | **20 and 22** — the LTS pair the CI matrix names. ⚠ **24 is what Phase 0 was measured on**, because it is what the development machine has; 24 is reported, never substituted for 20 or 22 |
| OS / libm | **ubuntu (glibc)**, **macOS arm64 (Apple libm)**, **windows** — all three, because Phase 0 measured one and W-107's hazard cites another |

🔴 **A green arm on one OS is not a green arm.** The whole reason this document
exists is that two libms disagree; running the arm on one of them measures
nothing about the other.

---

## 5 · What is filed, per run

Per `CLAUDE.md` §Conformance runs, and none of it is optional:

- `report.md` with `classification: blind|informed` and the **Authorship**
  block. A port comparison is `blind` when its author had no access to a prior
  discordance list; **it becomes `informed` the moment anyone fixes a specific
  failing query and re-runs.**
- **Per-query rows under `evidence/`, as `.jsonl`** — one row per query per
  arm, discordant or not. ⚠ **`tests/test_regression_runs.py` accepts any
  `.jsonl` under `evidence/`**, so the file being *rows* is on the author, not
  on the check.
- `ANALYSIS.md` with a repro command per finding.
- A `VERDICT.md` naming this file's frozen sha, for each of `N0`–`N4`.

---

## 6 · What would make this pre-registration wrong

**Stated now, so it is not adjudicated later.**

- **If any platform pair ever shows a `log` divergence larger than ~`1e-9`
  relative**, option (b) is dead on arrival and `N0`/`N1` cannot be judged
  under it — the pre-registration is **superseded by a new one**, never edited.
- **If `_format` bumps in Python between the Python sha and the Node sha**, the
  arm is comparing two contracts and every number in it is void. The version
  policy is Phase 4's, and until it exists both shas are pinned by hand above.
- **If the `idf` argument population stays narrow**, `N0`/`N1` passing means
  *"these corpora did not reach a divergent argument"* and not *"the readers
  agree"*. Widening it is
  [the ANALYSIS's §3 improvement](../regression/2026-09-05-node-log-divergence/ANALYSIS.md)
  and should land before N0 is judged.
