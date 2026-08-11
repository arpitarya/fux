# W-33 — Resolve the ADR-numbering contradiction

**Status:** OPEN · **human** (Arpit owns the convention)
**Blocked by:** — (settle before or with [W-32](W-32-claude-md-adoption.md))
**Flagged in:** [`adr/README.md`](../adr/README.md) §"Unresolved for Arpit"

## The contradiction

Two live documents disagree about ADR numbering:

| document | says |
|---|---|
| [`adr/README.md`](../adr/README.md) | **Numbering restarted at 0001** for the v0.30 rebuild (Arpit, 2026-08-09); v0.26's 0001–0015 are frozen under `archive/v0.26-docs/adr/` and are always cited as "archived ADR-NNNN" |
| `CLAUDE.md` §"How work happens here" (line ~160) and §Layout (line ~308) | **"Numbering continues at 0016"** |

The numbers actually on disk follow `adr/README.md`: 0001–0004, 0010–0012.
ADR-0012 took the next free number under that policy. `CLAUDE.md` was
deliberately **not** edited to match a choice recorded elsewhere, because a
convention is Arpit's to set, not a builder's to assume.

## Definition of done

- [ ] One policy stated in one place; the other document references it
      rather than restating it. (Restating a convention in two files is how
      this happened.)
- [ ] Both `CLAUDE.md` lines fixed — §"How work happens here" **and**
      §Layout.
- [ ] `adr/README.md` drops its "Unresolved for Arpit" block.
- [ ] If the restart-at-0001 policy stands (it matches disk, so it almost
      certainly does), no ADR files move — this is a documentation fix only.

## Why it is not cosmetic

A future session reading `CLAUDE.md` first will number its ADR 0016 and
collide with nothing, silently forking the sequence. The cost lands later,
which is the same failure mode as picking the wrong model.
