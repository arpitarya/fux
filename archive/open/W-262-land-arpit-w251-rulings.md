---
type: Handoff
name: W-262
description: "Land six of Arpit's 2026-10-04 W-251 rulings: #2 doctor names a stale template copy (option B, never rewrites); #4 the library's explain/graph/path JSON converges on the CLI's; #22 no required check on main (record text); #25 L3's snapshot sentence re-pointed; #3 find --no-archived; #15 SR-RS d12 narrowed to evaluation-set metrics."
item: W-262
filed: 2026-10-04
ball: agent
---

# W-262 — land Arpit's W-251 rulings #2, #3, #4, #15, #22, #25

**Status: ratified 2026-10-04; DoD 1, 2, 3, 4, 6 and 7 LANDED 2026-10-05 (Claude Code, Opus) — #2 the template stamp and `seeded copies current` row, #4 library → CLI payloads on both readers, #22, #25, #15 record text, B-013/B-014/B-147/B-154 deleted. DoD 5 (#3, `fux find --no-archived`, Python + Node, band on the unfiltered list) landed the same day beside W-261's find split. CLOSED 2026-10-05; B-143 deleted.** Rulings quoted in
[W-251 §3a](../../archive/open/W-251-backlog-audit-rulings.md).

**Model:** Claude Code, **Opus** for #4 (a public shape, two readers);
**Sonnet** for the rest.

## Definition of done

1. **#2 — option B** of [`consumer-template-refresh`](../compare/consumer-template-refresh.compare.md):
   seeded copies carry a stamp of the template they came from; `fux doctor`
   names an **unedited** copy whose template has changed, with the lever
   (*re-seed it yourself*). **fux never writes the file.** Records: SR-DECODE
   d10, SR-DOTFUX 6a, SR-FETCHER d12; the compare's verdict block.
2. **#4 — library → CLI shape** for `explain`, `graph`, `path` `--json`
   ([`cli-library-parity`](../compare/cli-library-parity.compare.md)): the
   library returns what the CLI prints, including `truncated` on `path`, and
   lexical seeds for `graph` (SR-GRAPH d13). SR-API d1's freeze is reopened for
   these three only; CHANGELOG names it as breaking for library callers.
3. **#22 — no:** SR-WORK-RELEASE §Alternatives records *decided: no required
   check on `main` for now; the release is the gate* (Arpit, 2026-10-04).
4. **#25:** SR-LAW-3's text becomes *"The only exceptions are declared per
   source on a committed line the operator wrote — §1 names them; none is built
   as a committed copy today."*; run `gen-laws.py --write`; CLAUDE.md's L3 line
   follows.
5. **#3 — `fux find --no-archived`:** a REMOVE-only filter on the declared
   `archived` fact, in SR-FIND d7's shape; `band` computed on the unfiltered
   list (d9); Node twin; help text; skill `fux-search` names it. **Sonnet.**
6. **#15 — SR-RS d12 narrowed** ([0133](../../records/0133_predictions.md)
   §12): a delta is forbidden on an *evaluation-set metric* (nDCG, pass@k,
   hit@k, fixed/broken on a golden set); bytes on disk, wall-clock and wheel
   size may be stated; a latency on a chosen query set may be stated with the
   sample's authorship disclosed (d13). The block's header becomes *REPAIRED
   2026-10-04 — the trigger fired 2026-08-27* (model-removal,
   rank-flip-susceptibility, p3-sha-stability); the *"Arpit ruled the text
   stands"* paragraph stays as the argument. Arpit, 2026-10-04: *"go with the
   recommendation."*
7. B-rows for each repointed or deleted in `BACKLOG.md`, same change.
