# ADRs — v0.30 line, numbered from 0001

One ADR per completed feature or ruled measurement; every rule carries a
reference. **Numbering restarted at 0001 for the v0.30 rebuild** (Arpit,
2026-08-09). The v0.26 engine's ADRs 0001–0015 are frozen at
[`../archive/v0.26-docs/adr/`](../archive/v0.26-docs/adr/) and are always
cited as **"archived ADR-NNNN"** with that path — a bare "ADR-NNNN" in any
live doc means this directory.

| # | title | status |
|---|---|---|
| [0001](0001-ingest-mode-naming.md) | Ingest-mode naming — `extracted` / `enriched` | ⏳ proposed (Arpit ratifies) |
| [0002](0002-pruning-eval-gate.md) | P1 gate, first run — INCONCLUSIVE (a correct refusal; unmodified record) | accepted as record |
| [0003](0003-pruning-criterion-rerun.md) | P1 re-run — **FAIL**; option E (full postings) accepted by Arpit in session | accepted |
| 0004 | Index format & committed store (written at M1; spec: [`../compare/index-format.compare.md`](../compare/index-format.compare.md)) | planned |
| 0005 | Derived accelerator & differential law (M2) | planned |

Renumbering note (2026-08-09): these files previously carried numbers
0016–0018 continuing the v0.26 sequence; all live references were rewritten
in the same change. Frozen artifacts (`PRE-REGISTRATION*.md`, conformance
`evidence/`) intentionally retain the old numbers — a frozen document is
never edited, and its "ADR-0017/0018" means today's 0002/0003.
