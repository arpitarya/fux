---
type: Runbook
name: RUNBOOK-BENCHMARK
title: RUNBOOK-BENCHMARK — how an agent executes a version benchmark, step by step
description: "The operating procedure for a version-to-version benchmark run against a frozen pre-registration in this directory: preconditions, where each step runs, the halt gates in order, the two-session blind protocol, the filing checklist. Restates no bar."
timestamp: 2026-08-28T00:00:00Z
---

# RUNBOOK-BENCHMARK — a version benchmark, executed by an agent

**Model: Sonnet** for every step in §1–§5 and §7 — they are specified work
with a mechanical gate that catches a wrong one. **Opus** for §6's authoring
session, for `ANALYSIS.md`, and for *any* moment a number wants to be
reinterpreted: that is where a disappointing null becomes a claim, and this repo
has got it wrong four times. **State the model out loud when handing over.**

> **This document restates no bar.** Every threshold, metric and predicted
> verdict lives in the frozen pre-registration the run cites —
> [`PRE-REGISTRATION-V1-VS-HEAD.md`](PRE-REGISTRATION-V1-VS-HEAD.md) or
> [`PRE-REGISTRATION-CONTESTED.md`](PRE-REGISTRATION-CONTESTED.md). Where a step
> says *"rule against §4.x"*, open that section and rule against it as written.
> If this runbook and a pre-registration disagree, the pre-registration wins and
> this file is corrected in the same change.

Written 2026-08-28 from what the two executed runs learned
([v1-vs-HEAD](../regression/2026-08-28-benchmark-v1-vs-head/report.md),
[contested](../regression/2026-08-28-benchmark-contested/report.md)). Every ⚠
below is a thing one of them paid for.

---

## 0. Before the first command — read, decide, write down

| # | do | why |
|---:|---|---|
| 0.1 | Read [`README.md`](README.md) rules 1–7, [SETUP-BENCHMARK](../setup/fux-benchmark.md), and the pre-registration you will cite, **end to end** | the run may never be used to say the things in its §5, and you need to know them before you can avoid saying them |
| 0.2 | Decide: **is this a new run of a frozen pre-registration, or a new pre-registration?** A later `HEAD`, a different knob, a rebuilt instrument = **new pre-registration, new id letter**. Never edit a frozen one | README, *id spaces* |
| 0.3 | Decide **`blind` or `informed`** now, not at filing. One session doing everything is `informed` by construction. `blind` needs §6 | CLAUDE.md, *every measured run is blind or informed* |
| 0.4 | Decide **where each half runs** (§2). Quality and bytes: cloud or laptop. Wall-clock: **laptop only, one session** | SETUP-BENCHMARK, *where it can and cannot run* |
| 0.5 | Write the run's `work/regression/<date>-<run>/` directory name and the model per step into the handoff **before** starting | the filing checklist (§8) is easier to keep than to reconstruct |

🔴 **Halt conditions apply in order.** A gate that fails stops the run at that
step; nothing after it is measured, and the halt is filed as the run's result.
Running the interesting numbers first and the gates last is how a broken
harness gets believed.

---

## 1. Preconditions — verify, never rebuild

```bash
# 1.1 the three siblings exist and are not inside the repo
ls ~/my_programs            # expect: fux  fux-playground  fux-lab  fux-benchmark

# 1.2 the harness is a git repo with the two entry points
cd ~/my_programs/fux-benchmark && git status --short | head && ls bin/
# expect: bench.py  latency.py   — ⚠ not the seven shell scripts an old draft listed

# 1.3 shared/ is the lab's generator, imported not copied
readlink shared               # expect: ../fux-lab/shared/
python3 shared/generate/make_corpus.py --selftest

# 1.4 both arms resolve and DIFFER
arms/A/venv/bin/fux --version
arms/B/venv/bin/fux --version
arms/A/venv/bin/python -c 'import sys;print(sys.version_info[:2])'
arms/B/venv/bin/python -c 'import sys;print(sys.version_info[:2])'   # same minor, ≥ 3.11
```

| gate | on failure |
|---|---|
| `fux-benchmark` missing | stand it up per SETUP-BENCHMARK §Shape. 🔴 **Never delete or recreate an existing one** — new work is a new `runs/<date>/` inside it |
| `shared` is a copy, not a link | fix the link. A forked generator produces numbers that *look* lab-comparable and are not |
| `--selftest` fails | halt. The instrument is broken before the run |
| arms resolve to the same version | the second venv was installed from the wrong source; re-install, re-check |
| Python minors differ | re-create the odd venv with `uv python install 3.11` |

⚠ **Not on the Cowork device VM** — no network, Python 3.10. Cloud sandbox or
the local macOS shell for §1–§5; laptop only for §7.

---

## 2. The machine split — decide it, then never mix it

| what | deterministic? | may run in the cloud? | may run on the laptop? |
|---|---|---|---|
| corpus generation, `sha256` | yes | yes | yes |
| quality rows (`hit@k`, `target_first`, inversions, declines) | yes | yes | yes |
| committed bytes, wheel size | yes | yes | yes |
| `ask` p50/p95, ingest/build wall-clock | **no** | 🔴 **no** | yes — **one machine, one session** |

**A run that quietly measures latency in the cloud and quality on the laptop has
published two numbers that cannot be read together.** If the laptop half slips,
the deterministic results still stand and latency is filed as **`not
measured`** — never as *unchanged*.

---

## 3. Freeze — nothing here is a number

```bash
# 3.1 the HEAD sha, if arm B is the working tree
cd ~/my_programs/fux && git rev-parse HEAD
#   → write it into the NEW pre-registration's §1, commit that file, THEN continue.
#   ⚠ a frozen pre-registration already carries its sha; a later HEAD is a new run, new doc.

# 3.2 the pre-registration's own hash, recorded in the run's evidence
shasum -a 256 work/benchmark/PRE-REGISTRATION-<X>.md
```

| gate | on failure |
|---|---|
| the sha is not in git before the first corpus byte | stop; commit it. *"Committed before the first command ran"* is a sentence the report has to be able to write |
| the pre-registration has no predicted verdict per endpoint | it is not a pre-registration yet — Opus writes the predictions, then freeze |

---

## 4. Corpus — generate, assert, record

```bash
cd ~/my_programs/fux-benchmark

# 4.1 the instrument asserts its own headroom, or halts
python3 shared/generate/make_corpus.py --selftest

# 4.2 every corpus a previous run used still regenerates byte-identical
#     (the generator extension must be strictly additive — or prior runs stop reproducing)
python3 shared/generate/make_corpus.py --out /tmp/regen-t1000 --docs 1000 --seed 12 \
        --bench --pairs 240 --chains 40 --decoys 50 --unanswerable 20
diff <(cd /tmp/regen-t1000 && find . -type f | sort | xargs shasum -a 256) \
     <(cd corpora/t1000     && find . -type f | sort | xargs shasum -a 256)

# 4.3 generate the tiers the pre-registration names — primary tier first
#     v1-vs-HEAD:  t100 / t1000 / t10000  (+ t1000b, the second seed)
#     contested:   t1200 (two seeds) / t10000
python3 shared/generate/make_corpus.py --out corpora/t1200 --docs 1200 --seed 12 --bench \
        --pairs 120 --chains 20 --decoys 30 --unanswerable 20 \
        --contested 120 --heading 40 --path 60 --cluster 4

# 4.4 record the corpus hash — this goes into evidence/ARMS.toml
(cd corpora/t1200 && find . -type f | sort | xargs shasum -a 256 | shasum -a 256)
```

| gate | on failure |
|---|---|
| `--selftest` fails | 🔴 halt. Do not "fix the assertion" |
| 4.2 differs | the generator change is not additive. Halt; the prior runs' reproduce commands are now false |
| a planted structure's count is impossible at a tier (40 chains = 80 % of 100 docs) | use the pre-registered count at the **primary** tier and file the deviation **in the report**, as the v1-vs-HEAD run did (deviation 2) |

⚠ **`fux setup` anchors on the nearest git root, not `cwd`.** Every
`work/<arm>-<tier>/` corpus copy must be its own git repository or `.fux/`
lands in `fux-benchmark/` and the corpus has no index. `bench.py prepare` does
this; verify with `git -C work/A-t1200 rev-parse --show-toplevel`.

⚠ **Hand-verify one planted fact.** `shared/` is imported, so a generator bug
corrupts both arms identically and reads as *"no detected change"*. Open one
generated document and confirm its planted marker / target property is really
there before believing any null.

---

## 5. Gates first, then the numbers

### 5.1 Null control — the same-corpus repeat (rule against the pre-registration's B9 / C5)

```bash
python3 bin/bench.py prepare --run <run> --arm A --tier <primary>
python3 bin/bench.py quality --run <run> --arm A --tier <primary> --label A-rep1
python3 bin/bench.py quality --run <run> --arm A --tier <primary> --label A-rep2
diff runs/<run>/rows/A-rep1-<primary>.jsonl runs/<run>/rows/A-rep2-<primary>.jsonl && echo IDENTICAL
```

| gate | on failure |
|---|---|
| rows not byte-identical | 🔴 **halt — every later number in this session is void.** File the halt |

⚠ The **cross-seed** pairing (A on seed 12 vs A′ on seed 13) is a **rate
check**: query ids are positional, so it compares different questions. Run it,
report it descriptively, **never call it the determinism check**.

### 5.2 The arms manifest — before any A-vs-B row

`bench.py prepare` writes `runs/<run>/ARMS.toml`. Assert, per arm: install
source, resolved version, Python minor, `separation_floor`, `doc_coverage_floor`,
`.fux/enrich` **absent** (except a declared B-full arm), corpus `sha256`.

| gate | on failure |
|---|---|
| floors differ between two arms that will be paired | 🔴 void for that pair — a pre-registered threshold is moving inside the comparison (ADR-CONFIDENCE d13 reopen trigger). Fix the config, re-prepare |
| `.fux/enrich` present in a core arm | remove it, re-prepare. An enrichment delta is not a version delta |

### 5.3 The differential law — within each arm, before any `--fast` number

`ask --fast` ≡ `ask --scan`, byte-identical, across the full query set, **per
arm**. `archived_weight` must be `1.0` in both arms (below it W-73's law does
not hold).

| gate | on failure |
|---|---|
| any mismatch in an arm | that arm is **scan-only** in the latency section. Not a halt; a scope cut, filed |

### 5.4 Quality — primary tier first, rows as the run goes

```bash
for ARM in A B; do
  python3 bin/bench.py prepare --run <run> --arm $ARM --tier <primary>
  python3 bin/bench.py quality --run <run> --arm $ARM --tier <primary> --label $ARM
done
python3 bin/bench.py mcnemar --a runs/<run>/rows/A-<primary>.jsonl \
                             --b runs/<run>/rows/B-<primary>.jsonl \
                             --suite <suite> --key <metric> [--kind <kind>]
```

- One row per query per arm, written **as the run goes**. An aggregate
  reconstructed afterwards is not evidence.
- **Headroom per endpoint, per arm** — score and *could-have-changed* count —
  computed from the rows before any `p` is read (README rule 5).
- Any ablation arm (B-tuned) differs from its base in **exactly one key**, or
  it is void (contested §2).
- Secondary tiers after the primary; descriptive only.
- ⚠ **`fux answer` writes its repeat-query `note:` to stderr.** Capture stdout
  alone or `--json` is intermittently unparseable and reads as a flaky engine.

| gate | on failure |
|---|---|
| an endpoint has **0 headroom** in both arms | its verdict is **`INCONCLUSIVE`**, whatever `p` says — it could not have detected anything. Never `PASS` |
| a control (C4-type) shows a delta | the instrument measures something other than the field it names; C1/C3-type endpoints are in doubt. File that, do not rescue |
| the harness merged stdout/stderr | fix the harness, re-run that arm. Do not filter rows by hand |

### 5.5 Bytes and wheel — deterministic, cheap, run early

`.fux/index/` bytes and shard count per tier per arm; built wheel size per arm.
Read the record shape from an actual record (`tf_fields`, presence of `code` /
`vectors` keys) rather than assuming it.

---

## 6. The two-session `blind` protocol — the only way this run states a delta

Whoever writes the generator and reads a score is `informed`, and **no delta
may be stated from an `informed` run**. Blind takes two sessions that never
share what the other made:

| session | model | may read | may NOT read | stops after |
|---|---|---|---|---|
| **1 — author** | Opus | source of both arms, the pre-registration, this runbook | any arm's output on the eval corpus, any prior per-query score | §4 complete: corpora generated, `sha256` recorded, generator + query sets **committed and hashed**, hand-authored subsets (chains, unanswerables) written. **Then it stops.** |
| **2 — execute** | Sonnet (Opus for `ANALYSIS.md`) | the frozen corpora, the harness, the pre-registration | the generator's source, session 1's transcript, any failure list | §5, §7, §8 |

Rules that make it hold:

1. Session 1's last act is a commit whose message names the corpus hashes. Session
   2's first act is verifying them. The hash is the handoff.
2. Session 2 never opens `make_corpus.py`. If it must (a bug), the run is
   reclassified `informed` and says why.
3. The "decline" observable and every other operationalisation is written by
   session 1, **before** either arm runs — the v1-vs-HEAD run chose one after
   watching both arms and that alone made it `informed` (deviation 4).
4. Post-hoc analysis is allowed, labelled **post-hoc**, kept out of every verdict.

⚠ This is a handoff shape, not a process document, and it costs one extra
session. Skipping it is legitimate — the run is then `informed`, files
everything, and **states no delta**. What is not legitimate is one session
claiming blind.

---

## 7. Latency — laptop only, one session, arms interleaved

```bash
python3 bin/latency.py --run <run> --tier t10000 --queries 240 --repeats 5   # A B A B, never AAAA BBBB
```

- 20 warm-up queries per arm, discarded. Cold ingest and `build`, 3 repeats,
  interleaved, **all three filed** with the median reported.
- Close everything else. The v1-vs-HEAD run's third ingest repeat was a 38.8 s
  outlier on a busy laptop; the median saved it, the outlier is still in the file.
- Rule against the pre-registration's B5 / B6 fences. ⚠ **They are regression
  fences, not improvement claims.**

| gate | on failure |
|---|---|
| any wall-clock produced on a different machine or session from the rest | file latency as **`not measured`**. Never merge |

---

## 8. Analysis, verdicts, filing — one change, all of it

**Opus writes `ANALYSIS.md` and every `VERDICT*.md`.** Sonnet may draft the
tables.

- [ ] `work/regression/<date>-<run>/report.md` — frontmatter `type`, `name`,
      `description`, **`classification: blind|informed`**, `timestamp`,
      `prereg:` path. An `## Authorship` table: *artifact · author · could
      reach (queries / judgments / prior scores / none)*.
- [ ] `ANALYSIS.md` — each finding → a specific improvement with a repro
      command; unresolved causes stated as unresolved.
- [ ] `evidence/` — `rows/*.jsonl` (one file per arm per tier), both eval sets,
      `ARMS.toml`, the harness **as run**, the pre-registration's `sha256`.
- [ ] `VERDICT.md` for the primary endpoint and `VERDICT-<id>.md` for every
      other — `type: Verdict`, `verdict: PASS|FAIL|INCONCLUSIVE`, `prediction:`,
      `pre_registration:` path. **Predicted vs measured, in the file.**
- [ ] **Deviations from the pre-registration, listed in the report**, numbered,
      never absorbed.
- [ ] A row in [`../regression/README.md`](../regression/README.md).
- [ ] The `benchmark/` row in `../DOC-REGISTRY.md` bumped.
- [ ] The presentation (`README.md` rule 4) beside the plan, linked from the
      README table — **no number the filed run does not carry**.
- [ ] `work/OPEN-WORK.md`: the item's row deleted if closed, its file moved to
      `archive/open/`; new items filed for what the run found.
- [ ] `python -m pytest -q tests/test_regression_runs.py tests/test_doc_registry.py tests/test_doc_links.py tests/test_setup_docs.py`
      green **before** the commit.

🔴 **What the report may never say** is the pre-registration's §5. Read it again
before writing the one-line result. A null is reported in the same font as a win.

---

## 9. Hazards this harness has already taught

| hazard | looks like | the check |
|---|---|---|
| saturated suite (marker `df = 1`) | two identical engines, 0 discordant everywhere | headroom column (§5.4) |
| saturated **control** | the predicted null, at 100 % both arms | a control with 0 headroom is `INCONCLUSIVE` |
| every ranking prior off at the default | B-core ≡ A on ranking | read `tune.py` defaults **before** predicting; say so in §1.1 of the pre-registration |
| generator bug in `shared/` | identical failures in both arms | hand-verify a planted fact (§4) |
| `fux setup` anchored on the harness root | corpus with no index, `.fux/` in `fux-benchmark/` | `git -C work/<arm>-<tier> rev-parse --show-toplevel` |
| stderr merged into `--json` | intermittent parse failures, "flaky engine" | capture stdout only |
| cross-seed read as determinism | "0 discordant across two seeds" | same-corpus repeat is the gate |
| one session, blind claimed | — | §6, or file `informed` |
| latency across surfaces | a p95 ratio nobody can read | §2 |
| B-full "ceiling" never run | the pre-registration promises a table the run lacks | if an arm is dropped, **say so as a deviation**; the v1-vs-HEAD run did not |
