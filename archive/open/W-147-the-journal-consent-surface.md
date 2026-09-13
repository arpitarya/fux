---
type: OpenItem
id: W-147
title: "W-147 — the journal has two consent surfaces; bind them and say so on the specimen"
description: "RULED (a): the `--journal` flag AND a committed `[cli.answer] journal = true` are both explicit consent. Both records are amended. What is owed is a test binding the two surfaces across both runtimes and a specimen line that says the key writes to disk. Ratified, not built."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-12
ruled: 2026-09-13
---

# W-147 — the journal's two consent surfaces

**Model: Sonnet** — the ruling is made and both records are amended; what is
left is a test and one string, against a written definition of done.

**Ratified, not built** (this session ruled it and amended the records; no
`src/`, `node/` or `tests/` byte moved).

## The ruling

> **Arpit, 2026-09-13:** *"I need the flag as well as output TOML
> configuration."*

**Option (a).** Both surfaces are explicit consent and both stay:

| surface | scope | reviewability |
|---|---|---|
| `fux answer --journal` | one invocation | whoever typed it |
| `[cli.answer] journal = true` in `.fux/output.toml` | the repository | **git, code review, readable without watching a terminal** |

- **Default stays `false` on both.** `output_config.BUILT_IN["journal"]` and the
  generated specimen agree, so nothing records by accident.
- **The fork decision 10 reserved — always-on BY DEFAULT — is still refused.**
  An opt-in somebody committed is not a default fux picked. That distinction is
  the whole ruling.
- **(b) `output.toml` refuses the key by name — REJECTED.** It would remove a
  repository-level opt-in that is more auditable than the flag it left behind.
- **(c) move it to `.fux/tune.toml` — REJECTED.** `tune.toml` is the ranking
  file; journalling is not ranking. It trades one mislabelled home for another.

## Already landed in the ruling change (2026-09-13, this session)

- [SR-PROVENANCE](../../records/0142_provenance.md) **decision 10** — the false
  *"only `--journal` WRITES"* replaced by the two-surface ruling, with the
  `tune.toml` refusal and the always-on refusal both stated.
- [SR-OUTPUT](../../records/0143_output-defaults.md) **decision 22** — ratified,
  and `journal` is named a **declared exception to decision 2's boundary rule**
  rather than an instance of it: it leaves the result set identical and still
  writes bytes, which is why the boundary rule alone was never going to catch
  it.

## Definition of done

1. **A test that binds both surfaces**, so neither can be tidied away by a
   later session reading `output.toml` as a pure rendering config:
   - `fux answer` with no flag, in a repo whose `.fux/output.toml` carries
     `[cli.answer] journal = true`, **journals**;
   - `fux answer --journal` with no config **journals**;
   - neither surface present → **no journal file is written**;
   - `journal` at the **shared `[cli]` level is still refused BY NAME**
     (`output_config.py:166` — it is per-verb, and that has not changed).
2. **The Node twin holds.** `node/src/config/output.mjs` already carries
   `journal` in `answer`'s key tuple and in `BUILT_IN`;
   `tests/test_node_config_parity.py` is what keeps them equal — confirm it
   covers the key rather than assuming it, and extend it if it does not.
3. **The specimen line says what the key does.**
   `src/fux/output_config.py:686` emits
   `journal = false    # record each answer's receipt locally`. *"locally"* is
   not *"writes a durable file"*. Rewrite it so a reader of a rendering config
   is told, in the file, which key is not about rendering — and keep the
   generated specimen and any `fux output` sample in step.
4. Both suites green; `no SR affected` is **not** available — if behaviour
   moves, the owning record moves with it in the same commit.
5. Row and this file handled per
   [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rules 54–58 —
   **archived to `archive/open/` with a map row, never deleted** — and the
   outcome written to `IMPLEMENTATION.md`.

## Out of scope

- **A `fux doctor` row reporting that journalling is on.** Decision 10's
  argument says a committed key is within doctor's *reach*; it does not order a
  row. Filing one here would be inventing scope Arpit did not rule on.
- **Any change to the journal's shape, bound or location.** `DEFAULT_JOURNAL_MAX`
  and the gitignored path are SR-PROVENANCE decisions 11 and 13 and are untouched.
- **L8.** The committed key holds the *instruction* to journal, never the
  journal. No committed byte of use record is created by this item.

## Key files

| file | why |
|---|---|
| `src/fux/output_config.py` | `CLI_VERBS["answer"]`, `BUILT_IN["journal"]`, the by-name refusal, the specimen emitter |
| `src/fux/query/provenance.py` | the journal writer itself — read, do not change |
| `src/fux/cli.py` | `_apply_output_defaults`, where the key becomes `args.journal` |
| `node/src/config/output.mjs` | the Node twin of the key set and the defaults |
| `tests/test_node_config_parity.py` | what holds the two runtimes equal |
