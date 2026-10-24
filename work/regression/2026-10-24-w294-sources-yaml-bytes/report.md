---
type: Run Report
run: 2026-10-24-w294-sources-yaml-bytes
item: W-294
date: 2026-10-24
classification: blind
status: PASS — zero index bytes changed
---

# 2026-10-24 — W-294 step 10: one `.fux/sources.yaml` changes no index byte — **PASS**

**The claim:** replacing `.fux/sources/dirs` + `.fux/sources/urls` with
`.fux/sources.yaml`, and moving the three `!work/golden*` lines into
`.fux/.fuxignore`, leaves this repository's committed index byte-identical. L4
proven, not asserted — same documents, same bytes.

**No per-query rows, and not a paired run:** this run has no queries — it
compares index bytes between two engines on one corpus, and the whole result is
the diff, filed in `evidence/output.txt`.

**The run** ([`evidence/acceptance.sh`](evidence/acceptance.sh), output in
[`evidence/output.txt`](evidence/output.txt)):

| step | engine | source files | result |
|---|---|---|---|
| A | pre-W-294 (main at `cc2e8599`) | `.fux/sources/dirs`, `.fux/sources/urls` | index committed in a scratch worktree |
| B | W-294 branch, `fux ingest` | `.fux/sources.yaml` + converted `.fuxignore` + `fux.toml` | 2453 docs, 0 changed, 0 shards written; `git diff -- .fux/index` **empty** |
| B′ | W-294 branch, `fux ingest --full` | same | 2453 docs, 0 carried forward, 0 shards written; **0 diff lines** |

`.fux/.fuxignore` changed by exactly the conversion: the generated
`work/golden/  # excluded by !work/golden` block line left (nothing excludes by
`!` any more) and the three anchored `/work/golden*` lines arrived. Because B′
re-extracted everything and wrote nothing new, the golden tree is excluded
exactly as before — the L11 guard moved without a gap.

**Reproduce:**

```bash
OLD_PY=<pre-W-294 venv>/bin/python NEW_PY=<W-294 venv>/bin/python \
BASE=cc2e8599 NEWTREE=<checkout of the W-294 commit> \
  work/regression/2026-10-24-w294-sources-yaml-bytes/evidence/acceptance.sh
```

## Authorship

| artifact | author | could reach |
|---|---|---|
| the engine change, the converted files | Claude Code (Opus 5.5), W-294 | none — no evaluation query, judgment or score is involved |
| `acceptance.sh`, this report | the same session | none |

**`blind`**: the check reads no question set and scores nothing; it compares
index bytes.
