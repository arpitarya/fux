---
type: Analysis
name: node-arm-2-analysis
description: "What the W-252 run does and does not establish, and the one place the frozen pre-registration's wording and the procedure disagree."
run: 2026-10-04-node-arm-2
item: W-252
---

# Analysis

## Reading the zero

0 of 3 204 is the endpoint, but the weight of it is the *coverage*, not the count:
six surfaces on two corpora at two sizes, with a query set that the harness
derives from the corpus's own vocabulary by a fixed rule (no curation toward
green), 5 hazard pins (non-ASCII, empty, whitespace, a no-match term), and the
bundle a consumer runs compared against the tree it was built from.

The two tune passes were the same run (rung tune files are all defaults), so
they confirm determinism of the arm, not a second independent sample. The
effective independent evidence is 2 rungs x 801.

## Why green here still costs little to trust and little to claim

Same model family wrote both readers: a transcription error that both share
would pass. This was true of every earlier run (0/750, 60/60, 0/225), and the
2026-09-12 report's own finding (the arm had been green for a month because both
sides ignored the same things) is the standing caution. The result is parity.

## The one place the pre-registration and the procedure disagree

Pre-registration §5 says the build check is `diff -rq` on the two runtime
directories, "only stamp.json may differ". The procedure, written in the same
section, deletes `.fux/runtime` in the Node copy first. `diff -rq` therefore
prints six `Only in …` lines for files that only *ingest* writes, as well as the
`stamp.json` difference. **Read literally, the §7 conjunction ("no file but
`stamp.json` differing") is not met by that output.**

Read as the claim it was written to make (the plane Node builds equals the plane
Python builds), it is met: every one of the 596 files Node wrote exists in
Python's directory, 595 are byte-equal and the 596th is `stamp.json`. That is also
the figure `2026-09-30-shared-runtime` reported at Tier 2 (595/595 + stamp).

The pre-registration is frozen and is not edited. The reading used here is
disclosed rather than hidden, and the deciding fact is that the six files are not
plane files and the difference was created by the check's own `rm -rf`, not by
either builder. The verdict takes the second reading and says so; if Arpit
disagrees the correct move is a one-line rerun that removes only
`graph.json`-and-friends instead of the directory, which this note does not
pre-empt.

## Machine and scope

One machine, one OS, Node 24. NODE-2's cross-OS half (ubuntu, windows, Node 20 and
22) remains unrun. The ends of the ladder only.

## Addendum — the build check re-run (orchestrating session, 2026-10-04)

The second reading above was not needed in the end. The check was re-run once
with the deletion step corrected — only the 596 files Node's build writes were
removed from the copy, so the six ingest-side files stayed — and on both rungs
the two runtime directories then held the same 602 files, none differing,
`stamp.json` included. §7's clause holds as written. The defect was §5's
`rm -rf .fux/runtime`, which a future pre-registration should spell as
*remove the plane files*. Evidence: `evidence/build-diff-rerun.txt`.
