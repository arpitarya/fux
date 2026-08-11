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

## Definition of done

- [ ] Arpit adopts or rejects the M0a rewrite. Adoption is mechanical:
      `git mv CLAUDE.md.proposed CLAUDE.md`, delete the PROPOSED block, bump
      the DOC-REGISTRY row.
- [ ] The `.fux/` layout diff is applied (or folded into the adoption, if
      the rewrite lands first) so the Layout section describes the tree that
      actually exists.
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
