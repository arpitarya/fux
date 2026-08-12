# W-32 — Adopt or reject the CLAUDE.md rewrite

**Status:** OPEN · **human** (Arpit) — agent-steering files are proposed,
never auto-applied.
**Blocked by:** —
**Artifacts:** [`handoff/v0.30.0-claude-md.diff`](../handoff/v0.30.0-claude-md.diff)
(the M0a rewrite, 48 KB) · [`handoff/v0.31.0-claude-md-layout.diff`](../handoff/v0.31.0-claude-md-layout.diff)
(the four-line `.fux/` layout addition)

## The situation

`CLAUDE.md` carries its own header saying **"PROPOSED — not in force"**.
The DOC-REGISTRY row was corrected on 2026-08-10 after previously — and
wrongly — claiming the rewrite was adopted. So the file every agent reads
first is in an undecided state, and has been since M0.

This is the highest-leverage open item on the list, and the cheapest: every
session that starts, starts by reading a document nobody has ratified.

## Correction (2026-08-12) — there is no `CLAUDE.md.proposed`

**The rewrite is already the live file.** It was written straight into
`CLAUDE.md` with a header declaring itself not in force, and has been there
since `3892c55` (2026-08-09). Verified: the diff is
`a/CLAUDE.md → b/CLAUDE.md.proposed`, its a-side blob `4f52859` is the
*pre-rewrite* file, and the live `CLAUDE.md` is the b-side content;
`git log --follow -- CLAUDE.md` shows no move.

So the decision is asymmetric, and the DoD below is corrected for it:

- **Yes** → delete the eight-line PROPOSED header. Nothing moves.
- **No** → revert ~800 lines of the file every session reads first, which
  every session since 2026-08-09 has followed as binding.

Packaged for decision in
[`handoff/v0.32.0-ratification-package.md`](../handoff/v0.32.0-ratification-package.md)
§Decision 4.

## Definition of done

- [ ] Arpit adopts or rejects the M0a rewrite. Adoption is deleting the
      PROPOSED header block and bumping the DOC-REGISTRY row — **not** a
      `git mv`; see the correction above.
- [ ] The `.fux/` layout diff is applied (or folded into the adoption, if
      the rewrite lands first) so the Layout section describes the tree that
      actually exists.
- [ ] The §Layout `archive/` line is fixed — it says `docs/archive/` holds
      `v0.26-docs/ (frozen)`, which is false; that set is at **root**
      `archive/v0.26-docs/`. *(Found closing W-43, 2026-08-12; left in place
      under law 7.)*
- [ ] §"Package identity" says the version is **`0.30.0.dev0` at M0b**.
      **`0.32.0` is released.** *(Found at the 0.32.0 release, 2026-08-12;
      left in place under law 7 like the rest.)*
- [ ] The stale `src/fux/ does not exist yet, by design` passage goes — it
      has been false since 2026-08-10.
- [ ] The ADR-numbering line is fixed as part of
      [W-33](W-33-adr-numbering-contradiction.md).
- [ ] The "what to work on next" row is repointed: it says
      `docs/OPEN-WORK.md` **§2**, and that section stopped existing in the
      2026-08-12 restructure. It is now an index, with detail in
      `docs/open/`. *(Deliberately not fixed in place — law 7: agent-steering
      files are proposed, never auto-applied, even for a pointer.)*
- [ ] DOC-REGISTRY row updated in the same change.

## Hazard

Do **not** let an agent adopt this on its own initiative. The rule that
agent-steering files are proposed and never auto-applied is the thing that
keeps a model from editing its own instructions.
