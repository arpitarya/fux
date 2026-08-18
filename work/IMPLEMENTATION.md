# IMPLEMENTATION — the milestone log

**How to use this file.** This is the **evidence store**: what shipped, when,
and how it turned out. [`OPEN-WORK.md`](OPEN-WORK.md) reconciles against this
file before anything is treated as done, and a `W-nn` may only be **deleted**
from the queue once its outcome is recorded here.

Rules:

1. **Append a row when a milestone or release lands** — not when it is
   started, not when it is believed finished.
2. **Every row names its evidence**: the ADR that closed it, and the measured
   run under [`regression/`](regression/README.md) where one exists. A row
   with neither is a claim, not a record.
3. **Record the outcome honestly, including the negatives.** A measurement
   that stopped a month of building is a shipped result and belongs here.
4. **Ground it before writing it** — `git tag`, `git log`, the published
   package. Do not copy a status from another doc.
5. This file is **not** a changelog. `CHANGELOG.md` is per release, for users;
   this is per milestone, for the next session.

---

## Milestones

| milestone | shipped | release | closed by | outcome |
|---|---|---|---|---|
| **P1 — the pruning gate** | 2026-08-09 | — | [P1-GATE](regression/2026-08-09-pruning-eval/VERDICT.md) | **INCONCLUSIVE**, and correctly refused. Top-128 was a no-op for 97 %+ of documents on all three corpora — their median vocabulary is 32–46 distinct terms. [Run](regression/2026-08-09-pruning-eval/) |
| **P1 — the re-run** | 2026-08-09 | — | [P1-RERUN](regression/2026-08-09-pruning-rerun/VERDICT.md) | **FAIL.** Five selectors at matched retention; best arm 35.9 pts below unpruned recall@20 at 6 % retention. Option E accepted: the committed index carries **full postings, permanently**. A negative that ended the pruning design. [Run](regression/2026-08-09-pruning-rerun/) |
| **M0 — scaffold** | 2026-08-11 | `v0.30.0` | [ADR-RECORD](../archive/adr/0004_index-format.md) | `src/fux/` package, `fux --version`, `fux doctor`. |
| **M1 — the T0 vertical slice** | 2026-08-11 | `v0.30.0` | [ADR-RECORD](../archive/adr/0004_index-format.md) | Canonical committed store, git-dir ingest, scan-based `fux ask`. **R1 PASS · R2 2/3 PASS** at the time; the third was blocked on a doc-hygiene gap, not the engine. |
| **`.fux/` becomes a declared layout** | 2026-08-11 | *(0.31.x, never published)* | [ADR-DOTFUX](../archive/adr/0011_fux-dir-layout.md) | Every child declared committed or derived; URL source moved inside; `fux doctor` now asserts `git check-ignore` on the index — the ignore rule was the silent failure mode. |
| **URL ingestion via consumer middleware** | 2026-08-10 | *(0.31.x, never published)* | [ADR-URL-INGEST](../archive/adr/0010_url-source-consumer-middleware.md) | `src:"url"`, hashed-meta default, offline carry-forward. `src/fux/` still holds zero network lines — the adapter cap survived by making fetch *configuration plus consumer code*. |
| **The demo corpus leaves the repo** | 2026-08-12 | *(0.31.x, never published)* | [SETUP-PLAYGROUND](setup/fux-playground.md) | `examples/` deleted; graded `fux-playground` sibling with 50 ranked goldens — **41 pass / 9 named `xfail`**. |
| **R2 closes** | 2026-08-12 | — | [ADR-RECORD](../archive/adr/0004_index-format.md) §Consequences | **3/3 PASS** on this repo's own corpus, after adding `archive/v0.26-docs` to configured sources; index +45.1 %. Post-hoc finding filed as [W-44](open/W-44-archived-content-signalling.md), not solved. [Run](regression/2026-08-12-r2-close/report.md) |
| **M2 — the T1 accelerator** | 2026-08-12 | `v0.32.0` (PyPI 2026-08-13) | [ADR-T1-ACCELERATOR](../archive/adr/0005_derived-accelerator.md) | **R3 PASS** — worst-case warm p95 **27.2 ms** on 8 870 RFCs against a pre-registered 150 ms bar, where the reference scan takes 4 248.8 ms. Differential law byte-identical over 6 088 comparisons plus all 50 goldens. **Hybrid fusion measured net −6 and ships default-off.** [Run](regression/2026-08-12-m2-accelerator/report.md) |

## Not yet shipped

`M3` graph lane · `M4` refer plane · `M5` maintenance · `M6` scale & T2 ·
`M7` dogfood & release gate · `M8` deferred. Their state is in
[`OPEN-WORK.md`](OPEN-WORK.md), their spec in [the ADR register](../docs/adr/README.md).
**Nothing above `M2` has a row here, and that is the honest position** — a
milestone earns its row by landing, not by being planned.

## Predictions

| id | status | where |
|---|---|---|
| R1 | **PASS** | M1 |
| R2 | **PASS 3/3** (2026-08-12) | [run](regression/2026-08-12-r2-close/report.md) |
| R3 | **PASS** — 27.2 ms p95 vs a 150 ms bar | [run](regression/2026-08-12-m2-accelerator/report.md) |
| R4–R7 | unmeasured | [`OPEN-WORK.md`](OPEN-WORK.md) |
| P1 | **FAIL** — full postings, permanently | [P1-RERUN](regression/2026-08-09-pruning-rerun/VERDICT.md) |
| P2–P7 | retired with plan revision 1; successors are R3–R7 | [the ADR register](../docs/adr/README.md) |
