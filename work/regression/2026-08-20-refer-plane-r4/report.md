# 2026-08-20 — R4: the refer plane, cold and warm

**A measurement against a pre-registered threshold.** The threshold, the arms
and the verdict rule were frozen in
[`tools/refer-bench/PRE-REGISTRATION.md`](../../../tools/refer-bench/PRE-REGISTRATION.md)
and committed **before** this harness produced a number (`d98874d`). The ruling
is [`VERDICT.md`](VERDICT.md).

- **Engine:** the working tree at `d98874d` (dirty — the harness itself was
  uncommitted while it ran). **Not** the published `0.33.0` wheel, which
  predates the refer plane entirely.
- **Surface:** Darwin 25.3.0 arm64, Python 3.14.2. Latency is **not comparable
  across machines** (fux-lab TEST-PLAN §2); a re-run elsewhere is a new
  measurement, not a confirmation.
- **Reproduce:** [`evidence/reproduce.sh`](evidence/reproduce.sh) — offline; the
  only socket opened is to loopback.
- **Raw:** [`evidence/report.json`](evidence/report.json) ·
  [`evidence/cache-arms.json`](evidence/cache-arms.json) ·
  [`evidence/run.log`](evidence/run.log)

---

## 1 · R4 — the numbers

k = 10 cited documents, 20 cold/warm pairs per arm, p95 nearest-rank.

| arm | server delay | cold median | **cold p95** | warm median | **warm p95** |
|---|---|---|---|---|---|
| `local` | 0 ms | 0.015 s | 0.042 s | 0.009 s | 0.010 s |
| **`internal`** | **100 ms** | 1.067 s | **1.113 s** | 0.009 s | **0.016 s** |
| `slow` | 500 ms | 5.044 s | 5.069 s | 0.009 s | 0.010 s |

| bound | judged arm | result |
|---|---|---|
| cold k=10 ≤ **3.000 s** | `internal` | **1.113 s** — passes with 1.9 s of headroom |
| warm ≤ **0.300 s** | `internal` | **0.016 s** — passes by 19× |

**Verdict: PASS.** See [`VERDICT.md`](VERDICT.md).

Every arm was checked for having actually done the work: six citations
assembled and `current` on every document of the last cold call, recorded in
the report as `citations_on_last_cold_call` and
`verdict_labels_on_last_cold_call`. That field exists because the first run of
this bench returned **zero citations in 1.9 ms** and would otherwise have read
as a spectacular pass — see §4.

## 2 · The finding the pre-registration named in advance

**The plane fetches serially, and the `slow` arm shows what that costs.**
`refer()` loops over candidates; there is no concurrency anywhere in
`src/fux/refer/`. Paper §8's P4 says *"(k=10, parallel)"* and **that
parallelism is not built**.

The three arms are almost exactly `k × delay` plus a fixed ~40 ms:

| arm | `k × delay` | measured cold p95 | residual |
|---|---|---|---|
| `local` | 0 s | 0.042 s | 0.042 s |
| `internal` | 1.000 s | 1.113 s | 0.113 s |
| `slow` | 5.000 s | 5.069 s | 0.069 s |

So **cold latency is the source's latency, ten times over**, and the engine's
own contribution is under 120 ms in every arm. Two consequences:

- **The 3 s bound is a statement about the source, not about fux.** It holds
  for any source answering in under ~295 ms and fails for any source slower
  than that, at k=10.
- **`slow` fails the cold bound (5.069 s > 3 s)** and is reported here rather
  than omitted. It is not part of the verdict — the judged arm was fixed in
  advance — but it is the honest boundary of the claim.

## 3 · The warm bound was generous, and the pre-registration said so first

Pre-registration §5 recorded, before the run, that the warm bound might be
measuring the wrong thing: with both caches populated there is no network at
all, so the warm number is chunking, re-scoring and assembly over ten
documents.

It was. **Warm p95 is 16 ms against a 300 ms bound — a factor of 19.** Warm is
also flat across all three arms (0.010 / 0.016 / 0.010 s), which is exactly
what "no network on this path" looks like.

**Read the warm pass as confirming the caches work, not as evidence that the
plane is fast.** A bound nothing could plausibly have failed did not test much.

## 4 · Two defects in the harness, both caught by its own instrumentation

Recorded because the run is only as trustworthy as what it noticed about
itself.

**1. The fetcher was passed as a module, not a callable.** `load_fetcher`
returns the imported module; the plane wants `module.fetch`. Every fetch raised
a `TypeError`, which the plane **correctly** degraded to `unverified` — so the
bench ran in 1.9 ms, reported a comfortable pass, and had fetched nothing. The
`verdict_labels_on_last_cold_call` field was added in response and is now part
of the report.

**2. The mock server served markdown as `text/plain`.** The shipped fetcher is
an *HTML-to-markdown* fetcher: `html_to_markdown` runs on whatever comes back,
and its inline-text path collapses all whitespace. A 9 KB document arrived as
one line, `chunk()` found no heading boundaries, the single passage exceeded
the 8 000-byte budget, and **every citation was dropped**. The fixture now
serves HTML, which is what a wiki page is.

Neither is an engine defect. Both are the same lesson twice: *a latency bench
with nothing to show for the latency is the easiest wrong number to file.*

## 5 · ARC versus LRU — measured, and **post-hoc**

[`work/compare/cache-policy.compare.md`](../../compare/cache-policy.compare.md)
chose ARC over LRU with its own reopen-trigger: *"measured hit-rate shows no
advantage over LRU on real Fux workloads (then take the simpler code)."*
Nothing had measured it. This does — with a caveat that must be read first.

| workload | metric | ARC | LRU | advantage |
|---|---|---|---|---|
| `hot` | overall | 97.50 % | 97.50 % | +0.00 pts |
| `scan` | overall | 25.15 % | 24.24 % | **+0.91 pts** |
| `scan` | **hot requests only** | 90.00 % | 87.50 % | **+2.50 pts** |

**The metric was changed after seeing the first number, and that is
disqualifying on its own.** The overall figure came out at +0.91 pts, below the
2-pt bar declared before the run. Inspecting why showed the bulk pass is 76 %
of the trace and a guaranteed miss for both policies, so it drowns the effect
the workload exists to expose. Restricting to the requests a caller actually
waits on gives +2.50 pts — above the bar, and the opposite outcome.

The reasoning for the second metric is sound, and it is still a metric chosen
after seeing a result it then reversed. **So this is reported as post-hoc and
does not close the trigger.** Both numbers are above; the choice between them
is Arpit's, not this run's.

Two further limits, independent of that:

- **These are synthetic traces.** The trigger says *real Fux workloads*, and
  there is no production access log because nothing is in production. A run
  like this can **fire** the trigger — no advantage even on the workload ARC
  was chosen for would be strong evidence — but it cannot **clear** one whose
  wording asks for something it does not have.
- **The margin is small either way.** ARC costs four lists, two ghost lists and
  an adaptation parameter, for 2.5 points on its best workload. Whether that is
  worth the code is a judgement the compare doc's own weighting should be
  re-read against, not a number this run settles.

## 6 · What this run does not measure

- **Not the budget sweep.** It needs a graded corpus, and `fux-playground`'s
  goldens are unwritten by design ([W-57](../../open/W-57-graph-lane-acceptance.md)
  — a golden derived from the engine's own output passes forever). W-59 stays
  open for it.
- **Not `mode = never`.** It never fetches, so it has no cold path.
- **Not a real Confluence instance.** The 100 ms delay is a stand-in and is
  named as one.
- **Not concurrency.** There is none to measure.
