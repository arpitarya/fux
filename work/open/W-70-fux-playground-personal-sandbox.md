# W-70 — retire fux-playground's grading contract; it becomes a personal sandbox

**Status:** OPEN — **planning only, do not execute without a fresh read of this
file's Hazards section** · **Filed:** 2026-08-22.

**Spec:** this file.
**Closes with:** `fux-playground` holds documents and URL sources for Arpit to
browse and feel out the engine on, and nothing in it is graded — no
`goldens/queries.jsonl`, no `check.py` rank assertions, no `xfail`/`XPASS`.
[`SETUP-PLAYGROUND`](../setup/fux-playground.md) rewritten to describe that
contract, and [`setup/README.md`](../setup/README.md)'s "which is which" table
stops calling the playground graded.
**Blocked by:** nothing structurally — but see Hazards. This retires a live
regression contract other items read from, so treat "blocked by nothing" as
"mechanically startable," not "safe to run without reading W-57."
**Model:** **Sonnet** for the mechanical rewrite (corpus, `check.py` removal,
doc rewrite); **Opus** for the one real call inside this item — where the
graded phenomena (supersession, near-duplication, staleness) go once
`fux-playground` stops being their home. That is a design decision about the
project's only regression net, not mechanical work.

## Why this exists

Arpit, 2026-08-22, direct: *"[the playground is] for me to try it out how it
works, how does it feel like... No testing or anything or any sample set
should be captured from Fux Playground. It is just for my personal use."*

That is a scope reversal, not an extension. `fux-playground` as it stands
today (rebuilt 2026-08-20, per [`SETUP-PLAYGROUND`](../setup/fux-playground.md))
is a **graded** fixture: 10 adversarial documents plus ~50 hand-written golden
queries in `goldens/queries.jsonl`, asserting rank, with `check.py` failing on
any unexplained regression and on any `xfail` that starts passing unexpectedly
(`XPASS`). Arpit's description above is a different thing: a repo to read and
poke at, with no pass/fail output at all.

## What changes

| | today (`SETUP-PLAYGROUND`) | after this item |
|---|---|---|
| **purpose** | grades — regression net for ranking | personal feel/try-out only |
| **corpus** | 10 adversarial docs, deliberately planting hazards | documents Arpit actually wants to read fux answer against — no adversarial requirement |
| **goldens** | ~50 queries, `goldens/queries.jsonl`, graded on rank | **none** |
| **`check.py`** | grades the corpus, fails on regression/XPASS | **removed** |
| **URLs** | 10, runtime smoke test only, never graded | kept as a browsing/consumption feature, still never graded |
| **`--index-guard` staleness check** | present, doubles as determinism test | open question below — it costs nothing and needs no goldens, so it may be worth keeping even in a pure sandbox |

## Definition of done

- [ ] `goldens/queries.jsonl` and the grading path in `check.py` removed (or
      `check.py` removed outright if nothing else in it earns its keep).
- [ ] The corpus is no longer required to be adversarial — Arpit can add,
      remove, or replace documents freely without owing a golden update.
- [ ] [`SETUP-PLAYGROUND`](../setup/fux-playground.md) rewritten: drop
      "the graded corpus" framing, the contract table's `goldens`/`known
      failures` rows, and the xfail/XPASS explanation. Keep the sibling-repo
      layout, the editable `../fux` dependency, the CDP port note (9299), and
      the URL carry-forward trap — none of that is about grading.
- [ ] [`setup/README.md`](../setup/README.md)'s "which is which" table and
      "why these are documents and not ADRs" section stop calling the
      playground graded.
- [ ] **W-57 and the XPASS gate are explicitly re-homed or explicitly
      orphaned** — see Hazards. This box cannot be checked by silence.
- [ ] A `work/WORKLOG.md` entry recording the reversal and citing this file,
      per CLAUDE.md's doc-sync rule (a scope reversal is a decision, and
      Law zero's "no ADR affected" escape hatch still requires saying so
      out loud in the commit message, since no `docs/adr/` record owns
      `work/setup/`).

## What is reused

- The **sibling-repo layout** (`~/my_programs/fux-playground`, never inside
  `fux`), the **editable `../fux` dependency** in `pyproject.toml` (so it
  exercises the working tree, not a released wheel), and the **CDP port 9299**
  convention all survive untouched — none of that is about grading.
- The **existing corpus content** (Calder Group / Helix, the fictional
  10k-engineer developer platform, chosen to satisfy CLAUDE.md's
  do-not-design-in-reference-to-Anton litmus) can seed the sandbox as-is.
  Nothing forces Arpit to keep it adversarial, but nothing forces him to
  throw it away either — reuse, don't rebuild, unless he wants different
  documents to read.
- The **URL-consumption path** and its carry-forward trap (a plain `fux
  ingest` carries existing `url:` records forward byte-identically; only
  `--refresh-urls` reconciles) are exactly what Arpit described wanting —
  "some URLs, which will be consumed by Fux" — so this is the one place the
  existing contract already matches the new ask without change.

## Hazards

- **This is the project's only ranking regression net.** Removing it does not
  just simplify a repo — it deletes the mechanism that catches a ranking
  change breaking a known answer. [W-59](W-59-refer-plane-measurement.md) and
  [W-57](W-57-graph-lane-acceptance.md) both currently point at this corpus's
  phenomena (the ADR-0007→ADR-0019 supersession pair, the near-duplicate
  runbooks) as their measurement target. **Do not execute this item without
  first reading both files and either re-homing their target corpus or
  recording, by name, that they now have none.** Silence here is exactly the
  failure mode CLAUDE.md's Law zero exists to prevent, applied to a fixture
  instead of an ADR.
- **The corpus was rebuilt once already, from nothing, on 2026-08-20**, after
  the repo went missing with no remote. If this item deletes the goldens
  without deciding whether the *corpus itself* still needs the deliberate
  hazards (supersession pair, near-duplicate pair, etc.) for some other
  consumer, that decision should be made explicitly, not by attrition.
- **Concurrent sessions.** `work/setup/fux-playground.md` and
  `work/OPEN-WORK.md` are touched by Cowork, Claude Code and scheduled tasks
  alike — re-stage and re-read before committing (per
  [[concurrent-sessions-in-one-tree]]).

## Open questions

1. **Where do the graded phenomena go, if anywhere?** Options an executor
   should weigh, not assume: (a) they move into `tests_e2e/` as a proper test
   fixture rather than something a human browses — the option the original
   `ADR-PLAYGROUND` decision explicitly rejected in 2026-08-12 for making the
   corpus unreadable-in-twenty-minutes, but circumstances changed since
   grading is leaving the playground either way; (b) a *third*, separately
   named repo takes over grading and `fux-playground` is purely personal —
   this was the alternative Arpit rejected when asked directly on
   2026-08-22 ("redefine fux-playground itself," not "a separate repo"), so
   it should not be revisited without a new ask; (c) grading is simply
   dropped project-wide and W-57/W-59 lose their acceptance measurement
   entirely — the most consequential option, and Arpit's to choose.
2. **Does `--index-guard` (the byte-for-byte determinism check) survive?** It
   costs nothing, needs no goldens, and doubles as a determinism regression
   test independent of ranking — there is a reasonable case for keeping it
   even in a pure-sandbox playground. Not decided here.
3. **Git history.** The repo has one local commit and no remote (per
   `SETUP-PLAYGROUND`'s Open section). Reset it, or keep history and just
   change what's tracked going forward? Not decided here.

## Reference

- [`SETUP-PLAYGROUND`](../setup/fux-playground.md) — the contract this item
  rewrites.
- [`setup/README.md`](../setup/README.md) — "which is which," also touched.
- [W-57](W-57-graph-lane-acceptance.md), [W-59](W-59-refer-plane-measurement.md)
  — the items whose measurement target this retires; must be re-homed or
  explicitly orphaned before this item can close.
- CLAUDE.md §Law zero — the standing rule that a change touching a record's
  behaviour updates that record in the same change, applied here to a Setup
  doc rather than an ADR.
- Arpit, 2026-08-22 (this session) — the direction this item implements, and
  the AskUserQuestion exchange in this session confirming "redefine
  fux-playground itself" over "a separate repo."
