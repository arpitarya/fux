# Analysis — what the R2 run diagnosed, and what it earns

## 1 · Q3 was configuration, and the diagnosis was already correct

**Nothing to improve here.** ADR-0004 diagnosed this correctly at M1 — the
citation target was outside configured sources — and deliberately declined
to fix it, because moving the archived doc set was Arpit's open call, not a
schema-and-store ADR's to make unilaterally.

That restraint paid. The call was made (2026-08-10, root `archive/` is
canonical), and the fix afterwards was one line with a measured result. A
build that had "helpfully" moved the doc set at M1 would have pre-empted a
decision and made the ruling harder to reverse.

**Repro:** `git show e8035bb:fux.toml` vs the current file — one line.

## 2 · The real finding: retired content answers current questions

This is the improvement the run earns, and it is **not shipped here.**

### The mechanism

`archive/v0.26-docs/` describes an engine that no longer exists. Its
documents are well-written, dense, and on-topic for exactly the vocabulary
the current engine uses — *ingest*, *cache*, *doctor*, *BM25F*, *index*.
They are strong BM25F matches for questions about the **current** system
because they are about a system that shared its vocabulary.

Nothing in the ranking knows one is retired. `df` and term statistics are
computed over the union, so the archived set also shifts the statistics
every live document is scored against.

### Why it is not fixed in this change

Three reasons, all of them binding rather than cautious:

1. **It would be a ranking change shipped off one corpus.** CLAUDE.md:
   *never ship a ranking/behaviour change off a single synthetic corpus.*
   Five hand-picked probe queries on this repo is weaker evidence than that.
2. **The probe is post-hoc.** It was not pre-registered, the queries were
   chosen to stress the risk, and it has no denominator. It is a
   hypothesis-generator, not a measurement.
3. **The precedent is a ruling, not a default.** The v0.26 line faced the
   same shape of problem — stale documents outranking current ones — and
   Arpit ruled *annotate, never reorder* (archived ADR-0013), then later
   reopened the reorder option only on a second corpus's evidence and only
   default-off. Picking a mechanism here without him would re-run a decision
   he has already shown he wants to make himself.

### The options, for Arpit — filed as W-44

| option | what it does | cost | precedent |
|---|---|---|---|
| **A · accept** | archived docs are legitimately the answer to historical questions; `loc` is the signal | zero | the status quo since this commit |
| **B · annotate, never reorder** *(recommended shape)* | a source declared `archived` stamps its results, so `find`/`ask --json` carry the flag and ranking is byte-identical | small; needs a config key and a schema field | archived ADR-0013 — the ruling that already worked here |
| **C · narrow the source** | index only `archive/v0.26-docs/adr/`, not the whole set | one line | none; and Q3 would have passed under it too, which is what makes it arbitrary |

**Recommended shape: B**, because it is the one option that cannot regress a
ranking, and because the repo has already ruled that annotation is the
correct first move for exactly this failure. It still needs its own
measurement and its own ADR before it ships — the recommendation is about
*shape*, not about skipping the gate.

**Do not treat B as approved.** Nothing here authorises building it.

## 3 · A smaller improvement, cheap and unambiguous

**Date-stamp recorded ranks in ADRs.** Finding 1 showed a recorded "#1"
silently becoming "#2" because `README.md` grew a relevant table two days
later. The rank was never wrong; the record just read as a property of the
engine rather than a snapshot of a corpus.

Applied in this change to ADR-0004's R2 paragraph. Cheap, and it removes a
class of future confusion where someone re-runs a recorded measurement, gets
a different number, and cannot tell whether the engine regressed.

**Repro:** `.venv/bin/fux ask "what format is the committed index" --json`
against `baa5b04` (pre-session) and against HEAD — #2 in both.

## 4 · Unresolved

- **How large the intrusion actually is** is unknown. Five probes is not a
  measurement, and no instrument in this repo measures it — the playground
  goldens live in a sibling repo over a different corpus and cannot see it.
  Building that instrument is part of W-44 if Arpit picks B or C, and is
  itself the reason not to guess now.
- **Whether the archived set should also shift `df`** for live documents is
  a separate question from whether its documents should rank. This run does
  not distinguish them, and the distinction may matter to any fix.
