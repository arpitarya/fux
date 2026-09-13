---
type: Analysis
description: "What this run's evidence points at, turned into specific improvements with repro commands — and the two causes it leaves unresolved."
run: 2026-09-13-benchmark-captures
item: W-150
filed: 2026-09-13
---

# ANALYSIS — 2026-09-13, the benchmark capture set

[`report.md`](report.md) is the run. This is what to do about it.

---

## 1. 🔴 The abstention shape, fourth occurrence, first instrument that names it

**What the evidence shows.** Both versions answered **10 of 10** questions
planted to have no answer, each with a citation. Arm B reported
`band: "partial"`, `answerable: true`, and listed the absent word in `missing` —
including one at `coverage: 0.0009`, where essentially nothing matched.

**Why this occurrence is different from the three before it.** The earlier ones
(20/20 twice, 0/124 across five golden rungs) counted *that* fux answered. This
one carries, per question, **the word the engine itself said was missing** and
the coverage it computed. That turns *"fux does not abstain"* into a testable
statement about a specific band: **`partial` with the distinguishing term in
`missing` is the state that should be reachable by a refusal rule.**

**It is not adjudicated here.** *Does `weak` imply `answerable: false`?* is open
in [`work/BLOCKED.json`](../../BLOCKED.json) and is Arpit's; SR-WORK-BENCHMARK
decision 6 forbids a benchmark ruling one.

**Repro:**

```bash
cd ~/my_programs/fux-benchmark/runs/2026-09-13-benchmark-captures/work/B-docs-00100
../../../../arms/B/venv/bin/fux answer "volume 10014" --json --band \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["confidence"])'
# expect: band partial, answerable true, coverage ~0.0009, missing ["10014"]
```

**The improvement this warrants, and it is a PRE-REGISTRATION, not a change.**
The two-strikes rule makes a second recorded occurrence the trigger for a gate;
this is the fourth, and the gate is still unwritten **because what it should
assert is undecided**. What a session can do without a ruling is write the
pre-registration: the endpoint (planted unanswerables declined), the arms (the
shipped rule against a candidate that reads `missing` against the query's own
terms), and the bar — **before** any number exists.

## 2. `title` at `hit@1` is 0.12, and the cause is not yet known

**What the evidence shows.** Eight questions of the form
`<domain> <subject> handbook` — each is a document's own title line. Neither
version puts that document first; both find it by rank 10.

**Two candidate causes, and this run separates neither.**

1. **The corpus.** 100 documents over ten domains means `freight` selects ten of
   them, and `manifest` appears in the body of most. The title match may simply
   not be rare enough to win at 100 documents.
2. **The ranking.** `title` and `heading` carry weights of 2.0 and 3.0, so a
   title match *should* win. If it does not, the question is whether the query's
   three terms are being spread across five fields in a way that favours a long
   body.

🔴 **Unresolved, and stated as unresolved.** The discriminating experiment is
the same 8 questions at `docs-10000`, where a domain selects 1 000 documents and
a title selects 50: if `hit@1` rises, cause 1; if it stays at 0.12, cause 2.

**Repro:**

```bash
cd ~/my_programs/fux-benchmark
python3 bin/bench.py prepare --run 2026-09-13-title-probe --corpus docs-10000
python3 bin/bench.py hits    --run 2026-09-13-title-probe --corpus docs-10000
# read the `title` rows of runs/2026-09-13-title-probe/rows/hits-docs-10000.jsonl
```

⚠ **Do not run this on a machine somebody else is using**, and it is a
**separate run id** — a probe is not this run's evidence.

## 3. The four saturated classes are a ceiling, and that is why they stay

`needle`, `volume`, `rare+domain` and `domain` are **1.000 at every k on both
arms**. A class that cannot fail measures nothing *today*; what it does is fail
**loudly** the day a ranking change breaks exact-token retrieval, which is the
cheapest catastrophic regression there is.

**No improvement owed.** Stated so a later session does not "tidy" them away as
uninformative — that would be deleting a tripwire for being quiet.

## 4. Latency: the number is untrustworthy and the cause is known

Arm B measured 72.6 ms against arm A's 51.3 ms on 100 documents. **Do not quote
it.** Another session was working on this machine throughout, and
[SETUP-BENCHMARK](../../setup/fux-benchmark.md) standing rule 0a records exactly
this: a loaded machine yields a clean, localised anomaly that reads like a
finding. Interleaving `A B A B` protects the *difference*; it cannot rescue the
absolute number, and a 40 % gap across a major version is large enough that it
deserves a quiet machine before anyone reasons from it.

**Improvement:** re-time `docs-00100` and `docs-01000` on an idle machine, as
its own run, and compare the *shape* of the two curves rather than either
number.

## 5. What the harness itself still owes

- **Six tiers unmeasured.** This run covers `docs-00100`. Nothing about the
  harness is tier-specific; it is a wall-clock cost, not a build cost.
- **`--fast` unmeasured.** Every verb takes `--path fast`; only `scan` was run.
- **CAP-4 on arm A is read off `answer` alone**, because 1.0.0 has no `--band`.
  That asymmetry is permanent — the flag cannot be added to a released version —
  and every row keeps the fields so a reader can see which test applied.
