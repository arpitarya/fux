---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

NOW: working tree committed (`6f518c6`) — several sessions' work, 191 paths. W-142 RETIRED · W-115 MEASURED · W-144 answered (compare doc = Arpit's call) · W-136 phase 2 COMPLETE (8 rungs to 10 000) · W-140 row 22 fixed, row 21 not reproduced in 11 tries.
🔴 EIGHT FILES ARE DELIBERATELY UNCOMMITTED and two advisory tests are red because of them — that is the tests working. `src/fux/config.py` + `config.schema.json` (ADR-CONFIG) · `setup.py` + `store/fuxdir.py` (ADR-DOTFUX) · `tools/differential/*_arm.py` (ADR-T1-ACCELERATOR). ~500 lines including a DELETED schema and a new 308-line module. `no ADR affected` would be FALSE, and writing those records from a diff means guessing at another session's design intent. **They belong to whoever wrote them.** `config.py` also owes its Node twin `node/src/config/root.mjs`.
🔴 The sealed answer key WAS STAGED — a copy outside the one path `.gitignore` named. Unstaged, file untouched, and `.gitignore` now ignores it by NAME anywhere. Check `git status` for it before any `git add -A`.
⚠ Arpit, 2026-09-12: the built corpora in fux-lab and fux-benchmark are KEPT and reused — never wiped. SETUP-LAB and SETUP-BENCHMARK carry it.
