# docs/archive — completed doc artifacts

*Implemented handoff/prompt pairs, graduated proposals, and superseded design
docs land here, stamped `status: implemented` with a link to the ADR that closed
them. Active directories hold live work only; history stays greppable, not
underfoot.*

**Naming:** archived handoffs/prompts are prefixed by the release version they
shipped (`vX.Y.Z-name.md`), not their in-flight `NNNN` index. Orchestrator or
meta docs that map to no single release keep an unversioned name.

Currently empty — v0.30 has shipped no feature yet. The first entry will be the
M0/M1 handoff pair, once [ADR-0017](../adr/0017-pruning-eval-gate.md) is ruled
on.

---

## ⚠ Where the v0.26 documentation actually lives

**Not here.** The v0.19–0.26 doc set — ADRs 0001–0015, its compare docs,
`example/` contracts, `IMPLEMENTATION.md`, the old flow diagram — is at:

> [`../../archive/v0.26/archive/v0.26-docs/`](../../archive/v0.26/archive/v0.26-docs/)

and the previous plan at
[`../../archive/v0.26/archive/PLAN-v0.26.md`](../../archive/v0.26/archive/PLAN-v0.26.md).

**This is a discrepancy, found by the M0a hygiene pass (2026-08-09), and it is
Arpit's call to resolve.**

- **What the docs said:** the reset's own commit message, `PLAN.md`,
  `INTERVIEW.md`, `README.md` and `index.md` all announced
  `docs/archive/v0.26-docs/`.
- **What the tree does:** the reset moved the entire old repo — engine, tests,
  tools, docs, CHANGELOG — into `archive/v0.26/`, so the doc set went with it.
- **Why it was left alone:** the M0/M1 handoff's binding constraint is *do not
  modify `archive/v0.26/`*, and moving the doc set out would both violate that
  and split a snapshot that is currently whole and self-consistent.
- **Live references have been corrected to the real path**, so no doc names a
  path that does not exist.

**Two defensible end states — pick one:**

| option | argument |
|---|---|
| **Leave it** (current) | `archive/v0.26/` is a complete, self-contained snapshot of the old repo. Its docs belong with the engine they document, and the snapshot stays byte-verifiable. |
| **Move the doc set here** | Matches CLAUDE.md's stated convention (`docs/archive/` = doc artifacts, repo-root `archive/` = old builds) and what the reset intended. Costs one `git mv` and a link sweep. |

The old repo-root `CLAUDE.md` was replaced in place rather than archived, so
that file exists only in git history — `git show 6473987:CLAUDE.md`.
