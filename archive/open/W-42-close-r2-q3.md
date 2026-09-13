# W-42 — Close R2-Q3: make the frozen citation reachable

**Status:** OPEN · small, mechanical, unblocked
**Blocked by:** —
**Evidence:** [`adr/0004-index-format.md`](../adr/0004-index-format.md)
§Consequences · prediction **R2**
**Model:** **Sonnet** — a config change plus a re-ingest with an exact
assertion.

## The gap

**R2 stands at 2/3 PASS.** Q1 and Q2 cite correctly. Q3 fails for a reason
that is not this build's fault: its frozen citation target lives in
`archive/v0.26-docs/`, which is **not in `fux.toml`'s configured sources**.
The document exists; the engine was never pointed at it.

```toml
[sources]
dirs = ["docs", "README.md", "CLAUDE.md"]   # archive/v0.26-docs/ is absent
```

## The fix

1. Add `archive/v0.26-docs` to `[sources].dirs` in
   [`fux.toml`](../../fux.toml).
2. Re-ingest.
3. Re-run the three frozen R2 questions.

## Definition of done

- [ ] Q3 returns its frozen citation. **If it still does not, that is a
      real engine finding** — write it up rather than adjusting the
      question. A pre-registered question may not move.
- [ ] R2 recorded as **3/3 PASS** (or the honest failure written up) in
      `OPEN-WORK.md` and in ADR-0004's consequences.
- [ ] Determinism holds: double-ingest after the change is still
      byte-identical (R1 must not regress).
- [ ] Index size delta noted — the archived doc set is large, and this is
      the first time the committed index grows from a config change rather
      than from new work.

## Sequencing note

Recorded intent (2026-08-10): do this **with a build turn**, not as a lone
commit, because it changes the committed index bytes and is best reviewed
alongside code that exercises them. Folding it in ahead of W-22 is the
natural slot.
