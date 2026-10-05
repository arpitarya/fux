---
type: Analysis
run: 2026-10-05-ladder-gen4-rebuild
description: "Why rung-00100 needed two driver changes at 94 seeds, why archived exceeds superseded by one, the title-H1 knife-edge behind the unplanted misfits, the misfit_floor proposal, the name-leak search, and what the new baseline means."
---

# ANALYSIS — the 94-document ladder

## 1 · rung-00100 holds 6 ext documents, and two rules assumed more

Every rung keeps its headline size (the rule since 2026-09-21). So 26 new seeds
cut `rung-00100`'s ext from 32 to **6**: authored hard negatives a01–a06. Two
things that held at 32 broke at 6.

1. **No `ext/archive/` directory.** The builder writes `ext/archive
   archived=true` whenever there is any ext. A source line naming a missing
   directory is a hard ingest error.
   - **Change:** [`build_from_worktree.py`](evidence/build_from_worktree.py)
     wraps the builder's `run()`. Just before `.fux/` is first staged, it drops
     that one line, only when the directory is absent.
   - The README's declaration rule cannot be met by a directory that does not
     exist. Every rung that has the directory gets byte-identical config.
2. **A split supersession pair.** The generator emits its 20 authored documents
   first, in filename order, then the generated stream. a05 and a06 declare
   `supersedes:` on a19 and a20, which sort last, so a 6-document prefix admits
   successors without their targets. The builder refuses that rung.
   - **Change:** [`make_golden_ext_gen4.py`](evidence/make_golden_ext_gen4.py)
     imports the unmodified generator and reorders only the authored list: each
     retired document is emitted immediately before its successor. The order
     becomes `a01 a02 a03 a04 a19 a05 a20 a06 a07 … a18`.
   - This is the generator's own slot-5/6 rule for its generated stream. No
     document's bytes change. The generated stream is untouched, because there
     are still 20 authored documents.
   - Every rung ≥ 200 holds all 20 either way. Only `rung-00100`'s membership
     depends on this order: a19 + a05 instead of a05 + a06.
   - `python3 evidence/make_golden_ext_gen4.py --check-closure` verifies that
     every prefix from 1 to 10 000 is supersedes-closed.

Neither change touches fux-lab. ⚠ **The generator's own `--check` covers only
ext counts 80, 180, 480 and 980, so it could not catch the second break.** Folding
the reorder and an every-prefix closure check into fux-lab's generator is owed.
That is a lab change for a session that may commit there.

## 2 · Archived exceeds superseded by one above rung-00100

Ext counts are no longer multiples of ten: 106, 406, 906 … 9 906. Each rung
therefore ends just after a slot-5 retired document whose slot-6 successor
falls past the boundary. That document is archived and superseded by nothing.
The builder declares archived from paths and superseded from `supersedes:`
targets, so both counts match the index. This is legal and declared. Nested
rungs pick the successor up at the next rung.

## 3 · The unplanted misfits are a knife-edge at `core_share`

Generated SOPs (`ext/sibling/*-sop.md`) open with the H1 `# Temperature
Excursion Response SOP`, but their front-matter title is `Temperature Excursion
Response SOP — <Company>`. So the 2026-09-28 rule ("a leading heading equal to
the title is left out") does not strip it. Quarantine documents in the same
family carry their own H1. Whether the SOP H1 counts as a **core** heading
depends only on the share of members that carry it:

| ladder | rung | family size | lacking the H1 | share carrying it | ≥ 0.80? |
|---|---|---:|---:|---:|---|
| gen 3 | rung-01000 | 74 | — | below 0.80 | no → 1 misfit total |
| gen 4 | rung-01000 | 71 | 14 | 0.8028 | yes → 14 |
| gen 4 | rung-02000 | 150 | 29 | 0.8067 | yes |
| gen 4 | rung-05000 | 385 | 72 | 0.8130 | yes |
| gen 4 | rung-10000 | 779 | 143 | 0.8164 | yes |

**The engine did not cause it.** The gen-3 `rung-01000` was copied and
re-ingested at `ba1c0e44`, and still gives 23 families and 1 misfit. The cause
is the 26-document shift in which ext documents fill the rung. Two fixes are
possible, and **neither is applied**: each is a lens change under SR-INSPECT
d24, or a generator change that moves every rung's bytes.
- the lens compares a leading heading against the title with a ` — …` suffix
  removed;
- the generator writes an H1 that equals its title.

## 4 · The `misfit_floor` proposal (not applied)

W-228 DoD 11 asked for a seed that contains families and planted misfits, and a
filed rung that reports the lens on it. Both now exist. Recall is **3/3 on 8/8
rungs**, and the controls are **0/3 flagged on 8/8**. The `misfit_share` flag (floor
0.20) never fires on any rung (max 10.7 %, on the 94-document seed, where
3 planted misfits sit among 28 family members). SR-INSPECT's discipline is to
keep the floor and drop it to descriptive only if it ever flags a healthy rung,
and it has not. **The proposal for Arpit:**
- **(a)** take `misfit_floor` 0.20 off PROVISIONAL unchanged, the value in
  `inspect.toml` and the `provisional` marker in `src/fux/inspect/__init__.py`; or
- **(b)** keep it provisional until §3's knife-edge is fixed, because from
  rung-01000 up most listed misfits are that artefact.

This run takes neither, because it is a tuning decision.

## 5 · Name-leak search

Seeds 63–88 introduce 288 tokens, and 31 also occur in `rung-10000/ext/`:
- 15 dates;
- 10 common words (`Annex`, `Booking`, `Chilled`, `Water`, …);
- 6 that matter:
  - `Siliguri` and `Raipur` are places that seeds 76, 78, 82 and 86 use, and
    that the generator's companies already use as *Siliguri site* and *Raipur
    site* (50+ documents each);
  - `Imran` and `Vikram` are seed people (Imran Shaikh in 63, Vikram Thakur in
    67) who share a first name with the generator's Imran Sheikh and Vikram
    Sethi (500+ occurrences each);
  - `SHELF` is a capitalised common word in seed 82.

None states a fact about a seed entity. Each is a hard negative for a query that
names only the place or the first name. The generator's banned-name list is
still behind the seed (owed since 2026-09-23). Extending it would change bytes
only if a real leak existed.

## 6 · A new baseline

A rebuilt ladder is a new baseline (A23). Every golden number filed against the
gen-3 ladder names `golden-gen3/` and is never differenced against this one.
- **Rung commit hashes are not reproducible.** GPG signatures carry their own
  time. The manifests and index roots are the reproducible claim.
- **W-240's gate cannot be read off this run.** That gate is a `step10_section`
  pool ≥ 6, and the pool is unknown until a phase-5 capture of `set-5-claude` is
  scored. If the pool is under 6, the 2026-10-03 ruling applies: lengthen seeds
  64–66, then rebuild again.

## Reproduce

    # the ladder (fux-lab's builder + generator unmodified; ~35 min)
    for r in rung-seed:94 rung-00100:100 rung-00200:200 rung-00500:500 \
             rung-01000:1000 rung-02000:2000 rung-05000:5000 rung-10000:10000; do
      .venv/bin/python work/regression/2026-10-05-ladder-gen4-rebuild/evidence/build_from_worktree.py \
        "$PWD" "${r%%:*}" "${r##*:}"
    done
    uv run pytest -q tests/test_golden_ladder_seed.py
    uv run python tools/differential/ladder_check.py
    uv run python tools/quality-controls/ref_edge_census.py --corpora ~/my_programs/fux-lab/corpora/golden
    # the lens against the planted misfits (scratch copies)
    bash work/regression/2026-10-05-ladder-gen4-rebuild/evidence/families_check.sh "$PWD" <scratch> \
      rung-seed rung-00100 rung-00200 rung-00500 rung-01000 rung-02000 rung-05000 rung-10000
    # the leak search
    uv run python work/regression/2026-10-05-ladder-gen4-rebuild/evidence/new_seed_name_leaks.py . \
      ~/my_programs/fux-lab/corpora/golden/rung-10000
