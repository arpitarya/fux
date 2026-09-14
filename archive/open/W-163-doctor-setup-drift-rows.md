---
type: Handoff
name: W-163
description: "Eight `fux doctor` rows the records already name as the remedy for setup-time drift and obvious misdeclarations: retired skill folders, a stale `.fux/README.md`, stale starter refusal rules, frozen tunables, frozen output defaults, a type binding that resolves to no decoder, a listed directory that does not exist, and suspiciously thin URLs. Promoted from BACKLOG B-015–B-019 and B-021–B-023."
item: W-163
filed: 2026-09-14
ball: agent
---

# W-163 — `fux doctor`: the setup-drift rows and the three obvious checks

**Model: Sonnet.** Every row has a written source, a stated condition and an
existing register to land in ([SR-DOCTOR](../../records/0152_doctor.md)). The
one judgement — *doctor row, not loader refusal or rewrite* — is the option
every source names first, and it is the only one that changes no behaviour.

**Promoted 2026-09-14 from [`BACKLOG.md`](../BACKLOG.md)** rows B-015, B-016,
B-017, B-018, B-019, B-021, B-022, B-023 (deleted there per SR-WORK-BACKLOG
rule 23). Ratified-not-built: Cowork filed it; Claude Code builds it.

## Context

`fux setup` writes once and never rewrites
([SR-DOTFUX](../../records/0102_fux-directory.md) decision 6). Everything that
ships in a template therefore freezes in every repo that ran setup before the
template changed, and **nothing tells the repo**. Five records each name
`fux doctor` as the place that should say so; three more name checks
`doctor` could run today over declarations it already reads. None is built.

## Definition of done — one row each, all read-only

| row | fires when | source |
|---|---|---|
| **retired agent folders** | `.codex/skills/` or `.github/skills/` exists in a repo set up after their retirement (Copilot then sees duplicate skill copies) | [SR-AGENT-POLICY](../../records/0132_agent-policy.md) decision 16 |
| **stale `.fux/README.md`** | the file's section set differs from the current template's | [SR-DOTFUX](../../records/0102_fux-directory.md) 2026-09-12 amendment |
| **stale starter refusal rules** | `.fux/refusals.toml` is byte-equal to a *previous* starter, i.e. never edited and superseded | [SR-REFUSAL](../../records/0146_refusals.md) W-140 row-17 block |
| **frozen tunables** | `.fux/tune.toml`'s key set lacks keys the current `BUILT_IN` carries | [SR-TUNE](../../records/0135_tuning.md) decision 4 |
| **frozen output defaults** | same, for `.fux/output.toml` | [SR-OUTPUT-DEFAULTS](../../records/0143_output-defaults.md) decision 14 |
| **unbound type** | a declared type in `.fux/formats.toml` resolves to no built-in and no `.fux/decoders/` decoder | [SR-TYPES-LIST](../../records/0128_types-list.md) Consequences |
| **missing directory** | a line in `.fux/sources/dirs` names a path that does not exist | [SR-DIR-LIST](../../records/0120_dir-list.md) Consequences |
| **thin URLs** (advisory) | an indexed `url:` record's extracted byte count is below a stated floor relative to its fetched size | [SR-HTTP-FETCHER](../../records/0119_http-fetcher.md) Consequences |

1. Each row is **report-only** — `doctor` names, it never rewrites
   ([SR-DOCTOR](../../records/0152_doctor.md) decision 1). The remedy line
   says what to do (`delete the folder`, `re-run fux setup --refresh <file>`
   if that exists, else the manual step).
2. Each row lands in the doctor register with its `describes` claim, and
   `--json` carries it. Both readers where `doctor` exists in both.
3. Tests per row: fires on the condition, silent otherwise, on a repo built
   by hand with `.fux/pii.toml` present ([SR-PII](../../records/0148_pii.md)
   decision 17).
4. Records: SR-DOCTOR (the register), and each source record's sentence
   changes from *"is where that would go"* to *"is there"* — in the same
   change. `sr-hash.py --write` after.

## Out of scope

- Any loader refusal (the invasive alternative B-018/B-019 named) — a fork
  for Arpit if a row proves insufficient.
- A `setup --refresh` that rewrites files — a separate decision under
  SR-DOTFUX decision 6.
- The `[priority]` orphan check (B-020): it needs a tune-load seam that does
  not exist; stays in the backlog.

## Where the work is

[`src/fux/doctor.py`](../../src/fux/doctor.py) (`_layout`, `_types_health`,
`_tune_config_health`, `_output_config_health`, `_refusal_health`,
`_url_health` are the neighbours), [`src/fux/templates/`](../../src/fux/templates/),
[`tests/test_doctor*.py`](../../tests/).

## Records this will touch

SR-DOCTOR · SR-AGENT-POLICY · SR-DOTFUX · SR-REFUSAL · SR-TUNE ·
SR-OUTPUT-DEFAULTS · SR-TYPES-LIST · SR-DIR-LIST · SR-HTTP-FETCHER.

## Verification, and the keep/remove call (gap check 2026-09-14)

Order: **implement → test → run on real repos → call each row.**

- **Tests:** per row, fires on the planted condition, silent otherwise, on a
  hand-built repo with `.fux/pii.toml`; `--json` shape asserted.
- **The call, per row, before it ships default-on:** run `fux doctor` on this
  repo, on every golden rung, and on `fux-lab`'s corpora. A row that fires on
  a **healthy** repo is a false positive: it is demoted to `--verbose`-only
  or removed, and the record says which and why. A row that never fires
  anywhere is kept only if its planted-condition test proves it can.
- **Never a fix, always a report** — a row that grows a `--fix` in review is
  out of scope; that is SR-DOTFUX decision 6's fork.
