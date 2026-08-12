# ADRs — v0.30 line, numbered from 0001

One ADR per completed feature or ruled measurement; every rule carries a
reference. **Numbering restarted at 0001 for the v0.30 rebuild** (Arpit,
2026-08-09). The v0.26 engine's ADRs 0001–0015 are frozen at
[`../archive/v0.26-docs/adr/`](../../archive/v0.26-docs/adr/) and are always
cited as **"archived ADR-NNNN"** with that path — a bare "ADR-NNNN" in any
live doc means this directory.

| # | title | status |
|---|---|---|
| [0001](0001-ingest-mode-naming.md) | Ingest-mode naming — `extracted` / `enriched` | ⏳ proposed (Arpit ratifies) |
| [0002](0002-pruning-eval-gate.md) | P1 gate, first run — INCONCLUSIVE (a correct refusal; unmodified record) | accepted as record |
| [0003](0003-pruning-criterion-rerun.md) | P1 re-run — **FAIL**; option E (full postings) accepted by Arpit in session | accepted |
| [0004](0004-index-format.md) | Index format & committed store — schema, canonical rules, unicode policy frozen | accepted |
| [0005](0005-derived-accelerator.md) | Derived T1 accelerator, the differential law, bounded `mx` skipping; dense lane + RRF **default-off** on measured evidence — **R3 PASS** (worst-case p95 27.2 ms) | ⏳ proposed (Arpit ratifies) |
| 0006–0009 | Reserved: M3 graph · M4 refer · M5 maintenance · M6 scale (numbers already cited by OPEN-WORK DoDs) | planned |
| [0010](0010-url-source-consumer-middleware.md) | URL source via consumer-owned middleware (CDP template) — `src:"url"`, hashed-meta default, offline carry-forward · **amended by 0011** | ⏳ proposed (Arpit ratifies) |
| [0011](0011-fux-dir-layout.md) | The `.fux/` directory — declared committed vs derived planes, `.fux/sources/urls`, `.fux/middleware/cdp.py`, opaque `[sources.url.config]`, doctor checks | ⏳ proposed (Arpit ratifies) |
| [0012](0012-playground-sibling-repo.md) | Demo corpus leaves the engine repo — `examples/` deleted, graded `fux-playground` sibling, file-only committed index, 50 ranked goldens with named `xfail` gaps | accepted |

**Unresolved for Arpit (2026-08-12):** the live `CLAUDE.md` §"How work
happens here" still says *"Numbering continues at 0016"*, which contradicts
this file's restart-at-0001 policy and the numbers actually on disk. ADR-0012
took the next free number under *this* file's policy. The two documents need
reconciling by whoever owns the convention; `CLAUDE.md` was deliberately not
edited to match a choice made here.

Renumbering note (2026-08-09): these files previously carried numbers
0016–0018 continuing the v0.26 sequence; all live references were rewritten
in the same change. Frozen artifacts (`PRE-REGISTRATION*.md`, conformance
`evidence/`) intentionally retain the old numbers — a frozen document is
never edited, and its "ADR-0017/0018" means today's 0002/0003.
