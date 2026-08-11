# W-30 — Ratify ADR-0001 (ingest-mode naming)

**Status:** OPEN · **human** (Arpit)
**Blocked by:** —
**Artifact:** [`adr/0001-ingest-mode-naming.md`](../adr/0001-ingest-mode-naming.md)
· [`compare/ingest-mode-naming.compare.md`](../compare/ingest-mode-naming.compare.md)

## The decision

`extracted` / `enriched` as the two ingest-mode names. Proposed over
Arpit's original `extracted` / *extracted-plus*-style framing; the
semantics are already fixed in code and prose, so this is a naming
ratification, not a design one.

## Definition of done

- [ ] ADR status → **accepted** (or Arpit overrides the naming, in which
      case the rename is mechanical and lands in the same change).
- [ ] `adr/README.md` status column updated.

## Note

**Non-blocking.** The semantics are already fixed; nothing waits on this.
It is on the list because a permanently-⏳ ADR erodes the meaning of the
status column for every other ADR.
