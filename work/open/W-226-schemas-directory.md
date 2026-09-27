---
type: Handoff
name: W-226
description: "Move the five declared-shape schema files into one src/fux/schemas/ directory, beside templates/, and amend SR-LAWS decision 6 — ownership by explicit per-file carve-out instead of by directory. Built and committed 2026-09-27."
item: W-226
filed: 2026-09-27
ball: agent
---

# W-226 — all schemas in `src/fux/schemas/` (committed)

**Status: COMMITTED 2026-09-27 (Claude Code, Opus)**, together with the
serve Answer tab, once the W-225 stage-3a hunks in `constants.toml`,
`query/__init__.py` and `api.py` had landed (`999c1976`). The `owns:` hashes
for `src/fux/query`, `src/fux/api.py` and `src/fux/constants.toml` were
re-stamped in that commit. The Node twins read no schema file, so the commit
message says why `test_node_twins` flags `graph/plane.py`. §3 items 1–8 are
done. Next: reconcile against IMPLEMENTATION, then close.

**Model:** Claude Code, Opus — a small move with an ownership and packaging
edge that is easy to get subtly wrong.

## §1 — The ruling

Arpit, 2026-09-27 (Cowork): *"move all schemas to a separate dir like
templates."* Shown the standing rule against it (SR-LAWS decision 6: *"a shared
`schemas/` directory is forbidden"*, enforced by
`tests/test_schemas.py::test_every_schema_lives_beside_the_code_it_describes`),
he chose **"`src/fux/schemas/` + rule change"**.

This **amends [SR-LAWS](../../records/0001_LAWS.md) decision 6** on his
ruling. It is not a violation of it.

## §2 — What moves

| from | to | owner (unchanged) |
|---|---|---|
| `src/fux/derive/runtime.schema.json` | `src/fux/schemas/runtime.schema.json` | SR-T1-ACCELERATOR |
| `src/fux/graph/graph.schema.json` | `src/fux/schemas/graph.schema.json` | SR-GRAPH |
| `src/fux/maintain/state.schema.json` | `src/fux/schemas/state.schema.json` | SR-MAINTENANCE |
| `src/fux/query/output.schema.json` | `src/fux/schemas/output.schema.json` | SR-ASK |
| `src/fux/store/index-record.schema.json` | `src/fux/schemas/index-record.schema.json` | SR-RECORD |

File names do not change, so the `[schema_files]` / `url_state_schema` names in
`src/fux/constants.toml` stay as they are.

## §3 — Definition of done

1. **The five files are moved with `git mv`** (history preserved), and
   `src/fux/schemas/__init__.py` exists so `importlib.resources.files("fux.schemas")`
   resolves in the wheel and in an editable install.
2. **One loader, one location.** `fux.schema.load` resolves every schema from
   `fux.schemas`. Take the package name from `constants.toml` (L12), not a
   literal. Update every caller:
   - `src/fux/graph/plane.py:129`
   - `src/fux/maintain/urlstate.py:81`
   - `src/fux/query/__init__.py:556`
   - `src/fux/store/recordschema.py:126`, which reads `resources.files("fux.store")`
     directly
   - tests: `test_schemas.py`, `test_api.py:153`, `refer/test_refer_acquired.py:137`,
     `store/test_recordschema.py` (5×), `derive/test_runtime_schema.py`
3. **Ownership by explicit carve-out.** In `records/README.md` OWNERSHIP:
   - `src/fux/schemas/` → **SR-LAWS**, the owner of `schema.py`, the mechanism.
   - One file-level row per schema, owned by the record in §2.
   - The old `src/fux/store/index-record.schema.json` row moves to the new path.
   - Each owner's `owns:` gains its file. Then run `sr-owns --write`,
     `sr-hash --write` and `gen-components --write`.
4. **SR-LAWS decision 6 is amended**, quoting §1:
   - The schemas live in one directory.
   - Ownership stays per shape, **by carve-out rather than by construction**.
   - The cost is named: a schema added without its own row falls to SR-LAWS.
   - The *Alternatives considered* bullet rejecting `src/fux/schemas/` is
     rewritten as history.
   - The same text is rewritten in `src/fux/schema.py`'s module docstring, §*Where a schema file lives*.
5. **The test flips.** `test_every_schema_lives_beside_the_code_it_describes`
   becomes two tests:
   - every `*.schema.json` in `src/fux/` is under `src/fux/schemas/`;
   - every file there has its **own** file-level OWNERSHIP row, never just the
     directory's. That second test replaces what construction used to guarantee.
6. **Links repointed** in the live records: 0002, 0103, 0105, 0106, 0108,
   0109, 0110, 0113, 0126, 0129, 0135, 0141, 0142, 0143, 0146, 0147 and 0154, plus
   `records/RULE-SINCE`, `src/fux/api.py`'s docstring link and the
   code comments that name `<pkg>/X.schema.json`. `archive/`, `work/regression/`,
   `WORKLOG` and `CHANGELOG` history stay as they are.
7. **Packaging checked:**
   - the built wheel contains `fux/schemas/*.schema.json`;
   - `fux setup` and `fux ask --json` work from an installed wheel, not just the
     source tree;
   - the Node bundle is confirmed to read none of these files (only comments
     name them today).
8. **Suites green:** `pytest` full, the node tests, `tests_e2e/`.

## §4 — Out of scope

- Renaming any schema or changing any shape or `schema` version id.
- `records/TEMPLATE.md` and `src/fux/templates/`. They are templates, not
  schemas, and stay where they are.
- A `CHANGELOG` entry beyond one line. Nothing about the public shape changes.

## §5 — Records amended in the same change

SR-LAWS (d6), records/README (OWNERSHIP), SR-RECORD, SR-T1-ACCELERATOR,
SR-GRAPH, SR-MAINTENANCE and SR-ASK (`owns:`), and every record linking a moved
path (§3 item 6).
