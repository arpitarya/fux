---
type: Handoff
name: W-225
description: "The migration that satisfies law L12 — every value lives in a config file, never in code. Tunables move to the consumer's committed TOML, fixed engine values to a new src/fux/constants.toml read by both planes, and every fallback becomes a hard error naming the missing key. Ratified 2026-09-27, NOT built."
item: W-225
filed: 2026-09-27
ball: agent
---

# W-225 — every value lives in a config file (the L12 migration)

**Status: building — stages 1–4 of 8 landed 2026-09-27/28 (3a `output.toml`, 3b `fux.toml`, 4a decoder caps in `formats.toml`, 4b `refusals.toml [scan]`, 4c `.fux/inspect.toml`); stage 5 (R7 structural numerals → `constants.toml`) is in progress: 5a (hashes, parsers, the analyzer), 5b (decoders), 5c/5d (wire, store, protocols, CLI) and 5e (13 leftover tunables → `fux.toml`, SR-CONFIG decision 18) landed 2026-09-28; 5f `doctor` landed too. Stage 6 landed 2026-09-28 (`4d63291e`: parameter defaults removed, the library reads `output.toml [api]`, `[refer] timeout_seconds`). Stage 7 landed 2026-09-28 (`dad6c5fa`: the AST veto test, `tests/l12_allow.toml`), and the CHANGELOG's 3.0 lines. Arpit ruled the open calls (R11–R13) and R13 is built (2026-09-28). Left: 5f `inspect` (after W-228) and stage 8's flip of SR-LAW-12 decision 9.** Stage 3b's four behaviour changes are listed for Arpit in the compare doc §"Where the build departed". (Stage 7's `doctor --fix` writer landed early, with stage 2: every later stage needs it.) Stages, in order: 1 `constants.toml` + the fixed names · 2 `tune.toml`, no fallback · 3 `fux.toml` + `output.toml` · 4 the other `.fux/*.toml` (formats limits + digest, refusals, `inspect.toml`) · 5 R7 structural numerals · 6 R8 bool and every parameter default · 7 `doctor --fix`/`setup` + the AST test · 8 records, CHANGELOG, byte-equality run. The law is [SR-LAW-12](../../records/0014_LAW-12-values-live-in-config.md);
this item makes it true.

## ✅ OPEN CALLS RULED — 2026-09-28 (Arpit, Cowork) · ratified, NOT built

**Arpit, 2026-09-28:** *"go with the recommendation"*, on all three. Now [SR-LAW-12](../../records/0014_LAW-12-values-live-in-config.md) decision 6b (R11–R13) and its veto condition.

- **R11 · `output.toml [api]` stays** as built (SR-OUTPUT d25). No behaviour change.
- **R12 · dataclass boolean field defaults are NOT values** (record shape, *absent means no*). No code change: the ratified scanner already skips a `bool` in a class body. Non-boolean field literals stay values.
- **R13 · the 16 `for-arpit` sites:** OOXML part names + `MAGIC`/`MAGIC_BY_DECODER` → `constants.toml [decoders.*.format]` (both planes, parity test); generated file bodies (`_GITIGNORE`, `_SHIM`, `CACHEDIR_TAG`, `HOOKS`, `_PREAMBLE`) → `src/fux/templates/*.txt`; `sourcelist` `DIRS`/`TYPES`/`URLS` → `grammar` on `tests/l12_allow.toml`.
- ✅ **R13 built 2026-09-28** (Claude Code, Opus): `for-arpit` → 0, byte-equal. See the compare doc §"Where the build departed".
- **Left:** stage 5f `inspect` (the `pending-w228` 101) — **waits on W-228**, which holds `src/fux/inspect/` open. Then stage 8 (SR-LAW-12 decision 9's flip, byte-equality run). Both suites whole before it closes.
- ✅ **2026-10-03 (Cowork, by Arpit's delegation): the hold on W-228 is LIFTED — 🟢.** W-228's DoD 1–10 landed 2026-09-28 and `src/fux/inspect/` is no longer held open; what W-228 still owes (planted misfits in `seed/`, a rung) is golden data, not code, and a later `misfit_floor` lands in `.fux/inspect.toml` — which is where L12 wants it anyway. Stage 5f is agent-closable now.

**Model:** Claude Code, Opus — a cross-plane refactor with byte-equality gates.

## §1 — The ruling

Arpit, 2026-09-27 (Cowork): *"every const or default value will only and only
be defined in tune.toml or fux.toml or in one of the other config files, or
maybe create a new config file; if the value is missing throw an error, but
there shouldn't be any default value within the functions … be it node or
python it should always be read from one of the toml files; exception is the
files used for setup."*

Scope, asked and answered the same day:
- **Tunable values** → the consumer's TOML. **Fixed values** (`SCHEMA`,
  `RULES_VERSION`, …) → *"another internal-to-code file"* — named
  `src/fux/constants.toml` in the law.
- **Missing file or key** → hard error naming it.
- **Exempt:** `setup.py` + `templates/`, `tests/` + `tests_e2e/`, `tools/` + `scripts/`.

**Step 1 ruled — Arpit, 2026-09-27: *"I accept the recommendation."*** On
[the classification](../compare/l12-classify.compare.md), R1–R6 all as
recommended; now SR-LAW-12 decisions 1, 6, 9a, 9b and the veto condition:
- **R1–R3:** enum tags, `KNOWN_AGENTS`, presentation counts → not-a-value.
- **R4:** the six two-home conflicts → one home each, today's behaviour kept (decision 9a).
- **R5:** the veto check becomes one AST-based test; classify the ~220 sites the greps miss before step 4. **Scope is ~580 sites, not ~360.**
- **R6:** new `.fux/inspect.toml` for the 20 inspect values.
- **Decoder caps:** every one enters the extract-config digest (decision 9b).

## §2 — Evidence (2026-09-27 scan)

- **276** module-level literal constants in `src/fux/**/*.py`, **70** in `node/src/**/*.mjs`.
- **16** Python functions with a numeric parameter default.
- The worked example: `MINED_WEIGHT = 0.5` in `query/mined.py` and
  `query/mined.mjs`, imported as a fallback by `tune.py:663` and
  `config/tune.mjs:159`.
- `tune.py` `load()` returns `DEFAULT_TUNE` when the file is absent, empty or
  unparseable-as-empty — the fallback the law forbids.

## §3 — Definition of done

1. **Classify every literal.** One table in this item's evidence folder: each
   of the ~360 sites as `tunable → <file>.<table>.<key>`, `fixed →
   constants.toml.<key>`, or `not a value` (SR-LAW-12 decision 6, with the
   reason). ⚠ **Every `not a value` call Arpit has not seen is listed for his
   review before step 3.**
2. **`src/fux/constants.toml`** exists, holds every fixed value, is read by
   one Python loader and one Node loader, ships in the wheel, and is inlined
   into the Node bundle at publish ([L10](../../records/0012_LAW-10-bundled-output.md)).
   It gets an owner record and a row in `records/README.md`'s ownership table.
3. **Templates hold every tunable.** `src/fux/templates/` gains
   `tune.toml.txt`, `output.toml.txt`, `formats.toml.txt` (today some are written
   from code). `fux.toml.txt` writes **every** key — nothing omitted to inherit.
4. **No fallback anywhere.** `DEFAULT_TUNE`, every `DEFAULT_*`, every
   module-level literal in the classify table, and every literal parameter
   default are deleted from `src/fux/**` and `node/src/**`. A missing
   file/table/key raises `FuxError` (`<file>: [table] key is missing`) in both
   planes, with the same message.
5. **`fux doctor`** reports every missing key in one pass; **`fux doctor --fix`**
   and **`fux setup`** write missing keys from the templates and nothing else
   does.
6. **`--no-tune`** reads the packaged `tune.toml.txt`, not code.
7. **The AST-based L12 test exists and passes** (SR-LAW-12 §Veto condition),
   with a reviewed allow-list of decision-6 sites; the ~220 sites it finds
   beyond the greps are classified in the compare doc before step 4, and any
   new judgement call goes to Arpit.
7a. **Decision 9a's six single homes** are in place, each keeping today's behaviour.
7b. **Decoder caps** live in `formats.toml [limits.<decoder>]` and enter the
   extract-config digest; a test proves a changed cap makes `fux ingest --check` stale.
7c. **`.fux/inspect.toml`** exists, is written by `fux setup` from a template,
   and gets its owner record (SR-INSPECT) and a SR-FUX-DIRECTORY row.
8. **Byte equality holds**: scan = accelerator = Node = bundle, on the golden
   rungs, before and after — this is a refactor, not a ranking change.

## §4 — In scope / out of scope

- **In:** `src/fux/**`, `node/src/**`, `src/fux/templates/`, this repo's own
  `fux.toml` and `.fux/*.toml` (gain every key), the records below, CHANGELOG.
- **Out:** `tests/`, `tests_e2e/`, `tools/`, `scripts/` — exempt. Changing any
  value — every number keeps exactly the value it has today.

## §5 — Records amended in the same change

- **SR-TUNE** — *absent means every default*, *delete the file and nothing
  changes*, `DEFAULT_TUNE`; `--no-tune`'s meaning (L12 decision 7).
- **SR-CONFIG** — the omit-to-inherit rule for `fux.toml`.
- **SR-OUTPUT-DEFAULTS**, **SR-FORMATS**/decode, **SR-DOCTOR**, **SR-FUX-DIRECTORY**
  (new files `fux setup` writes), and every component record whose owned module
  loses a constant — the classify table names them.
- **SR-LAW-12** — decision 9 flips to *satisfied*, `owns:` gains the constants file.

## §6 — Tests

- A test per plane: removing any one key from a fixture `.fux/tune.toml`
  fails the ranked verbs with the named-key message.
- A repo-wide test running SR-LAW-12's veto greps, so a new literal fails CI.
- Python/Node parity test: both loaders read identical values from
  `constants.toml` and each consumer TOML.
- The existing byte-equality and golden-rung gates, unchanged numbers.

## §7 — Consumer impact (CHANGELOG, breaking)

- An existing repo whose `.fux/*.toml` lacks a key **stops** until
  `fux doctor --fix` is run. That is a breaking change: next major, or a
  migration note Arpit approves.
- A raised default no longer reaches a consumer silently (SR-LAW-12
  §Consequences) — every future default change ships with a migration line.

## §8 — Open questions for Arpit

- ✅ **Release vehicle — ruled 2026-09-27 (R9): 3.0, breaking**, no auto-`--fix`.
- ✅ **R5's scan, ruled the same day (R7, R8, R10):** structural numerals are
  `fixed` → `constants.toml`; every boolean parameter default goes;
  `__version__` stays. SR-LAW-12 decision 6a.
- ⚠ **Regexes:** the law treats parsing regexes as code, not values. Nobody
  has asked for one in TOML; they stay code until someone does.
