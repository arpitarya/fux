---
type: Run Report
run: 2026-09-11-blind-unanswerable-rerun
classification: blind
date: 2026-09-11
pre_registration: work/regression/2026-09-11-blind-unanswerable-rerun/PRE-REGISTRATION.md
---

# Still 0 abstentions of 20: **TRUE** — 20 of 20 `answerable: true`

**Arpit asked on 2026-09-11 whether the 2026-08-28 finding still holds. It does,
exactly.** Fourteen days and five engine changes later, the engine reports
`answerable: true` on all twenty questions a blind session ruled unanswerable.
**Agreement with ground truth: 0 of 20**, unchanged.

| | 2026-08-28 | 2026-09-11 |
|---|---:|---:|
| `answerable: true` | **20 of 20** | **20 of 20** |
| abstained correctly | 0 | 0 |
| **ids that flipped** | — | **0** |

## Authorship — classification `blind`

| artifact | author | could reach |
|---|---|---|
| the 20 `unanswerable` queries | a fresh session, 2026-08-28 | the ten corpus documents and [`BLIND-AUTHOR-BRIEF.md`](../../../tools/quality-controls/BLIND-AUTHOR-BRIEF.md) — **nothing else** |
| the ground-truth answerability ruling | a second fresh session, 2026-08-28 | the documents and the queries — **no engine output** |
| the harness, the pre-registration, this report | Claude Code (Opus), 2026-09-11 | **everything**, including the 2026-08-28 per-query values |

⚠ **The orchestrating session is informed and authored no evaluation material.**
Both blind artifacts are reused **byte-for-byte**; neither was edited, re-ruled
or extended. 🔴 **The brief's own author was not blind** — stated in the brief,
unchanged by this run, and mitigated by publication rather than by trust.

## Headroom — declared in the pre-registration, before any number

[ADR-RS](../../../docs/adr/0133_predictions.md) decision 22. Computed from the
frozen 2026-08-28 rows, so both figures were knowable in advance and are:

| direction | headroom | status | result |
|---|---:|---|---|
| **improvement** (more abstentions) | **20** | **proven** — by construction: the frozen arm answered `true` on all 20, so every query had room | **no detected change** (0 flips of 20 available) |
| **regression** (fewer abstentions) | **0** | proven | 🔴 **INCONCLUSIVE** |

🔴 **The regression direction is Inconclusive, not "no detected change"**
(decision 22d). The engine was already at the floor on this set: with 0
abstentions to lose, it *cannot* get worse here, so the absence of a regression
is arithmetic rather than evidence. **This run says nothing about whether
abstention got worse.**

**The improvement null is real.** Twenty queries could have moved, none did, and
the headroom is proven rather than asserted — which is the distinction decision
22c exists for and the reason this null means something where the `heading`
control's did not.

## What did move: the bands, slightly, and nothing that changes the answer

| band | 2026-08-28 | 2026-09-11 |
|---|---:|---:|
| `grounded` | 6 | **4** |
| `partial` | 13 | **15** |
| `weak` | 1 | 1 |

**Four ids changed band; none changed answerability.**

| id | then | now |
|---|---|---|
| `u004` | `grounded` | `partial` |
| `u008` | `grounded` | `partial` |
| `u017` | `grounded` | `weak` |
| `u015` | `weak` | `grounded` |

**Net −2 `grounded`. The paired net is 2, below decision 19's floor of 6, so it
is "no detected change"** — a net of 2 cannot clear α = 0.05 at any discordant
count, and this one has 4 discordant pairs going both ways.

⚠ **A band move is not an abstention.** `weak` is still `answerable: true`, so
`u017` sliding two bands changed how confident the engine *said* it was and not
whether it claimed an answer existed. **That is the finding restated, not
softened:** the confidence block moved and the verdict it gates did not.

## Separation still does not catch it

| | 2026-08-28 | 2026-09-11 |
|---|---:|---:|
| at or above the `0.1` floor | 17 of 20 | **15 of 20** |
| median separation | 0.3982 | **0.3238** |
| max separation | 0.8276 | 0.8251 |
| median `doc_coverage` | 0.4667 | **0.3971** |
| median `coverage` | 0.6855 | **0.5233** |

**Three quarters of the set still sits above the floor while answering a
question the corpus cannot answer.** Every value drifted down and none drifted
far enough to matter: two queries crossed the floor, and crossing it changes no
verdict because the floor gates a band, not `answerable`.

The three the ground-truth session called sharpest, unchanged in kind:

| id | band | separation |
|---|---|---|
| `u001` — names of all four regions | `grounded` → `grounded` | 0.4755 → 0.3095 |
| `u005` — north-south ingress | `partial` → `partial` | 0.5568 → 0.5798 |
| `u010` — the on-call stipend | `partial` → `partial` | 0.3483 → 0.3943 |

**`u001` is still reported `grounded`.** The corpus says *"four regions"* and
never names them; perfect vocabulary overlap, absent fact, and the engine's
highest confidence band.

## ⚠ One number in the 2026-08-28 report is not reproducible from its own evidence

**Found while pairing, reported rather than repeated, and the frozen file is
NOT edited** (`CLAUDE.md`: nothing supersedes a measurement except a better
measurement, and a frozen report is never edited to satisfy a later rule).

That report states *"17 of 20 sat at or above the `0.1` floor (median `0.448`,
max `0.828`)"*. Recomputed from `evidence/per-query.csv` in the same directory:

| claim | reproduces? |
|---|---|
| 17 of 20 at or above the floor | ✅ exactly 17 |
| max `0.828` | ✅ 0.8276 |
| **median `0.448`** | ❌ the median is **0.3982** |

`0.448` matches no statistic of that column — not the median (0.3982), the mean
(0.3940), the median above the floor (0.4755) or the mean above the floor
(0.4592). **The prose and the evidence beside it disagree, and the evidence
wins.** This run's own comparison uses 0.3982 throughout.

🟢 **This is the per-query-rows rule working.** The discrepancy is findable at
all only because that run filed its rows — ADR-RS decision 21a's point, from the
other side: every paired result filed *before* 2026-08-28 is uncheckable in
exactly this way, and nobody will ever know which of them says a number its data
does not support.

## Post-hoc — what changed in the engine since 2026-08-28

**Labelled post-hoc and kept out of the answer** (`CLAUDE.md` §"A pre-registered
threshold may never move"). None of this was pre-registered as an explanation
and none of it is offered as one:

- **W-108** — `answer` top-3, and `rerank_weight` reaching the refer plane's
  passage rescore.
- **W-109** — query expansion (`expand_weight` at 0.2).
- **W-111** — declared ties.
- **W-115** — the fenced-code-block fix and the decoder heading skeletons, which
  re-ranked every document containing a fenced block. ⚠ **Landed as defect fixes
  and never measured**; W-116 is that measurement and this run is not it.
- **`[index]`** — `max_phrases` 12 → 32, and `max_table_rows` moved to
  `.fux/tune.toml`.

**The plausible mechanism for the band drift is `max_phrases`**: more committed
headings move `coverage` and `doc_coverage`, both of which feed the band. Both
medians did fall. **This is a hypothesis with no arm behind it**, and testing it
would be a different run with its own pre-registration.

## What this run does NOT establish

- **It adjudicates nothing.** No threshold was proposed, moved or implied; no
  `VERDICT.md` is filed, because there is no prediction to rule on.
- **It does not measure R10**, and it does not reopen ADR-CONFIDENCE's
  `doc_coverage` gate. Fitting a floor to these same 20 numbers is the
  moving-threshold failure.
- **It says nothing about regression.** Headroom in that direction is 0.
- **It does not explain the band drift.** See the post-hoc section, which is
  labelled as such.
- **It is one corpus of ten documents.** The mechanism ADR-CONFIDENCE already
  names — `coverage` and `missing` are **corpus-wide**, so a question whose terms
  exist *somewhere* reads as answerable — is not a property of this corpus's size.

## Evidence

- [`evidence/per-query.csv`](evidence/per-query.csv) — one row per query, with
  the 2026-08-28 values beside each: `prior_engine_answerable`, `prior_band`,
  `prior_separation`.
- [`evidence/per-query.jsonl`](evidence/per-query.jsonl) — the same rows, sorted
  by id, keys sorted, no clock: byte-stable across runs.
- The queries and the ground truth are **not copied here**. They live in
  [`2026-08-28-blind-unanswerable/evidence/`](../2026-08-28-blind-unanswerable/evidence/)
  and were read from there, unedited — a second copy is a second thing to drift.

## Environment

| | |
|---|---|
| engine | `fux-engine` 2.0.0-alpha.7, fux `94d7a76` |
| corpus | `fux-playground` `fece5a3`, `docs/` only — ten documents, sha256 of the sorted file digests `871c492f…` |
| where | `~/my_programs/fux-lab/2026-09-11-blind-unanswerable-rerun` — a **copy**; `fux-playground` was not touched |
| python | 3.14.3 · **os** Darwin arm64 |

⚠ **Whether the ten documents are the same bytes the 2026-08-28 run read could
NOT be established, and is not assumed.** That run recorded no corpus hash. What
*is* established: the 20 queries and the ground truth are byte-identical (both
read from the frozen directory), and the playground's corpus has no commit
between the two dates that touches `docs/`. **The band drift is therefore
consistent with either an engine change or a corpus change, and this run cannot
separate them** — which is why the section above is post-hoc.

🟢 **The gap this exposes is cheap to close and is closed going forward:** this
run records its corpus hash, so the next re-run can answer the question this one
could not.

## Reproduce

```bash
# the lab environment persists; recreate it from the playground's commit
LAB=~/my_programs/fux-lab/2026-09-11-blind-unanswerable-rerun
cd ~/my_programs/fux-playground && git archive --format=tar fece5a3 -o /tmp/pg.tar
mkdir -p "$LAB" && tar -xf /tmp/pg.tar -C "$LAB" && cd "$LAB"
/Users/arpitarya/my_programs/fux/.venv/bin/python -m fux.cli ingest --full

# the corpus hash this report states
find docs -name '*.md' -type f | sort | xargs shasum -a 256 | shasum -a 256

# one query, the command the 2026-08-28 report froze
/Users/arpitarya/my_programs/fux/.venv/bin/python -m fux.cli ask \
  "What are the names of all four Calder Group regions?" --json --band --top 5
```
