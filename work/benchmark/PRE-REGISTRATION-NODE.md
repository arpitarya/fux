---
type: PreRegistration
name: PRE-REG-NODE
description: "Frozen before node/ gets a line, and FULLY frozen since 2026-09-06 when Arpit ruled option (b). The third arm of the differential law: a Node reader of an index Python committed must produce what Python produces. Fixes what must be byte-equal, the corpora, the runtimes and ISAs, the p95 fence at 10 000 documents, and the per-query rows. Ids N0-N4. The one deliberately-unfrozen cell (score comparison) is filled: (b), equal after round(9)."
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

## 0 · ✅ THE LAST CELL IS FILLED — THIS DOCUMENT IS FROZEN

**§2's score-comparison mode was blank on purpose.** W-107 Phase 0's third
bullet was Arpit's call; nothing in this document defaulted it.

**He ruled on 2026-09-06: option (b), equal after `round(9)`.** The cell in §2
carries it. **This pre-registration is now frozen in full**, and §3's bars, the
comparison table and §6's kill clauses may not move again — a threshold edited
after a number exists is not a pre-registration.

⚠ **What the ruling did NOT do.** It did not weaken the ordering assertion,
which stays byte-equal (§2, last paragraph), and it did not touch §6's first
bullet: a `log` divergence above `~1e-9` relative on any platform pair still
kills option (b) and supersedes this document.

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
| `source`, `freshness` | **byte-equal** | the claim-strength vocabulary ([ADR-URL-FRESHNESS](../../docs/adr/0149_url-freshness.md)) |
| `graph.json` plane digest | **byte-equal** | one digest or the arm proves nothing |
| **`score`** | ✅ **(b) — equal after `round(9)`.** Arpit, 2026-09-06. `round(9)` is `rank.py`'s own sort-key resolution, not a tolerance invented to pass a test; **(a)** (byte-equal on one portable `log`) was declined | **his call, per §0** |

**The measurement behind the ruling, in one line:** `Math.log` and `math.log`
genuinely differ — **655 / 100 000** wide doubles on darwin/arm64 and
**722 / 100 000** on **glibc 2.39 / x86_64** — but **every difference is one
ulp** (max rel `2.211e-16`) and **none survives `round(9)`**. Both limits that
bounded the first run are now closed: the `idf` argument domain is
**exhausted, not sampled** — all **10 939** arguments `df = 1..n` at
`n ∈ {101, 838, 10 000}`, of which **841 (7.69 %) differ and 0 differ at
`round(9)`**
([`ADDENDUM-GLIBC`](../regression/2026-09-05-node-log-divergence/ADDENDUM-GLIBC.md),
[`ADDENDUM-IDF`](../regression/2026-09-05-node-log-divergence/ADDENDUM-IDF.md))
— and **glibc is measured**. End to end, **0 discordant scores and 0 discordant
top-5 across 249 141 scored documents** on the three corpora, under both the
exact and the rounded sort.

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
- ~~**If the `idf` argument population stays narrow**, `N0`/`N1` passing means
  *"these corpora did not reach a divergent argument"* and not *"the readers
  agree"*.~~ ✅ **Discharged 2026-09-06, and further than asked.** The clause
  wanted a wider sample; what landed is the **whole domain** — `idf`'s argument
  is `(n - df + 0.5)/(df + 0.5) + 1` with `df ∈ 1..n`, so it is enumerable, and
  [`evidence/idfdomain.py`](../regression/2026-09-05-node-log-divergence/evidence/idfdomain.py)
  enumerates it at three corpus sizes. **The clause is struck, not deleted, and
  its bar was never lowered to discharge it.**
