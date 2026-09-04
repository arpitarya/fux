**Model: Opus** — every item touches ranking arithmetic, a law, or a gate; a wrong last bit is invisible until a differential arm fires. Run in `~/my_programs/fux`.

---

You are implementing **Search v3** in the fux repo. Read, in this order, before touching anything: `CLAUDE.md` (binding), `work/INTERVIEW.md` (from the reset block), `work/OPEN-WORK.md`, then `work/proposals/search-v3.md` (the spec) and the seven detail files `work/open/W-106…W-112-*.md` (each is the handoff: goal, definition of done, blockers, hazards). The target picture is `work/architecture-search-v3.svg`.

## Ratification — this prompt is it

Arpit ratifies the following items by this prompt. Flip each row's lane from `arpit` to `agent` in `work/OPEN-WORK.md` and `status`/`lane` in its detail file **as the first commit**, then work them **in this order**:

1. **W-108** — `answer` refers top-3 + proximity in the passage rescore.
2. **W-107 Phase 0** and **W-106** — two measurements, no product code. Run them next so their verdicts are on file while you build.
3. **W-107 Phases 1–4** — the Node read plane.
4. **W-109** → **W-110** → **W-111**.
5. **W-112** only if W-106's `VERDICT.md` says PASS **and** Arpit has ruled on the compare doc it requires. Otherwise leave its row blocked and say so.

## Decisions Arpit has made (do not re-open; record them where the DoD says)

<!-- Arpit: fill or strike each line before pasting. Anything left blank is a blocker, not a default. -->

- W-107 Phase 0, `log()`: **[ portable `log` in both runtimes | tolerance at round(9) ]**
- W-109 `expand_weight` default: **[ 0.2 ]** · W-110 self-retrieval `k`: **[ 3 ]**
- W-111 tie-break order: **[ superseded → recency → priority → id ]**
- W-112 hashed-meta sources: **[ no vectors unless the line says `embed=true` ]**

Anything else you cannot proceed on without Arpit: write `work/BLOCKED.json` (`decision: ASK`, `surfaced: false`), stop, and say so first. **Never pick a plausible default and continue.**

## How to work each item

For each W-item, in one branch per item off `main`:

1. **Explore.** Read every file the detail file names. Reconcile the item's claims against the code and `git log` — a stale claim is a defect to record, not a reason to stop.
2. **Plan.** Write the plan into the detail file under a `## Plan` heading (files, tests, records to amend). For W-107 the plan is the pre-registration: `work/benchmark/PRE-REGISTRATION-NODE.md` is written and its sha frozen **before** `node/` gets a line.
3. **Implement**, tests first where the DoD names a property (byte-identity at `rerank_weight = 0`, `.fux/index/` unchanged by vectors, the accelerator bound with `--expand`, BLAKE2b vectors, the Porter dump, the `round(9)` tie).
4. **Verify.** `uv run pytest -q tests` and `uv run pytest -q tests_e2e` green; the differential law re-run for anything that touches `rank()`, the sort key, or the accelerator bound; goldens updated only deliberately, with the diff explained in the commit body.
5. **Docs in the same commit** (Law zero): the owning ADR(s) named in the detail file — amended, not just touched; `docs/adr/README.md` ownership table + `tests/test_adr_ownership.py` for any new component or record (`ADR-NODE-SEARCH`, `ADR-EXPAND`, `ADR-VECTORS`); `CHANGELOG.md`; `work/IMPLEMENTATION.md` row; `work/DOC-REGISTRY.md` bumps; `work/OPEN-WORK.md` row deleted and the detail file moved to `archive/open/` **only after** the IMPLEMENTATION row exists and any run is filed under `work/regression/`.
6. **Measured runs** follow `CLAUDE.md §Conformance runs`: pre-registration first, `classification: blind|informed` with the Authorship block, **per-query rows under `evidence/`**, `VERDICT.md` naming the frozen bar, `ANALYSIS.md` with repro commands. Never above 10 000 documents. A result between clear PASS and clear FAIL is written up as ambiguous and handed to Arpit.

Commit messages end with the records touched or `no ADR affected`; install the guard once: `ln -sf ../../scripts/adr-guard.sh .git/hooks/commit-msg`. Check `gh pr checks` yourself — CI green is not enforced by the merge wall.

## Hard rules for this work specifically

- **Nothing in `src/fux/` imports or calls a model, an embedder, or the network.** W-106's script lives under `tools/vector-gate/` behind the dev extra; the embedders are consumer templates under `src/fux/templates/`.
- **`.fux/index/` is byte-identical before and after every item.** Assert it in a test for W-112; check it by hand for the rest.
- **The Node port is a transcription.** Any place it "improves" on Python is a divergence. Zero `package.json` dependencies, no build step, Node ≥ 20, one ESM file. It never fetches.
- **A default is never moved** by any item here: `rerank_weight`, `superseded_weight`, abstention stay Arpit's separate calls already on the Blocked list.
- **Ten lines or fewer** per reply unless asked; announce transitions (`→ W-108: …` / `✓ W-108 · → W-107 P0`), keep `work/NOW.md` current, append a `work/WORKLOG.md` entry per substantive exchange, keep `work/INTERVIEW.md` true during the session.

Start with the triage rule: read `work/OPEN-WORK.md`'s *Blocked on Arpit* block, name anything older than 5 days in your first output, then `→ W-108`.
