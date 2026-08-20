# Pre-registration — M4's gate, R4

**Written before any number was produced.** Metric definitions, arm
definitions, the mock server's behaviour and the pass/fail conditions are fixed
here so they cannot be adjusted in the direction the numbers happen to point.
`git log` on this file is the evidence: it is committed **before** the run it
governs.

If something below turns out to be under-specified once the data exists, the
honest move is to **record the ambiguity and hand the call to Arpit** — not to
redefine the term.

---

## 1. The question

The refer plane ranks in the committed index, then goes and gets the cited
documents from the systems that own them. **Is that affordable enough to put on
a query path** — once, cold, and then repeatedly, warm?

## 2. The threshold — not restated loosely

**Verbatim from [`work/OPEN-WORK.md`](../../work/OPEN-WORK.md) §Predictions and
from paper §8 (P4): cold k=10 ≤ 3 s / warm ≤ 300 ms.**

| outcome | condition |
|---|---|
| **PASS** | cold p95 ≤ 3.000 s **and** warm p95 ≤ 0.300 s, on the judged arm (§4) |
| **FAIL** | either bound exceeded on the judged arm |

No tolerance band is invented around either bound. What is handed to Arpit
rather than adjudicated is anything the run reveals about the threshold's own
construction — see §5, which names one such thing **in advance**.

## 3. What "cold" and "warm" mean

The plane has **two** caches, and they are not the same thing, so both are
defined here rather than left to the harness:

| | ARC (`refer/arc.py`) | the TTL fetch cache (`refer/fetchcache.py`) |
|---|---|---|
| keyed by | `(loc, sha)` — content address | `loc` alone |
| served | only when the sha is already known correct | before the sha is confirmed, within `cache_ttl_seconds` |

- **Cold** — a fresh `ARC` instance, an empty `.fux/runtime/fetch-cache/`, and
  a process that has already imported the engine. **Interpreter start-up is
  excluded**: the prediction is about a query on a running agent's path, not
  about `python -c`.
- **Warm** — the immediately following identical call, with both caches
  populated by the cold call and nothing evicted.

Both are measured in the same process, cold first, so the warm number is the
genuine second call and not a differently-configured one.

## 4. Arms — the mock server, and which arm the verdict is read from

A real `http.server` on `127.0.0.1`, serving ten documents through the
**consumer fetcher `fux setup` generates** (`.fux/fetchers/http.py`). The whole
transport path is exercised: socket, HTTP, the consumer's file,
`urlsrc.sanitize`, the sha comparison. Nothing is injected past it.

The server sleeps a fixed interval before responding. That interval is the arm:

| arm | per-request delay | what it stands for | judged? |
|---|---|---|---|
| `local` | 0 ms | the engine's own cost, with transport but no source latency | no — reported as the floor |
| **`internal`** | **100 ms** | **an internal corporate service over SSO/proxy** | **yes — R4 is read from this arm** |
| `slow` | 500 ms | a rate-limited or geographically distant source | no — reported as the stress case |

**`internal` is the judged arm**, fixed here by argument and not by result: 100
ms is the round trip an internal Confluence or SharePoint instance behind a
proxy plausibly costs, and the paper's own §6 places live fetch at *"0.5–2 s
live-parallel"* for k documents, which at k=10 is only consistent with a
per-document cost in this range.

### 4.1 A disclosure that changes how the arms read

**The plane fetches serially.** `refer()` loops over candidates; there is no
concurrency anywhere in `src/fux/refer/`. Paper §8's P4 says *"(k=10,
parallel)"*, and **that parallelism is not built**. This is stated here, before
the run, because otherwise a cold number linear in `k × delay` would look like a
surprise rather than a known property. If the `slow` arm exceeds 3 s while
`internal` passes, the finding is *the serial loop*, and it is a design finding
rather than a constant that needs tuning.

## 5. The construction risk, named in advance

**The warm bound may be measuring the wrong thing.** With both caches populated
there is no network at all, so the warm number is chunking, re-scoring and
assembly over ten documents — a bound of 300 ms on that is generous by a wide
margin, and passing it says little about the plane. If the warm p95 lands far
below the bound, the report says so plainly rather than presenting a comfortable
pass as a strong result.

## 6. The statistic

- **k = 10** cited documents per call, fixed.
- **20 cold/warm pairs per arm**, each cold pair preceded by a fresh cache and
  a restarted TTL directory.
- Judged on **p95**; median reported beside it. Worst case decides, as R3 did.
- Corpus and queries are seeded and deterministic; the document bodies are
  large enough (≥ 4 KB) that chunking and re-scoring do measurable work.

## 7. What this run does not measure

- **Not the budget sweep**, and not ARC-vs-LRU. Both are named in
  [W-59](../../work/open/W-59-refer-plane-measurement.md), both need a graded
  corpus, and a generated corpus cannot grade answer quality — that is the
  playground's job, not the lab's.
- **Not `mode = never`.** It never fetches, so it has no cold path.
- **Not a real Confluence instance.** The mock server's delay is a stand-in and
  is stated as one.

## 8. The instrument

- **Harness:** [`run.py`](run.py) in this directory.
- **Engine:** the working tree, by path — **not** the published `0.33.0` wheel,
  which predates the refer plane. The commit sha is recorded in the report.
- **Surface:** recorded with the number; latency is not comparable across
  machines (fux-lab TEST-PLAN §2).
